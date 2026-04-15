import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Button,
  Card,
  Row,
  Col,
  Typography,
  Space,
  Input,
  Select,
  message,
  Divider,
  Form,
  InputNumber,
  Switch,
  Alert,
} from 'antd';
import {
  InboxOutlined,
  ArrowRightOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import TablePreview from '../components/TablePreview';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { TextArea } = Input;

export default function UploadPage() {
  const navigate = useNavigate();
  const [table, setTable] = useState<any[][] | null>(null);
  const [filename, setFilename] = useState('');
  const [textInput, setTextInput] = useState('');
  const [textFormat, setTextFormat] = useState<'json' | 'markdown'>('json');
  const [loading, setLoading] = useState(false);

  const [config, setConfig] = useState({
    model_name: 'deepseek-v3-250324',
    model_type: 'oai',
    api_key: '',
    base_url: '',
    temperature: 0.3,
    tree_mode: 'normal',
    using_embedding: false,
    embedding_model_name: '',
    embedding_api_key: '',
    embedding_base_url: '',
  });

  const handleFileUpload = async (file: File) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/upload', { method: 'POST', body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setTable(data.table);
      setFilename(data.filename);
      message.success(`Loaded ${data.rows} rows × ${data.cols} columns`);
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setLoading(false);
    }
    return false;
  };

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/upload-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format: textFormat, content: textInput }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Parse failed');
      setTable(data.table);
      setFilename(`pasted.${textFormat}`);
      message.success(`Loaded ${data.rows} rows × ${data.cols} columns`);
    } catch (err: any) {
      message.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveConfigAndNavigate = async () => {
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      navigate('/build');
    } catch {
      navigate('/build');
    }
  };

  return (
    <div>
      <Title level={3}>Step 1: Upload & Preview Table</Title>
      <Paragraph type="secondary">
        Upload a table file or paste table content to begin. Supported formats: JSON (list-of-lists),
        XLSX, CSV, Markdown.
      </Paragraph>

      <Row gutter={24}>
        <Col span={12}>
          <Card title="Upload File" style={{ height: '100%' }}>
            <Dragger
              accept=".json,.xlsx,.csv,.md"
              showUploadList={false}
              beforeUpload={handleFileUpload}
              disabled={loading}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">Click or drag table file here</p>
              <p className="ant-upload-hint">.json, .xlsx, .csv, .md</p>
            </Dragger>

            <Divider>or paste content</Divider>

            <Space.Compact style={{ width: '100%' }}>
              <Select
                value={textFormat}
                onChange={setTextFormat}
                options={[
                  { value: 'json', label: 'JSON' },
                  { value: 'markdown', label: 'Markdown' },
                ]}
                style={{ width: 120 }}
              />
              <Button onClick={handleTextSubmit} loading={loading}>
                Parse
              </Button>
            </Space.Compact>
            <TextArea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={6}
              placeholder={
                textFormat === 'json'
                  ? '[["Name", "Age"], ["Alice", 30], ["Bob", 25]]'
                  : '| Name | Age |\n|------|-----|\n| Alice | 30 |'
              }
              style={{ marginTop: 8, fontFamily: 'monospace', fontSize: 12 }}
            />
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title={
              <Space>
                <SettingOutlined />
                <Text strong>Model Configuration</Text>
              </Space>
            }
            style={{ height: '100%' }}
          >
            <Form layout="vertical" size="small">
              <Form.Item label="API Key" required>
                <Input.Password
                  value={config.api_key}
                  onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                  placeholder="sk-..."
                  visibilityToggle
                />
              </Form.Item>
              <Form.Item label="Base URL" required>
                <Input
                  value={config.base_url}
                  onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                />
              </Form.Item>
              <Form.Item label="Model Name" required>
                <Input
                  value={config.model_name}
                  onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                  placeholder="gpt-4o / deepseek-v3-250324 / ..."
                />
              </Form.Item>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Temperature">
                    <InputNumber
                      value={config.temperature}
                      onChange={(v) => setConfig({ ...config, temperature: v ?? 0.3 })}
                      min={0}
                      max={2}
                      step={0.1}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Tree Mode">
                    <Select
                      value={config.tree_mode}
                      onChange={(v) => setConfig({ ...config, tree_mode: v })}
                      options={[
                        { value: 'normal', label: 'Normal' },
                        { value: 'enhanced', label: 'Enhanced (XLSX)' },
                      ]}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider style={{ margin: '12px 0' }} />

              <Form.Item label="Embedding Retrieval" style={{ marginBottom: config.using_embedding ? 12 : 0 }}>
                <Switch
                  checked={config.using_embedding}
                  onChange={(v) => setConfig({ ...config, using_embedding: v })}
                />
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  Use embedding model for path retrieval
                </Text>
              </Form.Item>
              {config.using_embedding && (
                <>
                  <Form.Item label="Embedding API Key">
                    <Input.Password
                      value={config.embedding_api_key}
                      onChange={(e) => setConfig({ ...config, embedding_api_key: e.target.value })}
                      placeholder="sk-... (defaults to main API Key if empty)"
                      visibilityToggle
                    />
                  </Form.Item>
                  <Form.Item label="Embedding Base URL">
                    <Input
                      value={config.embedding_base_url}
                      onChange={(e) => setConfig({ ...config, embedding_base_url: e.target.value })}
                      placeholder="https://api.openai.com/v1 (defaults to main Base URL if empty)"
                    />
                  </Form.Item>
                  <Form.Item label="Embedding Model Name">
                    <Input
                      value={config.embedding_model_name}
                      onChange={(e) => setConfig({ ...config, embedding_model_name: e.target.value })}
                      placeholder="text-embedding-3-small / ..."
                    />
                  </Form.Item>
                </>
              )}
            </Form>
          </Card>
        </Col>
      </Row>

      {table && (
        <>
          <Divider />
          <Card
            title={`Table Preview: ${filename}`}
            extra={
              <Button
                type="primary"
                icon={<ArrowRightOutlined />}
                onClick={saveConfigAndNavigate}
                size="large"
              >
                Build Tree
              </Button>
            }
          >
            <TablePreview table={table} maxHeight={350} />
          </Card>
        </>
      )}

      {!table && (
        <Alert
          message="Upload a table to get started"
          description="The table will be preprocessed into a unified list-of-lists format for tree construction."
          type="info"
          showIcon
          style={{ marginTop: 24 }}
        />
      )}
    </div>
  );
}
