import { useEffect, useState } from 'react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import AlertBanner from './AlertBanner';
import { useAuth } from '../context/AuthContext';

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const { session } = useAuth();

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
        className="min-h-screen px-3 py-3 transition-all duration-300 md:px-5"
        style={{ marginLeft: collapsed ? 84 : 250 }}
      >
        <Navbar />
        <div className="mb-3">
          <AlertBanner
            level="warning"
            title="Air-gapped Offline Mode Enabled"
            description={`All detections, model inference, and playbook generation are running inside the isolated banking network. Active role: ${session.role}.`}
          />
        </div>
        {children}
      </main>
    </div>
  );
}
