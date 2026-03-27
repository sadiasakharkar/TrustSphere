import { envelopeTimestamp, unwrapApiEnvelope } from './contracts';
import { isDemoModeEnabled, resolveDemoFallback } from './demoFallbacks';

const DEMO_MODE = isDemoModeEnabled();

/**
 * @param {string} path
 * @param {RequestInit & { timeoutMs?: number, retries?: number }} [options]
 * @returns {Promise<{data:any, meta:any, raw:any}>}
 */
function buildFallbackResult(path, method, fallbackData, error) {
  const resolved = typeof fallbackData === 'function' ? fallbackData() : fallbackData ?? resolveDemoFallback(path, method);
  if (resolved == null) return null;
  return {
    data: resolved,
    meta: {
      timestamp: new Date().toISOString(),
      fallback: true,
      demoMode: DEMO_MODE,
      error: error?.message || null,
    },
    raw: {
      success: true,
      data: resolved,
      meta: {
        timestamp: new Date().toISOString(),
        fallback: true,
        demoMode: DEMO_MODE,
      },
      error: null,
    },
  };
}

export async function apiRequest(path, options = {}) {
  const { fallbackData = null, ...requestInit } = options;
  const method = (requestInit.method || 'GET').toUpperCase();
  const fallback = buildFallbackResult(path, method, fallbackData, null);

  if (fallback) {
    return fallback;
  }

  return {
    data: unwrapApiEnvelope(null),
    meta: { timestamp: new Date().toISOString(), demoMode: DEMO_MODE },
    raw: null,
  };
}

export function getApiBaseUrl() {
  return 'demo://local';
}

export function isDemoMode() {
  return true;
}
