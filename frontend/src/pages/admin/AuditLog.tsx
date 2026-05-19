/** 审计日志查看 — 按事件类型筛选，支持分页. */
import { useState, useEffect } from 'react';
import { Table, Select, Typography, Card, Tag, Space, Empty } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { listAuditLogs } from '@/api/client';
import type { AuditLog as AuditLogType } from '@/types';

const EVENT_COLORS: Record<string, string> = {
  auth: 'blue', knowledge: 'green', menu: 'orange', chat: 'purple',
};

export default function AuditLog() {
  const [logs, setLogs] = useState<AuditLogType[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [eventType, setEventType] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await listAuditLogs({ event_type: eventType, page, page_size: pageSize });
      setLogs(data.logs);
      setTotal(data.total);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchLogs(); }, [eventType, page, pageSize]);

  const columns: ColumnsType<AuditLogType> = [
    {
      title: '事件类型', dataIndex: 'event_type', key: 'event_type', width: 100,
      render: (v: string) => <Tag color={EVENT_COLORS[v] || 'default'}>{v}</Tag>,
    },
    { title: '操作', dataIndex: 'action', key: 'action', width: 120 },
    { title: '资源类型', dataIndex: 'resource_type', key: 'resource_type', width: 100 },
    { title: '资源ID', dataIndex: 'resource_id', key: 'resource_id', width: 120, ellipsis: true },
    { title: '详情', dataIndex: 'detail', key: 'detail', width: 250, ellipsis: true,
      render: (v: string | null) => v || '-' },
    { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 120, ellipsis: true },
    { title: 'IP', dataIndex: 'ip_address', key: 'ip_address', width: 120 },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 170,
      render: (v: string) => new Date(v).toLocaleString('zh-CN') },
  ];

  return (
    <div>
      <Typography.Title level={4}>审计日志</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Typography.Text>事件类型：</Typography.Text>
          <Select
            allowClear
            placeholder="全部"
            value={eventType}
            onChange={setEventType}
            style={{ width: 160 }}
            options={[
              { label: '认证', value: 'auth' },
              { label: '知识库', value: 'knowledge' },
              { label: '菜单', value: 'menu' },
              { label: '聊天', value: 'chat' },
            ]}
          />
          <Typography.Text type="secondary">共 {total} 条记录</Typography.Text>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps); },
          }}
          locale={{ emptyText: <Empty description="暂无审计日志" /> }}
        />
      </Card>
    </div>
  );
}
