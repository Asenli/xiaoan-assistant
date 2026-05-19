/** 系统菜单路由映射管理 — CRUD + 树形展示 + 批量导入. */
import { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, InputNumber, Switch, Space, message,
  Card, Typography, Tag, Popconfirm, Tree, Empty, Tabs, Select,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, ApartmentOutlined,
  UnorderedListOutlined, ImportOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { listMenus, getMenuTree, createMenu, updateMenu, deleteMenu } from '@/api/client';
import type { MenuItem, MenuTreeNode } from '@/types';

export default function MenuMapping() {
  const [menus, setMenus] = useState<MenuItem[]>([]);
  const [tree, setTree] = useState<MenuTreeNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingMenu, setEditingMenu] = useState<MenuItem | null>(null);
  const [activeTab, setActiveTab] = useState('table');
  const [importText, setImportText] = useState('');
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [menuList, menuTree] = await Promise.all([listMenus(false), getMenuTree()]);
      setMenus(menuList);
      setTree(menuTree);
    } catch {
      message.error('获取菜单数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = () => {
    setEditingMenu(null);
    form.resetFields();
    form.setFieldsValue({ level: 0, sort_order: 0, is_visible: true, is_active: true });
    setModalOpen(true);
  };

  const handleEdit = (menu: MenuItem) => {
    setEditingMenu(menu);
    form.setFieldsValue(menu);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    try {
      if (editingMenu) {
        await updateMenu(editingMenu.id, values);
        message.success('菜单已更新');
      } else {
        await createMenu(values);
        message.success('菜单已创建');
      }
      setModalOpen(false);
      fetchData();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '操作失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMenu(id);
      message.success('已删除');
      fetchData();
    } catch { message.error('删除失败'); }
  };

  const handleImport = async () => {
    try {
      const items = JSON.parse(importText);
      if (!Array.isArray(items)) {
        message.error('请输入 JSON 数组格式');
        return;
      }
      // 简化处理 — 只导入第一个
      for (const item of items) {
        await createMenu(item);
      }
      message.success(`成功导入 ${items.length} 个菜单`);
      setImportModalOpen(false);
      setImportText('');
      fetchData();
    } catch (e: any) {
      message.error('导入失败: ' + (e.message || '格式错误'));
    }
  };

  const columns: ColumnsType<MenuItem> = [
    { title: '名称', dataIndex: 'name', key: 'name', width: 180, ellipsis: true },
    { title: '层级', dataIndex: 'level', key: 'level', width: 60,
      render: (v: number) => <Tag>{v}</Tag> },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 60 },
    { title: '路由', dataIndex: 'route_path', key: 'route_path', width: 180, ellipsis: true,
      render: (v: string) => v ? <Tag color="blue">{v}</Tag> : '-' },
    { title: '图标', dataIndex: 'icon', key: 'icon', width: 60 },
    { title: '关键词', dataIndex: 'keywords', key: 'keywords', width: 150, ellipsis: true },
    { title: '可见', dataIndex: 'is_visible', key: 'is_visible', width: 60,
      render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    { title: '启用', dataIndex: 'is_active', key: 'is_active', width: 60,
      render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
    { title: '说明', dataIndex: 'description', key: 'description', width: 200, ellipsis: true },
    {
      title: '操作', key: 'action', width: 120, fixed: 'right',
      render: (_: any, record: MenuItem) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="删除此菜单及其子菜单？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const renderTreeNodes = (nodes: MenuTreeNode[]): any[] =>
    nodes.map((node) => ({
      key: node.id,
      title: (
        <Space size={4}>
          <span>{node.icon || '📁'}</span>
          <span>{node.name}</span>
          {node.route_path && <Tag color="blue" style={{ fontSize: 10 }}>{node.route_path}</Tag>}
        </Space>
      ),
      children: node.children.length > 0 ? renderTreeNodes(node.children) : undefined,
    }));

  return (
    <div>
      <Typography.Title level={4}>菜单路由映射管理</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新增菜单</Button>
          <Button icon={<ImportOutlined />} onClick={() => setImportModalOpen(true)}>批量导入</Button>
          <Typography.Text type="secondary">
            配置系统菜单名称、层级、路由地址与业务说明的映射关系
          </Typography.Text>
        </Space>
      </Card>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
          {
            key: 'table',
            label: <span><UnorderedListOutlined /> 列表视图</span>,
            children: (
              <Table
                columns={columns}
                dataSource={menus}
                rowKey="id"
                loading={loading}
                scroll={{ x: 1200 }}
                pagination={{ pageSize: 50 }}
                locale={{ emptyText: <Empty description="暂无菜单，点击「新增菜单」开始配置" /> }}
              />
            ),
          },
          {
            key: 'tree',
            label: <span><ApartmentOutlined /> 树形视图</span>,
            children: tree.length === 0
              ? <Empty description="暂无菜单数据" />
              : <Tree treeData={renderTreeNodes(tree)} defaultExpandAll showLine />,
          },
        ]} />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingMenu ? '编辑菜单' : '新增菜单'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={640}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="菜单名称" rules={[{ required: true, message: '请输入' }]}>
            <Input placeholder="如：结算对账" />
          </Form.Item>
          <Form.Item name="parent_id" label="父菜单ID">
            <Input placeholder="留空为顶级菜单" />
          </Form.Item>
          <Space>
            <Form.Item name="level" label="层级">
              <InputNumber min={0} max={5} />
            </Form.Item>
            <Form.Item name="sort_order" label="排序">
              <InputNumber min={0} />
            </Form.Item>
          </Space>
          <Form.Item name="route_path" label="路由地址">
            <Input placeholder="如：/#/orderReconciliation" />
          </Form.Item>
          <Form.Item name="icon" label="图标">
            <Input placeholder="如：💰" />
          </Form.Item>
          <Form.Item name="description" label="简要描述">
            <Input.TextArea rows={2} placeholder="该菜单的功能简要说明" />
          </Form.Item>
          <Form.Item name="business_desc" label="业务说明">
            <Input.TextArea rows={3} placeholder="详细的业务操作说明" />
          </Form.Item>
          <Form.Item name="keywords" label="搜索关键词">
            <Input placeholder="逗号分隔，如：对账,结算,财务" />
          </Form.Item>
          <Form.Item name="related_knowledge_doc_ids" label="关联知识文档ID">
            <Input placeholder="逗号分隔的文档ID" />
          </Form.Item>
          <Space>
            <Form.Item name="is_visible" label="是否可见" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="is_active" label="是否启用" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>

      {/* Import Modal */}
      <Modal
        title="批量导入菜单"
        open={importModalOpen}
        onOk={handleImport}
        onCancel={() => setImportModalOpen(false)}
        width={600}
        okText="导入"
        cancelText="取消"
      >
        <Typography.Paragraph type="secondary">
          请粘贴 JSON 格式的菜单数组，每个元素包含 name, level, route_path, description 等字段。
        </Typography.Paragraph>
        <Input.TextArea
          rows={12}
          value={importText}
          onChange={(e) => setImportText(e.target.value)}
          placeholder={`[\n  {\n    "name": "财务管理",\n    "level": 0,\n    "route_path": "/#/finance",\n    "description": "财务管理模块",\n    "keywords": "财务,结算,对账",\n    "is_visible": true,\n    "is_active": true\n  }\n]`}
        />
      </Modal>
    </div>
  );
}
