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
import { genericAnalysisApi } from '@/app/services/genericAnalysisApi'
import '@/app/styles/analysis.css'

interface GenericAnalysisPageProps {
  position: 'forward' | 'midfielder' | 'defender' | 'goalkeeper'
  playerCount: number
}

const POSITION_INFO = {
  forward: {
    displayName: 'FORWARDS',
    count: 127,
    color: '#1688CC'
  },
  midfielder: {
    displayName: 'MIDFIELDERS',
    count: 234,
    color: '#DC273D'
  },
  defender: {
    displayName: 'DEFENDERS', 
    count: 198,
    color: '#AFA15F'
  },
  goalkeeper: {
    displayName: 'GOALKEEPERS',
    count: 47,
    color: '#BE2F7A'
  }
}

export default function GenericAnalysisPage({ position, playerCount }: GenericAnalysisPageProps) {
  // State
  const [metrics, setMetrics] = useState<ForwardMetrics[]>([])
  const [weights, setWeights] = useState<Record<string, number>>({})
  const [algorithm, setAlgorithm] = useState('weighted_score')
  const [recommendations, setRecommendations] = useState<PlayerRecommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [pcaData, setPcaData] = useState<PCAData | null>(null)

  const positionInfo = POSITION_INFO[position]

  // Apply position-specific styling
  useEffect(() => {
    // Update CSS variables for position color
    document.documentElement.style.setProperty('--position-color', positionInfo.color)
    
    // Add position class to body for specific styling
    document.body.classList.add(`analysis-${position}`)
    
    return () => {
      document.body.classList.remove(`analysis-${position}`)
    }
  }, [position, positionInfo.color])

  // Load metrics on mount
  useEffect(() => {
    loadMetrics()
    loadPCAData()
  }, [position])

  // Load available metrics
  const loadMetrics = async () => {
    try {
      const data = await genericAnalysisApi.getPositionMetrics(position)
      setMetrics(data)
      
      // Initialize weights to 50
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
      const data = await genericAnalysisApi.getPCAData(position, k)
      setPcaData(data)
    } catch (error) {
      console.error('Failed to load PCA data:', error)
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

  // Fetch recommendations
  const getRecommendations = async () => {
    setLoading(true)
    try {
      const data = await genericAnalysisApi.getRecommendations(position, weights, algorithm)
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

  return (
    <div className={`analysis-page position-${position}`}>
      {/* Custom Cursor */}
      <CustomCursor />

      {/* Film Grain Effect */}
      <FilmGrain />

      {/* Background */}
      <div className="analysis-bg" />

      {/* Add position-specific gradient overlay */}
      <div 
        className="position-gradient-overlay"
        style={{
          background: `radial-gradient(ellipse at top right, ${positionInfo.color}10 0%, transparent 50%)`
        }}
      />

      {/* Header */}
      <AnalysisHeader 
        position={positionInfo.displayName} 
        playerCount={positionInfo.count} 
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
                  image_url: player.image_url
                }))}
              />
            )}
          </div>
        </div>

        {/* Second Page - PCA Visualization */}
        <div className="second-page">
          <div className="pca-header">
            <h2 className="panel-title">{positionInfo.displayName} LANDSCAPE — STATISTICAL CLUSTERING</h2>
            <div className="pca-controls">
              <button className="pca-button">RESET VIEW</button>
              <button className="pca-button">HIGHLIGHT SIMILAR</button>
            </div>
          </div>
          
          <PCAVisualization 
            data={pcaData}
            highlightedPlayers={recommendations.map(r => r.player_id)}
            onClusterCountChange={(k) => loadPCAData(k || undefined)}
          />
        </div>
      </div>
    </div>
  )
}