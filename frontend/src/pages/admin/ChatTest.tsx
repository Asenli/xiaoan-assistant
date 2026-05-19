/** 管理员聊天测试页面 — 完整的聊天界面用于测试 RAG 效果. */
import { useState, useEffect, useRef } from 'react';
import {
  Input, Button, Space, Typography, Card, List, Select, Spin, Empty, message,
} from 'antd';
import { SendOutlined, PlusOutlined, FileTextOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  chatSSE, listConversations, createConversation, deleteConversation,
  getMessages, listDocuments,
} from '@/api/client';
import ChatBubble from '@/components/ChatBubble';
import StreamingText from '@/components/StreamingText';
import type { ChatMessage, Source, MenuCard, StepInfo, KnowledgeDocument } from '@/types';

export default function ChatTest() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [streamSources, setStreamSources] = useState<Source[]>([]);
  const [streamMenuCards, setStreamMenuCards] = useState<MenuCard[]>([]);
  const [streamSteps, setStreamSteps] = useState<StepInfo[]>([]);
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[] | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => { loadConversations(); loadDocs(); }, []);
  useEffect(() => {
    if (activeConvId) {
      getMessages(activeConvId).then(setMessages).catch(() => setMessages([]));
    } else {
      setMessages([]);
    }
  }, [activeConvId]);

  const loadConversations = async () => {
    try {
      const data = await listConversations();
      setConversations(data.conversations);
    } catch { /* */ }
  };

  const loadDocs = async () => {
    try {
      const data = await listDocuments({ page_size: 100 });
      setDocs((data.documents || []).filter((d: KnowledgeDocument) => d.status === 'ready'));
    } catch { /* */ }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
    }, 50);
  };

  const handleNewConv = async () => {
    try {
      const c = await createConversation('新对话');
      loadConversations();
      setActiveConvId(c.id);
    } catch { message.error('创建对话失败'); }
  };

  const handleDeleteConv = async (id: string) => {
    try {
      await deleteConversation(id);
      message.success('已删除');
      if (activeConvId === id) { setActiveConvId(null); setMessages([]); }
      loadConversations();
    } catch { message.error('删除失败'); }
  };

  const handleSend = async () => {
    if (!input.trim() || streaming) return;
    const query = input.trim();
    setInput('');
    setStreamText('');
    setStreamSources([]);
    setStreamMenuCards([]);
    setStreamSteps([]);
    setStreaming(true);

    let targetConvId = activeConvId;
    if (!targetConvId) {
      try {
        const c = await createConversation(query.slice(0, 50));
        targetConvId = c.id;
        loadConversations();
        setActiveConvId(targetConvId);
      } catch {
        message.error('创建对话失败');
        setStreaming(false);
        return;
      }
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      sources: null, menu_cards: null, steps: null,
      intent: null, created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    scrollToBottom();

    abortRef.current = chatSSE(
      targetConvId!, query, selectedDocIds,
      (event) => {
        if (event.type === 'text') {
          setStreamText((prev) => { if (!prev) scrollToBottom(); return prev + (event.content || ''); });
        } else if (event.type === 'sources') {
          setStreamSources(event.sources || []);
        } else if (event.type === 'menu_cards') {
          setStreamMenuCards(event.menu_cards || []);
        } else if (event.type === 'steps') {
          setStreamSteps(event.steps || []);
        }
      },
      () => {
        setStreamText((prev) => {
          const assistantMsg: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: prev,
            sources: JSON.stringify(streamSources),
            menu_cards: JSON.stringify(streamMenuCards),
            steps: JSON.stringify(streamSteps),
            intent: null, created_at: new Date().toISOString(),
          };
          setMessages((msgs) => [...msgs, assistantMsg]);
          return '';
        });
        setStreaming(false);
        loadConversations();
      },
      (err) => {
        message.error('请求失败: ' + err);
        setStreaming(false);
      },
    );
  };

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 160px)' }}>
      {/* Sidebar */}
      <div style={{ width: 220, flexShrink: 0 }}>
        <Card size="small" title="文档范围" bodyStyle={{ padding: 8 }}>
          <Select
            mode="multiple"
            placeholder="不限文档"
            value={selectedDocIds || []}
            onChange={(vals) => setSelectedDocIds(vals.length > 0 ? vals : null)}
            style={{ width: '100%', marginBottom: 8 }}
            maxTagCount={1}
            options={docs.map((d) => ({ label: d.filename, value: d.id }))}
            allowClear
          />
        </Card>

        <Card size="small" title="对话列表" bodyStyle={{ padding: 8 }} style={{ marginTop: 12 }}>
          <Button icon={<PlusOutlined />} block size="small" onClick={handleNewConv}>新建对话</Button>
          <List
            size="small"
            style={{ marginTop: 8 }}
            dataSource={conversations.slice(0, 15)}
            renderItem={(item: any) => (
              <List.Item
                style={{
                  padding: '4px 8px', cursor: 'pointer', borderRadius: 4,
                  background: item.id === activeConvId ? '#e6f4ff' : undefined,
                }}
                onClick={() => setActiveConvId(item.id)}
                actions={[
                  <Button key="del" type="link" size="small" danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => { e.stopPropagation(); handleDeleteConv(item.id); }} />,
                ]}
              >
                <Typography.Text ellipsis style={{ maxWidth: 130, fontSize: 12 }}>
                  {item.title}
                </Typography.Text>
              </List.Item>
            )}
          />
        </Card>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div ref={listRef} style={{
          flex: 1, overflow: 'auto', padding: '0 16px', marginBottom: 12,
          background: '#fff', borderRadius: 8,
        }}>
          {messages.length === 0 && !streaming && (
            <Empty description="选择对话或新建对话开始测试" style={{ marginTop: 80 }} />
          )}
          {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}
          {streaming && streamText && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 20, gap: 8 }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%', background: '#1677ff',
                color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>🤖</div>
              <div style={{ maxWidth: '78%' }}>
                <StreamingText text={streamText} />
                {streamSources.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <FileTextOutlined style={{ fontSize: 12, color: '#999' }} />
                    <Typography.Text type="secondary" style={{ fontSize: 11, marginLeft: 4 }}>
                      来源：{[...new Set(streamSources.map((s) => s.document_name))].join(', ')}
                    </Typography.Text>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <Space.Compact style={{ width: '100%' }}>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={handleSend}
            placeholder="输入测试问题，如：我需要结算对账应该干什么？"
            disabled={streaming}
            size="large"
          />
          <Button type="primary" icon={<SendOutlined />}
            onClick={handleSend} loading={streaming} size="large">
            发送
          </Button>
        </Space.Compact>
      </div>
    </div>
  );
}
