const ICE_SERVERS = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
};

let peerConnection = null;
let localStream = null;
let remoteStream = null;

export function createPeerConnection(onRemoteStream, onIceCandidate) {
  peerConnection = new RTCPeerConnection(ICE_SERVERS);

  peerConnection.onicecandidate = (event) => {
    if (event.candidate && onIceCandidate) {
      onIceCandidate(event.candidate);
    }
  };

  peerConnection.ontrack = (event) => {
    remoteStream = event.streams[0];
    if (onRemoteStream) onRemoteStream(remoteStream);
  };

  peerConnection.onconnectionstatechange = () => {
    console.log('Connection state:', peerConnection.connectionState);
  };

  return peerConnection;
}

export async function getLocalStream(video = true, audio = true) {
  try {
    localStream = await navigator.mediaDevices.getUserMedia({
      video: video ? { width: 640, height: 480 } : false,
      audio
    });
    return localStream;
  } catch (err) {
    console.error('Failed to get local stream:', err);
    return null;
  }
}

export async function createOffer() {
  if (!peerConnection) return null;
  const offer = await peerConnection.createOffer({
    offerToReceiveAudio: true,
    offerToReceiveVideo: true
  });
  await peerConnection.setLocalDescription(offer);
  return offer;
}

export async function createAnswer() {
  if (!peerConnection) return null;
  const answer = await peerConnection.createAnswer();
  await peerConnection.setLocalDescription(answer);
  return answer;
}

export async function setRemoteDescription(sdp) {
  if (!peerConnection) return;
  await peerConnection.setRemoteDescription(new RTCSessionDescription(sdp));
}

export async function addIceCandidate(candidate) {
  if (!peerConnection) return;
  await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
}

export function addLocalTracks() {
  if (!peerConnection || !localStream) return;
  localStream.getTracks().forEach(track => {
    peerConnection.addTrack(track, localStream);
  });
}

export function toggleAudio() {
  if (!localStream) return false;
  const audioTrack = localStream.getAudioTracks()[0];
  if (audioTrack) {
    audioTrack.enabled = !audioTrack.enabled;
    return audioTrack.enabled;
  }
  return false;
}

export function toggleVideo() {
  if (!localStream) return false;
  const videoTrack = localStream.getVideoTracks()[0];
  if (videoTrack) {
    videoTrack.enabled = !videoTrack.enabled;
    return videoTrack.enabled;
  }
  return false;
}

export function stopStream(stream) {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
}

export function cleanup() {
  stopStream(localStream);
  stopStream(remoteStream);
  if (peerConnection) {
    peerConnection.close();
    peerConnection = null;
  }
  localStream = null;
  remoteStream = null;
}

export function getLocalStreamRef() {
  return localStream;
}

export function getRemoteStreamRef() {
  return remoteStream;
}
