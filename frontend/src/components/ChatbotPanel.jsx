'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, Sparkles, Loader2 } from 'lucide-react';
import { sendChat } from '@/lib/api';

const SUGGESTIONS = [
  "Summarise today's high-risk alerts",
  "Which vendors appear most suspicious?",
  "How many CRITICAL alerts are there?",
  "What action should I take right now?",
];

function Message({ msg }) {
  const isBot = msg.role === 'assistant';
  return (
    <div className={`flex gap-2 ${isBot ? 'justify-start' : 'justify-end'} animate-fade-in`}>
      {isBot && (
        <div className="w-6 h-6 rounded-full bg-neon-green/10 border border-neon-green/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Bot className="w-3 h-3 text-neon-green" />
        </div>
      )}
      <div className={`max-w-[82%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
        isBot
          ? 'dark:bg-white/5 bg-slate-100 dark:text-slate-200 text-slate-800 rounded-tl-sm'
          : 'bg-neon-green/20 border border-neon-green/20 text-neon-green rounded-tr-sm'
      }`}>
        {msg.text}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-2 justify-start">
      <div className="w-6 h-6 rounded-full bg-neon-green/10 border border-neon-green/20 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Bot className="w-3 h-3 text-neon-green" />
      </div>
      <div className="px-3 py-2 rounded-xl rounded-tl-sm dark:bg-white/5 bg-slate-100 flex items-center gap-1">
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-neon-green/60 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function ChatbotPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hi! I\'m AuditAI. Ask me anything about the flagged transactions — risk summaries, vendor patterns, or what action to take.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (isOpen) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const submit = async (text) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    setInput('');

    const userMsg = { role: 'user', text: q };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      // Build history for context (exclude the initial greeting)
      const history = messages.slice(1).map(m => ({ role: m.role, text: m.text }));
      const data = await sendChat(q, history);
      setMessages(prev => [...prev, { role: 'assistant', text: data.answer }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Sorry, I could not reach the backend. Make sure the server is running.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <div className="flex-shrink-0 relative z-20 px-2 pb-2 pt-2">
      {/* Slide-up drawer */}
      <div
        className={`absolute bottom-full left-2 right-2 glass-panel rounded-2xl flex flex-col overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[520px] opacity-100' : 'max-h-0 opacity-0 pointer-events-none'}`}
        style={{ marginBottom: '4px' }}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b dark:border-white/5 border-slate-200 flex items-center justify-between flex-shrink-0 dark:bg-white/5 bg-slate-50/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-neon-green" />
            </div>
            <div>
              <h3 className="text-xs font-bold dark:text-white text-slate-900">AuditAI Assistant</h3>
              <p className="text-[10px] dark:text-slate-400 text-slate-500">Powered by OpenRouter (gpt-oss-120b)</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse" />
            <span className="text-[10px] text-neon-green font-semibold">Live</span>
            <button onClick={() => setIsOpen(false)} className="p-1 rounded-lg dark:bg-white/5 bg-slate-100 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors ml-1">
              <X className="w-3.5 h-3.5 dark:text-slate-400 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5 min-h-0">
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Suggestions (only when just greeting) */}
        {messages.length === 1 && !loading && (
          <div className="px-3 pb-2 space-y-1.5">
            <p className="text-[9px] font-bold uppercase tracking-wider dark:text-slate-500 text-slate-400">Try asking:</p>
            <div className="grid grid-cols-2 gap-1">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="text-left text-[10px] px-2.5 py-1.5 rounded-lg border dark:border-white/5 border-slate-200 dark:text-slate-400 text-slate-600 dark:bg-white/5 bg-slate-50 hover:bg-neon-green/10 hover:border-neon-green/20 hover:text-neon-green transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-3 border-t dark:border-white/5 border-slate-200 flex-shrink-0">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about alerts, risks, actions…"
              disabled={loading}
              className="flex-1 text-xs px-3 py-2 rounded-xl dark:bg-white/5 bg-slate-100 border dark:border-white/5 border-slate-200 dark:text-slate-300 text-slate-700 placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-neon-green/50 disabled:opacity-60 transition"
            />
            <button
              onClick={() => submit()}
              disabled={!input.trim() || loading}
              className="p-2 rounded-xl bg-neon-green/20 border border-neon-green/30 text-neon-green hover:bg-neon-green/30 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Pill FAB */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl glass-panel hover:border-neon-green/30 transition-all duration-200 hover:shadow-[0_0_16px_rgba(57,255,20,0.15)] group"
      >
        <div className="w-8 h-8 rounded-xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center flex-shrink-0 group-hover:bg-neon-green/20 transition-colors">
          {isOpen ? <X className="w-4 h-4 text-neon-green" /> : <MessageCircle className="w-4 h-4 text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]" />}
        </div>
        <div className="text-left">
          <p className="text-xs font-semibold dark:text-white text-slate-900">{isOpen ? 'Close Assistant' : 'Ask AuditAI'}</p>
          <p className="text-[10px] dark:text-slate-400 text-slate-500">{isOpen ? 'Collapse the AI chat' : 'Get answers about flagged alerts'}</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          {!isOpen && messages.length > 1 && (
            <span className="w-4 h-4 rounded-full bg-neon-green text-app-dark text-[9px] font-black flex items-center justify-center">
              {messages.filter(m => m.role === 'assistant').length - 1}
            </span>
          )}
          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-neon-green/10 border border-neon-green/20 text-neon-green">AI</span>
        </div>
      </button>
    </div>
  );
}
