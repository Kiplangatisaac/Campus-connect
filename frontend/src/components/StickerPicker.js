import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './StickerPicker.css';

const stickerSets = [
  {
    name: 'Smileys',
    stickers: ['😀', '😃', '😄', '😁', '😅', '😂', '🤣', '😊', '😇', '🙂', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '🤐', '🤨']
  },
  {
    name: 'Gestures',
    stickers: ['👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '👇', '☝️', '✋', '🤚', '🖐️', '🖖', '👋', '🤝', '🙏', '💪', '🦾', '👊', '✊', '🤛', '🤜', '👏', '🙌', '👐', '🤲']
  },
  {
    name: 'Hearts',
    stickers: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '♥️', '😍', '🥰', '😘', '💑', '💏', '👩‍❤️‍👨', '👨‍❤️‍👨', '👩‍❤️‍👩']
  },
  {
    name: 'Objects',
    stickers: ['📱', '💻', '🖥️', '🖨️', '⌨️', '🖱️', '🖲️', '💾', '💿', '📀', '📼', '📷', '📸', '📹', '🎥', '📽️', '🎞️', '📞', '☎️', '📟', '📠', '📺', '📻', '🎙️', '🎚️', '🎛️', '🧭', '⏱️', '⏲️', '⏰']
  },
  {
    name: 'Nature',
    stickers: ['🌸', '💐', '🌷', '🌹', '🥀', '🌺', '🌻', '🌼', '🌿', '☘️', '🍀', '🍁', '🍂', '🍃', '🌍', '🌎', '🌏', '🌕', '🌙', '⭐', '🌟', '✨', '⚡', '🔥', '🌈', '☀️', '🌤️', '⛅', '🌥️', '☁️']
  },
  {
    name: 'Food',
    stickers: ['🍏', '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🫐', '🍈', '🍒', '🍑', '🥭', '🍍', '🥥', '🥝', '🍅', '🥑', '🌮', '🌯', '🥙', '🧆', '🥚', '🍳', '🥘', '🍲', '🫕', '🥣', '🥗']
  }
];

const StickerPicker = ({ onSelect, onClose }) => {
  const [activeSet, setActiveSet] = useState(0);

  return (
    <motion.div
      className="sticker-picker"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
    >
      <div className="sticker-tabs">
        {stickerSets.map((set, index) => (
          <button
            key={set.name}
            className={`sticker-tab ${activeSet === index ? 'active' : ''}`}
            onClick={() => setActiveSet(index)}
          >
            {set.stickers[0]}
          </button>
        ))}
      </div>
      
      <div className="sticker-grid">
        {stickerSets[activeSet].stickers.map((sticker, index) => (
          <motion.button
            key={index}
            className="sticker-item"
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => {
              onSelect(sticker);
              onClose();
            }}
          >
            {sticker}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
};

export default StickerPicker;
