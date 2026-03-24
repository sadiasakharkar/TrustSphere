import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusIndicator from '../components/soc/StatusIndicator';
import { useAuth } from '../context/AuthContext';
import { getAdministrationWorkspace } from '../services/api/detectionService';

export default function SettingsPage() {
  const [data, setData] = useState(null);
  const { isAdmin, session } = useAuth();

  useEffect(() => {
    getAdministrationWorkspace().then(setData);
  }, []);

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <SectionHeader
            eyebrow="Settings"
            title="Workspace Settings"
            description="Operator preferences and platform status. Administrators see additional governance controls in the same Stitch layout."
          />

          {!data ? <LoadingSkeleton rows={5} /> : (
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
