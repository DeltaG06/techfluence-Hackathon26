'use client';

import { useState } from 'react';
import { spendTrendData, topAnomalousDays } from '@/lib/mockData';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts';
import { Calendar, ChevronDown, Filter } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white dark:bg-app-panel border border-slate-200 dark:border-app-border p-3 rounded-lg shadow-xl">
        <p className="dark:text-slate-400 text-slate-500 text-xs mb-1">{label}</p>
        <p className="dark:text-white text-slate-900 font-bold flex items-center">
          <span className="w-2 h-2 rounded-full dark:bg-neon-green bg-indigo-500 mr-2"></span>
          ${data.spend.toLocaleString()}
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

export default function SpendTrend() {
  const [department, setDepartment] = useState('All Departments');
  const departments = ['All Departments', 'Engineering', 'Sales', 'Marketing', 'Executive', 'Operations'];
  const anomalies = spendTrendData.filter(d => d.isAnomaly);

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold dark:text-white text-slate-900 tracking-tight">Spend Trend Analysis</h1>
          <p className="text-sm dark:text-slate-400 text-slate-500 mt-1">30-day historical spend with anomaly markers.</p>
        </div>
        <div className="relative">
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="appearance-none bg-white dark:bg-app-panel border border-slate-300 dark:border-app-border dark:text-white text-slate-700 py-2.5 pl-4 pr-10 rounded-xl shadow-sm text-sm font-medium focus:outline-none focus:ring-1 focus:ring-neon-green cursor-pointer transition-colors"
          >
            {departments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 dark:text-slate-400 text-slate-500">
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-2xl p-6 pop-out mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold dark:text-white text-slate-900">Daily Expenditure</h2>
          <div className="flex items-center space-x-2 text-sm dark:text-neon-green text-indigo-600 bg-indigo-50 dark:bg-neon-green/10 px-3 py-1.5 rounded-lg font-medium border border-indigo-100 dark:border-neon-green/20">
            <Calendar className="w-4 h-4" />
            <span>Last 30 Days</span>
          </div>
        </div>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={spendTrendData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3} />
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} tickMargin={10} minTickGap={30} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={(v) => `$${v / 1000}k`} tickMargin={10} />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#39ff14', strokeWidth: 1, strokeDasharray: '4 4', opacity: 0.5 }} />
              <Line type="monotone" dataKey="spend" stroke="#39ff14" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#03001C', stroke: '#39ff14', strokeWidth: 3 }} style={{ filter: 'drop-shadow(0px 4px 6px rgba(57,255,20,0.4))' }} />
              {anomalies.map((entry, index) => (
                <ReferenceDot key={`anomaly-${index}`} x={entry.date} y={entry.spend} r={6} fill="#ef4444" stroke="#111111" strokeWidth={3} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden pop-out delay-100">
        <div className="px-6 py-5 border-b dark:border-slate-800 border-slate-200 flex items-center justify-between dark:bg-white/5 bg-slate-50/50">
          <h2 className="text-lg font-bold dark:text-white text-slate-900">Top Anomalous Days</h2>
          <button className="text-sm font-bold dark:text-neon-green text-indigo-600 flex items-center bg-transparent">
            <Filter className="w-4 h-4 mr-1.5" />Filter
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                {['Date', 'Total Spend', 'Risk Severity'].map(h => (
                  <th key={h} className="px-6 py-4 border-b dark:border-slate-800 border-slate-200 dark:bg-app-dark bg-white text-xs font-bold dark:text-slate-400 text-slate-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="dark:divide-slate-800 divide-slate-100 divide-y">
              {topAnomalousDays.map((day, idx) => (
                <tr key={idx} className="dark:hover:bg-white/5 hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium dark:text-white text-slate-900">{day.date}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm dark:text-slate-300 text-slate-600 font-mono">{day.amount}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${day.riskLevel === 'HIGH' ? 'bg-red-500/10 text-red-500 border-red-500/30' : day.riskLevel === 'MEDIUM' ? 'bg-amber-500/10 text-amber-500 border-amber-500/30' : 'bg-slate-500/10 text-slate-400 border-slate-500/30'}`}>
                      {day.riskLevel}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
