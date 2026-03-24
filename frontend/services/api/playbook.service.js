import { apiRequest } from './apiClient';

export async function getPlaybooks() {
  const response = await apiRequest('/api/playbooks');
  return {
    schemaVersion: 'frontend.playbooks.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    playbooks: response.data
  };
}

export async function runPlaybook(incidentId, playbookId) {
  const response = await apiRequest('/api/playbooks/run', {
    method: 'POST',
    body: JSON.stringify({ incidentId, playbookId: playbookId || null })
  });
  return {
    schemaVersion: 'frontend.playbooks.execution.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    ...response.data
  };
}
