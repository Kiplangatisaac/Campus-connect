import React, { createContext, useContext, useState, useCallback } from 'react';
import api from '../services/api';

const ChatContext = createContext(null);

export function useChat() {
  return useContext(ChatContext);
}

export function ChatProvider({ children }) {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState({});
  const [typingUsers, setTypingUsers] = useState({});
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const [unreadCounts, setUnreadCounts] = useState({});
  const [loading, setLoading] = useState(false);

  const fetchConversations = useCallback(async () => {
    try {
      const { data } = await api.get('/chat/conversations');
      setConversations(data.conversations || []);
      const counts = {};
      (data.conversations || []).forEach(c => {
        if (c.unreadCount > 0) counts[c._id] = c.unreadCount;
      });
      setUnreadCounts(counts);
    } catch (err) {
      console.error('Failed to fetch conversations', err);
    }
  }, []);

  const fetchMessages = useCallback(async (conversationId) => {
    setLoading(true);
    try {
      const { data } = await api.get(`/chat/conversations/${conversationId}/messages`);
      setMessages(prev => ({ ...prev, [conversationId]: data.messages || [] }));
      setUnreadCounts(prev => {
        const next = { ...prev };
        delete next[conversationId];
        return next;
      });
    } catch (err) {
      console.error('Failed to fetch messages', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (conversationId, content, type = 'text', file = null) => {
    try {
      let payload = { content, type };
      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('content', content);
        formData.append('type', type);
        const { data } = await api.post(`/chat/conversations/${conversationId}/messages`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        setMessages(prev => ({
          ...prev,
          [conversationId]: [...(prev[conversationId] || []), data.message]
        }));
        return data.message;
      }
      const { data } = await api.post(`/chat/conversations/${conversationId}/messages`, payload);
      setMessages(prev => ({
        ...prev,
        [conversationId]: [...(prev[conversationId] || []), data.message]
      }));
      return data.message;
    } catch (err) {
      console.error('Failed to send message', err);
      return null;
    }
  }, []);

  const createConversation = useCallback(async (participantIds, isGroup = false, name = '') => {
    try {
      const { data } = await api.post('/chat/conversations', {
        participants: participantIds,
        isGroup,
        name
      });
      setConversations(prev => [data.conversation, ...prev]);
      return data.conversation;
    } catch (err) {
      console.error('Failed to create conversation', err);
      return null;
    }
  }, []);

  const addTypingUser = useCallback((conversationId, userId) => {
    setTypingUsers(prev => ({
      ...prev,
      [conversationId]: [...new Set([...(prev[conversationId] || []), userId])]
    }));
  }, []);

  const removeTypingUser = useCallback((conversationId, userId) => {
    setTypingUsers(prev => ({
      ...prev,
      [conversationId]: (prev[conversationId] || []).filter(id => id !== userId)
    }));
  }, []);

  const addOnlineUser = useCallback((userId) => {
    setOnlineUsers(prev => new Set([...prev, userId]));
  }, []);

  const removeOnlineUser = useCallback((userId) => {
    setOnlineUsers(prev => {
      const next = new Set(prev);
      next.delete(userId);
      return next;
    });
  }, []);

  const receiveMessage = useCallback((message) => {
    setMessages(prev => ({
      ...prev,
      [message.conversation]: [...(prev[message.conversation] || []), message]
    }));
    if (activeConversation?._id !== message.conversation) {
      setUnreadCounts(prev => ({
        ...prev,
        [message.conversation]: (prev[message.conversation] || 0) + 1
      }));
    }
  }, [activeConversation]);

  const totalUnread = Object.values(unreadCounts).reduce((a, b) => a + b, 0);

  const value = {
    conversations,
    activeConversation,
    messages,
    typingUsers,
    onlineUsers,
    unreadCounts,
    totalUnread,
    loading,
    setActiveConversation,
    fetchConversations,
    fetchMessages,
    sendMessage,
    createConversation,
    addTypingUser,
    removeTypingUser,
    addOnlineUser,
    removeOnlineUser,
    receiveMessage,
    setConversations
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}
