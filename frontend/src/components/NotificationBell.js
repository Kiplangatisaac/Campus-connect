import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import api from '../services/api';

export default function NotificationBell({ collapsed }) {
  const { totalUnread } = useChat();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/notifications');
      setNotifications(data.notifications || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isOpen) fetchNotifications();
    setIsOpen(!isOpen);
  };

  const markAsRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(prev =>
        prev.map(n => n._id === id ? { ...n, read: true } : n)
      );
    } catch (err) {
      console.error(err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="notification-bell-wrapper" ref={dropdownRef}>
      <button className="nav-item notification-bell" onClick={handleToggle}>
        <span className="nav-icon">🔔</span>
        {!collapsed && <span className="nav-label">Notifications</span>}
        {(unreadCount > 0 || totalUnread > 0) && (
          <span className="notification-badge">{unreadCount || totalUnread}</span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <h4>Notifications</h4>
            <button className="mark-all-read" onClick={markAllAsRead}>
              Mark all read
            </button>
          </div>
          <div className="notification-list">
            {loading ? (
              <div className="notification-loading">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="notification-empty">No notifications</div>
            ) : (
              notifications.slice(0, 20).map(notif => (
                <div
                  key={notif._id}
                  className={`notification-item ${notif.read ? '' : 'unread'}`}
                  onClick={() => markAsRead(notif._id)}
                >
                  <div className="notification-icon">
                    {notif.type === 'message' && '💬'}
                    {notif.type === 'group' && '👥'}
                    {notif.type === 'event' && '📅'}
                    {notif.type === 'bulletin' && '📋'}
                    {notif.type === 'system' && '⚙️'}
                  </div>
                  <div className="notification-content">
                    <p className="notification-text">{notif.message}</p>
                    <span className="notification-time">
                      {new Date(notif.createdAt).toLocaleString()}
                    </span>
                  </div>
                  {!notif.read && <span className="unread-dot"></span>}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
