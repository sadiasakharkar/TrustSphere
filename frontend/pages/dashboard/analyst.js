import DashboardLayout from '../../components/dashboard/DashboardLayout';
import RequireAuth from '../../components/RequireAuth';
import RoleGuard from '../../components/RoleGuard';

const riskCards = [
  { title: 'Critical', value: '04' },
  { title: 'High', value: '09' },
  { title: 'Medium', value: '17' },
];

export default function AnalystDashboardPage() {
  return (
    <RequireAuth>
      <RoleGuard allowedRoles={['analyst']} fallback={null}>
        <DashboardLayout role="analyst">
          <div className="grid gap-4 lg:grid-cols-3">
            <section className="soc-panel">
              <p className="soc-kicker">Incidents</p>
              <h2 className="soc-section-title">Active</h2>
              <p className="mt-5 text-4xl font-extrabold text-white">12</p>
            </section>

            <section className="soc-panel">
              <p className="soc-kicker">Approvals</p>
              <h2 className="soc-section-title">Pending</h2>
              <p className="mt-5 text-4xl font-extrabold text-white">5</p>
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
        </DashboardLayout>
      </RoleGuard>
    </RequireAuth>
  );
}
