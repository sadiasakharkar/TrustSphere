import { useEffect, useMemo, useState } from 'react';
import { notifications } from '../../data/socConsoleData';
import CommandPalette from './CommandPalette';
import RightInsightDrawer from './RightInsightDrawer';
import SocSidebar from './SocSidebar';
import SocTopbar from './SocTopbar';
import { socNavigation } from './navigation';

export default function AppShell({ children, insightSummary }) {
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(true);

  useEffect(() => {
    const onResize = () => {
      setCollapsed(window.innerWidth < 1280);
      setDrawerOpen(window.innerWidth >= 1440);
    };
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setPaletteOpen((value) => !value);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const paletteActions = useMemo(() => socNavigation.map((item) => ({ href: item.href, label: item.label, section: item.section })), []);
  const contentOffset = collapsed ? 88 : 256;
  const rightOffset = drawerOpen ? 352 : 0;

  return (
    <div className="soc-shell">
      <SocSidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
      <div className="soc-workspace" style={{ marginLeft: contentOffset, marginRight: rightOffset }}>
        <SocTopbar
          onTogglePalette={() => setPaletteOpen(true)}
          onToggleInsights={() => setDrawerOpen((value) => !value)}
          notifications={notifications}
        />
        <div className="pt-6">{children}</div>
      </div>
      <RightInsightDrawer open={drawerOpen} summary={insightSummary} />
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} actions={paletteActions} />
    </div>
  );
}
