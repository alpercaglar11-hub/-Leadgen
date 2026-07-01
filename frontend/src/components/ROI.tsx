import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const VS_DATA = [
  { label: 'Monthly cost', us: '$99', them: '$4,167+', highlight: true },
  { label: 'Leads / month', us: 'Up to 500', them: '~40', highlight: false },
  { label: 'Hours / week', us: '0 (automated)', them: '15+', highlight: true },
  { label: 'Setup time', us: '5 minutes', them: 'Weeks', highlight: false },
  { label: 'Scales with volume', us: 'Instantly', them: 'Hire more', highlight: false },
  { label: 'Reply rate', us: '34% avg', them: '~10%', highlight: true },
]

function ComparisonRow({ row, i }: { row: typeof VS_DATA[0]; i: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: -12 }}
      animate={inView ? { opacity: 1, x: 0 } : {}}
      transition={{ type: 'spring', stiffness: 160, damping: 22, delay: 0.03 + i * 0.04 }}
      className={`grid grid-cols-3 gap-4 py-3 px-4 rounded-lg transition-colors duration-200 ${
        row.highlight ? 'bg-[rgba(99,102,241,0.03)]' : ''
      }`}
    >
      <span className="text-sm text-[#94a3b8]">{row.label}</span>
      <span className="text-sm font-medium text-white">{row.us}</span>
      <span className="text-sm text-[#64748b]">{row.them}</span>
    </motion.div>
  )
}

export default function ROI() {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section className="section-pad relative overflow-hidden" id="roi">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 -right-40 w-96 h-96 bg-[rgba(99,102,241,0.015)] rounded-full blur-[120px]" />
      </div>

      <div className="mx-auto max-w-7xl px-6 md:px-10 relative z-10" ref={ref}>
        <div className="max-w-2xl mb-14 md:mb-16">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.05 }}
            className="text-[10px] font-mono text-[#64748b] uppercase tracking-[0.18em] mb-5"
          >
            Return on investment
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 24 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.08 }}
            className="text-[clamp(1.8rem,4vw,3rem)] font-bold leading-[1.05] tracking-[-0.035em] text-white mb-4"
          >
            $99/month or hire someone<br />
            <span className="text-[#94a3b8]">for $50,000/year.</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.12 }}
            className="text-base text-[#94a3b8] leading-relaxed text-pretty"
          >
            Most companies spend $4,000+ per month on a single SDR — and still rely on manual prospecting.
            LeadGen does the work of a full-time employee for the price of a dinner out.
          </motion.p>
        </div>

        <div className="grid lg:grid-cols-12 gap-10 lg:gap-16 items-start">
          {/* Comparison table */}
          <div className="lg:col-span-7">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.15 }}
            >
              {/* Header */}
              <div className="grid grid-cols-3 gap-4 px-4 pb-2 text-[10px] font-mono text-[#475569] uppercase tracking-[0.12em]">
                <span></span>
                <span className="text-[#818cf8]">LeadGen</span>
                <span>Human SDR</span>
              </div>
              <div className="h-px bg-[rgba(255,255,255,0.04)] mb-2" />

              {VS_DATA.map((row, i) => (
                <ComparisonRow key={row.label} row={row} i={i} />
              ))}
            </motion.div>
          </div>

          {/* Key metric cards */}
          <div className="lg:col-span-5 space-y-4">
            {[
              { value: '$0.20', label: 'per qualified lead', sub: 'vs $15–$50 with ads or agencies' },
              { value: '15+ hrs', label: 'saved per week', sub: 'that\'s 60+ hours per month you get back' },
              { value: '42×', label: 'more output vs manual outreach', sub: 'at 1/40th the cost of a human' },
            ].map((m, i) => (
              <motion.div
                key={m.value}
                initial={{ opacity: 0, y: 20 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ type: 'spring', stiffness: 160, damping: 22, delay: 0.2 + i * 0.08 }}
                className="p-5 rounded-xl bg-[rgba(255,255,255,0.015)] border border-[rgba(255,255,255,0.04)]"
              >
                <div className="text-2xl font-bold text-white tracking-tight mb-1">{m.value}</div>
                <div className="text-sm text-[#94a3b8] mb-0.5">{m.label}</div>
                <div className="text-[11px] text-[#475569]">{m.sub}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
