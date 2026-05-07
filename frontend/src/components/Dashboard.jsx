'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import RiskFeed from '@/components/RiskFeed';
import AuditReport from '@/components/AuditReport';
import SpendTrend from '@/components/SpendTrend';
import SpendTrendPanel from '@/components/SpendTrendPanel';
import ChatbotPanel from '@/components/ChatbotPanel';
import DailySummary from '@/components/DailySummary';
import { useAlerts } from '@/lib/useAlerts';

const VIEW_TO_PATH = {
  'risk-feed': '/risk-feed',
  'spend-trend': '/spend-trend',
  'daily-summary': '/daily-summary',
};

export default function Dashboard({ initialView = 'risk-feed' }) {
  const router = useRouter();
  const [currentView, setCurrentView] = useState(initialView);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [spendPanelExpanded, setSpendPanelExpanded] = useState(true);

  // ── Live data from backend ────────────────────────────────────────────────
  const { alerts, spendTrend, metrics, connected, loading, error, refresh } = useAlerts();

  useEffect(() => {
    if (isDarkMode) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [isDarkMode]);

  useEffect(() => {
    setCurrentView(initialView);
  }, [initialView]);

  const handleViewReport = (anomaly) => {
    setSelectedAnomaly(anomaly);
    setCurrentView('audit-report-detail');
  };

  const handleBackToFeed = () => {
    setSelectedAnomaly(null);
    setCurrentView('risk-feed');
  };

  const handleSetView = (view) => {
    if (view !== 'audit-report-detail') setSelectedAnomaly(null);
    setCurrentView(view);
    if (VIEW_TO_PATH[view]) {
      router.push(VIEW_TO_PATH[view]);
    }
  };

  const isSplitView = currentView === 'risk-feed';

  const renderFullContent = () => {
    switch (currentView) {
      case 'audit-report-detail':
        return <AuditReport anomaly={selectedAnomaly} onBack={handleBackToFeed} />;
      case 'spend-trend':
        return <SpendTrend spendTrend={spendTrend} alerts={alerts} />;
      case 'daily-summary':
        return <DailySummary />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-screen font-sans overflow-hidden bg-slate-50 dark:bg-app-dark text-slate-900 dark:text-slate-200 transition-colors duration-300">

      {/* Floating Navbar */}
      <Navbar
        currentView={currentView}
        setCurrentView={handleSetView}
        isDarkMode={isDarkMode}
        toggleDarkMode={() => setIsDarkMode(d => !d)}
        connected={connected}
      />

      {/* Backend error banner */}
      {error && (
        <div className="mx-4 mt-2 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400 flex items-center justify-between">
          <span>⚠ {error}</span>
          <button onClick={refresh} className="underline hover:text-red-300 transition-colors">Retry</button>
        </div>
      )}

      {/* Page body */}
      <div className="flex-1 overflow-hidden pt-3 pb-4 px-4">
        {isSplitView ? (
          /* Split layout: 65% Risk Feed | 35% Right Panel */
          <div className="flex gap-4 h-full">

            {/* Left panel — Risk Feed */}
            <div className="flex-[65] overflow-y-auto px-3 py-1">
              <RiskFeed
                alerts={alerts}
                metrics={metrics}
                loading={loading}
                connected={connected}
                onViewReport={handleViewReport}
              />
            </div>

            {/* Right panel — Spend trend + chatbot */}
            <div className="flex-[35] flex flex-col overflow-hidden relative">
              <div className="flex-1 overflow-y-auto space-y-3 py-1 pr-1 min-h-0">
                <SpendTrendPanel
                  isExpanded={spendPanelExpanded}
                  setIsExpanded={setSpendPanelExpanded}
                  onViewLarger={() => handleSetView('spend-trend')}
                  spendTrend={spendTrend}
                  alerts={alerts}
                />
              </div>

              {/* Chatbot panel */}
              <ChatbotPanel />
            </div>

          </div>
        ) : (
          /* Full-width views */
          <div className="h-full overflow-y-auto px-3">
            {renderFullContent()}
          </div>
        )}
      </div>
    </div>
  );
}
