import Link from 'next/link';
import { useRouter } from 'next/router';
import { getNavigationForRole } from './navigation';
import { useAuth } from '../../context/AuthContext';

export default function SocSidebar({ collapsed, mobileOpen, onToggle, onClose }) {
  const router = useRouter();
  const { session } = useAuth();
  const visibleNavigation = getNavigationForRole(session.role);
  const roleLabel = session.role === 'admin' ? 'Admin' : session.role === 'employee' ? 'Employee' : 'Analyst';
  const isActiveRoute = (href) => {
    if (router.pathname === href) return true;
    if (href === '/incidents' && (router.pathname === '/triage' || router.pathname === '/incident/[id]')) return true;
    if (href === '/playbooks' && router.pathname === '/response') return true;
    if (href === '/settings' && router.pathname === '/administration') return true;
    return false;
  };

  return (
    <>
      {mobileOpen ? <button className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={onClose} aria-label="Close sidebar overlay" /> : null}
      <aside className={`soc-sidebar ${collapsed ? 'lg:soc-sidebar-collapsed' : ''} ${mobileOpen ? 'translate-x-0' : '-translate-x-full'} fixed flex flex-col py-4 transition-transform duration-300 lg:translate-x-0`}>
        <div className="mb-6 flex items-center justify-between px-5">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,#d8e2ff_0%,#4b8eff_100%)] text-[#00285c] shadow-soft">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>shield_lock</span>
            </div>
            {!collapsed ? (
              <div>
                <h1 className="font-headline text-xl font-extrabold tracking-tight text-[#adc6ff]">TrustSphere</h1>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.55)]">SOC Analyst</p>
              </div>
            ) : null}
          </div>
          <button className="soc-btn-ghost hidden px-2 py-1 lg:inline-flex" onClick={onToggle} aria-label="Toggle sidebar width">
            <span className="material-symbols-outlined">{collapsed ? 'left_panel_open' : 'left_panel_close'}</span>
          </button>
        </div>

        <div className="mb-6 px-4">
          <div className="soc-panel-muted px-4 py-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.55)]">Current operator</p>
            {!collapsed ? (
              <>
                <p className="mt-2 text-sm font-semibold text-white">{session.username || 'secure.operator'}</p>
                <p className="mt-1 text-xs soc-text-muted">{roleLabel}</p>
              </>
            ) : <p className="mt-2 text-xs font-semibold text-white">{session.role?.slice(0,1)?.toUpperCase()}</p>}
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3">
          {visibleNavigation.map((item) => {
            const active = isActiveRoute(item.href);
            return (
              <Link key={`${session.role}-${item.label}-${item.href}`} href={item.href} className={`soc-nav-link ${active ? 'soc-nav-link-active' : ''}`} onClick={onClose}>
                <span className="soc-nav-icon material-symbols-outlined">{item.icon}</span>
                {!collapsed ? <span>{item.label}</span> : null}
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
