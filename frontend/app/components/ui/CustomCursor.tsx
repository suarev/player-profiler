'use client'

import { useEffect, useState } from 'react'
import { useMousePosition } from '@/app/hooks/useMousePosition'

export default function CustomCursor() {
  const [isHovering, setIsHovering] = useState(false)
  const { cursorPosition } = useMousePosition()

  useEffect(() => {
    const handleMouseEnter = () => setIsHovering(true)
    const handleMouseLeave = () => setIsHovering(false)

    const hoverElements = document.querySelectorAll('a, .data-card')
    
    hoverElements.forEach(elem => {
      elem.addEventListener('mouseenter', handleMouseEnter)
      elem.addEventListener('mouseleave', handleMouseLeave)
    })

    return () => {
      hoverElements.forEach(elem => {
        elem.removeEventListener('mouseenter', handleMouseEnter)
        elem.removeEventListener('mouseleave', handleMouseLeave)
      })
    }
  }, [])

  return (
    <div 
      className={`cursor ${isHovering ? 'hover' : ''}`}
      style={{
        left: `${cursorPosition.x}px`,
        top: `${cursorPosition.y}px`,
      }}
    />
  )
}