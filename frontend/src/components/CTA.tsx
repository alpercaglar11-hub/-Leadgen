import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

export default function CTA() {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <section className="section-pad relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_25%_at_50%_50%,rgba(99,102,241,0.025),transparent)]" />
        <div className="absolute top-0 left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-[rgba(99,102,241,0.08)] to-transparent" />
      </div>
      <div className="mx-auto max-w-7xl px-6 md:px-10 relative z-10 text-center" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ type: 'spring', stiffness: 80, damping: 22 }}
          className="max-w-xl mx-auto space-y-6"
        >
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.04 }}
            className="text-[10px] font-mono text-[#64748b] uppercase tracking-[0.18em]"
          >
            Get started
          </motion.div>

          <h2 className="text-[clamp(2rem,5vw,3.6rem)] font-bold leading-[1.05] tracking-[-0.035em] text-white">
            What are you waiting for?<br />
            <span className="text-[#94a3b8]">You've seen it work.</span>
          </h2>

          <p className="text-sm md:text-base text-[#94a3b8] leading-relaxed text-pretty mx-auto max-w-md">
            Set a target query. The agent starts immediately. Replies land in your inbox within hours — not days.
          </p>

          <div className="pt-4 flex flex-col items-center gap-3">
            <a
              href="/subscribe"
              className="group relative inline-flex items-center gap-2 px-7 py-3.5 rounded-xl text-sm font-medium text-white no-underline border border-[rgba(255,255,255,0.2)] hover:border-white/40 hover:bg-[rgba(255,255,255,0.02)] active:scale-[0.97] transition-all duration-200"
            >
              Start Free Trial
              <svg
                width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className="transition-transform duration-200 group-hover:translate-x-[3px]"
              >
                <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
              </svg>
            </a>
            <div className="text-xs text-[#64748b]">
              5-minute setup · 14-day free trial · No code · No commitment
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
