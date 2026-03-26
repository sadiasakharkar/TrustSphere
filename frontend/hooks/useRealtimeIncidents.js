import { useEffect, useRef } from 'react';
import { getApiBaseUrl } from '../services/api/apiClient';

export function useRealtimeIncidents({ enabled = true, onEvent } = {}) {
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    if (!enabled || typeof window === 'undefined' || typeof onEventRef.current !== 'function') return undefined;
    const base = getApiBaseUrl().replace(/^http/, 'ws');
    const socket = new WebSocket(`${base}/ws/incidents`);
    socket.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data);
        if (typeof onEventRef.current === 'function') onEventRef.current(payload);
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
  }, [enabled]);
}
