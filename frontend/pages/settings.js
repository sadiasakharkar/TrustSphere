import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusIndicator from '../components/soc/StatusIndicator';
import { useAuth } from '../context/AuthContext';
import { getAdministrationWorkspace } from '../services/api/detectionService';
import { getWorkflowInsight } from '../services/api/insight.service';

export default function SettingsPage() {
  const [data, setData] = useState(null);
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState('');
  const { isAdmin, session } = useAuth();

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const workspace = await getAdministrationWorkspace();
        if (active) {
          setData(workspace);
          const workflow = await getWorkflowInsight('settings');
          if (active) setInsight(workflow);
        }
      } catch (err) {
        if (active) setError(err.message || 'Unable to load administration data.');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <RequireAuth adminOnly>
      <Layout insightSummary={insight}>
        <PageContainer>
          <SectionHeader
            eyebrow="Settings"
            title="Workspace Settings"
            description="Operator preferences and platform status. Administrators see additional governance controls in the same Stitch layout."
          />

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="System settings snapshot" detail={error} /> : (
            <div className="grid gap-6 xl:grid-cols-[0.85fr,1.15fr]">
              <section className="soc-panel">
                <SectionHeader eyebrow="Profile" title={session.username || 'secure.operator'} description={`Role: ${session.role}`} />
                <div className="mt-4 space-y-3">
                  {data.systemStatus.map((item) => (
                    <div key={item.label} className="soc-panel-muted flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-white">{item.label}</p>
                      <StatusIndicator status={item.value} pulse={item.value === 'Ready'} />
                    </div>
                  ))}
                </div>
              </section>

              <section className="soc-panel">
                <SectionHeader eyebrow={isAdmin ? 'Administration' : 'Read only'} title={isAdmin ? 'User and audit controls' : 'Audit visibility'} />
                <div className="mt-4 space-y-3">
                  {(isAdmin ? data.users : data.auditLogs).map((item) => (
                    <div key={item.id || item.name} className="soc-panel-muted">
                      {'name' in item ? (
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-white">{item.name}</p>
                            <p className="mt-1 text-xs soc-text-muted">{item.role}</p>
                          </div>
                          <StatusIndicator status={item.status} />
                        </div>
                      ) : (
                        <div>
                          <p className="text-sm font-semibold text-white">{item.action}</p>
                          <p className="mt-1 text-xs soc-text-muted">{item.timestamp} · {item.actor} · {item.result}</p>
                        </div>
                      )}
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
