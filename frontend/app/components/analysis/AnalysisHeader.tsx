'use client'

import { useRouter } from 'next/navigation'

interface AnalysisHeaderProps {
  position: string
  playerCount: number
}

export default function AnalysisHeader({ position, playerCount }: AnalysisHeaderProps) {
  const router = useRouter()

  return (
    <header className="analysis-header">
      <div className="header-content">
        <button 
          onClick={() => router.push('/')} 
          className="back-link"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M19 12H5M12 19l-7-7 7-7" strokeWidth="2"/>
          </svg>
          BACK
        </button>
        <div className="position-info">
          <h1 className="position-title">{position}</h1>
          <span className="player-count">{playerCount} PLAYERS ANALYZED</span>
        </div>
      </div>
    </header>
  )
}