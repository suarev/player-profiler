'use client'

import { useState } from 'react'
import { Algorithm } from '@/app/types/analysis'

interface AlgorithmSelectorProps {
  algorithms: Algorithm[]
  selectedAlgorithm: string
  onAlgorithmChange: (algorithm: string) => void
}

export default function AlgorithmSelector({ 
  algorithms, 
  selectedAlgorithm, 
  onAlgorithmChange 
}: AlgorithmSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  
  const currentAlgorithm = algorithms.find(a => a.id === selectedAlgorithm)

  return (
    <div className="algorithm-selector-wrapper">
      <div 
        className="algorithm-selector"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div>
          <div className="algorithm-name">
            {currentAlgorithm?.name || 'Select Algorithm'}
          </div>
          <div className="algorithm-desc">
            {currentAlgorithm?.description || ''}
          </div>
        </div>
        <svg 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor"
          className={`dropdown-icon ${isOpen ? 'open' : ''}`}
        >
          <path d="M6 9l6 6 6-6" strokeWidth="2"/>
        </svg>
      </div>

      {isOpen && (
        <div className="algorithm-dropdown">
          {algorithms.map(algo => (
            <div
              key={algo.id}
              className={`algorithm-option ${algo.id === selectedAlgorithm ? 'selected' : ''}`}
              onClick={() => {
                onAlgorithmChange(algo.id)
                setIsOpen(false)
              }}
            >
              <div className="algorithm-name">{algo.name}</div>
              <div className="algorithm-desc">{algo.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}