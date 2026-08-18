import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import './WelcomePage.css';

const features = [
  'Real-time Chat',
  'Study Groups',
  'Campus Events',
  'AI Assistant',
  'File Sharing',
  'Voice & Video Calls',
  'Calendar Sync',
  'Moments Feed'
];

export default function WelcomePage() {
  const [featureIndex, setFeatureIndex] = useState(0);
  const [displayText, setDisplayText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const currentFeature = features[featureIndex];
    let timeout;

    if (!isDeleting && displayText === currentFeature) {
      timeout = setTimeout(() => setIsDeleting(true), 2000);
    } else if (isDeleting && displayText === '') {
      setIsDeleting(false);
      setFeatureIndex((prev) => (prev + 1) % features.length);
    } else {
      timeout = setTimeout(() => {
        setDisplayText(
          isDeleting
            ? currentFeature.substring(0, displayText.length - 1)
            : currentFeature.substring(0, displayText.length + 1)
        );
      }, isDeleting ? 50 : 100);
    }
    return () => clearTimeout(timeout);
  }, [displayText, isDeleting, featureIndex]);

  return (
    <div className="welcome-page">
      <div className="welcome-particles">
        {[...Array(20)].map((_, i) => (
          <div key={i} className="particle" style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 5}s`,
            animationDuration: `${5 + Math.random() * 10}s`
          }} />
        ))}
      </div>

      <motion.div
        className="welcome-card"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <div className="welcome-logo-section">
          <img
            src="/images/kyu-logo.png"
            alt="Kirinyaga University"
            className="welcome-logo"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        </div>

        <h1 className="welcome-uni-name">Kirinyaga University</h1>
        <p className="welcome-motto">Innovative Technology for a Dynamic World</p>
        <div className="welcome-iso">ISO 9001:2015 Certified</div>

        <h2 className="welcome-app-name">KyU Campus Connect</h2>
        <p className="welcome-desc">
          Your digital campus for communication, collaboration, and community.
          Connect with classmates, join study groups, stay updated with campus events,
          and experience the future of university life.
        </p>

        <div className="welcome-typing">
          <span className="typing-label">Powered by </span>
          <span className="typing-text">{displayText}</span>
          <span className="typing-cursor">|</span>
        </div>

        <Link to="/login" className="welcome-cta">
          Get Started <span className="cta-arrow">&rarr;</span>
        </Link>

        <Link to="/downloads" className="welcome-download">
          📲 Install App on Your Device
        </Link>

        <Link to="/login" className="welcome-signin">
          &#10140; Already have an account? Sign In
        </Link>

        <div className="welcome-features">
          {features.map((f, i) => (
            <span key={i} className="feature-tag">{f}</span>
          ))}
        </div>

        <div className="welcome-contact">
          <div className="contact-row">
            <span>&#128205; P.O.Box 143-10300, Kerugoya, Kenya</span>
          </div>
          <div className="contact-row">
            <span>&#128222; +254 709 742000</span>
            <span>&#9993; info@kyu.ac.ke</span>
          </div>
          <div className="contact-row">
            <a href="https://www.kyu.ac.ke" target="_blank" rel="noreferrer">&#127760; www.kyu.ac.ke</a>
            <a href="https://web.whatsapp.com/send?phone=254728499650" target="_blank" rel="noreferrer">&#128172; WhatsApp</a>
          </div>
          <div className="contact-socials">
            <a href="https://www.facebook.com/kirinyagauniversity" target="_blank" rel="noreferrer">Facebook</a>
            <a href="https://www.instagram.com/kirinyaga_university/" target="_blank" rel="noreferrer">Instagram</a>
            <a href="https://x.com/KyUniversity" target="_blank" rel="noreferrer">Twitter/X</a>
            <a href="https://www.youtube.com/channel/UCJOUsBeWOeD8DpYcwWyogxw" target="_blank" rel="noreferrer">YouTube</a>
            <a href="https://www.linkedin.com/school/kirinyaga-university/" target="_blank" rel="noreferrer">LinkedIn</a>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
