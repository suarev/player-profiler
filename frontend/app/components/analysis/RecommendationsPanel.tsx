import { PlayerRecommendation } from '@/app/types/analysis'

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
  
  // Show skeleton while loading (only for primary variant)
  if (loading && variant === 'primary') {
    return (
      <div className="recommendations-panel">
        <h2 className="panel-title">TOP MATCHES</h2>
        <div className="player-cards">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="player-card skeleton">
              <div className="player-rank">{i}</div>
              <div className="player-info">
                <div className="skeleton-line" style={{ width: '150px', height: '24px' }} />
                <div className="skeleton-line" style={{ width: '100px', height: '16px', marginTop: '8px' }} />
                <div className="player-stats">
                  <div className="skeleton-line" style={{ width: '60px', height: '20px' }} />
                  <div className="skeleton-line" style={{ width: '60px', height: '20px' }} />
                  <div className="skeleton-line" style={{ width: '60px', height: '20px' }} />
                </div>
              </div>
              <div className="match-score">
                <div className="skeleton-line" style={{ width: '60px', height: '36px' }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Secondary variant - more compact
  if (variant === 'secondary') {
    return (
      <div className="secondary-player-cards">
        {recommendations.map((player, index) => (
          <div key={player.player_id} className="secondary-player-card">
            <div className="secondary-rank">{index + 6}</div>
            <div className="secondary-player-info">
              <h4>{player.name}</h4>
              <span className="secondary-team">{player.team}</span>
            </div>
            <div className="secondary-score">
             <span className="secondary-score-value">{player.match_score.toFixed(1)}</span>
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Primary variant - full details
  return (
    <div className="recommendations-panel">
      <h2 className="panel-title">TOP MATCHES</h2>
      <div className="player-cards">
        {recommendations.map((player, index) => (
          <div key={player.player_id} className="player-card">
            <div className="player-rank">{index + 1}</div>
            <div className="player-info">
              <h3>{player.name}</h3>
              <p className="player-team">{player.team}</p>
              <div className="player-stats">
                <div className="mini-stat">
                  <span className="mini-stat-value">{player.key_stats.goals}</span>
                  <span className="mini-stat-label">goals</span>
                </div>
                <div className="mini-stat">
                  <span className="mini-stat-value">{player.key_stats['xG/90'].toFixed(2)}</span>
                  <span className="mini-stat-label">xG/90</span>
                </div>
                <div className="mini-stat">
                  <span className="mini-stat-value">{player.key_stats['shots/90'].toFixed(1)}</span>
                  <span className="mini-stat-label">shots/90</span>
                </div>
              </div>
            </div>
            <div className="match-score">
              <div className="score-value">{player.match_score.toFixed(1)}</div>
              <div className="score-label">MATCH</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}