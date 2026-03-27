import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { exportReport } from '../services/api/report.service';
import { getWorkflowInsight } from '../services/api/insight.service';
import { useHybridData } from '../hooks/useHybridData';

const columns = [
  { key: 'id', label: 'Report' },
  { key: 'title', label: 'Title' },
  { key: 'severity', label: 'Severity' },
  { key: 'author', label: 'Author' },
  { key: 'updated', label: 'Updated' }
];

export default function ReportsPage() {
  const [exportState, setExportState] = useState(null);
  const [insight, setInsight] = useState(null);
  const { data } = useHybridData('reports', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const workflow = await getWorkflowInsight('reports');
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
    <RequireAuth adminOnly>
      <Layout insightSummary={insight}>
        <PageContainer>
          <SectionHeader eyebrow="Reports" title="Incident Reports" description="Review and export backend-generated SOC reports." actions={<Link href="/overview" className="soc-btn-secondary">Return to overview</Link>} />

          {!data ? <LoadingSkeleton rows={5} /> : (
            <div className="space-y-6">
              <section className="grid gap-4 md:grid-cols-2">
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Total reports</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.summary?.totalReports || 0}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Critical reports</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.summary?.criticalReports || 0}</p>
                </div>
              </section>

              <div className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
              <section className="soc-panel">
                <DataTable
                  columns={columns}
                  rows={data.reports || []}
                  getRowKey={(row) => row.id}
                  renderCell={(row, key) => {
                    if (key === 'severity') return <StatusBadge tone={row.severity}>{row.severity}</StatusBadge>;
                    if (key === 'id') return <span className="font-semibold text-white">{row.id}</span>;
                    return row[key];
                  }}
                />
              </section>
              <section className="soc-panel">
                <SectionHeader eyebrow="Export" title={data.featuredReport?.title || 'Select report'} />
                {data.featuredReport ? (
                  <div className="mb-4 soc-panel-muted">
                    <p className="text-sm font-semibold text-white">{data.featuredReport.author}</p>
                    <p className="mt-2 text-sm leading-6 soc-text-muted">Last updated {data.featuredReport.updated}. Severity {data.featuredReport.severity}.</p>
                  </div>
                ) : null}
                <div className="mt-4 flex items-center gap-3">
                  <button
                    className="soc-btn-primary"
                    onClick={async () => {
                      if (!data?.featuredReport?.id) return;
                      const result = await exportReport(data.featuredReport.id, 'markdown');
                      setExportState(result);
                    }}
                  >
                    Export markdown
                  </button>
                  {exportState ? <StatusBadge tone="ready">{exportState.status}</StatusBadge> : null}
                </div>
                {exportState ? <p className="mt-4 text-sm leading-6 soc-text-muted">Artifact: {exportState.downloadPath}</p> : null}
              </section>
              </div>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
