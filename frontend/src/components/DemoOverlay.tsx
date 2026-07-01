import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

/* ── Demo lifecycle steps ────────────────────────────────────── */

const DEMO_STEPS = [
  {
    phase: 'user',
    icon: '👤',
    title: 'You enter a target query',
    desc: '"Digital agencies in Berlin looking for Series A"',
    detail: 'Setup takes 5 seconds.',
    waitMs: 1500,
  },
  {
    phase: 'search',
    icon: '🔍',
    title: 'Agent searches Google',
    desc: 'Real browser opens. Searches Google. Filters by stage, location, revenue.',
    detail: 'google.com/search?q=digital+agencies+Berlin+Series+A',
    waitMs: 2000,
  },
  {
    phase: 'parse',
    icon: '📋',
    title: 'Parses results',
    desc: '47 companies found. 3 duplicates removed. 44 unique leads extracted.',
    detail: '→ CannyBuild GmbH · Series A · €4.2M',
    waitMs: 1800,
  },
  {
    phase: 'visit',
    icon: '🌐',
    title: 'Visits every website',
    desc: 'Opens each site. Reads homepage, about, team, careers pages. Extracts context.',
    detail: 'cannybuild.io — 200 OK · 1.2s · 6 pages scanned',
    waitMs: 2000,
  },
  {
    phase: 'extract',
    icon: '📎',
    title: 'Finds decision-makers',
    desc: 'Identifies founders, CEOs, and heads of sales. Extracts verified email addresses.',
    detail: 'marcus@cannybuild.io · confidence 94%',
    waitMs: 1800,
  },
  {
    phase: 'score',
    icon: '📊',
    title: 'Scores every lead',
    desc: 'Ranks each company against your ideal customer profile. Low matches discarded.',
    detail: 'CannyBuild: 94% match · ICP fit: strong ✓',
    waitMs: 1500,
  },
  {
    phase: 'compose',
    icon: '✍️',
    title: 'Writes personalized email',
    desc: 'AI reads the company website, understands their business, writes a unique message.',
    detail: '"Hi Marcus — came across your Series A and expansion into enterprise..."',
    waitMs: 2500,
  },
  {
    phase: 'review',
    icon: '✅',
    title: 'Reviews tone & quality',
    desc: 'Checks for warmth, clarity, personalization. Scores the draft before sending.',
    detail: 'Tone: confident · warm · concise · Score: 92%',
    waitMs: 1200,
  },
  {
    phase: 'send',
    icon: '📤',
    title: 'Sends via SendGrid',
    desc: 'Delivered with tracking. Opens, clicks, and replies are monitored in real-time.',
    detail: 'Sent to marcus@cannybuild.io · tracking enabled',
    waitMs: 1500,
  },
  {
    phase: 'wait',
    icon: '⏳',
    title: 'Waits & follows up',
    desc: 'Follow-up #1 scheduled in 48 hours if no reply. Agent continues working other leads.',
    detail: '38 leads remaining in queue · batch 2/4',
    waitMs: 2000,
  },
  {
    phase: 'reply',
    icon: '📬',
    title: 'Reply detected',
    desc: 'Positive response. Lead automatically moved to qualified.',
    detail: '"Thanks for reaching out — let\'s talk next week"',
    waitMs: 2000,
  },
  {
    phase: 'meeting',
    icon: '📅',
    title: 'Meeting booked',
    desc: 'Calendar invite synced. Deal moves to pipeline.',
    detail: '30 min · Thursday 2pm · Pipeline value: $240K',
    waitMs: 1500,
  },
  {
    phase: 'sleep',
    icon: '😴',
    title: 'Meanwhile, you were sleeping.',
    desc: 'You set one query. The agent did the rest. You just take the meetings.',
    detail: '0 hours spent. 44 leads found. 1 meeting booked. ∞ value.',
    waitMs: 0,
    final: true,
  },
]

