import React, { useState, useEffect, useCallback } from 'react';
import {
  FiPalette, FiUpload, FiLayout, FiMegaphone, FiUsers, FiShield,
  FiSettings, FiBarChart2, FiDatabase, FiCalendar, FiUserPlus,
  FiTrash2, FiEdit, FiPlus, FiSave, FiX, FiCheck, FiAlertTriangle,
  FiEye, FiEyeOff, FiLock, FiUnlock, FiDownload, FiRefreshCw,
  FiChevronDown, FiChevronRight, FiSearch, FiFlag, FiClock, FiGlobe
} from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import './AdminCustomization.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
};

const ColorPicker = ({ value, onChange, label }) => (
  <div className="admin-color-picker">
    {label && <label>{label}</label>}
    <div className="color-input-row">
      <input type="color" value={value} onChange={e => onChange(e.target.value)} />
      <input type="text" value={value} onChange={e => onChange(e.target.value)} placeholder="#000000" />
    </div>
  </div>
);

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <motion.div
      className="admin-modal-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="admin-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={e => e.stopPropagation()}
      >
        <div className="admin-modal-header">
          <h3>{title}</h3>
          <button onClick={onClose} className="admin-modal-close"><FiX /></button>
        </div>
        <div className="admin-modal-body">{children}</div>
      </motion.div>
    </motion.div>
  );
};

const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, message }) => (
  <Modal isOpen={isOpen} onClose={onClose} title={title || 'Confirm'}>
    <p className="admin-confirm-msg">{message}</p>
    <div className="admin-confirm-actions">
      <button className="admin-btn admin-btn-danger" onClick={onConfirm}>Confirm</button>
      <button className="admin-btn admin-btn-secondary" onClick={onClose}>Cancel</button>
    </div>
  </Modal>
);

const TabPanel = ({ tabs, activeTab, onTabChange }) => (
  <div className="admin-tabs">
    {tabs.map(tab => (
      <button
        key={tab.id}
        className={`admin-tab ${activeTab === tab.id ? 'active' : ''}`}
        onClick={() => onTabChange(tab.id)}
      >
        <tab.icon /> {tab.label}
      </button>
    ))}
  </div>
);

