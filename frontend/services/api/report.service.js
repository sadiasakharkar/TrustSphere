import { apiRequest } from './apiClient';

export async function getReports() {
  const response = await apiRequest('/api/reports');
  return {
    schemaVersion: 'frontend.reports.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    reports: response.data
  };
}

export async function exportReport(reportId, format = 'markdown') {
  const response = await apiRequest(`/api/reports/${encodeURIComponent(reportId)}/export`, {
    method: 'POST',
    body: JSON.stringify({ format })
  });
  return {
    schemaVersion: 'frontend.report.export.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    ...response.data
  };
}

export async function getReportsWorkspace() {
  const reportResponse = await getReports();
  return {
    schemaVersion: 'frontend.reports.workspace.v1',
    generatedAt: reportResponse.generatedAt,
    reports: reportResponse.reports,
    featuredReport: reportResponse.reports[0] || null,
    summary: {
      totalReports: reportResponse.reports.length,
      criticalReports: reportResponse.reports.filter((item) => item.severity === 'Critical').length,
    }
  };
}
