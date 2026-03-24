import { apiRequest } from './apiClient';

function buildEntitySummary(events) {
  const bucket = new Map();
  events.forEach((event) => {
    const key = event.entity || event.user || event.host || 'unknown-entity';
    const current = bucket.get(key) || {
      entity: key,
      type: event.host ? 'Host' : event.user ? 'User' : 'Entity',
      score: 0,
      events: 0,
      signal: event.eventType || 'unknown_signal'
    };
    current.events += 1;
    current.score = Math.max(current.score, Number(event.score || 0));
    current.signal = current.signal || event.eventType;
    bucket.set(key, current);
  });
  return Array.from(bucket.values()).sort((a, b) => b.score - a.score);
}

export async function getInvestigationEntity(id) {
  const response = await apiRequest(`/api/investigations/entity/${encodeURIComponent(id)}`);
  return {
    schemaVersion: 'frontend.investigation.entity.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    ...response.data
  };
}

export async function searchEvents(query = '', severity) {
  const params = new URLSearchParams();
  if (query) params.set('query', query);
  if (severity) params.set('severity', severity);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await apiRequest(`/api/events/search${suffix}`);
  return {
    schemaVersion: 'frontend.events.search.v1',
    generatedAt: response.meta?.timestamp || new Date().toISOString(),
    events: response.data
  };
}

export async function getInvestigationWorkspace(query = '') {
  const response = await searchEvents(query);
  const entities = buildEntitySummary(response.events);
  return {
    schemaVersion: 'frontend.investigations.v2',
    generatedAt: response.generatedAt,
    entities,
    relatedEvidence: response.events.slice(0, 6).map((event) => ({
      value: event.entity,
      note: `${event.eventType} observed via ${event.source} at ${event.timestamp}. Severity ${event.severity}.`
    }))
  };
}
