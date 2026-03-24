import { apiRequest } from './apiClient';

/** @returns {Promise<import('./contracts').GraphResponse>} */
export async function getAttackGraph(incidentId) {
  const path = incidentId ? `/api/attack-graph/${encodeURIComponent(incidentId)}` : '/api/attack-graph';
  const response = await apiRequest(path);
  return {
    schemaVersion: 'frontend.graph.v2',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    ...response.data
  };
}
