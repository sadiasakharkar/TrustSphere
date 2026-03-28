import DashboardLayout from '../../components/dashboard/DashboardLayout';
import RequireAuth from '../../components/RequireAuth';
import RoleGuard from '../../components/RoleGuard';
import IncidentCard from '../../components/soc/IncidentCard';
import { useIncidentApprovals } from '../../hooks/useIncidentApprovals';

const riskCards = [
  { title: 'Critical', value: '04' },
  { title: 'High', value: '09' },
  { title: 'Medium', value: '17' },
];

export default function AnalystDashboardPage() {
  const { incidents, currentTime, counts, liveActivity, approveIncident, rejectIncident, modifyIncident } = useIncidentApprovals();

  return (
    <RequireAuth>
      <RoleGuard allowedRoles={['analyst']} fallback={null}>
        <DashboardLayout role="analyst">
          <div id="dashboard" className="grid gap-4 lg:grid-cols-3">
            <section className="soc-panel">
              <p className="soc-kicker">Incidents</p>
              <h2 className="soc-section-title">Active</h2>
              <p className="mt-5 text-4xl font-extrabold text-white">{counts.active}</p>
            </section>

            <section className="soc-panel">
              <p className="soc-kicker">Approvals</p>
              <h2 className="soc-section-title">Pending</h2>
              <p className="mt-5 text-4xl font-extrabold text-white">{counts.pending}</p>
            </section>

            <section className="soc-panel">
              <p className="soc-kicker">Risk</p>
              <h2 className="soc-section-title">Overview</h2>
              <div className="mt-5 grid gap-3">
                {riskCards.map((item) => (
                  <div key={item.title} className="flex items-center justify-between rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(24,28,34,0.85)] px-4 py-3">
                    <span className="text-sm font-semibold text-white">{item.title}</span>
                    <span className="text-lg font-bold text-white">{item.value}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <section id="incidents" className="grid gap-4">
            <div>
              <p className="soc-kicker">Approvals</p>
              <h2 className="soc-section-title">Pending</h2>
            </div>
            {incidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                role="analyst"
                currentTime={currentTime}
                onApprove={(incidentId) => approveIncident(incidentId, 'analyst')}
                onReject={(incidentId) => rejectIncident(incidentId, 'analyst')}
                onModify={(incidentId, action) => modifyIncident(incidentId, action, 'analyst')}
              />
            ))}
          </section>

          <section id="activity" className="soc-panel">
            <p className="soc-kicker">Activity</p>
            <h2 className="soc-section-title">Live</h2>
            <div className="mt-4 grid gap-2">
              {liveActivity.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(24,28,34,0.85)] px-3 py-2 text-sm">
                  <span className="text-white">{item.message}</span>
                  <span className="soc-text-muted">{new Intl.DateTimeFormat('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date(item.timestamp))}</span>
                </div>
              ))}
            </div>
          </section>
          <div id="settings" className="hidden" />
        </DashboardLayout>
      </RoleGuard>
    </RequireAuth>
  );
}
