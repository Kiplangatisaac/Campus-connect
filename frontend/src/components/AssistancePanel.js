import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  FiHelpCircle, FiMessageSquare, FiX, FiSend, FiUser, FiPhone,
  FiMail, FiChevronDown, FiChevronUp, FiSearch, FiClock,
  FiAlertCircle, FiHeadphones, FiBook, FiMinimize2,
  FiMaximize2
} from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import './AssistancePanel.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const FAQ_DATA = [
  { q: 'How do I reset my password?', a: 'Go to Settings > Account > Change Password, or use the "Forgot Password" link on the login page.' },
  { q: 'How do I change my theme?', a: 'Navigate to Settings > Customize > Theme to select from available themes or create a custom one.' },
  { q: 'Can I use Campus Connect on mobile?', a: 'Yes! Campus Connect is responsive and works on all devices. A native app is coming soon.' },
  { q: 'How do I report inappropriate content?', a: 'Click the flag icon on any message or use the Report button on user profiles.' },
  { q: 'How do I join a study group?', a: 'Go to Groups > Browse Groups or use the search bar to find and join groups.' },
  { q: 'Is my data secure?', a: 'Yes, all data is encrypted end-to-end. We follow strict data protection policies.' },
  { q: 'How do I enable dark mode?', a: 'Go to Settings > Customize > Theme and select "Dark" from the theme options.' },
  { q: 'How do I customize my chat bubbles?', a: 'Go to Settings > Customize > Chat Bubbles to choose colors and styles.' },
  { q: 'Can I schedule messages?', a: 'Yes, long-press the send button to schedule a message for later delivery.' },
  { q: 'How do I contact IT support?', a: 'Use this assistance panel or email support@kyu.ac.ke. You can also call ext. 1234.' },
];

const CONTACT_INFO = [
  { department: 'IT Support', name: 'Help Desk', email: 'support@kyu.ac.ke', phone: 'Ext. 1234', hours: 'Mon-Fri 8AM-5PM', icon: FiHeadphones },
  { department: 'Dean of Students', name: 'Prof. Jane Mwangi', email: 'dean.students@kyu.ac.ke', phone: 'Ext. 2001', hours: 'Mon-Fri 9AM-4PM', icon: FiUser },
  { department: 'Student Affairs', name: 'Student Welfare Office', email: 'studentaffairs@kyu.ac.ke', phone: 'Ext. 1500', hours: 'Mon-Fri 8AM-5PM', icon: FiBook },
];

const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
};

