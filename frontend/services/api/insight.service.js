import { apiRequest } from './apiClient';

export async function getWorkflowInsight(view, incidentId) {
  const path = incidentId
    ? `/api/insights/workflow/${encodeURIComponent(view)}?incident_id=${encodeURIComponent(incidentId)}`
    : `/api/insights/workflow/${encodeURIComponent(view)}`;
  const response = await apiRequest(path);
  return response.data;
}

export async function getIncidentInsight(incidentId) {
  const response = await apiRequest(`/api/insights/incident/${encodeURIComponent(incidentId)}`);
  return response.data;
}
