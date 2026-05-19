import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout as AntLayout, Menu, Typography, Button, Avatar, Dropdown, Space,
} from 'antd';
import {
  DatabaseOutlined, MenuOutlined, CommentOutlined, AuditOutlined,
  DashboardOutlined, LogoutOutlined, UserOutlined, RobotOutlined,
} from '@ant-design/icons';

const { Sider, Content, Header } = AntLayout;

const menuItems = [
  { key: '/admin', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/admin/knowledge', icon: <DatabaseOutlined />, label: '知识库管理' },
  { key: '/admin/menus', icon: <MenuOutlined />, label: '菜单路由映射' },
  { key: '/admin/chat', icon: <CommentOutlined />, label: '聊天测试' },
  { key: '/admin/audit', icon: <AuditOutlined />, label: '审计日志' },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const user = JSON.parse(localStorage.getItem('xiaoan_user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('xiaoan_user');
    navigate('/login');
  };

  const selectedKey = menuItems.find((m) => location.pathname.startsWith(m.key))?.key || '/admin';

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        width={220}
      >
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          <RobotOutlined style={{ fontSize: 24, color: '#1677ff', marginRight: collapsed ? 0 : 8 }} />
          {!collapsed && <Typography.Text style={{ color: '#fff', fontSize: 16, fontWeight: 600 }}>小安助手</Typography.Text>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <AntLayout>
        <Header style={{
          background: '#fff', padding: '0 24px',
          display: 'flex', justifyContent: 'flex-end', alignItems: 'center',
          borderBottom: '1px solid #f0f0f0',
        }}>
          <Dropdown
            menu={{
              items: [
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
              ],
              onClick: ({ key }) => { if (key === 'logout') handleLogout(); },
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} size="small" />
              <Typography.Text>{user.username || '管理员'}</Typography.Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ padding: 24, background: '#f5f5f5', overflow: 'auto' }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
