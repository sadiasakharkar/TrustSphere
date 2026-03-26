import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import EmailEvidencePanel from '../components/soc/EmailEvidencePanel';
import EmailHistoryTable from '../components/soc/EmailHistoryTable';
import LiveOperationsBanner from '../components/soc/LiveOperationsBanner';
import LiveResponseFeed from '../components/soc/LiveResponseFeed';
import MetricCard from '../components/soc/MetricCard';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import TimelinePanel from '../components/soc/TimelinePanel';
import { getWorkflowInsight } from '../services/api/insight.service';
import { useHybridData } from '../hooks/useHybridData';
import { useRealtimeIncidents } from '../hooks/useRealtimeIncidents';
import { deriveRealtimeSummary, deriveResponseFeed } from '../services/actionAdvisor';

const columns = [
  { key: 'id', label: 'Incident' },
  { key: 'entity', label: 'Entity' },
  { key: 'eventType', label: 'Alert Type' },
  { key: 'severity', label: 'Severity' },
  { key: 'riskScore', label: 'Risk' }
];
const activityColumns = [
  { key: 'timestamp', label: 'Time' },
  { key: 'entity', label: 'Entity' },
  { key: 'eventType', label: 'Activity' },
  { key: 'severity', label: 'Severity' }
];
const EMAIL_HISTORY_STORAGE_KEY = 'trustsphere.overview.emailHistory';

