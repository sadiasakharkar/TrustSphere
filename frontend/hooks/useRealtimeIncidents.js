import { useEffect, useRef } from 'react';

export function useRealtimeIncidents({ enabled = true, onEvent } = {}) {
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    if (!enabled || typeof window === 'undefined' || typeof onEventRef.current !== 'function') return undefined;
    return undefined;
  }, [enabled]);
}
