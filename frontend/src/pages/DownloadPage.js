import React, { useState } from 'react';

const PLATFORMS = [
  {
    id: 'playstore',
    name: 'Google Play Store',
    icon: '▶️',
    description: 'Get it on Google Play - automatic updates',
    fileSize: '~15 MB',
    format: 'Play Store',
    downloadUrl: 'https://play.google.com/store/apps/details?id=com.kyucampus.connect',
    external: true,
    minVersion: 'Android 8.0+',
    instructions: [
      'Tap "Install" on the Google Play Store page',
      'App installs automatically',
      'Open from your home screen or app drawer',
      'Enable auto-updates for latest features',
    ],
  },
  {
    id: 'appstore',
    name: 'Apple App Store',
    icon: '',
    description: 'Download on the App Store - automatic updates',
    fileSize: '~20 MB',
    format: 'App Store',
    downloadUrl: 'https://apps.apple.com/app/kyu-campus-connect/id000000000',
    external: true,
    minVersion: 'iOS 15.0+',
    instructions: [
      'Tap "Get" on the App Store page',
      'Confirm with Face ID, Touch ID, or password',
      'App installs automatically',
      'Open from your home screen',
    ],
  },
  {
    id: 'android',
    name: 'Android (Direct APK)',
    icon: '📱',
    description: 'Install directly on your Android device',
    fileSize: '~15 MB',
    format: 'APK',
    downloadUrl: '/api/downloads/android',
    minVersion: 'Android 6.0+',
    instructions: [
      'Download the APK file',
      'Enable "Unknown sources" in Settings > Security',
      'Open the downloaded file',
      'Follow the installation prompts',
    ],
  },
  {
    id: 'windows',
    name: 'Windows',
    icon: '💻',
    description: 'Install on your Windows PC',
    fileSize: '~25 MB',
    format: 'EXE',
    downloadUrl: '/api/downloads/windows',
    minVersion: 'Windows 10+',
    instructions: [
      'Download the installer',
      'Double-click the .exe file',
      'Follow the installation wizard',
      'Launch from Start Menu or Desktop',
    ],
  },
  {
    id: 'linux',
    name: 'Linux',
    icon: '🐧',
    description: 'Install on your Linux system',
    fileSize: '~12 MB',
    format: 'DEB',
    downloadUrl: '/api/downloads/linux',
    minVersion: 'Ubuntu 20.04+',
    instructions: [
      'Download the .deb package',
      'Run: sudo dpkg -i KyU-CampusConnect.deb',
      'Or install via Software Center',
      'Launch from Applications menu',
    ],
  },
  {
    id: 'appimage',
    name: 'Linux AppImage',
    icon: '📦',
    description: 'Portable Linux app - no installation required',
    fileSize: '~50 MB',
    format: 'AppImage',
    downloadUrl: '/api/downloads/appimage',
    minVersion: 'Any Linux',
    instructions: [
      'Download the AppImage file',
      'Make it executable: chmod +x KyU-CampusConnect.AppImage',
      'Double-click to run',
      'Optional: Move to /usr/local/bin for system-wide access',
    ],
  },
  {
    id: 'web',
    name: 'Web App (PWA)',
    icon: '🌐',
    description: 'Add to your home screen - no download needed',
    fileSize: 'N/A',
    format: 'PWA',
    downloadUrl: null,
    minVersion: 'Any modern browser',
    instructions: [
      'Open this site in Chrome/Edge/Safari',
      'Click "Install" in the address bar',
      'Or use the install prompt below',
      'Access from your home screen',
    ],
  },
];

