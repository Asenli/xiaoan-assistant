/** 可点击的菜单导航卡片 — 支持手动点击和自动跳转. */
import { Card, Typography, Tag, Space } from 'antd';
import { LinkOutlined, RightOutlined } from '@ant-design/icons';
import type { MenuCard as MenuCardType } from '@/types';

interface Props {
  card: MenuCardType;
  onNavigate?: (routePath: string) => void;
  baseUrl?: string; // 宿主系统的 base URL，用于构建完整跳转链接
}

export default function MenuCard({ card, onNavigate, baseUrl }: Props) {
  const fullUrl = baseUrl ? `${baseUrl}${card.route_path}` : card.route_path;

  const handleClick = () => {
    if (onNavigate) {
      onNavigate(card.route_path);
    } else if (fullUrl) {
      // 通过 postMessage 通知宿主页面跳转
      window.parent.postMessage({
        type: 'XIAOAN_NAVIGATE',
        route: card.route_path,
        breadcrumb: card.breadcrumb,
        menuName: card.menu_name,
      }, '*');
      // 同时尝试直接打开（同源情况）
      if (window.top && window.top.location.origin === window.location.origin) {
        window.top.location.hash = card.route_path.startsWith('/#') ? card.route_path.slice(1) : '#' + card.route_path;
      }
    }
  };

  return (
    <Card
      size="small"
      hoverable
      onClick={handleClick}
      style={{
        marginBottom: 8,
        borderLeft: '3px solid #1677ff',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      bodyStyle={{ padding: '10px 14px' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {card.icon && <span style={{ fontSize: 16 }}>{card.icon}</span>}
            <Typography.Text strong style={{ fontSize: 14 }}>
              {card.breadcrumb || card.menu_name}
            </Typography.Text>
          </div>
          {card.description && (
            <Typography.Paragraph
              type="secondary"
              style={{ margin: '4px 0 0', fontSize: 12 }}
              ellipsis={{ rows: 2 }}
            >
              {card.description}
            </Typography.Paragraph>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {card.route_path && (
            <Tag color="blue" style={{ fontSize: 11 }}>
              <LinkOutlined /> {card.route_path}
            </Tag>
          )}
          <RightOutlined style={{ color: '#bbb', fontSize: 12 }} />
        </div>
      </div>
    </Card>
  );
}
