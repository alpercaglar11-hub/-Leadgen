/**
 * LeadGen — Motion Configuration
 *
 * Single source of truth for all animation physics.
 * Every component imports from here.
 *
 * Philosophy:
 * - Springs only. No cubic-bezier for motion (only for opacity).
 * - Gentle (stiffness 80–120) for reveals and entrances.
 * - Expressive (stiffness 200–300) for interactions.
 * - Snappy (stiffness 400+) for micro-interactions.
 * - Mass > 1 = slower, heavier feel.
 * - Damping ~20 = no bounce. 15 = slight overshoot.
 */

/* ── Spring presets ── */

/** Heavy, slow — for full-section reveals */
export const gentle = {
  type: 'spring' as const,
  stiffness: 80,
  damping: 22,
  mass: 1.2,
}

/** Standard reveal — for individual elements appearing */
export const reveal = {
  type: 'spring' as const,
  stiffness: 120,
  damping: 20,
  mass: 0.9,
}

/** Tighter — for staggered children */
export const stagger = {
  type: 'spring' as const,
  stiffness: 160,
  damping: 22,
  mass: 0.7,
}

/** Quick snap — for small UI elements, badges */
export const snap = {
  type: 'spring' as const,
  stiffness: 300,
  damping: 24,
}

/** Interaction — for hover/tap/feedback */
export const interactive = {
  type: 'spring' as const,
  stiffness: 400,
  damping: 18,
}

/** Magnetic follow — for cursor-aware movement */
export const magnetic = {
  type: 'spring' as const,
  stiffness: 500,
  damping: 14,
}

/** Layout animation — for shared element transitions */
export const layout = {
  type: 'spring' as const,
  stiffness: 380,
  damping: 30,
}

/* ── Timing (for opacity-only transitions) ── */
export const fadeIn = {
  duration: 0.8,
  ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
}

/* ── Viewport margin (standardised) ── */
export const VIEWPORT_MARGIN = '-80px'
