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
    photo?: string
    key_stats: {
      goals: number
      xG: number
      shots: number
      assists: number
    }
    percentiles?: {
      finishing: number
      physical: number
      creativity: number
      pace_dribbling: number
      work_rate: number
      box_presence: number
      // Add these:
      performance_gls_pct?: number
      per_90_minutes_npxg_pct?: number
      standard_sot_pct?: number
      performance_ast_pct?: number
      expected_xag_pct?: number
      kp_pct?: number
      take_ons_succ_pct?: number
      aerial_duels_wonpct_pct?: number
      touches_att_pen_pct?: number
      carries_prgc_pct?: number
    }
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
  // Mini stat dots for collapsed view
// Mini stat dots for collapsed view
// Example: Show different metrics
const topStats = [
  { value: player.percentiles?.finishing || 50, label: 'FIN' },
  { value: player.percentiles?.creativity || 50, label: 'CRE' },
  { value: player.percentiles?.work_rate || 50, label: 'WRK' },
  { value: player.percentiles?.box_presence || 50, label: 'BOX' }
]

  // Full radar chart metrics - ACTUAL METRICS
  const radarMetrics = [
    { key: 'performance_gls_pct', label: 'Goals', value: player.percentiles?.performance_gls_pct || 50 },
    { key: 'P90M_npxg_pct', label: 'xG', value: player.percentiles?.per_90_minutes_npxg_pct || 50 },
    { key: 'standard_sot_pct', label: 'SoT%', value: player.percentiles?.standard_sot_pct || 50 },
    { key: 'performance_ast_pct', label: 'Assists', value: player.percentiles?.performance_ast_pct || 50 },
    { key: 'expected_xag_pct', label: 'xA', value: player.percentiles?.expected_xag_pct || 50 },
    { key: 'kp_pct', label: 'KeyPass', value: player.percentiles?.kp_pct || 50 },
    { key: 'take_ons_succ_pct', label: 'Dribbles', value: player.percentiles?.take_ons_succ_pct || 50 },
    { key: 'aerial_duels_wonpct_pct', label: 'Aerials', value: player.percentiles?.aerial_duels_wonpct_pct || 50 },
    { key: 'touches_att_pen_pct', label: 'BoxTouch', value: player.percentiles?.touches_att_pen_pct || 50 },
    { key: 'carries_prgc_pct', label: 'ProgCarry', value: player.percentiles?.carries_prgc_pct || 50 }
  ]

  // ADD THIS DEBUG CODE - FIXED VERSION
  React.useEffect(() => {
    if (isExpanded) {
      console.log(`\n🎯 RADAR DATA FOR: ${player.name} (${player.team})`)
      console.log('=====================================')
      
      radarMetrics.forEach(metric => {
        // Type-safe way to access the value
        const actualValue = player.percentiles?.[metric.key as keyof typeof player.percentiles]
        const exists = actualValue !== undefined && actualValue !== null
        const displayValue = metric.value
        
        console.log(
          `${metric.label.padEnd(10)} (${metric.key}): ${
            exists 
              ? `✅ ${displayValue.toFixed(1)}` 
              : `❌ MISSING (defaulted to ${displayValue})`
          }`
        )
      })
      
      // Also log all available percentiles
      console.log('\n📊 ALL AVAILABLE PERCENTILES:')
      if (player.percentiles) {
        Object.entries(player.percentiles).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            console.log(`  ${key}: ${value}`)
          }
        })
      } else {
        console.log('  No percentiles object found!')
      }
      console.log('=====================================\n')
    }
  }, [isExpanded, player])
  // Calculate radar points for expanded view
  const centerX = 120  // Increased
  const centerY = 120  // Increased
  const radius = 100   // Increased
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

  // Add hover effect for radar points
// Add hover effect for radar points
React.useEffect(() => {
  if (!isExpanded) return

  const handlePointHover = (e: Event) => {
    const point = e.target as SVGCircleElement
    if (!point.classList.contains('radar-point')) return
    
    const value = point.getAttribute('data-value')
    const tooltip = point.closest('svg')?.querySelector('.radar-tooltip-group') as SVGGElement
    const tooltipBg = tooltip?.querySelector('.tooltip-bg') as SVGRectElement
    const tooltipText = tooltip?.querySelector('.tooltip-text') as SVGTextElement
    
    if (tooltip && tooltipText && tooltipBg && value) {
      const rect = point.getBoundingClientRect()
      const svgRect = point.closest('svg')?.getBoundingClientRect()
      
      if (svgRect) {
        const x = rect.left - svgRect.left + rect.width / 2
        const y = rect.top - svgRect.top - 25
        
        tooltipText.textContent = value
        tooltipText.setAttribute('x', String(x))
        tooltipText.setAttribute('y', String(y))
        
        // Update background
        const bbox = tooltipText.getBBox()
        tooltipBg.setAttribute('x', String(bbox.x - 8))
        tooltipBg.setAttribute('y', String(bbox.y - 4))
        tooltipBg.setAttribute('width', String(bbox.width + 16))
        tooltipBg.setAttribute('height', String(bbox.height + 8))
        
        tooltip.style.display = 'block'
      }
    }
  }

  const handlePointLeave = () => {
    const tooltips = document.querySelectorAll('.radar-tooltip-group')
    tooltips.forEach(t => {
      const tooltip = t as SVGGElement
      tooltip.style.display = 'none'
    })
  }

  const svg = document.querySelector('.expanded .radar-chart-small')
  if (svg) {
    svg.addEventListener('mouseover', handlePointHover as EventListener)
    svg.addEventListener('mouseout', handlePointLeave as EventListener)
    
    return () => {
      svg.removeEventListener('mouseover', handlePointHover as EventListener)
      svg.removeEventListener('mouseout', handlePointLeave as EventListener)
    }
  }
}, [isExpanded])

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
          {player.photo ? (
            <img src={player.photo} alt={player.name} />
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
                <div className="mini-stat-hover-value">{stat.value.toFixed(2)}</div>
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
              <div className="key-stat">
                <span className="stat-value">{player.key_stats.goals}</span>
                <span className="stat-label">Goals</span>
              </div>
              <div className="key-stat">
                <span className="stat-value">{player.key_stats.xG.toFixed(1)}</span>
                <span className="stat-label">xG</span>
              </div>
              <div className="key-stat">
                <span className="stat-value">{player.key_stats.assists}</span>
                <span className="stat-label">Assists</span>
              </div>
              <div className="key-stat">
                <span className="stat-value">{player.key_stats.shots}</span>
                <span className="stat-label">Shots</span>
              </div>
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
              stroke="#ff6b6b"
              strokeWidth="2"
            />

            {/* Points with hover */}
            {radarPoints.map((point, i) => (
              <g key={i} className="radar-point-group">
                <circle
                  cx={point.x}
                  cy={point.y}
                  r="4"
                  fill="#ff6b6b"
                  className="radar-point"
                  style={{ cursor: 'pointer' }}
                />
                {/* Hover value - positioned above the point */}
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
                  {radarMetrics[i].value.toFixed(2)}
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