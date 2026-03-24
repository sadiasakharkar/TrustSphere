import { useEffect, useState } from 'react';
import RightInsightDrawer from './RightInsightDrawer';
import SocSidebar from './SocSidebar';
import SocTopbar from './SocTopbar';

export default function AppShell({ children, insightSummary = null }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const onResize = () => {
      const desktop = window.innerWidth >= 1024;
      setIsDesktop(desktop);
      if (!desktop) {
        setCollapsed(false);
      }
      if (desktop) {
        setMobileOpen(false);
      }
    };
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const sidebarWidth = collapsed ? 88 : 256;

  return (
    <div className="soc-shell">
      <SocSidebar
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onToggle={() => setCollapsed((value) => !value)}
        onClose={() => setMobileOpen(false)}
      />
      <main className="soc-workspace" style={isDesktop ? { marginLeft: sidebarWidth } : undefined}>
        <div className="soc-layout-frame">
          <SocTopbar onMenu={() => setMobileOpen(true)} />
          <div className={`soc-content-grid ${insightSummary ? 'soc-content-grid-with-drawer' : ''}`}>
            <section className="soc-content-main">{children}</section>
            <RightInsightDrawer summary={insightSummary} />
          </div>
        </div>
      </main>
    </div>
  );
}
