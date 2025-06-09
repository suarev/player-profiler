// Types for the analysis page

export interface ForwardMetrics {
  id: string
  name: string
  description: string
  stat_columns: string[]
}

export interface MetricWeight {
  metric: string
  weight: number
}

export interface PlayerRecommendation {
  player_id: number
  name: string
  team: string
  position: string
  match_score: number
  key_stats: {
    goals: number
    'xG/90': number
    'shots/90': number
    assists: number
  }
  percentile_ranks: Record<string, number>
}

export interface RecommendationResponse {
  algorithm_used: string
  recommendations: PlayerRecommendation[]
}

export interface Algorithm {
  id: string
  name: string
  description: string
}

export interface PCAPoint {
  player_id: number
  name: string
  team: string
  x: number
  y: number
  cluster?: string
}

export interface PCAData {
  points: PCAPoint[]
  explained_variance: number[]
}