export default function OverviewPage() {
  const [focusIncident, setFocusIncident] = useState(null);
  const [emailHistory, setEmailHistory] = useState([]);
  const [insight, setInsight] = useState(null);
  const [lastStreamEvent, setLastStreamEvent] = useState(null);
  const latestEmailSignature = useRef('');
  const { data, status } = useHybridData('overview', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const { data: focusData } = useHybridData('incidentDetail', { id: data?.demoScenario?.focusIncidentId || data?.criticalQueue?.[0]?.id }, { enabled: Boolean(data?.demoScenario?.focusIncidentId || data?.criticalQueue?.[0]?.id), bootstrapDelayMs: 8000, pollIntervalMs: 6000 });

  useRealtimeIncidents({
    enabled: status.backendConnected,
    onEvent: (event) => setLastStreamEvent(event)
  });

  useEffect(() => {
    setFocusIncident(focusData || null);
  }, [focusData]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const saved = window.localStorage.getItem(EMAIL_HISTORY_STORAGE_KEY);
      if (saved) setEmailHistory(JSON.parse(saved));
    } catch {
      setEmailHistory([]);
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(EMAIL_HISTORY_STORAGE_KEY, JSON.stringify(emailHistory));
  }, [emailHistory]);

  useEffect(() => {
    const emailEvidence = focusIncident?.emailEvidence;
    const incidentId = focusIncident?.summary?.id;
    if (!emailEvidence || !incidentId) return;

    const signature = JSON.stringify({
      incidentId,
      subject: emailEvidence.subject,
      risk: emailEvidence.phishingScore,
      severity: emailEvidence.severity,
      timestamp: emailEvidence.timestamp
    });

    if (latestEmailSignature.current === signature) return;
    latestEmailSignature.current = signature;

    const newEntry = {
      id: `${incidentId}-${emailEvidence.timestamp}-${emailEvidence.subject}`,
      incidentId,
      subject: emailEvidence.subject,
      bodySnippet: emailEvidence.bodySnippet,
      risk: emailEvidence.phishingScore,
      severity: emailEvidence.severity,
      actions: emailEvidence.actions,
      time: new Date().toLocaleString()
    };

    setEmailHistory((current) => {
      if (current.some((item) => item.id === newEntry.id)) return current;
      return [newEntry, ...current].slice(0, 12);
    });
  }, [focusIncident]);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const overviewInsight = await getWorkflowInsight('overview');
        if (active) setInsight(overviewInsight);
      } catch {
        if (active) setInsight(null);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const realtimeSummary = deriveRealtimeSummary(data?.criticalQueue || [], lastStreamEvent);
  const responseFeed = deriveResponseFeed(data?.criticalQueue || []);
  const operationsStatusLabel = status.backendConnected
    ? (status.modelActive ? 'Threat stream active' : 'Live link connected')
    : 'Hybrid bootstrap monitoring';
  const operationsHighlight = realtimeSummary.topAction
    ? `${realtimeSummary.topAction.label} is currently the best fit for ${realtimeSummary.topIncident?.title || 'the highest-risk case'}, based on evidence, urgency, and disruption balance.`
    : 'The platform is collecting enough evidence to prioritize the next best action automatically.';

  return (
    <RequireAuth>
      <Layout insightSummary={insight}>
        <PageContainer>
          <SectionHeader
            eyebrow="Overview"
            title="Security Operations Overview"
            description="Start here to assess current alert pressure, incident severity, and investigation tempo before moving into incident handling."
            actions={
              <>
                <Link href="/email" className="soc-btn-primary">Email analyzer</Link>
                <button className="soc-btn-secondary">Last 24h</button>
                <Link href="/monitoring" className="soc-btn-secondary">Open monitoring</Link>
              </>
            }
          />

          {!data ? <LoadingSkeleton rows={5} /> : (
            <>
              <LiveOperationsBanner
                title="Realtime SOC command posture"
                statusLabel={operationsStatusLabel}
                statusTone={status.backendConnected ? 'ready' : 'medium'}
                updatedAt={lastStreamEvent?.timestamp ? new Date(lastStreamEvent.timestamp * 1000).toISOString() : data.generatedAt}
                summary={realtimeSummary}
                highlight={operationsHighlight}
                cta={data.demoScenario?.focusIncidentId ? <Link href={`/incident/${data.demoScenario.focusIncidentId}`} className="soc-btn-primary">Open live decision workspace</Link> : null}
              />

              <section className="soc-demo-banner">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="soc-kicker">Demo Scenario</p>
                    <h3 className="mt-2 text-base font-semibold text-white">{data.demoScenario?.title}</h3>
                    <p className="mt-2 text-sm leading-6 soc-text-muted">{data.demoScenario?.summary}</p>
                  </div>
                  {data.demoScenario?.focusIncidentId ? <Link href={`/incident/${data.demoScenario.focusIncidentId}`} className="soc-btn-primary">Open focus incident</Link> : null}
                </div>
              </section>

              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {data.metrics.map((metric) => (
                  <MetricCard key={metric.label} label={metric.label} value={metric.value} delta={metric.delta} tone={metric.status} helper={metric.helper} />
                ))}
              </section>

              <section className="grid gap-6 xl:grid-cols-[1.25fr,0.75fr]">
                <div className="soc-panel">
                  <SectionHeader eyebrow="Alerts" title="Priority alerts summary" description="Critical and high-risk cases requiring analyst review." />
                  <div className="mt-4">
                    <DataTable
                      columns={columns}
                      rows={data.criticalQueue}
                      getRowKey={(row) => row.id}
                      renderCell={(row, key) => {
                        if (key === 'id') return <span className="font-semibold text-white">{row.id}</span>;
                        if (key === 'severity') return <StatusBadge tone={row.severity}>{row.severity}</StatusBadge>;
                        return row[key];
                      }}
                      emptyMessage="No active priority alerts."
                    />
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="soc-panel">
                    <SectionHeader eyebrow="Status" title="Operations state" description="Current platform and queue posture." />
                    <div className="mt-4 space-y-3">
                      {data.modelHealth.map((item) => (
                        <div key={item.name} className="soc-panel-muted">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold text-white">{item.name}</p>
                              <p className="mt-1 text-xs soc-text-muted">{item.detail}</p>
                            </div>
                            <StatusBadge tone={item.status}>{item.status}</StatusBadge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>

              <LiveResponseFeed items={responseFeed} streamEvent={lastStreamEvent} title="Recommended response queue" />

              <section className="grid gap-6 xl:grid-cols-[0.9fr,1.1fr]">
                <div>
                  <SectionHeader eyebrow="Activity" title="Investigation timeline" description="Recent correlated activity requiring continued monitoring." />
                  <div className="mt-4">
                    <TimelinePanel items={focusIncident?.timeline || []} />
                  </div>
                </div>
                <div className="soc-panel">
                  <SectionHeader eyebrow="Summary" title="Current analyst notes" description="Operational context for the top active case." />
                  <div className="mt-4 space-y-3">
                    {(focusIncident?.evidence || []).map((item) => (
                      <div key={item.title} className="soc-panel-muted">
                        <p className="text-sm font-semibold text-white">{item.title}</p>
                        <p className="mt-2 text-sm leading-6 soc-text-muted">{item.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <section className="soc-panel">
                <SectionHeader
                  eyebrow="Email"
                  title="Focus email analysis"
                  description="Phishing-focused evidence for the current priority incident, surfaced directly from the active case context."
                />
                <div className="mt-4">
                  <EmailEvidencePanel email={focusIncident?.emailEvidence} />
                </div>
              </section>

              <EmailHistoryTable
                history={emailHistory}
                onClear={() => {
                  latestEmailSignature.current = '';
                  setEmailHistory([]);
                }}
              />

              <section className="grid gap-6 xl:grid-cols-[1.05fr,0.95fr]">
                <div className="soc-panel">
                  <SectionHeader eyebrow="Recent Activity" title="Latest correlated events" description="Backend-fed activity associated with the current risk spike." />
                  <div className="mt-4">
                    <DataTable
                      columns={activityColumns}
                      rows={data.analytics?.recentActivity || []}
                      getRowKey={(row) => row.id}
                      renderCell={(row, key) => {
                        if (key === 'severity') return <StatusBadge tone={row.severity}>{row.severity}</StatusBadge>;
                        return row[key];
                      }}
                      emptyMessage="No recent activity in the current window."
                    />
                  </div>
                </div>
                <div className="soc-panel">
                  <SectionHeader eyebrow="Distribution" title="Severity posture" description="Current severity balance from the active backend event window." />
                  <div className="mt-4 space-y-3">
                    {Object.entries(data.analytics?.severityDistribution || {}).map(([label, value]) => (
                      <div key={label} className="soc-panel-muted flex items-center justify-between gap-3">
                        <p className="text-sm font-medium text-white">{label}</p>
                        <StatusBadge tone={label}>{value}</StatusBadge>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            </>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
