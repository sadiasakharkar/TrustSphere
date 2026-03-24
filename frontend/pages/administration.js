import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageHeader from '../components/soc/PageHeader';
import StatusIndicator from '../components/soc/StatusIndicator';
import { getAdministrationWorkspace } from '../services/api/detectionService';

export default function AdministrationPage() {
  const [data, setData] = useState(null);
  useEffect(() => { getAdministrationWorkspace().then(setData); }, []);

  return (
    <RequireAuth adminOnly>
      <Layout insightSummary={{ title: 'Administration focus: govern users, system health, and model operations without duplicating intelligence logic in the UI.' }}>
        <PageHeader kicker="Administration" title="Platform Governance" description="Administrators manage users, audit events, model operations, and infrastructure readiness from this workspace." />
        {!data ? <LoadingSkeleton rows={5} /> : (
          <div className="grid gap-6 xl:grid-cols-[1fr,1fr]">
            <section className="soc-panel">
              <h2 className="soc-section-title">System status</h2>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {data.systemStatus.map((item) => (
                  <div key={item.label} className="soc-panel-muted">
                    <p className="text-xs uppercase tracking-[0.16em] text-[rgba(193,198,215,0.55)]">{item.label}</p>
                    <div className="mt-3"><StatusIndicator status={item.value} pulse={item.value === 'Ready'} /></div>
                  </div>
                ))}
              </div>
              <h3 className="mt-6 text-base font-semibold text-white">Audit log</h3>
              <div className="mt-4 space-y-3">
                {data.auditLogs.map((log) => (
                  <div key={log.id} className="soc-panel-muted">
                    <p className="text-sm font-semibold text-white">{log.action}</p>
                    <p className="mt-1 text-xs soc-text-muted">{log.timestamp} · {log.actor} · {log.result}</p>
                  </div>
                ))}
              </div>
            </section>
            <section className="soc-panel">
              <h2 className="soc-section-title">Users and model training</h2>
              <div className="mt-5 space-y-3">
                {data.users.map((user) => (
                  <div key={user.id} className="soc-panel-muted">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{user.name}</p>
                        <p className="mt-1 text-xs soc-text-muted">{user.role}</p>
                      </div>
                      <StatusIndicator status={user.status} />
                    </div>
                  </div>
                ))}
              </div>
              <h3 className="mt-6 text-base font-semibold text-white">Model training status</h3>
              <div className="mt-4 space-y-3">
                {data.modelTrainingStatus.map((job) => (
                  <div key={job.model} className="soc-panel-muted">
                    <p className="text-sm font-semibold text-white">{job.model}</p>
                    <p className="mt-1 text-xs soc-text-muted">{job.state} · ETA {job.eta} · Last run {job.lastRun}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </Layout>
    </RequireAuth>
  );
}
