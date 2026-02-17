import { useEffect } from 'react';
import Layout from '../components/Layout';
import MetricCard from '../components/MetricCard';
import { AlertPieChart, AnomalyLineChart, SeverityBarChart } from '../components/Charts';
import Card from '../components/Card';
import Badge from '../components/Badge';
import RequireAuth from '../components/RequireAuth';
import { useAuth } from '../context/AuthContext';
import { adminMetrics, aiPipeline, alertTypeSplit, analystMetrics, anomalyTrend, severityDistribution } from '../data/mockData';
import { fetchAlerts } from '../services/apiPlaceholders';

const statusTone = {
  Operational: 'success',
  'High Activity': 'high'
};

export default function DashboardPage() {
  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchAlerts();
  }, []);

  const metrics = isAdmin ? adminMetrics : analystMetrics;

  return (
    <RequireAuth>
      <Layout>
        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </section>

        <section className="mt-3 grid gap-3 xl:grid-cols-2">
          <AnomalyLineChart series={anomalyTrend} />
          <AlertPieChart items={alertTypeSplit} />
        </section>

        <section className="mt-3">
          <SeverityBarChart values={severityDistribution} />
        </section>

        <section className="mt-3">
          <Card title="Autonomous AI Pipeline Status" subtitle="Self-explanatory flow from data ingestion to response narrative">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {aiPipeline.map((item) => (
                <div key={item.module} className="rounded-xl border border-white/10 bg-bg/50 p-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-white">{item.module}</p>
                    <Badge tone={statusTone[item.status] || 'info'}>{item.status}</Badge>
                  </div>
                  <p className="text-xs text-text/75">{item.detail}</p>
                </div>
              ))}
            </div>
          </Card>
        </section>
      </Layout>
    </RequireAuth>
  );
}
