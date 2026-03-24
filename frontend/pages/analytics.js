import { useMemo } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import { AnomalyLineChart, DualSeriesBarChart } from '../components/Charts';
import Card from '../components/Card';
import DataTable from '../components/soc/DataTable';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { analyticsTrend, anomalousEntities, behavioralDeviationByZone, correlatedAlertsByZone } from '../data/mockData';

const columns = [
  { key: 'entity', label: 'Entity' },
  { key: 'type', label: 'Type' },
  { key: 'score', label: 'Risk' },
  { key: 'signal', label: 'Signal' }
];

export default function AnalyticsPage() {
  const rows = useMemo(() => anomalousEntities, []);

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <SectionHeader
            eyebrow="Analytics"
            title="Behavioral Analytics"
            description="Review anomaly trends and concentration by entity without clutter. This page is intentionally sparse so charts remain readable."
          />

          <section className="grid gap-6 xl:grid-cols-2">
            <AnomalyLineChart series={analyticsTrend} title="Behavioral Deviation Trend" label="Deviation score" />
            <DualSeriesBarChart labels={['Zone A', 'Zone B', 'Zone C', 'Zone D', 'Zone E', 'Zone F']} firstSeries={behavioralDeviationByZone} secondSeries={correlatedAlertsByZone} title="Deviation vs correlated alerts" />
          </section>

          <Card title="Top anomalous entities" subtitle="Ranked by current behavioral risk score.">
            <DataTable
              columns={columns}
              rows={rows}
              getRowKey={(row) => row.entity}
              renderCell={(row, key) => {
                if (key === 'entity') return <span className="font-semibold text-white">{row.entity}</span>;
                if (key === 'score') return <StatusBadge tone={row.score > 90 ? 'critical' : row.score > 80 ? 'high' : 'medium'}>{row.score}</StatusBadge>;
                return row[key];
              }}
            />
          </Card>
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
