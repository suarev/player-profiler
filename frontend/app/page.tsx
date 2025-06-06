'use client'

import CustomCursor from './components/ui/CustomCursor'
import FilmGrain from './components/ui/FilmGrain'
import Navigation from './components/ui/Navigation'
import StadiumBackground from './components/home/StadiumBackground'
import HeroSection from './components/home/HeroSection'

export default function HomePage() {
  return (
    <>
      {/* Custom Cursor */}
      <CustomCursor />

      {/* Film Grain Effect */}
      <FilmGrain />

      {/* Stadium Background */}
      <StadiumBackground />

      {/* Navigation */}
      <Navigation />

      {/* Main Container */}
      <HeroSection />

      {/* Scroll Indicator */}
      <div className="scroll-indicator">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>

      {/* Version */}
      <div className="version">V1.0 BETA</div>
    </>
  )
}