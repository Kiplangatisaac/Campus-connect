import React, { useEffect, useRef } from 'react';

export default function MediaViewer({ media, onClose }) {
  const overlayRef = useRef(null);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [onClose]);

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  if (!media) return null;

  const renderContent = () => {
    if (media.type?.startsWith('image/') || media.url?.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
      return <img src={media.url} alt="" className="media-viewer-image" />;
    }
    if (media.type?.startsWith('video/') || media.url?.match(/\.(mp4|webm|ogg)$/i)) {
      return (
        <video controls autoPlay className="media-viewer-video">
          <source src={media.url} type={media.type} />
          Your browser does not support video.
        </video>
      );
    }
    if (media.type?.startsWith('audio/') || media.url?.match(/\.(mp3|wav|ogg|m4a)$/i)) {
      return (
        <div className="media-viewer-audio">
          <div className="audio-icon">🎵</div>
          <audio controls autoPlay>
            <source src={media.url} type={media.type} />
            Your browser does not support audio.
          </audio>
        </div>
      );
    }
    return (
      <div className="media-viewer-file">
        <div className="file-icon">📎</div>
        <p>{media.name || 'File'}</p>
        <a href={media.url} download className="download-btn">Download</a>
      </div>
    );
  };

  return (
    <div className="media-viewer-overlay" ref={overlayRef} onClick={handleOverlayClick}>
      <div className="media-viewer-content">
        <button className="media-viewer-close" onClick={onClose}>✕</button>
        {renderContent()}
      </div>
    </div>
  );
}
