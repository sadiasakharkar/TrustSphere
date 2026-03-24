import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageHeader from '../components/soc/PageHeader';
import SeverityBadge from '../components/soc/SeverityBadge';
import { getReportsWorkspace } from '../services/api/detectionService';

export default function ReportsPage() {
  const [data, setData] = useState(null);
  useEffect(() => { getReportsWorkspace().then(setData); }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Reports focus: move from analyst evidence to executive-ready summaries and formally export response artifacts.' }}>
        <PageHeader kicker="Reports" title="Incident Reporting" description="TrustSphere converts incident context into structured markdown and executive summaries. Use this view to review and export those outputs." />
        {!data ? <LoadingSkeleton rows={4} /> : (
          <div className="space-y-4">
            {data.reports.map((report) => (
              <section key={report.id} className="soc-panel">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.55)]">{report.id}</p>
                    <h2 className="mt-2 text-lg font-semibold text-white">{report.title}</h2>
                    <p className="mt-2 text-sm soc-text-muted">Author: {report.author} · Updated {report.updated}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <SeverityBadge level={report.severity}>{report.severity}</SeverityBadge>
                    <button className="soc-btn-secondary">Preview</button>
                    <button className="soc-btn-primary">Export</button>
                  </div>
                </div>
              </section>
            ))}
          </div>
        )}
      </Layout>
    </RequireAuth>
  );
}
