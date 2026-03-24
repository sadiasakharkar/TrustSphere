import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageHeader from '../components/soc/PageHeader';
import SeverityBadge from '../components/soc/SeverityBadge';
import { getTriageQueue } from '../services/api/incidentService';

export default function TriagePage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getTriageQueue().then(setData);
  }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Triage focus: rank incidents by severity, confidence, and SLA, then move into incident detail for evidence review.' }}>
        <PageHeader kicker="Triage" title="Incident Queue" description="Prioritize analyst effort by severity, confidence, owner, and SLA pressure. This queue is the operational bridge from monitoring to investigation." />
        {!data ? <LoadingSkeleton rows={5} /> : !data.queue.length ? <EmptyState title="Queue clear" detail="There are no incidents awaiting analyst action." /> : (
          <div className="soc-panel overflow-x-auto">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>Incident</th><th>Entity</th><th>Tactic</th><th>Owner</th><th>SLA</th><th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {data.queue.map((item) => (
                  <tr key={item.id} className="soc-table-row">
                    <td><a href={`/incident/${item.id}`} className="font-semibold text-white hover:text-[#adc6ff]">{item.id}</a><p className="mt-1 text-xs soc-text-muted">{item.eventType}</p></td>
                    <td>{item.entity}</td>
                    <td>{item.tactic}</td>
                    <td>{item.owner}</td>
                    <td>{item.sla}</td>
                    <td><SeverityBadge level={item.severity}>{item.severity}</SeverityBadge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Layout>
    </RequireAuth>
  );
}
