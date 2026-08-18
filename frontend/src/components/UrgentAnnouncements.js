import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiAlertTriangle, FiX, FiChevronLeft, FiChevronRight, FiMaximize2, FiMinimize2 } from 'react-icons/fi';
import { formatDistanceToNow } from 'date-fns';
import './UrgentAnnouncements.css';

const URGENT_SOUND_URL = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACAf39/f3+AgICAgH9/f39/gICAgIB/f39/f4CAgICAf39/f3+AgICAgH9/f39/gICAgIB/f39/f4CAgICA';

function playUrgentSound() {
  try {
    const audio = new Audio(URGENT_SOUND_URL);
    audio.volume = 0.5;
    audio.play().catch(() => {});
  } catch {}
}

function timeAgo(date) {
  try {
    return formatDistanceToNow(new Date(date), { addSuffix: true });
  } catch {
    return '';
  }
}

export default function UrgentAnnouncements({ announcements = [], onDismiss, onMarkRead }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [dismissed, setDismissed] = useState(new Set());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const prevIdsRef = useRef(new Set());
  const intervalRef = useRef(null);

  const visible = announcements.filter((a) => !dismissed.has(a._id));
  const pinned = visible.filter((a) => a.pinned);
  const unpinned = visible.filter((a) => !a.pinned);
  const sorted = [...pinned, ...unpinned];

  const critical = sorted.find((a) => a.priority === 'critical' || a.urgent);

  useEffect(() => {
    const currentIds = new Set(announcements.map((a) => a._id));
    const prevIds = prevIdsRef.current;
    const brandNew = [...currentIds].filter((id) => !prevIds.has(id));
    if (brandNew.length > 0) {
      playUrgentSound();
    }
    prevIdsRef.current = currentIds;
  }, [announcements]);

  useEffect(() => {
    if (sorted.length <= 1) return;
    intervalRef.current = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % sorted.length);
    }, 5000);
    return () => clearInterval(intervalRef.current);
  }, [sorted.length]);

  const handleDismiss = useCallback(
    (id) => {
      setDismissed((prev) => new Set([...prev, id]));
      onDismiss?.(id);
      if (currentIndex >= sorted.length - 1) setCurrentIndex(0);
    },
    [currentIndex, sorted.length, onDismiss]
  );

  const handlePrev = () => {
    clearInterval(intervalRef.current);
    setCurrentIndex((prev) => (prev - 1 + sorted.length) % sorted.length);
  };

  const handleNext = () => {
    clearInterval(intervalRef.current);
    setCurrentIndex((prev) => (prev + 1) % sorted.length);
  };

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape' && isFullscreen) setIsFullscreen(false);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isFullscreen]);

  if (sorted.length === 0) return null;

  const current = sorted[currentIndex] || sorted[0];

  return (
    <>
      <div className={`ku-urgent-banner ${current?.priority === 'critical' || current?.urgent ? 'critical' : ''}`}>
        <div className="ku-urgent-icon">
          <FiAlertTriangle size={20} />
        </div>

        <div className="ku-urgent-content">
          <AnimatePresence mode="wait">
            <motion.div
              key={current?._id}
              className="ku-urgent-text"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              {current?.pinned && <span className="ku-urgent-pin">📌</span>}
              <strong>{current?.title}</strong>
              <span className="ku-urgent-message">{current?.message || current?.content}</span>
              <span className="ku-urgent-time">{timeAgo(current?.createdAt)}</span>
            </motion.div>
          </AnimatePresence>
        </div>

        {sorted.length > 1 && (
          <div className="ku-urgent-nav">
            <button onClick={handlePrev} className="ku-urgent-nav-btn" aria-label="Previous">
              <FiChevronLeft size={16} />
            </button>
            <span className="ku-urgent-counter">
              {currentIndex + 1}/{sorted.length}
            </span>
            <button onClick={handleNext} className="ku-urgent-nav-btn" aria-label="Next">
              <FiChevronRight size={16} />
            </button>
          </div>
        )}

        <button
          onClick={() => setIsFullscreen(true)}
          className="ku-urgent-action-btn"
          aria-label="Fullscreen"
        >
          <FiMaximize2 size={14} />
        </button>

        <button
          onClick={() => handleDismiss(current?._id)}
          className="ku-urgent-dismiss"
          aria-label="Dismiss"
        >
          <FiX size={16} />
        </button>
      </div>

      <AnimatePresence>
        {isFullscreen && critical && (
          <motion.div
            className="ku-urgent-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="ku-urgent-overlay-card"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
            >
              <div className="ku-urgent-overlay-header">
                <FiAlertTriangle size={32} className="ku-urgent-overlay-icon" />
                <h2>Critical Alert</h2>
                <button
                  onClick={() => setIsFullscreen(false)}
                  className="ku-urgent-overlay-close"
                  aria-label="Close"
                >
                  <FiMinimize2 size={20} />
                </button>
              </div>
              <h3>{critical.title}</h3>
              <p>{critical.message || critical.content}</p>
              <span className="ku-urgent-overlay-time">{timeAgo(critical.createdAt)}</span>
              <button
                onClick={() => {
                  handleDismiss(critical._id);
                  setIsFullscreen(false);
                }}
                className="ku-urgent-overlay-dismiss"
              >
                Dismiss
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
