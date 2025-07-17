'use client'

import { useEffect, useRef, useState } from 'react'
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

  useEffect(() => {
    if (!data || !svgRef.current) return

    // Clear previous content
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // Fixed dimensions - let's just hardcode them for now
    const width = 800
    const height = 600
    const margin = { top: 40, right: 40, bottom: 60, left: 60 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    // Set SVG size
    svg
      .attr('width', width)
      .attr('height', height)

    // Create main group
    const g = svg.append('g')
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

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).ticks(5))
      .style('color', 'rgba(255, 255, 255, 0.5)')

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(5))
      .style('color', 'rgba(255, 255, 255, 0.5)')

    // Color scale
    const uniqueClusters = Array.from(new Set(data.points.map(p => p.cluster).filter(Boolean))) as string[]
    const colorScale = d3.scaleOrdinal<string>()
      .domain(uniqueClusters)
      .range(['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#f9ca24', '#f0932b', '#6c5ce7', '#a29bfe'])

    // Add points
    g.selectAll('.point')
      .data(data.points)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => highlightedPlayers.includes(d.player_id) ? 7 : 4)
      .attr('fill', d => d.cluster ? colorScale(d.cluster) : 'rgba(255, 255, 255, 0.6)')
      .attr('stroke', d => highlightedPlayers.includes(d.player_id) ? '#fff' : 'none')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseenter', function(event, d) {
        setHoveredPlayer({ name: d.name, team: d.team })
        const rect = containerRef.current?.getBoundingClientRect()
        if (rect) {
          setMousePos({ 
            x: event.clientX - rect.left, 
            y: event.clientY - rect.top - 20 
          })
        }
      })
      .on('mouseleave', function() {
        setHoveredPlayer(null)
      })

  }, [data, highlightedPlayers])

  if (!data) return <div>No PCA data available</div>

  return (
    <div className="pca-viz-container" ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '700px' }}>
      {/* SVG Canvas with fixed size */}
      <svg 
        ref={svgRef} 
        style={{ 
          width: '100%', 
          maxWidth: '800px',
          height: '600px',
          display: 'block',
          margin: '0 auto',
          background: 'rgba(0, 0, 0, 0.5)'
        }} 
      />
      
      {/* Tooltip */}
      {hoveredPlayer && (
        <div 
          className="pca-hover-tooltip"
          style={{ 
            position: 'absolute',
            left: `${mousePos.x}px`, 
            top: `${mousePos.y}px`,
            background: 'rgba(0, 0, 0, 0.9)',
            color: 'white',
            padding: '8px',
            borderRadius: '4px',
            pointerEvents: 'none'
          }}
        >
          {hoveredPlayer.name} ({hoveredPlayer.team})
        </div>
      )}
    </div>
  )
}