function StepCard({ step, visible, isLast }: { step: typeof DEMO_STEPS[0]; visible: boolean; isLast: boolean }) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 16, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 120, damping: 20 }}
          className={`flex items-start gap-4 p-4 rounded-xl border transition-colors duration-300 ${
            step.final
              ? 'border-[rgba(99,102,241,0.2)] bg-[rgba(99,102,241,0.06)]'
              : isLast
                ? 'border-[rgba(99,102,241,0.15)] bg-[rgba(99,102,241,0.03)]'
                : 'border-[rgba(255,255,255,0.04)] bg-[rgba(255,255,255,0.015)]'
          }`}
        >
          <span className="text-xl mt-0.5">{step.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white mb-0.5">{step.title}</div>
            <div className="text-xs text-[#94a3b8] leading-relaxed text-pretty mb-1">{step.desc}</div>
            <div className={`text-[11px] font-mono ${step.final ? 'text-[#818cf8]' : 'text-[#475569]'} truncate`}>
              {step.detail}
            </div>
          </div>
          {!step.final && (
            <div className={`w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${isLast ? 'bg-[#818cf8]' : 'bg-[#475569]'}`} />
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function ThinkingIndicator({ step }: { step: typeof DEMO_STEPS[0] }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-3 px-1 py-2"
    >
      <span className="text-lg">{step.icon}</span>
      <span className="text-xs font-mono text-[#64748b]">
        {step.title}..
        <span className="inline-flex gap-[2px] ml-1">
          <span className="animate-pulse">.</span>
          <span className="animate-pulse" style={{ animationDelay: '200ms' }}>.</span>
          <span className="animate-pulse" style={{ animationDelay: '400ms' }}>.</span>
        </span>
      </span>
    </motion.div>
  )
}

function ProgressBar({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex gap-1">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1 flex-1 rounded-full transition-all duration-500 ${
            i < current ? 'bg-[#818cf8]' : i === current ? 'bg-[rgba(99,102,241,0.3)]' : 'bg-[rgba(255,255,255,0.04)]'
          }`}
        />
      ))}
    </div>
  )
}

export default function DemoOverlay({ onClose }: { onClose: () => void }) {
  const [visibleSteps, setVisibleSteps] = useState<number[]>([])
  const [thinking, setThinking] = useState<number | null>(null)
  const [done, setDone] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)

  const run = useCallback(() => {
    setVisibleSteps([])
    setThinking(0)
    setDone(false)
    setElapsed(0)

    let i = 0
    const advance = () => {
      if (!mountedRef.current || i >= DEMO_STEPS.length) return
      const step = DEMO_STEPS[i]
      setThinking(i)

      const actualWait = step.waitMs + Math.random() * step.waitMs * 0.15
      setTimeout(() => {
        if (!mountedRef.current) return
        setThinking(null)
        setVisibleSteps(p => [...p, i])
        i++
        if (i >= DEMO_STEPS.length) {
          setDone(true)
        } else {
          setTimeout(advance, 300 + Math.random() * 200)
        }
      }, actualWait)
    }
    setTimeout(advance, 400)
  }, [])

  useEffect(() => {
    mountedRef.current = true
    run()
    timerRef.current = setInterval(() => {
      setElapsed(e => e + 1)
    }, 1000)
    return () => {
      mountedRef.current = false
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [run])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const currentStep = visibleSteps.length
  const totalSteps = DEMO_STEPS.length - 1 // exclude final "sleep" from count

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-[100] flex items-start justify-center overflow-y-auto"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="fixed inset-0 bg-[rgba(2,4,10,0.85)] backdrop-blur-xl" />

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 25 }}
        className="relative w-full max-w-xl mx-auto my-8 md:my-12 px-4"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-[#4ade80]" style={{ animation: 'status-pulse 2.5s ease-in-out infinite' }} />
            <span className="text-xs font-mono text-[#64748b]">
              Agent Demo · {elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-[#64748b] hover:text-white hover:bg-[rgba(255,255,255,0.04)] transition-all cursor-pointer"
            aria-label="Close"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Progress */}
        {!done && <ProgressBar current={currentStep} total={totalSteps} />}
        <div className="h-4" />

        {/* Steps */}
        <div className="space-y-3">
          {DEMO_STEPS.map((step, i) => (
            <StepCard key={i} step={step} visible={visibleSteps.includes(i)} isLast={i === visibleSteps.length - 1} />
          ))}
          {thinking !== null && !done && (
            <ThinkingIndicator step={DEMO_STEPS[thinking]} />
          )}
        </div>

        {/* Final CTA */}
        {done && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, type: 'spring', stiffness: 100, damping: 20 }}
            className="mt-8 text-center"
          >
            <div className="text-center space-y-4">
              <p className="text-sm text-[#94a3b8]">
                That&rsquo;s what happens while you sleep. Every single night.
              </p>
              <a
                href="/subscribe"
                className="group relative inline-flex items-center gap-2 px-7 py-3.5 rounded-xl text-sm font-medium text-white no-underline border border-[rgba(255,255,255,0.2)] hover:border-white/40 hover:bg-[rgba(255,255,255,0.02)] active:scale-[0.97] transition-all duration-200"
              >
                Start Free Trial
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  className="transition-transform duration-200 group-hover:translate-x-[3px]">
                  <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
                </svg>
              </a>
              <div className="text-[11px] text-[#64748b]">
                5-minute setup · 14-day free trial · No credit card required
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  )
}
