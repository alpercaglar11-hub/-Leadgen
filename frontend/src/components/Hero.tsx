import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import DemoOverlay from './DemoOverlay'

// ── Stream variant pools for natural variation ────────────────────

const SEARCH_POOL = [
  { t: 'google.com', d: 'query: B2B SaaS founders Europe' },
  { t: 'google.com', d: 'query: digital agencies Berlin Series A' },
  { t: 'google.com', d: 'query: fintech startups London' },
  { t: 'google.com', d: 'query: enterprise SaaS Paris' },
]

const VISIT_POOL = [
  { t: 'cannybuild.io', d: '200 OK · 1.2s · homepage scanned' },
  { t: 'nexusai.eu', d: '200 OK · 0.9s · 14 pages indexed' },
  { t: 'brightstudio.de', d: '200 OK · 1.6s · team page found' },
  { t: 'cloudscale.dev', d: '200 OK · 0.8s · about page scanned' },
  { t: 'growthlab.se', d: '200 OK · 2.1s · contact found' },
  { t: 'prismventures.io', d: '200 OK · 1.1s · careers scanned' },
  { t: 'datacore.tech', d: '200 OK · 1.4s · leadership identified' },
  { t: 'meridian.agency', d: '200 OK · 0.7s · pricing found' },
]

const EXTRACT_POOL = [
  { t: 'CEO email', d: 'marcus@cannybuild.io · confidence 94%' },
  { t: 'founder name', d: 'Elena Vogt · co-founder, CRO' },
  { t: 'tech stack', d: 'React · Node.js · PostgreSQL · AWS' },
  { t: 'funding', d: '€4.2M Series A · 2025' },
  { t: 'team size', d: '18 employees · 3 open roles' },
  { t: 'email', d: 'anna@nexusai.eu · verified' },
]

const SCORE_RESULTS = [
  { t: 'Acme Corp', d: '94% match · ICP fit: strong', s: 94 },
  { t: 'NexusAI', d: '91% match · ICP fit: strong', s: 91 },
  { t: 'BrightStudio', d: '72% match · ICP fit: medium', s: 72 },
  { t: 'CloudScale', d: '88% match · ICP fit: strong', s: 88 },
]

const EMAIL_POOL = [
  { to: 'marcus@cannybuild.io', line: 'Hi Marcus — came across your Series A and expansion into enterprise...' },
  { to: 'anna@nexusai.eu', line: 'Hey Anna — noticed NexusAI is expanding into the German market. We help...' },
  { to: 'lars@cloudscale.dev', line: 'Hi Lars — CloudScale caught my attention. We help infrastructure...' },
]

const OUTCOME_POOL = [
  { t: 'REPLY', d: 'positive · interested in demo' },
  { t: 'REPLY', d: "let's talk next week · sent calendar" },
  { t: 'MEETING', d: 'booked · 30 min · Thursday 2pm' },
  { t: 'PIPELINE', d: '3 active · 1 qualified · $240K potential' },
]

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function pickButNot<T>(arr: T[], notIdx: number): T {
  let idx: number
  do { idx = Math.floor(Math.random() * arr.length) } while (idx === notIdx && arr.length > 1)
  return arr[idx]
}

interface EventDef {
  action: string
  target: string
  detail: string
  thinkMs: number
}

function generateCycle(): EventDef[] {
  const s = pick(SEARCH_POOL)
  const v1 = pick(VISIT_POOL)
  let v2 = pickButNot(VISIT_POOL, VISIT_POOL.indexOf(v1))
  const e1 = pick(EXTRACT_POOL)
  let e2 = pickButNot(EXTRACT_POOL, EXTRACT_POOL.indexOf(e1))
  const em = pick(EMAIL_POOL)
  const oc = pick(OUTCOME_POOL)
  const scoreResult = pick(SCORE_RESULTS)

  return [
    { action: 'SEARCH', target: s.t, detail: s.d, thinkMs: 300 + Math.random() * 200 },
    { action: 'PARSE', target: '47 results', detail: '3 dupes removed · 44 unique', thinkMs: 250 + Math.random() * 150 },
    { action: 'FILTER', target: 'by ICP', detail: 'stage: Series A+ · location: EU · revenue: €2M+', thinkMs: 400 + Math.random() * 300 },
    { action: 'FETCH', target: v1.t, detail: v1.d, thinkMs: 900 + Math.random() * 400 },
    { action: 'EXTRACT', target: e1.t, detail: e1.d, thinkMs: 600 + Math.random() * 300 },
    { action: 'FETCH', target: v2.t, detail: v2.d, thinkMs: 800 + Math.random() * 500 },
    { action: 'EXTRACT', target: e2.t, detail: e2.d, thinkMs: 500 + Math.random() * 300 },
    { action: 'SCORE', target: scoreResult.t, detail: scoreResult.d, thinkMs: 700 + Math.random() * 300 },
    { action: 'COMPOSE', target: em.to, detail: '142 words · personalized · context-aware', thinkMs: 1200 + Math.random() * 400 },
    { action: 'REVIEW', target: 'tone check', detail: 'confident · warm · concise · score: 92%', thinkMs: 600 + Math.random() * 200 },
    { action: 'SEND', target: 'SendGrid', detail: 'delivered · tracking enabled', thinkMs: 400 + Math.random() * 200 },
    { action: 'WAIT', target: '⏳', detail: 'follow-up scheduled in 48h', thinkMs: 300 + Math.random() * 100 },
    { action: 'RECEIVE', target: 'inbox', detail: oc.d, thinkMs: 1000 + Math.random() * 500 },
    { action: 'SYNC', target: 'pipeline', detail: oc.d === 'booked · 30 min · Thursday 2pm' ? 'meeting synced to calendar' : 'lead moved to qualified', thinkMs: 400 + Math.random() * 200 },
  ]
}

