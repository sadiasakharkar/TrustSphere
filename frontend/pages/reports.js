import Link from 'next/link';
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { exportReport, getReportsWorkspace } from '../services/api/report.service';
import { getWorkflowInsight } from '../services/api/insight.service';

const columns = [
  { key: 'id', label: 'Report' },
  { key: 'title', label: 'Title' },
  { key: 'severity', label: 'Severity' },
  { key: 'author', label: 'Author' },
  { key: 'updated', label: 'Updated' }
];

export default function ReportsPage() {
  const [data, setData] = useState(null);
  const [exportState, setExportState] = useState(null);
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await getReportsWorkspace();
        if (active) {
          setData(response);
          const workflow = await getWorkflowInsight('reports');
          if (active) setInsight(workflow);
        }
      } catch (err) {
        if (active) setError(err.message || 'Unable to load reports.');
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
          <SectionHeader eyebrow="Reports" title="Incident Reports" description="Review and export backend-generated SOC reports." actions={<Link href="/overview" className="soc-btn-secondary">Return to overview</Link>} />

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Report library snapshot" detail={error} /> : (
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
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
