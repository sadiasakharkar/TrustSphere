const DEFAULT_AUTH_BASE_URL =
  process.env.NEXT_PUBLIC_AUTH_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  'http://127.0.0.1:8000';
const DEFAULT_API_KEY = process.env.NEXT_PUBLIC_TRUSTSPHERE_API_KEY || 'trustsphere-local-dev-key';

function resolveAuthBaseUrl() {
  return DEFAULT_AUTH_BASE_URL.replace(/\/+$/, '');
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
  return authRequest('/auth/signup', payload);
}

export async function loginUser(payload) {
  return authRequest('/auth/login', payload);
}

export async function getCurrentUser(token) {
  return authGet('/auth/me', token);
}

export function getAuthBaseUrl() {
  return resolveAuthBaseUrl();
}
