import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import AIInsightPanel from '../components/soc/AIInsightPanel';
import DataTable from '../components/soc/DataTable';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import RequireAuth from '../components/RequireAuth';
import StatusBadge from '../components/soc/StatusBadge';
import TimelinePanel from '../components/soc/TimelinePanel';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';
import { getIncidentInsight } from '../services/api/insight.service';

const columns = [
  { key: 'title', label: 'Incident' },
  { key: 'severity', label: 'Severity' },
  { key: 'owner', label: 'Owner' },
  { key: 'riskScore', label: 'Risk' },
];

export default function IncidentsPage() {
  const router = useRouter();
  const { session } = useAuth();
  const { data } = useHybridData('incidents');
  const queue = Array.isArray(data?.queue) ? data.queue : [];
  const initialId = typeof router.query.id === 'string' ? router.query.id : (typeof router.query.create === 'string' ? queue[0]?.id : null);
  const [selectedId, setSelectedId] = useState(initialId);
  const { data: detail } = useHybridData('incidentDetail', { id: selectedId || queue[0]?.id }, { enabled: Boolean(selectedId || queue[0]?.id) });
  const [insight, setInsight] = useState(null);

  useEffect(() => {
    if (!selectedId && queue[0]?.id) setSelectedId(queue[0].id);
  }, [queue, selectedId]);

  useEffect(() => {
    const nextId = typeof router.query.id === 'string' ? router.query.id : null;
    if (nextId) setSelectedId(nextId);
  }, [router.query.id]);

  useEffect(() => {
    const incidentId = selectedId || queue[0]?.id;
    if (!incidentId) return undefined;
    let active = true;
    getIncidentInsight(incidentId).then((value) => {
      if (active) setInsight(value);
    });
    return () => {
      active = false;
    };
  }, [queue, selectedId]);

  const activeIncident = useMemo(() => detail || queue.find((item) => item.id === selectedId) || queue[0], [detail, queue, selectedId]);

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="Workflow" title="Incidents" />

          <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <section className="soc-panel">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="soc-kicker">Queue</p>
                  <h2 className="soc-section-title">Active</h2>
                </div>
                <StatusBadge tone={data?.sourceMode === 'live' ? 'healthy' : 'medium'}>{queue.length} open</StatusBadge>
              </div>
              <DataTable
                columns={columns}
                rows={queue}
                getRowKey={(row) => row.id}
                renderCell={(row, key) => {
                  if (key === 'title') return <span className="text-sm font-semibold text-white">{row.title}</span>;
                  if (key === 'severity') return <StatusBadge tone={row.severity}>{row.severity}</StatusBadge>;
                  if (key === 'riskScore') return <span className="text-sm font-semibold text-white">{row.riskScore}</span>;
                  return <span className="text-sm text-white">{row[key] || '--'}</span>;
                }}
                renderExpandedRow={(row) => (
                  <div className="flex flex-wrap gap-2">
                    <button type="button" className="soc-btn-secondary" onClick={() => setSelectedId(row.id)}>Focus</button>
                    <Link href={`/investigations?incident=${encodeURIComponent(row.id)}`} className="soc-btn-secondary">Investigate</Link>
                    <Link href={`/response?incident=${encodeURIComponent(row.id)}`} className="soc-btn-secondary">Response</Link>
                  </div>
                )}
              />
            </section>

            <div className="grid gap-4">
              <section className="soc-panel">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="soc-kicker">Detail</p>
                    <h2 className="soc-section-title">{activeIncident?.title || 'Incident'}</h2>
                  </div>
                  {activeIncident?.severity ? <StatusBadge tone={activeIncident.severity}>{activeIncident.severity}</StatusBadge> : null}
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Risk</p>
                    <p className="mt-2 text-2xl font-bold text-white">{activeIncident?.risk_score || activeIncident?.riskScore || '--'}</p>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Owner</p>
                    <p className="mt-2 text-sm font-semibold text-white">{activeIncident?.owner || activeIncident?.assigned_to || '--'}</p>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">MITRE</p>
                    <p className="mt-2 text-sm font-semibold text-white">{activeIncident?.mitre_stage || activeIncident?.summary?.mitre?.[0] || '--'}</p>
                  </div>
                </div>
                <div className="mt-4">
                  <TimelinePanel items={activeIncident?.timeline || []} embedded />
                </div>
              </section>

              <AIInsightPanel title="Insights">
                <div className="grid gap-2">
                  <div className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Summary</p>
                    <p className="mt-2 text-sm font-semibold text-white">{insight?.summary || activeIncident?.title || 'Incident risk raised'}</p>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Actions</p>
                    <p className="mt-2 text-sm font-semibold text-white">{(insight?.recommended_actions || activeIncident?.recommended_actions || []).join(' • ') || 'Investigate • Respond'}</p>
                  </div>
                </div>
              </AIInsightPanel>
            </div>
          </div>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}
