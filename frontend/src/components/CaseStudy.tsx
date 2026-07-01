import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

export default function CaseStudy() {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section className="section-pad relative overflow-hidden" id="case-study">
      <div className="absolute inset-0 pointer-events-none"><div className="absolute top-1/3 -left-40 w-96 h-96 bg-[rgba(99,102,241,0.02)] rounded-full blur-[120px]" /></div>
      <div className="mx-auto max-w-7xl px-6 md:px-10 relative z-10" ref={ref}>
        <div className="max-w-2xl mb-12 md:mb-16">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.08 }}
            className="text-[10px] font-mono text-[#64748b] uppercase tracking-[0.18em] mb-5">Customer Results</motion.div>
          <motion.h2 initial={{ opacity: 0, y: 24 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.1 }}
            className="text-[clamp(1.8rem,4vw,3rem)] font-bold leading-[1.05] tracking-[-0.035em] text-white mb-4">
            &ldquo;We went from 10 cold emails a week to 300 — all automated.&rdquo;</motion.h2>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.15 }} className="max-w-3xl">
          <div className="flex items-center gap-4 mb-6 pb-5 border-b border-[rgba(255,255,255,0.04)]">
            <div className="w-10 h-10 rounded-full bg-[#475569] flex items-center justify-center text-sm font-medium text-[#94a3b8]">S</div>
            <div><div className="text-sm font-medium text-white/90">Sarah Kim</div><div className="text-xs text-[#94a3b8]">CEO, BrightStudio</div></div>
          </div>
          <blockquote className="text-sm md:text-base text-[#cbd5e1] leading-relaxed text-pretty mb-8">We were spending 15+ hours a week on prospecting — searching Google, finding emails, writing cold emails. The agent does all of it in the background. We just review the replies and jump on calls. Setup took 5 minutes.</blockquote>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[rgba(255,255,255,0.04)] rounded-xl overflow-hidden mb-8">
            {[{ l: 'Leads / month', v: '240+' }, { l: 'Reply rate', v: '34%' }, { l: 'Meetings booked', v: '18' }, { l: 'Time saved', v: '~15h/wk' }].map(s => (
              <div key={s.l} className="bg-[#060a14] p-6 text-center">
                <div className="text-2xl font-bold text-white tracking-tight mb-1">{s.v}</div>
                <div className="text-xs text-[#94a3b8]">{s.l}</div>
              </div>
            ))}
          </div>

          <div className="space-y-3 py-4">
            <div className="text-xs font-mono text-[#64748b] uppercase tracking-[0.12em] mb-4">Pipeline Snapshot</div>
            {[{ l: 'Companies found', v: '847', p: 100 }, { l: 'Qualified leads', v: '240', p: 28 }, { l: 'Emails sent', v: '240', p: 28 }, { l: 'Replies received', v: '82', p: 10 }, { l: 'Meetings booked', v: '18', p: 2 }].map(s => (
              <div key={s.l} className="flex items-center gap-3">
                <span className="text-sm text-[#94a3b8] w-36 shrink-0">{s.l}</span>
                <div className="flex-1 h-1.5 rounded-full bg-[rgba(255,255,255,0.03)] overflow-hidden">
                  <div className="h-full rounded-full bg-[rgba(99,102,241,0.4)]" style={{ width: `${s.p}%` }} /></div>
                <span className="text-sm font-mono text-[#cbd5e1] w-12 text-right">{s.v}</span>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-4 mt-6 pt-5 border-t border-[rgba(255,255,255,0.04)]">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[rgba(99,102,241,0.06)] border border-[rgba(99,102,241,0.08)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[rgba(99,102,241,0.5)]" /><span className="text-[11px] font-mono text-[rgba(99,102,241,0.6)]">3 closed deals · 3× ROI</span></span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
