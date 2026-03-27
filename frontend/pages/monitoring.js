import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { getWorkflowInsight } from '../services/api/insight.service';
import { useHybridData } from '../hooks/useHybridData';

const eventColumns = [
  { key: 'timestamp', label: 'Time' },
  { key: 'entity', label: 'Entity' },
  { key: 'eventType', label: 'Event' },
  { key: 'source', label: 'Source' },
  { key: 'severity', label: 'Severity' }
];

export default function MonitoringPage() {
  const [insight, setInsight] = useState(null);
  const { session } = useAuth();
  const { data } = useHybridData('monitoring', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const events = data?.events || [];
  const detectors = data?.detectors || [];
  const metrics = data?.metrics || {};

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const workflow = await getWorkflowInsight('monitoring');
        if (active) setInsight(workflow);
      } catch {
        if (active) setInsight(null);
      }
    };
    load();
    const interval = window.setInterval(load, 6000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={insight}>
        <PageContainer>
          <SectionHeader
            eyebrow="Monitoring"
            title="Live Security Monitoring"
            description={session.role === 'employee'
              ? 'Review your latest alerts and personal risk posture using backend-driven telemetry.'
              : 'Review the latest security events and detector posture using backend-driven telemetry.'}
            actions={session.role === 'employee'
              ? <Link href="/email" className="soc-btn-primary">Analyze email</Link>
              : <Link href="/incidents" className="soc-btn-primary">Promote to triage</Link>}
          />

          {!data ? <LoadingSkeleton rows={5} /> : (
            <div className="space-y-6">
              <section className="grid gap-4 md:grid-cols-3">
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Live events</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{events?.length || 0}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Active detectors</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{detectors?.length || 0}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Critical volume</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{metrics?.severityDistribution?.Critical || 0}</p>
                </div>
              </section>

              <div className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
              <section className="soc-panel">
                <SectionHeader eyebrow="Events" title="Live event feed" description="Recent high-signal telemetry from the backend event stream." />
                {metrics?.spikeSummary ? (
                  <div className="mt-4 rounded-xl border border-[rgba(255,179,173,0.2)] bg-[rgba(255,179,173,0.08)] px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#ffb3ad]">{metrics.spikeSummary.label}</p>
                        <p className="mt-1 text-sm leading-6 soc-text-muted">{metrics.spikeSummary.detail}</p>
                      </div>
                      <StatusBadge tone="high">{metrics.spikeSummary.window}</StatusBadge>
                    </div>
                  </div>
                ) : null}
                <div className="mt-4">
                  <DataTable
                    columns={eventColumns}
                    rows={events || []}
                    getRowKey={(row) => row.id}
                    renderCell={(row, key) => {
                      if (key === 'severity') return <StatusBadge tone={row.severity}>{row.severity}</StatusBadge>;
                      return row[key];
                    }}
                  />
                </div>
              </section>

              <section className="soc-panel">
                <SectionHeader eyebrow="Detectors" title="Detection feed" description="Current detector precision and runtime posture." />
                <div className="mt-4 space-y-3">
                  {(detectors || []).map((item) => (
                    <div key={item.id} className="soc-panel-muted">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-white">{item.source}</p>
                          <p className="mt-1 text-xs soc-text-muted">Precision {item.precision} · drift {item.drift}</p>
                        </div>
                        <StatusBadge tone={item.status}>{item.status}</StatusBadge>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
              </div>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
