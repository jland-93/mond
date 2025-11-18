/**
 * 🌙 Mond - Dashboard Page
 */

import React from 'react';
import { Row, Col, Card, Statistic, Progress, List, Tag, Typography, Space } from 'antd';
import {
  SecurityScanOutlined,
  TagsOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import styled from 'styled-components';

const { Title, Text } = Typography;

const DashboardContainer = styled.div`
  .dashboard-card {
    background: #1e293b;
    border: 1px solid #334155;
    
    .ant-card-head {
      border-bottom: 1px solid #334155;
    }
  }
  
  .metric-card {
    text-align: center;
    
    .ant-statistic-title {
      color: #94a3b8;
    }
    
    .ant-statistic-content {
      color: #ffffff;
    }
  }
`;

// Mock data for charts
const securityTrendData = [
  { date: '2024-01-01', score: 85 },
  { date: '2024-01-02', score: 87 },
  { date: '2024-01-03', score: 89 },
  { date: '2024-01-04', score: 91 },
  { date: '2024-01-05', score: 88 },
  { date: '2024-01-06', score: 92 },
  { date: '2024-01-07', score: 94 },
];

const tagComplianceData = [
  { name: 'Compliant', value: 78, color: '#10b981' },
  { name: 'Missing Tags', value: 15, color: '#f59e0b' },
  { name: 'Invalid Tags', value: 7, color: '#ef4444' },
];

const recentFindings = [
  {
    id: 1,
    title: 'S3 Bucket Public Read Access',
    severity: 'HIGH',
    resource: 'arn:aws:s3:::my-bucket',
    time: '2 hours ago',
  },
  {
    id: 2,
    title: 'EC2 Instance Missing Required Tags',
    severity: 'MEDIUM',
    resource: 'arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0',
    time: '4 hours ago',
  },
  {
    id: 3,
    title: 'IAM Policy Overly Permissive',
    severity: 'HIGH',
    resource: 'arn:aws:iam::123456789012:policy/MyPolicy',
    time: '6 hours ago',
  },
];

const Dashboard: React.FC = () => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return '#dc2626';
      case 'HIGH': return '#ea580c';
      case 'MEDIUM': return '#d97706';
      case 'LOW': return '#65a30d';
      default: return '#6b7280';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
      case 'HIGH':
        return <ExclamationCircleOutlined />;
      case 'MEDIUM':
        return <AlertOutlined />;
      case 'LOW':
        return <CheckCircleOutlined />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  return (
    <DashboardContainer>
      <Title level={2} style={{ color: '#ffffff', marginBottom: '24px' }}>
        🌙 Dashboard Overview
      </Title>

      {/* Key Metrics Row */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card metric-card">
            <Statistic
              title="Security Score"
              value={94}
              suffix="/100"
              prefix={<SecurityScanOutlined />}
              valueStyle={{ color: '#10b981' }}
            />
            <Progress
              percent={94}
              showInfo={false}
              strokeColor="#10b981"
              trailColor="#374151"
              size="small"
              style={{ marginTop: '8px' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card metric-card">
            <Statistic
              title="Tag Compliance"
              value={78}
              suffix="%"
              prefix={<TagsOutlined />}
              valueStyle={{ color: '#3b82f6' }}
            />
            <Progress
              percent={78}
              showInfo={false}
              strokeColor="#3b82f6"
              trailColor="#374151"
              size="small"
              style={{ marginTop: '8px' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card metric-card">
            <Statistic
              title="Active Findings"
              value={23}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#f59e0b' }}
            />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              ↓ 15% from last week
            </Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card metric-card">
            <Statistic
              title="Resources Monitored"
              value={1247}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#8b5cf6' }}
            />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Across 3 AWS accounts
            </Text>
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card 
            title="Security Score Trend" 
            className="dashboard-card"
            extra={<Text type="secondary">Last 7 days</Text>}
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={securityTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="date" 
                  stroke="#94a3b8"
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  stroke="#94a3b8"
                  tick={{ fontSize: 12 }}
                  domain={[80, 100]}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#3f51b5" 
                  strokeWidth={3}
                  dot={{ fill: '#3f51b5', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="Tag Compliance Breakdown" className="dashboard-card">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={tagComplianceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {tagComplianceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <Space direction="vertical" style={{ width: '100%', marginTop: '16px' }}>
              {tagComplianceData.map((item, index) => (
                <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space>
                    <div 
                      style={{ 
                        width: '12px', 
                        height: '12px', 
                        backgroundColor: item.color, 
                        borderRadius: '2px' 
                      }} 
                    />
                    <Text style={{ color: '#94a3b8' }}>{item.name}</Text>
                  </Space>
                  <Text style={{ color: '#ffffff' }}>{item.value}%</Text>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Recent Findings */}
      <Row gutter={[24, 24]}>
        <Col xs={24}>
          <Card title="Recent Security Findings" className="dashboard-card">
            <List
              dataSource={recentFindings}
              renderItem={(item) => (
                <List.Item
                  style={{ 
                    borderBottom: '1px solid #334155',
                    padding: '16px 0'
                  }}
                >
                  <List.Item.Meta
                    avatar={
                      <div style={{ color: getSeverityColor(item.severity), fontSize: '20px' }}>
                        {getSeverityIcon(item.severity)}
                      </div>
                    }
                    title={
                      <Space>
                        <Text style={{ color: '#ffffff' }}>{item.title}</Text>
                        <Tag color={getSeverityColor(item.severity)}>{item.severity}</Tag>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {item.resource}
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          <ClockCircleOutlined /> {item.time}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </DashboardContainer>
  );
};

export default Dashboard;
