import { useEffect } from 'react';
import { getApiBaseUrl } from '../services/api/apiClient';

export function useRealtimeIncidents({ enabled = true, onEvent } = {}) {
  useEffect(() => {
    if (!enabled || typeof window === 'undefined' || typeof onEvent !== 'function') return undefined;
    const protocol = getApiBaseUrl().startsWith('https') ? 'wss' : 'ws';
    const base = getApiBaseUrl().replace(/^http/, 'ws');
    const socket = new WebSocket(`${base}/ws/incidents`);
    socket.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data);
        onEvent(payload);
      } catch {
        // Ignore malformed realtime payloads to preserve UI stability.
      }
    };
    socket.onerror = () => {
      socket.close();
    };
    return () => {
      try {
        socket.close();
      } catch {
        // Ignore close errors.
      }
    };
  }, [enabled, onEvent]);
}
