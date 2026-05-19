/** 操作步骤展示组件 — 可视化呈现操作步骤流程. */
import { Steps, Typography, Card } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import type { StepInfo } from '@/types';

interface Props {
  steps: StepInfo[];
}

export default function StepGuide({ steps }: Props) {
  if (!steps || steps.length === 0) return null;

  const items = steps.map((s, i) => ({
    title: `步骤 ${i + 1}`,
    description: s.step,
    status: 'process' as const,
  }));

  return (
    <Card
      size="small"
      title={
        <Typography.Text style={{ fontSize: 13 }}>
          <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 4 }} />
          操作步骤
        </Typography.Text>
      }
      bodyStyle={{ padding: '8px 12px' }}
      style={{ background: '#f6ffed', border: '1px solid #d9f7be' }}
    >
      <Steps
        direction="vertical"
        size="small"
        current={-1}
        items={items}
        style={{ fontSize: 12 }}
      />
    </Card>
  );
}
