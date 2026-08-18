import React, { useState, useEffect, useRef, useMemo } from 'react';
import { format, isToday, isYesterday } from 'date-fns';
import { useChat } from '../context/ChatContext';
import { useSocket } from '../context/SocketContext';

export default function ChatWindow({ conversation }) {
  const { messages, typingUsers, loading } = useChat();
  const { joinConversation, leaveConversation } = useSocket();
  const messagesEndRef = useRef(null);
  const prevConversationId = useRef(null);

  const conversationTyping = typingUsers[conversation?._id] || [];
  const currentMessages = useMemo(() => messages[conversation?._id] || [], [messages, conversation?._id]);

  useEffect(() => {
    if (prevConversationId.current) {
      leaveConversation(prevConversationId.current);
    }
    if (conversation?._id) {
      joinConversation(conversation._id);
      prevConversationId.current = conversation._id;
    }
  }, [conversation?._id, joinConversation, leaveConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages]);

  const formatMessageTime = (date) => {
    const d = new Date(date);
    if (isToday(d)) return format(d, 'HH:mm');
    if (isYesterday(d)) return `Yesterday ${format(d, 'HH:mm')}`;
    return format(d, 'MMM d, HH:mm');
  };

  const formatDateSeparator = (date) => {
    const d = new Date(date);
    if (isToday(d)) return 'Today';
    if (isYesterday(d)) return 'Yesterday';
    return format(d, 'MMMM d, yyyy');
  };

  const shouldShowDateSeparator = (msg, index) => {
    if (index === 0) return true;
    const prevDate = new Date(currentMessages[index - 1].createdAt).toDateString();
    const currentDate = new Date(msg.createdAt).toDateString();
    return prevDate !== currentDate;
  };

  const shouldShowAvatar = (msg, index) => {
    if (index === 0) return true;
    const prevMsg = currentMessages[index - 1];
    return prevMsg.sender._id !== msg.sender._id;
  };

  if (!conversation) {
    return (
      <div className="chat-window empty-chat">
        <div className="empty-chat-content">
          <div className="empty-chat-icon">💬</div>
          <h3>Welcome to Campus Chat</h3>
          <p>Select a conversation or start a new one</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="chat-contact-info">
          <img
            src={conversation.isGroup
              ? conversation.avatar || `https://ui-avatars.com/api/?name=${conversation.name}&background=1a237e&color=fff`
              : conversation.participants?.[0]?.avatar || `https://ui-avatars.com/api/?name=${conversation.participants?.[0]?.name}&background=1a237e&color=fff`
            }
            alt=""
            className="chat-contact-avatar"
          />
          <div>
            <h3 className="chat-contact-name">
              {conversation.isGroup ? conversation.name : conversation.participants?.[0]?.name}
            </h3>
            <span className="chat-contact-status">
              {conversation.isGroup
                ? `${conversation.participants?.length} members`
                : 'Online'
              }
            </span>
          </div>
        </div>
        <div className="chat-actions">
          <button className="chat-action-btn" title="Voice Call">📞</button>
          <button className="chat-action-btn" title="Video Call">📹</button>
          <button className="chat-action-btn" title="Info">ℹ️</button>
        </div>
      </div>

      <div className="chat-messages">
        {loading ? (
          <div className="chat-loading">
            <div className="spinner"></div>
          </div>
        ) : (
          currentMessages.map((msg, index) => (
            <React.Fragment key={msg._id}>
              {shouldShowDateSeparator(msg, index) && (
                <div className="message-date-separator">
                  <span>{formatDateSeparator(msg.createdAt)}</span>
                </div>
              )}
              <div className={`message ${msg.sender._id === 'self' ? 'sent' : 'received'}`}>
                {shouldShowAvatar(msg, index) && (
                  <img
                    src={msg.sender.avatar || `https://ui-avatars.com/api/?name=${msg.sender.name}&background=666&color=fff`}
                    alt={msg.sender.name}
                    className="message-avatar"
                  />
                )}
                <div className="message-bubble">
                  {conversation.isGroup && msg.sender._id !== 'self' && shouldShowAvatar(msg, index) && (
                    <span className="message-sender">{msg.sender.name}</span>
                  )}
                  {msg.type === 'text' && <p className="message-text">{msg.content}</p>}
                  {msg.type === 'image' && (
                    <div className="message-media">
                      <img src={msg.fileUrl} alt="" className="message-image" />
                    </div>
                  )}
                  {msg.type === 'file' && (
                    <div className="message-file">
                      <span className="file-icon">📎</span>
                      <span className="file-name">{msg.fileName}</span>
                    </div>
                  )}
                  <span className="message-time">{formatMessageTime(msg.createdAt)}</span>
                </div>
              </div>
            </React.Fragment>
          ))
        )}
        {conversationTyping.length > 0 && (
          <div className="typing-indicator">
            <div className="typing-dots">
              <span></span><span></span><span></span>
            </div>
            <span className="typing-text">
              {conversationTyping.length === 1 ? 'Someone is typing...' : `${conversationTyping.length} people typing...`}
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
