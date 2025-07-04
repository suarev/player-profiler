'use client'

import { useState, useEffect } from 'react'
import { ForwardMetrics, Algorithm } from '@/app/types/analysis'
import MetricSlider from './MetricSlider'
import AlgorithmSelector from './AlgorithmSelector'
import { genericAnalysisApi } from '@/app/services/genericAnalysisApi'

interface PreferencesPanelProps {
  metrics: ForwardMetrics[]
  weights: Record<string, number>
  algorithm: string
  onWeightChange: (metricId: string, value: number) => void
  onAlgorithmChange: (algorithm: string) => void
}

export default function PreferencesPanel({
  metrics,
  weights,
  algorithm,
  onWeightChange,
  onAlgorithmChange
}: PreferencesPanelProps) {
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([])

  useEffect(() => {
    loadAlgorithms()
  }, [])

  const loadAlgorithms = async () => {
    try {
      const data = await genericAnalysisApi.getAlgorithms()
      setAlgorithms(data)
    } catch (error) {
      console.error('Failed to load algorithms:', error)
    }
  }

  return (
    <div className="preferences-panel">
      <h2 className="panel-title">PROFILE PREFERENCES</h2>
      
      {/* Algorithm Selector */}
      <AlgorithmSelector
        algorithms={algorithms}
        selectedAlgorithm={algorithm}
        onAlgorithmChange={onAlgorithmChange}
      />

      {/* Sliders Grid */}
      <div className="sliders-grid">
        {metrics.map(metric => (
          <MetricSlider
            key={metric.id}
            metric={metric}
            value={weights[metric.id] ?? 50}
            onChange={(value) => onWeightChange(metric.id, value)}
          />
        ))}
      </div>
    </div>
  )
}