import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { useChat } from '../context/ChatContext';
import api from '../services/api';

export default function ConversationList() {
  const { conversations, activeConversation, setActiveConversation, unreadCounts, fetchConversations } = useChat();
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState([]);
  const [showNewChat, setShowNewChat] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const searchUsers = async (query) => {
    if (!query) { setUsers([]); return; }
    try {
      const { data } = await api.get(`/users/search?q=${query}`);
      setUsers(data.users || []);
    } catch (err) {
      console.error(err);
    }
  };

  const startNewChat = async (userId) => {
    try {
      const { data } = await api.post('/chat/conversations', { participants: [userId] });
      setActiveConversation(data.conversation);
      setShowNewChat(false);
      setSearchQuery('');
      setUsers([]);
      navigate(`/chat/${data.conversation._id}`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleConversationClick = (conv) => {
    setActiveConversation(conv);
    navigate(`/chat/${conv._id}`);
  };

  const getConversationName = (conv) => {
    if (conv.isGroup) return conv.name;
    const other = conv.participants?.find(p => p._id !== localStorage.getItem('userId'));
    return other?.name || 'Unknown';
  };

  const getConversationAvatar = (conv) => {
    if (conv.isGroup) return conv.avatar;
    const other = conv.participants?.find(p => p._id !== localStorage.getItem('userId'));
    return other?.avatar;
  };

  const formatLastMessageTime = (date) => {
    if (!date) return '';
    const d = new Date(date);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) return format(d, 'HH:mm');
    return format(d, 'MMM d');
  };

  const filteredConversations = conversations.filter(conv => {
    const name = getConversationName(conv).toLowerCase();
    return name.includes(searchQuery.toLowerCase());
  });

  return (
    <div className="conversation-list">
      <div className="conversation-header">
        <h3>Messages</h3>
        <button className="new-chat-btn" onClick={() => setShowNewChat(!showNewChat)}>
          {showNewChat ? '✕' : '✏️'}
        </button>
      </div>

      <div className="conversation-search">
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            if (showNewChat) searchUsers(e.target.value);
          }}
        />
      </div>

      {showNewChat && (
        <div className="new-chat-dropdown">
          {users.length > 0 ? (
            users.map(user => (
              <div
                key={user._id}
                className="new-chat-user"
                onClick={() => startNewChat(user._id)}
              >
                <img
                  src={user.avatar || `https://ui-avatars.com/api/?name=${user.name}&background=1a237e&color=fff`}
                  alt=""
                  className="new-chat-avatar"
                />
                <div>
                  <span className="new-chat-name">{user.name}</span>
                  <span className="new-chat-dept">{user.department}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="new-chat-empty">Type to search for users</div>
          )}
        </div>
      )}

      <div className="conversation-items">
        {filteredConversations.map(conv => (
          <div
            key={conv._id}
            className={`conversation-item ${activeConversation?._id === conv._id ? 'active' : ''} ${unreadCounts[conv._id] > 0 ? 'unread' : ''}`}
            onClick={() => handleConversationClick(conv)}
          >
            <div className="conversation-avatar-wrapper">
              <img
                src={getConversationAvatar(conv) || `https://ui-avatars.com/api/?name=${getConversationName(conv)}&background=1a237e&color=fff`}
                alt=""
                className="conversation-avatar"
              />
              {!conv.isGroup && (
                <span className="online-indicator"></span>
              )}
            </div>
            <div className="conversation-info">
              <div className="conversation-top">
                <span className="conversation-name">{getConversationName(conv)}</span>
                <span className="conversation-time">
                  {formatLastMessageTime(conv.lastMessage?.createdAt)}
                </span>
              </div>
              <div className="conversation-bottom">
                <span className="conversation-last-msg">
                  {conv.lastMessage?.content || 'No messages yet'}
                </span>
                {unreadCounts[conv._id] > 0 && (
                  <span className="unread-badge">{unreadCounts[conv._id]}</span>
                )}
              </div>
            </div>
          </div>
        ))}
        {filteredConversations.length === 0 && (
          <div className="no-conversations">
            <p>No conversations found</p>
          </div>
        )}
      </div>
    </div>
  );
}
