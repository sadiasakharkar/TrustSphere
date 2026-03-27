import { bootstrapAlerts } from '../data/bootstrap/alerts.js';
import { bootstrapAttackGraph } from '../data/bootstrap/attackGraph.js';
import { bootstrapEntities } from '../data/bootstrap/entities.js';
import { bootstrapIncidents } from '../data/bootstrap/incidents.js';
import { bootstrapMetrics } from '../data/bootstrap/metrics.js';
import { bootstrapPlaybooks } from '../data/bootstrap/playbooks.js';
import { getApiBaseUrl, isDemoMode } from './api/apiClient.js';
import { getAdministrationWorkspace } from './api/admin.service.js';
import { getAnalyticsWorkspace } from './api/analytics.service.js';
import { getDetectionsOverview } from './api/detectionService.js';
import { getAttackGraph } from './api/graph.service.js';
import { getIncidentDetail, getIncidents } from './api/incident.service.js';
import { getInvestigationWorkspace } from './api/investigation.service.js';
import { getDetectionsFeed, getLiveEvents } from './api/monitoring.service.js';
import { getOverviewSummary } from './api/overview.service.js';
import { getPlaybooks } from './api/playbook.service.js';
import { getReportsWorkspace } from './api/report.service.js';

const CACHE_PREFIX = 'trustsphere.domain-cache';

async function fetchHealth() {
  const response = await fetch(`${getApiBaseUrl()}/system/health`, {
    headers: { 'x-api-key': process.env.NEXT_PUBLIC_TRUSTSPHERE_API_KEY || 'trustsphere-local-dev-key' }
  });
  if (!response.ok) throw new Error('Backend unavailable');
  const raw = await response.json();
  return raw?.data || {};
}

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function cacheKey(domain, params = {}) {
  return `${CACHE_PREFIX}:${domain}:${JSON.stringify(params || {})}`;
}

export function getCachedDomainData(domain, params = {}) {
  if (!canUseStorage()) return null;
  try {
    const raw = window.localStorage.getItem(cacheKey(domain, params));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.data || null;
  } catch {
    return null;
  }
}

export function setCachedDomainData(domain, params = {}, data) {
  if (!canUseStorage() || !data) return;
  try {
    window.localStorage.setItem(cacheKey(domain, params), JSON.stringify({
      savedAt: new Date().toISOString(),
      data,
    }));
  } catch {
    // Ignore local cache write failures to preserve UI availability.
  }
}

