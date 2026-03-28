import Link from 'next/link';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import RequireAuth from '../components/RequireAuth';
import MetricCard from '../components/soc/MetricCard';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';

function severityToTone(value) {
  const normalized = String(value || '').toLowerCase();
  if (normalized.includes('critical')) return 'critical';
  if (normalized.includes('high')) return 'high';
  if (normalized.includes('healthy') || normalized.includes('low')) return 'healthy';
  return 'medium';
}

export default function MonitoringPage() {
  const { session } = useAuth();
  const { data } = useHybridData('monitoring');
  const events = Array.isArray(data?.events) ? data.events : [];
  const detectors = Array.isArray(data?.detectors) ? data.detectors : [];

  const criticalCount = events.filter((item) => String(item.severity).toLowerCase() === 'critical').length;
  const highCount = events.filter((item) => String(item.severity).toLowerCase() === 'high').length;
  const averageScore = events.length
    ? (events.reduce((total, item) => total + Number(item.score || 0), 0) / events.length).toFixed(1)
    : '0.0';

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader
            kicker="Alerts"
            title={session.role === 'employee' ? 'My Alerts' : 'Monitoring'}
            description="Track live alert activity, watch detector posture, and move quickly from suspicious signals into investigation."
            actions={(
              <div className="flex flex-wrap gap-2">
                <Link href="/incidents" className="soc-btn-secondary">Open incidents</Link>
                <Link href="/email" className="soc-btn-primary">Open Email Analyzer</Link>
              </div>
            )}
          />

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Active Alerts" value={events.length || '--'} delta={data?.sourceMode || 'demo'} tone="critical" role={session.role} />
            <MetricCard label="Critical Alerts" value={criticalCount} delta="Immediate review" tone="critical" role={session.role} />
            <MetricCard label="High Alerts" value={highCount} delta="Priority queue" tone="high" role={session.role} />
            <MetricCard label="Average Score" value={averageScore} delta="Across active alerts" tone="medium" role={session.role} />
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <section className="soc-panel">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="soc-kicker">Feed</p>
                  <h2 className="soc-section-title">Live alert stream</h2>
                </div>
                <StatusBadge tone={data?.sourceMode === 'live' ? 'healthy' : 'medium'}>{data?.sourceMode || 'demo'}</StatusBadge>
              </div>

              <div className="grid gap-3">
                {events.length ? events.map((event) => (
                  <div key={event.id} className="soc-panel-muted">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{event.eventType || event.title || 'Alert event'}</p>
                        <p className="mt-1 text-xs soc-text-muted">{event.source} | {event.entity}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <StatusBadge tone={event.severity}>{event.severity}</StatusBadge>
                        <span className="text-sm font-semibold text-white">{Number(event.score || 0).toFixed(1)}</span>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-xs soc-text-muted">
                      <span>{event.timestamp || 'Unknown time'}</span>
                      {event.status ? <span>Status: {event.status}</span> : null}
                    </div>
                  </div>
                )) : (
                  <div className="soc-panel-muted text-sm soc-text-muted">
                    No active alerts are available yet.
                  </div>
                )}
              </div>
            </section>

            <section className="grid gap-4">
              <section className="soc-panel">
                <p className="soc-kicker">Detectors</p>
                <h2 className="soc-section-title">Model posture</h2>
                <div className="mt-4 grid gap-3">
                  {detectors.length ? detectors.map((detector) => (
                    <div key={detector.id} className="soc-panel-muted">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-white">{detector.source}</p>
                          <p className="mt-1 text-xs soc-text-muted">{detector.id}</p>
                        </div>
                        <StatusBadge tone={severityToTone(detector.status)}>{detector.status}</StatusBadge>
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="soc-text-muted">Precision</p>
                          <p className="mt-1 text-white">{detector.precision ?? '--'}</p>
                        </div>
                        <div>
                          <p className="soc-text-muted">Drift</p>
                          <p className="mt-1 text-white">{detector.drift || '--'}</p>
                        </div>
                      </div>
                    </div>
                  )) : (
                    <div className="soc-panel-muted text-sm soc-text-muted">
                      Detector health data is not available yet.
                    </div>
                  )}
                </div>
              </section>

              <section className="soc-panel">
                <p className="soc-kicker">Next Step</p>
                <h2 className="soc-section-title">Analyst workflow</h2>
                <div className="mt-4 space-y-3 text-sm leading-6 soc-text-muted">
                  <p>Use this page to catch new alerts quickly, then jump into incidents for deeper triage and case handling.</p>
                  <p>If the alert originates from a suspicious message, move to the Email Analyzer to inspect content and explain why it was flagged.</p>
                </div>
              </section>
            </section>
          </div>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}
