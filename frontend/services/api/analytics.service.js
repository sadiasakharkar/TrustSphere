import { apiRequest } from './apiClient';

export async function getAnalyticsWorkspace() {
  const response = await apiRequest('/api/metrics/soc');
  const data = response.data || {};
  const severityDistribution = data.severityDistribution || {};
  const labels = Object.keys(severityDistribution);
  const severityValues = labels.map((label) => severityDistribution[label]);

  return {
    schemaVersion: 'frontend.analytics.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    severityLabels: labels,
    severityValues,
    riskDistribution: Array.isArray(data.riskDistribution) ? data.riskDistribution : [],
    recentActivity: Array.isArray(data.recentActivity) ? data.recentActivity : []
  };
}