// ── Theme Manager ──
const ThemeManager = () => {
  const [themes, setThemes] = useState([]);
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: '', primaryColor: '#1a73e8', secondaryColor: '#34a853',
    bgColor: '#ffffff', textColor: '#202124', accentColor: '#fbbc04',
    chatBubbleColor: '#1a73e8', headerColor: '#1a73e8'
  });

  const loadThemes = useCallback(async () => {
    try {
      const data = await apiCall('/admin/themes');
      setThemes(data.themes || []);
    } catch { setThemes([]); }
  }, []);

  useEffect(() => { loadThemes(); }, [loadThemes]);

  const handleSave = async () => {
    try {
      if (editing) {
        await apiCall(`/admin/themes/${editing._id}`, { method: 'PUT', body: JSON.stringify(form) });
      } else {
        await apiCall('/admin/themes', { method: 'POST', body: JSON.stringify(form) });
      }
      setShowForm(false);
      setEditing(null);
      setForm({ name: '', primaryColor: '#1a73e8', secondaryColor: '#34a853', bgColor: '#ffffff', textColor: '#202124', accentColor: '#fbbc04', chatBubbleColor: '#1a73e8', headerColor: '#1a73e8' });
      loadThemes();
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id) => {
    try {
      await apiCall(`/admin/themes/${id}`, { method: 'DELETE' });
      loadThemes();
    } catch (err) { console.error(err); }
  };

  const startEdit = (theme) => {
    setEditing(theme);
    setForm({ ...theme });
    setShowForm(true);
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3>Theme Manager</h3>
        <button className="admin-btn admin-btn-primary" onClick={() => { setEditing(null); setShowForm(true); }}>
          <FiPlus /> Create Theme
        </button>
      </div>

      <div className="admin-theme-grid">
        {themes.map(theme => (
          <div key={theme._id} className="admin-theme-card">
            <div className="theme-preview">
              <div style={{ background: theme.primaryColor, height: 30, borderRadius: '8px 8px 0 0' }} />
              <div style={{ background: theme.bgColor, padding: 12 }}>
                <div style={{ width: '60%', height: 10, background: theme.textColor, borderRadius: 4, marginBottom: 6, opacity: 0.3 }} />
                <div style={{ background: theme.chatBubbleColor, color: '#fff', padding: '6px 12px', borderRadius: 12, fontSize: 11, width: '70%', textAlign: 'center' }}>Message</div>
              </div>
            </div>
            <div className="theme-card-footer">
              <span className="theme-name">{theme.name}</span>
              <div className="theme-actions">
                <button onClick={() => startEdit(theme)} className="admin-icon-btn"><FiEdit /></button>
                <button onClick={() => handleDelete(theme._id)} className="admin-icon-btn admin-icon-danger"><FiTrash2 /></button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <AnimatePresence>
        <Modal isOpen={showForm} onClose={() => { setShowForm(false); setEditing(null); }} title={editing ? 'Edit Theme' : 'Create Theme'}>
          <div className="admin-form">
            <div className="admin-form-group">
              <label>Theme Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="My Custom Theme" />
            </div>
            <ColorPicker label="Primary Color" value={form.primaryColor} onChange={v => setForm({ ...form, primaryColor: v })} />
            <ColorPicker label="Secondary Color" value={form.secondaryColor} onChange={v => setForm({ ...form, secondaryColor: v })} />
            <ColorPicker label="Background Color" value={form.bgColor} onChange={v => setForm({ ...form, bgColor: v })} />
            <ColorPicker label="Text Color" value={form.textColor} onChange={v => setForm({ ...form, textColor: v })} />
            <ColorPicker label="Accent Color" value={form.accentColor} onChange={v => setForm({ ...form, accentColor: v })} />
            <ColorPicker label="Chat Bubble Color" value={form.chatBubbleColor} onChange={v => setForm({ ...form, chatBubbleColor: v })} />
            <ColorPicker label="Header Color" value={form.headerColor} onChange={v => setForm({ ...form, headerColor: v })} />
            <div className="admin-form-actions">
              <button className="admin-btn admin-btn-primary" onClick={handleSave}><FiSave /> {editing ? 'Update' : 'Create'}</button>
              <button className="admin-btn admin-btn-secondary" onClick={() => { setShowForm(false); setEditing(null); }}>Cancel</button>
            </div>
          </div>
        </Modal>
      </AnimatePresence>
    </div>
  );
};

// ── Logo & Branding ──
const LogoBranding = () => {
  const [branding, setBranding] = useState({ logo: '', favicon: '', appName: 'KyU Campus Connect', tagline: '' });
  const [preview, setPreview] = useState({ logo: '', favicon: '' });

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiCall('/admin/branding');
        setBranding(data.branding || branding);
      } catch {}
    };
    load();
  }, []);

  const handleUpload = async (field, file) => {
    const reader = new FileReader();
    reader.onload = (e) => setPreview(p => ({ ...p, [field]: e.target.result }));
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE}/admin/branding/upload/${field}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      setBranding(b => ({ ...b, [field]: data.url }));
    } catch (err) { console.error(err); }
  };

  const handleSave = async () => {
    try {
      await apiCall('/admin/branding', { method: 'PUT', body: JSON.stringify(branding) });
    } catch (err) { console.error(err); }
  };

  return (
    <div className="admin-section">
      <h3>Logo & Branding</h3>
      <div className="admin-form">
        <div className="admin-form-group">
          <label>App Name</label>
          <input value={branding.appName} onChange={e => setBranding({ ...branding, appName: e.target.value })} />
        </div>
        <div className="admin-form-group">
          <label>Tagline</label>
          <input value={branding.tagline} onChange={e => setBranding({ ...branding, tagline: e.target.value })} placeholder="Your campus, connected." />
        </div>
        <div className="admin-upload-group">
          <label>Logo</label>
          <div className="admin-upload-area">
            {(preview.logo || branding.logo) && <img src={preview.logo || branding.logo} alt="Logo" className="upload-preview" />}
            <label className="admin-upload-btn">
              <FiUpload /> Upload Logo
              <input type="file" accept="image/*" hidden onChange={e => handleUpload('logo', e.target.files[0])} />
            </label>
          </div>
        </div>
        <div className="admin-upload-group">
          <label>Favicon</label>
          <div className="admin-upload-area">
            {(preview.favicon || branding.favicon) && <img src={preview.favicon || branding.favicon} alt="Favicon" className="upload-preview small" />}
            <label className="admin-upload-btn">
              <FiUpload /> Upload Favicon
              <input type="file" accept="image/*" hidden onChange={e => handleUpload('favicon', e.target.files[0])} />
            </label>
          </div>
        </div>
        <button className="admin-btn admin-btn-primary" onClick={handleSave}><FiSave /> Save Branding</button>
      </div>
    </div>
  );
};

