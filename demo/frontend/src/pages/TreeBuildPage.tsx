import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  Row,
  Col,
  Typography,
  Steps,
  Space,
  Tag,
  Alert,
  Divider,
  Descriptions,
} from 'antd';
import {
  PlayCircleOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import TablePreview from '../components/TablePreview';
import TreeVisualization from '../components/TreeVisualization';
import StepPanel from '../components/StepPanel';
import { useWebSocket } from '../hooks/useWebSocket';
import type { StepMessage } from '../types';

const { Title, Text, Paragraph } = Typography;

type StageStatus = 'pending' | 'running' | 'completed' | 'failed';

interface StageData {
  status: StageStatus;
  rawOutput?: string;
  data?: Record<string, any>;
}

export default function TreeBuildPage() {
  const navigate = useNavigate();
  const { messages, isConnected, isComplete, connect } = useWebSocket('/ws/build-tree');

  const [table, setTable] = useState<any[][] | null>(null);
  const [treeTable, setTreeTable] = useState<Record<string, any> | null>(null);
  const [building, setBuilding] = useState(false);

  const [stages, setStages] = useState<Record<string, StageData>>({
    header_normalization: { status: 'pending' },
    hierarchy_identification: { status: 'pending' },
    tree_construction: { status: 'pending' },
  });

  useEffect(() => {
    fetch('/api/session')
      .then((r) => r.json())
      .then((data) => {
        if (data.has_table && data.table) {
          setTable(data.table);
        }
        if (data.has_tree && data.tree_table) {
          setTreeTable(data.tree_table);
        }
      })
      .catch(() => null);
  }, []);

  useEffect(() => {
    for (const msg of messages) {
      const { stage, status, data } = msg;

      if (stage === 'error') {
        setBuilding(false);
        return;
      }

      if (['header_normalization', 'hierarchy_identification', 'tree_construction'].includes(stage)) {
        setStages((prev) => ({
          ...prev,
          [stage]: {
            status: status as StageStatus,
            rawOutput: data?.raw_output ?? prev[stage]?.rawOutput,
            data: data ?? prev[stage]?.data,
          },
        }));

        if (stage === 'tree_construction' && status === 'completed' && data?.tree_table) {
          setTreeTable(data.tree_table);
        }
      }
    }
  }, [messages]);

  useEffect(() => {
    if (isComplete) setBuilding(false);
  }, [isComplete]);

  const startBuild = async () => {
    setBuilding(true);
    setTreeTable(null);
    setStages({
      header_normalization: { status: 'pending' },
      hierarchy_identification: { status: 'pending' },
      tree_construction: { status: 'pending' },
    });

    const configRes = await fetch('/api/config');
    const config = await configRes.json();
    connect(config);
  };

  const currentStepIdx = useMemo(() => {
    const order = ['header_normalization', 'hierarchy_identification', 'tree_construction'];
    for (let i = order.length - 1; i >= 0; i--) {
      if (stages[order[i]].status !== 'pending') return i;
    }
    return 0;
  }, [stages]);

  const stageStepStatus = (s: StageStatus) => {
    if (s === 'completed') return 'finish';
    if (s === 'running') return 'process';
    if (s === 'failed') return 'error';
    return 'wait';
  };

  return (
    <div>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Step 2: Build Semantic Tree
        </Title>
        <Space>
          <Button
            type="primary"
            icon={building ? <LoadingOutlined /> : <PlayCircleOutlined />}
            onClick={startBuild}
            loading={building}
            size="large"
          >
            {building ? 'Building...' : 'Start Build'}
          </Button>
          {treeTable && (
            <Button
              type="primary"
              icon={<ArrowRightOutlined />}
              onClick={() => navigate('/qa')}
              size="large"
              ghost
            >
              Go to QA
            </Button>
          )}
        </Space>
      </Space>

      <Steps
        current={currentStepIdx}
        items={[
          {
            title: 'Header Normalization',
            status: stageStepStatus(stages.header_normalization.status),
            icon: stages.header_normalization.status === 'running' ? <LoadingOutlined /> : undefined,
          },
          {
            title: 'Hierarchy Identification',
            status: stageStepStatus(stages.hierarchy_identification.status),
            icon: stages.hierarchy_identification.status === 'running' ? <LoadingOutlined /> : undefined,
          },
          {
            title: 'Tree Construction',
            status: stageStepStatus(stages.tree_construction.status),
            icon: stages.tree_construction.status === 'running' ? <LoadingOutlined /> : undefined,
          },
        ]}
        style={{ marginBottom: 24 }}
      />

      <Row gutter={24}>
        <Col span={10}>
          <StepPanel
            title="Stage 1: Header Normalization"
            status={stages.header_normalization.status}
            rawOutput={stages.header_normalization.rawOutput}
          >
            {stages.header_normalization.status === 'completed' && (
              <Paragraph type="secondary" style={{ fontSize: 12 }}>
                Headers have been normalized by the LLM. Multi-level headers are combined
                using the format: [Lower-level] - [Upper-level].
              </Paragraph>
            )}
          </StepPanel>

          <StepPanel
            title="Stage 2: Hierarchy Identification"
            status={stages.hierarchy_identification.status}
            rawOutput={stages.hierarchy_identification.rawOutput}
          >
            {stages.hierarchy_identification.status === 'completed' && (
              <Paragraph type="secondary" style={{ fontSize: 12 }}>
                The LLM identified hierarchy keys, value leaves, and semantic groups
                from the table structure.
              </Paragraph>
            )}
          </StepPanel>

          <StepPanel
            title="Stage 3: Tree Construction"
            status={stages.tree_construction.status}
            rawOutput={stages.tree_construction.rawOutput}
          >
            {stages.tree_construction.status === 'completed' && (
              <Descriptions size="small" column={1}>
                <Descriptions.Item label="Root nodes">
                  {treeTable ? Object.keys(treeTable).length : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Status">
                  <Tag icon={<CheckCircleOutlined />} color="success">
                    Tree built successfully
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            )}
          </StepPanel>
        </Col>

        <Col span={14}>
          <Card title="Tree Visualization" style={{ minHeight: 500 }}>
            <TreeVisualization treeData={treeTable} height={500} />
          </Card>
        </Col>
      </Row>

      {!building && !treeTable && (
        <Alert
          message="Click 'Start Build' to begin tree construction"
          description="The pipeline will process the uploaded table through 3 stages: Header Normalization → Hierarchy Identification → Tree Construction. Each stage's intermediate results will be displayed in real-time."
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  );
}
