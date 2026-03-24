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
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const queue = await getTriageQueue();
        if (!active) return;
        setData(queue);
        const firstId = queue?.queue?.[0]?.id;
        if (firstId) {
          const detail = await getIncidentDetail(firstId);
          if (active) setFocusIncident(detail);
        }
      } catch (err) {
        if (active) setError(err.message || 'Unable to load incidents.');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <SectionHeader
            eyebrow="Incidents"
            title="Incident Triage Queue"
            description="Prioritize incidents by severity and SLA, then pivot into the detailed case view for evidence validation and response decisions."
            actions={<button className="soc-btn-secondary">Assigned to me</button>}
          />

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Incidents unavailable" detail={error} /> : (
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
              </div>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
