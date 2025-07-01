import React from 'react'

interface BenchPlayer {
  player_id: number
  name: string
  team: string
  match_score: number
  rank: number
  image_url?: string
}

interface BenchRecommendationsProps {
  players: BenchPlayer[]
}

export default function BenchRecommendations({ players }: BenchRecommendationsProps) {
  return (
    <div className="bench-container">
      <h3 className="bench-title">ON THE BENCH</h3>
      <div className="bench-grid">
        {players.map((player) => (
          <div key={player.player_id} className="bench-player-card">
            <div className="bench-rank">{player.rank}</div>
            
            {/* Image section with proper wrapper */}
            <div className="bench-player-photo">
              {player.image_url ? (
                <>
                  <img 
                    src={player.image_url} 
                    alt={player.name}
                    onError={(e) => {
                      const img = e.currentTarget;
                      img.style.display = 'none';
                      const placeholder = img.nextElementSibling as HTMLElement;
                      if (placeholder) {
                        placeholder.classList.remove('hidden');
                      }
                    }}
                  />
                  <div className="bench-photo-placeholder hidden">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/>
                    </svg>
                  </div>
                </>
              ) : (
                <div className="bench-photo-placeholder">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/>
                  </svg>
                </div>
              )}
            </div>
            
            <div className="bench-player-info">
              <div className="bench-name">{player.name}</div>
              <div className="bench-team">{player.team}</div>
            </div>
            <div className="bench-score">{player.match_score.toFixed(0)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}