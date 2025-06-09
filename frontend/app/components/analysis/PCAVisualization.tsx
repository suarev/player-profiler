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
  const [tooltip, setTooltip] = useState<{ x: number; y: number; player: string } | null>(null)

  useEffect(() => {
    if (!data || !svgRef.current) return

    // Clear previous visualization
    d3.select(svgRef.current).selectAll('*').remove()

    // Set dimensions and margins
    const margin = { top: 40, right: 40, bottom: 60, left: 60 }
    const width = svgRef.current.clientWidth - margin.left - margin.right
    const height = svgRef.current.clientHeight - margin.top - margin.bottom

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Create scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(data.points, d => d.x) as [number, number])
      .range([0, width])
      .nice()

    const yScale = d3.scaleLinear()
      .domain(d3.extent(data.points, d => d.y) as [number, number])
      .range([height, 0])
      .nice()

    // Add grid
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .style('color', 'rgba(255, 255, 255, 0.5)')

    g.append('g')
      .call(d3.axisLeft(yScale))
      .style('color', 'rgba(255, 255, 255, 0.5)')

    // Add axis labels
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.5)')
      .style('font-size', '12px')
      .text(`PC2 - Playmaking (${(data.explained_variance[1] * 100).toFixed(0)}% variance)`)

    g.append('text')
      .attr('transform', `translate(${width / 2}, ${height + margin.bottom})`)
      .style('text-anchor', 'middle')
      .style('fill', 'rgba(255, 255, 255, 0.5)')
      .style('font-size', '12px')
      .text(`PC1 - Goal Threat (${(data.explained_variance[0] * 100).toFixed(0)}% variance)`)

    // Color scale for clusters
    const colorScale = d3.scaleOrdinal()
      .domain(['target_forward', 'complete_forward', 'false_nine', 'poacher'])
      .range(['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'])

    // Add points
    const points = g.selectAll('.pca-point')
      .data(data.points)
      .enter().append('circle')
      .attr('class', 'pca-point')
      .attr('cx', d => xScale(d.x))
      .attr('cy', d => yScale(d.y))
      .attr('r', d => highlightedPlayers.includes(d.player_id) ? 8 : 5)
      .attr('fill', d => d.cluster ? colorScale(d.cluster) as string : 'rgba(255, 255, 255, 0.6)')
      .attr('stroke', d => highlightedPlayers.includes(d.player_id) ? '#fff' : 'none')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .style('opacity', d => highlightedPlayers.includes(d.player_id) ? 1 : 0.7)
      .on('mouseover', function(event, d) {
        d3.select(this).attr('r', 10)
        const [x, y] = d3.pointer(event, svg.node())
        setTooltip({ x, y: y - 20, player: `${d.name} (${d.team})` })
      })
      .on('mouseout', function(event, d) {
        d3.select(this).attr('r', highlightedPlayers.includes(d.player_id) ? 8 : 5)
        setTooltip(null)
      })

    // Add legend
    const legend = svg.append('g')
      .attr('transform', `translate(${width - 150}, 20)`)

    const legendData = [
      { cluster: 'target_forward', label: 'Target Forwards' },
      { cluster: 'complete_forward', label: 'Complete Forwards' },
      { cluster: 'false_nine', label: 'False 9s' },
      { cluster: 'poacher', label: 'Poachers' }
    ]

    legend.selectAll('.legend-item')
      .data(legendData)
      .enter().append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 20})`)
      .each(function(d) {
        d3.select(this).append('circle')
          .attr('r', 5)
          .attr('fill', colorScale(d.cluster) as string)

        d3.select(this).append('text')
          .attr('x', 10)
          .attr('y', 5)
          .style('fill', 'rgba(255, 255, 255, 0.8)')
          .style('font-size', '12px')
          .text(d.label)
      })

  }, [data, highlightedPlayers])

  return (
    <div className="pca-container">
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
    </div>
  )
}