import Link from 'next/link';
import { useRouter } from 'next/router';
import { socNavigation } from './navigation';
import { useAuth } from '../../context/AuthContext';

export default function SocSidebar({ collapsed, onToggle }) {
  const router = useRouter();
  const { isAdmin, session } = useAuth();
  const items = socNavigation.filter((item) => !item.adminOnly || isAdmin);
  const grouped = items.reduce((acc, item) => {
    acc[item.section] = acc[item.section] || [];
    acc[item.section].push(item);
    return acc;
  }, {});

  return (
    <aside className={`soc-sidebar ${collapsed ? 'soc-sidebar-collapsed' : ''} flex flex-col py-4`}>
      <div className="mb-6 flex items-center justify-between px-5">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#d8e2ff_0%,#4b8eff_100%)] text-[#00285c] shadow-soft">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>shield_lock</span>
          </div>
          {!collapsed ? (
            <div>
              <h1 className="font-headline text-xl font-extrabold tracking-tight text-[#adc6ff]">TrustSphere</h1>
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[rgba(193,198,215,0.55)]">SOC Console</p>
            </div>
          ) : null}
        </div>
        <button className="soc-btn-ghost px-2 py-1" onClick={onToggle} aria-label="Toggle sidebar">
          <span className="material-symbols-outlined">{collapsed ? 'menu_open' : 'menu'}</span>
        </button>
      </div>

      <div className="mb-6 px-4">
        <div className="soc-panel-muted px-4 py-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.55)]">Active role</p>
          {!collapsed ? (
            <>
              <p className="mt-2 text-sm font-semibold text-white">{session.role}</p>
              <p className="mt-1 truncate text-xs soc-text-muted">{session.username || 'Secure terminal'}</p>
            </>
          ) : <p className="mt-2 text-xs font-semibold text-white">{session.role?.slice(0, 1)}</p>}
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3">
        {Object.entries(grouped).map(([section, sectionItems]) => (
          <div key={section}>
            {!collapsed ? <p className="soc-nav-group-label">{section}</p> : null}
            <div className="space-y-1">
              {sectionItems.map((item) => {
                const active = router.pathname === item.href;
                return (
                  <Link key={item.href} href={item.href} className={`soc-nav-link ${active ? 'soc-nav-link-active' : ''}`}>
                    <span className="soc-nav-icon material-symbols-outlined">{item.icon}</span>
                    {!collapsed ? <span>{item.label}</span> : null}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
