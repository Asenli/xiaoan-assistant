/** 知识库管理 — 上传、查看、搜索、删除、版本管理. */
import { useState, useEffect } from 'react';
import {
  Table, Button, Upload, Tag, Space, message, Popconfirm, Card, Typography,
  Modal, Input, Select, Descriptions, Drawer, List, Empty, Form,
} from 'antd';
import {
  UploadOutlined, DeleteOutlined, CheckCircleOutlined,
  SyncOutlined, CloseCircleOutlined, SearchOutlined, HistoryOutlined,
  EditOutlined, FileTextOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  listDocuments, uploadDocument, deleteDocument, updateDocument,
  getDocumentVersions,
} from '@/api/client';
import type { KnowledgeDocument, DocumentVersion } from '@/types';

export default function KnowledgeBase() {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [category, setCategory] = useState('general');
  const [tags, setTags] = useState('');
  const [searchText, setSearchText] = useState('');
  const [editDoc, setEditDoc] = useState<KnowledgeDocument | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [versionsDoc, setVersionsDoc] = useState<KnowledgeDocument | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [versionsOpen, setVersionsOpen] = useState(false);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const data = await listDocuments();
      setDocs(data.documents);
    } catch {
      message.error('获取文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const result = await uploadDocument(file, { category, tags });
      if (result.status === 'ready') {
        message.success(`"${result.filename}" 上传成功`);
      } else {
        message.info(result.message || '处理中');
      }
      fetchDocs();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '上传失败');
    } finally {
      setUploading(false);
      setCategory('general');
      setTags('');
    }
    return false;
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id);
      message.success('已删除');
      fetchDocs();
    } catch { message.error('删除失败'); }
  };

  const handleEdit = async () => {
    if (!editDoc) return;
    try {
      await updateDocument(editDoc.id, null, {
        title: editTitle || undefined,
        category: editDoc.category,
        tags: editDoc.tags,
        isPublic: editDoc.is_public,
      });
      message.success('更新成功');
      setEditDoc(null);
      fetchDocs();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '更新失败');
    }
  };

  const handleViewVersions = async (doc: KnowledgeDocument) => {
    setVersionsDoc(doc);
    try {
      const data = await getDocumentVersions(doc.id);
      setVersions(data);
    } catch {
      setVersions([]);
    }
    setVersionsOpen(true);
  };

  const statusTag = (status: string) => {
    switch (status) {
      case 'ready': return <Tag icon={<CheckCircleOutlined />} color="success">就绪</Tag>;
      case 'processing': return <Tag icon={<SyncOutlined spin />} color="processing">处理中</Tag>;
      default: return <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>;
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const filteredDocs = searchText
    ? docs.filter((d) =>
        d.filename.includes(searchText) ||
        d.title.includes(searchText) ||
        d.category.includes(searchText) ||
        (d.tags && d.tags.includes(searchText))
      )
    : docs;

  const columns: ColumnsType<KnowledgeDocument> = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true, width: 200,
      render: (v: string, r) => v || r.filename },
    { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true, width: 200 },
    { title: '类别', dataIndex: 'category', key: 'category', width: 100,
      render: (v: string) => <Tag>{v}</Tag> },
    { title: '标签', dataIndex: 'tags', key: 'tags', width: 120, ellipsis: true,
      render: (v: string) => v ? v.split(',').map((t: string) => <Tag key={t} style={{ fontSize: 11 }}>{t}</Tag>) : '-' },
    { title: '版本', dataIndex: 'version', key: 'version', width: 60,
      render: (v: number) => <Tag color="blue">v{v}</Tag> },
    { title: '大小', dataIndex: 'file_size', key: 'file_size', width: 80,
      render: (v: number) => formatSize(v) },
    { title: '分块', dataIndex: 'chunk_count', key: 'chunk_count', width: 60 },
    { title: '状态', dataIndex: 'status', key: 'status', render: statusTag, width: 90 },
    { title: '公开', dataIndex: 'is_public', key: 'is_public', width: 70,
      render: (v: boolean) => v ? <Tag color="blue">公开</Tag> : <Tag>私有</Tag> },
    { title: '上传时间', dataIndex: 'created_at', key: 'created_at', width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN') },
    {
      title: '操作', key: 'action', width: 140, fixed: 'right',
      render: (_: any, record: KnowledgeDocument) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />}
            onClick={() => { setEditDoc(record); setEditTitle(record.title); }} />
          <Button type="link" size="small" icon={<HistoryOutlined />}
            onClick={() => handleViewVersions(record)} />
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>知识库管理</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="上传后分类"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={{ width: 140 }}
          />
          <Input
            placeholder="标签，逗号分隔"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            style={{ width: 180 }}
          />
          <Upload
            beforeUpload={(file) => { handleUpload(file); return false; }}
            showUploadList={false}
            accept=".pdf,.docx,.txt,.md"
          >
            <Button type="primary" icon={<UploadOutlined />} loading={uploading}>
              上传文档
            </Button>
          </Upload>
          <Typography.Text type="secondary">支持 PDF / Word / TXT / Markdown</Typography.Text>
        </Space>
      </Card>

      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索文档..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            style={{ width: 300 }}
          />
          <Typography.Text type="secondary">共 {filteredDocs.length} 篇文档</Typography.Text>
        </Space>
        <Table
          columns={columns}
          dataSource={filteredDocs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 篇` }}
          locale={{ emptyText: <Empty description="暂无文档，上传第一篇吧" /> }}
        />
      </Card>

      {/* Edit Modal */}
      <Modal
        title="编辑文档信息"
        open={!!editDoc}
        onOk={handleEdit}
        onCancel={() => setEditDoc(null)}
        okText="保存"
        cancelText="取消"
      >
        {editDoc && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Typography.Text type="secondary">文件名</Typography.Text>
              <Input value={editDoc.filename} disabled />
            </div>
            <div>
              <Typography.Text type="secondary">标题</Typography.Text>
              <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
            </div>
            <div>
              <Typography.Text type="secondary">类别</Typography.Text>
              <Input value={editDoc.category}
                onChange={(e) => setEditDoc({ ...editDoc, category: e.target.value })} />
            </div>
            <div>
              <Typography.Text type="secondary">标签</Typography.Text>
              <Input value={editDoc.tags}
                onChange={(e) => setEditDoc({ ...editDoc, tags: e.target.value })} />
            </div>
          </Space>
        )}
      </Modal>

      {/* Versions Drawer */}
      <Drawer
        title={`版本历史 — ${versionsDoc?.filename || ''}`}
        open={versionsOpen}
        onClose={() => setVersionsOpen(false)}
        width={500}
      >
        {versions.length === 0 ? (
          <Empty description="暂无历史版本" />
        ) : (
          <List
            dataSource={versions}
            renderItem={(v: DocumentVersion) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Tag color="blue">v{v.version}</Tag>}
                  title={v.change_note || '无变更说明'}
                  description={
                    <Space direction="vertical" size={2}>
                      <span>大小: {formatSize(v.file_size)} | 分块: {v.chunk_count}</span>
                      <span>时间: {new Date(v.created_at).toLocaleString('zh-CN')}</span>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Drawer>
    </div>
  );
}
