// ========== Auth ==========
export interface User {
  user_id: string;
  username: string;
  role: string;
  access_token: string;
  token_type: string;
}

// ========== Knowledge Base ==========
export interface KnowledgeDocument {
  id: string;
  filename: string;
  title: string;
  category: string;
  tags: string;
  file_size: number;
  file_type: string;
  version: number;
  chunk_count: number;
  is_public: boolean;
  status: 'processing' | 'ready' | 'failed';
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentVersion {
  id: string;
  version: number;
  file_size: number;
  chunk_count: number;
  change_note: string;
  updated_by: string;
  created_at: string;
}

// ========== Menu ==========
export interface MenuItem {
  id: string;
  name: string;
  parent_id: string | null;
  level: number;
  sort_order: number;
  route_path: string;
  icon: string;
  description: string;
  business_desc: string;
  keywords: string;
  related_knowledge_doc_ids: string | null;
  is_visible: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MenuTreeNode {
  id: string;
  name: string;
  route_path: string;
  icon: string;
  description: string;
  level: number;
  children: MenuTreeNode[];
}

export interface MenuCard {
  menu_id: string;
  menu_name: string;
  route_path: string;
  breadcrumb: string;
  description: string;
  icon: string;
}

// ========== Chat ==========
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Source {
  document_name: string;
  document_id: string;
  score: number;
}

export interface StepInfo {
  step: string;
  source: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: string | null;
  menu_cards: string | null;
  steps: string | null;
  intent: string | null;
  created_at: string;
}

// SS E stream event types
export interface SSEIntent { type: 'intent'; intent: string; confidence: number }
export interface SSESources { type: 'sources'; sources: Source[] }
export interface SSEMenuCards { type: 'menu_cards'; menu_cards: MenuCard[] }
export interface SSESteps { type: 'steps'; steps: StepInfo[] }
export interface SSEText { type: 'text'; content: string }
export interface SSEDone { type: 'done'; answer?: string }
export interface SSEMeta { type: 'meta'; guest_id?: string; conversation_id?: string }
export interface SSEError { type: 'error'; content: string }

export type SSEEvent = SSEIntent | SSESources | SSEMenuCards | SSESteps | SSEText | SSEDone | SSEMeta | SSEError;

// ========== Audit ==========
export interface AuditLog {
  id: string;
  event_type: string;
  user_id: string | null;
  guest_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  detail: string | null;
  ip_address: string | null;
  created_at: string;
}
