'use client';

import { useState } from 'react';
import { ShieldAlert, LayoutDashboard, TrendingUp, Moon, Sun, Settings, FileText } from 'lucide-react';
import SettingsDrawer from '@/components/SettingsDrawer';

const NavLink = ({ id, label, icon: Icon, isActive, onClick }) => (
  <button
    onClick={() => onClick(id)}
    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
      isActive
        ? 'bg-white/20 text-white border border-white/25 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]'
        : 'text-white/60 hover:bg-white/10 hover:text-white'
    }`}
  >
    <Icon className={`w-4 h-4 ${isActive ? 'text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.6)]' : 'text-white/60'}`} />
    {label}
  </button>
);

export default function Navbar({ currentView, setCurrentView, isDarkMode, toggleDarkMode }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const displayName = 'Analyst';
  const displayEmail = 'local-session';

  const navItems = [
    { id: 'risk-feed', label: 'Risk Feed', icon: LayoutDashboard },
    { id: 'spend-trend', label: 'Spend Trend', icon: TrendingUp },
    { id: 'daily-summary', label: 'Daily Summary', icon: FileText },
  ];

  return (
    <>
      {/* Floating navbar outer padding */}
      <div className="px-4 pt-4 pb-0 flex-shrink-0 z-40">
        <div
          className="rounded-2xl px-5 py-3 flex items-center justify-between transition-colors duration-300"
          style={{
            background: isDarkMode ? '#001960' : '#4169E1',
            boxShadow: isDarkMode
              ? '0 4px 24px rgba(0,25,96,0.7), inset 0 1px 0 rgba(255,255,255,0.06)'
              : '0 4px 24px rgba(65,105,225,0.45), inset 0 1px 0 rgba(255,255,255,0.2)',
            border: isDarkMode ? '1px solid rgba(255,255,255,0.06)' : '1px solid rgba(255,255,255,0.25)',
          }}
        >
          {/* Left: Logo */}
          <div className="flex items-center gap-3">
            <ShieldAlert className="text-green-300 w-7 h-7 flex-shrink-0 drop-shadow-[0_0_8px_rgba(57,255,20,0.5)]" />
            <span className="text-xl font-bold tracking-tight text-white">AuditAI</span>
          </div>

          {/* Center: Nav Links */}
          <nav className="flex items-center gap-1">
            {navItems.map(item => (
              <NavLink
                key={item.id}
                {...item}
                isActive={currentView === item.id || (currentView === 'audit-report-detail' && item.id === 'risk-feed')}
                onClick={setCurrentView}
              />
            ))}
          </nav>

          {/* Right: User chip + Settings + Theme toggle */}
          <div className="flex items-center gap-2">

            {/* Theme Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-xl bg-blue-950/10 hover:bg-white/20 border border-white/15 transition-colors"
              title="Toggle Theme"
            >
              {isDarkMode
                ? <Sun className="w-4 h-4 text-amber-300 drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]" />
                : <Moon className="w-4 h-4 text-fuchsia-300" />
              }
            </button>

            {/* Settings */}
            <button
              onClick={() => setSettingsOpen(true)}
              className="p-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 transition-colors"
              title="Settings"
            >
              <Settings className="w-4 h-4 text-white/70 hover:text-white transition-colors" />
            </button>

            {/* User card */}
            <div
              className="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl cursor-pointer transition-all duration-200 hover:brightness-110 active:scale-95"
              style={{
                background: isDarkMode ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.22)',
                border: '1.5px solid rgba(255,255,255,0.3)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2), 0 2px 8px rgba(0,0,0,0.15)',
              }}
            >
              <div className="w-7 h-7 rounded-full border border-white/40 bg-white/10 text-white text-xs font-bold flex items-center justify-center">
                A
              </div>
              <div className="leading-tight">
                <p className="text-xs font-semibold text-white leading-tight">{displayName}</p>
                {displayEmail && (
                  <p className="text-[9px] text-white/60 leading-tight truncate max-w-[110px]">{displayEmail}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <SettingsDrawer isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
