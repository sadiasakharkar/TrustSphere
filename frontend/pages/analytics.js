import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import { AnomalyLineChart, SeverityBarChart } from '../components/Charts';
import Card from '../components/Card';
import DataTable from '../components/soc/DataTable';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { getAnalyticsWorkspace } from '../services/api/analytics.service';

const columns = [
  { key: 'entity', label: 'Entity' },
  { key: 'type', label: 'Type' },
  { key: 'score', label: 'Risk' },
  { key: 'signal', label: 'Signal' }
];

export default function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const workspace = await getAnalyticsWorkspace();
        if (active) setData(workspace);
      } catch (err) {
        if (active) setError(err.message || 'Unable to load analytics.');
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
            eyebrow="Analytics"
            title="Behavioral Analytics"
            description="Review anomaly trends and concentration by entity without clutter. This page is intentionally sparse so charts remain readable."
          />

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Analytics snapshot" detail={error} /> : (
            <>
              <section className="grid gap-6 xl:grid-cols-2">
                <AnomalyLineChart series={data.riskDistribution} title="Incident Risk Distribution" label="Risk score" />
                <SeverityBarChart values={data.severityValues} title="Severity Distribution" />
              </section>

              <Card title="Recent correlated activity" subtitle="Backend-aggregated operational activity from the SOC metrics endpoint.">
                <DataTable
                  columns={columns}
                  rows={data.recentActivity}
                  getRowKey={(row) => row.id}
                  renderCell={(row, key) => {
                    if (key === 'entity') return <span className="font-semibold text-white">{row.entity}</span>;
                    if (key === 'score') return <StatusBadge tone={row.severity}>{row.score}</StatusBadge>;
                    if (key === 'type') return row.source;
                    if (key === 'signal') return row.eventType;
                    return row[key];
                  }}
                />
              </Card>
            </>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