function useCycle() {
  const [visible, setVisible] = useState<number[]>([])
  const [thinking, setThinking] = useState<'thinking' | 'composing' | 'analyzing' | 'waiting' | null>(null)
  const [events, setEvents] = useState<EventDef[]>(() => generateCycle())
  const [phase, setPhase] = useState<'idle' | 'running' | 'done'>('idle')
  const [cycle, setCycle] = useState(0)
  const cycleRef = useRef(cycle)
  cycleRef.current = cycle

  const run = useCallback(() => {
    const evts = generateCycle()
    setEvents(evts)
    setVisible([])
    setThinking('thinking')
    setPhase('running')

    let i = 0
    const process = () => {
      if (i >= evts.length) {
        setThinking(null)
        setPhase('done')
        // After completion, wait 8-15s then start next cycle
        setTimeout(() => {
          if (cycleRef.current < 3) {
            setCycle(c => c + 1)
          }
        }, 8000 + Math.random() * 7000)
        return
      }
      const evt = evts[i]
      // Show thinking state based on event type
      if (evt.action === 'COMPOSE') setThinking('composing')
      else if (evt.action === 'FETCH' || evt.action === 'EXTRACT') setThinking('analyzing')
      else if (evt.action === 'WAIT') setThinking('waiting')
      else setThinking('thinking')

      setTimeout(() => {
        setThinking(null)
        setVisible(p => [...p, i])
        i++
        setTimeout(process, 200 + Math.random() * 150)
      }, evt.thinkMs)
    }

    // Small initial delay before first event
    setTimeout(process, 500 + Math.random() * 300)
  }, [])

  useEffect(() => {
    cycleRef.current = cycle
    run()
  }, [cycle, run])

  return { visible, thinking, events, phase }
}

function EventRow({ e, isLast }: { e: EventDef; isLast: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8, filter: 'blur(3px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ type: 'spring', stiffness: 120, damping: 20 }}
    >
      <div className="flex items-start gap-3 py-[6px] group">
        <div
          className={`mt-[5px] w-[6px] h-[6px] rounded-full shrink-0 transition-all duration-300 ${
            isLast
              ? 'bg-[#818cf8] shadow-[0_0_10px_rgba(99,102,241,0.4)]'
              : 'bg-[#475569]'
          }`}
        />
        <span
          className={`text-[11px] font-mono tracking-wider w-20 shrink-0 transition-colors duration-300 ${
            isLast ? 'text-[#818cf8]' : 'text-[#64748b]'
          }`}
        >
          {e.action}
        </span>
        <span
          className={`text-sm font-medium min-w-[120px] truncate transition-colors duration-300 ${
            isLast ? 'text-white' : 'text-[#94a3b8]'
          }`}
        >
          {e.target}
        </span>
        <span className="text-[11px] font-mono text-[#475569] hidden sm:block truncate">{e.detail}</span>
      </div>
    </motion.div>
  )
}

function ThinkingRow({ state }: { state: 'thinking' | 'composing' | 'analyzing' | 'waiting' }) {
  const labels = {
    thinking: 'processing',
    composing: 'composing message',
    analyzing: 'analyzing page',
    waiting: 'waiting for reply',
  }
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-3 py-[6px]"
    >
      <div
        className="mt-[5px] w-[6px] h-[6px] rounded-full bg-[rgba(99,102,241,0.3)]"
        style={{ animation: 'pulse-dot 1.2s ease-in-out infinite' }}
      />
      <span className="text-[11px] font-mono tracking-wider text-[rgba(99,102,241,0.4)] w-20">{state === 'waiting' ? 'WAIT' : 'THINK'}</span>
      <span className="text-sm text-[rgba(255,255,255,0.3)]">
        {labels[state]}
        <span className="inline-flex gap-[2px] ml-1">
          <span className="animate-pulse">.</span>
          <span className="animate-pulse" style={{ animationDelay: '200ms' }}>.</span>
          <span className="animate-pulse" style={{ animationDelay: '400ms' }}>.</span>
        </span>
      </span>
    </motion.div>
  )
}

