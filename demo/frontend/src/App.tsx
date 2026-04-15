import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Steps, Typography, theme } from 'antd';
import { CloudUploadOutlined, ApartmentOutlined, MessageOutlined } from '@ant-design/icons';
import UploadPage from './pages/UploadPage';
import TreeBuildPage from './pages/TreeBuildPage';
import QAChatPage from './pages/QAChatPage';

const { Header, Content } = Layout;
const { Title } = Typography;

const stepItems = [
  { title: 'Upload Table', icon: <CloudUploadOutlined /> },
  { title: 'Build Tree', icon: <ApartmentOutlined /> },
  { title: 'Ask Questions', icon: <MessageOutlined /> },
];

const pathToStep: Record<string, number> = {
  '/': 0,
  '/build': 1,
  '/qa': 2,
};

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();
  const currentStep = pathToStep[location.pathname] ?? 0;

  return (
    <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
      <Header
        style={{
          background: '#fff',
          padding: '0 32px',
          display: 'flex',
          alignItems: 'center',
          gap: 32,
          boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <Title level={4} style={{ margin: 0, whiteSpace: 'nowrap', color: token.colorPrimary }}>
          🌳 ASTRA
        </Title>
        <Steps
          current={currentStep}
          items={stepItems}
          size="small"
          style={{ maxWidth: 560 }}
          onChange={(step) => {
            const paths = ['/', '/build', '/qa'];
            navigate(paths[step]);
          }}
        />
      </Header>
      <Content style={{ padding: '24px 32px', maxWidth: 1400, margin: '0 auto', width: '100%' }}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/build" element={<TreeBuildPage />} />
          <Route path="/qa" element={<QAChatPage />} />
        </Routes>
      </Content>
    </Layout>
  );
}
