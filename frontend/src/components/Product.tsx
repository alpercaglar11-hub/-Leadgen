import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const STEPS = [
  { n: '01', title: 'Searches the web.', text: 'Launches a real browser session, navigates Google, filters results by your ICP. Finds prospects no one else does.', metric: '47 companies per query', v: 'search' },
  { n: '02', title: 'Scores every lead.', text: 'Every company ranked against your ideal customer profile. Low matches discarded. Only qualified leads enter the pipeline.', metric: '91% scoring accuracy', v: 'score' },
  { n: '03', title: 'Writes personalized emails.', text: 'Reads each website, understands their business, generates messaging that references their actual work. No templates.', metric: '3.2× industry reply rate', v: 'email' },
  { n: '04', title: 'Observes and adapts.', text: 'Detects replies, schedules follow-ups, updates pipeline. The agent learns what works and gets better over time.', metric: '34% average reply rate', v: 'observe' },
]

function Visual({ v }: { v: string }) {
  return (
    <div className="rounded-xl bg-[rgba(255,255,255,0.015)] border border-[rgba(255,255,255,0.04)] p-6 min-h-[180px] flex items-center">
      {v === 'search' && (
        <div className="space-y-2.5 w-full">
          <div className="text-[11px] font-mono text-[#64748b]"><span className="text-[rgba(74,222,128,0.6)]">●</span> google.com/search?q=digital+agencies+Berlin+SaaS</div>
          {['CannyBuild GmbH · Series A', 'NexusAI · Series B', 'BrightStudio · Bootstrapped', 'CloudScale · Series A', 'GrowthLab · Seed'].map((r, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-[rgba(148,163,184,0.8)] pl-4 border-l border-[rgba(99,102,241,0.1)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[rgba(99,102,241,0.3)]" />{r}
            </div>
          ))}
        </div>
      )}
      {v === 'score' && (
        <div className="space-y-3 w-full">
          {[{ n: 'CannyBuild', s: 94, m: 'high' }, { n: 'NexusAI', s: 91, m: 'high' }, { n: 'BrightStudio', s: 72, m: 'medium' }, { n: 'CloudScale', s: 88, m: 'high' }].map(r => (
            <div key={r.n} className="flex items-center gap-3 text-sm">
              <span className="w-24 text-[#cbd5e1]">{r.n}</span>
              <div className="flex-1 h-1.5 rounded-full bg-[rgba(255,255,255,0.04)] overflow-hidden">
                <div className="h-full rounded-full bg-[rgba(99,102,241,0.5)]" style={{ width: `${r.s}%` }} />
              </div>
              <span className="w-8 text-right font-mono text-xs text-[#94a3b8]">{r.s}</span>
              <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${r.m === 'high' ? 'text-[rgba(74,222,128,0.6)] bg-[rgba(74,222,128,0.05)]' : 'text-[rgba(251,191,36,0.6)] bg-[rgba(251,191,36,0.05)]'}`}>{r.m}</span>
            </div>
          ))}
        </div>
      )}
      {v === 'email' && (
        <div className="space-y-2.5 w-full">
          <div className="text-[11px] font-mono text-[#64748b]">✉ Draft — CannyBuild GmbH</div>
          <div className="p-3.5 rounded-lg bg-[rgba(0,0,0,0.2)] border border-[rgba(255,255,255,0.04)] text-sm text-[#94a3b8] leading-relaxed">
            <div className="text-[#64748b] mb-1.5 font-mono text-[11px]">To: founders@cannybuild.com</div>
            <p className="text-[#cbd5e1]">Hi Marcus, came across CannyBuild&rsquo;s Series A and your expansion into enterprise construction software. We help companies like yours connect with qualified leads...</p>
          </div>
        </div>
      )}
      {v === 'observe' && (
        <div className="space-y-3 w-full">
          <div className="flex gap-3 mb-2">
            {[{ l: 'Sent', c: 34 }, { l: 'Opened', c: 16 }, { l: 'Replied', c: 12, a: true }].map(s => (
              <div key={s.l} className={`flex-1 p-3 rounded-lg text-center text-xs font-mono ${s.a ? 'bg-[rgba(99,102,241,0.1)] border border-[rgba(99,102,241,0.15)] text-[#818cf8]' : 'bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.04)] text-[#94a3b8]'}`}>
                <div className="text-lg font-semibold mb-1">{s.c}</div>{s.l}
              </div>
            ))}
          </div>
          <div className="text-[11px] font-mono text-[#64748b] text-center pt-1">Last reply: 12m ago · Follow-up #2 in 24h</div>
        </div>
      )}
    </div>
  )
}

function StepRow({ step, i, total }: { step: typeof STEPS[0]; i: number; total: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ type: 'spring', stiffness: 160, damping: 22, delay: 0.05 + i * 0.06 }}
      className="py-8 md:py-10 border-t border-[rgba(255,255,255,0.04)] last:border-b">
      <div className="grid md:grid-cols-2 gap-6 md:gap-10 items-start">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-[#64748b]">{step.n}</span>
            <div className="flex-1 h-px bg-[rgba(255,255,255,0.04)]" />
            <span className="text-[10px] font-mono text-[#475569]">{i + 1}/{total}</span>
          </div>
          <h3 className="text-lg md:text-xl font-semibold text-white tracking-tight">{step.title}</h3>
          <p className="text-sm md:text-base text-[#94a3b8] leading-relaxed text-pretty">{step.text}</p>
          <div className="text-[11px] font-mono text-[rgba(99,102,241,0.5)]">{step.metric}</div>
        </div>
        <Visual v={step.v} />
      </div>
    </motion.div>
  )
}

export default function Product() {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })
  return (
    <section className="section-pad relative" id="product">
      <div className="absolute inset-0 pointer-events-none"><div className="absolute top-1/4 left-0 w-72 h-72 bg-[rgba(99,102,241,0.015)] rounded-full blur-[100px]" /></div>
      <div className="mx-auto max-w-7xl px-6 md:px-10 relative z-10" ref={ref}>
        <div className="max-w-2xl mb-14 md:mb-16">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.05 }}
            className="text-[10px] font-mono text-[#64748b] uppercase tracking-[0.18em] mb-5">How it works</motion.div>
          <motion.h2 initial={{ opacity: 0, y: 24 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 80, damping: 22, delay: 0.08 }}
            className="text-[clamp(1.8rem,4vw,3rem)] font-bold leading-[1.05] tracking-[-0.035em] text-white mb-4">
            Your AI employee works<br />while you sleep.<span className="text-[#94a3b8]"></span></motion.h2>
          <motion.p initial={{ opacity: 0, y: 16 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 0.12 }}
            className="text-base text-[#94a3b8] leading-relaxed text-pretty">You set the target. The agent searches, scores, writes, sends, and follows up. You wake up to replies.</motion.p>
        </div>
        <div className="max-w-4xl">{STEPS.map((s, i) => <StepRow key={s.n} step={s} i={i} total={STEPS.length} />)}</div>
      </div>
    </section>
  )
}