const DownloadPage = () => {
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = (platform) => {
    if (platform.downloadUrl) {
      if (platform.external) {
        window.open(platform.downloadUrl, '_blank', 'noopener,noreferrer');
      } else {
        const a = document.createElement('a');
        a.href = platform.downloadUrl;
        a.download = '';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <img src="/images/kyu-logo.png" alt="KyU Campus" style={styles.logo} />
        <h1 style={styles.title}>Download KyU Campus</h1>
        <p style={styles.subtitle}>
          Innovative Technology for a Dynamic World
        </p>
        <p style={styles.version}>Version 1.0.0 • ISO 9001:2015 Certified</p>
      </div>

      <div style={styles.platforms}>
        {PLATFORMS.map((platform) => (
          <div
            key={platform.id}
            style={{
              ...styles.card,
              ...(selectedPlatform?.id === platform.id ? styles.cardSelected : {}),
            }}
            onClick={() => setSelectedPlatform(platform)}
          >
            <span style={styles.icon}>{platform.icon}</span>
            <div style={styles.cardContent}>
              <h3 style={styles.cardTitle}>{platform.name}</h3>
              <p style={styles.cardDesc}>{platform.description}</p>
              <div style={styles.cardMeta}>
                <span style={styles.badge}>{platform.format}</span>
                <span style={styles.badge}>{platform.fileSize}</span>
                <span style={styles.badge}>{platform.minVersion}</span>
              </div>
            </div>
            <button
              style={styles.downloadBtn}
              onClick={(e) => {
                e.stopPropagation();
                handleDownload(platform);
              }}
              disabled={downloading || !platform.downloadUrl}
            >
              {platform.downloadUrl ? (platform.external ? '↗ Get' : '↓ Download') : 'Install'}
            </button>
          </div>
        ))}
      </div>

      {selectedPlatform && (
        <div style={styles.instructions}>
          <h3 style={styles.instructionsTitle}>
            {selectedPlatform.icon} {selectedPlatform.name} Installation Guide
          </h3>
          <ol style={styles.instructionsList}>
            {selectedPlatform.instructions.map((step, idx) => (
              <li key={idx} style={styles.instructionItem}>
                {step}
              </li>
            ))}
          </ol>
          {selectedPlatform.downloadUrl && (
            <button
              style={styles.primaryBtn}
              onClick={() => handleDownload(selectedPlatform)}
              disabled={downloading}
            >
              {downloading ? 'Downloading...' : selectedPlatform.external ? `Get ${selectedPlatform.name}` : `Download ${selectedPlatform.name} Now`}
            </button>
          )}
        </div>
      )}

      <div style={styles.footer}>
        <p>Kerugoya University • P.O.Box 143-10300 Kerugoya</p>
        <p>+254 709 742000 • info@kyu.ac.ke</p>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #1a365d 0%, #2c5282 100%)',
    padding: '40px 20px',
    color: 'white',
  },
  header: {
    textAlign: 'center',
    marginBottom: '40px',
  },
  logo: {
    width: '80px',
    height: '80px',
    borderRadius: '16px',
    marginBottom: '16px',
    objectFit: 'contain',
  },
  title: {
    fontSize: '32px',
    fontWeight: '700',
    margin: '0 0 8px 0',
  },
  subtitle: {
    fontSize: '16px',
    opacity: 0.9,
    margin: '0 0 8px 0',
  },
  version: {
    fontSize: '14px',
    opacity: 0.7,
    margin: 0,
  },
  platforms: {
    maxWidth: '800px',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  card: {
    background: 'white',
    borderRadius: '12px',
    padding: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    color: '#1a365d',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  },
  cardSelected: {
    outline: '3px solid #2c5282',
    background: '#f7fafc',
  },
  icon: {
    fontSize: '32px',
    width: '56px',
    height: '56px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#f7fafc',
    borderRadius: '12px',
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    margin: '0 0 4px 0',
    fontSize: '18px',
    fontWeight: '600',
  },
  cardDesc: {
    margin: '0 0 8px 0',
    fontSize: '14px',
    color: '#718096',
  },
  cardMeta: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  badge: {
    fontSize: '12px',
    padding: '2px 8px',
    background: '#e2e8f0',
    borderRadius: '4px',
    color: '#4a5568',
  },
  downloadBtn: {
    background: '#2c5282',
    color: 'white',
    border: 'none',
    padding: '12px 24px',
    borderRadius: '8px',
    fontWeight: '600',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    whiteSpace: 'nowrap',
  },
  instructions: {
    maxWidth: '800px',
    margin: '32px auto 0',
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    color: '#1a365d',
  },
  instructionsTitle: {
    fontSize: '18px',
    fontWeight: '600',
    margin: '0 0 16px 0',
  },
  instructionsList: {
    margin: '0 0 20px 0',
    paddingLeft: '20px',
  },
  instructionItem: {
    marginBottom: '8px',
    fontSize: '14px',
    color: '#4a5568',
  },
  primaryBtn: {
    background: '#1a365d',
    color: 'white',
    border: 'none',
    padding: '14px 32px',
    borderRadius: '8px',
    fontWeight: '600',
    fontSize: '16px',
    cursor: 'pointer',
    width: '100%',
    transition: 'all 0.2s',
  },
  footer: {
    textAlign: 'center',
    marginTop: '40px',
    opacity: 0.7,
    fontSize: '14px',
  },
};

export default DownloadPage;
