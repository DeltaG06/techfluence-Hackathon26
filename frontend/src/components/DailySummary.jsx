'use client';

import { useEffect, useState } from 'react';
import { CalendarDays, Sparkles, Loader2, AlertTriangle, History, Trash2, Send, Bot, User } from 'lucide-react';
import { fetchPeriodSummary, sendChat } from '@/lib/api';

const RECENT_SUMMARIES_KEY = 'auditai.recentDailySummaries.v1';
const CHAT_HISTORY_KEY = 'auditai.chatHistory.v1';
const MAX_RECENT = 12;
const MAX_CHAT = 50;

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function renderSummary(summary) {
  const lines = String(summary ?? '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);

  return lines.map((line, idx) => {
    const clean = line.replace(/\*\*/g, '');

    if (/^(OVERVIEW|RISK SNAPSHOT|TOP CONCERNS|RECOMMENDED ACTIONS)\b/i.test(clean)) {
      return (
        <h3
          key={`h-${idx}`}
          className="text-xs font-black uppercase tracking-widest dark:text-neon-green text-green-700 mt-6 mb-2 first:mt-0"
        >
          {clean}
        </h3>
      );
    }

    if (/^[-•]\s*/.test(clean)) {
      return (
        <p key={`b-${idx}`} className="text-sm dark:text-slate-300 text-slate-700 leading-relaxed mb-1 pl-2">
          • {clean.replace(/^[-•]\s*/, '')}
        </p>
      );
    }

    if (/^\d+[\.)]\s*/.test(clean)) {
      return (
        <p key={`n-${idx}`} className="text-sm dark:text-slate-300 text-slate-700 leading-relaxed mb-1 pl-2">
          {clean}
        </p>
      );
    }

    return (
      <p key={`p-${idx}`} className="text-sm dark:text-slate-200 text-slate-800 leading-relaxed mb-2">
        {clean}
      </p>
    );
  });
}

