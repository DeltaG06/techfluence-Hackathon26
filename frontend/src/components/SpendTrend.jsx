'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot, ScatterChart, Scatter, ReferenceLine } from 'recharts';
import { Calendar, Activity } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-app-panel border border-slate-200 dark:border-app-border p-3 rounded-lg shadow-xl">
        <p className="dark:text-slate-400 text-slate-500 text-xs mb-1">{label}</p>
        <p className="dark:text-white text-slate-900 font-bold flex items-center">
          <span className="w-2 h-2 rounded-full dark:bg-neon-green bg-indigo-500 mr-2"></span>
          ₹{Number(data.spend || 0).toLocaleString('en-IN')}
        </p>
        {data.isAnomaly && (
          <p className="text-red-500 text-xs font-bold mt-2 bg-red-500/10 inline-block px-2 py-0.5 rounded border border-red-500/20">
            Anomaly Detected
          </p>
        )}
      </div>
    );
  }
  return null;
};

const ScatterTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="bg-white dark:bg-app-panel border border-slate-200 dark:border-app-border p-3 rounded-lg shadow-xl text-xs">
        <p className="dark:text-slate-400 text-slate-500 mb-1">{d.date}</p>
        <p className="dark:text-white text-slate-900 font-bold">₹{Number(d.spend || 0).toLocaleString('en-IN')}</p>
        <span className={`inline-block mt-1.5 px-2 py-0.5 rounded font-bold text-[10px] border ${
          d.isAnomaly
            ? 'bg-red-500/15 text-red-400 border-red-500/30'
            : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
        }`}>
          {d.isAnomaly ? '⚠ Anomaly' : '✓ Normal'}
        </span>
      </div>
    );
  }
  return null;
};

function CustomDot({ cx, cy, isAnomaly }) {
  if (cx === undefined || cy === undefined) return null;
  const color = isAnomaly ? '#f87171' : '#34d399';
  const glowColor = isAnomaly ? 'rgba(248,113,113,0.6)' : 'rgba(52,211,153,0.5)';
  const r = isAnomaly ? 7 : 5;
  return (
    <g>
      <circle cx={cx} cy={cy} r={r + 4} fill={glowColor} opacity={0.25} />
      <circle cx={cx} cy={cy} r={r} fill={color} stroke={isAnomaly ? '#991b1b' : '#065f46'} strokeWidth={1.5} />
      {isAnomaly && (
        <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fontSize={8} fill="white" fontWeight="bold">!</text>
      )}
    </g>
  );
}

