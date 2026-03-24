import { apiRequest } from './apiClient';

/** @returns {Promise<import('./contracts').MonitoringResponse>} */
export async function getLiveEvents() {
  const response = await apiRequest('/api/events/live');
  return {
    schemaVersion: 'frontend.monitoring.v2',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    events: response.data
  };
}

export async function getDetectionsFeed() {
  const response = await apiRequest('/api/detections/feed');
  return {
    schemaVersion: 'frontend.detections.feed.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    detectors: response.data
  };
}
