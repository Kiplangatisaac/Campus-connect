import React, { useState, useEffect } from 'react';
import './InstallBanner.css';

const PLATFORMS = [
  {
    id: 'android',
    name: 'Android',
    icon: '📱',
    description: 'Install on your Android device',
    fileSize: '~15 MB',
    format: 'APK',
    downloadUrl: '/api/downloads/android',
  },
  {
    id: 'windows',
    name: 'Windows',
    icon: '💻',
    description: 'Install on your Windows PC',
    fileSize: '~25 MB',
    format: 'EXE',
    downloadUrl: '/api/downloads/windows',
  },
  {
    id: 'linux',
    name: 'Linux',
    icon: '🐧',
    description: 'Install on your Linux system',
    fileSize: '~12 MB',
    format: 'DEB',
    downloadUrl: '/api/downloads/linux',
  },
  {
    id: 'web',
    name: 'Web App',
    icon: '🌐',
    description: 'Add to home screen',
    fileSize: 'N/A',
    format: 'PWA',
    downloadUrl: null,
  },
];

const InstallBanner = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showBanner, setShowBanner] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [, setIsInstalling] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowBanner(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setShowBanner(false);
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstallClick = () => {
    setShowModal(true);
  };

  const handlePlatformSelect = async (platform) => {
    setSelectedPlatform(platform);

    if (platform.id === 'web' && deferredPrompt) {
      // Native PWA install
      setIsInstalling(true);
      try {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
          setShowBanner(false);
        }
      } catch (err) {
        console.error('Install failed:', err);
      }
      setIsInstalling(false);
      setDeferredPrompt(null);
    } else if (platform.downloadUrl) {
      // Direct download
      window.location.href = platform.downloadUrl;
    }
    setShowModal(false);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedPlatform(null);
  };

  if (!showBanner) return null;

  return (
    <>
      {/* Bottom install banner */}
      <div className="install-banner">
        <div className="install-banner-content">
          <img src="/images/kyu-logo.png" alt="KyU" className="install-banner-logo" />
          <div className="install-banner-text">
            <strong>Install KyU Campus</strong>
            <span>Get the full experience on any device</span>
          </div>
        </div>
        <div className="install-banner-actions">
          <button className="install-btn-primary" onClick={handleInstallClick}>
            Install Now
          </button>
          <button className="install-btn-dismiss" onClick={() => setShowBanner(false)}>
            ✕
          </button>
        </div>
      </div>

      {/* Platform selection modal */}
      {showModal && (
        <div className="install-modal-overlay" onClick={handleCloseModal}>
          <div className="install-modal" onClick={(e) => e.stopPropagation()}>
            <div className="install-modal-header">
              <img src="/images/kyu-logo.png" alt="KyU" className="install-modal-logo" />
              <h2>Install KyU Campus</h2>
              <p>Choose your platform to install</p>
              <button className="install-modal-close" onClick={handleCloseModal}>✕</button>
            </div>

            <div className="install-platforms">
              {PLATFORMS.map((platform) => (
                <div
                  key={platform.id}
                  className={`install-platform-card ${selectedPlatform?.id === platform.id ? 'selected' : ''}`}
                  onClick={() => handlePlatformSelect(platform)}
                >
                  <span className="platform-icon">{platform.icon}</span>
                  <div className="platform-info">
                    <h3>{platform.name}</h3>
                    <p>{platform.description}</p>
                    <span className="platform-meta">
                      {platform.format} • {platform.fileSize}
                    </span>
                  </div>
                  <span className="platform-arrow">→</span>
                </div>
              ))}
            </div>

            <div className="install-modal-footer">
              <p>ISO 9001:2015 Certified • Kerugoya University</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default InstallBanner;
