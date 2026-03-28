import { useMemo } from 'react';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import IncidentCard from '../components/soc/IncidentCard';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import RequireAuth from '../components/RequireAuth';
import { useAuth } from '../context/AuthContext';
import { useIncidentApprovals } from '../hooks/useIncidentApprovals';

export default function ResponsePage() {
  const { session } = useAuth();
  const { incidents, currentTime, counts, approveIncident, rejectIncident, modifyIncident } = useIncidentApprovals();
  const auditRows = useMemo(
    () => incidents.flatMap((incident) => (incident.activityLog || []).slice(-3).map((item, index) => ({
      id: `${incident.id}-${index}-${item.timestamp}`,
      incident: incident.id,
      action: item.action,
      user: item.user,
      timestamp: item.timestamp,
    }))).slice(0, 8),
    [incidents]
  );

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="Approval" title="Response" actions={<a href="#audit" className="soc-btn-secondary">Audit Log</a>} />

          <div className="grid gap-4 md:grid-cols-3">
            <section className="soc-panel">
              <p className="soc-kicker">Pending</p>
              <h2 className="soc-section-title">Approvals</h2>
              <p className="mt-4 text-4xl font-extrabold text-white">{counts.pending}</p>
            </section>
            <section className="soc-panel">
              <p className="soc-kicker">Active</p>
              <h2 className="soc-section-title">Cases</h2>
              <p className="mt-4 text-4xl font-extrabold text-white">{counts.active}</p>
            </section>
            <section id="audit" className="soc-panel">
              <p className="soc-kicker">Audit</p>
              <h2 className="soc-section-title">Log</h2>
              <p className="mt-4 text-4xl font-extrabold text-white">{auditRows.length}</p>
            </section>
          </div>

          <section className="grid gap-4">
            {incidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                role={session.role}
                currentTime={currentTime}
                onApprove={(incidentId) => approveIncident(incidentId, session.username || session.name || 'analyst')}
                onReject={(incidentId) => rejectIncident(incidentId, session.username || session.name || 'analyst')}
                onModify={(incidentId, action) => modifyIncident(incidentId, action, session.username || session.name || 'analyst')}
              />
            ))}
          </section>

          <section className="soc-panel">
            <p className="soc-kicker">Audit</p>
            <h2 className="soc-section-title">Recent</h2>
            <div className="mt-4 grid gap-3">
              {auditRows.map((item) => (
                <div key={item.id} className="soc-panel-muted flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">{item.action}</p>
                    <p className="mt-1 text-xs soc-text-muted">{item.incident} • {item.user}</p>
                  </div>
                  <span className="text-xs soc-text-muted">{new Date(item.timestamp).toLocaleTimeString('en-IN')}</span>
                </div>
              ))}
            </div>
          </section>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}
