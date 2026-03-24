import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { getMonitoringFeed } from '../services/api/incidentService';
import { getDetectionsOverview } from '../services/api/detectionService';

const eventColumns = [
  { key: 'timestamp', label: 'Time' },
  { key: 'entity', label: 'Entity' },
  { key: 'eventType', label: 'Event' },
  { key: 'source', label: 'Source' },
  { key: 'severity', label: 'Severity' }
];

export default function MonitoringPage() {
  const [events, setEvents] = useState(null);
  const [detectors, setDetectors] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [eventResponse, detectionResponse] = await Promise.all([
          getMonitoringFeed(),
          getDetectionsOverview()
        ]);
        if (!active) return;
        setEvents(eventResponse.events);
        setDetectors(detectionResponse.detectors);
      } catch (err) {
        if (active) setError(err.message || 'Unable to load monitoring feed.');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Monitoring focus', description: 'Track event velocity, detector health, and severity concentration before promoting activity into incident handling.' }}>
        <PageContainer>
          <SectionHeader
            eyebrow="Monitoring"
            title="Live Security Monitoring"
            description="Review the latest security events and detector posture using backend-driven telemetry."
          />

          {!events && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Monitoring unavailable" detail={error} /> : (
            <div className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
              <section className="soc-panel">
                <SectionHeader eyebrow="Events" title="Live event feed" description="Recent high-signal telemetry from the backend event stream." />
                <div className="mt-4">
                  <DataTable
                    columns={eventColumns}
                    rows={events || []}
                    getRowKey={(row) => row.id}
                    renderCell={(row, key) => {
                      if (key === 'severity') return <StatusBadge tone={row.severity}>{row.severity}</StatusBadge>;
                      return row[key];
                    }}
                  />
                </div>
              </section>

              <section className="soc-panel">
                <SectionHeader eyebrow="Detectors" title="Detection feed" description="Current detector precision and runtime posture." />
                <div className="mt-4 space-y-3">
                  {(detectors || []).map((item) => (
                    <div key={item.id} className="soc-panel-muted">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-white">{item.source}</p>
                          <p className="mt-1 text-xs soc-text-muted">Precision {item.precision} · drift {item.drift}</p>
                        </div>
                        <StatusBadge tone={item.status}>{item.status}</StatusBadge>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
