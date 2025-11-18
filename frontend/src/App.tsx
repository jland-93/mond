/**
 * 🌙 Mond - Main Application Component
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from 'react-query';

import { store } from '@/store';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import TagManagement from '@/pages/TagManagement';
import Security from '@/pages/Security';
import Settings from '@/pages/Settings';

import '@/assets/styles/global.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Mond theme configuration
const mondTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#3f51b5',
    colorBgBase: '#0d1421',
    colorBgContainer: '#1e293b',
    colorText: '#ffffff',
    colorTextSecondary: '#64748b',
    borderRadius: 8,
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  components: {
    Layout: {
      bodyBg: '#0d1421',
      headerBg: '#1e293b',
      siderBg: '#1e293b',
    },
    Card: {
      colorBgContainer: '#1e293b',
    },
    Button: {
      primaryShadow: '0 2px 8px rgba(63, 81, 181, 0.3)',
    },
  },
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={mondTheme}>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/tags" element={<TagManagement />} />
                <Route path="/security" element={<Security />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </Router>
        </ConfigProvider>
      </QueryClientProvider>
    </Provider>
  );
};

export default App;
