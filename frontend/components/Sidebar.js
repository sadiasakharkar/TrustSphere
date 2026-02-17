import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';

const commonNav = [
  { href: '/dashboard', label: 'Dashboard', icon: 'DS' },
  { href: '/incidents', label: 'Incidents', icon: 'IN' },
  { href: '/playbooks', label: 'Playbooks', icon: 'PB' },
  { href: '/analytics', label: 'Analytics', icon: 'AN' },
  { href: '/settings', label: 'Settings', icon: 'ST' }
];

const adminNav = [
  { href: '/settings#users', label: 'User Mgmt', icon: 'UM' },
  { href: '/settings#system', label: 'System Config', icon: 'SC' },
  { href: '/settings#audit', label: 'Audit Logs', icon: 'AL' }
];

export default function Sidebar({ collapsed, setCollapsed }) {
  const router = useRouter();
  const { isAdmin } = useAuth();
  const navItems = isAdmin ? [...commonNav, ...adminNav] : commonNav;

  return (
    <aside
      className={`fixed left-0 top-0 z-40 h-screen border-r border-white/10 bg-panel/95 backdrop-blur transition-all duration-300 ${
        collapsed ? 'w-[84px]' : 'w-[250px]'
      }`}
    >
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-3">
        <div className="flex items-center gap-2">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-accent via-secondary to-violet text-xs font-bold text-bg">
            TS
          </div>
          {!collapsed && (
            <div>
              <p className="text-base font-bold text-white">TrustSphere</p>
              <p className="text-[10px] uppercase tracking-wide text-accent">Offline ACIRS</p>
            </div>
          )}
        </div>
        <button
          className="rounded-md border border-white/10 px-2 py-1 text-xs text-text hover:border-accent/60"
          onClick={() => setCollapsed((prev) => !prev)}
        >
          {collapsed ? '>' : '<'}
        </button>
      </div>

      <nav className="space-y-1 p-2">
        {navItems.map((item) => {
          const active = router.asPath === item.href || router.pathname === item.href;
          return (
            <Link
              key={item.href + item.label}
              href={item.href}
              className={`flex items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium transition ${
                active
                  ? 'bg-gradient-to-r from-accent/20 to-violet/20 text-white ring-1 ring-accent/40'
                  : 'text-text hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-md border border-white/10 bg-bg/60 text-[10px]">
                {item.icon}
              </span>
              {!collapsed && item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
