import DataCards from './DataCards'

export default function HeroSection() {
  return (
    <div className="container">
      <div className="content">
        {/* Left Side - Text */}
        <div className="text-side">
          <div className="logo">LENS™</div>
          
          <h1 className="main-title">
            <span className="line">BRING PLAYERS INTO</span>
            <span className="line accent">FOCUS</span>
          </h1>
          
          <p className="description">
            Find Premier League players by profiling them, not just reviewing stats. Use LENS to weight different attributes and get personalized recommendations. 
            See where every player sits in our data visualization to understand the full picture.
          </p>
          

        </div>

        {/* Right Side - Visual */}
        <DataCards />
      </div>
    </div>
  )
}