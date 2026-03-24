import { overviewSnapshot } from '../../data/socConsoleData';

const wait = (ms = 240) => new Promise((resolve) => setTimeout(resolve, ms));

/** @returns {Promise<import('./contracts').OverviewResponse>} */
export async function getOverviewSummary() {
  await wait();
  return {
    schemaVersion: 'frontend.overview.v1',
    generatedAt: new Date().toISOString(),
    ...overviewSnapshot
  };
}
