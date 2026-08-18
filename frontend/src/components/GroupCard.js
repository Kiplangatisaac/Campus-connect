import React from 'react';
import { useChat } from '../context/ChatContext';

export default function GroupCard({ group, onJoin, onLeave }) {
  const { onlineUsers } = useChat();

  const isMember = group.members?.some(m => m._id === localStorage.getItem('userId'));
  const memberCount = group.members?.length || 0;
  const onlineCount = group.members?.filter(m => onlineUsers.has(m._id)).length || 0;

  const getGroupTypeColor = () => {
    switch (group.type) {
      case 'faculty': return 'var(--role-admin)';
      case 'study': return 'var(--role-moderator)';
      case 'club': return 'var(--accent-gold)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div className="group-card">
      <div className="group-card-header">
        <img
          src={group.avatar || `https://ui-avatars.com/api/?name=${group.name}&background=1a237e&color=fff`}
          alt={group.name}
          className="group-card-avatar"
        />
        <div className="group-card-type" style={{ background: getGroupTypeColor() }}>
          {group.type}
        </div>
      </div>
      <div className="group-card-body">
        <h3 className="group-card-name">{group.name}</h3>
        <p className="group-card-description">{group.description || 'No description'}</p>
        <div className="group-card-stats">
          <span className="group-stat">👥 {memberCount} members</span>
          <span className="group-stat">🟢 {onlineCount} online</span>
        </div>
        {group.department && (
          <span className="group-card-dept">📚 {group.department}</span>
        )}
      </div>
      <div className="group-card-footer">
        {isMember ? (
          <button className="group-btn leave" onClick={() => onLeave(group._id)}>
            Leave Group
          </button>
        ) : (
          <button className="group-btn join" onClick={() => onJoin(group._id)}>
            Join Group
          </button>
        )}
        <button className="group-btn view">View</button>
      </div>
    </div>
  );
}
