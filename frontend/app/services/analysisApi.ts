import { 
  ForwardMetrics, 
  RecommendationResponse, 
  Algorithm, 
  PCAData,
  MetricWeight 
} from '@/app/types/analysis'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const analysisApi = {
  // Get available metrics for forwards
  async getForwardMetrics(): Promise<ForwardMetrics[]> {
    const response = await fetch(`${API_BASE_URL}/api/forwards/metrics`)
    if (!response.ok) throw new Error('Failed to fetch metrics')
    return response.json()
  },

  // Get player recommendations
  async getRecommendations(
weights: Record<string, number>, algorithm: string = 'weighted_score', selectedLeagues?: string[]  ): Promise<RecommendationResponse> {
    const metricWeights: MetricWeight[] = Object.entries(weights).map(([metric, weight]) => ({
      metric,
      weight
    }))

    const response = await fetch(`${API_BASE_URL}/api/forwards/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        weights: metricWeights,
        algorithm,
        limit: 10
      })
    })

    if (!response.ok) throw new Error('Failed to get recommendations')
    return response.json()
  },

  // Get PCA visualization data
  async getPCAData(): Promise<PCAData> {
    const response = await fetch(`${API_BASE_URL}/api/forwards/pca-data`)
    if (!response.ok) throw new Error('Failed to fetch PCA data')
    return response.json()
  },

  // Get available algorithms
  async getAlgorithms(): Promise<Algorithm[]> {
    const response = await fetch(`${API_BASE_URL}/api/algorithms/list`)
    if (!response.ok) throw new Error('Failed to fetch algorithms')
    return response.json()
  }
}