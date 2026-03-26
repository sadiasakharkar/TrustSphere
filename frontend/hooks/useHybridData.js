import { useEffect, useMemo, useRef, useState } from 'react';
import { getBootstrapData, getDomainData, probeBackend, shouldPreferBootstrap } from '../services/dataProvider.js';

export function useHybridData(domain, params = {}, options = {}) {
  const {
    bootstrapDelayMs = 8000,
    pollIntervalMs = 6000,
    enabled = true
  } = options;

  const paramsKey = useMemo(() => JSON.stringify(params || {}), [params]);
  const [data, setData] = useState(() => getBootstrapData(domain, params));
  const [status, setStatus] = useState({
    mode: shouldPreferBootstrap() ? 'demo' : 'live',
    backendConnected: false,
    modelActive: false,
    loading: false
  });
  const lastDataRef = useRef(data);

  useEffect(() => {
    lastDataRef.current = data;
  }, [data]);

  useEffect(() => {
    if (!enabled) return undefined;
    let active = true;
    let pollTimer = null;

    const hydrateLive = async () => {
      const probe = await probeBackend();
      if (!active) return;
      if (!probe.connected) {
        setStatus((prev) => ({ ...prev, backendConnected: false, modelActive: false }));
        return;
      }
      try {
        const liveData = await getDomainData(domain, params);
        if (!active) return;
        setData(liveData || lastDataRef.current);
        setStatus({
          mode: 'live',
          backendConnected: true,
          modelActive: true,
          loading: false
        });
      } catch {
        if (!active) return;
        setData(lastDataRef.current || getBootstrapData(domain, params));
        setStatus((prev) => ({
          ...prev,
          backendConnected: false,
          modelActive: false,
          mode: prev.mode === 'live' ? 'demo' : prev.mode
        }));
      }
    };

    setData(getBootstrapData(domain, params));
    setStatus((prev) => ({
      ...prev,
      mode: 'demo',
      backendConnected: false,
      modelActive: false,
      loading: false
    }));

    const bootstrapTimer = window.setTimeout(() => {
      hydrateLive();
      pollTimer = window.setInterval(hydrateLive, pollIntervalMs);
    }, bootstrapDelayMs);

    return () => {
      active = false;
      window.clearTimeout(bootstrapTimer);
      if (pollTimer) window.clearInterval(pollTimer);
    };
  }, [domain, paramsKey, bootstrapDelayMs, pollIntervalMs, enabled]);

  return { data, status };
}
