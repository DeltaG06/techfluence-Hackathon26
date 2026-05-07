'use client';

import { motion } from 'framer-motion';
import { ShieldAlert, Activity, DollarSign, BarChart2, Globe } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const router = useRouter();

  const handleScroll = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-neon-green/30 font-sans overflow-x-hidden">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 px-4 pt-4 pb-0">
        <div className="mx-auto max-w-6xl rounded-2xl px-6 py-4 flex items-center justify-between transition-colors duration-300"
             style={{
               background: 'rgba(0, 25, 96, 0.7)',
               backdropFilter: 'blur(12px)',
               boxShadow: '0 4px 24px rgba(0,25,96,0.7), inset 0 1px 0 rgba(255,255,255,0.06)',
               border: '1px solid rgba(255,255,255,0.06)',
             }}>
          <div className="flex items-center gap-3">
            <ShieldAlert className="text-green-300 w-7 h-7 flex-shrink-0 drop-shadow-[0_0_8px_rgba(57,255,20,0.5)]" />
            <span className="text-xl font-bold tracking-tight text-white">AuditAI</span>
          </div>
          
          <div className="flex items-center gap-6">
            <button onClick={() => handleScroll('preview')} className="text-sm font-medium text-white/70 hover:text-white transition-colors">Preview</button>
            <button onClick={() => handleScroll('features')} className="text-sm font-medium text-white/70 hover:text-white transition-colors">Features</button>
            
            <div className="h-6 w-px bg-white/20 mx-2"></div>
            
            <button onClick={() => router.push('/risk-feed')} className="text-sm font-bold text-white bg-blue-600 hover:bg-blue-500 px-5 py-2 rounded-xl transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)]">
              Go to Dashboard
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
        {/* Abstract Background Design */}
        <div className="absolute inset-0 w-full h-full z-0 pointer-events-none overflow-hidden">
          {/* Grid Pattern */}
          <div className="absolute inset-0 bg-[url('/grid.svg')] bg-repeat opacity-20" />

          <div className="absolute top-[20%] left-[10%] w-[40rem] h-[40rem] bg-blue-600/20 rounded-full blur-[120px] mix-blend-screen" />
          <div className="absolute bottom-[10%] right-[10%] w-[30rem] h-[30rem] bg-green-500/20 rounded-full blur-[100px] mix-blend-screen" />
          
          {/* Floating Fintech Icons */}
          <motion.div 
            animate={{ y: [-20, 20, -20], rotate: [0, 10, -10, 0] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-[15%] right-[20%] text-blue-500/20"
          >
            <Activity size={120} strokeWidth={1} />
          </motion.div>
          <motion.div 
            animate={{ y: [20, -20, 20], rotate: [0, -15, 15, 0] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="absolute bottom-[25%] left-[15%] text-green-400/10"
          >
            <BarChart2 size={160} strokeWidth={1} />
          </motion.div>
          <motion.div 
            animate={{ y: [-15, 15, -15], rotate: [0, 5, -5, 0] }}
            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut", delay: 2 }}
            className="absolute top-[40%] left-[5%] text-white/5"
          >
            <DollarSign size={100} strokeWidth={1} />
          </motion.div>
          <motion.div 
            animate={{ y: [15, -15, 15], rotate: [0, -5, 5, 0] }}
            transition={{ duration: 14, repeat: Infinity, ease: "easeInOut", delay: 3 }}
            className="absolute bottom-[10%] right-[10%] text-blue-400/10"
          >
            <Globe size={140} strokeWidth={1} />
          </motion.div>

          {/* Animated "transaction" lines */}
          <svg className="absolute w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
             <motion.path 
               d="M 0 500 Q 250 400 500 500 T 1000 500 T 1500 500" 
               stroke="#39FF14" strokeWidth="2" fill="none"
               initial={{ pathLength: 0, opacity: 0 }}
               animate={{ pathLength: 1, opacity: 0.5 }}
               transition={{ duration: 3, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
             />
             <motion.path 
               d="M 0 600 Q 350 700 700 600 T 1400 600" 
               stroke="#4169E1" strokeWidth="2" fill="none"
               initial={{ pathLength: 0, opacity: 0 }}
               animate={{ pathLength: 1, opacity: 0.3 }}
               transition={{ duration: 4, repeat: Infinity, repeatType: "reverse", ease: "easeInOut", delay: 1 }}
             />
          </svg>
        </div>

        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-6 leading-tight"
          >
            Detect Anomalies in <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500">
              Real-Time Financial Data
            </span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            AuditAI uses cutting-edge machine learning to automatically flag irregular spend, 
            generate audit narratives, and protect your organization's bottom line.
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <button onClick={() => router.push('/risk-feed')} className="text-lg font-bold text-[#001960] bg-green-400 hover:bg-green-300 px-8 py-4 rounded-xl transition-all shadow-[0_0_20px_rgba(74,222,128,0.5)] hover:scale-105 active:scale-95">
              Enter Dashboard
            </button>
          </motion.div>
        </div>
      </section>

      {/* Preview Section */}
      <section id="preview" className="min-h-screen py-24 px-6 m-4 flex items-center justify-center bg-emerald-400 relative z-10 overflow-hidden rounded-[2rem]">
        {/* Subtle Grid Pattern Background */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-repeat opacity-80 pointer-events-none" />
        
        <div className="max-w-6xl mx-auto w-full relative z-10">
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-bold text-white mb-4">Command Center for Risk</h2>
            <p className="text-blue-900 max-w-2xl mx-auto">
              Our intuitive dashboard gives you an unparalleled view of your financial health, 
              highlighting what matters most so you can act immediately.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="rounded-2xl border border-white/10 p-2 bg-gradient-to-b from-white/5 to-transparent shadow-2xl group transition-all duration-500 hover:shadow-[0_0_80px_rgba(57,255,20,0.4)]"
          >
            <div className="rounded-xl overflow-hidden aspect-video bg-[#001960] relative border border-white/5 flex items-center justify-center">
              <img 
                src="/dash_preview.png" 
                alt="AuditAI Dashboard Preview" 
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.02]"
              />
              {/* Optional glowing effect over it */}
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-800/10 to-transparent mix-blend-overlay pointer-events-none transition-opacity duration-500 group-hover:opacity-0"></div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="min-h-screen py-24 px-6 flex items-center justify-center relative z-10 overflow-hidden">
        {/* Subtle Dot Grid Pattern */}
        <div className="absolute inset-0 bg-[url('/dots.svg')] bg-repeat opacity-30 pointer-events-none" />
        
        {/* Background glow for pop */}
        <div className="absolute top-[30%] right-[10%] w-[30rem] h-[30rem] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[20%] left-[10%] w-[25rem] h-[25rem] bg-green-500/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="max-w-6xl mx-auto w-full relative z-10">
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="text-center mb-20"
          >
            <h2 className="text-4xl font-bold text-white mb-4">Unmatched Capabilities</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Everything you need to ensure complete financial compliance and prevent fraud before it happens.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { title: "Real-Time Detection", desc: "Flag suspicious transactions within milliseconds of them hitting your ledger." },
              { title: "AI-Powered Narrative", desc: "Automatically generate comprehensive audit reports explaining the nature of anomalies." },
              { title: "Spend Analytics", desc: "Visualize your entire financial footprint and identify abnormal trends." }
            ].map((feat, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: i * 0.2 }}
                className="p-8 rounded-2xl bg-[#001960]/40 border border-white/10 hover:border-green-400/50 transition-colors group"
              >
                <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <div className="w-6 h-6 bg-green-400 rounded-full shadow-[0_0_10px_rgba(57,255,20,0.8)]"></div>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feat.title}</h3>
                <p className="text-slate-400 leading-relaxed">{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-slate-500 border-t border-white/10 relative z-10">
        <p>&copy; {new Date().getFullYear()} AuditAI. All rights reserved.</p>
      </footer>
    </div>
  );
}
