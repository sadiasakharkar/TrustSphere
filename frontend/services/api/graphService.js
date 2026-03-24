import { graphWorkspace } from '../../data/socConsoleData';

const wait = (ms = 220) => new Promise((resolve) => setTimeout(resolve, ms));

/** @returns {Promise<import('./contracts').GraphResponse>} */
export async function getThreatGraph() {
  await wait();
  return {
    schemaVersion: 'frontend.graph.v1',
    generatedAt: new Date().toISOString(),
    ...graphWorkspace
  };
}
