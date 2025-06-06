import Link from 'next/link'

export default function Navigation() {
  return (
    <nav>
      <Link href="#about">ABOUT</Link>
      <Link href="#methodology">METHODOLOGY</Link>
      <Link href="#contact">CONTACT</Link>
    </nav>
  )
}