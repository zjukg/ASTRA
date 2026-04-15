import { useState } from 'react';
import { Input, Button, List, Typography, Tag, Space, Card } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  metadata?: Record<string, any>;
}

interface Props {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  loading?: boolean;
  reasoningSteps?: React.ReactNode;
}

export default function ChatInterface({ messages, onSend, loading, reasoningSteps }: Props) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <List
          dataSource={messages}
          renderItem={(msg) => (
            <List.Item style={{ border: 'none', padding: '6px 0' }}>
              <Card
                size="small"
                style={{
                  width: '100%',
                  background: msg.role === 'user' ? '#e6f4ff' : '#f6ffed',
                  borderColor: msg.role === 'user' ? '#91caff' : '#b7eb8f',
                }}
              >
                <Space align="start">
                  <Tag
                    icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    color={msg.role === 'user' ? 'blue' : 'green'}
                  >
                    {msg.role === 'user' ? 'You' : 'ASTRA'}
                  </Tag>
                  <div>
                    <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </Paragraph>
                    {msg.metadata?.evidence_paths && (
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          Evidence paths: {msg.metadata.evidence_paths.length}
                        </Text>
                      </div>
                    )}
                  </div>
                </Space>
              </Card>
            </List.Item>
          )}
        />
        {reasoningSteps}
      </div>
      <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 12, display: 'flex', gap: 8 }}>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={handleSend}
          placeholder="Ask a question about the table..."
          disabled={loading}
          size="large"
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={loading}
          size="large"
        >
          Send
        </Button>
      </div>
    </div>
  );
}
