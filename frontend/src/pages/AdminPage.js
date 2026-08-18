import React from 'react';
import AdminPanel from '../components/AdminPanel';
import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import '../styles/admin.css';

export default function AdminPage() {
  const { user } = useAuth();

  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" />;
  }

  return (
    <AdminPanel />
  );
}
