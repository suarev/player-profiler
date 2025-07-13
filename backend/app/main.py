from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, os
from app.core.config import settings


# Import routers after creating app
app = FastAPI(
    title="LENS Player Profiler API",
    description="API for football player profiling and recommendations",
    version="1.0.0"
)

# Import here to avoid circular imports
from app.api import positions, algorithms, stats

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(algorithms.router, prefix="/api/algorithms", tags=["algorithms"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])

@app.get("/")
async def root():
    return {"message": "LENS Player Profiler API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
