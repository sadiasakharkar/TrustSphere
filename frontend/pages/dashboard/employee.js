import DashboardLayout from '../../components/dashboard/DashboardLayout';
import RequireAuth from '../../components/RequireAuth';
import RoleGuard from '../../components/RoleGuard';
import IncidentCard from '../../components/soc/IncidentCard';
import { useIncidentApprovals } from '../../hooks/useIncidentApprovals';

const alerts = [
  { title: 'Email', value: '2' },
  { title: 'Login', value: '1' },
  { title: 'Device', value: '0' },
];

export default function EmployeeDashboardPage() {
  const { incidents, currentTime } = useIncidentApprovals();

  return (
    <RequireAuth>
      <RoleGuard allowedRoles={['employee']} fallback={null}>
        <DashboardLayout role="employee">
          <div className="grid gap-4 lg:grid-cols-3">
            <section className="soc-panel flex min-h-[148px] flex-col justify-between">
              <p className="soc-kicker">Action</p>
              <h2 className="soc-section-title">Report</h2>
              <button className="soc-btn-primary mt-6 w-full">Report Incident</button>
            </section>

            <section className="soc-panel lg:col-span-2">
              <p className="soc-kicker">Alerts</p>
              <h2 className="soc-section-title">Mine</h2>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                {alerts.map((item) => (
                  <div key={item.title} className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">{item.title}</p>
                    <p className="mt-3 text-3xl font-bold text-white">{item.value}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <section className="soc-panel max-w-sm">
            <p className="soc-kicker">Status</p>
            <h2 className="soc-section-title">Secure</h2>
            <div className="mt-5 inline-flex items-center rounded-full border border-[rgba(65,71,85,0.55)] bg-[rgba(28,32,38,0.92)] px-3 py-2 text-sm font-semibold text-white">
              <span className="mr-2 inline-flex h-2.5 w-2.5 rounded-full bg-[#52d4a6]" />
              Normal
            </div>
          </section>

          <section className="grid gap-4">
            <div>
              <p className="soc-kicker">Approvals</p>
              <h2 className="soc-section-title">Pending</h2>
            </div>
            {incidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                role="employee"
                currentTime={currentTime}
              />
            ))}
          </section>
        </DashboardLayout>
      </RoleGuard>
    </RequireAuth>
  );
}
