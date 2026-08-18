import React from 'react';
import { useChat } from '../context/ChatContext';

export default function OnlineStatus({ userId, showLabel = false }) {
  const { onlineUsers } = useChat();
  const isOnline = onlineUsers.has(userId);

  return (
    <span className={`online-status ${isOnline ? 'online' : 'offline'}`}>
      <span className={`status-dot ${isOnline ? 'online' : 'offline'}`}></span>
      {showLabel && (
        <span className="status-label">{isOnline ? 'Online' : 'Offline'}</span>
      )}
    </span>
  );
}
