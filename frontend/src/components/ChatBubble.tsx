import ReactMarkdown from 'react-markdown';
import { Tag, Space, Typography } from 'antd';
import { FileTextOutlined, UserOutlined, RobotOutlined } from '@ant-design/icons';
import type { Source, StepInfo, ChatMessage } from '@/types';
import MenuCard from './MenuCard';
import StepGuide from './StepGuide';

interface Props {
  message: ChatMessage;
  onMenuNavigate?: (routePath: string) => void;
  baseUrl?: string;
}

export default function ChatBubble({ message, onMenuNavigate, baseUrl }: Props) {
  const isUser = message.role === 'user';
  const sources: Source[] = parseJSON(message.sources);
  const menuCards = parseJSON(message.menu_cards);
  const steps: StepInfo[] = parseJSON(message.steps);

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 20,
      gap: 8,
    }}>
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: '#1677ff', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, fontSize: 16,
        }}>
          <RobotOutlined />
        </div>
      )}

      <div style={{ maxWidth: '78%' }}>
        {/* Main content */}
        <div style={{
          padding: '10px 16px',
          borderRadius: 14,
          background: isUser ? '#1677ff' : '#f5f5f5',
          color: isUser ? '#fff' : '#1a1a1a',
          lineHeight: 1.7,
          fontSize: 14,
          wordBreak: 'break-word',
        }}>
          {isUser ? (
            <span>{message.content}</span>
          ) : (
            <ReactMarkdown
              components={{
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: '#1677ff' }}>
                    {children}
                  </a>
                ),
                code: ({ children }) => (
                  <code style={{ background: '#e8e8e8', padding: '2px 6px', borderRadius: 4, fontSize: 13 }}>
                    {children}
                  </code>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Menu Cards */}
        {!isUser && menuCards.length > 0 && (
          <div style={{ marginTop: 10 }}>
            <Typography.Text type="secondary" style={{ fontSize: 12, marginBottom: 4, display: 'block' }}>
              📍 相关功能菜单
            </Typography.Text>
            {menuCards.map((card: any, i: number) => (
              <MenuCard
                key={i}
                card={card}
                onNavigate={onMenuNavigate}
                baseUrl={baseUrl}
              />
            ))}
          </div>
        )}

        {/* Steps */}
        {!isUser && steps.length > 0 && (
          <div style={{ marginTop: 10 }}>
            <StepGuide steps={steps} />
          </div>
        )}

        {/* Sources */}
        {!isUser && sources.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <Space size={4} wrap>
              <FileTextOutlined style={{ fontSize: 12, color: '#999' }} />
              <Typography.Text type="secondary" style={{ fontSize: 11 }}>来源：</Typography.Text>
              {sources
                .filter((s, i, arr) => i === arr.findIndex((t) => t.document_name === s.document_name))
                .slice(0, 5)
                .map((s, i) => (
                <Tag key={i} color="default" style={{ fontSize: 10, margin: 0 }}>
                  {s.document_name}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </div>

      {isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: '#52c41a', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, fontSize: 16,
        }}>
          <UserOutlined />
        </div>
      )}
    </div>
  );
}

function parseJSON(val: string | null | undefined): any[] {
  if (!val || val === '[]' || val === 'null') return [];
  try { return JSON.parse(val); } catch { return []; }
}
