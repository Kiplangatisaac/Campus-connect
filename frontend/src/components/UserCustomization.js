import React, { useState, useEffect, useCallback } from 'react';
import {
  FiPalette, FiMessageCircle, FiType, FiBell, FiLock, FiImage,
  FiSave, FiCheck, FiUpload, FiX, FiChevronRight, FiUser, FiGlobe,
  FiSun, FiMoon, FiCircle
} from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import './UserCustomization.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const DEFAULT_PREFS = {
  theme: 'default',
  chatBubbleColor: '#1a73e8',
  chatBubbleColorCustom: '',
  sentMessageColor: '#9aa0a6',
  deliveredColor: '#1a73e8',
  readColor: '#34a853',
  customStatusColors: false,
  chatBackground: '#ffffff',
  chatBackgroundType: 'solid',
  chatBackgroundGradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  chatBackgroundImage: '',
  fontSize: 14,
  wallpaperPreset: 'default',
  notifications: { messages: true, mentions: true, announcements: true, sound: true, vibration: true },
  privacy: { lastSeen: true, readReceipts: true, onlineStatus: true, profilePhoto: 'everyone' },
  statusMessage: '',
  displayName: '',
};

const THEMES = [
  { id: 'default', name: 'Default', primary: '#1a73e8', bg: '#ffffff', text: '#202124' },
  { id: 'dark', name: 'Dark', primary: '#8ab4f8', bg: '#1a1a2e', text: '#e8eaed' },
  { id: 'light', name: 'Light', primary: '#1a73e8', bg: '#f8f9fa', text: '#202124' },
  { id: 'kyu-green', name: 'KyU Green', primary: '#0d6b3d', bg: '#ffffff', text: '#202124' },
  { id: 'kyu-blue', name: 'KyU Blue', primary: '#003366', bg: '#ffffff', text: '#202124' },
];

const BUBBLE_COLORS = [
  { id: 'blue', color: '#1a73e8', label: 'Blue' },
  { id: 'green', color: '#25D366', label: 'Green' },
  { id: 'purple', color: '#7c3aed', label: 'Purple' },
  { id: 'orange', color: '#f97316', label: 'Orange' },
  { id: 'red', color: '#ea4335', label: 'Red' },
  { id: 'teal', color: '#0891b2', label: 'Teal' },
  { id: 'pink', color: '#ec4899', label: 'Pink' },
  { id: 'custom', color: '', label: 'Custom' },
];

