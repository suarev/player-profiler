'use client'

import { useEffect, useState } from 'react'
import PositionColumn from './PositionColumn'

const positions = [
  {
    name: 'FORWARDS',
    subtitle: 'THE FINISHERS',
    description: 'Goal scorers, creators, and game changers. From clinical finishers to creative false 9s.',
    players: 127,
    profiles: 8,
    colorClass: 'forwards',
    bgImage: '/images/positions/forward.png' // You'll need to add these images
  },
  {
    name: 'MIDFIELDERS',
    subtitle: 'THE ORCHESTRATORS',
    description: 'Controllers of tempo and space. Deep playmakers to box-to-box engines.',
    players: 234,
    profiles: 12,
    colorClass: 'midfielders',
    bgImage: '/images/positions/midfielder.png'
  },
  {
    name: 'DEFENDERS',
    subtitle: 'THE GUARDIANS',
    description: 'Last line of defense and first line of attack. Ball-playing CBs to marauding fullbacks.',
    players: 198,
    profiles: 10,
    colorClass: 'defenders',
    bgImage: '/images/positions/defender.png'
  },
  {
    name: 'GOALKEEPERS',
    subtitle: 'THE LAST STAND',
    description: 'Shot-stoppers and sweeper-keepers. The foundation of defensive security.',
    players: 47,
    profiles: 5,
    colorClass: 'goalkeepers',
    bgImage: '/images/positions/goalkeeper.png'
  }
]

export default function PositionsSection() {
  const [showTitle, setShowTitle] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowTitle(false)
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <section id="positions" className="positions-page">
      {/* Header */}
      <header className="positions-header">
        <button onClick={scrollToTop} className="back-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          BACK TO HOME
        </button>
        <div className="page-indicator">STEP 01 / 03</div>
      </header>

      {/* Page Title (shows initially, then fades) */}
      <div className={`page-title ${!showTitle ? 'fade-out' : ''}`}>
        <h1>SELECT YOUR POSITION</h1>
        <p>Choose a position to explore player profiles</p>
      </div>

      {/* Positions Container */}
      <div className="positions-container">
        {positions.map((position, index) => (
          <PositionColumn
            key={position.name}
            position={position}
            index={index}
          />
        ))}
      </div>
    </section>
  )
}