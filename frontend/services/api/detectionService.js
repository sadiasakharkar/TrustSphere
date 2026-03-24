import { getAdminUsers, getAdministrationWorkspace } from './admin.service.js';
import { getDetectionsFeed } from './monitoring.service.js';
import { getInvestigationWorkspace } from './investigation.service.js';
import { getPlaybooks, runPlaybook } from './playbook.service.js';
import { getReportsWorkspace } from './report.service.js';

export async function getDetectionsOverview() {
  const response = await getDetectionsFeed();
  return {
    schemaVersion: 'frontend.detections.v2',
    generatedAt: response.generatedAt,
    detectors: response.detectors
  };
}

export { getInvestigationWorkspace, getAdministrationWorkspace, getPlaybooks, runPlaybook, getReportsWorkspace, getAdminUsers };
