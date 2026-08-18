import React, { useState, useRef, useEffect } from 'react';
import EmojiPicker from 'emoji-picker-react';
import { useChat } from '../context/ChatContext';
import { useSocket } from '../context/SocketContext';

export default function MessageInput({ conversationId }) {
  const { sendMessage } = useChat();
  const { startTyping, stopTyping } = useSocket();
  const [text, setText] = useState('');
  const [showEmoji, setShowEmoji] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const inputRef = useRef(null);

  const handleTyping = () => {
    startTyping(conversationId);
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      stopTyping(conversationId);
    }, 2000);
  };

  const handleSend = async () => {
    if (!text.trim()) return;
    const content = text.trim();
    setText('');
    stopTyping(conversationId);
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    await sendMessage(conversationId, content);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const type = file.type.startsWith('image/') ? 'image' : 'file';
    await sendMessage(conversationId, file.name, type, file);
    e.target.value = '';
  };

  const handleEmojiClick = (emojiData) => {
    setText(prev => prev + emojiData.emoji);
    inputRef.current?.focus();
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
  };

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    };
  }, []);

  return (
    <div className="message-input-container">
      {showEmoji && (
        <div className="emoji-picker-wrapper">
          <EmojiPicker onEmojiClick={handleEmojiClick} theme="dark" width={350} height={400} />
        </div>
      )}
      <div className="message-input-actions">
        <button
          className="input-action-btn"
          onClick={() => setShowEmoji(!showEmoji)}
          title="Emoji"
        >
          😊
        </button>
        <button
          className="input-action-btn"
          onClick={() => fileInputRef.current.click()}
          title="Attach file"
        >
          📎
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          accept="image/*,.pdf,.doc,.docx,.txt,.zip"
        />
      </div>
      <div className="message-input-wrapper">
        <textarea
          ref={inputRef}
          className="message-input"
          placeholder="Type a message..."
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            handleTyping();
          }}
          onKeyDown={handleKeyDown}
          rows={1}
        />
      </div>
      <div className="message-input-actions">
        <button
          className={`input-action-btn ${isRecording ? 'recording' : ''}`}
          onClick={toggleRecording}
          title={isRecording ? 'Stop recording' : 'Record voice'}
        >
          {isRecording ? '⏹️' : '🎤'}
        </button>
        {text.trim() ? (
          <button className="send-btn" onClick={handleSend} title="Send">
            ➤
          </button>
        ) : (
          <button className="input-action-btn" title="Video call">
            📹
          </button>
        )}
      </div>
    </div>
  );
}
