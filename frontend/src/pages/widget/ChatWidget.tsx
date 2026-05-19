/** 嵌入式聊天组件 — 通过 iframe 嵌入到宿主业务系统.

  使用方式：
  <iframe src="http://xiaoan-host/widget?token=xxx" style="..."></iframe>

  通过 postMessage 与宿主通信实现菜单导航跳转. */
import { useState, useEffect, useRef } from 'react';
import { Input, Button, Space, Typography, message as antMsg, Empty, Spin } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, CloseOutlined, FileTextOutlined } from '@ant-design/icons';
import { widgetChatSSE } from '@/api/client';
import ChatBubble from '@/components/ChatBubble';
import StreamingText from '@/components/StreamingText';
import MenuCard from '@/components/MenuCard';
import StepGuide from '@/components/StepGuide';
import type { ChatMessage, Source, MenuCard as MenuCardType, StepInfo } from '@/types';

const WIDGET_TOKEN = new URLSearchParams(window.location.search).get('token') || 'xiaoan-widget-key-change-in-production';

export default function ChatWidget() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [streamSources, setStreamSources] = useState<Source[]>([]);
  const [streamMenuCards, setStreamMenuCards] = useState<MenuCardType[]>([]);
  const [streamSteps, setStreamSteps] = useState<StepInfo[]>([]);
  const [guestId, setGuestId] = useState<string>(() => localStorage.getItem('xiaoan_guest_id') || '');
  const [conversationId, setConversationId] = useState<string>(() => localStorage.getItem('xiaoan_conv_id') || '');
  const [expanded, setExpanded] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!guestId) {
      const id = 'guest_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
      setGuestId(id);
      localStorage.setItem('xiaoan_guest_id', id);
    }
  }, []);

  const scrollToBottom = () => {
    setTimeout(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
    }, 50);
  };

  const handleMenuNavigate = (routePath: string) => {
    window.parent.postMessage({
      type: 'XIAOAN_NAVIGATE',
      route: routePath,
    }, '*');
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

    if (!expanded) setExpanded(true);

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      sources: null, menu_cards: null, steps: null, intent: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    scrollToBottom();

    abortRef.current = widgetChatSSE(
      query,
      { conversationId, guestId, token: WIDGET_TOKEN },
      (event) => {
        if (event.type === 'text') {
          setStreamText((prev) => { if (!prev) scrollToBottom(); return prev + (event.content || ''); });
        } else if (event.type === 'sources') {
          setStreamSources(event.sources || []);
        } else if (event.type === 'menu_cards') {
          setStreamMenuCards(event.menu_cards || []);
        } else if (event.type === 'steps') {
          setStreamSteps(event.steps || []);
        } else if (event.type === 'meta') {
          if (event.conversation_id) {
            setConversationId(event.conversation_id);
            localStorage.setItem('xiaoan_conv_id', event.conversation_id);
          }
          if (event.guest_id) {
            setGuestId(event.guest_id);
            localStorage.setItem('xiaoan_guest_id', event.guest_id);
          }
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
      },
      (err) => {
        antMsg.error('请求失败');
        setStreaming(false);
      },
    );
  };

  // 折叠状态 — 只显示触发按钮
  if (!expanded) {
    return (
      <div style={{
        position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
      }}>
        <Button
          type="primary"
          shape="circle"
          size="large"
          icon={<RobotOutlined style={{ fontSize: 22 }} />}
          onClick={() => setExpanded(true)}
          style={{
            width: 56, height: 56, boxShadow: '0 4px 16px rgba(22, 119, 255, 0.35)',
          }}
        />
        <div style={{
          position: 'absolute', top: -4, right: -4,
          width: 12, height: 12, borderRadius: '50%', background: '#52c41a',
          border: '2px solid #fff',
        }} />
      </div>
    );
  }

  // 展开状态 — 完整的聊天窗口
  return (
    <div style={{
      position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
      width: 420, height: 600,
      display: 'flex', flexDirection: 'column',
      background: '#fff', borderRadius: 16,
      boxShadow: '0 8px 40px rgba(0, 0, 0, 0.15)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', background: '#1677ff', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <Space>
          <RobotOutlined style={{ fontSize: 18 }} />
          <span style={{ fontWeight: 600, fontSize: 15 }}>小安助手</span>
          <span style={{
            fontSize: 11, opacity: 0.8, background: 'rgba(255,255,255,0.2)',
            padding: '0 6px', borderRadius: 4,
          }}>食安客服</span>
        </Space>
        <Button
          type="text" size="small"
          icon={<CloseOutlined />}
          onClick={() => setExpanded(false)}
          style={{ color: '#fff' }}
        />
      </div>

      {/* Messages */}
      <div ref={listRef} style={{
        flex: 1, overflow: 'auto', padding: '12px 14px',
        background: '#fafafa',
      }}>
        {messages.length === 0 && !streaming && (
          <div style={{ textAlign: 'center', marginTop: 60 }}>
            <RobotOutlined style={{ fontSize: 40, color: '#d9d9d9' }} />
            <Typography.Paragraph type="secondary" style={{ marginTop: 16, fontSize: 13 }}>
              你好！我是小安助手 👋<br />
              可以问我系统操作、功能入口、食安规定等问题
            </Typography.Paragraph>
            <Space direction="vertical" style={{ marginTop: 8 }}>
              {['我需要结算对账应该干什么？', '如何生成凭证？', '食安法规有哪些？'].map((q) => (
                <Button key={q} size="small" type="dashed"
                  onClick={() => { setInput(q); }}
                  style={{ fontSize: 12 }}>
                  {q}
                </Button>
              ))}
            </Space>
          </div>
        )}
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} onMenuNavigate={handleMenuNavigate} />
        ))}
        {streaming && streamText && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 20, gap: 8 }}>
            <div style={{
              width: 30, height: 30, borderRadius: '50%', background: '#1677ff',
              color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, fontSize: 14,
            }}>🤖</div>
            <div style={{ maxWidth: '80%' }}>
              <StreamingText text={streamText} />
              {/* Inline menu cards during streaming */}
              {streamMenuCards.map((card, i) => (
                <div key={i} style={{ marginTop: 8 }}>
                  <MenuCard card={card} onNavigate={handleMenuNavigate} />
                </div>
              ))}
              {/* Inline steps during streaming */}
              {streamSteps.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <StepGuide steps={streamSteps} />
                </div>
              )}
              {streamSources.length > 0 && (
                <div style={{ marginTop: 4 }}>
                  <FileTextOutlined style={{ fontSize: 11, color: '#999' }} />
                  <Typography.Text type="secondary" style={{ fontSize: 10, marginLeft: 4 }}>
                    {[...new Set(streamSources.map((s) => s.document_name))].join(', ')}
                  </Typography.Text>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '8px 12px', borderTop: '1px solid #f0f0f0' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={handleSend}
            placeholder="输入问题..."
            disabled={streaming}
            size="middle"
          />
          <Button type="primary" icon={<SendOutlined />}
            onClick={handleSend} loading={streaming} size="middle" />
        </Space.Compact>
        <div style={{ textAlign: 'center', marginTop: 4 }}>
          <Typography.Text style={{ fontSize: 10, color: '#ccc' }}>
            本次对话ID: {conversationId ? conversationId.slice(0, 8) + '...' : '新建'}
          </Typography.Text>
        </div>
      </div>
    </div>
  );
}