// ── Dashboard Layout ──
const DashboardLayout = () => {
  const defaultWidgets = [
    { id: 'announcements', label: 'Announcements', enabled: true },
    { id: 'users', label: 'User Stats', enabled: true },
    { id: 'messages', label: 'Message Stats', enabled: true },
    { id: 'storage', label: 'Storage Usage', enabled: true },
    { id: 'recent-activity', label: 'Recent Activity', enabled: true },
    { id: 'calendar', label: 'Calendar', enabled: false },
    { id: 'analytics', label: 'Analytics Chart', enabled: true },
    { id: 'notifications', label: 'Notifications', enabled: true },
  ];

  const [widgets, setWidgets] = useState(defaultWidgets);
  const [draggedIdx, setDraggedIdx] = useState(null);

  const handleDragStart = (idx) => setDraggedIdx(idx);
  const handleDragOver = (e, idx) => {
    e.preventDefault();
    if (draggedIdx === null) return;
    const updated = [...widgets];
    const [dragged] = updated.splice(draggedIdx, 1);
    updated.splice(idx, 0, dragged);
    setWidgets(updated);
    setDraggedIdx(idx);
  };

  const toggleWidget = (id) => {
    setWidgets(ws => ws.map(w => w.id === id ? { ...w, enabled: !w.enabled } : w));
  };

  const saveLayout = async () => {
    try {
      await apiCall('/admin/dashboard-layout', { method: 'PUT', body: JSON.stringify({ widgets }) });
    } catch (err) { console.error(err); }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3>Dashboard Layout</h3>
        <button className="admin-btn admin-btn-primary" onClick={saveLayout}><FiSave /> Save Layout</button>
      </div>
      <p className="admin-hint">Drag to reorder widgets. Toggle visibility on/off.</p>
      <div className="admin-widget-list">
        {widgets.map((widget, idx) => (
          <div
            key={widget.id}
            className={`admin-widget-item ${widget.enabled ? 'enabled' : 'disabled'}`}
            draggable
            onDragStart={() => handleDragStart(idx)}
            onDragOver={(e) => handleDragOver(e, idx)}
            onDragEnd={() => setDraggedIdx(null)}
          >
            <span className="drag-handle">⋮⋮</span>
            <FiLayout className="widget-icon" />
            <span className="widget-label">{widget.label}</span>
            <button className="admin-icon-btn" onClick={() => toggleWidget(widget.id)}>
              {widget.enabled ? <FiEye /> : <FiEyeOff />}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Announcement Manager ──
const AnnouncementManager = () => {
  const [announcements, setAnnouncements] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', content: '', type: 'info', pinned: false, urgent: false });

  const loadAnnouncements = useCallback(async () => {
    try {
      const data = await apiCall('/admin/announcements');
      setAnnouncements(data.announcements || []);
    } catch { setAnnouncements([]); }
  }, []);

  useEffect(() => { loadAnnouncements(); }, [loadAnnouncements]);

  const handleSave = async () => {
    try {
      await apiCall('/admin/announcements', { method: 'POST', body: JSON.stringify(form) });
      setShowForm(false);
      setForm({ title: '', content: '', type: 'info', pinned: false, urgent: false });
      loadAnnouncements();
    } catch (err) { console.error(err); }
  };

  const togglePin = async (id, pinned) => {
    try {
      await apiCall(`/admin/announcements/${id}`, { method: 'PUT', body: JSON.stringify({ pinned: !pinned }) });
      loadAnnouncements();
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id) => {
    try {
      await apiCall(`/admin/announcements/${id}`, { method: 'DELETE' });
      loadAnnouncements();
    } catch (err) { console.error(err); }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3>Announcements</h3>
        <button className="admin-btn admin-btn-primary" onClick={() => setShowForm(true)}><FiPlus /> New Announcement</button>
      </div>

      <div className="admin-announcement-list">
        {announcements.map(a => (
          <div key={a._id} className={`admin-announcement-card ${a.urgent ? 'urgent' : ''} ${a.pinned ? 'pinned' : ''}`}>
            <div className="announcement-header">
              <span className={`announcement-type type-${a.type}`}>{a.type}</span>
              {a.urgent && <span className="urgent-badge"><FiAlertTriangle /> Urgent</span>}
              {a.pinned && <span className="pinned-badge">📌 Pinned</span>}
            </div>
            <h4>{a.title}</h4>
            <p>{a.content}</p>
            <div className="announcement-footer">
              <span className="announcement-date"><FiClock /> {new Date(a.createdAt).toLocaleDateString()}</span>
              <div className="announcement-actions">
                <button className="admin-icon-btn" onClick={() => togglePin(a._id, a.pinned)} title={a.pinned ? 'Unpin' : 'Pin'}>📌</button>
                <button className="admin-icon-btn admin-icon-danger" onClick={() => handleDelete(a._id)}><FiTrash2 /></button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <AnimatePresence>
        <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="New Announcement">
          <div className="admin-form">
            <div className="admin-form-group">
              <label>Title</label>
              <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Announcement title" />
            </div>
            <div className="admin-form-group">
              <label>Content</label>
              <textarea rows={4} value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} placeholder="Announcement content..." />
            </div>
            <div className="admin-form-group">
              <label>Type</label>
              <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="success">Success</option>
                <option value="error">Error</option>
              </select>
            </div>
            <div className="admin-checkbox-row">
              <label>
                <input type="checkbox" checked={form.pinned} onChange={e => setForm({ ...form, pinned: e.target.checked })} /> Pin this announcement
              </label>
              <label>
                <input type="checkbox" checked={form.urgent} onChange={e => setForm({ ...form, urgent: e.target.checked })} /> Mark as urgent
              </label>
            </div>
            <div className="admin-form-actions">
              <button className="admin-btn admin-btn-primary" onClick={handleSave}><FiSave /> Publish</button>
              <button className="admin-btn admin-btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </div>
        </Modal>
      </AnimatePresence>
    </div>
  );
};

// ── User Management ──
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [showUserModal, setShowUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const loadUsers = useCallback(async () => {
    try {
      const data = await apiCall(`/admin/users?search=${search}&role=${filter}`);
      setUsers(data.users || []);
    } catch { setUsers([]); }
  }, [search, filter]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const updateUserRole = async (userId, role) => {
    try {
      await apiCall(`/admin/users/${userId}/role`, { method: 'PUT', body: JSON.stringify({ role }) });
      loadUsers();
    } catch (err) { console.error(err); }
  };

  const toggleBan = async (userId, banned) => {
    try {
      await apiCall(`/admin/users/${userId}/${banned ? 'unban' : 'ban'}`, { method: 'PUT' });
      loadUsers();
    } catch (err) { console.error(err); }
  };

  const viewUser = (user) => {
    setSelectedUser(user);
    setShowUserModal(true);
  };

  return (
    <div className="admin-section">
      <h3>User Management</h3>
      <div className="admin-toolbar">
        <div className="admin-search">
          <FiSearch />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search users..." />
        </div>
        <select value={filter} onChange={e => setFilter(e.target.value)} className="admin-select">
          <option value="all">All Roles</option>
          <option value="student">Students</option>
          <option value="lecturer">Lecturers</option>
          <option value="admin">Admins</option>
          <option value="sub-admin">Sub-Admins</option>
        </select>
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user._id} className={user.banned ? 'row-banned' : ''}>
                <td>
                  <div className="user-cell">
                    <img src={user.avatar || '/default-avatar.png'} alt="" className="user-avatar-sm" />
                    <span>{user.name}</span>
                  </div>
                </td>
                <td>{user.email}</td>
                <td>
                  <select
                    value={user.role}
                    onChange={e => updateUserRole(user._id, e.target.value)}
                    className="admin-select-sm"
                  >
                    <option value="student">Student</option>
                    <option value="lecturer">Lecturer</option>
                    <option value="admin">Admin</option>
                    <option value="sub-admin">Sub-Admin</option>
                  </select>
                </td>
                <td>
                  <span className={`status-badge ${user.banned ? 'banned' : 'active'}`}>
                    {user.banned ? 'Banned' : 'Active'}
                  </span>
                </td>
                <td>
                  <div className="table-actions">
                    <button className="admin-icon-btn" onClick={() => viewUser(user)} title="View"><FiEye /></button>
                    <button
                      className={`admin-icon-btn ${user.banned ? 'admin-icon-success' : 'admin-icon-danger'}`}
                      onClick={() => toggleBan(user._id, user.banned)}
                      title={user.banned ? 'Unban' : 'Ban'}
                    >
                      {user.banned ? <FiUnlock /> : <FiLock />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <AnimatePresence>
        <Modal isOpen={showUserModal} onClose={() => setShowUserModal(false)} title="User Details">
          {selectedUser && (
            <div className="admin-user-detail">
              <img src={selectedUser.avatar || '/default-avatar.png'} alt="" className="user-avatar-lg" />
              <h4>{selectedUser.name}</h4>
              <p>{selectedUser.email}</p>
              <div className="user-detail-grid">
                <div><strong>Role:</strong> {selectedUser.role}</div>
                <div><strong>Joined:</strong> {new Date(selectedUser.createdAt).toLocaleDateString()}</div>
                <div><strong>Last Active:</strong> {selectedUser.lastSeen ? new Date(selectedUser.lastSeen).toLocaleString() : 'N/A'}</div>
                <div><strong>Status:</strong> {selectedUser.banned ? 'Banned' : 'Active'}</div>
              </div>
            </div>
          )}
        </Modal>
      </AnimatePresence>
    </div>
  );
};

// ── Content Moderation ──
const ContentModeration = () => {
  const [flagged, setFlagged] = useState([]);
  const [filter, setFilter] = useState('pending');

  const loadFlagged = useCallback(async () => {
    try {
      const data = await apiCall(`/admin/flagged-content?status=${filter}`);
      setFlagged(data.content || []);
    } catch { setFlagged([]); }
  }, [filter]);

  useEffect(() => { loadFlagged(); }, [loadFlagged]);

  const handleAction = async (id, action) => {
    try {
      await apiCall(`/admin/flagged-content/${id}/${action}`, { method: 'POST' });
      loadFlagged();
    } catch (err) { console.error(err); }
  };

  return (
    <div className="admin-section">
      <h3><FiShield /> Content Moderation</h3>
      <div className="admin-toolbar">
        <div className="admin-filter-group">
          {['pending', 'reviewed', 'actioned'].map(f => (
            <button key={f} className={`admin-filter-btn ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="admin-flagged-list">
        {flagged.length === 0 && <p className="admin-empty">No flagged content found.</p>}
        {flagged.map(item => (
          <div key={item._id} className="admin-flagged-card">
            <div className="flagged-header">
              <div className="flagged-user">
                <img src={item.reportedBy?.avatar || '/default-avatar.png'} alt="" className="user-avatar-sm" />
                <span>Reported by {item.reportedBy?.name || 'Unknown'}</span>
              </div>
              <span className={`flagged-type type-${item.type}`}>{item.type}</span>
            </div>
            <div className="flagged-content">
              {item.type === 'message' && <p className="flagged-text">"{item.content}"</p>}
              {item.type === 'image' && <img src={item.imageUrl} alt="Flagged" className="flagged-image" />}
              <p className="flagged-reason"><FiFlag /> Reason: {item.reason}</p>
            </div>
            <div className="flagged-actions">
              <button className="admin-btn admin-btn-secondary" onClick={() => handleAction(item._id, 'dismiss')}>
                Dismiss
              </button>
              <button className="admin-btn admin-btn-warning" onClick={() => handleAction(item._id, 'warn')}>
                <FiAlertTriangle /> Warn User
              </button>
              <button className="admin-btn admin-btn-danger" onClick={() => handleAction(item._id, 'delete')}>
                <FiTrash2 /> Delete Content
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── System Settings ──
const SystemSettings = () => {
  const [settings, setSettings] = useState({
    maintenanceMode: false,
    registrationEnabled: true,
    maxUploadSize: 10,
    maxMessageLength: 5000,
    allowFileSharing: true,
    allowVoiceMessages: true,
    allowVideoCalls: true,
    requireEmailVerification: true,
    allowGuestAccess: false,
    rateLimitPerMinute: 60,
  });

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiCall('/admin/settings');
        if (data.settings) setSettings(s => ({ ...s, ...data.settings }));
      } catch {}
    };
    load();
  }, []);

  const handleSave = async () => {
    try {
      await apiCall('/admin/settings', { method: 'PUT', body: JSON.stringify(settings) });
    } catch (err) { console.error(err); }
  };

  const toggleSetting = (key) => {
    setSettings(s => ({ ...s, [key]: !s[key] }));
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3><FiSettings /> System Settings</h3>
        <button className="admin-btn admin-btn-primary" onClick={handleSave}><FiSave /> Save Settings</button>
      </div>

      <div className="admin-settings-grid">
        <div className="admin-setting-card">
          <div className="setting-info">
            <FiGlobe />
            <div>
              <h4>Maintenance Mode</h4>
              <p>When enabled, only admins can access the platform</p>
            </div>
          </div>
          <label className="admin-toggle">
            <input type="checkbox" checked={settings.maintenanceMode} onChange={() => toggleSetting('maintenanceMode')} />
            <span className="toggle-slider"></span>
          </label>
        </div>

        <div className="admin-setting-card">
          <div className="setting-info">
            <FiUserPlus />
            <div>
              <h4>Registration</h4>
              <p>Allow new user registrations</p>
            </div>
          </div>
          <label className="admin-toggle">
            <input type="checkbox" checked={settings.registrationEnabled} onChange={() => toggleSetting('registrationEnabled')} />
            <span className="toggle-slider"></span>
          </label>
        </div>

        <div className="admin-setting-card">
          <div className="setting-info">
            <FiUpload />
            <div>
              <h4>Max Upload Size (MB)</h4>
              <p>Maximum file size for uploads</p>
            </div>
          </div>
          <input
            type="number"
            className="admin-input-sm"
            value={settings.maxUploadSize}
            onChange={e => setSettings({ ...settings, maxUploadSize: parseInt(e.target.value) || 0 })}
            min={1}
            max={100}
          />
        </div>

        <div className="admin-setting-card">
          <div className="setting-info">
            <FiSettings />
            <div>
              <h4>Max Message Length</h4>
              <p>Maximum characters per message</p>
            </div>
          </div>
          <input
            type="number"
            className="admin-input-sm"
            value={settings.maxMessageLength}
            onChange={e => setSettings({ ...settings, maxMessageLength: parseInt(e.target.value) || 0 })}
            min={100}
            max={50000}
          />
        </div>

        <div className="admin-setting-card">
          <div className="setting-info">
            <FiLock />
            <div>
              <h4>Email Verification</h4>
              <p>Require email verification for new accounts</p>
            </div>
          </div>
          <label className="admin-toggle">
            <input type="checkbox" checked={settings.requireEmailVerification} onChange={() => toggleSetting('requireEmailVerification')} />
            <span className="toggle-slider"></span>
          </label>
        </div>

        <div className="admin-setting-card">
          <div className="setting-info">
            <FiBarChart2 />
            <div>
              <h4>Rate Limit (per minute)</h4>
              <p>API requests limit per user per minute</p>
            </div>
          </div>
          <input
            type="number"
            className="admin-input-sm"
            value={settings.rateLimitPerMinute}
            onChange={e => setSettings({ ...settings, rateLimitPerMinute: parseInt(e.target.value) || 0 })}
            min={10}
            max={500}
          />
        </div>
      </div>
    </div>
  );
};

// ── Analytics Dashboard ──
const AnalyticsDashboard = () => {
  const [analytics, setAnalytics] = useState({
    totalUsers: 0, activeUsers: 0, totalMessages: 0, messagesToday: 0,
    storageUsed: 0, storageTotal: 0, newUsersToday: 0, peakConcurrent: 0,
    userGrowth: [], messageGrowth: [], topChatters: [], recentActivity: []
  });

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiCall('/admin/analytics');
        if (data.analytics) setAnalytics(a => ({ ...a, ...data.analytics }));
      } catch {}
    };
    load();
  }, []);

  const statCards = [
    { label: 'Total Users', value: analytics.totalUsers, icon: <FiUsers />, color: '#1a73e8' },
    { label: 'Active Today', value: analytics.activeUsers, icon: <FiEye />, color: '#34a853' },
    { label: 'Total Messages', value: analytics.totalMessages, icon: <FiMegaphone />, color: '#fbbc04' },
    { label: 'Messages Today', value: analytics.messagesToday, icon: <FiBarChart2 />, color: '#ea4335' },
    { label: 'Storage Used', value: `${(analytics.storageUsed / 1024).toFixed(1)} GB`, icon: <FiDatabase />, color: '#9334e6' },
    { label: 'New Today', value: analytics.newUsersToday, icon: <FiUserPlus />, color: '#185abc' },
  ];

  const storagePercent = analytics.storageTotal > 0 ? (analytics.storageUsed / analytics.storageTotal) * 100 : 0;

  return (
    <div className="admin-section">
      <h3><FiBarChart2 /> Analytics Dashboard</h3>

      <div className="admin-stats-grid">
        {statCards.map((stat, i) => (
          <motion.div
            key={i}
            className="admin-stat-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <div className="stat-icon" style={{ background: stat.color + '20', color: stat.color }}>{stat.icon}</div>
            <div className="stat-info">
              <span className="stat-value">{stat.value}</span>
              <span className="stat-label">{stat.label}</span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="admin-charts-row">
        <div className="admin-chart-card">
          <h4>User Growth (7 Days)</h4>
          <div className="mini-bar-chart">
            {(analytics.userGrowth || []).map((val, i) => (
              <div key={i} className="bar-wrapper">
                <div className="bar" style={{ height: `${Math.min((val / (Math.max(...analytics.userGrowth) || 1)) * 100, 100)}%` }} />
                <span className="bar-label">Day {i + 1}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="admin-chart-card">
          <h4>Storage Usage</h4>
          <div className="storage-ring">
            <div className="storage-circle" style={{ background: `conic-gradient(#1a73e8 ${storagePercent}%, #e0e0e0 ${storagePercent}%)` }}>
              <span>{storagePercent.toFixed(1)}%</span>
            </div>
            <p>{(analytics.storageUsed / 1024).toFixed(2)} / {(analytics.storageTotal / 1024).toFixed(1)} GB</p>
          </div>
        </div>
      </div>

      <div className="admin-chart-card full-width">
        <h4>Recent Activity</h4>
        <div className="admin-activity-list">
          {(analytics.recentActivity || []).map((act, i) => (
            <div key={i} className="activity-item">
              <span className={`activity-type type-${act.type}`}>{act.type}</span>
              <span className="activity-text">{act.description}</span>
              <span className="activity-time">{new Date(act.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
          {(!analytics.recentActivity || analytics.recentActivity.length === 0) && (
            <p className="admin-empty">No recent activity data available.</p>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Backup Management ──
const BackupManagement = () => {
  const [backups, setBackups] = useState([]);
  const [creating, setCreating] = useState(false);

  const loadBackups = useCallback(async () => {
    try {
      const data = await apiCall('/admin/backups');
      setBackups(data.backups || []);
    } catch { setBackups([]); }
  }, []);

  useEffect(() => { loadBackups(); }, [loadBackups]);

  const createBackup = async () => {
    setCreating(true);
    try {
      await apiCall('/admin/backups', { method: 'POST' });
      loadBackups();
    } catch (err) { console.error(err); }
    setCreating(false);
  };

  const restoreBackup = async (id) => {
    if (!window.confirm('Are you sure you want to restore this backup? This action cannot be undone.')) return;
    try {
      await apiCall(`/admin/backups/${id}/restore`, { method: 'POST' });
    } catch (err) { console.error(err); }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3><FiDatabase /> Backup Management</h3>
        <button className="admin-btn admin-btn-primary" onClick={createBackup} disabled={creating}>
          {creating ? <><FiRefreshCw className="spin" /> Creating...</> : <><FiDownload /> Create Backup</>}
        </button>
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Backup Name</th>
              <th>Size</th>
              <th>Created</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {backups.map(backup => (
              <tr key={backup._id}>
                <td>{backup.name || `backup-${backup._id.slice(-6)}`}</td>
                <td>{backup.size ? `${(backup.size / 1024 / 1024).toFixed(1)} MB` : 'N/A'}</td>
                <td>{new Date(backup.createdAt).toLocaleString()}</td>
                <td><span className={`status-badge ${backup.status}`}>{backup.status}</span></td>
                <td>
                  <div className="table-actions">
                    <button className="admin-icon-btn" onClick={() => restoreBackup(backup._id)} title="Restore"><FiRefreshCw /></button>
                    <button className="admin-icon-btn" title="Download"><FiDownload /></button>
                  </div>
                </td>
              </tr>
            ))}
            {backups.length === 0 && (
              <tr><td colSpan={5} className="admin-empty">No backups yet. Create one to get started.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ── Calendar Integration ──
const CalendarIntegration = () => {
  const [calendars, setCalendars] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', type: 'academic', color: '#1a73e8', syncEnabled: true, icsUrl: '' });

  const loadCalendars = useCallback(async () => {
    try {
      const data = await apiCall('/admin/calendars');
      setCalendars(data.calendars || []);
    } catch { setCalendars([]); }
  }, []);

  useEffect(() => { loadCalendars(); }, [loadCalendars]);

  const handleSave = async () => {
    try {
      await apiCall('/admin/calendars', { method: 'POST', body: JSON.stringify(form) });
      setShowForm(false);
      setForm({ name: '', type: 'academic', color: '#1a73e8', syncEnabled: true, icsUrl: '' });
      loadCalendars();
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id) => {
    try {
      await apiCall(`/admin/calendars/${id}`, { method: 'DELETE' });
      loadCalendars();
    } catch (err) { console.error(err); }
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3><FiCalendar /> Calendar Integration</h3>
        <button className="admin-btn admin-btn-primary" onClick={() => setShowForm(true)}><FiPlus /> Add Calendar</button>
      </div>

      <div className="admin-calendar-list">
        {calendars.map(cal => (
          <div key={cal._id} className="admin-calendar-card">
            <div className="cal-color" style={{ background: cal.color }} />
            <div className="cal-info">
              <h4>{cal.name}</h4>
              <span className={`cal-type type-${cal.type}`}>{cal.type}</span>
            </div>
            <div className="cal-status">
              {cal.syncEnabled ? <FiCheck className="text-success" /> : <FiX className="text-danger" />}
              <span>{cal.syncEnabled ? 'Synced' : 'Disabled'}</span>
            </div>
            <div className="cal-actions">
              <button className="admin-icon-btn" onClick={() => handleDelete(cal._id)}><FiTrash2 /></button>
            </div>
          </div>
        ))}
      </div>

      <AnimatePresence>
        <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="Add Calendar">
          <div className="admin-form">
            <div className="admin-form-group">
              <label>Calendar Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Academic Calendar 2026" />
            </div>
            <div className="admin-form-group">
              <label>Type</label>
              <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                <option value="academic">Academic</option>
                <option value="events">Events</option>
                <option value="holidays">Holidays</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <ColorPicker label="Color" value={form.color} onChange={v => setForm({ ...form, color: v })} />
            <div className="admin-form-group">
              <label>ICS URL (optional)</label>
              <input value={form.icsUrl} onChange={e => setForm({ ...form, icsUrl: e.target.value })} placeholder="https://..." />
            </div>
            <div className="admin-checkbox-row">
              <label>
                <input type="checkbox" checked={form.syncEnabled} onChange={e => setForm({ ...form, syncEnabled: e.target.checked })} /> Enable auto-sync
              </label>
            </div>
            <div className="admin-form-actions">
              <button className="admin-btn admin-btn-primary" onClick={handleSave}><FiSave /> Add Calendar</button>
              <button className="admin-btn admin-btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </div>
        </Modal>
      </AnimatePresence>
    </div>
  );
};

// ── Sub-Admin Management ──
const SubAdminManagement = () => {
  const [subAdmins, setSubAdmins] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: '', permissions: { themes: false, users: false, announcements: false, moderation: false, settings: false, backups: false, analytics: false } });

  const loadSubAdmins = useCallback(async () => {
    try {
      const data = await apiCall('/admin/sub-admins');
      setSubAdmins(data.subAdmins || []);
    } catch { setSubAdmins([]); }
  }, []);

  useEffect(() => { loadSubAdmins(); }, [loadSubAdmins]);

  const handleCreate = async () => {
    try {
      await apiCall('/admin/sub-admins', { method: 'POST', body: JSON.stringify(form) });
      setShowForm(false);
      setForm({ email: '', permissions: { themes: false, users: false, announcements: false, moderation: false, settings: false, backups: false, analytics: false } });
      loadSubAdmins();
    } catch (err) { console.error(err); }
  };

  const handleRemove = async (id) => {
    try {
      await apiCall(`/admin/sub-admins/${id}`, { method: 'DELETE' });
      loadSubAdmins();
    } catch (err) { console.error(err); }
  };

  const togglePerm = (perm) => {
    setForm(f => ({ ...f, permissions: { ...f.permissions, [perm]: !f.permissions[perm] } }));
  };

  const permLabels = {
    themes: 'Theme Manager', users: 'User Management', announcements: 'Announcements',
    moderation: 'Content Moderation', settings: 'System Settings', backups: 'Backup Management', analytics: 'Analytics'
  };

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3><FiUserPlus /> Sub-Admin Management</h3>
        <button className="admin-btn admin-btn-primary" onClick={() => setShowForm(true)}><FiPlus /> Add Sub-Admin</button>
      </div>

      <div className="admin-subadmin-list">
        {subAdmins.map(sa => (
          <div key={sa._id} className="admin-subadmin-card">
            <div className="subadmin-info">
              <img src={sa.user?.avatar || '/default-avatar.png'} alt="" className="user-avatar-sm" />
              <div>
                <span className="subadmin-name">{sa.user?.name || sa.email}</span>
                <span className="subadmin-email">{sa.email}</span>
              </div>
            </div>
            <div className="subadmin-perms">
              {Object.entries(sa.permissions || {}).filter(([, v]) => v).map(([k]) => (
                <span key={k} className="perm-badge">{permLabels[k] || k}</span>
              ))}
            </div>
            <button className="admin-icon-btn admin-icon-danger" onClick={() => handleRemove(sa._id)}><FiTrash2 /></button>
          </div>
        ))}
        {subAdmins.length === 0 && <p className="admin-empty">No sub-admins configured.</p>}
      </div>

      <AnimatePresence>
        <Modal isOpen={showForm} onClose={() => setShowForm(false)} title="Add Sub-Admin">
          <div className="admin-form">
            <div className="admin-form-group">
              <label>Email Address</label>
              <input value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="user@kyu.ac.ke" type="email" />
            </div>
            <div className="admin-form-group">
              <label>Permissions</label>
              <div className="admin-permissions-grid">
                {Object.entries(permLabels).map(([key, label]) => (
                  <label key={key} className="admin-perm-checkbox">
                    <input type="checkbox" checked={form.permissions[key]} onChange={() => togglePerm(key)} />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="admin-form-actions">
              <button className="admin-btn admin-btn-primary" onClick={handleCreate}><FiSave /> Create Sub-Admin</button>
              <button className="admin-btn admin-btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </div>
        </Modal>
      </AnimatePresence>
    </div>
  );
};

// ── Main Admin Panel ──
const AdminCustomization = () => {
  const [activeTab, setActiveTab] = useState('themes');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const tabs = [
    { id: 'themes', label: 'Themes', icon: FiPalette },
    { id: 'branding', label: 'Branding', icon: FiUpload },
    { id: 'layout', label: 'Dashboard Layout', icon: FiLayout },
    { id: 'announcements', label: 'Announcements', icon: FiMegaphone },
    { id: 'users', label: 'Users', icon: FiUsers },
    { id: 'moderation', label: 'Moderation', icon: FiShield },
    { id: 'settings', label: 'System Settings', icon: FiSettings },
    { id: 'analytics', label: 'Analytics', icon: FiBarChart2 },
    { id: 'backups', label: 'Backups', icon: FiDatabase },
    { id: 'calendar', label: 'Calendars', icon: FiCalendar },
    { id: 'subadmins', label: 'Sub-Admins', icon: FiUserPlus },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'themes': return <ThemeManager />;
      case 'branding': return <LogoBranding />;
      case 'layout': return <DashboardLayout />;
      case 'announcements': return <AnnouncementManager />;
      case 'users': return <UserManagement />;
      case 'moderation': return <ContentModeration />;
      case 'settings': return <SystemSettings />;
      case 'analytics': return <AnalyticsDashboard />;
      case 'backups': return <BackupManagement />;
      case 'calendar': return <CalendarIntegration />;
      case 'subadmins': return <SubAdminManagement />;
      default: return <ThemeManager />;
    }
  };

  return (
    <div className={`admin-panel ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <h2>Admin Panel</h2>
          <button className="admin-toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <FiChevronRight className={!sidebarOpen ? 'rotated' : ''} />
          </button>
        </div>
        <nav className="admin-sidebar-nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`admin-nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="admin-main">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
};

export default AdminCustomization;
