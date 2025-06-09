'use client'

import { useRef, useState, useEffect } from 'react'
import { ForwardMetrics } from '@/app/types/analysis'

interface MetricSliderProps {
  metric: ForwardMetrics
  value: number
  onChange: (value: number) => void
}

export default function MetricSlider({ metric, value, onChange }: MetricSliderProps) {
  const sliderRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    updateValue(e.nativeEvent)
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return
    updateValue(e)
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const updateValue = (e: MouseEvent) => {
    if (!sliderRef.current) return
    
    const rect = sliderRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100))
    onChange(Math.round(percentage))
  }

  // Add global listeners when dragging
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging])

  return (
    <div className="slider-item">
      <div className="slider-header">
        <span className="slider-label">{metric.name}</span>
        <span className="slider-value">{value}</span>
      </div>
      <div 
        className="slider-track" 
        ref={sliderRef}
        onMouseDown={handleMouseDown}
      >
        <div className="slider-fill" style={{ width: `${value}%` }} />
        <div className="slider-thumb" style={{ left: `${value}%` }} />
      </div>
      <div className="slider-description">{metric.description}</div>
    </div>
  )
}
