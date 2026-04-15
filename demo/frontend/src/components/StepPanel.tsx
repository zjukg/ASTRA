import { Card, Tag, Typography, Collapse } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface Props {
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  children?: React.ReactNode;
  rawOutput?: string;
}

const statusConfig = {
  pending: { color: 'default', icon: null, text: 'Pending' },
  running: { color: 'processing', icon: <LoadingOutlined />, text: 'Running' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: 'Done' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: 'Failed' },
} as const;

export default function StepPanel({ title, status, children, rawOutput }: Props) {
  const cfg = statusConfig[status];

  return (
    <Card
      size="small"
      title={
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {cfg.icon}
          <Text strong>{title}</Text>
          <Tag color={cfg.color as string}>{cfg.text}</Tag>
        </span>
      }
      style={{ marginBottom: 12 }}
    >
      {children}
      {rawOutput && (
        <Collapse
          size="small"
          items={[
            {
              key: 'raw',
              label: <Text type="secondary">Raw LLM Output</Text>,
              children: (
                <Paragraph
                  code
                  style={{
                    maxHeight: 200,
                    overflow: 'auto',
                    fontSize: 12,
                    whiteSpace: 'pre-wrap',
                    margin: 0,
                  }}
                >
                  {rawOutput}
                </Paragraph>
              ),
            },
          ]}
        />
      )}
    </Card>
  );
}
