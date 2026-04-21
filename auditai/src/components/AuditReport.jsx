'use client';

import { ArrowLeft, Download, Share2, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function AuditReport({ anomaly, onBack }) {
  if (!anomaly) return null;

  return (
    <div className="max-w-7xl mx-auto h-full flex flex-col animate-fade-in">
      <div className="mb-6 flex items-center">
        <button onClick={onBack} className="flex items-center text-sm font-medium dark:text-slate-400 text-slate-500 hover:text-neon-green transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Risk Feed
        </button>
      </div>
      <div className="flex flex-col lg:flex-row gap-6 flex-1 h-[calc(100vh-120px)]">
        <div className="w-full lg:w-[40%] flex flex-col space-y-6 overflow-y-auto pr-2 pb-10">
          <div className="glass-panel rounded-2xl p-6 pop-out">
            <h2 className="text-xl font-bold dark:text-white text-slate-900 mb-5">Transaction Details</h2>
            <div className="space-y-4">
              {[
                ['Transaction ID', <span className="font-mono">{anomaly.id}</span>],
                ['Amount', <span className="font-bold dark:text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.3)]">{anomaly.amount}</span>],
                ['Vendor', anomaly.vendor],
                ['Department', anomaly.department],
                ['Employee', anomaly.employee],
                ['Submitted at', anomaly.timestamp],
                ['Category', anomaly.category],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between border-b dark:border-slate-800 border-slate-200 pb-3">
                  <span className="text-sm dark:text-slate-400 text-slate-500">{label}</span>
                  <span className="text-sm font-medium dark:text-white text-slate-900">{value}</span>
                </div>
              ))}
              <div className="flex justify-between pb-1">
                <span className="text-sm dark:text-slate-400 text-slate-500">Anomaly Score</span>
                <span className="text-sm font-bold dark:text-white text-slate-800 bg-slate-200 dark:bg-slate-800 px-2 py-0.5 rounded-md">{anomaly.anomalyScore}/100</span>
              </div>
            </div>
          </div>
          <div className="glass-panel rounded-2xl p-6 pop-out delay-100">
            <h2 className="text-xl font-bold dark:text-white text-slate-900 mb-5">Detection Evidence</h2>
            <ul className="space-y-3">
              {anomaly.evidence.map((item, idx) => (
                <li key={idx} className="flex items-start text-sm dark:text-slate-300 text-slate-700">
                  <span className="mr-3 text-neon-green mt-0.5 drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]">•</span>
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="w-full lg:w-[60%] glass-panel rounded-2xl flex flex-col h-full overflow-hidden pop-out delay-200">
          <div className="p-6 border-b dark:border-slate-800 border-slate-200 dark:bg-white/5 bg-slate-50/50 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className={`flex items-center px-3 py-1.5 rounded-lg border ${anomaly.riskLevel === 'HIGH' ? 'bg-red-500/10 border-red-500/30 text-red-500' : anomaly.riskLevel === 'MEDIUM' ? 'bg-amber-500/10 border-amber-500/30 text-amber-500' : 'bg-slate-500/10 border-slate-500/30 text-slate-400'}`}>
                <AlertTriangle className="w-4 h-4 mr-2" />
                <span className="text-xs font-bold tracking-wide uppercase">Risk: {anomaly.riskLevel}</span>
              </div>
              <div className={`flex items-center px-3 py-1.5 rounded-lg border ${anomaly.riskLevel === 'HIGH' ? 'bg-red-500/10 border-red-500/30 text-red-500' : 'bg-neon-green/10 border-neon-green/30 text-neon-green'}`}>
                <ShieldCheck className="w-4 h-4 mr-2" />
                <span className="text-xs font-bold tracking-wide uppercase">
                  Action: {anomaly.riskLevel === 'HIGH' ? 'ESCALATE' : anomaly.riskLevel === 'MEDIUM' ? 'REVIEW' : 'DISMISS'}
                </span>
              </div>
            </div>
          </div>
          <div className="p-8 flex-1 overflow-y-auto">
            <h1 className="text-2xl font-serif dark:text-white text-slate-900 mb-6 font-semibold">Audit Narrative Report</h1>
            <p className="font-serif text-[1.05rem] leading-loose dark:text-slate-300 text-slate-800">{anomaly.narrative}</p>
          </div>
          <div className="p-6 border-t dark:border-slate-800 border-slate-200 dark:bg-white/5 bg-slate-50 flex items-center justify-end space-x-3">
            <button className="flex items-center px-4 py-2 text-sm font-bold dark:text-slate-300 text-slate-700 bg-transparent border dark:border-slate-600 border-slate-300 rounded-lg dark:hover:bg-slate-800 hover:bg-slate-100 transition-colors shadow-sm">
              <Share2 className="w-4 h-4 mr-2 dark:text-slate-400 text-slate-500" />Share with team
            </button>
            <button className="flex items-center px-4 py-2 text-sm font-bold text-app-dark bg-neon-green border border-transparent rounded-lg hover:bg-green-400 transition-colors shadow-[0_0_15px_rgba(57,255,20,0.4)]">
              <Download className="w-4 h-4 mr-2" />Export as PDF
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
