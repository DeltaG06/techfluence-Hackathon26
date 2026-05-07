'use client';

import { useMemo, useState } from 'react';
import { AlertCircle, ShieldAlert, Activity, CheckCircle2, FileSearch, WifiOff, RefreshCw, ChevronUp, ChevronDown } from 'lucide-react';
import { escalateAlert, dismissAlert } from '@/lib/api';

const RiskBadge = ({ level }) => {
  const styles = {
    HIGH:     'bg-red-500/10 text-red-500 border-red-500/30',
    CRITICAL: 'bg-red-600/10 text-red-600 border-red-600/30',
    MEDIUM:   'bg-amber-500/10 text-amber-500 border-amber-500/30',
    LOW:      'bg-slate-500/10 text-slate-500 border-slate-500/30 dark:text-slate-400 dark:border-slate-600',
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[level] ?? styles.LOW}`}>
      {level}
    </span>
  );
};

const ScoreBar = ({ score, riskLevel }) => (
  <div className="flex items-center gap-2 min-w-[120px]">
    <span className="font-medium whitespace-nowrap text-xs">
      Score: <span className="dark:text-white text-slate-900">{score}</span>
    </span>
    <div className="flex-1 h-1.5 dark:bg-slate-800 bg-slate-200 rounded-full overflow-hidden shadow-inner">
      <div
        className={`h-full rounded-full transition-all duration-700 ${
          riskLevel === 'HIGH' || riskLevel === 'CRITICAL'
            ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.7)]'
            : riskLevel === 'MEDIUM'
            ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.7)]'
            : 'bg-slate-400'
        }`}
        style={{ width: `${score}%` }}
      />
    </div>
  </div>
);

// Individual alert card with its own escalate/dismiss state
function AlertCard({ alert, onViewReport }) {
  const [status, setStatus] = useState('active'); // active | escalated | dismissed | loading
  const [expanded, setExpanded] = useState(false);

  const handleEscalate = async () => {
    setStatus('loading');
    await escalateAlert(alert.alert_id ?? alert.id);
    setStatus('escalated');
  };

  const handleDismiss = async () => {
    setStatus('loading');
    await dismissAlert(alert.alert_id ?? alert.id);
    setStatus('dismissed');
  };

  if (status === 'dismissed') {
    return (
      <div className="glass-panel rounded-xl p-3 opacity-40 flex items-center gap-3 text-xs dark:text-slate-500 text-slate-400 line-through">
        <CheckCircle2 className="w-4 h-4 text-slate-400 flex-shrink-0" />
        <span>Dismissed: {alert.amount} — {alert.vendor}</span>
      </div>
    );
  }

  return (
    <div className={`glass-panel rounded-xl p-4 transition-all duration-300 ${
      status === 'escalated' ? 'border border-red-500/40 shadow-[0_0_16px_rgba(239,68,68,0.15)]' : 'neon-border'
    }`}>
      {/* Escalated banner */}
      {status === 'escalated' && (
        <div className="mb-3 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-500 font-semibold flex items-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5" /> Escalated to Compliance Team
        </div>
      )}

      {/* Top row */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-3">
        {/* Left: amount block */}
        <div className="sm:w-1/3 sm:border-r dark:border-slate-800 border-slate-200 sm:pr-4 flex flex-col gap-1 flex-shrink-0">
          <RiskBadge level={alert.riskLevel} />
          <div className="text-xl font-bold dark:text-white text-slate-900 tracking-tight">{alert.amount}</div>
          <div className="text-xs dark:text-slate-400 text-slate-500 truncate">{alert.vendor}</div>
        </div>

        {/* Right: explanation */}
        <div className="flex-1 flex flex-col gap-2 justify-center">
          <p className={`dark:text-slate-300 text-slate-700 text-sm leading-snug ${expanded ? '' : 'line-clamp-2'}`}>
            {alert.explanation}
          </p>
          {alert.explanation?.length > 120 && (
            <button onClick={() => setExpanded(!expanded)} className="self-start flex items-center gap-1 text-[10px] dark:text-slate-500 text-slate-400 hover:text-neon-green">
              {expanded ? <><ChevronUp className="w-3 h-3" /> Less</> : <><ChevronDown className="w-3 h-3" /> More</>}
            </button>
          )}
          <button
            onClick={() => onViewReport(alert)}
            className="self-start flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-neon-green bg-neon-green/10 hover:bg-neon-green/20 rounded-lg transition-colors border border-neon-green/20 mt-1 group"
          >
            <FileSearch className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
            Check Audit Report
          </button>
        </div>
      </div>

      {/* Bottom row */}
      <div className="mt-3 pt-3 border-t dark:border-slate-800 border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between text-xs dark:text-slate-400 text-slate-500 gap-2">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-blue-500" />{alert.department}</span>
          <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-purple-500" />{alert.employee}</span>
          <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-slate-500" />{alert.timestamp}</span>
        </div>
        <div className="flex items-center gap-3">
          <ScoreBar score={alert.anomalyScore} riskLevel={alert.riskLevel} />
          <div className="flex gap-1.5">
            <button
              onClick={handleEscalate}
              disabled={status !== 'active'}
              className="px-2.5 py-1 text-[10px] font-bold text-red-500 bg-red-500/10 hover:bg-red-500/20 active:scale-95 rounded-md transition-all border border-red-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === 'loading' ? '…' : status === 'escalated' ? '✓ Escalated' : 'Escalate'}
            </button>
            <button
              onClick={handleDismiss}
              disabled={status !== 'active'}
              className="px-2.5 py-1 text-[10px] font-bold dark:text-slate-400 text-slate-600 bg-slate-500/10 hover:bg-slate-500/20 active:scale-95 rounded-md transition-all border border-slate-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === 'loading' ? '…' : 'Dismiss'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RiskFeed({ alerts = [], metrics = {}, loading = false, connected = false, onViewReport }) {
  /** null = show all; otherwise filter the list to match the clicked metric */
  const [activeFilter, setActiveFilter] = useState(null);

  const displayAlerts = useMemo(() => {
    const todayDateString = new Date().toDateString();

    const timeMs = (a) => {
      try {
        const t = a.timestampRaw ?? a.timestamp;
        if (!t) return 0;
        const ms = new Date(t).getTime();
        return Number.isNaN(ms) ? 0 : ms;
      } catch {
        return 0;
      }
    };

    /** Newest transactions first */
    const sortByTimeDesc = (arr) =>
      [...arr].sort((x, y) => timeMs(y) - timeMs(x));

    /** Highest anomaly score first, then amount */
    const sortByScoreDesc = (arr) =>
      [...arr].sort((x, y) => {
        const ds = (y.anomalyScore ?? 0) - (x.anomalyScore ?? 0);
        if (ds !== 0) return ds;
        return (y.amountRaw ?? 0) - (x.amountRaw ?? 0);
      });

    const isFlaggedToday = (a) => {
      try {
        const t = a.timestampRaw ?? a.timestamp;
        if (!t) return false;
        return new Date(t).toDateString() === todayDateString;
      } catch {
        return false;
      }
    };

    const isHighRisk = (a) => a.riskLevel === 'HIGH' || a.riskLevel === 'CRITICAL';

    if (activeFilter === 'today') {
      return sortByTimeDesc(alerts.filter(isFlaggedToday));
    }
    if (activeFilter === 'high') {
      return sortByScoreDesc(alerts.filter(isHighRisk));
    }
    if (activeFilter === 'score' && metrics.avgScore != null) {
      const target = Number(metrics.avgScore) || 0;
      return [...alerts].sort((x, y) => {
        const dx = Math.abs((x.anomalyScore ?? 0) - target);
        const dy = Math.abs((y.anomalyScore ?? 0) - target);
        if (dx !== dy) return dx - dy;
        return (y.anomalyScore ?? 0) - (x.anomalyScore ?? 0);
      });
    }
    if (activeFilter === 'all') {
      return sortByTimeDesc(alerts);
    }
    return sortByTimeDesc(alerts);
  }, [alerts, activeFilter, metrics.avgScore]);

  const filterTitle = {
    today: "Today's flagged transactions (newest first)",
    high: 'High / critical risk (highest score first)',
    score: 'Closest to average score, then highest score',
    all: 'All alerts (newest first)',
  };

  const toggleFilter = (key) => {
    if (key === 'all') {
      setActiveFilter(null);
      return;
    }
    setActiveFilter((prev) => (prev === key ? null : key));
  };

  const metricCards = [
    { key: 'today', label: 'Flagged Today',     value: loading ? '…' : String(metrics.flaggedToday ?? 0), icon: AlertCircle,  color: 'text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]', bg: 'bg-neon-green/10' },
    { key: 'high',  label: 'High Risk',         value: loading ? '…' : String(metrics.highRisk ?? 0),     icon: ShieldAlert,  color: 'text-red-500',                                               bg: 'bg-red-500/10' },
    { key: 'score', label: 'Avg Anomaly Score', value: loading ? '…' : `${metrics.avgScore ?? 0}%`,        icon: Activity,     color: 'text-blue-500',                                              bg: 'bg-blue-500/10' },
    { key: 'all',   label: 'Total Alerts',      value: loading ? '…' : String(metrics.total ?? 0),         icon: CheckCircle2, color: 'text-slate-500 dark:text-slate-400',                         bg: 'bg-slate-500/10' },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6 animate-fade-in flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight dark:text-white text-slate-900">Risk Feed</h1>
          <p className="text-sm dark:text-slate-400 text-slate-500 mt-1">Real-time detection of anomalous financial activities.</p>
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ${
          connected
            ? 'bg-neon-green/10 border-neon-green/30 text-neon-green'
            : 'bg-slate-500/10 border-slate-500/30 dark:text-slate-400 text-slate-500'
        }`}>
          {connected
            ? <><span className="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse" /> LIVE</>
            : <><WifiOff className="w-3 h-3" /> Polling</>}
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {metricCards.map((metric) => {
          const Icon = metric.icon;
          const isOn = metric.key === 'all' ? activeFilter === null : activeFilter === metric.key;
          return (
            <button
              type="button"
              key={metric.key}
              onClick={() => toggleFilter(metric.key)}
              title="Click to filter the list below. Click again to show all."
              className={`glass-panel rounded-xl p-4 pop-out text-left w-full transition-all cursor-pointer ${
                isOn
                  ? 'ring-2 ring-neon-green/50 border border-neon-green/30'
                  : 'hover:border-neon-green/20 border border-transparent'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium dark:text-slate-400 text-slate-500">{metric.label}</p>
                  <p className="text-xl font-bold dark:text-white text-slate-900 mt-1">{metric.value}</p>
                </div>
                <div className={`p-2.5 rounded-xl ${metric.bg}`}>
                  <Icon className={`w-5 h-5 ${metric.color}`} />
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {activeFilter && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 glass-panel rounded-xl px-3 py-2 text-xs">
          <p className="text-neon-green font-semibold">
            Showing: {filterTitle[activeFilter]} <span className="text-slate-500 font-normal">({displayAlerts.length} items)</span>
          </p>
          <button
            type="button"
            onClick={() => setActiveFilter(null)}
            className="px-2 py-1 rounded-lg border border-slate-500/30 text-slate-400 hover:text-white hover:border-neon-green/30"
          >
            Clear filter
          </button>
        </div>
      )}

      <h2 className="text-base font-semibold mb-3 dark:text-white text-slate-900">Recent Transaction Analysis</h2>

      {/* Loading skeleton */}
      {loading && alerts.length === 0 && (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-panel rounded-xl p-4 animate-pulse">
              <div className="flex gap-4">
                <div className="w-1/3 space-y-2">
                  <div className="h-4 bg-slate-700/50 rounded-full w-16" />
                  <div className="h-6 bg-slate-700/50 rounded w-24" />
                  <div className="h-3 bg-slate-700/50 rounded w-32" />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-slate-700/50 rounded w-full" />
                  <div className="h-3 bg-slate-700/50 rounded w-3/4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && alerts.length === 0 && (
        <div className="glass-panel rounded-xl p-8 text-center">
          <RefreshCw className="w-8 h-8 mx-auto mb-3 dark:text-slate-500 text-slate-400 animate-spin" />
          <p className="dark:text-slate-400 text-slate-500 text-sm">Waiting for live alerts…</p>
          <p className="dark:text-slate-500 text-slate-400 text-xs mt-1">
            Simulator is running — alerts will appear here shortly.
          </p>
        </div>
      )}

      {!loading && alerts.length > 0 && activeFilter && displayAlerts.length === 0 && (
        <div className="glass-panel rounded-xl p-6 text-center text-sm text-slate-400 mb-3">
          No transactions match this filter.
        </div>
      )}

      {/* Alert List */}
      <div className="space-y-3">
        {displayAlerts.map((alert) => (
          <AlertCard
            key={alert.alert_id ?? alert.id}
            alert={alert}
            onViewReport={onViewReport}
          />
        ))}
      </div>
    </div>
  );
}
