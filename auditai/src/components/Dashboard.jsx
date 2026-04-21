'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import RiskFeed from '@/components/RiskFeed';
import AuditReport from '@/components/AuditReport';
import SpendTrend from '@/components/SpendTrend';
import SpendTrendPanel from '@/components/SpendTrendPanel';
import ChatbotPanel from '@/components/ChatbotPanel';

export default function Dashboard() {
  const [currentView, setCurrentView] = useState('risk-feed');
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [spendPanelExpanded, setSpendPanelExpanded] = useState(true);

  useEffect(() => {
    if (isDarkMode) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [isDarkMode]);

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
  };

  const isSplitView = currentView === 'risk-feed';

  const renderFullContent = () => {
    switch (currentView) {
      case 'audit-report-detail':
        return <AuditReport anomaly={selectedAnomaly} onBack={handleBackToFeed} />;
      case 'spend-trend':
        return <SpendTrend />;
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
      />

      {/* Page body */}
      <div className="flex-1 overflow-hidden pt-3 pb-4 px-4">
        {isSplitView ? (
          /* Split layout: 65% Risk Feed | 35% Right Panel */
          <div className="flex gap-4 h-full">

            {/* Left panel — Risk Feed with more padding */}
            <div className="flex-[65] overflow-y-auto px-3 py-1">
              <RiskFeed onViewReport={handleViewReport} />
            </div>

            {/* Right panel — Spend trend + chatbot, column-aware, no overflow leak */}
            <div className="flex-[35] flex flex-col overflow-hidden relative">
              {/* Scrollable spend trend area - leaves room for chatbot pill */}
              <div className="flex-1 overflow-y-auto space-y-3 py-1 pr-1 min-h-0 ">
                <SpendTrendPanel
                  isExpanded={spendPanelExpanded}
                  setIsExpanded={setSpendPanelExpanded}
                  onViewLarger={() => handleSetView('spend-trend')}
                />
              </div>

              {/* Chatbot panel — pill + slide-up drawer, stays within right column */}
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
