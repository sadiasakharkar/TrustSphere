import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { apiRequest } from '../../services/api/apiClient';
import StatusIndicator from './StatusIndicator';

export default function SocTopbar({ onMenu }) {
  const { session, logout } = useAuth();
  const router = useRouter();
  const roleLabel = session.role === 'admin' ? 'Admin' : session.role === 'employee' ? 'Employee' : 'Analyst';
  const [now, setNow] = useState('');
  const [modeStatus, setModeStatus] = useState({
    pipeline: 'ready',
    pipelineMode: 'HYBRID_MODE',
    backendConnected: false,
    modelActive: false,
    fallbackMode: true,
  });

  useEffect(() => {
    const formatNow = () => {
      const formatter = new Intl.DateTimeFormat('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: 'short'
      });
      setNow(formatter.format(new Date()));
    };
    formatNow();
    const timer = window.setInterval(formatNow, 30000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let active = true;
    const loadStatus = async () => {
      try {
        const response = await apiRequest('/system/health');
        if (!active) return;
        setModeStatus({
          pipeline: response.data?.pipeline || 'degraded',
          pipelineMode: response.data?.pipeline_mode || 'HYBRID_MODE',
          backendConnected: true,
          modelActive: Boolean(response.data?.ml_runtime || response.data?.ollama),
          fallbackMode: Boolean(response.data?.fallback_mode),
        });
      } catch {
        if (active) {
          setModeStatus({
            pipeline: 'degraded',
            pipelineMode: 'SIMULATION_MODE',
            backendConnected: false,
            modelActive: false,
            fallbackMode: true,
          });
        }
      }
    };
    loadStatus();
    const timer = window.setInterval(loadStatus, 10000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <header className="soc-topbar">
      <div className="flex flex-1 items-center gap-3">
        <button className="soc-btn-ghost lg:hidden" onClick={onMenu} aria-label="Open navigation">
          <span className="material-symbols-outlined">menu</span>
        </button>
        <div className="relative w-full max-w-[360px]">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[rgba(193,198,215,0.5)]">search</span>
          <input className="soc-input pl-10" placeholder="Search alerts or incidents" />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden rounded-full border border-[rgba(65,71,85,0.55)] bg-[rgba(28,32,38,0.9)] px-3 py-2 text-xs font-medium text-[rgba(223,226,235,0.72)] xl:inline-flex">
          Live {now}
        </div>
        <div className="hidden items-center gap-3 rounded-full border border-[rgba(65,71,85,0.55)] bg-[rgba(28,32,38,0.9)] px-3 py-2 xl:flex">
          <StatusIndicator
            status={modeStatus.backendConnected ? 'System ready' : 'Offline mode'}
            pulse={!modeStatus.backendConnected}
          />
        </div>
        <button className="soc-btn-secondary hidden sm:inline-flex" onClick={() => router.push(session.role === 'admin' ? '/settings' : '/overview')}>
          <span className="material-symbols-outlined">manage_accounts</span>
          {roleLabel}
        </button>
        <button
          className="soc-btn-ghost"
          onClick={() => {
            logout();
            router.push('/login');
          }}
          aria-label="Logout"
        >
          <span className="material-symbols-outlined">logout</span>
        </button>
      </div>
    </header>
  );
}
