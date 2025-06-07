'use client'

import { useRouter } from 'next/navigation'

interface PositionProps {
  position: {
    name: string
    subtitle: string
    description: string
    players: number
    profiles: number
    colorClass: string
    bgImage: string
  }
  index: number
}

export default function PositionColumn({ position, index }: PositionProps) {
  const router = useRouter()

  const handleClick = () => {
    // Navigate to the analysis page for this position
    router.push(`/analysis/${position.name.toLowerCase()}`)
  }

  return (
    <div 
      className={`position-column ${position.colorClass}`} 
      onClick={handleClick}
      style={{ animationDelay: `${0.1 + index * 0.1}s` }}
    >
      <div 
        className="player-bg" 
        style={{ 
          backgroundImage: position.bgImage ? `url(${position.bgImage})` : 
            `url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 600"><rect fill="%23222" width="400" height="600"/><text x="200" y="300" text-anchor="middle" fill="%23444" font-size="20">${position.name} IMAGE</text></svg>')`
        }} 
      />
      <div className="overlay" />
      <div className="position-content">
        <h2 className="position-name">{position.name}</h2>
        <p className="position-subtitle">{position.subtitle}</p>
        <div className="position-description">
          <p className="description-text">
            {position.description}
          </p>
        </div>
        <div className="position-stats">
          <div className="stat">
            <div className="stat-value">{position.players}</div>
            <div className="stat-label">PLAYERS</div>
          </div>
          <div className="stat">
            <div className="stat-value">{position.profiles}</div>
            <div className="stat-label">PROFILES</div>
          </div>
        </div>
        <div className="enter-arrow">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14m-7-7l7 7-7 7" strokeWidth="1.5" stroke="currentColor"/>
          </svg>
        </div>
      </div>
    </div>
  )
}