import { useEffect, useState } from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const onResize = () => setCollapsed(window.innerWidth < 1024);
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return (
    <div className="min-h-screen bg-glow-grid">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <main
        className="min-h-screen px-4 py-4 transition-all duration-300 md:px-6"
        style={{ marginLeft: collapsed ? 84 : 250 }}
      >
        <Topbar />
        {children}
      </main>
    </div>
  );
}
