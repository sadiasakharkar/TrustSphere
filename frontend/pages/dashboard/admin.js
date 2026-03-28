import DashboardLayout from '../../components/dashboard/DashboardLayout';
import RequireAuth from '../../components/RequireAuth';
import RoleGuard from '../../components/RoleGuard';

const cards = [
  { title: 'Health', value: 'Healthy' },
  { title: 'Users', value: '248' },
  { title: 'Risks', value: '21' },
  { title: 'Policy', value: 'Active' },
];

export default function AdminDashboardPage() {
  return (
    <RequireAuth adminOnly>
      <RoleGuard allowedRoles={['admin']} fallback={null}>
        <DashboardLayout role="admin">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {cards.map((item) => (
              <section key={item.title} className="soc-panel">
                <p className="soc-kicker">{item.title}</p>
                <h2 className="soc-section-title">{item.title}</h2>
                <p className="mt-5 text-3xl font-extrabold text-white">{item.value}</p>
              </section>
            ))}
          </div>
        </DashboardLayout>
      </RoleGuard>
    </RequireAuth>
  );
}
