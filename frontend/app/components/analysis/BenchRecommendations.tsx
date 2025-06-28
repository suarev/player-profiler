import React from 'react'

interface BenchPlayer {
  player_id: number
  name: string
  team: string
  match_score: number
  rank: number
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