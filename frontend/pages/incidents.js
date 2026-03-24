import Link from 'next/link';
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import TimelinePanel from '../components/soc/TimelinePanel';
import EmptyState from '../components/soc/EmptyState';
import { getTriageQueue } from '../services/api/incidentService';
import { getIncidentDetail } from '../services/api/incidentService';
import { getWorkflowInsight } from '../services/api/insight.service';

const columns = [
  { key: 'id', label: 'Incident' },
  { key: 'entity', label: 'Entity' },
  { key: 'owner', label: 'Owner' },
  { key: 'sla', label: 'SLA' },
  { key: 'severity', label: 'Severity' }
];

export default function IncidentsPage() {
  const [data, setData] = useState(null);
  const [focusIncident, setFocusIncident] = useState(null);
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const queue = await getTriageQueue();
        if (!active) return;
        setData(queue);
        const workflow = await getWorkflowInsight('incidents', queue?.queue?.[0]?.id);
        if (active) setInsight(workflow);
        const firstId = queue?.queue?.[0]?.id;
        if (firstId) {
          const detail = await getIncidentDetail(firstId);
          if (active) setFocusIncident(detail);
        }
      } catch (err) {
        if (active) setError(err.message || 'Unable to load incidents.');
      }
    };
    load();
    const interval = window.setInterval(load, 2000);
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
            eyebrow="Incidents"
            title="Incident Triage Queue"
            description="Prioritize incidents by severity and SLA, then pivot into the detailed case view for evidence validation and response decisions."
            actions={
              <>
                <button className="soc-btn-secondary">Assigned to me</button>
                {focusIncident?.summary?.id ? <Link href={`/incident/${focusIncident.summary.id}`} className="soc-btn-primary">Review top case</Link> : null}
              </>
            }
          />

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Incident queue snapshot" detail={error} /> : (
            <div className="space-y-6">
              <section className="grid gap-4 md:grid-cols-4">
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Queue depth</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.queue.length}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Critical</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.queue.filter((item) => item.severity === 'Critical').length}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Unassigned</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.queue.filter((item) => item.owner === 'Unassigned').length}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Highest risk</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.queue[0]?.riskScore || 0}</p>
                </div>
              </section>

              <div className="grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
              <div className="soc-panel">
                <DataTable
                  columns={columns}
                  rows={data.queue}
                  getRowKey={(row) => row.id}
                  renderCell={(row, key) => {
                    if (key === 'id') {
                      return <Link href={'/incident/' + row.id} className="font-semibold text-white hover:text-[#adc6ff]">{row.id}</Link>;
                    }
                    if (key === 'severity') return <StatusBadge tone={row.severity}>{row.severity}</StatusBadge>;
                    return row[key];
                  }}
                  renderExpandedRow={(row) => (
                    <div className="grid gap-4 lg:grid-cols-[1fr,auto] lg:items-center">
                      <div>
                        <p className="text-sm font-semibold text-white">{row.eventType}</p>
                        <p className="mt-2 text-sm leading-6 soc-text-muted">Affected: {row.affected}. Risk score {row.riskScore}. Tactic: {row.tactic}.</p>
                      </div>
                      <Link href={'/incident/' + row.id} className="soc-btn-secondary">Open incident</Link>
                    </div>
                  )}
                />
              </div>

              <div className="space-y-6">
                <div className="soc-panel">
                  <SectionHeader eyebrow="Current focus" title={focusIncident?.summary?.title || 'No active case'} />
                  <div className="mt-4 flex flex-wrap gap-2">
                    <StatusBadge tone={focusIncident?.summary?.severity || 'medium'}>{focusIncident?.summary?.severity || 'Medium'}</StatusBadge>
                    <StatusBadge tone="medium">Confidence {focusIncident?.summary?.confidence || '0.00'}</StatusBadge>
                  </div>
                  <p className="mt-4 text-sm leading-6 soc-text-muted">{focusIncident?.summary?.mitre?.join(' · ') || 'No MITRE mapping available.'}</p>
                </div>
                <div>
                  <SectionHeader eyebrow="Workflow" title="Current case timeline" />
                  <div className="mt-4">
                    <TimelinePanel items={focusIncident?.timeline || []} />
                  </div>
                </div>
                <div className="soc-panel">
                  <SectionHeader eyebrow="Evidence" title="Current case evidence" />
                  <div className="mt-4 space-y-3">
                    {(focusIncident?.evidence || []).map((item) => (
                      <div key={item.title} className="soc-panel-muted">
                        <p className="text-sm font-semibold text-white">{item.title}</p>
                        <p className="mt-2 text-sm leading-6 soc-text-muted">{item.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              </div>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
