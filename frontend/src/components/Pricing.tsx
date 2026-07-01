import { useRef, useState, useEffect } from 'react'
import { motion, useInView } from 'framer-motion'

function AnimatedPrice() {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true })
  const [started, setStarted] = useState(false)

  useEffect(() => {
    if (!inView || started) return
    setStarted(true)
    const startTime = performance.now()
    const animate = (now: number) => {
      const t = Math.min((now - startTime) / 800, 1)
      setCount(Math.round(99 * (1 - (1 - t) ** 3)))
      if (t < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [inView, started])

  return (
    <div ref={ref} className="inline-flex items-baseline gap-2">
      <span className="text-5xl md:text-6xl font-bold text-white tracking-[-0.03em]">
        ${count}
      </span>
      <span className="text-lg text-[#94a3b8]">/month</span>
    </div>
  )
}

export default function Pricing() {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <section className="section-pad relative" id="pricing">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div ref={ref}>
          <div className="max-w-2xl mb-14 md:mb-16">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.05 }}
              className="text-[10px] font-mono text-[#64748b] uppercase tracking-[0.18em] mb-5"
            >
              Pricing
            </motion.div>
            <motion.h2
              initial={{ opacity: 0, y: 24 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.08 }}
              className="text-[clamp(2rem,4.5vw,3.6rem)] font-bold leading-[1.05] tracking-[-0.035em] text-white mb-4"
            >
              $4,167/month for an SDR.
              <br />
              <span className="text-[#94a3b8]">$99/month for LeadGen.</span>
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.12 }}
              className="text-base text-[#94a3b8] leading-relaxed text-pretty"
            >
              Same output. 42× fewer zeros.
            </motion.p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.16 }}
            className="max-w-3xl"
          >
            {/* Price and value frame */}
            <div className="flex flex-wrap items-end gap-6 mb-8">
              <div>
                <div className="text-[11px] font-mono text-[#64748b] mb-1">Your investment</div>
                <AnimatedPrice />
              </div>
              <div className="h-12 w-px bg-[rgba(255,255,255,0.04)] hidden sm:block" />
              <div className="text-sm text-[#94a3b8] leading-relaxed max-w-xs text-pretty">
                Up to 500 qualified leads. That&rsquo;s ~$0.20 per lead — and 15+ hours of your week back.
              </div>
            </div>

            {/* Feature set */}
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3 mb-8">
              {[
                { icon: '⏱️', label: 'Setup', value: '5 minutes, no code' },
                { icon: '🎯', label: 'Targets', value: 'Unlimited queries' },
                { icon: '📬', label: 'Leads / month', value: 'Up to 500' },
                { icon: '📤', label: 'Email volume', value: 'Unlimited' },
                { icon: '🔄', label: 'Follow-ups', value: 'Automated' },
                { icon: '📊', label: 'Analytics', value: 'Live dashboard' },
                { icon: '🔐', label: 'Infrastructure', value: 'Stripe · SendGrid' },
                { icon: '🤝', label: 'Support', value: 'Email within 24h' },
                { icon: '⏸️', label: 'Control', value: 'Pause or cancel' },
              ].map(f => (
                <div
                  key={f.label}
                  className="flex items-start gap-2.5 px-4 py-3 rounded-lg bg-[rgba(255,255,255,0.015)] border border-[rgba(255,255,255,0.04)]"
                >
                  <span className="text-sm mt-0.5">{f.icon}</span>
                  <div>
                    <div className="text-sm text-[#cbd5e1]">{f.value}</div>
                    <div className="text-[10px] font-mono text-[#64748b]">{f.label}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Risk reducers */}
            <div className="flex flex-wrap gap-2 mb-8">
              <span className="inline-flex items-center px-3 py-1.5 rounded-full border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] text-[11px] font-mono text-[#94a3b8]">
                ✓ 14-day free trial
              </span>
              <span className="inline-flex items-center px-3 py-1.5 rounded-full border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] text-[11px] font-mono text-[#94a3b8]">
                ✓ No credit card required
              </span>
              <span className="inline-flex items-center px-3 py-1.5 rounded-full border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] text-[11px] font-mono text-[#94a3b8]">
                ✓ Cancel 2 clicks
              </span>
              <span className="inline-flex items-center px-3 py-1.5 rounded-full border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] text-[11px] font-mono text-[#94a3b8]">
                ✓ Pause anytime
              </span>
            </div>

            {/* CTA */}
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
            <div className="mt-3 text-xs text-[#64748b]">
              14-day free trial · No credit card required · Cancel or pause anytime
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
