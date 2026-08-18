import React, { createContext, useContext, useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';
import { useChat } from './ChatContext';

const SocketContext = createContext(null);

export function useSocket() {
  return useContext(SocketContext);
}

export function SocketProvider({ children }) {
  const socketRef = useRef(null);
  const { user } = useAuth();
  const {
    receiveMessage,
    addTypingUser,
    removeTypingUser,
    addOnlineUser,
    removeOnlineUser,
    fetchConversations
  } = useChat();

  const connect = useCallback(() => {
    if (!user || socketRef.current?.connected) return;

    const socket = io(process.env.REACT_APP_WS_URL || `http://${window.location.hostname}:8001`, {
      auth: { token: localStorage.getItem('token') },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000
    });

    socket.on('connect', () => {
      console.log('Socket connected');
      socket.emit('user:online', user._id);
    });

    socket.on('message:receive', (message) => {
      receiveMessage(message);
    });

    socket.on('user:typing', ({ conversationId, userId }) => {
      addTypingUser(conversationId, userId);
    });

    socket.on('user:stop-typing', ({ conversationId, userId }) => {
      removeTypingUser(conversationId, userId);
    });

    socket.on('user:online', (userId) => {
      addOnlineUser(userId);
    });

    socket.on('user:offline', (userId) => {
      removeOnlineUser(userId);
    });

    socket.on('conversation:updated', () => {
      fetchConversations();
    });

    socket.on('notification', (data) => {
      if (window.Notification && Notification.permission === 'granted') {
        new Notification(data.title, { body: data.body, icon: '/logo192.png' });
      }
    });

    socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    socketRef.current = socket;
  }, [user, receiveMessage, addTypingUser, removeTypingUser, addOnlineUser, removeOnlineUser, fetchConversations]);

  useEffect(() => {
    connect();
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [connect]);

  const emit = useCallback((event, data) => {
    socketRef.current?.emit(event, data);
  }, []);

  const joinConversation = useCallback((conversationId) => {
    emit('conversation:join', conversationId);
  }, [emit]);

  const leaveConversation = useCallback((conversationId) => {
    emit('conversation:leave', conversationId);
  }, [emit]);

  const startTyping = useCallback((conversationId) => {
    emit('user:typing', { conversationId });
  }, [emit]);

  const stopTyping = useCallback((conversationId) => {
    emit('user:stop-typing', { conversationId });
  }, [emit]);

  const value = {
    socket: socketRef.current,
    emit,
    joinConversation,
    leaveConversation,
    startTyping,
    stopTyping
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
}
