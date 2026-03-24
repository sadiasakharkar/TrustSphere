import { incidentWorkspace, monitoringFeed, triageSummary } from '../../data/socConsoleData';

const wait = (ms = 240) => new Promise((resolve) => setTimeout(resolve, ms));

export async function getMonitoringFeed() {
  await wait();
  return {
    schemaVersion: 'frontend.monitoring.v1',
    generatedAt: new Date().toISOString(),
    events: monitoringFeed
  };
}

/** @returns {Promise<import('./contracts').TriageResponse>} */
export async function getTriageQueue() {
  await wait();
  return {
    schemaVersion: 'frontend.triage.v1',
    generatedAt: new Date().toISOString(),
    ...triageSummary
  };
}

export async function getIncidentDetail(id) {
  await wait();
  return {
    schemaVersion: 'frontend.incident.v1',
    generatedAt: new Date().toISOString(),
    ...incidentWorkspace,
    summary: {
      ...incidentWorkspace.summary,
      id: id || incidentWorkspace.summary.id
    }
  };
}
