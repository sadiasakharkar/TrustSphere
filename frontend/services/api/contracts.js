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
 *  modelHealth: Array<Object>,
 *  pipeline: Array<Object>,
 *  notifications: Array<Object>
 * }} OverviewResponse
 */

/**
 * @typedef {ServiceResult & { queue: Array<Object> }} TriageResponse
 */

/**
 * @typedef {ServiceResult & { nodes: Array<Object>, edges: Array<Object>, chains: Array<Object> }} GraphResponse
 */

/**
 * @typedef {ServiceResult & { detectors: Array<Object> }} DetectionResponse
 */
