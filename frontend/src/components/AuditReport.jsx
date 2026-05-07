'use client';

import { useState } from 'react';
import {
  ArrowLeft, AlertTriangle, ShieldCheck, Download,
  Share2, Sparkles, Loader2, User, Building2, Tag,
  Calendar, Hash, CreditCard, TrendingUp, CheckCircle
} from 'lucide-react';
import { downloadReport } from '@/lib/api';

const BASE = 'http://localhost:8000';

// ─── Risk colours ─────────────────────────────────────────────────────────────
function riskStyle(level) {
  if (level === 'HIGH' || level === 'CRITICAL')
    return { badge: 'bg-red-500/10 border-red-500/30 text-red-500', bar: 'bg-red-500', glow: 'shadow-[0_0_12px_rgba(239,68,68,0.5)]' };
  if (level === 'MEDIUM')
    return { badge: 'bg-amber-500/10 border-amber-500/30 text-amber-500', bar: 'bg-amber-500', glow: '' };
  return { badge: 'bg-neon-green/10 border-neon-green/30 text-neon-green', bar: 'bg-neon-green', glow: '' };
}

function actionStyle(action) {
  if (action === 'BLOCK') return 'bg-red-500/10 border-red-500/30 text-red-500';
  if (action === 'REVIEW') return 'bg-amber-500/10 border-amber-500/30 text-amber-500';
  return 'bg-neon-green/10 border-neon-green/30 text-neon-green';
}

// ─── Stat chip ────────────────────────────────────────────────────────────────
function StatRow({ icon: Icon, label, value, mono = false, accent = false }) {
  return (
    <div className="flex items-center justify-between py-3.5 border-b dark:border-slate-800/80 border-slate-100 last:border-0 group">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg dark:bg-white/5 bg-slate-100 flex items-center justify-center flex-shrink-0">
          <Icon className="w-3.5 h-3.5 dark:text-slate-400 text-slate-500" />
        </div>
        <span className="text-sm dark:text-slate-400 text-slate-500">{label}</span>
      </div>
      <span className={`text-sm font-semibold ${mono ? 'font-mono text-xs' : ''} ${accent ? 'dark:text-neon-green text-green-600 drop-shadow-[0_0_6px_rgba(57,255,20,0.35)]' : 'dark:text-white text-slate-900'}`}>
        {value}
      </span>
    </div>
  );
}

// ─── Score ring ───────────────────────────────────────────────────────────────
function ScoreRing({ score, riskLevel }) {
  const rs = riskStyle(riskLevel);
  const r = 28, circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`relative w-20 h-20 rounded-full ${rs.glow}`}>
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 72 72">
          <circle cx="36" cy="36" r={r} fill="none" stroke="currentColor" strokeWidth="6" className="dark:text-slate-800 text-slate-200" />
          <circle
            cx="36" cy="36" r={r} fill="none" strokeWidth="6"
            strokeDasharray={circ} strokeDashoffset={offset}
            strokeLinecap="round"
            className={`${rs.bar} transition-all duration-700`}
            style={{ stroke: riskLevel === 'HIGH' || riskLevel === 'CRITICAL' ? '#ef4444' : riskLevel === 'MEDIUM' ? '#f59e0b' : '#39ff14' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-black dark:text-white text-slate-900">{score}</span>
        </div>
      </div>
      <span className="text-[10px] font-semibold dark:text-slate-400 text-slate-500 uppercase tracking-wider">Anomaly Score</span>
    </div>
  );
}

