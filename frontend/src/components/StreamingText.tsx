import { Spin } from 'antd';
import ReactMarkdown from 'react-markdown';

interface Props {
  text: string;
}

export default function StreamingText({ text }: Props) {
  if (!text) return <Spin size="small" />;

  return (
    <div style={{
      padding: '10px 16px',
      borderRadius: 14,
      background: '#e6f4ff',
      lineHeight: 1.7,
      fontSize: 14,
      wordBreak: 'break-word',
    }}>
      <ReactMarkdown>{text}</ReactMarkdown>
      <Spin size="small" style={{ marginLeft: 8 }} />
    </div>
  );
}