export const bootstrapData = {
  overview: {
    schemaVersion: 'bootstrap.overview.v1',
    generatedAt: new Date().toISOString(),
    headline: {
      title: 'Security Operations Overview',
      subtitle: 'Seeded SOC intelligence loaded instantly while live AI connectivity initializes.',
      status: 'Bootstrap mode',
      updatedAt: new Date().toISOString()
    },
    metrics: bootstrapMetrics.topRow.slice(0, 4),
    criticalQueue: bootstrapIncidents.slice(0, 4),
    modelHealth: [
      { name: 'UEBA Anomaly Model', status: 'Bootstrapping', detail: 'Behavioral baseline and risk scoring are initializing.' },
      { name: 'Attack Graph Engine', status: 'Ready', detail: 'Graph topology seeded with correlated path data.' },
      { name: 'SOC Analyst Reasoner', status: 'Ready', detail: 'Explanation layer available for seeded and live incidents.' }
    ],
    analytics: {
      severityDistribution: bootstrapMetrics.severityDistribution,
      recentActivity: bootstrapAlerts.map((item, index) => ({
        id: item.id,
        timestamp: item.timestamp,
        entity: item.entity,
        eventType: item.title,
        severity: item.severity,
        score: 92 - index * 3,
        source: item.source
      })),
      riskDistribution: bootstrapIncidents.map((item) => item.risk_score || item.riskScore)
    },
    demoScenario: {
      title: 'Hybrid SOC bootstrap state',
      focusIncidentId: bootstrapIncidents[0].id,
      summary: 'TrustSphere loads seeded incidents immediately, then reconciles into live backend intelligence.'
    },
    sourceMode: 'bootstrap'
  },
  monitoring: {
    schemaVersion: 'bootstrap.monitoring.v1',
    generatedAt: new Date().toISOString(),
    events: bootstrapAlerts.map((item, index) => ({
      id: item.id,
      timestamp: item.timestamp,
      entity: item.entity,
      source: item.source,
      eventType: item.title,
      severity: item.severity,
      score: 94 - index * 4
    })),
    detectors: [
      { id: 'DET-100', source: 'UEBA', status: 'High Activity', precision: 0.97, drift: 'Low' },
      { id: 'DET-101', source: 'Email AI', status: 'Healthy', precision: 0.95, drift: 'Low' },
      { id: 'DET-102', source: 'Credential AI', status: 'Healthy', precision: 0.93, drift: 'Low' }
    ],
    metrics: {
      severityDistribution: bootstrapMetrics.severityDistribution,
      spikeSummary: {
        label: 'Active anomaly wave',
        window: 'Last 15 minutes',
        detail: 'Seeded alerts represent concurrent authentication, phishing, and endpoint signals.'
      }
    },
    sourceMode: 'bootstrap'
  },
  incidents: {
    schemaVersion: 'bootstrap.incidents.v1',
    generatedAt: new Date().toISOString(),
    queue: bootstrapIncidents.map((incident, index) => ({
      ...incident,
      owner: incident.assigned_to,
      entity: incident.entities[1] || incident.entity,
      eventType: incident.title,
      riskScore: incident.risk_score,
      confidence: incident.confidence || incident.anomaly_score?.toFixed?.(2) || '0.90',
      affected: `${1 + (index % 3)} hosts, ${1 + (index % 2)} users`,
      tactic: incident.mitre_stage
    })),
    sourceMode: 'bootstrap'
  },
  attackGraph: {
    schemaVersion: 'bootstrap.graph.v1',
    generatedAt: new Date().toISOString(),
    ...bootstrapAttackGraph,
    riskLevels: bootstrapAttackGraph.nodes.map((node) => node.risk),
    sourceMode: 'bootstrap'
  },
  investigations: {
    schemaVersion: 'bootstrap.investigations.v1',
    generatedAt: new Date().toISOString(),
    entities: bootstrapEntities,
    relatedEvidence: bootstrapAlerts.slice(0, 5).map((item) => ({
      value: item.entity,
      note: `${item.title} observed via ${item.source} at ${item.timestamp}.`
    })),
    sourceMode: 'bootstrap'
  },
  playbooks: {
    schemaVersion: 'bootstrap.playbooks.v1',
    generatedAt: new Date().toISOString(),
    playbooks: bootstrapPlaybooks,
    sourceMode: 'bootstrap'
  },
  reports: {
    schemaVersion: 'bootstrap.reports.v1',
    generatedAt: new Date().toISOString(),
    reports: bootstrapIncidents.slice(0, 4).map((incident) => ({
      id: `RPT-${incident.id}`,
      title: incident.title,
      severity: incident.severity,
      author: 'TrustSphere AI',
      updated: incident.created_at
    })),
    featuredReport: {
      id: `RPT-${bootstrapIncidents[0].id}`,
      title: bootstrapIncidents[0].title,
      severity: bootstrapIncidents[0].severity,
      author: 'TrustSphere AI',
      updated: bootstrapIncidents[0].created_at
    },
    summary: {
      totalReports: 4,
      criticalReports: 2
    },
    sourceMode: 'bootstrap'
  },
  administration: {
    schemaVersion: 'bootstrap.admin.v1',
    generatedAt: new Date().toISOString(),
    systemStatus: [
      { label: 'Environment', value: 'Bootstrap' },
      { label: 'Queue', value: 'Nominal' },
      { label: 'Worker', value: 'Ready' },
      { label: 'Kafka', value: 'Simulated' },
      { label: 'Ollama', value: 'Ready' }
    ],
    modelHealth: [
      { name: 'UEBA', status: 'Bootstrapping', detail: 'Using seeded SOC baseline.' },
      { name: 'Graph Engine', status: 'Ready', detail: 'Correlated edges available.' },
      { name: 'Reasoner', status: 'Ready', detail: 'Analyst explanation service online.' }
    ],
    systemConfig: {
      demoMode: true,
      backendPreferred: true,
      offlineCapable: true
    },
    users: [
      { id: 'USR-01', name: 'Avery Collins', role: 'analyst', status: 'Active' },
      { id: 'USR-02', name: 'Maya Patel', role: 'admin', status: 'Active' }
    ],
    auditLogs: [
      { id: 'AUD-1001', action: 'Bootstrap dataset initialized', actor: 'TrustSphere Backend', result: 'Success', timestamp: new Date().toISOString() }
    ],
    sourceMode: 'bootstrap'
  },
  analytics: {
    schemaVersion: 'bootstrap.analytics.v1',
    generatedAt: new Date().toISOString(),
    severityLabels: Object.keys(bootstrapMetrics.severityDistribution),
    severityValues: Object.values(bootstrapMetrics.severityDistribution),
    riskDistribution: bootstrapMetrics.riskTrend,
    recentActivity: bootstrapAlerts.map((item, index) => ({
      id: item.id,
      entity: item.entity,
      source: item.source,
      eventType: item.title,
      severity: item.severity,
      score: 89 - index * 3
    })),
    sourceMode: 'bootstrap'
  }
};

