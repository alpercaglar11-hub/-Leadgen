import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

export default function Footer() {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  return (
    <footer className="relative z-10 border-t border-[rgba(255,255,255,0.03)]">
      <div className="mx-auto max-w-7xl px-6 md:px-10 py-12 md:py-16" ref={ref}>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 160, damping: 22, delay: 0.02 }}
          className="flex flex-wrap items-center justify-between gap-4 mb-10 pb-6 border-b border-[rgba(255,255,255,0.03)]">
          <span className="text-sm text-[#94a3b8]">Autonomous AI lead generation for B2B sales teams</span>
          <div className="flex gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] text-[10px] font-mono text-[#64748b]">Powered by Stripe</span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.02)] text-[10px] font-mono text-[#64748b]">SendGrid Delivery</span>
          </div>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
          {[
            { h: null, links: null, brand: true },
            { h: 'Product', links: [{ l: 'Pricing', h: '/#pricing' }, { l: 'Dashboard', h: '/dashboard' }, { l: 'API Status', h: '/health' }] },
            { h: 'Resources', links: [{ l: 'Blog', h: '#' }, { l: 'Documentation', h: '#' }, { l: 'Changelog', h: '#' }] },
            { h: 'Legal', links: [{ l: 'Privacy', h: '#' }, { l: 'Terms', h: '#' }] },
          ].map(({ h, links, brand }, ci) => (
            <motion.div key={h ?? 'brand'} initial={{ opacity: 0, y: 12 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 160, damping: 22, delay: 0.05 + ci * 0.04 }}>
              {brand ? (
                <><a href="/" className="text-sm font-semibold tracking-tight text-white/90 no-underline">LeadGen</a>
                  <p className="text-xs text-[#64748b] leading-relaxed mt-3 max-w-[200px] text-pretty">An autonomous AI employee that finds and contacts your ideal customers.</p></>
              ) : (
                <><h4 className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-[0.1em] mb-3">{h}</h4>
                  <nav className="flex flex-col gap-2" aria-label={`${h} links`}>
                    {links!.map(item => <a key={item.l} href={item.h} className="text-xs text-[#64748b] hover:text-[#94a3b8] no-underline transition-colors">{item.l}</a>)}
                  </nav></>
              )}
            </motion.div>
          ))}
        </div>

        <motion.div initial={{ opacity: 0 }} animate={inView ? { opacity: 1 } : {}} transition={{ duration: 0.5, delay: 0.3 }}
          className="pt-6 border-t border-[rgba(255,255,255,0.03)] flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-[10px] text-[#475569]">&copy; {new Date().getFullYear()} LeadGen.</div>
          <div className="flex gap-4 text-[10px] text-[#475569]">
            {['Twitter', 'GitHub', 'LinkedIn'].map(s => <a key={s} href="#" className="hover:text-[#94a3b8] no-underline transition-colors">{s}</a>)}
          </div>
        </motion.div>
      </div>
    </footer>
  )
}
