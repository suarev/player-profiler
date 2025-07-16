import { useState, useEffect } from 'react'

interface MousePosition {
  x: number
  y: number
}

export const useMousePosition = () => {
  const [mousePosition, setMousePosition] = useState<MousePosition>({ x: 0, y: 0 })
  const [cursorPosition, setCursorPosition] = useState<MousePosition>({ x: 0, y: 0 })

  useEffect(() => {
    const updateMousePosition = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY })
    }

    window.addEventListener('mousemove', updateMousePosition)

    return () => {
      window.removeEventListener('mousemove', updateMousePosition)
    }
  }, [])

  useEffect(() => {
    const animateCursor = () => {
      setCursorPosition(prev => {
        const dx = mousePosition.x - prev.x
        const dy = mousePosition.y - prev.y
        
        return {
          x: prev.x + dx * 0.8,
          y: prev.y + dy * 0.8
        }
      })
      
      requestAnimationFrame(animateCursor)
    }
    
    const animationId = requestAnimationFrame(animateCursor)
    
    return () => cancelAnimationFrame(animationId)
  }, [mousePosition])

  return { mousePosition, cursorPosition }
}