export async function probeBackend() {
  try {
    const health = await fetchHealth();
    return { connected: true, health };
  } catch {
    return { connected: false, health: null };
  }
}

export async function getDomainData(domain, params = {}) {
  switch (domain) {
    case 'overview':
      return getOverviewSummary();
    case 'monitoring':
      return {
        schemaVersion: 'provider.monitoring.v1',
        generatedAt: new Date().toISOString(),
        events: (await getLiveEvents()).events,
        detectors: (await getDetectionsFeed()).detectors,
        sourceMode: 'live'
      };
    case 'incidents':
      return getIncidents();
    case 'incidentDetail':
      return getIncidentDetail(params.id);
    case 'attackGraph':
      return getAttackGraph(params.id);
    case 'investigations':
      return getInvestigationWorkspace(params.query || '');
    case 'playbooks':
      return getPlaybooks();
    case 'reports':
      return getReportsWorkspace();
    case 'administration':
      return getAdministrationWorkspace();
    case 'analytics':
      return getAnalyticsWorkspace();
    case 'detections':
      return getDetectionsOverview();
    default:
      throw new Error(`Unknown domain: ${domain}`);
  }
}

export function getBootstrapData(domain, params = {}) {
  if (domain === 'incidentDetail') {
    const incident = bootstrapIncidents.find((item) => item.id === params.id) || bootstrapIncidents[0];
    return {
      schemaVersion: 'bootstrap.incident-detail.v1',
      generatedAt: new Date().toISOString(),
      ...incident,
      summary: {
        id: incident.id,
        title: incident.title,
        severity: incident.severity,
        confidence: incident.confidence,
        status: incident.status,
        owner: incident.assigned_to,
        users: [incident.entities[0]],
        hosts: [incident.entities[1]],
        mitre: [incident.mitre_stage]
      },
      timeline: incident.timeline,
      evidence: incident.evidence,
      relatedAlerts: bootstrapAlerts.filter((item) => item.entity === incident.entities[1] || item.entity === incident.entities[0]),
      sourceMode: 'bootstrap'
    };
  }
  if (domain === 'detections') {
    return {
      schemaVersion: 'bootstrap.detections.v1',
      generatedAt: new Date().toISOString(),
      detectors: bootstrapData.monitoring.detectors,
      sourceMode: 'bootstrap'
    };
  }
  return bootstrapData[domain];
}

export function shouldPreferBootstrap() {
  return isDemoMode();
}
