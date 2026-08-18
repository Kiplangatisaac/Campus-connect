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
  cleanup
} from '../services/webrtc';

export default function AudioCall({ targetUser, onEnd }) {
  const { user } = useAuth();
  const { emit } = useSocket();
  const [callState, setCallState] = useState('calling');
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [duration, setDuration] = useState(0);
  const remoteAudioRef = useRef(null);
  const timerRef = useRef(null);

  const handleRemoteStream = useCallback((stream) => {
    if (remoteAudioRef.current) {
      remoteAudioRef.current.srcObject = stream;
    }
  }, []);

  const handleIceCandidate = useCallback((candidate) => {
    emit('webrtc:ice-candidate', { targetId: targetUser._id, candidate });
  }, [emit, targetUser]);

  useEffect(() => {
    let cancelled = false;

    const initCall = async () => {
      const stream = await getLocalStream(false, true);
      if (cancelled || !stream) return;

      createPeerConnection(handleRemoteStream, handleIceCandidate);
      addLocalTracks();

      const offer = await createOffer();
      if (cancelled || !offer) return;

      emit('webrtc:audio-call', {
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

    emit('webrtc:audio-accept-listen', (data) => handleCallAccepted(data));
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

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-call-overlay">
      <div className="audio-call-container">
        <div className="audio-call-avatar">
          <img
            src={targetUser.avatar || `https://ui-avatars.com/api/?name=${targetUser.name}&background=1a237e&color=fff&size=120`}
            alt=""
          />
          {callState === 'calling' && <div className="calling-pulse"></div>}
        </div>
        <h3 className="audio-call-name">{targetUser.name}</h3>
        <span className="audio-call-status">
          {callState === 'calling' ? 'Calling...' : formatDuration(duration)}
        </span>
        <audio ref={remoteAudioRef} autoPlay />
        <div className="audio-call-controls">
          <button
            className={`call-control-btn ${audioEnabled ? '' : 'disabled'}`}
            onClick={toggleMic}
          >
            {audioEnabled ? '🎤' : '🔇'}
          </button>
          <button className="call-control-btn end-call" onClick={endCall}>
            📞
          </button>
        </div>
      </div>
    </div>
  );
}
