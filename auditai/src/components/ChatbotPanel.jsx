'use client';

import { useState, useEffect } from 'react';
import { MessageCircle, X, Send, Bot, Sparkles } from 'lucide-react';

const SkeletonMsg = ({ isBot = true, widthClass = 'w-3/4' }) => (
  <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} gap-2`}>
    {isBot && (
      <div className="w-6 h-6 rounded-full bg-neon-green/10 border border-neon-green/20 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Bot className="w-3 h-3 text-neon-green" />
      </div>
    )}
    <div className={`${widthClass} h-8 rounded-xl dark:bg-white/5 bg-slate-100 animate-pulse`} />
  </div>
);

export default function ChatbotPanel() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex-shrink-0 relative z-20 px-2 pb-2 pt-2">
      {/* Slide-up drawer — absolute, fills the right column behind the pill */}
      <div
        className={`absolute bottom-full left-2 right-2 glass-panel rounded-2xl flex flex-col overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[520px] opacity-100' : 'max-h-0 opacity-0 pointer-events-none'}`}
        style={{ marginBottom: '4px' }}
      >
        {/* Drawer Header */}
        <div className="px-4 py-3 border-b dark:border-white/5 border-slate-200 flex items-center justify-between flex-shrink-0 dark:bg-white/5 bg-slate-50/80">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-neon-green" />
            </div>
            <div>
              <h3 className="text-xs font-bold dark:text-white text-slate-900">AI Assistant</h3>
              <p className="text-[10px] dark:text-slate-400 text-slate-500">Powered by Gemini</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-1.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[9px] font-bold">Coming Soon</span>
            <button onClick={() => setIsOpen(false)} className="p-1 rounded-lg dark:bg-white/5 bg-slate-100 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors">
              <X className="w-3.5 h-3.5 dark:text-slate-400 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Messages / Preview Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
          <div className="text-center py-3">
            <div className="w-10 h-10 rounded-xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center mx-auto mb-2">
              <Bot className="w-5 h-5 text-neon-green" />
            </div>
            <p className="text-xs font-medium dark:text-white text-slate-900">AuditAI Assistant</p>
            <p className="text-[10px] dark:text-slate-400 text-slate-500 mt-0.5 max-w-[180px] mx-auto">Analyse anomalies, summarise risk exposure, generate audit narratives.</p>
          </div>

          <SkeletonMsg isBot widthClass="w-4/5" />
          <SkeletonMsg isBot={false} widthClass="w-3/5" />
          <SkeletonMsg isBot widthClass="w-3/4" />
          <SkeletonMsg isBot={false} widthClass="w-2/5" />

          <div className="space-y-1.5 pt-1">
            <p className="text-[9px] font-bold uppercase tracking-wider dark:text-slate-500 text-slate-400">Try asking:</p>
            {[
              "Summarise today's high-risk transactions",
              "Which dept has the most anomalies?",
            ].map(p => (
              <button key={p} disabled className="w-full text-left text-[10px] px-2.5 py-2 rounded-lg border dark:border-white/5 border-slate-200 dark:text-slate-400 text-slate-600 dark:bg-white/5 bg-slate-50 disabled:opacity-60 disabled:cursor-not-allowed">
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className="p-3 border-t dark:border-white/5 border-slate-200 flex-shrink-0">
          <div className="flex items-center gap-2">
            <input
              type="text"
              disabled
              placeholder="AI Assistant coming soon…"
              className="flex-1 text-xs px-3 py-2 rounded-xl dark:bg-white/5 bg-slate-100 border dark:border-white/5 border-slate-200 dark:text-slate-300 text-slate-700 placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button disabled className="p-2 rounded-xl bg-neon-green/20 border border-neon-green/20 text-neon-green disabled:opacity-40 disabled:cursor-not-allowed">
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Pill FAB — extended rounded rectangle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl glass-panel hover:border-neon-green/30 transition-all duration-200 hover:shadow-[0_0_16px_rgba(57,255,20,0.15)] group"
      >
        <div className="w-8 h-8 rounded-xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center flex-shrink-0 group-hover:bg-neon-green/15 transition-colors">
          {isOpen
            ? <X className="w-4 h-4 text-neon-green" />
            : <MessageCircle className="w-4 h-4 text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]" />
          }
        </div>
        <div className="text-left">
          <p className="text-xs font-semibold dark:text-white text-slate-900">
            {isOpen ? 'Close Assistant' : 'Ask AuditAI'}
          </p>
          <p className="text-[10px] dark:text-slate-400 text-slate-500">
            {isOpen ? 'Collapse the AI chat' : 'Welcome to your AI Assistant'}
          </p>
        </div>
        <div className="ml-auto">
          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-neon-green/10 border border-neon-green/20 text-neon-green">AI</span>
        </div>
      </button>
    </div>
  );
}
