import React from 'react'

interface HorizontalPlayerCardProps {
  player: {
    player_id: number
    name: string
    team: string
    position: string
    match_score: number
    rank: number
    age?: number
    nationality?: string
    image_url?: string
    key_stats: Record<string, number>
    percentiles?: Record<string, number>
  }
  isExpanded: boolean
  onHover: () => void
  onLeave: () => void
}

export default function HorizontalPlayerCard({ 
  player, 
  isExpanded, 
  onHover, 
  onLeave 
}: HorizontalPlayerCardProps) {
  // Helper function to format stat labels
  const formatStatLabel = (key: string): string => {
    const labelMap: Record<string, string> = {
      goals: 'Goals',
      xG: 'xG',
      shots: 'Shots',
      assists: 'Assists',
      passes: 'Pass %',
      key_passes: 'Key Pass',
      prog_carries: 'Prog Carry',
      tackles: 'Tackles',
      interceptions: 'Int',
      aerial_won: 'Aerial %',
      prog_passes: 'Prog Pass',
      save_pct: 'Save %',
      saves: 'Saves',
      clean_sheets: 'Clean Sheets',
      goals_against: 'GA'
    }
    return labelMap[key] || key
  }

  // Helper function to format radar labels
  const formatRadarLabel = (key: string): string => {
    // Remove _pct suffix and format
    const cleanKey = key.replace('_pct', '')
    const parts = cleanKey.split('_')
    
    // Take first 2-3 parts and capitalize
    return parts.slice(0, 2)
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ')
      .substring(0, 10) // Limit length for radar chart
  }

  // Mini stat dots for collapsed view - generic approach
  const getTopStats = () => {
    const percentileKeys = Object.keys(player.percentiles || {})
      .filter(key => !key.includes('_pct'))
      .slice(0, 4)
    
    return percentileKeys.map(key => ({
      value: player.percentiles?.[key] || 50,
      label: key.substring(0, 3).toUpperCase()
    }))
  }

  const topStats = getTopStats()

  // Get position-specific radar metrics
  const getRadarMetrics = () => {
    // Extract all percentile keys that end with _pct
    const percentileKeys = Object.keys(player.percentiles || {})
      .filter(key => key.endsWith('_pct'))
      .slice(0, 10) // Take first 10 metrics
    
    return percentileKeys.map(key => ({
      key: key,
      label: formatRadarLabel(key),
      value: player.percentiles?.[key as keyof typeof player.percentiles] || 50
    }))
  }

  const radarMetrics = getRadarMetrics()

  // Calculate radar points for expanded view
  const centerX = 120
  const centerY = 120
  const radius = 100
  const angleStep = (2 * Math.PI) / radarMetrics.length

  const getPoint = (value: number, index: number) => {
    const angle = index * angleStep - Math.PI / 2
    const r = (value / 100) * radius
    return {
      x: centerX + r * Math.cos(angle),
      y: centerY + r * Math.sin(angle)
    }
  }

  const radarPoints = radarMetrics.map((metric, i) => getPoint(metric.value, i))
  const radarPath = `M ${radarPoints.map(p => `${p.x},${p.y}`).join(' L ')} Z`

  return (
    <div 
      className={`horizontal-player-card ${isExpanded ? 'expanded' : ''}`}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
    >
      {/* Always visible content */}
      <div className="card-preview">
        <div className="rank-badge">{player.rank}</div>
        
        <div className="player-photo-small">
          {player.image_url ? (
            <div className="photo-wrapper">
              <img 
                src={player.image_url} 
                alt={player.name}
                onError={(e) => {
                  // Fallback to placeholder on error
                  e.currentTarget.style.display = 'none'
                  e.currentTarget.nextElementSibling?.classList.remove('hidden')
                }}
              />
              <div className="photo-placeholder-small hidden">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/>
                </svg>
              </div>
            </div>
          ) : (
            <div className="photo-placeholder-small">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/>
              </svg>
            </div>
          )}
        </div>

        <div className="player-basic-info">
          <h3 className="player-name">{player.name}</h3>
          <p className="player-team-pos">{player.team} • {player.position}</p>
        </div>

        {/* Mini stats */}
        <div className="mini-stats">
          {topStats.map((stat, i) => (
            <div key={i} className="mini-stat-item">
              <div className="mini-stat-hover-value">{stat.value.toFixed(0)}</div>
              <div className="mini-stat-bar">
                <div 
                  className="mini-stat-fill" 
                  style={{ height: `${stat.value}%` }}
                />
              </div>
              <span className="mini-stat-label">{stat.label}</span>
            </div>
          ))}
        </div>

        <div className="match-score-display">
          <div className="score-number">{player.match_score.toFixed(0)}</div>
          <div className="score-text">MATCH</div>
        </div>

        {/* Animated light bar */}
        <div className="horizontal-light-sweep" />
      </div>

      {/* Expandable content */}
      <div className={`card-expanded-content ${isExpanded ? 'show' : ''}`}>
        <div className="expanded-stats-grid">
          {/* Key stats */}
          <div className="key-stats-section">
            <h4 className="section-title">KEY STATS</h4>
            <div className="key-stats-grid">
              {Object.entries(player.key_stats).slice(0, 4).map(([key, value]) => (
                <div key={key} className="key-stat">
                  <span className="stat-value">
                    {typeof value === 'number' ? 
                      (value % 1 === 0 ? value : value.toFixed(1)) : 
                      value
                    }
                  </span>
                  <span className="stat-label">{formatStatLabel(key)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Radar chart */}
          <div className="radar-chart-section">
            <h4 className="section-title">PLAYER PROFILE</h4>
            <svg viewBox="0 0 240 240" className="radar-chart-small">
              {/* Grid circles */}
              {[20, 40, 60, 80, 100].map(r => (
                <circle
                  key={r}
                  cx={centerX}
                  cy={centerY}
                  r={(r / 100) * radius}
                  fill="none"
                  stroke="rgba(255, 255, 255, 0.1)"
                  strokeWidth="0.5"
                />
              ))}

              {/* Grid lines */}
              {radarMetrics.map((_, i) => {
                const angle = i * angleStep - Math.PI / 2
                const x2 = centerX + radius * Math.cos(angle)
                const y2 = centerY + radius * Math.sin(angle)
                return (
                  <line
                    key={i}
                    x1={centerX}
                    y1={centerY}
                    x2={x2}
                    y2={y2}
                    stroke="rgba(255, 255, 255, 0.1)"
                    strokeWidth="0.5"
                  />
                )
              })}

              {/* Radar shape */}
              <path
                d={radarPath}
                fill="rgba(255, 107, 107, 0.2)"
                stroke="var(--position-color)"
                strokeWidth="2"
              />

              {/* Points with hover */}
              {radarPoints.map((point, i) => (
                <g key={i} className="radar-point-group">
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill="var(--position-color)"
                    className="radar-point"
                    style={{ cursor: 'pointer' }}
                  />
                  {/* Hover value */}
                  <text
                    x={point.x}
                    y={point.y - 10}
                    textAnchor="middle"
                    className="radar-hover-value"
                    fill="white"
                    fontSize="11"
                    fontWeight="600"
                    style={{
                      opacity: 0,
                      transition: 'opacity 0.2s ease',
                      pointerEvents: 'none',
                      filter: 'drop-shadow(0 0 3px rgba(0,0,0,0.8))'
                    }}
                  >
                    {radarMetrics[i].value.toFixed(0)}
                  </text>
                </g>
              ))}

              {/* Labels */}
              {radarMetrics.map((metric, i) => {
                const angle = i * angleStep - Math.PI / 2
                const labelRadius = radius + 15
                const x = centerX + labelRadius * Math.cos(angle)
                const y = centerY + labelRadius * Math.sin(angle)
                return (
                  <text
                    key={i}
                    x={x}
                    y={y}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    className="radar-label-small"
                  >
                    {metric.label}
                  </text>
                )
              })}
            </svg>
          </div>

          {/* Additional info */}
          <div className="player-details-section">
            <h4 className="section-title">DETAILS</h4>
            <div className="detail-items">
              <div className="detail-item">
                <span className="detail-label">AGE</span>
                <span className="detail-value">{player.age || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">NAT</span>
                <span className="detail-value">{player.nationality || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}