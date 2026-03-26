import { apiRequest } from './apiClient';

function buildSummary(incident = {}) {
  const summary = incident.summary || {};
  return {
    id: summary.id || incident.id || '',
    title: summary.title || incident.title || 'Active incident',
    severity: summary.severity || incident.severity || 'Medium',
    confidence: summary.confidence || incident.confidence || incident.anomaly_score || '0.80',
    status: summary.status || incident.status || 'OPEN',
    owner: summary.owner || incident.owner || incident.assigned_to || 'Unassigned',
    users: summary.users || incident.users || (incident.entities ? [incident.entities[0]].filter(Boolean) : []),
    hosts: summary.hosts || incident.hosts || (incident.entities ? incident.entities.slice(1, 2).filter(Boolean) : []),
    mitre: summary.mitre || incident.mitre || (incident.mitre_stage ? [incident.mitre_stage] : [])
  };
}

export function normalizeIncidentListItem(incident = {}) {
  const summary = buildSummary(incident);
  return {
    ...incident,
    id: incident.id || summary.id,
    title: incident.title || summary.title,
    severity: incident.severity || summary.severity,
    status: incident.status || summary.status,
    owner: incident.owner || incident.assigned_to || summary.owner,
    assigned_to: incident.assigned_to || incident.owner || summary.owner,
    entity: incident.entity || summary.hosts?.[0] || summary.users?.[0] || incident.entities?.[0] || 'Unknown asset',
    eventType: incident.eventType || incident.title || summary.title,
    riskScore: Number(incident.riskScore ?? incident.risk_score ?? 0),
    risk_score: Number(incident.risk_score ?? incident.riskScore ?? 0),
    confidence: summary.confidence,
    affected: incident.affected || `${summary.hosts?.length || 0} hosts, ${summary.users?.length || 0} users`,
    tactic: incident.tactic || incident.mitre_stage || summary.mitre?.[0] || 'Unmapped',
    sla: incident.sla || (String(summary.severity).toLowerCase() === 'critical' ? '< 15m' : String(summary.severity).toLowerCase() === 'high' ? '< 30m' : '< 2h'),
    summary
  };
}

export function normalizeIncidentDetail(incident = {}) {
  const normalized = normalizeIncidentListItem(incident);
  return {
    ...normalized,
    summary: buildSummary(incident),
    timeline: incident.timeline || [],
    evidence: incident.evidence || [],
    relatedAlerts: incident.relatedAlerts || [],
    recommended_actions: incident.recommended_actions || incident.llm?.recommended_actions || []
  };
}

/** @returns {Promise<import('./contracts').TriageResponse>} */
export async function getIncidents() {
  const response = await apiRequest('/api/incidents');
  return {
    schemaVersion: 'frontend.triage.v2',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    queue: Array.isArray(response.data) ? response.data.map(normalizeIncidentListItem) : []
  };
}

/** @returns {Promise<import('./contracts').IncidentResponse>} */
export async function getIncidentDetail(id) {
  const response = await apiRequest(`/api/incidents/${encodeURIComponent(id)}`);
  return {
    schemaVersion: 'frontend.incident.v2',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    sourceMode: response.meta?.mode || 'bootstrap',
    streamCounter: response.meta?.streamCounter || 0,
    ...normalizeIncidentDetail(response.data)
  };
}

export async function updateIncidentStatus(id, status) {
  const response = await apiRequest(`/api/incidents/${encodeURIComponent(id)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status })
  });
  return response.data;
}

export async function assignIncident(id, assignee) {
  const response = await apiRequest(`/api/incidents/${encodeURIComponent(id)}/assign`, {
    method: 'PATCH',
    body: JSON.stringify({ assignee })
  });
  return response.data;
}
