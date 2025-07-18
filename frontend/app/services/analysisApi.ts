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
  weights: Record<string, number>, 
  algorithm: string = 'weighted_score'
): Promise<RecommendationResponse> {
  const metricWeights: MetricWeight[] = Object.entries(weights).map(([metric, weight]) => ({
    metric,
    weight
  }))

  try {
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

    if (!response.ok) {
      const errorText = await response.text()
      console.error('API Error:', errorText)
      throw new Error(`Failed to get recommendations: ${response.status}`)
    }
    
    return response.json()
  } catch (error) {
    console.error('Request failed:', error)
    throw error
  }
},

  // Get PCA visualization data
  async getPCAData(k?: number): Promise<PCAData> {
    const url = k 
      ? `${API_BASE_URL}/api/forwards/pca-data?k=${k}`
      : `${API_BASE_URL}/api/forwards/pca-data`
    
    console.log('Fetching PCA data from:', url)  // Debug log
    
    try {
      const response = await fetch(url)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('PCA API Error:', response.status, errorText)
        throw new Error(`Failed to fetch PCA data: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('PCA data received:', data)  // Debug log
      return data
    } catch (error) {
      console.error('PCA fetch error:', error)
      throw error
    }
  },

  // Get available algorithms
  async getAlgorithms(): Promise<Algorithm[]> {
    const response = await fetch(`${API_BASE_URL}/api/algorithms/list`)
    if (!response.ok) throw new Error('Failed to fetch algorithms')
    return response.json()
  }
}