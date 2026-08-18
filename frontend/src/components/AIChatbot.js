import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiMessageCircle, FiX, FiSend, FiCpu, FiUser } from 'react-icons/fi';
import api from '../services/api';
import './AIChatbot.css';

const AIChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, type: 'ai', text: "Hello! I'm KyU Assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen && suggestions.length === 0) {
      loadSuggestions();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const loadSuggestions = async () => {
    try {
      const { data } = await api.get('/ai/suggestions');
      setSuggestions(data.suggestions || []);
    } catch (err) {
      setSuggestions([
        "What services are available?",
        "How do I join a study group?",
        "Where is the library?"
      ]);
    }
  };

  const handleSend = async (text = null) => {
    const msg = text || input.trim();
    if (!msg) return;

    const userMsg = { id: Date.now(), type: 'user', text: msg };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const { data } = await api.post('/ai/chat', { message: msg, context: 'general' });
      const aiMsg = { id: Date.now() + 1, type: 'ai', text: data.response };
      setMessages(prev => [...prev, aiMsg]);
      if (data.suggestions?.length) {
        setSuggestions(data.suggestions);
      }
    } catch (err) {
      const errorMsg = { id: Date.now() + 1, type: 'ai', text: "Sorry, I couldn't process that. Please try again." };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <motion.button
        className="ai-chat-toggle"
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
      >
        {isOpen ? <FiX size={24} /> : <FiMessageCircle size={24} />}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="ai-chatbot"
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div className="ai-chat-header">
              <div className="ai-header-info">
                <FiCpu className="ai-icon" />
                <div>
                  <h4>KyU Assistant</h4>
                  <span className="ai-status">Online</span>
                </div>
              </div>
              <button className="ai-close-btn" onClick={() => setIsOpen(false)}>
                <FiX />
              </button>
            </div>

            <div className="ai-chat-messages">
              {messages.map(msg => (
                <motion.div
                  key={msg.id}
                  className={`ai-message ${msg.type}`}
                  initial={{ opacity: 0, x: msg.type === 'user' ? 20 : -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ type: 'spring', damping: 20 }}
                >
                  <div className="ai-message-avatar">
                    {msg.type === 'ai' ? <FiCpu /> : <FiUser />}
                  </div>
                  <div className="ai-message-bubble">
                    <p>{msg.text}</p>
                  </div>
                </motion.div>
              ))}
              {isTyping && (
                <div className="ai-message ai">
                  <div className="ai-message-avatar"><FiCpu /></div>
                  <div className="ai-message-bubble typing">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {suggestions.length > 0 && (
              <div className="ai-suggestions">
                {suggestions.slice(0, 3).map((s, i) => (
                  <button key={i} className="ai-suggestion-btn" onClick={() => handleSend(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}

            <div className="ai-chat-input">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                disabled={isTyping}
              />
              <button
                className="ai-send-btn"
                onClick={() => handleSend()}
                disabled={!input.trim() || isTyping}
              >
                <FiSend />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default AIChatbot;
