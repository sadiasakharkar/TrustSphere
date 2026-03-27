import {
  administrationWorkspace,
  graphWorkspace,
  incidentWorkspace,
  investigationWorkspace,
  monitoringFeed,
  overviewSnapshot,
  reportsWorkspace,
  responseWorkspace,
  triageSummary,
  detectionsWorkspace
} from '../../data/socConsoleData.js';
import { users } from '../../data/mockData.js';

function nowIso() {
  return new Date().toISOString();
}

function nowTime(offsetMinutes = 0) {
  return new Date(Date.now() - offsetMinutes * 60_000).toISOString().replace('T', ' ').slice(0, 19);
}

function dynamicEvents() {
  return monitoringFeed.map((event, index) => ({
    ...event,
    timestamp: nowTime(index * 3),
    score: Math.min(99, Number(event.score || 70) + (Math.floor(Date.now() / 5000) + index) % 4),
  }));
}

function overviewData() {
  return {
    ...overviewSnapshot,
    headline: {
      ...overviewSnapshot.headline,
      updatedAt: nowIso(),
    },
    metrics: overviewSnapshot.metrics.map((metric, index) => ({
      ...metric,
      value: typeof metric.value === 'number' ? metric.value + ((Math.floor(Date.now() / 5000) + index) % 2) : metric.value,
    })),
    criticalQueue: triageSummary.queue.slice(0, 4),
  };
}

function socMetricsData() {
  const live = dynamicEvents();
  return {
    severityDistribution: {
      Critical: live.filter((item) => item.severity === 'Critical').length || 2,
      High: live.filter((item) => item.severity === 'High').length || 3,
      Medium: live.filter((item) => item.severity === 'Medium').length || 2,
      Low: live.filter((item) => item.severity === 'Low').length || 1,
    },
    recentActivity: live.slice(0, 6),
    riskDistribution: triageSummary.queue.map((item) => item.riskScore),
    spikeSummary: {
      label: 'Active anomaly spike',
      window: 'Last 30 minutes',
      detail: 'Demo mode is simulating correlated authentication, privilege, and exfiltration signals.',
    },
  };
}

function incidentDetail(id) {
  const match = triageSummary.queue.find((item) => item.id === id) || triageSummary.queue[0];
  return {
    ...incidentWorkspace,
    summary: {
      ...incidentWorkspace.summary,
      id: match?.id || incidentWorkspace.summary.id,
      title: match?.eventType ? `${match.eventType} requiring analyst review` : incidentWorkspace.summary.title,
      severity: match?.severity || incidentWorkspace.summary.severity,
      status: match?.status || incidentWorkspace.summary.status,
      owner: match?.owner || incidentWorkspace.summary.owner,
    },
    relatedAlerts: dynamicEvents().slice(0, 4).map((event) => ({ ...event, incidentId: match?.id || incidentWorkspace.summary.id })),
  };
}

function playbooksData() {
  return [
    {
      id: 'PB-001',
      name: 'Credential containment',
      steps: responseWorkspace.playbook,
    },
    {
      id: 'PB-002',
      name: 'Exfiltration suppression',
      steps: responseWorkspace.playbook.slice(0, 4),
    },
  ];
}

function reportsData() {
  return reportsWorkspace.reports;
}

function adminSystemData() {
  return {
    environment: 'Demo mode',
    queue: 'Nominal',
    worker: 'Ready',
    kafka: 'Simulated',
    ollama: 'Fallback ready',
    lastUpdated: nowIso(),
    modelHealth: detectionsWorkspace.detectors,
    systemConfig: {
      demoMode: true,
      offlineCapable: true,
      strictMode: false,
    },
  };
}

function adminUsersData() {
  return users.map((user) => ({ ...user, role: String(user.role).toLowerCase() }));
}

function detectionsData() {
  return detectionsWorkspace.detectors.map((detector, index) => ({
    id: `DET-${index + 1}`,
    source: detector.name,
    status: detector.status,
    precision: Number(detector.precision),
    drift: detector.drift,
    version: detector.version,
    lastUpdated: nowIso(),
  }));
}

export function resolveDemoFallback(path, method = 'GET') {
  const normalizedMethod = String(method || 'GET').toUpperCase();
  const cleanPath = path.split('?')[0];

  if (cleanPath === '/api/overview/summary') return overviewData();
  if (cleanPath === '/api/metrics/soc') return socMetricsData();
  if (cleanPath === '/api/events/live') return dynamicEvents();
  if (cleanPath === '/api/detections/feed') return detectionsData();
  if (cleanPath === '/api/incidents') return triageSummary.queue;
  if (cleanPath.startsWith('/api/incidents/') && !cleanPath.endsWith('/status') && !cleanPath.endsWith('/assign')) {
    return incidentDetail(decodeURIComponent(cleanPath.split('/').pop() || triageSummary.queue[0]?.id || 'INC-21403'));
  }
  if (cleanPath.endsWith('/status') || cleanPath.endsWith('/assign')) {
    const incidentId = decodeURIComponent(cleanPath.split('/')[3] || triageSummary.queue[0]?.id || 'INC-21403');
    return incidentDetail(incidentId).summary;
  }
  if (cleanPath.startsWith('/api/investigations/entity/')) {
    const entityId = decodeURIComponent(cleanPath.split('/').pop() || 'acct-payroll-09');
    return {
      entity: entityId,
      timeline: dynamicEvents().slice(0, 5),
      aiSummary: investigationWorkspace.relatedEvidence[0]?.note || 'Entity shows repeated suspicious activity.',
      relatedAlerts: dynamicEvents().slice(0, 4).map((event) => event.id),
    };
  }
  if (cleanPath === '/api/events/search') return dynamicEvents();
  if (cleanPath === '/api/attack-graph' || cleanPath.startsWith('/api/attack-graph/')) return graphWorkspace;
  if (cleanPath === '/api/playbooks') return playbooksData();
  if (cleanPath === '/api/playbooks/run' && normalizedMethod === 'POST') {
    return {
      incidentId: 'INC-21403',
      incidentTitle: incidentWorkspace.summary.title,
      playbook: playbooksData()[0],
      executionStatus: 'READY',
      startedAt: nowIso(),
    };
  }
  if (cleanPath === '/api/reports') return reportsData();
  if (cleanPath.startsWith('/api/reports/') && cleanPath.endsWith('/export')) {
    const reportId = decodeURIComponent(cleanPath.split('/')[3] || 'RPT-201');
    return {
      reportId,
      format: 'markdown',
      status: 'EXPORTED',
      exportedAt: nowIso(),
      downloadPath: `outputs/${reportId}.md`,
    };
  }
  if (cleanPath === '/api/admin/system') return adminSystemData();
  if (cleanPath === '/api/admin/users') return adminUsersData();
  if (cleanPath.startsWith('/api/insights/workflow/')) {
    return null;
  }
  if (cleanPath.startsWith('/api/insights/incident/')) {
    return null;
  }
  if (cleanPath === '/health') {
    return { status: 'ok', service: 'trustsphere-security-platform', async_inference: true, offline_capable: true };
  }
  return null;
}

export function isDemoModeEnabled() {
  return true;
}
