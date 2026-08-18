import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useChat } from '../context/ChatContext';

export default function UserCard({ user, compact = false }) {
  const navigate = useNavigate();
  const { onlineUsers } = useChat();
  const isOnline = onlineUsers.has(user._id);

  const roleColors = {
    student: 'var(--role-student)',
    moderator: 'var(--role-moderator)',
    admin: 'var(--role-admin)'
  };

  const roleBadgeColors = {
    student: '#2196f3',
    moderator: '#4caf50',
    admin: '#f44336'
  };

  if (compact) {
    return (
      <div className="user-card compact" onClick={() => navigate(`/profile/${user._id}`)}>
        <div className="user-card-avatar-wrapper">
          <img
            src={user.avatar || `https://ui-avatars.com/api/?name=${user.name}&background=1a237e&color=fff`}
            alt=""
            className="user-card-avatar"
          />
          {isOnline && <span className="online-dot"></span>}
        </div>
        <div className="user-card-info">
          <span className="user-card-name">{user.name}</span>
          <span className="user-card-role" style={{ color: roleBadgeColors[user.role] }}>
            {user.role?.charAt(0).toUpperCase() + user.role?.slice(1)}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="user-card" onClick={() => navigate(`/profile/${user._id}`)}>
      <div className="user-card-header">
        <div className="user-card-avatar-wrapper large">
          <img
            src={user.avatar || `https://ui-avatars.com/api/?name=${user.name}&background=1a237e&color=fff`}
            alt=""
            className="user-card-avatar"
          />
          {isOnline && <span className="online-dot large"></span>}
        </div>
      </div>
      <div className="user-card-body">
        <h4 className="user-card-name">{user.name}</h4>
        <span
          className="user-card-role-badge"
          style={{ background: roleBadgeColors[user.role] }}
        >
          {user.role?.charAt(0).toUpperCase() + user.role?.slice(1)}
        </span>
        {user.department && (
          <p className="user-card-department">📚 {user.department}</p>
        )}
        {user.course && (
          <p className="user-card-course">🎓 {user.course}</p>
        )}
        {user.regNumber && (
          <p className="user-card-reg">ID: {user.regNumber}</p>
        )}
      </div>
      <div className="user-card-footer">
        <button className="user-card-btn message">💬 Message</button>
        <button className="user-card-btn profile">View Profile</button>
      </div>
    </div>
  );
}
