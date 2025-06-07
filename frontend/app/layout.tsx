import type { Metadata } from 'next'
import './globals.css'
import './styles/animations.css'
import './styles/positions.css'

export const metadata: Metadata = {
  title: 'LENS - Bring Players Into Focus',
  description: 'Find Premier League players by profiling them, not just reviewing stats.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  )
}