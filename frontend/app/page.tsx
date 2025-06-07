'use client'

import { useEffect, useState } from 'react'
import CustomCursor from './components/ui/CustomCursor'
import FilmGrain from './components/ui/FilmGrain'
import Navigation from './components/ui/Navigation'
import StadiumBackground from './components/home/StadiumBackground'
import HeroSection from './components/home/HeroSection'
import PositionsSection from './components/positions/PositIonsSection'

export default function HomePage() {
  const [scrolled, setScrolled] = useState(false)
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY
      setScrollY(scrollPosition)
      setScrolled(scrollPosition > window.innerHeight * 0.5)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <>
      {/* Custom Cursor */}
      <CustomCursor />

      {/* Film Grain Effect */}
      <FilmGrain />

      {/* Home Section */}
      <div 
        className="home-section"
        style={{
          transform: `translateY(${scrollY * 0.5}px)`,
          opacity: 1 - (scrollY / (typeof window !== 'undefined' ? window.innerHeight * 0.8 : 1000))
        }}
      >
        {/* Stadium Background */}
        <StadiumBackground />

        {/* Navigation - Hide when scrolled */}
        <div className={`nav-wrapper ${scrolled ? 'hidden' : ''}`}>
          <Navigation />
        </div>

        {/* Main Container */}
        <HeroSection />

        {/* Enhanced Scroll Prompt */}
        <div className="scroll-prompt" onClick={() => document.getElementById('positions')?.scrollIntoView({ behavior: 'smooth' })}>
          <span className="scroll-text">SCROLL TO START ANALYSIS</span>
          <div className="scroll-indicator">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </div>
        </div>

        {/* Version */}
        <div className="version">V1.0 BETA</div>
      </div>

      {/* Positions Section */}
      <PositionsSection scrolled={scrolled} />
    </>
  )
}