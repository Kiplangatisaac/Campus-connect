import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import { SocketProvider } from './context/SocketContext';
import ErrorBoundary from './components/ErrorBoundary';
import KyUHeader from './components/KyUHeader';
import Sidebar from './components/Sidebar';
import InstallBanner from './components/InstallBanner';
import WelcomePage from './pages/WelcomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import GroupsPage from './pages/GroupsPage';
import BulletinPage from './pages/BulletinPage';
import EventsPage from './pages/EventsPage';
import ProfilePage from './pages/ProfilePage';
import AdminPage from './pages/AdminPage';
import SettingsPage from './pages/SettingsPage';
import MomentsPage from './pages/MomentsPage';
import CalendarPage from './pages/CalendarPage';
import BackupPage from './pages/BackupPage';
import SocialLoginCallback from './components/SocialLoginCallback';
import AIChatbot from './components/AIChatbot';
import AssistancePanel from './components/AssistancePanel';
import DownloadPage from './pages/DownloadPage';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen"><div className="spinner"></div></div>;
  return user ? children : <Navigate to="/login" />;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen"><div className="spinner"></div></div>;
  return user ? <Navigate to="/dashboard" /> : children;
}

function PrivateLayout({ children }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  return (
    <div className="app-layout">
      <KyUHeader />
      <div className="app-body">
        <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
        <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
          {children}
        </main>
      </div>
    </div>
  );
}

function AppRoutes() {
  return (
    <>
      <Routes>
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
        <Route path="/auth/callback/:provider" element={<SocialLoginCallback />} />
        <Route path="/dashboard" element={<PrivateRoute><PrivateLayout><DashboardPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/chat" element={<PrivateRoute><PrivateLayout><ChatPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/chat/:conversationId" element={<PrivateRoute><PrivateLayout><ChatPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/groups" element={<PrivateRoute><PrivateLayout><GroupsPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/bulletin" element={<PrivateRoute><PrivateLayout><BulletinPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/events" element={<PrivateRoute><PrivateLayout><EventsPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/profile" element={<PrivateRoute><PrivateLayout><ProfilePage /></PrivateLayout></PrivateRoute>} />
        <Route path="/profile/:userId" element={<PrivateRoute><PrivateLayout><ProfilePage /></PrivateLayout></PrivateRoute>} />
        <Route path="/admin" element={<PrivateRoute><PrivateLayout><AdminPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/admin/customize" element={<PrivateRoute><PrivateLayout><AdminPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/settings" element={<PrivateRoute><PrivateLayout><SettingsPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/moments" element={<PrivateRoute><PrivateLayout><MomentsPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/calendar" element={<PrivateRoute><PrivateLayout><CalendarPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/backup" element={<PrivateRoute><PrivateLayout><BackupPage /></PrivateLayout></PrivateRoute>} />
        <Route path="/downloads" element={<DownloadPage />} />
        <Route path="/" element={<Navigate to="/welcome" />} />
        <Route path="*" element={<Navigate to="/welcome" />} />
      </Routes>
      <AIChatbot />
      <AssistancePanel />
      <InstallBanner />
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ChatProvider>
            <SocketProvider>
              <AppRoutes />
              <ToastContainer position="bottom-right" autoClose={3000} />
            </SocketProvider>
          </ChatProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
