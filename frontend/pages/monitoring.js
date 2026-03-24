import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import AlertTable from '../components/soc/AlertTable';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageHeader from '../components/soc/PageHeader';
import { getMonitoringFeed } from '../services/api/incidentService';

export default function MonitoringPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getMonitoringFeed().then(setData);
  }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Monitoring focus: watch live detectors, identify converging signals, then promote suspicious clusters into triage.' }}>
        <PageHeader kicker="Monitoring" title="Live Detection Monitoring" description="Watch real-time telemetry from UEBA and adjacent detectors. Analysts should filter here, verify signal quality, and escalate meaningful clusters into the triage queue." />
        {!data ? <LoadingSkeleton rows={5} /> : data.events.length ? <div className="soc-panel"><AlertTable rows={data.events} /></div> : <EmptyState title="No live events" detail="Telemetry feed is healthy but no suspicious activity is currently streaming into this view." />}
      </Layout>
    </RequireAuth>
  );
}
