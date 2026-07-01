import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const NAV = [
  { label: 'How it works', href: '#product' },
  { label: 'Case Study', href: '#case-study' },
  { label: 'Pricing', href: '#pricing' },
]

export default function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [active, setActive] = useState('product')
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [menuOpen])

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 20)
      const doc = document.documentElement
      setProgress(Math.min(1, window.scrollY / (doc.scrollHeight - doc.clientHeight)))
      let cur = 'hero'
      for (const s of NAV) {
        const el = document.getElementById(s.href.slice(1))
        if (el && el.getBoundingClientRect().top <= 150) cur = s.href.slice(1)
      }
      setActive(cur)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const scrollTo = (href: string) => {
    setMenuOpen(false)
    document.getElementById(href.slice(1))?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <>
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled ? 'bg-[rgba(6,10,20,0.85)] backdrop-blur-2xl border-b border-[rgba(255,255,255,0.03)]' : ''
        }`}
      >
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-[rgba(255,255,255,0.03)]">
          <div className="h-full bg-[rgba(99,102,241,0.4)] transition-all duration-100" style={{ width: `${progress * 100}%` }} />
        </div>

        <div className="mx-auto max-w-7xl px-6 md:px-10">
          <div className="flex items-center justify-between h-16 md:h-18">
            <a href="/" className="text-sm font-semibold tracking-tight text-white/90 no-underline">LeadGen</a>

            <nav className="hidden md:flex items-center gap-6" aria-label="Main">
              {NAV.map(s => (
                <a key={s.href} href={s.href} onClick={e => { e.preventDefault(); scrollTo(s.href) }}
                  className={`text-sm no-underline border-b border-transparent transition-colors duration-200 ${
                    active === s.href.slice(1) ? 'text-white border-white/30' : 'text-[#64748b] hover:text-[#94a3b8] hover:border-[rgba(255,255,255,0.2)]'
                  }`}>{s.label}</a>
              ))}
              <a href="/subscribe" className="ml-2 px-4 py-2 text-sm font-medium text-white rounded-lg border border-[rgba(255,255,255,0.15)] hover:border-white/30 transition-all duration-200 no-underline">
                Start Free Trial
              </a>
            </nav>

            <button onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? 'Close' : 'Menu'}
              className="md:hidden w-10 h-10 flex items-center justify-center rounded-lg text-[#64748b] hover:text-white transition-colors cursor-pointer">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
                className="transition-transform duration-300" style={{ transform: menuOpen ? 'rotate(90deg)' : '' }}>
                {menuOpen ? (
                  <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>
                ) : (
                  <><line x1="4" y1="6" x2="20" y2="6" /><line x1="4" y1="12" x2="20" y2="12" /><line x1="4" y1="18" x2="20" y2="18" /></>
                )}
              </svg>
            </button>
          </div>
        </div>
      </motion.header>

      <AnimatePresence>
        {menuOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-40 flex items-end justify-center" onClick={() => setMenuOpen(false)}>
            <div className="absolute inset-0 bg-[rgba(3,5,10,0.6)]" />
            <motion.div initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="relative w-[calc(100%-2rem)] max-w-sm mb-6 rounded-2xl bg-[#0b0f19] border border-[rgba(255,255,255,0.06)] p-6" onClick={e => e.stopPropagation()}>
              <div className="flex flex-col gap-3">
                {NAV.map((s, i) => (
                  <motion.a key={s.href} href={s.href} onClick={e => { e.preventDefault(); scrollTo(s.href) }}
                    initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05, type: 'spring', stiffness: 160, damping: 22 }}
                    className="text-base font-medium text-[#64748b] hover:text-white no-underline py-2 transition-colors">{s.label}</motion.a>
                ))}
                <motion.a href="/subscribe" initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2, type: 'spring', stiffness: 160, damping: 22 }}
                  className="mt-2 px-4 py-3 text-sm font-medium text-white rounded-xl border border-[rgba(255,255,255,0.15)] text-center no-underline">Start Free Trial</motion.a>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
