import { useEffect } from 'react';
import Layout from '../components/Layout';
import Badge from '../components/Badge';
import Card from '../components/Card';
import Table from '../components/Table';
import RequireAuth from '../components/RequireAuth';
import { AnomalyLineChart, DualSeriesBarChart } from '../components/Charts';
import { analyticsTrend, anomalousEntities, behavioralDeviationByZone, correlatedAlertsByZone } from '../data/mockData';
import { fetchAnalytics } from '../services/apiPlaceholders';

const columns = ['Entity', 'Type', 'Risk Score', 'Event Count', 'Signal'];

export default function AnalyticsPage() {
  useEffect(() => {
    fetchAnalytics('24h');
  }, []);

  return (
    <RequireAuth>
      <Layout>
        <section className="grid gap-3 xl:grid-cols-2">
          <AnomalyLineChart series={analyticsTrend} title="Behavioral Deviations" label="Deviation Index" />
          <DualSeriesBarChart
            title="Anomalies per Segment"
            labels={['Payments', 'Branch', 'ATM', 'Core API', 'IAM', 'Reporting']}
            firstSeries={behavioralDeviationByZone}
            secondSeries={correlatedAlertsByZone}
          />
        </section>

        <Card className="mt-3" title="Top Anomalous Entities" subtitle="Cross-metric risk correlation">
          <Table
            columns={columns}
            rows={anomalousEntities}
            rowKey="entity"
            renderCell={(row, column) => {
              if (column === 'Entity') return row.entity;
              if (column === 'Type') return row.type;
              if (column === 'Risk Score') {
                const tone = row.score >= 90 ? 'critical' : row.score >= 80 ? 'high' : 'success';
                return <Badge tone={tone}>{row.score}</Badge>;
              }
              if (column === 'Event Count') return row.events;
              if (column === 'Signal') return row.signal;
              return '';
            }}
          />
        </Card>
      </Layout>
    </RequireAuth>
  );
}
