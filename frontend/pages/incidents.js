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
import { incidentWorkspace } from '../data/socConsoleData';
import { getTriageQueue } from '../services/api/incidentService';

const columns = [
  { key: 'id', label: 'Incident' },
  { key: 'entity', label: 'Entity' },
  { key: 'owner', label: 'Owner' },
  { key: 'sla', label: 'SLA' },
  { key: 'severity', label: 'Severity' }
];

export default function IncidentsPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getTriageQueue().then(setData);
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

          {!data ? <LoadingSkeleton rows={5} /> : (
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
                  <SectionHeader eyebrow="Current focus" title={incidentWorkspace.summary.title} />
                  <div className="mt-4 flex flex-wrap gap-2">
                    <StatusBadge tone={incidentWorkspace.summary.severity}>{incidentWorkspace.summary.severity}</StatusBadge>
                    <StatusBadge tone="medium">Confidence {incidentWorkspace.summary.confidence}</StatusBadge>
                  </div>
                  <p className="mt-4 text-sm leading-6 soc-text-muted">{incidentWorkspace.summary.mitre.join(' · ')}</p>
                </div>
                <div>
                  <SectionHeader eyebrow="Workflow" title="Current case timeline" />
                  <div className="mt-4">
                    <TimelinePanel items={incidentWorkspace.timeline} />
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