export default function SpendTrend({ spendTrend = [], alerts = [] }) {
  const chartData = spendTrend.length > 0
    ? spendTrend
    : [{ date: 'No data', spend: 0, isAnomaly: false }];

  const anomalies = chartData.filter(d => d.isAnomaly);

  // Build the top anomalous days table from live alerts
  const topDays = [...alerts]
    .filter(a => a.riskLevel === 'HIGH' || a.riskLevel === 'CRITICAL')
    .sort((a, b) => (b.amountRaw ?? 0) - (a.amountRaw ?? 0))
    .slice(0, 8)
    .map(a => ({
      date: a.timestamp,
      amount: a.amount,
      riskLevel: a.riskLevel,
      vendor: a.vendor,
    }));

  // --- Scatter chart data ---
  const normalPoints = chartData.filter(d => !d.isAnomaly).map((d, i) => ({ ...d, idx: i }));
  const anomalyPoints = chartData.filter(d => d.isAnomaly).map((d, i) => ({ ...d, idx: normalPoints.length + i }));

  const spends = chartData.map(d => d.spend || 0);
  const mean = spends.length ? spends.reduce((a, b) => a + b, 0) / spends.length : 0;
  const stddev = spends.length
    ? Math.sqrt(spends.reduce((a, b) => a + (b - mean) ** 2, 0) / spends.length)
    : 0;
  const threshold = Math.round(mean + 1.5 * stddev);
  const totalAnomalies = anomalyPoints.length;
  const totalNormal = normalPoints.length;
  const pct = chartData.length > 0 ? ((totalAnomalies / chartData.length) * 100).toFixed(1) : '0.0';

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold dark:text-white text-slate-900 tracking-tight">Spend Trend Analysis</h1>
          <p className="text-sm dark:text-slate-400 text-slate-500 mt-1">Live spend with anomaly markers — powered by real-time ML detection.</p>
        </div>
      </div>

      {/* ── Chart 1: Line Chart ────────────────────────────────────────────── */}
      <div className="glass-panel rounded-2xl p-6 pop-out mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold dark:text-white text-slate-900">Daily Expenditure</h2>
          <div className="flex items-center space-x-2 text-sm dark:text-neon-green text-indigo-600 bg-indigo-50 dark:bg-neon-green/10 px-3 py-1.5 rounded-lg font-medium border border-indigo-100 dark:border-neon-green/20">
            <Calendar className="w-4 h-4" />
            <span>Live Data</span>
          </div>
        </div>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={0}>
            <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} tickMargin={10} minTickGap={30} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `₹${v / 1000}k`} tickMargin={10} />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#39ff14', strokeWidth: 1, strokeDasharray: '4 4', opacity: 0.5 }} />
              <Line type="monotone" dataKey="spend" stroke="#39ff14" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#03001C', stroke: '#39ff14', strokeWidth: 3 }} style={{ filter: 'drop-shadow(0px 4px 6px rgba(57,255,20,0.4))' }} />
              {anomalies.map((entry, index) => (
                <ReferenceDot key={`anomaly-${index}`} x={entry.date} y={entry.spend} r={6} fill="#ef4444" stroke="#111111" strokeWidth={3} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Chart 2: Anomaly vs Normal Scatter ────────────────────────────── */}
      <div className="glass-panel rounded-2xl p-6 pop-out mb-8 delay-75">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-bold dark:text-white text-slate-900">Anomaly vs Normal Distribution</h2>
            </div>
            <p className="text-xs dark:text-slate-400 text-slate-500">
              Each point is a transaction period. Red = flagged anomaly, Green = normal spend. Dashed line is the detection threshold (μ + 1.5σ).
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
              <span className="text-xs font-semibold text-emerald-400">{totalNormal} Normal</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-red-500/10 border border-red-500/20">
              <span className="w-2.5 h-2.5 rounded-full bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.8)]" />
              <span className="text-xs font-semibold text-red-400">{totalAnomalies} Anomalies</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <span className="text-xs font-bold text-amber-400">{pct}% flagged</span>
            </div>
          </div>
        </div>

        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={0}>
            <ScatterChart margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
              <XAxis
                dataKey="idx"
                type="number"
                name="Index"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickMargin={8}
                label={{ value: 'Transaction Period', position: 'insideBottom', offset: -8, fill: '#475569', fontSize: 11 }}
              />
              <YAxis
                dataKey="spend"
                type="number"
                name="Spend"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#64748b', fontSize: 11 }}
                tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                tickMargin={8}
                width={52}
              />
              <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: '4 4', stroke: '#475569' }} />

              {threshold > 0 && (
                <ReferenceLine
                  y={threshold}
                  stroke="#f59e0b"
                  strokeDasharray="6 3"
                  strokeWidth={1.5}
                  label={{ value: `Threshold ₹${(threshold / 1000).toFixed(0)}k`, position: 'insideTopRight', fill: '#f59e0b', fontSize: 10, fontWeight: 700 }}
                />
              )}

              <Scatter
                name="Normal"
                data={normalPoints}
                shape={(props) => <CustomDot {...props} isAnomaly={false} />}
              />

              <Scatter
                name="Anomaly"
                data={anomalyPoints}
                shape={(props) => <CustomDot {...props} isAnomaly={true} />}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="flex items-center gap-6 mt-4 pt-4 border-t dark:border-white/5 border-slate-100 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]" />
            <span className="text-xs dark:text-slate-400 text-slate-500">Normal transaction</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.7)]" />
            <span className="text-xs dark:text-slate-400 text-slate-500">Anomalous transaction</span>
          </div>
          <div className="flex items-center gap-2">
            <svg width="24" height="8"><line x1="0" y1="4" x2="24" y2="4" stroke="#f59e0b" strokeDasharray="5 2" strokeWidth="2" /></svg>
            <span className="text-xs dark:text-slate-400 text-slate-500">Detection threshold (μ + 1.5σ)</span>
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden pop-out delay-100">
        <div className="px-6 py-5 border-b dark:border-slate-800 border-slate-200 flex items-center justify-between dark:bg-white/5 bg-slate-50/50">
          <h2 className="text-lg font-bold dark:text-white text-slate-900">Top High-Risk Alerts</h2>
          <span className="text-xs font-semibold dark:text-neon-green text-green-700 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse" />
            Live
          </span>
        </div>
        <div className="overflow-x-auto">
          {topDays.length === 0 ? (
            <div className="px-6 py-8 text-center text-sm dark:text-slate-500 text-slate-400">
              No high-risk alerts yet. Simulator is running — data will appear shortly.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr>
                  {['Timestamp', 'Amount', 'Vendor', 'Risk Level'].map(h => (
                    <th key={h} className="px-6 py-4 border-b dark:border-slate-800 border-slate-200 dark:bg-app-dark bg-white text-xs font-bold dark:text-slate-400 text-slate-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="dark:divide-slate-800 divide-slate-100 divide-y">
                {topDays.map((day, idx) => (
                  <tr key={idx} className="dark:hover:bg-white/5 hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium dark:text-white text-slate-900">{day.date}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm dark:text-neon-green text-green-700 font-mono font-bold">{day.amount}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm dark:text-slate-300 text-slate-600">{day.vendor}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${
                        day.riskLevel === 'CRITICAL' || day.riskLevel === 'HIGH'
                          ? 'bg-red-500/10 text-red-500 border-red-500/30'
                          : day.riskLevel === 'MEDIUM'
                          ? 'bg-amber-500/10 text-amber-500 border-amber-500/30'
                          : 'bg-slate-500/10 text-slate-400 border-slate-500/30'
                      }`}>
                        {day.riskLevel}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
