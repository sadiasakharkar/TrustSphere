import { apiRequest } from './apiClient';

/** @returns {Promise<import('./contracts').TriageResponse>} */
export async function getIncidents() {
  const response = await apiRequest('/api/incidents');
  return {
    schemaVersion: 'frontend.triage.v2',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    queue: response.data
  };
}

/** @returns {Promise<import('./contracts').IncidentResponse>} */
export async function getIncidentDetail(id) {
  const response = await apiRequest(`/api/incidents/${encodeURIComponent(id)}`);
  return {
    schemaVersion: 'frontend.incident.v2',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    ...response.data
  };
}

export async function updateIncidentStatus(id, status) {
  const response = await apiRequest(`/api/incidents/${encodeURIComponent(id)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status })
  });
  return response.data;
}

export async function assignIncident(id, assignee) {
  const response = await apiRequest(`/api/incidents/${encodeURIComponent(id)}/assign`, {
    method: 'PATCH',
    body: JSON.stringify({ assignee })
  });
  return response.data;
}
