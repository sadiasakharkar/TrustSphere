/**
 * @typedef {Object} ApiMeta
 * @property {string} [timestamp]
 * @property {number} [count]
 * @property {string} [message]
 * @property {string} [requestId]
 * @property {string} [query]
 * @property {string} [severity]
 */

/**
 * @template T
 * @typedef {Object} ApiEnvelope
 * @property {boolean} success
 * @property {T} data
 * @property {ApiMeta} [meta]
 * @property {string | null} [error]
 */

/**
 * @typedef {Object} ServiceResult
 * @property {string} schemaVersion
 * @property {string} generatedAt
 */

/**
 * @typedef {ServiceResult & {
 *  headline: { title: string, subtitle: string, status: string, updatedAt: string },
 *  metrics: Array<{label: string, value: string|number, delta: string, status: string, helper: string}>,
 *  criticalQueue: Array<Object>,
 *  modelHealth: Array<Object>
 * }} OverviewResponse
 */

/**
 * @typedef {ServiceResult & { events: Array<Object> }} MonitoringResponse
 */

/**
 * @typedef {ServiceResult & { queue: Array<Object> }} TriageResponse
 */

/**
 * @typedef {ServiceResult & {
 *  summary: Object,
 *  timeline: Array<Object>,
 *  evidence: Array<Object>,
 *  relatedAlerts: Array<Object>
 * }} IncidentResponse
 */

/**
 * @typedef {ServiceResult & { nodes: Array<Object>, edges: Array<Object>, chains: Array<Object>, riskLevels?: Array<string> }} GraphResponse
 */

/**
 * @typedef {ServiceResult & { detectors: Array<Object> }} DetectionResponse
 */

/**
 * @typedef {ServiceResult & { entities: Array<Object>, relatedEvidence: Array<Object> }} InvestigationWorkspaceResponse
 */

/**
 * @typedef {ServiceResult & { systemStatus: Array<Object>, users: Array<Object>, auditLogs: Array<Object> }} AdministrationWorkspaceResponse
 */

/**
 * @param {ApiEnvelope<any>} envelope
 * @returns {any}
 */
export function unwrapApiEnvelope(envelope) {
  if (!envelope || typeof envelope !== 'object') {
    throw new Error('Invalid API response: empty payload.');
  }
  if (!envelope.success) {
    throw new Error(envelope.error || 'Request failed.');
  }
  return envelope.data;
}

/**
 * @param {ApiEnvelope<any>} envelope
 * @returns {string}
 */
export function envelopeTimestamp(envelope) {
  return envelope?.meta?.timestamp || new Date().toISOString();
}
