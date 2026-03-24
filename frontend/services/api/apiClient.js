import { envelopeTimestamp, unwrapApiEnvelope } from './contracts';
import { isDemoModeEnabled, resolveDemoFallback } from './demoFallbacks';

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
const DEFAULT_API_KEY = process.env.NEXT_PUBLIC_TRUSTSPHERE_API_KEY || 'trustsphere-local-dev-key';
const DEFAULT_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS || 12000);
const DEFAULT_RETRIES = 1;
const DEMO_MODE = isDemoModeEnabled();

function resolveBaseUrl() {
  return DEFAULT_BASE_URL.replace(/\/+$/, '');
}

function getStoredToken() {
  if (typeof window === 'undefined') return '';
  return window.localStorage.getItem('trustsphere.authToken') || '';
}

function buildHeaders(headers = {}) {
  const resolved = new Headers(headers);
  if (!resolved.has('Content-Type')) resolved.set('Content-Type', 'application/json');
  if (!resolved.has('x-api-key')) resolved.set('x-api-key', DEFAULT_API_KEY);
  const token = getStoredToken();
  if (token && !resolved.has('Authorization')) {
    resolved.set('Authorization', `Bearer ${token}`);
  }
  return resolved;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function shouldRetry(status, method, attempt) {
  if (attempt >= DEFAULT_RETRIES) return false;
  if (!['GET', 'HEAD'].includes((method || 'GET').toUpperCase())) return false;
  return status >= 500 || status === 429;
}

async function parseJson(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`Invalid JSON response from ${response.url}`);
  }
}

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
  const { timeoutMs = DEFAULT_TIMEOUT_MS, retries = DEFAULT_RETRIES, fallbackData = null, ...requestInit } = options;
  const method = (requestInit.method || 'GET').toUpperCase();
  const url = `${resolveBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        ...requestInit,
        method,
        headers: buildHeaders(requestInit.headers),
        signal: controller.signal
      });
      clearTimeout(timeout);
      const raw = await parseJson(response);

      if (!response.ok || raw?.success === false) {
        const errorMessage = raw?.error || `Request failed with status ${response.status}`;
        if (shouldRetry(response.status, method, attempt)) {
          await sleep(250 * (attempt + 1));
          continue;
        }
        const fallback = buildFallbackResult(path, method, fallbackData, new Error(errorMessage));
        if (fallback && DEMO_MODE) return fallback;
        const error = new Error(errorMessage);
        error.status = response.status;
        error.meta = raw?.meta || {};
        throw error;
      }

      const data = unwrapApiEnvelope(raw);
      return { data, meta: raw?.meta || { timestamp: envelopeTimestamp(raw) }, raw };
    } catch (error) {
      clearTimeout(timeout);
      const isAbort = error?.name === 'AbortError';
      if ((isAbort || !error?.status) && attempt < retries && ['GET', 'HEAD'].includes(method)) {
        await sleep(250 * (attempt + 1));
        continue;
      }
      const fallback = buildFallbackResult(path, method, fallbackData, error);
      if (fallback && DEMO_MODE) return fallback;
      if (isAbort) {
        throw new Error(`Request timed out after ${timeoutMs}ms`);
      }
      throw error;
    }
  }

  throw new Error(`Request failed after ${retries + 1} attempts`);
}

export function getApiBaseUrl() {
  return resolveBaseUrl();
}

export function isDemoMode() {
  return DEMO_MODE;
}
