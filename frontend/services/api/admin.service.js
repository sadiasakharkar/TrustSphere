import { apiRequest } from './apiClient';

export async function getAdminSystem() {
  const response = await apiRequest('/api/admin/system');
  return {
    schemaVersion: 'frontend.admin.system.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    ...response.data
  };
}

export async function getAdminUsers() {
  const response = await apiRequest('/api/admin/users');
  return {
    schemaVersion: 'frontend.admin.users.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    users: response.data
  };
}

export async function getAdministrationWorkspace() {
  const [system, users] = await Promise.all([getAdminSystem(), getAdminUsers()]);
  return {
    schemaVersion: 'frontend.administration.v2',
    generatedAt: system.generatedAt,
    systemStatus: [
      { label: 'Environment', value: system.environment },
      { label: 'Queue', value: system.queue },
      { label: 'Worker', value: system.worker },
      { label: 'Kafka', value: system.kafka },
      { label: 'Ollama', value: system.ollama }
    ],
    modelHealth: Array.isArray(system.modelHealth) ? system.modelHealth : [],
    systemConfig: system.systemConfig || {},
    users: users.users,
    auditLogs: [
      {
        id: 'AUD-001',
        action: 'System health snapshot',
        actor: 'TrustSphere Backend',
        result: system.environment,
        timestamp: system.lastUpdated
      }
    ]
  };
}
