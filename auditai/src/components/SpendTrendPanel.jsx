'use client';

import { useState } from 'react';
import { spendTrendData, topAnomalousDays } from '@/lib/mockData';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts';
import { ChevronDown, ChevronUp, TrendingUp, AlertTriangle, Maximize2, X, ExternalLink } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-app-panel border border-slate-200 dark:border-app-border p-2.5 rounded-lg shadow-xl text-xs">
        <p className="dark:text-slate-400 text-slate-500 mb-1">{label}</p>
        <p className="dark:text-white text-slate-900 font-bold">${data.spend.toLocaleString()}</p>
        {data.isAnomaly && <p className="text-red-500 font-bold mt-1">⚠ Anomaly</p>}
      </div>
    );
  }
  return null;
};

export default function SpendTrendPanel({ isExpanded, setIsExpanded, onViewLarger }) {
  const [modalOpen, setModalOpen] = useState(false);
  const anomalies = spendTrendData.filter(d => d.isAnomaly);
  const topDays = topAnomalousDays.slice(0, 3);

  return (
    <>
      {/* Compact Chart Panel */}
      <div className="glass-panel rounded-2xl overflow-hidden">
        {/* Panel Header */}
        <div className="px-4 py-3 flex items-center justify-between border-b dark:border-white/5 border-slate-200 dark:bg-white/5 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]" />
            <h3 className="text-sm font-bold dark:text-white text-slate-900">Spend Trend</h3>
          </div>
          <div className="flex items-center gap-1.5">
            {/* Expand to dialog */}
            <button
              onClick={() => setModalOpen(true)}
              className="p-1.5 rounded-lg dark:bg-white/5 bg-slate-100 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
              title="Expand chart"
            >
              <Maximize2 className="w-3.5 h-3.5 dark:text-slate-400 text-slate-500" />
            </button>
            {/* Collapse toggle */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 rounded-lg dark:bg-white/5 bg-slate-100 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded
                ? <ChevronUp className="w-3.5 h-3.5 dark:text-slate-400 text-slate-500" />
                : <ChevronDown className="w-3.5 h-3.5 dark:text-slate-400 text-slate-500" />
              }
            </button>
          </div>
        </div>

        {/* Collapsible chart body */}
        <div
          className="transition-all duration-400 ease-in-out overflow-hidden"
          style={{ maxHeight: isExpanded ? '260px' : '0px', opacity: isExpanded ? 1 : 0 }}
        >
          <div className="p-4">
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={spendTrendData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} tickMargin={6} minTickGap={40} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={(v) => `$${v / 1000}k`} tickMargin={4} width={38} />
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#39ff14', strokeWidth: 1, strokeDasharray: '4 4', opacity: 0.5 }} />
                  <Line type="monotone" dataKey="spend" stroke="#39ff14" strokeWidth={2.5} dot={false} activeDot={{ r: 5, fill: '#03001C', stroke: '#39ff14', strokeWidth: 2 }} style={{ filter: 'drop-shadow(0px 3px 5px rgba(57,255,20,0.35))' }} />
                  {anomalies.map((entry, i) => (
                    <ReferenceDot key={i} x={entry.date} y={entry.spend} r={5} fill="#ef4444" stroke="#111" strokeWidth={2} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Top Anomalous Days Panel */}
      <div className="glass-panel rounded-2xl overflow-hidden">
        <div className="px-4 py-3 flex items-center justify-between border-b dark:border-white/5 border-slate-200 dark:bg-white/5 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <h3 className="text-sm font-bold dark:text-white text-slate-900">Top Anomalous Days</h3>
          </div>
          <span className="text-[10px] font-semibold dark:text-slate-500 text-slate-400 uppercase tracking-wider">Last 30d</span>
        </div>
        <div className="divide-y dark:divide-white/5 divide-slate-100">
          {topDays.map((day, idx) => (
            <div key={idx} className="px-4 py-3 flex items-center justify-between hover:dark:bg-white/5 hover:bg-slate-50 transition-colors">
              <div>
                <p className="text-xs font-medium dark:text-white text-slate-900">{day.date}</p>
                <p className="text-xs dark:text-slate-400 text-slate-500 font-mono mt-0.5">{day.amount}</p>
              </div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                day.riskLevel === 'HIGH' ? 'bg-red-500/10 text-red-500 border-red-500/30' :
                day.riskLevel === 'MEDIUM' ? 'bg-amber-500/10 text-amber-500 border-amber-500/30' :
                'bg-slate-500/10 dark:text-slate-400 text-slate-500 border-slate-500/30'
              }`}>
                {day.riskLevel}
              </span>
            </div>
          ))}
        </div>
        <div className="px-4 py-2.5 border-t dark:border-white/5 border-slate-100">
          <button
            onClick={onViewLarger}
            className="text-[11px] font-semibold text-neon-green hover:opacity-80 transition-opacity w-full text-center"
          >
            View full Spend Trend →
          </button>
        </div>
      </div>

      {/* ─── Expanded Chart Modal ─── */}
      {modalOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm animate-fade-in"
            onClick={() => setModalOpen(false)}
          />
          {/* Dialog */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 pointer-events-none">
            <div className="w-full max-w-2xl glass-panel rounded-2xl flex flex-col overflow-hidden pointer-events-auto animate-pop-in shadow-2xl">
              {/* Modal Header */}
              <div className="px-6 py-4 border-b dark:border-white/5 border-slate-200 flex items-center justify-between dark:bg-white/5 bg-slate-50/50">
                <div className="flex items-center gap-2.5">
                  <TrendingUp className="w-5 h-5 text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]" />
                  <div>
                    <h2 className="text-base font-bold dark:text-white text-slate-900">Spend Trend Analysis</h2>
                    <p className="text-xs dark:text-slate-400 text-slate-500">30-day historical spend with anomaly markers</p>
                  </div>
                </div>
                <button
                  onClick={() => setModalOpen(false)}
                  className="p-2 rounded-xl dark:bg-white/5 bg-slate-100 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
                >
                  <X className="w-4 h-4 dark:text-slate-400 text-slate-500" />
                </button>
              </div>

              {/* Modal Chart */}
              <div className="p-6">
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={spendTrendData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
                      <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 11 }} tickMargin={8} minTickGap={35} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} tickMargin={8} width={42} />
                      <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#39ff14', strokeWidth: 1, strokeDasharray: '4 4', opacity: 0.5 }} />
                      <Line type="monotone" dataKey="spend" stroke="#39ff14" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#03001C', stroke: '#39ff14', strokeWidth: 3 }} style={{ filter: 'drop-shadow(0px 4px 6px rgba(57,255,20,0.4))' }} />
                      {anomalies.map((entry, i) => (
                        <ReferenceDot key={i} x={entry.date} y={entry.spend} r={6} fill="#ef4444" stroke="#111" strokeWidth={3} />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="px-6 pb-5 flex items-center justify-between">
                <p className="text-xs dark:text-slate-400 text-slate-500">
                  <span className="inline-flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />Red dots indicate anomalous spending days</span>
                </p>
                <button
                  onClick={() => { setModalOpen(false); onViewLarger(); }}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-app-dark bg-neon-green rounded-xl hover:opacity-90 transition-opacity shadow-[0_0_12px_rgba(57,255,20,0.35)]"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Larger
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
