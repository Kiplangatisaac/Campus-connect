import { io } from 'socket.io-client';

let socket = null;

export function getSocket() {
  return socket;
}

export function initSocket(token) {
  if (socket?.connected) return socket;

  socket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:5000', {
    auth: { token },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000
  });

  return socket;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

export function emitEvent(event, data) {
  socket?.emit(event, data);
}

export function onEvent(event, callback) {
  socket?.on(event, callback);
}

export function offEvent(event, callback) {
  socket?.off(event, callback);
}
