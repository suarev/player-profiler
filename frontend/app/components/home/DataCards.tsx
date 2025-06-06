'use client'

import { useEffect, useRef } from 'react'

interface DataCard {
  label: string
  value: string
  player: string
  className: string
}

const dataCards: DataCard[] = [
  {
    label: 'PROGRESSIVE CARRIES',
    value: '8.7',
    player: 'B. Saka',
    className: 'card-1'
  },
  {
    label: 'XA PER 90',
    value: '0.41',
    player: 'K. De Bruyne',
    className: 'card-2'
  },
  {
    label: 'PRESS RESISTANCE',
    value: '94%',
    player: 'Rodri',
    className: 'card-3'
  }
]

export default function DataCards() {
  const cardsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!cardsRef.current) return
      
      const cards = cardsRef.current.querySelectorAll('.data-card')
      const x = (e.clientX / window.innerWidth - 0.5) * 2
      const y = (e.clientY / window.innerHeight - 0.5) * 2
      
      cards.forEach((card, index) => {
        const speed = (index + 1) * 5
        const element = card as HTMLElement
        element.style.transform = `translate(${x * speed}px, ${y * speed}px)`
      })
    }

    const handleClick = (e: Event) => {
      const target = e.target as HTMLElement
      if (target.closest('.data-card')) {
        target.style.transform = 'scale(0.98)'
        setTimeout(() => {
          target.style.transform = ''
        }, 100)
      }
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('click', handleClick)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('click', handleClick)
    }
  }, [])

  return (
    <div className="visual-side" ref={cardsRef}>
      {dataCards.map((card, index) => (
        <div key={index} className={`data-card ${card.className}`}>
          <div className="card-label">{card.label}</div>
          <div className="card-value">{card.value}</div>
          <div className="card-player">{card.player}</div>
        </div>
      ))}
    </div>
  )
}