'use client'

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { PCAData } from '@/app/types/analysis'

interface PCAVisualizationProps {
  data: PCAData | null
  highlightedPlayers: number[]
}

export default function PCAVisualization({ data, highlightedPlayers }: PCAVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [tooltip, setTooltip] = useState<{ x: number; y: number; player: string } | null>(null)
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const [zoomLevel, setZoomLevel] = useState(1)
  const [isPanning, setIsPanning] = useState(false)

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        })
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    if (!data || !svgRef.current || dimensions.width === 0) return

    // Clear previous visualization
    d3.select(svgRef.current).selectAll('*').remove()

    // Set dimensions and margins
    const margin = { top: 60, right: 200, bottom: 80, left: 80 }
    const width = dimensions.width - margin.left - margin.right
    const height = dimensions.height - margin.top - margin.bottom

    // Create SVG with zoom capabilities
    const svg = d3.select(svgRef.current)
      .attr('width', dimensions.width)
      .attr('height', dimensions.height)

    // Create a group for zoom transformations
    const zoomGroup = svg.append('g')
    
    const g = zoomGroup.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Calculate data density to find where most points are
    const xValues = data.points.map(d => d.x)
    const yValues = data.points.map(d => d.y)
    
    // Find the 80th percentile range (where most data is)
    const xSorted = [...xValues].sort((a, b) => a - b)
    const ySorted = [...yValues].sort((a, b) => a - b)
    
    const percentile = (arr: number[], p: number) => {
      const index = Math.ceil(arr.length * p) - 1
      return arr[index]
    }
    
    // Focus on the middle 80% of data initially
    const xMin = percentile(xSorted, 0.1)
    const xMax = percentile(xSorted, 0.9)
    const yMin = percentile(ySorted, 0.1)
    const yMax = percentile(ySorted, 0.9)
    
    // Add some padding
    const xPadding = (xMax - xMin) * 0.1
    const yPadding = (yMax - yMin) * 0.1

    // Create scales - focused on the dense area
    const xScale = d3.scaleLinear()
      .domain([xMin - xPadding, xMax + xPadding])
      .range([0, width])

    const yScale = d3.scaleLinear()
      .domain([yMin - yPadding, yMax + yPadding])
      .range([height, 0])

    // Create full scales for reference (used in overview)
    const xExtent = d3.extent(data.points, d => d.x) as [number, number]
    const yExtent = d3.extent(data.points, d => d.y) as [number, number]
    
    const xScaleFull = d3.scaleLinear()
      .domain([xExtent[0] - 0.5, xExtent[1] + 0.5])
      .range([0, width])

    const yScaleFull = d3.scaleLinear()
      .domain([yExtent[0] - 0.5, yExtent[1] + 0.5])
      .range([height, 0])

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 10])  // Min and max zoom
      .extent([[0, 0], [dimensions.width, dimensions.height]])
      .on('zoom', (event) => {
        zoomGroup.attr('transform', event.transform)
        setZoomLevel(event.transform.k)
        setIsPanning(true)
        
        // Update axes based on zoom
        const newXScale = event.transform.rescaleX(xScale)
        const newYScale = event.transform.rescaleY(yScale)
        
        xAxis.call(d3.axisBottom(newXScale).ticks(5))
        yAxis.call(d3.axisLeft(newYScale).ticks(5))
      })
      .on('end', () => {
        setIsPanning(false)
      })

    svg.call(zoom)

    // Add subtle grid
    const xGridLines = g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
        .ticks(10)
      )
      .style('stroke-dasharray', '2,2')
      .style('opacity', 0.1)

    const yGridLines = g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
        .ticks(10)
      )
      .style('stroke-dasharray', '2,2')
      .style('opacity', 0.1)

    // Add axes
    const xAxis = g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).ticks(5))
      .style('color', 'rgba(255, 255, 255, 0.5)')

    const yAxis = g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(yScale).ticks(5))
      .style('color', 'rgba(255, 255, 255, 0.5)')

    // Add axis labels with interpretation
    g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.7)')
      .style('font-size', '14px')
      .text(`← ${data.pc_interpretation?.PC2 || 'PC2'} (${(data.explained_variance[1] * 100).toFixed(0)}% variance)`)

    g.append('text')
      .attr('class', 'axis-label')
      .attr('transform', `translate(${width / 2}, ${height + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.7)')
      .style('font-size', '14px')
      .text(`${data.pc_interpretation?.PC1 || 'PC1'} → (${(data.explained_variance[0] * 100).toFixed(0)}% variance)`)

    // Color scale for clusters
    const uniqueClusters = Array.from(new Set(data.points.map(p => p.cluster).filter((c): c is string => c !== null && c !== undefined)))
    const colorScale = d3.scaleOrdinal<string>()
      .domain(uniqueClusters)
      .range(['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#f9ca24', '#f0932b'])

    // Add cluster regions (subtle backgrounds)
    if (data.cluster_centers && data.cluster_centers.length > 0) {
      const voronoi = d3.Delaunay
        .from(data.cluster_centers, d => xScale(d.x), d => yScale(d.y))
        .voronoi([0, 0, width, height])

      g.append('g')
        .attr('class', 'cluster-regions')
        .selectAll('path')
        .data(data.cluster_centers)
        .enter()
        .append('path')
        .attr('d', (d, i) => voronoi.renderCell(i))
        .attr('fill', d => colorScale(d.label) as string)
        .attr('opacity', 0.05)
        .attr('stroke', 'none')
    }

    // Add cluster labels
    if (data.cluster_centers) {
      g.append('g')
        .attr('class', 'cluster-labels')
        .selectAll('text')
        .data(data.cluster_centers)
        .enter()
        .append('text')
        .attr('x', d => xScale(d.x))
        .attr('y', d => yScale(d.y))
        .style('text-anchor', 'middle')
        .style('fill', d => colorScale(d.label) as string)
        .style('opacity', 0.7)
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('pointer-events', 'none')
        .text(d => d.label)
    }

    // Add points
    const points = g.selectAll('.pca-point')
      .data(data.points)
      .enter().append('circle')
      .attr('class', 'pca-point')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => highlightedPlayers.includes(d.player_id) ? 8 : 5)
      .attr('fill', d => {
        if (selectedCluster && d.cluster !== selectedCluster) {
          return 'rgba(255, 255, 255, 0.2)'
        }
        return d.cluster ? colorScale(d.cluster) as string : 'rgba(255, 255, 255, 0.6)'
      })
      .attr('stroke', d => highlightedPlayers.includes(d.player_id) ? '#fff' : 'none')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .style('opacity', d => {
        if (selectedCluster && d.cluster !== selectedCluster) return 0.3
        return highlightedPlayers.includes(d.player_id) ? 1 : 0.8
      })
      .on('mouseover', function(event, d) {
        if (!isPanning) {
          d3.select(this).attr('r', 10)
          const [x, y] = d3.pointer(event, svg.node())
          setTooltip({ x, y: y - 20, player: `${d.name} (${d.team})` })
        }
      })
      .on('mouseout', function(event, d) {
        d3.select(this).attr('r', highlightedPlayers.includes(d.player_id) ? 8 : 5)
        setTooltip(null)
      })
      .on('click', function(event, d) {
        if (!isPanning) {
          event.stopPropagation()
          if (d.cluster) {
            setSelectedCluster(selectedCluster === d.cluster ? null : d.cluster)
          }
        }
      })

    // Add legend
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + margin.left + 20}, ${margin.top})`)

    const legendItems = uniqueClusters.map((cluster, i) => ({
      cluster,
      color: colorScale(cluster) as string,
      count: data.points.filter(p => p.cluster === cluster).length
    }))

    legend.append('text')
      .attr('x', 0)
      .attr('y', -10)
      .style('fill', 'rgba(255, 255, 255, 0.7)')
      .style('font-size', '12px')
      .style('font-weight', '600')
      .text('PLAYER TYPES')

    const legendItem = legend.selectAll('.legend-item')
      .data(legendItems)
      .enter().append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 25 + 10})`)
      .style('cursor', 'pointer')
      .on('click', function(event, d) {
        setSelectedCluster(selectedCluster === d.cluster ? null : d.cluster)
      })

    legendItem.append('circle')
      .attr('r', 6)
      .attr('fill', d => d.color)
      .style('opacity', d => {
        if (selectedCluster && d.cluster !== selectedCluster) return 0.3
        return 1
      })

    legendItem.append('text')
      .attr('x', 15)
      .attr('y', 5)
      .style('fill', d => {
        if (selectedCluster && d.cluster !== selectedCluster) return 'rgba(255, 255, 255, 0.3)'
        return 'rgba(255, 255, 255, 0.8)'
      })
      .style('font-size', '12px')
      .text(d => `${d.cluster} (${d.count})`)

    // Add highlighted player names
    const highlightedData = data.points.filter(p => highlightedPlayers.includes(p.player_id))
    if (highlightedData.length > 0) {
      g.append('g')
        .attr('class', 'player-labels')
        .selectAll('text')
        .data(highlightedData)
        .enter()
        .append('text')
        .attr('x', d => xScale(d.x))
        .attr('y', d => yScale(d.y) - 12)
        .style('text-anchor', 'middle')
        .style('fill', '#fff')
        .style('font-size', '11px')
        .style('font-weight', '600')
        .style('pointer-events', 'none')
        .style('text-shadow', '0 0 4px rgba(0,0,0,0.8)')
        .text(d => d.name)
    }

    // Clear cluster selection when clicking background
    svg.on('click', () => setSelectedCluster(null))

    // Zoom control functions
    const zoomIn = () => {
      svg.transition().duration(300).call(zoom.scaleBy, 1.5)
    }

    const zoomOut = () => {
      svg.transition().duration(300).call(zoom.scaleBy, 0.67)
    }

    const resetZoom = () => {
      svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity)
    }

    const focusDenseArea = () => {
      // Calculate transform to focus on the dense area
      const k = 1.2  // Slight zoom
      const x = -xScale(xMin + (xMax - xMin) / 2) * k + width / 2
      const y = -yScale(yMin + (yMax - yMin) / 2) * k + height / 2
      
      svg.transition().duration(500)
        .call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(k))
    }

    // Add zoom controls to the container
    d3.select(containerRef.current)
      .select('.zoom-controls')
      .remove()
    
    const controls = d3.select(containerRef.current)
      .append('div')
      .attr('class', 'zoom-controls')
      .style('position', 'absolute')
      .style('top', '20px')
      .style('right', '20px')
      .style('display', 'flex')
      .style('flex-direction', 'column')
      .style('gap', '8px')

    // Store functions for button clicks
    ;(window as any).pcaZoomIn = zoomIn
    ;(window as any).pcaZoomOut = zoomOut
    ;(window as any).pcaResetZoom = resetZoom
    ;(window as any).pcaFocusDense = focusDenseArea

    // Start with focused view
    setTimeout(focusDenseArea, 100)

  }, [data, highlightedPlayers, dimensions, selectedCluster, isPanning])

  return (
    <div className="pca-container" ref={containerRef}>
      <svg ref={svgRef} className="pca-canvas" />
      {tooltip && (
        <div 
          className="pca-tooltip" 
          style={{ 
            left: tooltip.x + 'px', 
            top: tooltip.y + 'px',
            opacity: 1 
          }}
        >
          {tooltip.player}
        </div>
      )}
      
      {/* Zoom Controls */}
      <div className="zoom-controls">
        <button 
          className="zoom-btn"
          onClick={() => (window as any).pcaZoomIn?.()}
          title="Zoom In"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35M11 8v6M8 11h6"/>
          </svg>
        </button>
        <button 
          className="zoom-btn"
          onClick={() => (window as any).pcaZoomOut?.()}
          title="Zoom Out"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35M8 11h6"/>
          </svg>
        </button>
        <button 
          className="zoom-btn"
          onClick={() => (window as any).pcaResetZoom?.()}
          title="Reset View"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M3.38 8A9.77 9.77 0 0 1 12 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12"/>
            <path d="M3 8h4V4"/>
          </svg>
        </button>
        <button 
          className="zoom-btn"
          onClick={() => (window as any).pcaFocusDense?.()}
          title="Focus Dense Area"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      </div>
      
      {/* Controls for the visualization */}
      <div className="pca-info-panel">
        <div className="variance-info">
          <h4>Variance Explained</h4>
          <div className="variance-bar">
            <div className="variance-pc1" style={{ width: `${(data?.explained_variance[0] || 0) * 100}%` }}>
              PC1: {((data?.explained_variance[0] || 0) * 100).toFixed(0)}%
            </div>
            <div className="variance-pc2" style={{ width: `${(data?.explained_variance[1] || 0) * 100}%` }}>
              PC2: {((data?.explained_variance[1] || 0) * 100).toFixed(0)}%
            </div>
          </div>
        </div>
        {zoomLevel !== 1 && (
          <div className="zoom-indicator">
            Zoom: {(zoomLevel * 100).toFixed(0)}%
          </div>
        )}
      </div>
    </div>
  )
}