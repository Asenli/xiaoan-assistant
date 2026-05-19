import { Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Login from './pages/Login';
import AdminLayout from './components/Layout';
import Dashboard from './pages/admin/Dashboard';
import KnowledgeBase from './pages/admin/KnowledgeBase';
import MenuMapping from './pages/admin/MenuMapping';
import ChatTest from './pages/admin/ChatTest';
import AuditLog from './pages/admin/AuditLog';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = localStorage.getItem('xiaoan_user');
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN} theme={{
      token: {
        colorPrimary: '#1677ff',
        borderRadius: 6,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif',
      },
    }}>
      <AntApp>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/admin"
            element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}
          >
            <Route index element={<Dashboard />} />
            <Route path="knowledge" element={<KnowledgeBase />} />
            <Route path="menus" element={<MenuMapping />} />
            <Route path="chat" element={<ChatTest />} />
            <Route path="audit" element={<AuditLog />} />
          </Route>
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </AntApp>
    </ConfigProvider>
  );
}
