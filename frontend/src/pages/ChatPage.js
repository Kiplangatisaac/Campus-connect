import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useChat } from '../context/ChatContext';
import ConversationList from '../components/ConversationList';
import ChatWindow from '../components/ChatWindow';
import MessageInput from '../components/MessageInput';
import VideoCall from '../components/VideoCall';
import AudioCall from '../components/AudioCall';
import '../styles/chat.css';

export default function ChatPage() {
  const { conversationId } = useParams();
  const { conversations, activeConversation, setActiveConversation, fetchMessages } = useChat();
  const [showCallModal, setShowCallModal] = useState(null);
  const [callingUser, setCallingUser] = useState(null);

  useEffect(() => {
    if (conversationId) {
      const conv = conversations.find(c => c._id === conversationId);
      if (conv) {
        setActiveConversation(conv);
        fetchMessages(conversationId);
      }
    }
  }, [conversationId, conversations, setActiveConversation, fetchMessages]);

  // eslint-disable-next-line no-unused-vars
  const handleCallUser = (targetUser, type) => {
    setCallingUser(targetUser);
    setShowCallModal(type);
  };

  const handleEndCall = () => {
    setShowCallModal(null);
    setCallingUser(null);
  };

  return (
    <div className="chat-page">
      <div className="chat-sidebar">
        <ConversationList />
      </div>
      <div className="chat-main">
        {activeConversation ? (
          <>
            <ChatWindow conversation={activeConversation} />
            <MessageInput conversationId={activeConversation._id} />
          </>
        ) : (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <h3>Start a Conversation</h3>
            <p>Select a conversation from the sidebar or start a new one</p>
          </div>
        )}
      </div>

      {showCallModal === 'video' && callingUser && (
        <VideoCall targetUser={callingUser} onEnd={handleEndCall} />
      )}
      {showCallModal === 'audio' && callingUser && (
        <AudioCall targetUser={callingUser} onEnd={handleEndCall} />
      )}
    </div>
  );
}