export default function DailySummary() {
  const [date, setDate] = useState(todayIso());
  const [period, setPeriod] = useState('daily');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('chat');
  const [recentSummaries, setRecentSummaries] = useState([]);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hi, I'm AuditAI. Ask me anything about alerts, or generate a daily/weekly/monthly brief report.",
    },
  ]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(RECENT_SUMMARIES_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) setRecentSummaries(parsed);
    } catch {
      // Ignore malformed local storage content.
    }
  }, []);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(CHAT_HISTORY_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) setMessages(parsed);
    } catch {
      // Ignore malformed chat history.
    }
  }, []);

  const persistChat = (next) => {
    const slim = next.slice(-MAX_CHAT);
    setMessages(slim);
    try {
      localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(slim));
    } catch {
      // Ignore storage write issues.
    }
  };

  const persistRecents = (next) => {
    setRecentSummaries(next);
    try {
      localStorage.setItem(RECENT_SUMMARIES_KEY, JSON.stringify(next));
    } catch {
      // Ignore storage write issues.
    }
  };

  const generate = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchPeriodSummary(period, date);
      setResult(data);
      setActiveTab('generate');
      const entry = {
        id: `${Date.now()}-${data.period ?? period}-${data.date}`,
        savedAt: new Date().toISOString(),
        period: data.period ?? period,
        start_date: data.start_date ?? data.date,
        end_date: data.end_date ?? data.date,
        requested_date: data.requested_date,
        date: data.date,
        fallback_used: !!data.fallback_used,
        available_range: data.available_range ?? null,
        summary: data.summary,
        stats: data.stats,
      };
      const deduped = [
        entry,
        ...recentSummaries.filter((x) => !(x.requested_date === entry.requested_date && x.date === entry.date)),
      ].slice(0, MAX_RECENT);
      persistRecents(deduped);
      persistChat([
        ...messages,
        { role: 'user', text: `Generate ${data.period ?? period} brief for ${date}` },
        { role: 'assistant', text: data.summary },
      ]);
    } catch (e) {
      setResult(null);
      setError(e.message || 'Failed to generate summary.');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setLoading(true);
    setError('');
    const next = [...messages, { role: 'user', text: q }];
    persistChat(next);
    setInput('');
    try {
      const history = next.map((m) => ({ role: m.role, text: m.text }));
      const data = await sendChat(q, history);
      persistChat([...next, { role: 'assistant', text: data.answer }]);
    } catch (e) {
      setError(e.message || 'Failed to send message.');
    } finally {
      setLoading(false);
    }
  };

  const loadRecent = (item) => {
    setResult(item);
    setDate(item.requested_date ?? item.date);
    setPeriod(item.period ?? 'daily');
    setError('');
    setActiveTab('generate');
  };

  const clearRecent = () => {
    persistRecents([]);
  };

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-bold dark:text-white text-slate-900 tracking-tight">AuditAI Assistant</h1>
        <p className="text-sm dark:text-slate-400 text-slate-500 mt-1">
          Chat naturally, and generate daily/weekly/monthly brief reports.
        </p>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <button
          onClick={() => setActiveTab('chat')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold border transition-colors ${
            activeTab === 'chat'
              ? 'bg-neon-green/20 border-neon-green/30 text-neon-green'
              : 'dark:bg-white/5 bg-slate-50 dark:border-slate-800 border-slate-200 dark:text-slate-300 text-slate-600'
          }`}
        >
          Chat
        </button>
        <button
          onClick={() => setActiveTab('generate')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold border transition-colors ${
            activeTab === 'generate'
              ? 'bg-neon-green/20 border-neon-green/30 text-neon-green'
              : 'dark:bg-white/5 bg-slate-50 dark:border-slate-800 border-slate-200 dark:text-slate-300 text-slate-600'
          }`}
        >
          Generate
        </button>
        <button
          onClick={() => setActiveTab('recent')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold border transition-colors inline-flex items-center gap-1.5 ${
            activeTab === 'recent'
              ? 'bg-neon-green/20 border-neon-green/30 text-neon-green'
              : 'dark:bg-white/5 bg-slate-50 dark:border-slate-800 border-slate-200 dark:text-slate-300 text-slate-600'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Recent Summaries ({recentSummaries.length})
        </button>
      </div>

      {activeTab === 'recent' && (
        <div className="glass-panel rounded-2xl p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold dark:text-white text-slate-900">Recent Summaries</h2>
            <button
              onClick={clearRecent}
              disabled={recentSummaries.length === 0}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-red-500/30 text-red-500 bg-red-500/10 hover:bg-red-500/20 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </button>
          </div>
          {recentSummaries.length === 0 ? (
            <p className="text-sm dark:text-slate-400 text-slate-500">No saved summaries yet. Generate one and it will appear here.</p>
          ) : (
            <div className="space-y-2.5">
              {recentSummaries.map((item) => (
                <button
                  key={item.id}
                  onClick={() => loadRecent(item)}
                  className="w-full text-left rounded-xl border dark:border-slate-800 border-slate-200 p-3.5 dark:bg-white/5 bg-slate-50 hover:border-neon-green/30 transition-colors"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold dark:text-white text-slate-900">
                      {String(item.period ?? 'daily').toUpperCase()} • Requested {item.requested_date} {item.fallback_used ? `-> Used ${item.date}` : ''}
                    </p>
                    <p className="text-[11px] dark:text-slate-400 text-slate-500">
                      {new Date(item.savedAt).toLocaleString('en-IN')}
                    </p>
                  </div>
                  <p className="text-xs mt-1 dark:text-slate-400 text-slate-500">
                    Window: {item.start_date ?? item.date} to {item.end_date ?? item.date} •{' '}
                    Txns: {item?.stats?.total_transactions ?? 0} • Spend: ₹{Number(item?.stats?.total_spend ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'chat' && (
        <div className="glass-panel rounded-2xl overflow-hidden mb-6">
          <div className="p-4 space-y-3 max-h-[460px] overflow-y-auto">
            {messages.map((msg, i) => {
              const isBot = msg.role === 'assistant';
              return (
                <div key={i} className={`flex gap-2 ${isBot ? 'justify-start' : 'justify-end'}`}>
                  {isBot && (
                    <div className="w-7 h-7 rounded-full bg-neon-green/10 border border-neon-green/20 flex items-center justify-center mt-1">
                      <Bot className="w-4 h-4 text-neon-green" />
                    </div>
                  )}
                  <div className={`max-w-[82%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                    isBot
                      ? 'dark:bg-white/5 bg-slate-100 dark:text-slate-200 text-slate-800'
                      : 'bg-neon-green/20 border border-neon-green/20 text-neon-green'
                  }`}>
                    {isBot ? renderSummary(msg.text) : <p>{msg.text}</p>}
                  </div>
                  {!isBot && (
                    <div className="w-7 h-7 rounded-full bg-slate-500/20 border border-slate-500/30 flex items-center justify-center mt-1">
                      <User className="w-4 h-4 text-slate-300" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <div className="p-4 border-t dark:border-slate-800 border-slate-200">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(); }}
                placeholder="Ask about alerts, risks, actions, vendors..."
                className="flex-1 bg-white dark:bg-app-panel border border-slate-300 dark:border-app-border dark:text-white text-slate-700 py-2 px-3 rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-neon-green"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="h-10 px-3 rounded-xl bg-neon-green/20 border border-neon-green/30 text-neon-green text-sm font-bold hover:bg-neon-green/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Send
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'generate' && (
        <>
      <div className="glass-panel rounded-2xl p-5 mb-6">
        <div className="flex flex-col md:flex-row md:items-end gap-3">
          <div className="w-full md:w-52">
            <label className="text-xs font-semibold uppercase tracking-wider dark:text-slate-400 text-slate-500 block mb-2">
              Period
            </label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full bg-white dark:bg-app-panel border border-slate-300 dark:border-app-border dark:text-white text-slate-700 py-2.5 px-3 rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-neon-green"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="text-xs font-semibold uppercase tracking-wider dark:text-slate-400 text-slate-500 block mb-2">
              Select Date
            </label>
            <div className="relative">
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full appearance-none bg-white dark:bg-app-panel border border-slate-300 dark:border-app-border dark:text-white text-slate-700 py-2.5 pl-10 pr-3 rounded-xl shadow-sm text-sm font-medium focus:outline-none focus:ring-1 focus:ring-neon-green"
              />
              <CalendarDays className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 dark:text-slate-400 text-slate-500" />
            </div>
          </div>

          <button
            onClick={generate}
            disabled={!date || loading}
            className="h-10 px-4 rounded-xl bg-neon-green/20 border border-neon-green/30 text-neon-green text-sm font-bold hover:bg-neon-green/30 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Generate {period} Summary
          </button>
        </div>
      </div>

      {error && (
        <div className="glass-panel rounded-2xl p-5 border border-red-500/30 bg-red-500/5 mb-6">
          <p className="text-sm text-red-500 font-semibold inline-flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </p>
        </div>
      )}

      {result && (
        <div className="glass-panel rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b dark:border-slate-800 border-slate-200 dark:bg-white/5 bg-slate-50/50 flex items-center justify-between">
            <h2 className="text-base font-bold dark:text-white text-slate-900">
              {String(result.period ?? 'daily').toUpperCase()} Summary • {result.start_date ?? result.date} to {result.end_date ?? result.date}
            </h2>
            <span className="text-[11px] dark:text-slate-400 text-slate-500">AI generated</span>
          </div>
          <div className="p-6">
            {result.fallback_used && (
              <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-500">
                No transactions found for <span className="font-bold">{result.requested_date}</span>. Showing nearest available date{' '}
                <span className="font-bold">{result.date}</span> (available range: {result.available_range?.min} to {result.available_range?.max}).
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
              <div className="rounded-xl border dark:border-slate-800 border-slate-200 p-3">
                <p className="text-xs dark:text-slate-400 text-slate-500">Total Transactions</p>
                <p className="text-lg font-bold dark:text-white text-slate-900">{result?.stats?.total_transactions ?? 0}</p>
              </div>
              <div className="rounded-xl border dark:border-slate-800 border-slate-200 p-3">
                <p className="text-xs dark:text-slate-400 text-slate-500">Total Spend</p>
                <p className="text-lg font-bold dark:text-white text-slate-900">
                  ₹{Number(result?.stats?.total_spend ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="rounded-xl border dark:border-slate-800 border-slate-200 p-3">
                <p className="text-xs dark:text-slate-400 text-slate-500">Risk Counts</p>
                <p className="text-sm font-semibold dark:text-white text-slate-900">{JSON.stringify(result?.stats?.risk_counts ?? {})}</p>
              </div>
            </div>

            <div className="rounded-xl border dark:border-slate-800 border-slate-200 p-4 dark:bg-white/5 bg-slate-50/50">
              {renderSummary(result.summary)}
            </div>
          </div>
        </div>
      )}
        </>
      )}
    </div>
  );
}
