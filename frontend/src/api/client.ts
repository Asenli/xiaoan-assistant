import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({ baseURL: API_BASE });

// Auth interceptor for admin
api.interceptors.request.use((config) => {
  const user = localStorage.getItem('xiaoan_user');
  if (user) {
    const { access_token } = JSON.parse(user);
    config.headers.Authorization = `Bearer ${access_token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('xiaoan_user');
      if (window.location.pathname !== '/login' && !window.location.pathname.includes('/widget')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// ========== Auth ==========
export const login = (username: string, password: string) =>
  api.post('/auth/login', { username, password }).then((r) => r.data);

export const register = (username: string, password: string) =>
  api.post('/auth/register', { username, password }).then((r) => r.data);

// ========== Knowledge ==========
export const listDocuments = (params?: { category?: string; status?: string; page?: number; page_size?: number }) =>
  api.get('/knowledge', { params }).then((r) => r.data);

export const uploadDocument = (file: File, opts: { category?: string; tags?: string; isPublic?: boolean; changeNote?: string }) => {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('category', opts.category || 'general');
  fd.append('tags', opts.tags || '');
  fd.append('is_public', String(opts.isPublic ?? true));
  fd.append('change_note', opts.changeNote || '');
  return api.post('/knowledge/upload', fd).then((r) => r.data);
};

export const updateDocument = (id: string, file: File | null, opts: { title?: string; category?: string; tags?: string; isPublic?: boolean; changeNote?: string }) => {
  const fd = new FormData();
  if (file) fd.append('file', file);
  if (opts.title) fd.append('title', opts.title);
  if (opts.category) fd.append('category', opts.category);
  if (opts.tags) fd.append('tags', opts.tags);
  if (opts.isPublic !== undefined) fd.append('is_public', String(opts.isPublic));
  fd.append('change_note', opts.changeNote || '');
  return api.put(`/knowledge/${id}`, fd).then((r) => r.data);
};

export const deleteDocument = (id: string) =>
  api.delete(`/knowledge/${id}`).then((r) => r.data);

export const getDocumentVersions = (id: string) =>
  api.get(`/knowledge/${id}/versions`).then((r) => r.data);

// ========== Menu ==========
export const listMenus = (activeOnly = true) =>
  api.get('/menus', { params: { active_only: activeOnly } }).then((r) => r.data);

export const getMenuTree = () =>
  api.get('/menus/tree').then((r) => r.data);

export const searchMenus = (keyword: string, limit = 10) =>
  api.get('/menus/search', { params: { keyword, limit } }).then((r) => r.data);

export const createMenu = (data: any) =>
  api.post('/menus', data).then((r) => r.data);

export const updateMenu = (id: string, data: any) =>
  api.put(`/menus/${id}`, data).then((r) => r.data);

export const deleteMenu = (id: string) =>
  api.delete(`/menus/${id}`).then((r) => r.data);

// ========== Chat ==========
export function chatSSE(
  conversationId: string,
  query: string,
  documentIds: string[] | null,
  onEvent: (event: any) => void,
  onDone: () => void,
  onError: (err: string) => void,
): AbortController {
  const user = JSON.parse(localStorage.getItem('xiaoan_user') || '{}');
  const controller = new AbortController();

  fetch(`${API_BASE}/chat/${conversationId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${user.access_token}`,
    },
    body: JSON.stringify({ query, document_ids: documentIds }),
    signal: controller.signal,
  })
    .then(async (resp) => {
      if (!resp.ok) throw new Error(await resp.text());
      const reader = resp.body?.getReader();
      if (!reader) { onDone(); return; }
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'done') { onDone(); return; }
              if (data.type === 'error') { onError(data.content); return; }
              onEvent(data);
            } catch { /* skip */ }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err.message);
    });

  return controller;
}

export function widgetChatSSE(
  query: string,
  opts: { conversationId?: string; guestId?: string; token?: string },
  onEvent: (event: any) => void,
  onDone: () => void,
  onError: (err: string) => void,
): AbortController {
  const controller = new AbortController();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;

  const url = opts.token
    ? `${API_BASE}/chat/widget?token=${opts.token}`
    : `${API_BASE}/chat/widget`;

  fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query, conversation_id: opts.conversationId, guest_id: opts.guestId }),
    signal: controller.signal,
  })
    .then(async (resp) => {
      if (!resp.ok) throw new Error(await resp.text());
      const reader = resp.body?.getReader();
      if (!reader) { onDone(); return; }
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'done') { onDone(); return; }
              if (data.type === 'error') { onError(data.content); return; }
              onEvent(data);
            } catch { /* skip */ }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err.message);
    });

  return controller;
}

export const listConversations = () =>
  api.get('/chat/conversations').then((r) => r.data);

export const createConversation = (title: string) =>
  api.post('/chat/conversations', null, { params: { title } }).then((r) => r.data);

export const deleteConversation = (id: string) =>
  api.delete(`/chat/conversations/${id}`).then((r) => r.data);

export const getMessages = (conversationId: string) =>
  api.get(`/chat/conversations/${conversationId}/messages`).then((r) => r.data);

// ========== Audit ==========
export const listAuditLogs = (params?: { event_type?: string; page?: number; page_size?: number }) =>
  api.get('/audit', { params }).then((r) => r.data);
