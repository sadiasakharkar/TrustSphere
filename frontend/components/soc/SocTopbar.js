import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import NotificationCenter from './NotificationCenter';
import StatusIndicator from './StatusIndicator';

export default function SocTopbar({ onTogglePalette, onToggleInsights, notifications = [] }) {
  const { session, logout } = useAuth();
  const [openNotifications, setOpenNotifications] = useState(false);
  const router = useRouter();

  return (
    <header className="soc-topbar">
      <div className="flex flex-1 items-center gap-4">
        <div className="relative w-full max-w-md">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[rgba(193,198,215,0.5)]">search</span>
          <input className="soc-input pl-10" placeholder="Search incidents, entities, chains, or reports" />
        </div>
        <button className="soc-btn-secondary hidden md:inline-flex" onClick={onTogglePalette}>
          <span className="material-symbols-outlined text-base">keyboard_command_key</span>
          Command palette
        </button>
      </div>

      <div className="relative flex items-center gap-3">
        <div className="hidden items-center gap-3 rounded-full border border-[rgba(65,71,85,0.55)] bg-[rgba(28,32,38,0.9)] px-3 py-2 md:flex">
          <StatusIndicator status="Ollama Ready" pulse />
          <div className="h-4 w-px bg-[rgba(65,71,85,0.55)]" />
          <StatusIndicator status="Queue Nominal" />
        </div>
        <button className="soc-btn-ghost relative" onClick={() => setOpenNotifications((value) => !value)} aria-label="Open notifications">
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute -right-0.5 -top-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-[#ff5451] px-1 text-[9px] font-bold text-white">{notifications.length}</span>
        </button>
        <button className="soc-btn-ghost" onClick={onToggleInsights} aria-label="Toggle insight drawer">
          <span className="material-symbols-outlined">right_panel_open</span>
        </button>
        <button className="soc-btn-secondary" onClick={() => session.role === 'Admin' ? router.push('/administration') : router.push('/reports')}>
          <span className="material-symbols-outlined">admin_panel_settings</span>
          <span className="hidden lg:inline">{session.role}</span>
        </button>
        <button
          className="soc-btn-ghost"
          onClick={() => {
            logout();
            router.push('/login');
          }}
        >
          <span className="material-symbols-outlined">logout</span>
        </button>
        <NotificationCenter open={openNotifications} onClose={() => setOpenNotifications(false)} items={notifications} />
      </div>
    </header>
  );
}
