'use client';

import { X, User, Bell, Shield, Palette, Globe, Key } from 'lucide-react';
import { useEffect } from 'react';

const SettingRow = ({ icon: Icon, label, description, children }) => (
  <div className="flex items-center justify-between py-3 border-b dark:border-white/5 border-slate-100 last:border-0">
    <div className="flex items-center gap-3">
      <div className="p-2 rounded-lg bg-slate-100 dark:bg-white/5">
        <Icon className="w-4 h-4 text-neon-green" />
      </div>
      <div>
        <p className="text-sm font-medium dark:text-white text-slate-900">{label}</p>
        {description && <p className="text-xs dark:text-slate-400 text-slate-500 mt-0.5">{description}</p>}
      </div>
    </div>
    {children}
  </div>
);

const Toggle = ({ defaultChecked = false }) => (
  <label className="relative inline-flex items-center cursor-pointer">
    <input type="checkbox" defaultChecked={defaultChecked} className="sr-only peer" />
    <div className="w-9 h-5 bg-slate-200 dark:bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:bg-neon-green/80 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4 transition-colors" />
  </label>
);

export default function SettingsDrawer({ isOpen, onClose }) {
  useEffect(() => {
    if (isOpen) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-50 bg-black/40 backdrop-blur-sm transition-opacity duration-300 ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-sm z-50 transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="h-full glass-panel flex flex-col rounded-l-2xl overflow-hidden">

          {/* Header */}
          <div className="px-6 py-5 border-b dark:border-white/5 border-slate-200 flex items-center justify-between flex-shrink-0">
            <div>
              <h2 className="text-lg font-bold dark:text-white text-slate-900">Settings</h2>
              <p className="text-xs dark:text-slate-400 text-slate-500 mt-0.5">Manage your preferences</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl dark:bg-white/5 bg-slate-100 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4 dark:text-slate-400 text-slate-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">

            {/* Profile Card */}
            <div className="glass-panel rounded-xl p-5">
              <p className="text-xs font-bold uppercase tracking-wider dark:text-slate-500 text-slate-400 mb-3">Profile</p>
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-full bg-slate-100 dark:bg-slate-800 border-2 border-neon-green/40 flex items-center justify-center flex-shrink-0">
                  <User className="w-7 h-7 dark:text-slate-300 text-slate-500" />
                </div>
                <div>
                  <p className="font-semibold dark:text-white text-slate-900">Janardan</p>
                  <p className="text-xs text-neon-green font-medium">Risk Analyst</p>
                  <p className="text-xs dark:text-slate-400 text-slate-500 mt-0.5">janardan@auditai.com</p>
                </div>
              </div>
              <button className="w-full text-sm font-semibold py-2 rounded-lg border dark:border-white/10 border-slate-200 dark:text-slate-300 text-slate-600 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                Edit Profile
              </button>
            </div>

            {/* Notifications Card */}
            <div className="glass-panel rounded-xl p-5">
              <p className="text-xs font-bold uppercase tracking-wider dark:text-slate-500 text-slate-400 mb-1">Notifications</p>
              <SettingRow icon={Bell} label="High Risk Alerts" description="Get notified for HIGH risk anomalies">
                <Toggle defaultChecked={true} />
              </SettingRow>
              <SettingRow icon={Bell} label="Daily Digest" description="Summary email every morning">
                <Toggle defaultChecked={false} />
              </SettingRow>
            </div>

            {/* Appearance Card */}
            <div className="glass-panel rounded-xl p-5">
              <p className="text-xs font-bold uppercase tracking-wider dark:text-slate-500 text-slate-400 mb-1">Appearance</p>
              <SettingRow icon={Palette} label="Compact Mode" description="Reduce card padding and spacing">
                <Toggle />
              </SettingRow>
              <SettingRow icon={Globe} label="Language" description="Interface language">
                <select className="text-xs dark:bg-slate-800 bg-slate-100 dark:text-slate-300 text-slate-700 border dark:border-slate-700 border-slate-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-neon-green">
                  <option>English</option>
                  <option>Hindi</option>
                </select>
              </SettingRow>
            </div>

            {/* Security Card */}
            <div className="glass-panel rounded-xl p-5">
              <p className="text-xs font-bold uppercase tracking-wider dark:text-slate-500 text-slate-400 mb-1">Security</p>
              <SettingRow icon={Shield} label="Two-Factor Auth" description="Extra layer of login security">
                <Toggle defaultChecked={true} />
              </SettingRow>
              <SettingRow icon={Key} label="Change Password" description="Last changed 30 days ago">
                <button className="text-xs font-bold text-neon-green hover:opacity-80 transition-opacity">Update</button>
              </SettingRow>
            </div>
          </div>

          {/* Footer */}
          <div className="p-5 border-t dark:border-white/5 border-slate-200 flex-shrink-0">
            <button className="w-full py-2.5 rounded-xl text-sm font-bold bg-neon-green text-app-dark hover:opacity-90 transition-opacity shadow-[0_0_15px_rgba(57,255,20,0.3)]">
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
