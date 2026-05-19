/** 仪表盘 — 概览知识库、对话量、菜单数量等统计数据. */
import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, List, Tag } from 'antd';
import {
  DatabaseOutlined, CommentOutlined, MenuOutlined,
  FileTextOutlined, UserOutlined,
} from '@ant-design/icons';
import { listDocuments, listMenus, listConversations } from '@/api/client';

export default function Dashboard() {
  const [docCount, setDocCount] = useState(0);
  const [menuCount, setMenuCount] = useState(0);
  const [convCount, setConvCount] = useState(0);
  const [recentDocs, setRecentDocs] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const [docs, menus, convs] = await Promise.all([
          listDocuments({ page_size: 5 }),
          listMenus(false),
          listConversations(),
        ]);
        setDocCount(docs.total || docs.documents?.length || 0);
        setMenuCount(menus.length || 0);
        setConvCount(convs.conversations?.length || 0);
        setRecentDocs((docs.documents || []).slice(0, 5));
      } catch { /* ignore */ }
    })();
  }, []);

  return (
    <div>
      <Typography.Title level={4}>仪表盘</Typography.Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="知识文档"
              value={docCount}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1677ff' }}
              suffix="篇"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="系统菜单"
              value={menuCount}
              prefix={<MenuOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="历史对话"
              value={convCount}
              prefix={<CommentOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix="个"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="系统状态"
              value="运行中"
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="最近上传的文档">
            {recentDocs.length === 0 ? (
              <Typography.Text type="secondary">暂无文档</Typography.Text>
            ) : (
              <List
                dataSource={recentDocs}
                renderItem={(doc: any) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<FileTextOutlined style={{ fontSize: 20 }} />}
                      title={doc.title || doc.filename}
                      description={
                        <span>
                          <Tag color={doc.status === 'ready' ? 'green' : 'orange'}>{doc.status}</Tag>
                          v{doc.version} | {new Date(doc.created_at).toLocaleDateString('zh-CN')}
                        </span>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="快捷操作">
            <List>
              <List.Item>
                <Typography.Link href="/admin/knowledge">📄 上传与管理知识文档</Typography.Link>
              </List.Item>
              <List.Item>
                <Typography.Link href="/admin/menus">📋 配置系统菜单路由映射</Typography.Link>
              </List.Item>
              <List.Item>
                <Typography.Link href="/admin/chat">💬 测试小安助手聊天</Typography.Link>
              </List.Item>
              <List.Item>
                <Typography.Link href="/admin/audit">📊 查看审计日志</Typography.Link>
              </List.Item>
            </List>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
