import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSocket } from '../context/SocketContext';
import { useAuth } from '../context/AuthContext';
import {
  createPeerConnection,
  getLocalStream,
  createOffer,
  setRemoteDescription,
  addIceCandidate,
  addLocalTracks,
  toggleAudio,
  toggleVideo,
  cleanup
} from '../services/webrtc';

export default function VideoCall({ targetUser, onEnd }) {
  const { user } = useAuth();
  const { emit } = useSocket();
  const [callState, setCallState] = useState('calling');
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [duration, setDuration] = useState(0);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const timerRef = useRef(null);

  const handleRemoteStream = useCallback((stream) => {
    if (remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = stream;
    }
  }, []);

  const handleIceCandidate = useCallback((candidate) => {
    emit('webrtc:ice-candidate', { targetId: targetUser._id, candidate });
  }, [emit, targetUser]);

  useEffect(() => {
    let cancelled = false;

    const initCall = async () => {
      const stream = await getLocalStream(true, true);
      if (cancelled || !stream) return;

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      createPeerConnection(handleRemoteStream, handleIceCandidate);
      addLocalTracks();

      const offer = await createOffer();
      if (cancelled || !offer) return;

      emit('webrtc:call', {
        targetId: targetUser._id,
        offer,
        callerName: user.name,
        callerAvatar: user.avatar
      });
    };

    const handleCallAccepted = async ({ answer }) => {
      await setRemoteDescription(answer);
      setCallState('connected');
      timerRef.current = setInterval(() => setDuration(d => d + 1), 1000);
    };

    const handleIceCandidateReceived = async ({ candidate }) => {
      await addIceCandidate(candidate);
    };

    const handleCallEnded = () => {
      endCall();
    };

    initCall();

    emit('webrtc:accept-listen', (data) => handleCallAccepted(data));
    emit('webrtc:ice-candidate-received', (data) => handleIceCandidateReceived(data));
    emit('webrtc:end-listen', () => handleCallEnded());

    return () => {
      cancelled = true;
      cleanup();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetUser, user, emit, handleRemoteStream, handleIceCandidate]);

  const endCall = () => {
    cleanup();
    emit('webrtc:end', { targetId: targetUser._id });
    if (timerRef.current) clearInterval(timerRef.current);
    onEnd?.();
  };

  const toggleMic = () => {
    const enabled = toggleAudio();
    setAudioEnabled(enabled);
  };

  const toggleCam = () => {
    const enabled = toggleVideo();
    setVideoEnabled(enabled);
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="video-call-overlay">
      <div className="video-call-container">
        <div className="video-call-header">
          <span className="call-status">
            {callState === 'calling' && 'Calling...'}
            {callState === 'connected' && formatDuration(duration)}
          </span>
          <span className="call-partner">{targetUser.name}</span>
        </div>

        <div className="video-call-main">
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            className="remote-video"
          />
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            className="local-video"
          />
        </div>

        <div className="video-call-controls">
          <button
            className={`call-control-btn ${audioEnabled ? '' : 'disabled'}`}
            onClick={toggleMic}
          >
            {audioEnabled ? '🎤' : '🔇'}
          </button>
          <button
            className={`call-control-btn ${videoEnabled ? '' : 'disabled'}`}
            onClick={toggleCam}
          >
            {videoEnabled ? '📹' : '📷'}
          </button>
          <button className="call-control-btn end-call" onClick={endCall}>
            📞
          </button>
        </div>
      </div>
    </div>
  );
}
