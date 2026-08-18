import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import NotificationBell from './NotificationBell';
import '../styles/sidebar.css';

const navItems = [
  { path: '/dashboard', icon: '📊', label: 'Dashboard' },
  { path: '/chat', icon: '💬', label: 'Messages', badge: 'totalUnread' },
  { path: '/groups', icon: '👥', label: 'Groups' },
  { path: '/moments', icon: '🌟', label: 'Moments' },
  { path: '/bulletin', icon: '📋', label: 'Bulletin' },
  { path: '/events', icon: '📅', label: 'Events' },
  { path: '/calendar', icon: '📆', label: 'Calendar' },
  { path: '/backup', icon: '💾', label: 'Backup' },
  { path: '/downloads', icon: '📲', label: 'Install App' },
  { path: '/profile', icon: '👤', label: 'Profile' },
];

const adminItems = [
  { path: '/admin', icon: '⚙️', label: 'Admin Panel' },
  { path: '/admin/customize', icon: '🎨', label: 'Customize' },
  { path: '/admin/moderation', icon: '🛡️', label: 'Moderation' },
];

export default function Sidebar({ collapsed, onToggle }) {
  const { user, logout } = useAuth();
  const { totalUnread } = useChat();
  const navigate = useNavigate();
  const [hoveredItem, setHoveredItem] = useState(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const roleColors = {
    student: 'var(--role-student)',
    moderator: 'var(--role-moderator)',
    admin: 'var(--role-admin)'
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <img src="/images/kyu-logo.png" alt="KyU" className="logo-icon-img" onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }} />
          <div className="logo-icon" style={{ display: 'none' }}>KyU</div>
          {!collapsed && <span className="logo-text">Campus Connect</span>}
        </div>
        <button className="sidebar-toggle" onClick={onToggle}>
          {collapsed ? '▶' : '◀'}
        </button>
      </div>

      <div className="sidebar-user">
        <div className="user-avatar-wrapper">
          <img
            src={user?.avatar || `https://ui-avatars.com/api/?name=${user?.name}&background=1a237e&color=fff`}
            alt={user?.name}
            className="user-avatar"
          />
          <span className="online-dot"></span>
        </div>
        {!collapsed && (
          <div className="user-info">
            <span className="user-name">{user?.name}</span>
            <span
              className="user-role-badge"
              style={{ background: roleColors[user?.role] }}
            >
              {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
            </span>
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            onMouseEnter={() => setHoveredItem(item.label)}
            onMouseLeave={() => setHoveredItem(null)}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && <span className="nav-label">{item.label}</span>}
            {item.badge === 'totalUnread' && totalUnread > 0 && (
              <span className="nav-badge">{totalUnread > 99 ? '99+' : totalUnread}</span>
            )}
            {collapsed && hoveredItem === item.label && (
              <span className="tooltip">{item.label}</span>
            )}
          </NavLink>
        ))}

        {user?.role === 'admin' && (
          <>
            <div className="nav-divider"></div>
            {adminItems.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => `nav-item admin-nav ${isActive ? 'active' : ''}`}
                onMouseEnter={() => setHoveredItem(item.label)}
                onMouseLeave={() => setHoveredItem(null)}
              >
                <span className="nav-icon">{item.icon}</span>
                {!collapsed && <span className="nav-label">{item.label}</span>}
                {collapsed && hoveredItem === item.label && (
                  <span className="tooltip">{item.label}</span>
                )}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="sidebar-footer">
        <NotificationBell collapsed={collapsed} />
        <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🔧</span>
          {!collapsed && <span className="nav-label">Settings</span>}
        </NavLink>
        <button className="nav-item logout-btn" onClick={handleLogout}>
          <span className="nav-icon">🚪</span>
          {!collapsed && <span className="nav-label">Logout</span>}
        </button>
        {!collapsed && (
          <div className="sidebar-kyu-info">
            <div className="sidebar-iso">
              <img src="/images/iso-badge.png" alt="ISO" className="sidebar-iso-img" onError={(e) => { e.target.style.display = 'none'; }} />
              <span className="sidebar-iso-text">ISO 9001:2015</span>
            </div>
            <div className="sidebar-motto">
              <span>Innovative Technology for a Dynamic World</span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
