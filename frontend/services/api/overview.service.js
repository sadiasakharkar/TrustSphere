import { apiRequest } from './apiClient';

/** @returns {Promise<import('./contracts').OverviewResponse>} */
export async function getOverviewSummary() {
  const [summary, metrics] = await Promise.all([
    apiRequest('/api/overview/summary'),
    apiRequest('/api/metrics/soc')
  ]);

  return {
    schemaVersion: 'frontend.overview.v2',
    generatedAt: summary.meta?.timestamp || new Date().toISOString(),
    sourceMode: summary.meta?.mode || 'bootstrap',
    streamCounter: summary.meta?.streamCounter || 0,
    ...summary.data,
    analytics: metrics.data
  };
}

export async function getSocMetrics() {
  const response = await apiRequest('/api/metrics/soc');
  return {
    schemaVersion: 'frontend.metrics.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    ...response.data
  };
}