// ─── Share button ─────────────────────────────────────────────────────────────
function ShareButton({ anomaly, report }) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const text = [
      `AuditAI Alert: ${anomaly.riskLevel} risk`,
      `Amount: ${anomaly.amount} | Vendor: ${anomaly.vendor}`,
      `Score: ${anomaly.anomalyScore}/100 | Action: ${anomaly.recommended_action}`,
      report ? `\nSummary: ${report.slice(0, 200)}…` : '',
    ].join('\n');

    if (navigator.share) {
      await navigator.share({ title: `AuditAI Report — ${anomaly.alert_id}`, text });
    } else {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleShare}
      className="flex items-center px-3.5 py-2 text-xs font-bold dark:text-slate-300 text-slate-700 bg-transparent border dark:border-slate-600 border-slate-300 rounded-lg dark:hover:bg-slate-800 hover:bg-slate-100 active:scale-95 transition-all"
    >
      {copied
        ? <><CheckCircle className="w-3.5 h-3.5 mr-1.5 text-neon-green" />Copied!</>
        : <><Share2 className="w-3.5 h-3.5 mr-1.5 dark:text-slate-400 text-slate-500" />Share</>
      }
    </button>
  );
}

// ─── AI Report panel ──────────────────────────────────────────────────────────
function AIReportPanel({ anomaly }) {
  const [status, setStatus] = useState('idle'); // idle | loading | done | error
  const [report, setReport] = useState('');
  const [showRaw, setShowRaw] = useState(false);

  const generateReport = async () => {
    setStatus('loading');
    try {
      // First try the analyze endpoint with the txn_id
      const txnId = anomaly.txn_id ?? anomaly.id;
      const res = await fetch(`${BASE}/api/analyze/${encodeURIComponent(txnId)}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setReport(data.explanation ?? data.narrative ?? anomaly.narrative ?? 'No report generated.');
        setStatus('done');
        return;
      }
    } catch {}

    // Fallback: use the narrative embedded in the alert itself
    const fallback = anomaly.narrative;
    if (fallback && fallback !== 'No narrative generated for this transaction.') {
      setReport(fallback);
      setStatus('done');
    } else {
      setStatus('error');
    }
  };

  const rs = riskStyle(anomaly.riskLevel);

  if (status === 'idle') {
    return (
      <div className="glass-panel rounded-2xl p-10 flex flex-col items-center justify-center gap-5 h-full min-h-[320px] border border-dashed dark:border-slate-700 border-slate-300 animate-fade-in">
        <div className="w-16 h-16 rounded-2xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center">
          <Sparkles className="w-7 h-7 text-neon-green drop-shadow-[0_0_8px_rgba(57,255,20,0.6)]" />
        </div>
        <div className="text-center max-w-xs">
          <h3 className="text-lg font-bold dark:text-white text-slate-900 mb-2">Generate AI Audit Report</h3>
          <p className="text-sm dark:text-slate-400 text-slate-500 leading-relaxed">
            AuditAI will write a full narrative report on this transaction — what happened, why it's suspicious, and what to do.
          </p>
        </div>
        <button
          onClick={generateReport}
          className="flex items-center gap-2 px-6 py-3 font-bold text-sm text-app-dark bg-neon-green rounded-xl hover:opacity-90 active:scale-95 transition-all shadow-[0_0_18px_rgba(57,255,20,0.4)]"
        >
          <Sparkles className="w-4 h-4" />
          Generate AI Report
        </button>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className="glass-panel rounded-2xl p-10 flex flex-col items-center justify-center gap-4 h-full min-h-[320px] animate-fade-in">
        <Loader2 className="w-10 h-10 text-neon-green animate-spin drop-shadow-[0_0_8px_rgba(57,255,20,0.6)]" />
        <div className="text-center">
          <p className="text-sm font-semibold dark:text-white text-slate-900">Analysing transaction…</p>
          <p className="text-xs dark:text-slate-400 text-slate-500 mt-1">Cross-referencing patterns, policies and ML signals</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="glass-panel rounded-2xl p-10 flex flex-col items-center justify-center gap-4 h-full min-h-[320px] animate-fade-in">
        <AlertTriangle className="w-10 h-10 text-red-500" />
        <div className="text-center">
          <p className="text-sm font-semibold dark:text-white text-slate-900">Report unavailable</p>
          <p className="text-xs dark:text-slate-400 text-slate-500 mt-1">Backend might be offline or OpenRouter key is not configured.</p>
        </div>
        <button onClick={() => setStatus('idle')} className="text-xs text-neon-green hover:underline">Try again</button>
      </div>
    );
  }

  // done — render the report
  const lines = report.split('\n').filter(Boolean);
  return (
    <div className="glass-panel rounded-2xl flex flex-col h-full overflow-hidden animate-fade-in shadow-lg">
      {/* Header */}
      <div className="px-8 py-5 border-b dark:border-slate-800 border-slate-200 dark:bg-white/5 bg-slate-50/50 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-neon-green drop-shadow-[0_0_6px_rgba(57,255,20,0.6)]" />
          <div>
            <h2 className="text-sm font-bold dark:text-white text-slate-900">AI Audit Narrative</h2>
            <p className="text-[11px] dark:text-slate-400 text-slate-500">Generated by AuditAI engine</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`flex items-center px-3 py-1.5 rounded-lg border text-xs font-bold ${rs.badge}`}>
            <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
            {anomaly.riskLevel}
          </div>
          <div className={`flex items-center px-3 py-1.5 rounded-lg border text-xs font-bold ${actionStyle(anomaly.recommended_action)}`}>
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
            {anomaly.recommended_action}
          </div>
        </div>
      </div>

      {/* Report body */}
      <div className="p-8 flex-1 overflow-y-auto">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {lines.map((line, i) => {
            if (/^(SUMMARY|RISK FACTORS|POLICY|EVIDENCE|RECOMMENDED)/.test(line.trim())) {
              return <h3 key={i} className="text-xs font-black uppercase tracking-widest dark:text-neon-green text-green-700 mt-6 mb-2 first:mt-0">{line.trim()}</h3>;
            }
            if (line.trim().startsWith('•') || line.trim().match(/^\d+\./)) {
              return <p key={i} className="text-sm dark:text-slate-300 text-slate-700 leading-relaxed mb-1 pl-2">{line.trim()}</p>;
            }
            return <p key={i} className="font-serif text-[1rem] dark:text-slate-200 text-slate-800 leading-loose mb-3">{line.trim()}</p>;
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="px-8 py-5 border-t dark:border-slate-800 border-slate-200 dark:bg-white/5 bg-slate-50 flex items-center justify-between">
        <button onClick={() => setStatus('idle')} className="text-xs dark:text-slate-400 text-slate-500 hover:text-neon-green transition-colors flex items-center gap-1">
          <Sparkles className="w-3 h-3" /> Regenerate
        </button>
        <div className="flex items-center gap-3">
          <ShareButton anomaly={anomaly} report={report} />
          <button
            onClick={() => downloadReport(anomaly, report)}
            className="flex items-center px-3.5 py-2 text-xs font-bold text-app-dark bg-neon-green rounded-lg hover:bg-green-400 active:scale-95 transition-all shadow-[0_0_12px_rgba(57,255,20,0.35)]"
          >
            <Download className="w-3.5 h-3.5 mr-1.5" />Export Report
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function AuditReport({ anomaly, onBack }) {
  if (!anomaly) return null;

  const rs = riskStyle(anomaly.riskLevel);

  return (
    <div className="max-w-7xl mx-auto h-full flex flex-col animate-fade-in">
      {/* Top bar */}
      <div className="mb-6 flex items-center justify-between">
        <button onClick={onBack} className="flex items-center text-sm font-medium dark:text-slate-400 text-slate-500 hover:text-neon-green transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Risk Feed
        </button>

        {/* Risk + Action badges */}
        <div className="flex items-center gap-2">
          <div className={`flex items-center px-3 py-1.5 rounded-lg border text-xs font-bold ${rs.badge}`}>
            <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
            Risk: {anomaly.riskLevel}
          </div>
          <div className={`flex items-center px-3 py-1.5 rounded-lg border text-xs font-bold ${actionStyle(anomaly.recommended_action)}`}>
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
            {anomaly.recommended_action}
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="flex flex-col lg:flex-row gap-6 flex-1 h-[calc(100vh-160px)]">

        {/* ── Left: Stats ── */}
        <div className="w-full lg:w-[42%] flex flex-col gap-5 overflow-y-auto pr-2 pb-10">

          {/* Score ring + amount hero */}
          <div className="glass-panel rounded-2xl p-6 pop-out flex items-center gap-6">
            <ScoreRing score={anomaly.anomalyScore} riskLevel={anomaly.riskLevel} />
            <div className="flex-1 min-w-0">
              <p className="text-xs dark:text-slate-400 text-slate-500 mb-1">Transaction Amount</p>
              <p className="text-3xl font-black dark:text-neon-green text-green-700 drop-shadow-[0_0_8px_rgba(57,255,20,0.4)] leading-none tracking-tight">{anomaly.amount}</p>
              <p className="text-xs dark:text-slate-500 text-slate-400 mt-2 font-mono truncate">{anomaly.alert_id ?? anomaly.id}</p>
            </div>
          </div>

          {/* Transaction stats */}
          <div className="glass-panel rounded-2xl p-6 pop-out delay-100">
            <h2 className="text-sm font-bold dark:text-white text-slate-900 mb-1 uppercase tracking-wider text-[11px] dark:text-slate-400 text-slate-500">Transaction Details</h2>
            <div>
              <StatRow icon={Hash}       label="Alert ID"        value={anomaly.alert_id ?? '—'}          mono />
              <StatRow icon={Hash}       label="Transaction ID"  value={anomaly.txn_id ?? anomaly.id}     mono />
              <StatRow icon={User}       label="Employee"        value={anomaly.employee}                  />
              <StatRow icon={Building2}  label="Department"      value={anomaly.department}                />
              <StatRow icon={CreditCard} label="Vendor"          value={anomaly.vendor}                    />
              <StatRow icon={Tag}        label="Category"        value={anomaly.category}                  />
              <StatRow icon={Calendar}   label="Submitted at"    value={anomaly.timestamp}                 />
              <StatRow icon={TrendingUp} label="Amount"          value={anomaly.amount}    accent          />
            </div>
          </div>

          {/* Evidence trail */}
          {(anomaly.evidence ?? []).length > 0 && (
            <div className="glass-panel rounded-2xl p-6 pop-out delay-150">
              <h2 className="text-[11px] font-bold dark:text-slate-400 text-slate-500 uppercase tracking-wider mb-3">Detection Evidence</h2>
              <ul className="space-y-2.5">
                {anomaly.evidence.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm dark:text-slate-300 text-slate-700">
                    <span className="mt-0.5 text-neon-green drop-shadow-[0_0_4px_rgba(57,255,20,0.5)] text-base leading-none flex-shrink-0">•</span>
                    <span className="leading-snug">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Pattern flags */}
          {anomaly.pattern_flags?.length > 0 && (
            <div className="glass-panel rounded-2xl p-6 pop-out delay-200">
              <h2 className="text-[11px] font-bold dark:text-slate-400 text-slate-500 uppercase tracking-wider mb-3">Pattern Flags</h2>
              <div className="space-y-3">
                {anomaly.pattern_flags.map((flag, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-red-500/5 border border-red-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-black text-red-400 uppercase tracking-widest">{flag.pattern_type}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 border border-red-500/30">{flag.severity}</span>
                    </div>
                    <p className="text-xs dark:text-slate-300 text-slate-600 leading-relaxed">{flag.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Right: AI Report ── */}
        <div className="w-full lg:w-[58%] flex flex-col h-full">
          <AIReportPanel anomaly={anomaly} />
        </div>

      </div>
    </div>
  );
}
