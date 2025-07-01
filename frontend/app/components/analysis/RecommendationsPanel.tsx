'use client'

import { useEffect, useRef, useState } from 'react'
import { PlayerRecommendation } from '@/app/types/analysis'
import HorizontalPlayerCard from './HorizontalPlayerCard'
import { analysisApi } from '@/app/services/analysisApi'

interface RecommendationsPanelProps {
  recommendations: PlayerRecommendation[]
  loading: boolean
  variant?: 'primary' | 'secondary'
}

export default function RecommendationsPanel({ 
  recommendations, 
  loading, 
  variant = 'primary' 
}: RecommendationsPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number>(0) // Default to first card
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([])
  const lastHoveredRef = useRef<number>(0) // Track last hovered

  useEffect(() => {
    loadAlgorithms()
  }, [])

  const loadAlgorithms = async () => {
    try {
      const data = await analysisApi.getAlgorithms()
      setAlgorithms(data)
    } catch (error) {
      console.error('Failed to load algorithms:', error)
    }
  }
  
  // Show skeleton while loading
  if (loading && variant === 'primary') {
    return (
      <div className="recommendations-panel">
        <h2 className="panel-title">TOP MATCHES</h2>
        <div className="horizontal-cards-container">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="horizontal-player-card">
              <div className="card-preview">
                <div className="rank-badge skeleton-line">{i}</div>
                <div className="player-photo-small skeleton-line" />
                <div className="player-basic-info">
                  <div className="skeleton-line" style={{ width: '150px', height: '20px' }} />
                  <div className="skeleton-line" style={{ width: '100px', height: '16px', marginTop: '4px' }} />
                </div>
                <div className="match-score-display">
                  <div className="skeleton-line" style={{ width: '60px', height: '36px' }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // We don't use secondary variant anymore
  if (variant === 'secondary') {
    return null
  }

  // Primary variant - horizontal expandable cards
  return (
    <div className="recommendations-panel">
      <h2 className="panel-title">TOP MATCHES</h2>
      <div className="horizontal-cards-container">
        {recommendations.map((player, index) => (
          <HorizontalPlayerCard
            key={player.player_id}
            player={{
              ...player,
              rank: index + 1,
              age: 25, // You'll need to add this from your data
              nationality: 'N/A', // You'll need to add this from your data
              photo: undefined, // Add when you have photo URLs
              percentiles: player.percentile_ranks as any
            }}
            isExpanded={expandedIndex === index}
            onHover={() => {
              setExpandedIndex(index)
              lastHoveredRef.current = index
            }}
            onLeave={() => {
              // Don't collapse - keep the last hovered one expanded
              // The expandedIndex stays as is
            }}
          />
        ))}
      </div>
    </div>
  )
}