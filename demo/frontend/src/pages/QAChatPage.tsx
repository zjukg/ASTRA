import { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Tag,
  Timeline,
  Alert,
  Switch,
  Divider,
  Badge,
} from 'antd';
import {
  SearchOutlined,
  CompassOutlined,
  ApartmentOutlined,
  CodeOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import TreeVisualization from '../components/TreeVisualization';
import ChatInterface from '../components/ChatInterface';
import CodeAnnotation from '../components/CodeAnnotation';
import StepPanel from '../components/StepPanel';
import { useWebSocket } from '../hooks/useWebSocket';
import type { StepMessage, NavigationStep } from '../types';

const { Title, Text, Paragraph } = Typography;

interface ChatMsg {
  role: 'user' | 'assistant';
  content: string;
  metadata?: Record<string, any>;
}

export default function QAChatPage() {
  const { messages: wsMessages, isComplete, connect } = useWebSocket('/ws/qa');

  const [treeTable, setTreeTable] = useState<Record<string, any> | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const [loading, setLoading] = useState(false);
  const [enableSymbolic, setEnableSymbolic] = useState(true);

  const [embeddingNodes, setEmbeddingNodes] = useState<any[]>([]);
  const [guidePath, setGuidePath] = useState('');
  const [navSteps, setNavSteps] = useState<NavigationStep[]>([]);
  const [currentNavStep, setCurrentNavStep] = useState<NavigationStep | null>(null);
  const [relevantPaths, setRelevantPaths] = useState<string[][]>([]);
  const [symbolicCode, setSymbolicCode] = useState<string | null>(null);
  const [symbolicAnswer, setSymbolicAnswer] = useState<any>(null);
  const [symbolicError, setSymbolicError] = useState<string | null>(null);
  const [symbolicAttempts, setSymbolicAttempts] = useState(0);

  useEffect(() => {
    fetch('/api/session')
      .then((r) => r.json())
      .then((data) => {
        if (data.has_tree && data.tree_table) {
          setTreeTable(data.tree_table);
        }
      })
      .catch(() => null);
  }, []);

  useEffect(() => {
    const lastMsg = wsMessages[wsMessages.length - 1];
    if (!lastMsg) return;

    const { stage, status, data } = lastMsg;

    if (stage === 'embedding_retrieval' && status === 'completed' && data?.top_k_nodes) {
      setEmbeddingNodes(data.top_k_nodes);
    }

    if (stage === 'plan_path_guide' && status === 'completed' && data?.guide_text) {
      setGuidePath(data.guide_text);
    }

    if (stage === 'tree_navigation_step' && data) {
      const step = data as NavigationStep;
      setNavSteps((prev) => [...prev, step]);
      setCurrentNavStep(step);
    }

    if (stage === 'tree_navigation' && status === 'completed' && data?.relevant_paths) {
      setRelevantPaths(data.relevant_paths);
      setCurrentNavStep(null);
    }

    if (stage === 'final_answer' && status === 'completed' && data?.answer) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          metadata: { evidence_paths: data.evidence_paths },
        },
      ]);
    }

    if (stage === 'symbolic_reasoning' && status === 'completed' && data) {
      setSymbolicCode(data.generated_code);
      setSymbolicAnswer(data.answer);
      setSymbolicAttempts(data.attempts);
    }

    if (stage === 'symbolic_attempt' && data) {
      if (data.code) setSymbolicCode(data.code);
      if (data.error) setSymbolicError(data.error);
    }

    if (stage === 'symbolic_reasoning' && status === 'failed' && data) {
      setSymbolicError(data.error);
      setSymbolicCode(data.last_code);
    }
  }, [wsMessages]);

  useEffect(() => {
    if (isComplete) setLoading(false);
  }, [isComplete]);

  const highlightedNodes = useMemo(() => {
    const nodes = new Set<string>();
    embeddingNodes.forEach((n: any) => nodes.add(n.key));
    return nodes;
  }, [embeddingNodes]);

  const handleSend = async (question: string) => {
    setChatMessages((prev) => [...prev, { role: 'user', content: question }]);
    setLoading(true);
    setEmbeddingNodes([]);
    setGuidePath('');
    setNavSteps([]);
    setCurrentNavStep(null);
    setRelevantPaths([]);
    setSymbolicCode(null);
    setSymbolicAnswer(null);
    setSymbolicError(null);
    setSymbolicAttempts(0);

    const configRes = await fetch('/api/config');
    const config = await configRes.json();
    connect({
      question,
      ...config,
      enable_symbolic: enableSymbolic,
    });
  };

  const reasoningSteps = (
    <div style={{ marginTop: 12 }}>
      {loading && (
        <Card size="small" title="Reasoning Process" style={{ marginBottom: 12 }}>
          <Timeline
            items={[
              {
                color: embeddingNodes.length > 0 ? 'green' : loading ? 'blue' : 'gray',
                dot: embeddingNodes.length > 0 ? <CheckCircleOutlined /> : loading ? <LoadingOutlined /> : undefined,
                children: (
                  <Space>
                    <SearchOutlined />
                    <Text>Embedding Retrieval</Text>
                    {embeddingNodes.length > 0 && (
                      <Tag color="green">{embeddingNodes.length} nodes found</Tag>
                    )}
                  </Space>
                ),
              },
              {
                color: guidePath ? 'green' : navSteps.length > 0 ? 'blue' : 'gray',
                dot: guidePath ? <CheckCircleOutlined /> : undefined,
                children: (
                  <div>
                    <Space>
                      <CompassOutlined />
                      <Text>Path Planning</Text>
                    </Space>
                    {guidePath && (
                      <Paragraph
                        type="secondary"
                        style={{ fontSize: 12, marginTop: 4, maxHeight: 100, overflow: 'auto' }}
                        ellipsis={{ rows: 3, expandable: true }}
                      >
                        {guidePath}
                      </Paragraph>
                    )}
                  </div>
                ),
              },
              {
                color: relevantPaths.length > 0 ? 'green' : navSteps.length > 0 ? 'blue' : 'gray',
                dot:
                  relevantPaths.length > 0 ? (
                    <CheckCircleOutlined />
                  ) : navSteps.length > 0 ? (
                    <LoadingOutlined />
                  ) : undefined,
                children: (
                  <div>
                    <Space>
                      <ApartmentOutlined />
                      <Text>Adaptive Tree Navigation</Text>
                      {navSteps.length > 0 && (
                        <Tag color="blue">{navSteps.length} steps</Tag>
                      )}
                    </Space>
                    {currentNavStep && (
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          At node: <Tag>{currentNavStep.current_node}</Tag>
                        </Text>
                        <div>
                          {currentNavStep.selected_children.map((c) => (
                            <Tag color="green" key={c} style={{ fontSize: 11, margin: 2 }}>
                              {c}
                            </Tag>
                          ))}
                          {currentNavStep.rejected_children.map((c) => (
                            <Tag color="default" key={c} style={{ fontSize: 11, margin: 2, opacity: 0.5 }}>
                              {c}
                            </Tag>
                          ))}
                        </div>
                      </div>
                    )}
                    {relevantPaths.length > 0 && (
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          Found {relevantPaths.length} evidence paths
                        </Text>
                      </div>
                    )}
                  </div>
                ),
              },
              ...(enableSymbolic
                ? [
                    {
                      color:
                        symbolicAnswer !== null
                          ? 'green'
                          : symbolicError
                            ? 'red'
                            : symbolicCode
                              ? 'blue'
                              : ('gray' as const),
                      dot:
                        symbolicAnswer !== null ? (
                          <CheckCircleOutlined />
                        ) : symbolicError && !symbolicCode ? (
                          <CloseCircleOutlined />
                        ) : undefined,
                      children: (
                        <Space>
                          <CodeOutlined />
                          <Text>Symbolic Reasoning</Text>
                          {symbolicAttempts > 0 && (
                            <Tag color="purple">
                              {symbolicAttempts} attempt{symbolicAttempts > 1 ? 's' : ''}
                            </Tag>
                          )}
                        </Space>
                      ),
                    },
                  ]
                : []),
            ]}
          />
        </Card>
      )}

      {symbolicCode && (
        <CodeAnnotation
          code={symbolicCode}
          answer={symbolicAnswer}
          error={symbolicError}
          attempts={symbolicAttempts}
        />
      )}
    </div>
  );

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Step 3: Question Answering
        </Title>
        <Space>
          <Text type="secondary">Symbolic Reasoning:</Text>
          <Switch checked={enableSymbolic} onChange={setEnableSymbolic} />
        </Space>
      </Space>

      <Row gutter={24}>
        <Col span={12}>
          <Card
            title={
              <Space>
                <ApartmentOutlined />
                <Text strong>Semantic Tree</Text>
                {navSteps.length > 0 && (
                  <Badge
                    count={navSteps.length}
                    style={{ backgroundColor: '#1677ff' }}
                  />
                )}
              </Space>
            }
            style={{ height: 'calc(100vh - 200px)', overflow: 'hidden' }}
          >
            <TreeVisualization
              treeData={treeTable}
              highlightedNodes={highlightedNodes}
              highlightedPaths={relevantPaths}
              navigationStep={currentNavStep}
              height={500}
            />
            {embeddingNodes.length > 0 && (
              <>
                <Divider style={{ margin: '12px 0' }} />
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Top-K Embedding Matches:
                  </Text>
                  <div style={{ marginTop: 4 }}>
                    {embeddingNodes.map((n: any, i: number) => (
                      <Tag color="gold" key={i} style={{ marginBottom: 4 }}>
                        {n.key} ({n.score})
                      </Tag>
                    ))}
                  </div>
                </div>
              </>
            )}
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title="Chat"
            style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
          >
            <ChatInterface
              messages={chatMessages}
              onSend={handleSend}
              loading={loading}
              reasoningSteps={reasoningSteps}
            />
          </Card>
        </Col>
      </Row>

      {!treeTable && (
        <Alert
          message="Build a tree first"
          description="Please go to the Build Tree step first to construct a semantic tree before asking questions."
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  );
}