function Stream() {
  const { visible, thinking, events, phase } = useCycle()

  return (
    <div>
      {events.map((e, i) => (
        <AnimatePresence key={`${e.action}-${i}`}>
          {visible.includes(i) && <EventRow e={e} isLast={i === visible.length - 1} />}
        </AnimatePresence>
      ))}
      <AnimatePresence>
        {thinking && visible.length < events.length && <ThinkingRow state={thinking} />}
      </AnimatePresence>
      {phase === 'done' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex items-center gap-3 py-[6px]"
        >
          <div
            className="w-[6px] h-[6px] rounded-full bg-[rgba(74,222,128,0.2)] shrink-0"
            style={{ animation: 'cursor-blink 1s step-end infinite' }}
          />
          <span className="text-[11px] font-mono text-[rgba(74,222,128,0.3)] tracking-wider w-20">IDLE</span>
          <span className="text-sm text-[rgba(255,255,255,0.25)]">scanning for new leads — next cycle in a few seconds</span>
        </motion.div>
      )}
    </div>
  )
}

export default function Hero() {
  const [showDemo, setShowDemo] = useState(false)
  return (
    <>
    <section className="relative min-h-dvh flex items-center overflow-hidden pt-20 pb-16 md:pt-24" id="hero">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_50%_-10%,rgba(99,102,241,0.04),transparent)]" />
        <div className="absolute bottom-0 left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-[rgba(99,102,241,0.08)] to-transparent" />
      </div>

      <div className="mx-auto max-w-7xl px-6 md:px-10 w-full relative z-10">
        <div className="grid lg:grid-cols-12 gap-10 lg:gap-16 items-start">
          <div className="lg:col-span-5 pt-8 md:pt-12 space-y-5">
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 80, damping: 22, mass: 1.2 }}
              className="text-[clamp(2.4rem,5.5vw,4.2rem)] font-bold leading-[1.02] tracking-[-0.035em] text-white"
            >
              I'll find you 100 qualified leads<br />while you sleep.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.08 }}
              className="text-base md:text-lg text-[#94a3b8] leading-relaxed max-w-md text-balance"
            >
              Set a target. The agent does the rest. You just take the meetings.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.16 }}
              className="flex flex-wrap gap-3 pt-4"
            >
              <a
                href="/subscribe"
                className="group relative inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium text-white no-underline border border-[rgba(255,255,255,0.2)] hover:border-white/40 hover:bg-[rgba(255,255,255,0.02)] active:scale-[0.97] transition-all duration-200"
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
              <button
                onClick={() => setShowDemo(true)}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium text-[#94a3b8] hover:text-white no-underline transition-colors duration-200 group cursor-pointer bg-transparent border-none"
              >
                <span
                  className="w-2 h-2 rounded-full bg-[#4ade80]"
                  style={{ animation: 'status-pulse 2.5s ease-in-out infinite' }}
                />
                Watch it work
              </button>
            </motion.div>

            {/* ── Trust indicators ── */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.6 }}
              className="flex flex-wrap items-center gap-x-5 gap-y-2 pt-8 text-[11px] font-mono text-[#475569]"
            >
              <span className="text-[#64748b] font-medium text-[10px] uppercase tracking-[0.1em]">Infrastructure</span>
              <span className="flex items-center gap-1.5"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[#64748b]"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/></svg>Stripe</span>
              <span className="flex items-center gap-1.5"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[#64748b]"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 7L2 7"/></svg>SendGrid</span>
              <span className="flex items-center gap-1.5"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[#64748b]"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>Chrome</span>
            </motion.div>
          </div>

          {/* ── Right: Live Agent Workspace ── */}
          <div className="lg:col-span-7 relative">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.2 }}
              className="relative"
            >
              {/* System status */}
              <div className="flex flex-wrap items-center gap-x-6 gap-y-1 mb-5 pb-4 border-b border-[rgba(255,255,255,0.04)]">
                <span className="flex items-center gap-2 text-[11px] font-mono text-[#64748b]">
                  <span
                    className="w-[6px] h-[6px] rounded-full bg-[#4ade80]"
                    style={{ animation: 'status-pulse 2.5s ease-in-out infinite' }}
                  />
                  Running · 24/7
                </span>
                <span className="text-[11px] font-mono text-[#64748b]">
                  <span className="text-[#475569]">●</span> Reply rate:{' '}
                  <span className="text-[#94a3b8]">34%</span>
                </span>
                <span className="text-[11px] font-mono text-[#64748b]">
                  <span className="text-[#475569]">●</span> Uptime:{' '}
                  <span className="text-[#94a3b8]">99.7%</span>
                </span>
              </div>

              <Stream />

              <div className="absolute -top-10 -right-20 -z-10 w-72 h-72 bg-[rgba(99,102,241,0.025)] rounded-full blur-[100px]" />
            </motion.div>
          </div>
        </div>
      </div>
    </section>
      <AnimatePresence>{showDemo && <DemoOverlay onClose={() => setShowDemo(false)} />}</AnimatePresence>
    </>
  )
}
