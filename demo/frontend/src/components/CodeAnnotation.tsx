import { Card, Tag, Typography, Alert } from 'antd';
import { CodeOutlined } from '@ant-design/icons';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';

SyntaxHighlighter.registerLanguage('python', python);

const { Text } = Typography;

interface Props {
  code: string | null;
  answer?: any;
  error?: string | null;
  attempts?: number;
}

export default function CodeAnnotation({ code, answer, error, attempts }: Props) {
  return (
    <Card
      size="small"
      title={
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CodeOutlined />
          <Text strong>Symbolic Tree Manipulation</Text>
          {attempts && <Tag color="purple">Attempt {attempts}</Tag>}
        </span>
      }
      style={{ marginBottom: 12 }}
    >
      {code && (
        <SyntaxHighlighter
          language="python"
          style={vs2015}
          customStyle={{ borderRadius: 6, fontSize: 13, maxHeight: 300 }}
        >
          {code}
        </SyntaxHighlighter>
      )}
      {answer !== undefined && answer !== null && (
        <Alert
          message={`Result: ${JSON.stringify(answer)}`}
          type="success"
          showIcon
          style={{ marginTop: 8 }}
        />
      )}
      {error && (
        <Alert message={error} type="error" showIcon style={{ marginTop: 8 }} />
      )}
    </Card>
  );
}
