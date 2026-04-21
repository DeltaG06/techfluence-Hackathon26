'use client';

import { anomalies } from '@/lib/mockData';
import { AlertCircle, ShieldAlert, Activity, CheckCircle2, FileSearch } from 'lucide-react';

const RiskBadge = ({ level }) => {
  const styles = {
    HIGH: 'bg-red-500/10 text-red-500 border-red-500/30',
    MEDIUM: 'bg-amber-500/10 text-amber-500 border-amber-500/30',
    LOW: 'bg-slate-500/10 text-slate-500 border-slate-500/30 dark:text-slate-400 dark:border-slate-600'
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[level]}`}>
      {level}
    </span>
  );
};

export default function RiskFeed({ onViewReport }) {
  const metrics = [
    { label: 'Flagged Today', value: '24', icon: AlertCircle, color: 'text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]', bg: 'bg-neon-green/10' },
    { label: 'High Risk', value: '5', icon: ShieldAlert, color: 'text-red-500', bg: 'bg-red-500/10' },
    { label: 'Avg Anomaly Score', value: '68%', icon: Activity, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { label: 'Auto-Dismissed', value: '142', icon: CheckCircle2, color: 'text-slate-500 dark:text-slate-400', bg: 'bg-slate-500/10' },
  ];

  return (
    <div>
      <div className="mb-6 animate-fade-in">
        <h1 className="text-2xl font-bold tracking-tight dark:text-white text-slate-900">Risk Feed</h1>
        <p className="text-sm dark:text-slate-400 text-slate-500 mt-1">Real-time detection of anomalous financial activities.</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {metrics.map((metric, i) => {
          const Icon = metric.icon;
          return (
            <div key={i} className={`glass-panel rounded-xl p-4 pop-out animate-slide-up delay-${(i + 1) * 100}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium dark:text-slate-400 text-slate-500">{metric.label}</p>
                  <p className="text-xl font-bold dark:text-white text-slate-900 mt-1">{metric.value}</p>
                </div>
                <div className={`p-2.5 rounded-xl ${metric.bg}`}>
                  <Icon className={`w-5 h-5 ${metric.color}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <h2 className="text-base font-semibold mb-3 dark:text-white text-slate-900">Recent Transaction Analysis</h2>

      {/* Anomaly List */}
      <div className="space-y-3">
        {anomalies.map((anomaly, index) => (
          <div
            key={anomaly.id}
            className={`glass-panel rounded-xl p-4 neon-border animate-slide-up delay-${Math.min((index + 1) * 100, 500)}`}
          >
            {/* Top row: badge + amount/vendor | explanation */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-3">
              {/* Left: amount block */}
              <div className="sm:w-1/3 sm:border-r dark:border-slate-800 border-slate-200 sm:pr-4 flex flex-col gap-1 flex-shrink-0">
                <RiskBadge level={anomaly.riskLevel} />
                <div className="text-xl font-bold dark:text-white text-slate-900 tracking-tight">{anomaly.amount}</div>
                <div className="text-xs dark:text-slate-400 text-slate-500 truncate">{anomaly.vendor}</div>
              </div>

              {/* Right: explanation */}
              <div className="flex-1 flex flex-col gap-2 justify-center">
                <p className="dark:text-slate-300 text-slate-700 text-sm leading-snug">{anomaly.explanation}</p>
                {/* Check Audit Report CTA */}
                <button
                  onClick={() => onViewReport(anomaly)}
                  className="self-start flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-neon-green bg-neon-green/10 hover:bg-neon-green/20 rounded-lg transition-colors border border-neon-green/20 mt-1 group"
                >
                  <FileSearch className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                  Check Audit Report
                </button>
              </div>
            </div>

            {/* Bottom row: meta + score bar + quick actions */}
            <div className="mt-3 pt-3 border-t dark:border-slate-800 border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between text-xs dark:text-slate-400 text-slate-500 gap-2">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-blue-500" />{anomaly.department}</span>
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-purple-500" />{anomaly.employee}</span>
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-slate-500" />{anomaly.timestamp}</span>
              </div>
              <div className="flex items-center gap-3">
                {/* Score bar */}
                <div className="flex items-center gap-2 min-w-[120px]">
                  <span className="font-medium whitespace-nowrap">Score: <span className="dark:text-white text-slate-900">{anomaly.anomalyScore}</span></span>
                  <div className="flex-1 h-1.5 dark:bg-slate-800 bg-slate-200 rounded-full overflow-hidden shadow-inner">
                    <div
                      className={`h-full rounded-full ${anomaly.riskLevel === 'HIGH' ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.7)]' : anomaly.riskLevel === 'MEDIUM' ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.7)]' : 'bg-slate-400'}`}
                      style={{ width: `${anomaly.anomalyScore}%` }}
                    />
                  </div>
                </div>
                {/* Quick actions */}
                <div className="flex gap-1.5">
                  <button className="px-2.5 py-1 text-[10px] font-bold text-red-500 bg-red-500/10 hover:bg-red-500/20 rounded-md transition-colors border border-red-500/20">Escalate</button>
                  <button className="px-2.5 py-1 text-[10px] font-bold dark:text-slate-400 text-slate-600 bg-slate-500/10 hover:bg-slate-500/20 rounded-md transition-colors border border-slate-500/20">Dismiss</button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
