import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

export default function ScrollReveal({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ type: 'spring', stiffness: 120, damping: 22, mass: 0.9 }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
