const DEFAULT_AUTH_BASE_URL =
  process.env.NEXT_PUBLIC_AUTH_API_BASE_URL ||
  '';
const DEFAULT_API_KEY = process.env.NEXT_PUBLIC_TRUSTSPHERE_API_KEY || 'trustsphere-local-dev-key';

function shouldUseSameOrigin(baseUrl) {
  if (!baseUrl) return true;

  if (typeof window === 'undefined') {
    return false;
  }

  try {
    const resolved = new URL(baseUrl, window.location.origin);
    const isLocalAuthHost = ['127.0.0.1', 'localhost'].includes(resolved.hostname);
    const isLocalAppHost = ['127.0.0.1', 'localhost'].includes(window.location.hostname);
    return isLocalAuthHost && !isLocalAppHost;
  } catch {
    return false;
  }
}

function resolveAuthBaseUrl() {
  const baseUrl = DEFAULT_AUTH_BASE_URL ? DEFAULT_AUTH_BASE_URL.replace(/\/+$/, '') : '';
  if (shouldUseSameOrigin(baseUrl)) {
    return '';
  }
  return baseUrl;
}

async function parseResponse(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    throw new Error('Invalid authentication server response.');
  }
}

async function authRequest(path, payload) {
  const response = await fetch(`${resolveAuthBaseUrl()}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': DEFAULT_API_KEY,
    },
    body: JSON.stringify(payload),
  });

  const payloadData = await parseResponse(response);
  const data = payloadData?.data ?? payloadData;
  const errorMessage = payloadData?.error || data?.message || 'Authentication request failed.';
  if (!response.ok || payloadData?.success === false) {
    throw new Error(errorMessage);
  }

  return data;
}

async function authGet(path, token) {
  const response = await fetch(`${resolveAuthBaseUrl()}${path}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
      'x-api-key': DEFAULT_API_KEY,
    },
  });

  const payloadData = await parseResponse(response);
  const data = payloadData?.data ?? payloadData;
  const errorMessage = payloadData?.error || data?.message || 'Authentication request failed.';
  if (!response.ok || payloadData?.success === false) {
    throw new Error(errorMessage);
  }

  return data;
}

export async function signupUser(payload) {
  return authRequest('/api/auth/signup', payload);
}

export async function loginUser(payload) {
  return authRequest('/api/auth/login', payload);
}

export async function getCurrentUser(token) {
  return authGet('/api/auth/me', token);
}

export function getAuthBaseUrl() {
  return resolveAuthBaseUrl() || 'same-origin /api';
}
