import { administrationWorkspace, detectionsWorkspace, investigationWorkspace, reportsWorkspace, responseWorkspace } from '../../data/socConsoleData';

const wait = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms));

/** @returns {Promise<import('./contracts').DetectionResponse>} */
export async function getDetectionsOverview() {
  await wait();
  return {
    schemaVersion: 'frontend.detections.v1',
    generatedAt: new Date().toISOString(),
    ...detectionsWorkspace
  };
}

export async function getInvestigationWorkspace() {
  await wait();
  return {
    schemaVersion: 'frontend.investigations.v1',
    generatedAt: new Date().toISOString(),
    ...investigationWorkspace
  };
}

export async function getResponseWorkspace() {
  await wait();
  return {
    schemaVersion: 'frontend.response.v1',
    generatedAt: new Date().toISOString(),
    ...responseWorkspace
  };
}

export async function getReportsWorkspace() {
  await wait();
  return {
    schemaVersion: 'frontend.reports.v1',
    generatedAt: new Date().toISOString(),
    ...reportsWorkspace
  };
}

export async function getAdministrationWorkspace() {
  await wait();
  return {
    schemaVersion: 'frontend.administration.v1',
    generatedAt: new Date().toISOString(),
    ...administrationWorkspace
  };
}
