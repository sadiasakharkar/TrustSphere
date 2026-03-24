import Link from 'next/link';
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import MetricCard from '../components/soc/MetricCard';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import TimelinePanel from '../components/soc/TimelinePanel';
import EmptyState from '../components/soc/EmptyState';
import { getOverviewSummary } from '../services/api/overviewService';
import { getIncidentDetail } from '../services/api/incidentService';
import { getWorkflowInsight } from '../services/api/insight.service';

const columns = [
  { key: 'id', label: 'Incident' },
  { key: 'entity', label: 'Entity' },
  { key: 'eventType', label: 'Alert Type' },
  { key: 'severity', label: 'Severity' },
  { key: 'riskScore', label: 'Risk' }
];

export default function OverviewPage() {
  const [data, setData] = useState(null);
  const [focusIncident, setFocusIncident] = useState(null);
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const summary = await getOverviewSummary();
        if (!active) return;
        setData(summary);
        const overviewInsight = await getWorkflowInsight('overview');
        if (active) setInsight(overviewInsight);
        const primary = summary?.criticalQueue?.[0]?.id;
        if (primary) {
          const detail = await getIncidentDetail(primary);
          if (active) setFocusIncident(detail);
        }
      } catch (err) {
        if (active) setError(err.message || 'Unable to load overview data.');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

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
                <button className="soc-btn-secondary">Last 24h</button>
                <Link href="/monitoring" className="soc-btn-primary">Open monitoring</Link>
              </>
            }
          />

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Overview unavailable" detail={error} /> : (
            <>
              <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
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
            </>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
