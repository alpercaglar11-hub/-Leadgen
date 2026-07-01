import { useEffect } from 'react'
import Lenis from 'lenis'
import Header from './components/Header'
import Hero from './components/Hero'
import Product from './components/Product'
import ROI from './components/ROI'
import CaseStudy from './components/CaseStudy'
import Pricing from './components/Pricing'
import CTA from './components/CTA'
import Footer from './components/Footer'
import ScrollReveal from './components/ScrollReveal'
import { LazyMotion, domMax } from 'framer-motion'

export default function App() {
  useEffect(() => {
    const lenis = new Lenis({ duration: 1.2, easing: t => Math.min(1, 1.001 - 2 ** (-10 * t)), smoothWheel: true, wheelMultiplier: 0.7 })
    function raf(time: number) { lenis.raf(time); requestAnimationFrame(raf) }
    requestAnimationFrame(raf)
    return () => lenis.destroy()
  }, [])

  return (
    <LazyMotion features={domMax}>
      <a href="#main" className="skip-link">Skip to main content</a>
      <Header />
      <main id="main" className="relative z-10" tabIndex={-1}>
        <Hero />
        <ScrollReveal><Product /></ScrollReveal>
        <ScrollReveal><ROI /></ScrollReveal>
        <ScrollReveal><CaseStudy /></ScrollReveal>
        <ScrollReveal><Pricing /></ScrollReveal>
        <CTA />
      </main>
      <Footer />
    </LazyMotion>
  )
}
