'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import * as d3 from 'd3'
import { PCAData } from '@/app/types/analysis'

interface PCAVisualizationProps {
  data: PCAData | null
  highlightedPlayers: number[]
  onClusterCountChange?: (k: number | null) => void
}

export default function PCAVisualization({ data, highlightedPlayers, onClusterCountChange }: PCAVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [hoveredPlayer, setHoveredPlayer] = useState<{name: string, team: string} | null>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null)
  const [transform, setTransform] = useState({ k: 1, x: 0, y: 0 })
  const [useOptimalClusters, setUseOptimalClusters] = useState(true)
  const [customClusterCount, setCustomClusterCount] = useState(5)
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)

<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> parent of 0bcdd79 (trying to go back to when zoom in/out worked)
  // Handle resize
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const rect = container.getBoundingClientRect()
    setDimensions({ width: rect.width, height: rect.height })

    const observer = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
    }


    update()
    const observer = new ResizeObserver(update)
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

>>>>>>> parent of 0bcdd79 (trying to go back to when zoom in/out worked)
  // Zoom handlers
  const handleZoom = useCallback((direction: 'in' | 'out' | 'reset' | 'focus') => {
    if (!svgRef.current || !zoomRef.current || !data) return

    const svg = d3.select(svgRef.current)
    
    switch (direction) {
      case 'in':
        svg.transition().duration(300).call(zoomRef.current.scaleBy, 1.5)
        break
      case 'out':
        svg.transition().duration(300).call(zoomRef.current.scaleBy, 0.67)
        break
      case 'reset':
        svg.transition().duration(300).call(zoomRef.current.transform, d3.zoomIdentity)
        break
      case 'focus':
        svg.transition().duration(500).call(zoomRef.current.transform, d3.zoomIdentity)
        break
    }
  }, [data])

  useEffect(() => {
    if (!data || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // Fixed dimensions for now
    const width = 900
    const height = 600
    const margin = { top: 40, right: 40, bottom: 60, left: 60 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    // Set SVG size
    svg
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)

    // Create zoom container
    const zoomContainer = svg.append('g')
      .attr('class', 'zoom-container')

    // Main group for the chart
    const g = zoomContainer.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Get data extents
    const xExtent = d3.extent(data.points, d => d.x) as [number, number]
    const yExtent = d3.extent(data.points, d => d.y) as [number, number]
    
    // Add padding
    const xPadding = (xExtent[1] - xExtent[0]) * 0.1
    const yPadding = (yExtent[1] - yExtent[0]) * 0.1

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([xExtent[0] - xPadding, xExtent[1] + xPadding])
      .range([0, innerWidth])

    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - yPadding, yExtent[1] + yPadding])
      .range([innerHeight, 0])

    // Add background
    g.append('rect')
      .attr('class', 'zoom-background')
      .attr('width', innerWidth)
      .attr('height', innerHeight)
      .attr('fill', 'transparent')

    // Add grid
    const xGrid = g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-innerHeight)
        .tickFormat(() => '')
        .ticks(10))
      .style('stroke-dasharray', '2,2')
      .style('opacity', 0.05)

    const yGrid = g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-innerWidth)
        .tickFormat(() => '')
        .ticks(10))
      .style('stroke-dasharray', '2,2')
      .style('opacity', 0.05)

    // Add axes
    const xAxisG = g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).ticks(5))
      .style('color', 'rgba(255, 255, 255, 0.3)')

    const yAxisG = g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(yScale).ticks(5))
      .style('color', 'rgba(255, 255, 255, 0.3)')

    // Style axis text
    xAxisG.selectAll('text').style('fill', 'rgba(255, 255, 255, 0.5)')
    yAxisG.selectAll('text').style('fill', 'rgba(255, 255, 255, 0.5)')

    // Add axis labels
    g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left + 15)
      .attr('x', 0 - (innerHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.5)')
      .style('font-size', '12px')
      .text(`← ${data.pc_interpretation?.PC2 || 'PC2'}`)

    g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', `translate(${innerWidth / 2}, ${innerHeight + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.5)')
      .style('font-size', '12px')
      .text(`${data.pc_interpretation?.PC1 || 'PC1'} →`)

    // Color scale
    const uniqueClusters = Array.from(new Set(data.points.map(p => p.cluster).filter(Boolean))) as string[]
    const colorScale = d3.scaleOrdinal<string>()
      .domain(uniqueClusters)
      .range(['var(--position-color)', '#4ecdc4', '#45b7d1', '#96ceb4', '#f9ca24', '#f0932b', '#6c5ce7', '#a29bfe'])

    // Add cluster labels
    if (data.cluster_centers && data.cluster_centers.length > 0) {
      g.append('g')
        .attr('class', 'cluster-labels-group')
        .selectAll('text')
        .data(data.cluster_centers)
        .enter()
        .append('text')
        .attr('class', 'cluster-label')
        .attr('x', d => xScale(d.x))
        .attr('y', d => yScale(d.y))
        .style('text-anchor', 'middle')
        .style('fill', d => colorScale(d.label))
        .style('opacity', 0.6)
        .style('font-size', '11px')
        .style('font-weight', '600')
        .style('pointer-events', 'none')
        .text(d => d.label)
    }

    // Create points group
    const pointsGroup = g.append('g')
      .attr('class', 'points-group')

    // Add points
    const points = pointsGroup.selectAll('.point')
      .data(data.points)
      .enter()
      .append('circle')
      .attr('class', 'point')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => highlightedPlayers.includes(d.player_id) ? 7 : 4)
      .attr('fill', d => {
        if (selectedCluster && d.cluster !== selectedCluster) {
          return 'rgba(255, 255, 255, 0.1)'
        }
        return d.cluster ? colorScale(d.cluster) : 'rgba(255, 255, 255, 0.6)'
      })
      .attr('stroke', d => highlightedPlayers.includes(d.player_id) ? '#fff' : 'none')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .style('opacity', d => {
        if (selectedCluster && d.cluster !== selectedCluster) return 0.2
        return highlightedPlayers.includes(d.player_id) ? 1 : 0.7
      })

    // Add interactions
    points
      .on('mouseenter', function(event, d) {
        d3.select(this).transition().duration(100).attr('r', 8)
        setHoveredPlayer({ name: d.name, team: d.team })
        const rect = containerRef.current?.getBoundingClientRect()
        if (rect) {
          setMousePos({ 
            x: event.clientX - rect.left, 
            y: event.clientY - rect.top - 20 
          })
        }
      })
      .on('mousemove', function(event, d) {
        const rect = containerRef.current?.getBoundingClientRect()
        if (rect) {
          setMousePos({ 
            x: event.clientX - rect.left, 
            y: event.clientY - rect.top - 20 
          })
        }
      })
      .on('mouseleave', function(event, d) {
        d3.select(this).transition().duration(100)
          .attr('r', highlightedPlayers.includes(d.player_id) ? 7 : 4)
        setHoveredPlayer(null)
      })
      .on('click', function(event, d) {
        event.stopPropagation()
        if (d.cluster) {
          setSelectedCluster(prev => prev === d.cluster ? null : d.cluster!)
        }
      })

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 8])
      .on('zoom', (event) => {
        const { transform } = event
        setTransform({ k: transform.k, x: transform.x, y: transform.y })
        zoomContainer.attr('transform', transform.toString())
      })

    svg.call(zoom)
    zoomRef.current = zoom

    const handleClick = () => setSelectedCluster(null)
    svg.on('click', handleClick)

    return () => {
      svg.on('.zoom', null).on('click', null)
    }
  }, [data, selectedCluster, highlightedPlayers])

  if (!data) return <div>No PCA data available</div>

  const uniqueClusters = Array.from(new Set(data.points.map(p => p.cluster).filter(Boolean))) as string[]
  const colorScale = d3.scaleOrdinal<string>()
    .domain(uniqueClusters)
    .range(['var(--position-color)', '#4ecdc4', '#45b7d1', '#96ceb4', '#f9ca24', '#f0932b', '#6c5ce7', '#a29bfe'])

  return (
    <div className="pca-viz-container" ref={containerRef}>
      {/* SVG Canvas */}
      <svg 
        ref={svgRef} 
        className="pca-svg"
        style={{ 
          width: '100%', 
          maxWidth: '900px',
          height: '600px',
          display: 'block',
          margin: '0 auto'
        }} 
      />
      
      {/* Tooltip */}
      {hoveredPlayer && (
        <div 
          className="pca-hover-tooltip"
          style={{ 
            left: `${mousePos.x}px`, 
            top: `${mousePos.y}px`
          }}
        >
          {hoveredPlayer.name} ({hoveredPlayer.team})
        </div>
      )}
      
      {/* Control Panel */}
      <div className="pca-control-panel">
        {/* Zoom Controls */}
        <div className="zoom-controls-group">
          <button className="pca-control-btn" onClick={() => handleZoom('in')} title="Zoom In">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35M11 8v6M8 11h6"/>
            </svg>
          </button>
          <button className="pca-control-btn" onClick={() => handleZoom('out')} title="Zoom Out">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35M8 11h6"/>
            </svg>
          </button>
          <button className="pca-control-btn" onClick={() => handleZoom('reset')} title="Reset">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M1 4v6h6M23 20v-6h-6"/>
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15"/>
            </svg>
          </button>
          <button className="pca-control-btn" onClick={() => handleZoom('focus')} title="Auto Focus">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
        </div>
        
        {/* Cluster Control */}
        <div className="cluster-control-group">
          <button 
            className={`cluster-toggle-btn ${useOptimalClusters ? 'active' : ''}`}
            onClick={() => {
              const newState = !useOptimalClusters
              setUseOptimalClusters(newState)
              if (onClusterCountChange) {
                onClusterCountChange(newState ? null : customClusterCount)
              }
            }}
            title={useOptimalClusters ? 'Using optimal clusters' : `Using ${customClusterCount} clusters`}
          >
            {useOptimalClusters ? 'AUTO' : 'SET'} CLUSTERS
          </button>
          
          {!useOptimalClusters && (
            <div className="cluster-count-selector">
              <input
                type="range"
                min="2"
                max="10"
                value={customClusterCount}
                onChange={(e) => {
                  const k = parseInt(e.target.value)
                  setCustomClusterCount(k)
                  if (onClusterCountChange) {
                    onClusterCountChange(k)
                  }
                }}
                className="cluster-slider"
              />
              <span className="cluster-count">{customClusterCount}</span>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="pca-bottom-bar">
        {/* Groups Section */}
        <div className="groups-section">
          <div className="section-label">PLAYER TYPES</div>
          <div className="groups-container">
            {uniqueClusters.map(cluster => (
              <div 
                key={cluster}
                className={`group-item ${selectedCluster === cluster ? 'selected' : ''}`}
                onClick={() => setSelectedCluster(prev => prev === cluster ? null : cluster)}
              >
                <div 
                  className="group-color" 
                  style={{ 
                    width: '12px', 
                    height: '12px', 
                    backgroundColor: colorScale(cluster),
                    borderRadius: '50%'
                  }} 
                />
                <span className="group-name">{cluster}</span>
                <span className="group-count" style={{ opacity: 0.5, fontSize: '0.8em' }}>
                  ({data.points.filter(p => p.cluster === cluster).length})
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Stats Section */}
        <div className="stats-section" style={{ flex: '0 0 30%', padding: '1rem 1.5rem' }}>
          <div className="section-label">VARIANCE EXPLAINED</div>
          <div className="variance-stats">
            <div className="variance-item">
              <span className="variance-label">PC1:</span>
              <span className="variance-value">{(data.variance_explained[0] * 100).toFixed(1)}%</span>
            </div>
            <div className="variance-item">
              <span className="variance-label">PC2:</span>
              <span className="variance-value">{(data.variance_explained[1] * 100).toFixed(1)}%</span>
            </div>
            <div className="variance-item">
              <span className="variance-label">Total:</span>
              <span className="variance-value">
                {((data.variance_explained[0] + data.variance_explained[1]) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}