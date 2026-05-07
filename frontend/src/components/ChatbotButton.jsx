'use client';

import { useState, useEffect } from 'react';
import { X, MessageCircle, Bot, Send, Sparkles } from 'lucide-react';

const SkeletonMsg = ({ isBot = true, widthClass = 'w-3/4' }) => (
  <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} gap-2`}>
    {isBot && (
      <div className="w-7 h-7 rounded-full bg-neon-green/10 border border-neon-green/20 flex items-center justify-center flex-shrink-0 mt-1">
        <Bot className="w-3.5 h-3.5 text-neon-green" />
      </div>
    )}
    <div className={`${widthClass} h-9 rounded-xl dark:bg-white/5 bg-slate-100 animate-pulse`} />
  </div>
);

export default function ChatbotButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');

  useEffect(() => {
    if (isOpen) document.body.style.overflow = 'hidden';
    else document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-50 bg-black/30 backdrop-blur-sm transition-opacity duration-300 ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setIsOpen(false)}
      />

      {/* Chat Drawer */}
      <div className={`fixed bottom-0 right-0 h-[85vh] w-full max-w-sm z-50 transition-transform duration-300 ease-in-out ${isOpen ? 'translate-y-0' : 'translate-y-full'}`}>
        <div className="h-full glass-panel flex flex-col rounded-t-2xl rounded-bl-2xl overflow-hidden mx-4 mb-0 shadow-2xl">

          {/* Header */}
          <div className="px-5 py-4 border-b dark:border-white/5 border-slate-200 flex items-center justify-between flex-shrink-0 dark:bg-white/5 bg-slate-50/80">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-neon-green drop-shadow-[0_0_5px_rgba(57,255,20,0.5)]" />
              </div>
              <div>
                <h3 className="text-sm font-bold dark:text-white text-slate-900">AI Assistant</h3>
                <p className="text-[11px] dark:text-slate-400 text-slate-500">AuditAI · Powered by OpenRouter (gpt-oss-120b)</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[10px] font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Coming Soon
              </span>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg dark:bg-white/5 bg-slate-100 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors"
              >
                <X className="w-4 h-4 dark:text-slate-400 text-slate-500" />
              </button>
            </div>
          </div>

          {/* Messages Area — skeleton placeholder */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            <div className="text-center mb-6">
              <div className="w-12 h-12 rounded-2xl bg-neon-green/10 border border-neon-green/20 flex items-center justify-center mx-auto mb-3">
                <Bot className="w-6 h-6 text-neon-green" />
              </div>
              <p className="text-sm font-medium dark:text-white text-slate-900">AuditAI Assistant</p>
              <p className="text-xs dark:text-slate-400 text-slate-500 mt-1 max-w-[240px] mx-auto">
                Ask me to analyse anomalies, summarise risk exposure, or generate audit narratives.
              </p>
            </div>

            {/* Skeleton chat messages for visual preview */}
            <SkeletonMsg isBot={true} widthClass="w-4/5" />
            <SkeletonMsg isBot={false} widthClass="w-3/5" />
            <SkeletonMsg isBot={true} widthClass="w-3/4" />
            <SkeletonMsg isBot={false} widthClass="w-2/5" />
            <SkeletonMsg isBot={true} widthClass="w-4/5" />

            {/* Suggested prompts */}
            <div className="space-y-2 pt-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider dark:text-slate-500 text-slate-400">Try asking:</p>
              {[
                'Summarise today\'s high-risk transactions',
                'Which department has the most anomalies?',
                'Generate an audit report for TXN-8924',
              ].map(prompt => (
                <button
                  key={prompt}
                  disabled
                  className="w-full text-left text-xs px-3 py-2.5 rounded-xl border dark:border-white/5 border-slate-200 dark:text-slate-400 text-slate-600 dark:bg-white/5 bg-slate-50 hover:border-neon-green/30 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t dark:border-white/5 border-slate-200 flex-shrink-0">
            <div className="flex items-center gap-2">
              <input
                type="text"
                disabled
                placeholder="AI Assistant coming soon..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="flex-1 text-sm px-4 py-2.5 rounded-xl dark:bg-white/5 bg-slate-100 border dark:border-white/5 border-slate-200 dark:text-slate-300 text-slate-700 placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-neon-green disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              />
              <button
                disabled
                className="p-2.5 rounded-xl bg-neon-green/20 border border-neon-green/20 text-neon-green disabled:opacity-40 disabled:cursor-not-allowed hover:bg-neon-green/30 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* FAB — always visible */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full glass-panel flex items-center justify-center shadow-[0_0_20px_rgba(57,255,20,0.25)] hover:shadow-[0_0_30px_rgba(57,255,20,0.4)] transition-all duration-300 animate-pop-in ${isOpen ? 'rotate-90' : 'hover:scale-110'}`}
        title="AI Assistant"
      >
        {isOpen
          ? <X className="w-5 h-5 text-neon-green" />
          : <MessageCircle className="w-5 h-5 text-neon-green drop-shadow-[0_0_6px_rgba(57,255,20,0.6)]" />
        }
      </button>
    </>
  );
}