const WALLPAPERS = [
  { id: 'default', name: 'Default', preview: '#ffffff' },
  { id: 'gradient-1', name: 'Purple Haze', preview: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  { id: 'gradient-2', name: 'Ocean Breeze', preview: 'linear-gradient(135deg, #2af598 0%, #009efd 100%)' },
  { id: 'gradient-3', name: 'Sunset', preview: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
  { id: 'gradient-4', name: 'Midnight', preview: 'linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 50%, #2d1b69 100%)' },
  { id: 'gradient-5', name: 'Forest', preview: 'linear-gradient(135deg, #134e5e 0%, #71b280 100%)' },
  { id: 'gradient-6', name: 'Peach', preview: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)' },
  { id: 'gradient-7', name: 'KyU Green', preview: 'linear-gradient(135deg, #0d6b3d 0%, #14a05c 100%)' },
];

const FontSizeSlider = ({ value, onChange }) => (
  <div className="uc-fontsize-control">
    <span className="uc-fontsize-label" style={{ fontSize: 11 }}>A</span>
    <input
      type="range"
      min={11}
      max={20}
      value={value}
      onChange={e => onChange(parseInt(e.target.value))}
      className="uc-range"
    />
    <span className="uc-fontsize-label" style={{ fontSize: 20 }}>A</span>
    <span className="uc-fontsize-value">{value}px</span>
  </div>
);

const ToggleSetting = ({ label, description, checked, onChange }) => (
  <div className="uc-toggle-row">
    <div className="uc-toggle-info">
      <span className="uc-toggle-label">{label}</span>
      {description && <span className="uc-toggle-desc">{description}</span>}
    </div>
    <label className="uc-toggle">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="uc-toggle-slider" />
    </label>
  </div>
);

const UserCustomization = ({ userId }) => {
  const [prefs, setPrefs] = useState(DEFAULT_PREFS);
  const [activeSection, setActiveSection] = useState('theme');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [customBubbleColor, setCustomBubbleColor] = useState('#1a73e8');
  const [customBgImage, setCustomBgImage] = useState(null);
  const [customBgPreview, setCustomBgPreview] = useState('');

  useEffect(() => {
    const stored = localStorage.getItem('userPreferences');
    if (stored) {
      try {
        setPrefs(p => ({ ...p, ...JSON.parse(stored) }));
      } catch {}
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('userPreferences', JSON.stringify(prefs));
    applyTheme(prefs.theme);
  }, [prefs]);

  const applyTheme = (themeId) => {
    const theme = THEMES.find(t => t.id === themeId);
    if (!theme) return;
    document.documentElement.style.setProperty('--uc-primary', theme.primary);
    document.documentElement.style.setProperty('--uc-bg', theme.bg);
    document.documentElement.style.setProperty('--uc-text', theme.text);
  };

  const syncToBackend = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_BASE}/user/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(prefs),
      });
    } catch (err) { console.error('Failed to sync preferences:', err); }
  }, [prefs]);

  const handleSave = async () => {
    setSaving(true);
    await syncToBackend();
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const updatePref = (key, value) => {
    setPrefs(p => ({ ...p, [key]: value }));
  };

  const updateNestedPref = (section, key, value) => {
    setPrefs(p => ({ ...p, [section]: { ...p[section], [key]: value } }));
  };

  const handleBgImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setCustomBgPreview(ev.target.result);
      updatePref('chatBackgroundImage', ev.target.result);
      updatePref('chatBackgroundType', 'image');
    };
    reader.readAsDataURL(file);
  };

  const sections = [
    { id: 'theme', label: 'Theme', icon: FiPalette },
    { id: 'bubbles', label: 'Chat Bubbles', icon: FiMessageCircle },
    { id: 'background', label: 'Chat Background', icon: FiImage },
    { id: 'font', label: 'Font Size', icon: FiType },
    { id: 'notifications', label: 'Notifications', icon: FiBell },
    { id: 'privacy', label: 'Privacy', icon: FiLock },
    { id: 'profile', label: 'Profile', icon: FiUser },
  ];

  const renderThemeSection = () => (
    <div className="uc-section-content">
      <h3>Choose Theme</h3>
      <div className="uc-theme-grid">
        {THEMES.map(theme => (
          <motion.button
            key={theme.id}
            className={`uc-theme-card ${prefs.theme === theme.id ? 'active' : ''}`}
            onClick={() => updatePref('theme', theme.id)}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
          >
            <div className="uc-theme-preview">
              <div style={{ background: theme.primary, height: 24, borderRadius: '6px 6px 0 0' }} />
              <div style={{ background: theme.bg, padding: 10, minHeight: 50 }}>
                <div style={{ width: '60%', height: 6, background: theme.text, borderRadius: 3, opacity: 0.2, marginBottom: 4 }} />
                <div style={{ width: '40%', height: 6, background: theme.text, borderRadius: 3, opacity: 0.1 }} />
              </div>
            </div>
            <div className="uc-theme-info">
              <span className="uc-theme-name">{theme.name}</span>
              {prefs.theme === theme.id && <FiCheck className="uc-theme-check" />}
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  );

  const renderBubblesSection = () => (
    <div className="uc-section-content">
      <h3>Chat Bubble Color</h3>
      <p className="uc-hint">Choose a color for your sent messages</p>
      <div className="uc-color-grid">
        {BUBBLE_COLORS.map(bc => (
          <motion.button
            key={bc.id}
            className={`uc-bubble-option ${prefs.chatBubbleColor === bc.color && bc.id !== 'custom' ? 'active' : ''}`}
            onClick={() => {
              if (bc.id === 'custom') {
                updatePref('chatBubbleColor', customBubbleColor);
              } else {
                updatePref('chatBubbleColor', bc.color);
                updatePref('chatBubbleColorCustom', '');
              }
            }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            {bc.id === 'custom' ? (
              <div className="uc-custom-bubble">
                <input
                  type="color"
                  value={customBubbleColor}
                  onChange={e => {
                    setCustomBubbleColor(e.target.value);
                    updatePref('chatBubbleColor', e.target.value);
                    updatePref('chatBubbleColorCustom', e.target.value);
                  }}
                  onClick={e => e.stopPropagation()}
                />
              </div>
            ) : (
              <div className="uc-bubble-circle" style={{ background: bc.color }} />
            )}
            <span className="uc-bubble-label">{bc.label}</span>
          </motion.button>
        ))}
      </div>

      <div className="uc-divider" />

      <h3>Message Status Colors</h3>
      <p className="uc-hint">Customize colors for sent, delivered, and read indicators</p>
      <div className="uc-status-colors">
        <div className="uc-status-row">
          <div className="uc-status-info">
            <span className="uc-status-dot" style={{ background: prefs.sentMessageColor }} />
            <span>Sent</span>
          </div>
          <input type="color" value={prefs.sentMessageColor} onChange={e => updatePref('sentMessageColor', e.target.value)} className="uc-color-input" />
        </div>
        <div className="uc-status-row">
          <div className="uc-status-info">
            <span className="uc-status-dot" style={{ background: prefs.deliveredColor }} />
            <span>Delivered</span>
          </div>
          <input type="color" value={prefs.deliveredColor} onChange={e => updatePref('deliveredColor', e.target.value)} className="uc-color-input" />
        </div>
        <div className="uc-status-row">
          <div className="uc-status-info">
            <span className="uc-status-dot" style={{ background: prefs.readColor }} />
            <span>Read</span>
          </div>
          <input type="color" value={prefs.readColor} onChange={e => updatePref('readColor', e.target.value)} className="uc-color-input" />
        </div>
      </div>

      <div className="uc-divider" />

      <div className="uc-preview-chat">
        <div className="uc-preview-header">Chat Preview</div>
        <div className="uc-preview-messages">
          <div className="uc-preview-msg received">
            <span>Hey! How's it going?</span>
          </div>
          <div className="uc-preview-msg sent" style={{ background: prefs.chatBubbleColor }}>
            <span>I'm doing great! Thanks for asking.</span>
            <span className="uc-preview-time" style={{ color: prefs.sentMessageColor === '#ffffff' ? 'rgba(255,255,255,0.7)' : '#999' }}>10:30 AM</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderBackgroundSection = () => (
    <div className="uc-section-content">
      <h3>Chat Background</h3>

      <div className="uc-bg-options">
        <button
          className={`uc-bg-option ${prefs.chatBackgroundType === 'solid' ? 'active' : ''}`}
          onClick={() => updatePref('chatBackgroundType', 'solid')}
        >
          <FiCircle /> Solid Color
        </button>
        <button
          className={`uc-bg-option ${prefs.chatBackgroundType === 'gradient' ? 'active' : ''}`}
          onClick={() => updatePref('chatBackgroundType', 'gradient')}
        >
          <FiPalette /> Gradient
        </button>
        <button
          className={`uc-bg-option ${prefs.chatBackgroundType === 'image' ? 'active' : ''}`}
          onClick={() => updatePref('chatBackgroundType', 'image')}
        >
          <FiImage /> Custom Image
        </button>
      </div>

      {prefs.chatBackgroundType === 'solid' && (
        <div className="uc-solid-picker">
          <input
            type="color"
            value={prefs.chatBackground}
            onChange={e => updatePref('chatBackground', e.target.value)}
            className="uc-color-input-lg"
          />
          <span>{prefs.chatBackground}</span>
        </div>
      )}

      {prefs.chatBackgroundType === 'gradient' && (
        <div className="uc-wallpaper-grid">
          {WALLPAPERS.filter(w => w.id.startsWith('gradient')).map(wp => (
            <motion.button
              key={wp.id}
              className={`uc-wallpaper-card ${prefs.wallpaperPreset === wp.id ? 'active' : ''}`}
              onClick={() => {
                updatePref('wallpaperPreset', wp.id);
                updatePref('chatBackgroundGradient', wp.preview);
              }}
              whileHover={{ scale: 1.05 }}
            >
              <div className="uc-wallpaper-preview" style={{ background: wp.preview }} />
              <span>{wp.name}</span>
            </motion.button>
          ))}
        </div>
      )}

      {prefs.chatBackgroundType === 'image' && (
        <div className="uc-image-upload">
          {customBgPreview || prefs.chatBackgroundImage ? (
            <div className="uc-bg-preview">
              <img src={customBgPreview || prefs.chatBackgroundImage} alt="Background" />
              <button className="uc-remove-bg" onClick={() => { setCustomBgPreview(''); updatePref('chatBackgroundImage', ''); }}>
                <FiX />
              </button>
            </div>
          ) : (
            <label className="uc-upload-area">
              <FiUpload size={24} />
              <span>Upload Image</span>
              <input type="file" accept="image/*" hidden onChange={handleBgImageUpload} />
            </label>
          )}
        </div>
      )}

      <div className="uc-preview-chat" style={{ marginTop: 16 }}>
        <div className="uc-preview-header">Background Preview</div>
        <div
          className="uc-preview-body"
          style={{
            background: prefs.chatBackgroundType === 'solid'
              ? prefs.chatBackground
              : prefs.chatBackgroundType === 'gradient'
                ? prefs.chatBackgroundGradient
                : (customBgPreview || prefs.chatBackgroundImage || '#ffffff'),
            backgroundSize: 'cover',
          }}
        >
          <div className="uc-preview-msg received">
            <span>This is how your chat will look!</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderFontSection = () => (
    <div className="uc-section-content">
      <h3>Font Size</h3>
      <p className="uc-hint">Adjust the text size across the app</p>
      <div className="uc-fontsize-box">
        <FontSizeSlider value={prefs.fontSize} onChange={v => updatePref('fontSize', v)} />
        <div className="uc-fontsize-preview" style={{ fontSize: prefs.fontSize }}>
          <p>The quick brown fox jumps over the lazy dog.</p>
          <p className="uc-fontsize-sample-sub">This is a sample message in your chat.</p>
        </div>
      </div>
    </div>
  );

  const renderNotificationsSection = () => (
    <div className="uc-section-content">
      <h3>Notification Preferences</h3>
      <div className="uc-settings-list">
        <ToggleSetting
          label="Message Notifications"
          description="Get notified for new messages"
          checked={prefs.notifications.messages}
          onChange={() => updateNestedPref('notifications', 'messages', !prefs.notifications.messages)}
        />
        <ToggleSetting
          label="Mentions"
          description="Get notified when someone mentions you"
          checked={prefs.notifications.mentions}
          onChange={() => updateNestedPref('notifications', 'mentions', !prefs.notifications.mentions)}
        />
        <ToggleSetting
          label="Announcements"
          description="Receive admin announcements"
          checked={prefs.notifications.announcements}
          onChange={() => updateNestedPref('notifications', 'announcements', !prefs.notifications.announcements)}
        />
        <ToggleSetting
          label="Sound"
          description="Play notification sounds"
          checked={prefs.notifications.sound}
          onChange={() => updateNestedPref('notifications', 'sound', !prefs.notifications.sound)}
        />
        <ToggleSetting
          label="Vibration"
          description="Vibrate on notification"
          checked={prefs.notifications.vibration}
          onChange={() => updateNestedPref('notifications', 'vibration', !prefs.notifications.vibration)}
        />
      </div>
    </div>
  );

  const renderPrivacySection = () => (
    <div className="uc-section-content">
      <h3>Privacy Settings</h3>
      <div className="uc-settings-list">
        <ToggleSetting
          label="Last Seen"
          description="Show when you were last online"
          checked={prefs.privacy.lastSeen}
          onChange={() => updateNestedPref('privacy', 'lastSeen', !prefs.privacy.lastSeen)}
        />
        <ToggleSetting
          label="Read Receipts"
          description="Show when you've read messages"
          checked={prefs.privacy.readReceipts}
          onChange={() => updateNestedPref('privacy', 'readReceipts', !prefs.privacy.readReceipts)}
        />
        <ToggleSetting
          label="Online Status"
          description="Show when you're online"
          checked={prefs.privacy.onlineStatus}
          onChange={() => updateNestedPref('privacy', 'onlineStatus', !prefs.privacy.onlineStatus)}
        />
      </div>

      <div className="uc-divider" />

      <h3>Profile Photo Visibility</h3>
      <div className="uc-radio-group">
        {['everyone', 'contacts', 'nobody'].map(opt => (
          <label key={opt} className="uc-radio-label">
            <input
              type="radio"
              name="profilePhoto"
              value={opt}
              checked={prefs.privacy.profilePhoto === opt}
              onChange={() => updateNestedPref('privacy', 'profilePhoto', opt)}
            />
            <span>{opt.charAt(0).toUpperCase() + opt.slice(1)}</span>
          </label>
        ))}
      </div>
    </div>
  );

  const renderProfileSection = () => (
    <div className="uc-section-content">
      <h3>Profile Customization</h3>

      <div className="uc-form-group">
        <label>Display Name</label>
        <input
          type="text"
          value={prefs.displayName}
          onChange={e => updatePref('displayName', e.target.value)}
          placeholder="Your display name"
          className="uc-input"
        />
      </div>

      <div className="uc-form-group">
        <label>Status Message</label>
        <input
          type="text"
          value={prefs.statusMessage}
          onChange={e => updatePref('statusMessage', e.target.value)}
          placeholder="Hey there! I'm using Campus Connect."
          className="uc-input"
          maxLength={100}
        />
        <span className="uc-char-count">{prefs.statusMessage.length}/100</span>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeSection) {
      case 'theme': return renderThemeSection();
      case 'bubbles': return renderBubblesSection();
      case 'background': return renderBackgroundSection();
      case 'font': return renderFontSection();
      case 'notifications': return renderNotificationsSection();
      case 'privacy': return renderPrivacySection();
      case 'profile': return renderProfileSection();
      default: return renderThemeSection();
    }
  };

  return (
    <div className="uc-panel">
      <aside className="uc-sidebar">
        <div className="uc-sidebar-header">
          <h2>Customize</h2>
        </div>
        <nav className="uc-sidebar-nav">
          {sections.map(sec => (
            <button
              key={sec.id}
              className={`uc-nav-item ${activeSection === sec.id ? 'active' : ''}`}
              onClick={() => setActiveSection(sec.id)}
            >
              <sec.icon />
              <span>{sec.label}</span>
              <FiChevronRight className="uc-nav-arrow" />
            </button>
          ))}
        </nav>
      </aside>

      <main className="uc-main">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>

        <div className="uc-save-bar">
          <motion.button
            className={`uc-save-btn ${saved ? 'saved' : ''}`}
            onClick={handleSave}
            disabled={saving}
            whileTap={{ scale: 0.95 }}
          >
            {saving ? 'Saving...' : saved ? <><FiCheck /> Saved!</> : <><FiSave /> Save Changes</>}
          </motion.button>
        </div>
      </main>
    </div>
  );
};

export default UserCustomization;
