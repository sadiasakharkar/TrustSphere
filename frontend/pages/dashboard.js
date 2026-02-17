import Layout from '../components/Layout';
import MetricCard from '../components/MetricCard';
import { AlertPieChart, AnomalyLineChart, SeverityBarChart } from '../components/Charts';
import { alertTypeSplit, anomalyTrend, metrics, severityDistribution } from '../data/mockData';
import { fetchAlerts } from '../services/apiPlaceholders';
import { useEffect } from 'react';

export default function DashboardPage() {
  useEffect(() => {
    fetchAlerts();
  }, []);

  return (
    <Layout>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <AnomalyLineChart series={anomalyTrend} />
        <AlertPieChart items={alertTypeSplit} />
      </section>

      <section className="mt-4">
        <SeverityBarChart values={severityDistribution} />
      </section>
    </Layout>
  );
}
