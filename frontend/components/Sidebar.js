import Link from 'next/link';
import { useRouter } from 'next/router';

const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/incidents', label: 'Incidents' },
  { href: '/playbooks', label: 'Playbooks' },
  { href: '/analytics', label: 'Analytics' },
  { href: '/settings', label: 'Settings' }
];

export default function Sidebar({ collapsed, setCollapsed }) {
  const router = useRouter();

  return (
    <aside
      className={`fixed left-0 top-0 z-40 h-screen border-r border-white/10 bg-panel/95 backdrop-blur transition-all duration-300 ${
        collapsed ? 'w-[84px]' : 'w-[250px]'
      }`}
    >
      <div className="flex h-16 items-center justify-between border-b border-white/10 px-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-accent to-violet" />
          {!collapsed && <span className="text-lg font-bold text-white">TrustSphere</span>}
        </div>
        <button
          className="rounded-md border border-white/10 px-2 py-1 text-sm text-text hover:border-accent/60"
          onClick={() => setCollapsed((prev) => !prev)}
        >
          {collapsed ? '>' : '<'}
        </button>
      </div>

      <nav className="space-y-2 p-3">
        {navItems.map((item) => {
          const active = router.pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                active
                  ? 'bg-gradient-to-r from-accent/20 to-violet/20 text-white ring-1 ring-accent/40'
                  : 'text-text hover:bg-white/5 hover:text-white'
              }`}
            >
              {!collapsed ? item.label : item.label[0]}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
