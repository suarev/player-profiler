'use client'

import { useState, useEffect } from 'react'
import CustomCursor from '@/app/components/ui/CustomCursor'
import FilmGrain from '@/app/components/ui/FilmGrain'
import AnalysisHeader from '@/app/components/analysis/AnalysisHeader'
import RecommendationsPanel from '@/app/components/analysis/RecommendationsPanel'
import PreferencesPanel from '@/app/components/analysis/PreferencesPanel'
import PCAVisualization from '@/app/components/analysis/PCAVisualization'
import BenchRecommendations from '@/app/components/analysis/BenchRecommendations'
import { ForwardMetrics, PlayerRecommendation, PCAData } from '@/app/types/analysis'
import { analysisApi } from '@/app/services/analysisApi'
import '@/app/styles/analysis.css'

export default function ForwardAnalysisPage() {
  // State for metrics and weights
  const [metrics, setMetrics] = useState<ForwardMetrics[]>([])
  const [weights, setWeights] = useState<Record<string, number>>({})
  const [algorithm, setAlgorithm] = useState('weighted_score')
  const [recommendations, setRecommendations] = useState<PlayerRecommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [pcaData, setPcaData] = useState<PCAData | null>(null)
  const [clusterCount, setClusterCount] = useState<number | null>(null)

  // Load metrics on mount
  useEffect(() => {
    loadMetrics()
    loadPCAData()
  }, [])

  // Load available metrics from API
  const loadMetrics = async () => {
    try {
      const data = await analysisApi.getForwardMetrics()
      setMetrics(data)
      
      // Initialize to 50
      const initialWeights: Record<string, number> = {}
      data.forEach(metric => {
        initialWeights[metric.id] = 50
      })
      setWeights(initialWeights)
    } catch (error) {
      console.error('Failed to load metrics:', error)
    }
  }

  // Load PCA data
  const loadPCAData = async (k?: number) => {
    try {
      console.log('Loading PCA data with k=', k)
      const data = await analysisApi.getPCAData(k)
      setPcaData(data)
      console.log('PCA data loaded successfully')
    } catch (error) {
      console.error('Failed to load PCA data:', error)
      alert('Failed to load PCA visualization. Check console for details.')
    }
  }

  // Get recommendations when weights or algorithm change
  useEffect(() => {
    if (Object.keys(weights).length > 0) {
      const debounceTimer = setTimeout(() => {
        getRecommendations()
      }, 300)

      return () => clearTimeout(debounceTimer)
    }
  }, [weights, algorithm])

  // Fetch recommendations from API
  const getRecommendations = async () => {
    setLoading(true)
    try {
      const data = await analysisApi.getRecommendations(weights, algorithm)
      setRecommendations(data.recommendations)
    } catch (error) {
      console.error('Failed to get recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  // Update a single weight
  const updateWeight = (metricId: string, value: number) => {
    setWeights(prev => ({
      ...prev,
      [metricId]: value
    }))
  }

  const handleClusterCountChange = (k: number | null) => {
    console.log('Cluster count changed to:', k)
    setClusterCount(k)
    loadPCAData(k || undefined)
  }

  return (
    <div className="analysis-page">
      {/* Custom Cursor */}
      <CustomCursor />

      {/* Film Grain Effect */}
      <FilmGrain />

      {/* Background */}
      <div className="analysis-bg" />

      {/* Header */}
      <AnalysisHeader 
        position="FORWARDS" 
        playerCount={127} 
      />

      {/* Main Container */}
      <div className="analysis-container">
        {/* First Page - Recommendations and Sliders */}
        <div className="first-page">
          {/* Left Side - Recommendations */}
          <div className="recommendations-side">
            <RecommendationsPanel 
              recommendations={recommendations.slice(0, 5)}
              loading={loading}
              variant="primary"
            />
          </div>

          {/* Right Side - Preferences and Bench */}
          <div className="preferences-side">
            <PreferencesPanel
              metrics={metrics}
              weights={weights}
              algorithm={algorithm}
              onWeightChange={updateWeight}
              onAlgorithmChange={setAlgorithm}
            />
            
            {/* Bench Recommendations */}
            {recommendations.length > 5 && (
              <BenchRecommendations 
                players={recommendations.slice(5, 10).map((player, index) => ({
                  ...player,
                  rank: index + 6,
                  image_url: player.image_url  // ADD THIS LINE
                }))}
              />
            )}
          </div>
        </div>

        {/* Second Page - PCA Visualization */}
        <div className="second-page">
          <div className="pca-header">
            <h2 className="panel-title">FORWARD LANDSCAPE — STATISTICAL CLUSTERING</h2>
            <div className="pca-controls">
              <button className="pca-button">RESET VIEW</button>
              <button className="pca-button">HIGHLIGHT SIMILAR</button>
            </div>
          </div>
          
          <PCAVisualization 
            data={pcaData}
            highlightedPlayers={recommendations.map(r => r.player_id)}
            onClusterCountChange={handleClusterCountChange}
          />
        </div>
      </div>
    </div>
  )
}