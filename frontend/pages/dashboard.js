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

const analystActions = [
  { title: 'Triage Queue', detail: '11 incidents waiting analyst decision in next 30m.', badge: 'high' },
  { title: 'Containment Actions', detail: '4 automated controls ready for approval.', badge: 'info' },
  { title: 'Narrative Briefings', detail: '3 executive-ready summaries generated.', badge: 'violet' }
];

const adminActions = [
  { title: 'Governance Alerts', detail: '2 policy drift events detected in model refresh rules.', badge: 'critical' },
  { title: 'Training Operations', detail: '2 model jobs queued; capacity utilization 73%.', badge: 'high' },
  { title: 'Audit Integrity', detail: 'All action logs signed and verified.', badge: 'success' }
];

export default function DashboardPage() {
  const { isAdmin } = useAuth();

  useEffect(() => {
    fetchAlerts();
  }, []);

  const metrics = isAdmin ? adminMetrics : analystMetrics;
  const roleActions = isAdmin ? adminActions : analystActions;

  return (
    <RequireAuth>
      <Layout>
        <section className="mb-3 rounded-xl border border-white/10 bg-gradient-to-r from-panel via-panel to-bg p-4 shadow-card">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wider text-secondary">{isAdmin ? 'Admin Command Deck' : 'Analyst Response Deck'}</p>
              <h2 className="mt-1 text-2xl font-bold text-white">
                {isAdmin ? 'Operational Governance & AI Reliability' : 'Active Threat Triage & Containment'}
              </h2>
              <p className="mt-1 text-sm text-text/80">
                {isAdmin
                  ? 'Monitor user governance, model lifecycle, and system controls across the offline SOC platform.'
                  : 'Prioritize incident handling, assess risk, and execute playbook actions with AI-assisted context.'}
              </p>
            </div>
            <Badge tone={isAdmin ? 'violet' : 'info'}>{isAdmin ? 'Admin View' : 'Analyst View'}</Badge>
          </div>
        </section>

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

        <section className="mt-3 grid gap-3 xl:grid-cols-3">
          {roleActions.map((item) => (
            <Card key={item.title} title={item.title}>
              <p className="text-sm text-text/80">{item.detail}</p>
              <div className="mt-3">
                <Badge tone={item.badge}>Priority</Badge>
              </div>
            </Card>
          ))}
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
