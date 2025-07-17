'use client'

import { useEffect, useRef, useState, useCallback, useLayoutEffect } from 'react'
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
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const [transform, setTransform] = useState({ k: 1, x: 0, y: 0 })
  const [useOptimalClusters, setUseOptimalClusters] = useState(true)
  const [customClusterCount, setCustomClusterCount] = useState(5)
  const [expandedCluster, setExpandedCluster] = useState<string | null>(null)
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)

  // Use ResizeObserver instead of window resize event
  useLayoutEffect(() => {
    if (!containerRef.current) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        if (width > 0 && height > 0) {
          setDimensions({ width, height })
        }
      }
    })

    resizeObserver.observe(containerRef.current)

    // Initial dimension calculation
    const rect = containerRef.current.getBoundingClientRect()
    if (rect.width > 0 && rect.height > 0) {
      setDimensions({
        width: rect.width,
        height: rect.height
      })
    }

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

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
        // Just reset to show all data properly centered
        svg.transition().duration(500).call(zoomRef.current.transform, d3.zoomIdentity)
        break
    }
  }, [data])

  // Main visualization effect - add dimensions.height check
  useEffect(() => {
    if (!data || !svgRef.current || dimensions.width === 0 || dimensions.height === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // Set SVG dimensions explicitly
    svg
      .attr('width', dimensions.width)
      .attr('height', dimensions.height)
      .attr('viewBox', `0 0 ${dimensions.width} ${dimensions.height}`)
      .style('width', '100%')
      .style('height', '100%')

    const margin = { top: 40, right: 40, bottom: 60, left: 60 }
    const width = dimensions.width - margin.left - margin.right
    const height = dimensions.height - margin.top - margin.bottom

    // Create zoom container
    const zoomContainer = svg.append('g')
      .attr('class', 'zoom-container')

    // Main group for the chart
    const g = zoomContainer.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Get data extents
    const xExtent = d3.extent(data.points, d => d.x) as [number, number]
    const yExtent = d3.extent(data.points, d => d.y) as [number, number]
    
    // Add padding to extents
    const xPadding = (xExtent[1] - xExtent[0]) * 0.1
    const yPadding = (yExtent[1] - yExtent[0]) * 0.1

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([xExtent[0] - xPadding, xExtent[1] + xPadding])
      .range([0, width])

    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - yPadding, yExtent[1] + yPadding])
      .range([height, 0])

    // Add background for interactivity
    g.append('rect')
      .attr('class', 'zoom-background')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', 'transparent')

    // Add grid FIRST (behind everything)
    const xGrid = g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
        .ticks(10))
      .style('stroke-dasharray', '2,2')
      .style('opacity', 0.05)

    const yGrid = g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
        .ticks(10))
      .style('stroke-dasharray', '2,2')
      .style('opacity', 0.05)

    // Add axes
    const xAxisG = g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`)
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
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.5)')
      .style('font-size', '12px')
      .text(`← ${data.pc_interpretation?.PC2 || 'PC2'}`)

    g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', `translate(${width / 2}, ${height + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.5)')
      .style('font-size', '12px')
      .text(`${data.pc_interpretation?.PC1 || 'PC1'} →`)

    // Color scale
    const uniqueClusters = Array.from(new Set(data.points.map(p => p.cluster).filter(Boolean))) as string[]
    const colorScale = d3.scaleOrdinal<string>()
      .domain(uniqueClusters)
      .range(['var(--position-color)', '#4ecdc4', '#45b7d1', '#96ceb4', '#f9ca24', '#f0932b', '#6c5ce7', '#a29bfe'])

    // Add cluster labels BEFORE points so they're behind
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

    // Add interactions to points
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

    // Add highlighted player labels - REMOVED TO ONLY SHOW OUTLINE
    const highlightedData = data.points.filter(p => highlightedPlayers.includes(p.player_id))
    // No labels, just the highlighted circles which are already styled above

// Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 8])
      .on('zoom', (event) => {
        const { transform } = event;
        setTransform({ k: transform.k, x: transform.x, y: transform.y });
        zoomContainer.attr('transform', transform.toString());
      });

    svg.call(zoom);
    zoomRef.current = zoom;

    const handleClick = () => setSelectedCluster(null);
    svg.on('click', handleClick);

    return () => {
      svg.on('.zoom', null).on('click', null);
    };
  }, [data, dimensions, selectedCluster, highlightedPlayers])

  if (!data) return null

  const uniqueClusters = Array.from(new Set(data.points.map(p => p.cluster).filter(Boolean))) as string[]
  const colorScale = d3.scaleOrdinal<string>()
    .domain(uniqueClusters)
    .range(['var(--position-color)', '#4ecdc4', '#45b7d1', '#96ceb4', '#f9ca24', '#f0932b', '#6c5ce7', '#a29bfe'])

  return (
    <div className="pca-viz-container" ref={containerRef}>
      {/* SVG Canvas */}
      <svg ref={svgRef} className="pca-svg" />
      
      {/* Tooltip - Rendered as React component */}
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
              // Notify parent to refetch data
              if (onClusterCountChange) {
                onClusterCountChange(newState ? null : customClusterCount)
              }
            }}
            title={useOptimalClusters ? "Using Optimal Clusters" : "Using Custom Clusters"}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            <span className="cluster-toggle-label">
              {useOptimalClusters ? 'AUTO' : `K=${customClusterCount}`}
            </span>
          </button>
          {!useOptimalClusters && (
            <div className="cluster-number-controls">
              <button 
                className="cluster-adjust-btn"
                onClick={() => {
                  const newCount = Math.max(2, customClusterCount - 1)
                  setCustomClusterCount(newCount)
                  if (!useOptimalClusters && onClusterCountChange) {
                    onClusterCountChange(newCount)
                  }
                }}
              >
                −
              </button>
              <span className="cluster-number">{customClusterCount}</span>
              <button 
                className="cluster-adjust-btn"
                onClick={() => {
                  const newCount = Math.min(10, customClusterCount + 1)
                  setCustomClusterCount(newCount)
                  if (!useOptimalClusters && onClusterCountChange) {
                    onClusterCountChange(newCount)
                  }
                }}
              >
                +
              </button>
            </div>
          )}
        </div>
        
        {/* Zoom Level Indicator */}
        {transform.k !== 1 && (
          <div className="zoom-level">{Math.round(transform.k * 100)}%</div>
        )}
      </div>
      
      {/* Bottom Info Bar - Clean horizontal layout */}
      <div className="pca-bottom-bar">
        {/* Groups Section - 70% */}
        <div className="groups-section">
          <h4 className="section-label">PLAYER TYPES</h4>
          <div className="groups-container">
            {uniqueClusters.map(cluster => {
              const count = data.points.filter(p => p.cluster === cluster).length
              const isActive = !selectedCluster || selectedCluster === cluster
              const isExpanded = expandedCluster === cluster
              const clusterPlayers = data.points.filter(p => p.cluster === cluster)
              
              return (
                <div key={cluster} className="group-box">
                  <div
                    className={`group-item ${!isActive ? 'inactive' : ''}`}
                    onClick={() => setSelectedCluster(prev => prev === cluster ? null : cluster)}
                  >
                    <div 
                      className="group-dot"
                      style={{ backgroundColor: colorScale(cluster) }}
                    />
                    <span className="group-label">{cluster}</span>
                    <span className="group-count">({count})</span>
                    <button
                      className="group-expand-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        setExpandedCluster(prev => prev === cluster ? null : cluster)
                      }}
                    >
                      <svg 
                        width="12" 
                        height="12" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor"
                        style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0)' }}
                      >
                        <path d="M6 9l6 6 6-6" strokeWidth="2"/>
                      </svg>
                    </button>
                  </div>
                  {isExpanded && (
                    <div className="group-players-dropdown">
                      <div className="group-players-list">
                        {clusterPlayers.map(player => (
                          <div key={player.player_id} className="group-player-item">
                            <span className="player-name">{player.name}</span>
                            <span className="player-team">{player.team}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
        
        {/* Variance Section - 30% */}
        <div className="variance-section">
          <h4 className="section-label">VARIANCE EXPLAINED</h4>
          <div className="variance-content">
            <div className="variance-item">
              <span className="variance-pc">PC1</span>
              <div className="variance-bar-mini">
                <div 
                  className="variance-fill-mini pc1"
                  style={{ width: `${(data.explained_variance[0] * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="variance-value">{(data.explained_variance[0] * 100).toFixed(0)}%</span>
            </div>
            <div className="variance-item">
              <span className="variance-pc">PC2</span>
              <div className="variance-bar-mini">
                <div 
                  className="variance-fill-mini pc2"
                  style={{ width: `${(data.explained_variance[1] * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="variance-value">{(data.explained_variance[1] * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}