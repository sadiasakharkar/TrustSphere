const DEFAULT_AUTH_BASE_URL = process.env.NEXT_PUBLIC_AUTH_API_BASE_URL || '';

function resolveAuthBaseUrl() {
  return DEFAULT_AUTH_BASE_URL ? DEFAULT_AUTH_BASE_URL.replace(/\/+$/, '') : '';
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
    },
    body: JSON.stringify(payload),
  });

  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data?.message || 'Authentication request failed.');
  }

  return data;
}

async function authGet(path, token) {
  const response = await fetch(`${resolveAuthBaseUrl()}${path}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data?.message || 'Authentication request failed.');
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
