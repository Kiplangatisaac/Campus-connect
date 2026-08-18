import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import api from '../services/api';

const providers = [
  { id: 'google_drive', name: 'Google Drive', icon: '📁', color: '#4285F4', connected: false },
  { id: 'onedrive', name: 'Microsoft OneDrive', icon: '☁️', color: '#0078D4', connected: false },
  { id: 'dropbox', name: 'Dropbox', icon: '📦', color: '#0061FF', connected: false },
];

export default function BackupPage() {
  const [cloudProviders, setCloudProviders] = useState(providers);
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [storageUsed, setStorageUsed] = useState(0);
  const [storageLimit, setStorageLimit] = useState(0);

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    try {
      const { data } = await api.get('/backup/list');
      setBackups(data.backups || []);
      setStorageUsed(data.storage_used || 0);
      setStorageLimit(data.storage_limit || 0);
    } catch {
      toast.error('Failed to load backups');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectProvider = async (providerId) => {
    try {
      const { data } = await api.post(`/backup/connect/${providerId}`);
      if (data.url) {
        window.location.href = data.url;
      } else {
        toast.success(`${providerId} connected successfully`);
        setCloudProviders(prev => prev.map(p =>
          p.id === providerId ? { ...p, connected: true } : p
        ));
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to connect');
    }
  };

  const handleDisconnectProvider = async (providerId) => {
    try {
      await api.post(`/backup/disconnect/${providerId}`);
      toast.success(`${providerId} disconnected`);
      setCloudProviders(prev => prev.map(p =>
        p.id === providerId ? { ...p, connected: false } : p
      ));
    } catch (err) {
      toast.error('Failed to disconnect');
    }
  };

  const handleCreateBackup = async (providerId) => {
    try {
      await api.post('/backup/upload', { provider: providerId });
      toast.success('Backup created successfully');
      loadBackups();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Backup failed');
    }
  };

  const handleRestore = async (backupId) => {
    if (!window.confirm('Are you sure you want to restore this backup?')) return;
    try {
      await api.post('/backup/restore', { backup_id: backupId });
      toast.success('Backup restored successfully');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Restore failed');
    }
  };

  const handleDeleteBackup = async (backupId) => {
    if (!window.confirm('Delete this backup?')) return;
    try {
      await api.delete(`/backup/${backupId}`);
      toast.success('Backup deleted');
      loadBackups();
    } catch (err) {
      toast.error('Failed to delete backup');
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Backup & Storage</h1>
        <p>Connect cloud storage and manage your backups</p>
      </div>

      <div className="settings-content">
        <div className="settings-section">
          <h2>Cloud Storage Providers</h2>
          <p className="section-subtitle">Connect a cloud storage service to enable automatic backups</p>

          <div className="cloud-providers-grid">
            {cloudProviders.map(provider => (
              <div key={provider.id} className="cloud-provider-card">
                <div className="provider-icon" style={{ backgroundColor: provider.color + '20', color: provider.color }}>
                  {provider.icon}
                </div>
                <div className="provider-info">
                  <h3>{provider.name}</h3>
                  <span className={`provider-status ${provider.connected ? 'connected' : ''}`}>
                    {provider.connected ? 'Connected' : 'Not connected'}
                  </span>
                </div>
                <div className="provider-actions">
                  {provider.connected ? (
                    <>
                      <button className="btn btn-primary btn-sm" onClick={() => handleCreateBackup(provider.id)}>
                        Backup Now
                      </button>
                      <button className="btn btn-outline btn-sm" onClick={() => handleDisconnectProvider(provider.id)}>
                        Disconnect
                      </button>
                    </>
                  ) : (
                    <button className="btn btn-primary btn-sm" onClick={() => handleConnectProvider(provider.id)}>
                      Connect
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="settings-section">
          <h2>Storage Overview</h2>
          <div className="storage-bar">
            <div className="storage-info">
              <span>{formatSize(storageUsed)} used</span>
              <span>{formatSize(storageLimit)} limit</span>
            </div>
            <div className="storage-progress">
              <div
                className="storage-fill"
                style={{ width: `${storageLimit > 0 ? (storageUsed / storageLimit) * 100 : 0}%` }}
              />
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h2>Recent Backups</h2>
          {loading ? (
            <div className="loading-state">Loading backups...</div>
          ) : backups.length === 0 ? (
            <div className="empty-state">
              <p>No backups yet. Connect a cloud storage provider and create your first backup.</p>
            </div>
          ) : (
            <div className="backup-list">
              {backups.map(backup => (
                <div key={backup.id} className="backup-item">
                  <div className="backup-info">
                    <h4>{backup.filename || `Backup ${backup.id}`}</h4>
                    <span className="backup-meta">
                      {formatSize(backup.size || 0)} • {formatDate(backup.created_at)} • {backup.provider}
                    </span>
                  </div>
                  <div className="backup-actions">
                    <button className="btn btn-outline btn-sm" onClick={() => handleRestore(backup.id)}>
                      Restore
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDeleteBackup(backup.id)}>
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
