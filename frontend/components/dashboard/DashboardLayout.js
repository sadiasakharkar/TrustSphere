import Link from 'next/link';
import { useRouter } from 'next/router';
import { useMemo, useState } from 'react';
import { useAuth } from '../../context/AuthContext';

const roleBadgeLabel = {
  employee: 'Employee',
  analyst: 'Analyst',
  admin: 'Admin',
};

const roleDashboardHref = {
  employee: '/dashboard/employee',
  analyst: '/dashboard/analyst',
  admin: '/dashboard/admin',
};

export function getDashboardNavigation(role = 'employee') {
  const normalizedRole = String(role || 'employee').toLowerCase();
  const baseHref = roleDashboardHref[normalizedRole] || roleDashboardHref.employee;
  return [
    { href: `${baseHref}#dashboard`, label: 'Dashboard', icon: 'dashboard' },
    { href: `${baseHref}#incidents`, label: 'Incidents', icon: 'assignment' },
    { href: `${baseHref}#activity`, label: 'Activity', icon: 'monitoring' },
    { href: `${baseHref}#settings`, label: 'Settings', icon: 'settings' },
  ];
}

function isActiveRoute(router, href) {
  const [path] = String(href).split('#');
  return router.pathname === path;
}

export default function DashboardLayout({ role = 'employee', children }) {
  const router = useRouter();
  const { session, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const navigation = useMemo(() => getDashboardNavigation(role), [role]);
  const displayRole = roleBadgeLabel[String(role || 'employee').toLowerCase()] || 'Employee';
  const displayName = session?.name || session?.username || 'secure.operator';
  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'TS';

  return (
    <div className="soc-shell">
      {mobileOpen ? (
        <button
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation"
        />
      ) : null}

      <aside className={`soc-sidebar fixed z-40 flex h-screen flex-col py-4 transition-transform duration-300 ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="mb-5 flex items-center gap-3 px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#d8e2ff_0%,#4b8eff_100%)] text-[#00285c] shadow-soft">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>shield_lock</span>
          </div>
          <div className="overflow-hidden">
            <h1 className="font-headline text-xl font-extrabold tracking-tight text-[#adc6ff]">TrustSphere</h1>
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3">
          {navigation.map((item) => {
            const active = isActiveRoute(router, item.href);
            return (
              <Link
                key={`${role}-${item.href}`}
                href={item.href}
                className={`soc-nav-link ${active ? 'soc-nav-link-active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <span className="soc-nav-icon material-symbols-outlined">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="soc-workspace lg:ml-64">
        <div className="soc-layout-frame">
          <header className="soc-topbar">
            <div className="flex items-center gap-3">
              <button className="soc-btn-ghost lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
                <span className="material-symbols-outlined">menu</span>
              </button>
              <span className="inline-flex items-center rounded-full border border-[rgba(65,71,85,0.55)] bg-[rgba(28,32,38,0.92)] px-3 py-2 text-xs font-semibold text-white">
                {displayRole}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button className="soc-btn-ghost" type="button" aria-label="Notifications">
                <span className="material-symbols-outlined">notifications</span>
              </button>

              <div className="relative">
                <button
                  type="button"
                  className="inline-flex h-10 items-center gap-3 rounded-xl border border-[rgba(65,71,85,0.55)] bg-[rgba(28,32,38,0.92)] px-3 text-sm font-medium text-white transition hover:bg-[rgba(49,53,60,0.92)]"
                  onClick={() => setMenuOpen((value) => !value)}
                  aria-expanded={menuOpen}
                  aria-haspopup="menu"
                >
                  <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(75,142,255,0.18)] text-xs font-bold text-[#d8e2ff]">
                    {initials}
                  </span>
                  <span className="hidden sm:inline">{displayName}</span>
                  <span className="material-symbols-outlined text-[18px]">expand_more</span>
                </button>

                {menuOpen ? (
                  <div
                    className="absolute right-0 top-12 z-50 min-w-[180px] rounded-xl border border-[rgba(65,71,85,0.55)] bg-[rgba(16,20,26,0.98)] p-2 shadow-card"
                    role="menu"
                  >
                    <button
                      type="button"
                      className="soc-nav-link w-full justify-start"
                      onClick={() => {
                        setMenuOpen(false);
                        router.push(`${roleDashboardHref[String(role || 'employee').toLowerCase()] || roleDashboardHref.employee}#settings`);
                      }}
                      role="menuitem"
                    >
                      <span className="soc-nav-icon material-symbols-outlined">manage_accounts</span>
                      <span>Profile</span>
                    </button>
                    <button
                      type="button"
                      className="soc-nav-link w-full justify-start"
                      onClick={() => {
                        setMenuOpen(false);
                        logout();
                        router.push('/login');
                      }}
                      role="menuitem"
                    >
                      <span className="soc-nav-icon material-symbols-outlined">logout</span>
                      <span>Logout</span>
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          </header>

          <section className="grid gap-4 pt-6 lg:gap-5">
            {children}
          </section>
        </div>
      </main>
    </div>
  );
}
