'use client'

import { useEffect, useState } from 'react'
import { useMousePosition } from '@/app/hooks/useMousePosition'

export default function CustomCursor() {
  const [isHovering, setIsHovering] = useState(false)
  const { cursorPosition } = useMousePosition()

  useEffect(() => {
    const handleMouseEnter = () => setIsHovering(true)
    const handleMouseLeave = () => setIsHovering(false)

    const updateHoverElements = () => {
      const hoverElements = document.querySelectorAll('a, .data-card, .position-column, button, .scroll-indicator')
      
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
    }

    // Initial setup
    const cleanup = updateHoverElements()

    // Re-run when DOM changes (for dynamically added elements)
    const observer = new MutationObserver(() => {
      cleanup()
      updateHoverElements()
    })

    observer.observe(document.body, { childList: true, subtree: true })

    return () => {
      cleanup()
      observer.disconnect()
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