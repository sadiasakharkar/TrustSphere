import { getApiBaseUrl } from './apiClient';

async function parseResponse(response) {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.error || `Request failed with status ${response.status}`);
  }
  return payload;
}

export async function analyzeEmail(input) {
  const response = await fetch(`${getApiBaseUrl()}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input })
  });
  return parseResponse(response);
}

export async function getEmailHistory() {
  const response = await fetch(`${getApiBaseUrl()}/history`);
  return parseResponse(response);
}

export async function clearEmailHistory() {
  const response = await fetch(`${getApiBaseUrl()}/history`, {
    method: 'DELETE'
  });
  return parseResponse(response);
}
