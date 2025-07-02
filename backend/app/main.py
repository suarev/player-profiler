from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.init_db import init_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    yield
    # Shutdown

app = FastAPI(
    title="LENS Player Profiler API",
    description="API for football player profiling and recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Import here to avoid circular imports
from app.api import forwards, algorithms, stats

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(forwards.router, prefix="/api/forwards", tags=["forwards"])
app.include_router(algorithms.router, prefix="/api/algorithms", tags=["algorithms"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])



@app.get("/")
async def root():
    return {"message": "LENS Player Profiler API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Add after creating the app
@app.on_event("startup")
async def startup_event():
    init_database()