// ── AI Chat ──
const AIChat = ({ onClose }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your Campus Connect assistant. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showEscalate, setShowEscalate] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const data = await apiCall('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message: userMsg.content, context: 'campus-assistance' }),
      });
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply || data.message || 'I\'m sorry, I couldn\'t process that. Let me connect you with a human agent.' }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'I\'m having trouble connecting. Would you like to speak with a human agent?' }]);
      setShowEscalate(true);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="ai-chat">
      <div className="ai-chat-messages">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            className={`ai-msg ${msg.role}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {msg.role === 'assistant' && <div className="ai-avatar"><FiHelpCircle /></div>}
            <div className="ai-msg-bubble">{msg.content}</div>
          </motion.div>
        ))}
        {loading && (
          <div className="ai-msg assistant">
            <div className="ai-avatar"><FiHelpCircle /></div>
            <div className="ai-msg-bubble ai-typing">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {showEscalate && (
        <motion.div
          className="ai-escalate-banner"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
        >
          <span>Would you like to talk to a human agent?</span>
          <div className="ai-escalate-actions">
            <button className="ap-btn ap-btn-sm ap-btn-primary" onClick={() => { setShowEscalate(false); onClose?.('human'); }}>
              <FiUser /> Talk to Human
            </button>
            <button className="ap-btn ap-btn-sm ap-btn-ghost" onClick={() => setShowEscalate(false)}>Continue with AI</button>
          </div>
        </motion.div>
      )}

      <div className="ai-chat-input">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question..."
          rows={1}
          className="ai-input"
        />
        <button className="ai-send-btn" onClick={sendMessage} disabled={!input.trim() || loading}>
          <FiSend />
        </button>
      </div>

      <div className="ai-chat-footer">
        <button className="ap-btn ap-btn-sm ap-btn-outline" onClick={() => setShowEscalate(true)}>
          <FiUser /> Talk to Human
        </button>
      </div>
    </div>
  );
};

// ── Ticket System ──
const TicketSystem = () => {
  const [tickets, setTickets] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ subject: '', category: 'general', message: '' });
  const [submitting, setSubmitting] = useState(false);

  const loadTickets = useCallback(async () => {
    try {
      const data = await apiCall('/support/tickets');
      setTickets(data.tickets || []);
    } catch { setTickets([]); }
  }, []);

  useEffect(() => { loadTickets(); }, [loadTickets]);

  const handleSubmit = async () => {
    if (!form.subject.trim() || !form.message.trim()) return;
    setSubmitting(true);
    try {
      await apiCall('/support/tickets', { method: 'POST', body: JSON.stringify(form) });
      setShowForm(false);
      setForm({ subject: '', category: 'general', message: '' });
      loadTickets();
    } catch (err) { console.error(err); }
    setSubmitting(false);
  };

  const statusColors = {
    open: '#1a73e8',
    pending: '#fbbc04',
    resolved: '#34a853',
    closed: '#9aa0a6',
  };

  return (
    <div className="ticket-system">
      <div className="ticket-header">
        <h3>Support Tickets</h3>
        <button className="ap-btn ap-btn-sm ap-btn-primary" onClick={() => setShowForm(true)}>New Ticket</button>
      </div>

      <AnimatePresence>
        {showForm && (
          <motion.div
            className="ticket-form-card"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="ticket-form">
              <div className="ticket-form-group">
                <label>Subject</label>
                <input
                  value={form.subject}
                  onChange={e => setForm({ ...form, subject: e.target.value })}
                  placeholder="Brief description of your issue"
                  className="ap-input"
                />
              </div>
              <div className="ticket-form-group">
                <label>Category</label>
                <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="ap-select">
                  <option value="general">General Inquiry</option>
                  <option value="technical">Technical Issue</option>
                  <option value="account">Account Problem</option>
                  <option value="feature">Feature Request</option>
                  <option value="bug">Bug Report</option>
                </select>
              </div>
              <div className="ticket-form-group">
                <label>Message</label>
                <textarea
                  value={form.message}
                  onChange={e => setForm({ ...form, message: e.target.value })}
                  placeholder="Describe your issue in detail..."
                  rows={4}
                  className="ap-textarea"
                />
              </div>
              <div className="ticket-form-actions">
                <button className="ap-btn ap-btn-primary" onClick={handleSubmit} disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Ticket'}
                </button>
                <button className="ap-btn ap-btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="ticket-list">
        {tickets.length === 0 && <p className="ap-empty">No tickets yet. Create one to get help.</p>}
        {tickets.map(ticket => (
          <div key={ticket._id} className="ticket-card">
            <div className="ticket-card-header">
              <span className="ticket-id">#{ticket._id.slice(-6).toUpperCase()}</span>
              <span className="ticket-status" style={{ color: statusColors[ticket.status] || '#9aa0a6' }}>
                <span className="status-dot" style={{ background: statusColors[ticket.status] || '#9aa0a6' }} />
                {ticket.status}
              </span>
            </div>
            <h4 className="ticket-subject">{ticket.subject}</h4>
            <p className="ticket-preview">{ticket.message?.slice(0, 100)}...</p>
            <div className="ticket-meta">
              <span><FiClock /> {new Date(ticket.createdAt).toLocaleDateString()}</span>
              <span className="ticket-category">{ticket.category}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── FAQ Section ──
const FAQSection = () => {
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(null);

  const filtered = FAQ_DATA.filter(f =>
    f.q.toLowerCase().includes(search.toLowerCase()) ||
    f.a.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="faq-section">
      <h3>Frequently Asked Questions</h3>
      <div className="faq-search">
        <FiSearch />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search FAQs..."
          className="ap-input"
        />
      </div>
      <div className="faq-list">
        {filtered.map((faq, i) => (
          <motion.div
            key={i}
            className={`faq-item ${expanded === i ? 'expanded' : ''}`}
            layout
          >
            <button className="faq-question" onClick={() => setExpanded(expanded === i ? null : i)}>
              <span>{faq.q}</span>
              {expanded === i ? <FiChevronUp /> : <FiChevronDown />}
            </button>
            <AnimatePresence>
              {expanded === i && (
                <motion.div
                  className="faq-answer"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <p>{faq.a}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
        {filtered.length === 0 && <p className="ap-empty">No matching FAQs found.</p>}
      </div>
    </div>
  );
};

// ── Contact Info ──
const ContactInfo = () => (
  <div className="contact-section">
    <h3>Contact Support</h3>
    <div className="contact-list">
      {CONTACT_INFO.map((contact, i) => (
        <div key={i} className="contact-card">
          <div className="contact-icon">
            <contact.icon />
          </div>
          <div className="contact-details">
            <h4>{contact.department}</h4>
            <p className="contact-name">{contact.name}</p>
            <div className="contact-row">
              <FiMail />
              <a href={`mailto:${contact.email}`}>{contact.email}</a>
            </div>
            <div className="contact-row">
              <FiPhone />
              <span>{contact.phone}</span>
            </div>
            <div className="contact-row">
              <FiClock />
              <span>{contact.hours}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

// ── Main Assistance Panel ──
const AssistancePanel = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [minimized, setMinimized] = useState(false);
  const [unread, setUnread] = useState(0);

  const handleEscalate = (type) => {
    if (type === 'human') {
      setActiveTab('tickets');
    }
  };

  const tabs = [
    { id: 'chat', label: 'AI Assistant', icon: FiMessageSquare },
    { id: 'tickets', label: 'Tickets', icon: FiAlertCircle },
    { id: 'faq', label: 'FAQ', icon: FiBook },
    { id: 'contact', label: 'Contact', icon: FiPhone },
  ];

  return (
    <>
      <motion.button
        className="assistance-fab"
        onClick={() => { setIsOpen(!isOpen); setMinimized(false); if (unread > 0) setUnread(0); }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        aria-label="Get Assistance"
      >
        {isOpen ? <FiX size={24} /> : <FiHelpCircle size={24} />}
        {unread > 0 && !isOpen && <span className="fab-badge">{unread}</span>}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={`assistance-panel ${minimized ? 'minimized' : ''}`}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            <div className="ap-header">
              <div className="ap-header-info">
                <FiHeadphones className="ap-header-icon" />
                <div>
                  <h3>Need Help?</h3>
                  <p>We're here to assist you</p>
                </div>
              </div>
              <div className="ap-header-actions">
                <button className="ap-icon-btn" onClick={() => setMinimized(!minimized)} title={minimized ? 'Expand' : 'Minimize'}>
                  {minimized ? <FiMaximize2 /> : <FiMinimize2 />}
                </button>
                <button className="ap-icon-btn" onClick={() => setIsOpen(false)} title="Close">
                  <FiX />
                </button>
              </div>
            </div>

            {!minimized && (
              <>
                <div className="ap-tabs">
                  {tabs.map(tab => (
                    <button
                      key={tab.id}
                      className={`ap-tab ${activeTab === tab.id ? 'active' : ''}`}
                      onClick={() => setActiveTab(tab.id)}
                    >
                      <tab.icon />
                      <span>{tab.label}</span>
                    </button>
                  ))}
                </div>

                <div className="ap-content">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeTab}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.15 }}
                      className="ap-tab-panel"
                    >
                      {activeTab === 'chat' && <AIChat onClose={handleEscalate} />}
                      {activeTab === 'tickets' && <TicketSystem />}
                      {activeTab === 'faq' && <FAQSection />}
                      {activeTab === 'contact' && <ContactInfo />}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default AssistancePanel;
