import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { toast } from 'react-toastify';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [stats, setStats] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [, setLoading] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchUsers();
    fetchDepartments();
    fetchAuditLog();
  }, []);

  const fetchStats = async () => {
    try {
      const { data } = await api.get('/admin/stats');
      setStats(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/admin/users');
      setUsers(data.users || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const { data } = await api.get('/admin/departments');
      setDepartments(data.departments || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAuditLog = async () => {
    try {
      const { data } = await api.get('/admin/audit-log');
      setAuditLog(data.logs || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.put(`/admin/users/${userId}/role`, { role: newRole });
      setUsers(users.map(u => u._id === userId ? { ...u, role: newRole } : u));
      toast.success('Role updated');
    } catch (err) {
      toast.error('Failed to update role');
    }
  };

  const handleBanUser = async (userId, banned) => {
    try {
      await api.put(`/admin/users/${userId}/ban`, { banned: !banned });
      setUsers(users.map(u => u._id === userId ? { ...u, banned: !banned } : u));
      toast.success(banned ? 'User unbanned' : 'User banned');
    } catch (err) {
      toast.error('Failed to update user status');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      setUsers(users.filter(u => u._id !== userId));
      toast.success('User deleted');
    } catch (err) {
      toast.error('Failed to delete user');
    }
  };

  const filteredUsers = users.filter(u => {
    const matchesSearch = u.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         u.email?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const roleBadgeColors = {
    student: '#2196f3',
    moderator: '#4caf50',
    admin: '#f44336'
  };

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h2>Admin Panel</h2>
        <div className="admin-stats-row">
          <div className="admin-stat-card">
            <span className="admin-stat-value">{stats.totalUsers || 0}</span>
            <span className="admin-stat-label">Total Users</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-value">{stats.activeUsers || 0}</span>
            <span className="admin-stat-label">Active Today</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-value">{stats.totalMessages || 0}</span>
            <span className="admin-stat-label">Messages</span>
          </div>
          <div className="admin-stat-card">
            <span className="admin-stat-value">{stats.totalGroups || 0}</span>
            <span className="admin-stat-label">Groups</span>
          </div>
        </div>
      </div>

      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
        <button
          className={`admin-tab ${activeTab === 'departments' ? 'active' : ''}`}
          onClick={() => setActiveTab('departments')}
        >
          Departments
        </button>
        <button
          className={`admin-tab ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          Audit Log
        </button>
      </div>

      {activeTab === 'users' && (
        <div className="admin-users-section">
          <div className="admin-filters">
            <input
              type="text"
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="all">All Roles</option>
              <option value="student">Students</option>
              <option value="moderator">Moderators</option>
              <option value="admin">Admins</option>
            </select>
          </div>
          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(user => (
                  <tr key={user._id}>
                    <td>
                      <div className="admin-user-cell">
                        <img
                          src={user.avatar || `https://ui-avatars.com/api/?name=${user.name}&background=1a237e&color=fff`}
                          alt=""
                        />
                        <span>{user.name}</span>
                      </div>
                    </td>
                    <td>{user.email}</td>
                    <td>
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user._id, e.target.value)}
                        className="role-select"
                        style={{ borderColor: roleBadgeColors[user.role] }}
                      >
                        <option value="student">Student</option>
                        <option value="moderator">Moderator</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td>{user.department || '-'}</td>
                    <td>
                      <span className={`status-badge ${user.banned ? 'banned' : 'active'}`}>
                        {user.banned ? 'Banned' : 'Active'}
                      </span>
                    </td>
                    <td>
                      <div className="admin-actions">
                        <button
                          className="admin-btn ban"
                          onClick={() => handleBanUser(user._id, user.banned)}
                          title={user.banned ? 'Unban' : 'Ban'}
                        >
                          {user.banned ? '♻️' : '🚫'}
                        </button>
                        <button
                          className="admin-btn delete"
                          onClick={() => handleDeleteUser(user._id)}
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'departments' && (
        <div className="admin-departments-section">
          <div className="departments-grid">
            {departments.map(dept => (
              <div key={dept._id} className="department-card">
                <h4>{dept.name}</h4>
                <p>{dept.description}</p>
                <span className="dept-user-count">{dept.userCount || 0} users</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="admin-audit-section">
          <div className="audit-log">
            {auditLog.map((log, i) => (
              <div key={log._id || i} className="audit-entry">
                <span className="audit-action">{log.action}</span>
                <span className="audit-user">{log.user?.name}</span>
                <span className="audit-target">{log.target}</span>
                <span className="audit-time">{new Date(log.createdAt).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
