import { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusIndicator from '../components/soc/StatusIndicator';
import { useAuth } from '../context/AuthContext';
import { getWorkflowInsight } from '../services/api/insight.service';
import { useHybridData } from '../hooks/useHybridData';

export default function SettingsPage() {
  const [insight, setInsight] = useState(null);
  const { isAdmin, session } = useAuth();
  const { data } = useHybridData('administration', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const rolePermissions = {
    Admin: ['Full access', 'View all reports', 'Manage users', 'Take actions'],
    Analyst: ['View threats', 'Analyze emails', 'View history'],
    Employee: ['View inbox', 'Check email risk', 'Basic alerts only']
  };

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const workflow = await getWorkflowInsight('settings');
        if (active) setInsight(workflow);
      } catch {
        if (active) setInsight(null);
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

          {data ? (
            <section className="grid gap-6 xl:grid-cols-[0.85fr,1.15fr]">
              <section className="soc-panel">
                <SectionHeader eyebrow="Access Control" title="Role permissions" description="Role-based access control for admin, analyst, and employee operators." />
                <div className="mt-4 grid gap-3 md:grid-cols-3">
                  {Object.entries(rolePermissions).map(([roleName, permissions]) => (
                    <div key={roleName} className="soc-panel-muted">
                      <p className="text-sm font-semibold text-white">{roleName}</p>
                      <ul className="mt-3 space-y-2 text-xs soc-text-muted">
                        {permissions.map((permission) => (
                          <li key={permission}>{"\u2714"} {permission}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </section>
              <section className="soc-panel">
                <SectionHeader eyebrow="Employee Access" title="Employee permissions" description="Basic view for inbox, risk checks, and limited alert visibility." />
                <div className="mt-4 space-y-3">
                  {rolePermissions.Employee.map((permission) => (
                    <div key={permission} className="soc-panel-muted flex items-center gap-3">
                      <span className="material-symbols-outlined text-[rgba(140,180,255,0.85)]">verified</span>
                      <p className="text-sm text-white">{permission}</p>
                    </div>
                  ))}
                </div>
              </section>
            </section>
          ) : null}

          {data ? (
            <section className="grid gap-6 xl:grid-cols-[0.85fr,1.15fr]">
              <section className="soc-panel">
                <SectionHeader eyebrow="Models" title="Backend model health" />
                <div className="mt-4 space-y-3">
                  {(data.modelHealth || []).map((item) => (
                    <div key={item.name} className="soc-panel-muted flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{item.name}</p>
                        <p className="mt-1 text-xs soc-text-muted">{item.detail}</p>
                      </div>
                      <StatusIndicator status={item.status} pulse={item.status === 'Bootstrapping'} />
                    </div>
                  ))}
                </div>
              </section>
              <section className="soc-panel">
                <SectionHeader eyebrow="Config" title="System configuration" />
                <div className="mt-4 space-y-3">
                  {Object.entries(data.systemConfig || {}).map(([key, value]) => (
                    <div key={key} className="soc-panel-muted flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-white">{key}</p>
                      <StatusIndicator status={String(value)} />
                    </div>
                  ))}
                </div>
              </section>
            </section>
          ) : null}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}
