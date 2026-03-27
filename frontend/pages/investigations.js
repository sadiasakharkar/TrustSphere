import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { getWorkflowInsight } from '../services/api/insight.service';
import { useHybridData } from '../hooks/useHybridData';

const columns = [
  { key: 'entity', label: 'Entity' },
  { key: 'type', label: 'Type' },
  { key: 'score', label: 'Risk Score' },
  { key: 'events', label: 'Event Count' },
  { key: 'signal', label: 'Primary Signal' }
];

export default function InvestigationsPage() {
  const [insight, setInsight] = useState(null);
  const { data } = useHybridData('investigations', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const workflow = await getWorkflowInsight('investigations');
        if (active) setInsight(workflow);
      } catch {
        if (active) setInsight(null);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <RequireAuth allowedRoles={['admin', 'analyst']}>
      <Layout insightSummary={insight}>
        <PageContainer>
          <SectionHeader
            eyebrow="Investigations"
            title="Entity Investigation Workspace"
            description="Investigate suspicious entities, compare evidence, and expand rows to inspect supporting context without losing table visibility."
            actions={
              <>
                <button className="soc-btn-secondary">Severity: All</button>
                <button className="soc-btn-secondary">Type: All</button>
                <Link href="/threat-graph" className="soc-btn-primary">Open attack graph</Link>
              </>
            }
          />

          {!data ? <LoadingSkeleton rows={5} /> : (
            <div className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
              <div className="soc-panel">
                <DataTable
                  columns={columns}
                  rows={data.entities}
                  getRowKey={(row) => row.entity}
                  renderCell={(row, key) => {
                    if (key === 'score') return <StatusBadge tone={row.score > 90 ? 'critical' : row.score > 80 ? 'high' : 'medium'}>{row.score}</StatusBadge>;
                    if (key === 'entity') return <span className="font-semibold text-white">{row.entity}</span>;
                    return row[key];
                  }}
                  renderExpandedRow={(row) => {
                    const related = data.relatedEvidence.find((item) => item.value === row.entity) || data.relatedEvidence[0];
                    return (
                      <div className="grid gap-4 lg:grid-cols-2">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.55)]">Investigation note</p>
                          <p className="mt-2 text-sm leading-6 soc-text-muted">{row.signal}</p>
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.55)]">Related evidence</p>
                          <p className="mt-2 text-sm leading-6 soc-text-muted">{related.note}</p>
                        </div>
                      </div>
                    );
                  }}
                />
              </div>
              <div className="soc-panel">
                <SectionHeader eyebrow="Evidence" title="Recent related evidence" />
                <div className="mt-4 space-y-3">
                  {(data.relatedEvidence || []).map((item, index) => (
                    <div key={`${item.value}-${index}`} className="soc-panel-muted">
                      <p className="text-sm font-semibold text-white">{item.value}</p>
                      <p className="mt-2 text-sm leading-6 soc-text-muted">{item.note}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
