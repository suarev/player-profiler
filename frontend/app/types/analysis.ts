// frontend/app/types/analysis.ts

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
    xG: number
    shots: number
    assists: number
  }
  percentile_ranks: Record<string, number>
  image_url?: string  // ADD THIS LINE
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

export interface ClusterCenter {
  cluster_id: number
  label: string
  x: number
  y: number
  count: number
}

export interface PCAData {
  points: PCAPoint[]
  explained_variance: number[]
  pc_interpretation: Record<string, string>
  cluster_centers: ClusterCenter[]
}