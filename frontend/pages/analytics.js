import { useEffect } from 'react';
import Layout from '../components/Layout';
import { AnomalyLineChart } from '../components/Charts';
import { analyticsTrend, anomalousEntities } from '../data/mockData';
import { fetchAnalytics } from '../services/apiPlaceholders';

const riskBadge = (score) => {
  if (score >= 90) return 'bg-red-500/20 text-red-300';
  if (score >= 80) return 'bg-violet/30 text-violet-200';
  return 'bg-secondary/20 text-secondary';
};

export default function AnalyticsPage() {
  useEffect(() => {
    fetchAnalytics('24h');
  }, []);

  return (
    <Layout>
      <AnomalyLineChart series={analyticsTrend} />

      <div className="card mt-4 overflow-x-auto p-4">
        <h3 className="mb-3 text-lg font-semibold text-white">Top 5 Anomalous Users / Hosts</h3>
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-white/10 text-text/70">
            <tr>
              <th className="px-3 py-2">Entity</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Risk Score</th>
              <th className="px-3 py-2">Event Count</th>
            </tr>
          </thead>
          <tbody>
            {anomalousEntities.map((row) => (
              <tr key={row.entity} className="border-b border-white/5">
                <td className="px-3 py-3">{row.entity}</td>
                <td className="px-3 py-3">{row.type}</td>
                <td className="px-3 py-3">
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${riskBadge(row.score)}`}>{row.score}</span>
                </td>
                <td className="px-3 py-3">{row.events}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
