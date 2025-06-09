# Backend Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Ensure PostgreSQL is Running**
   ```bash
   # Check if Docker containers are up
   cd ../infrastructure
   docker-compose ps
   
   # If not running:
   docker-compose up -d
   ```

3. **Run the Backend**
   ```bash
   cd backend
   
   # On Mac/Linux:
   chmod +x run.sh
   ./run.sh
   
   # On Windows:
   run.bat
   
   # Or manually:
   uvicorn app.main:app --reload
   ```

4. **Test the API**
   - Open browser: http://localhost:8000/docs
   - Or run: `python test_api.py`

## File Structure Created

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── forwards.py      # Forward-specific endpoints
│   │   ├── algorithms.py    # Algorithm listings
│   │   └── stats.py         # Player statistics
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database connection
│   │   ├── calculations.py  # Player analysis engine
│   │   └── metrics.py       # Metric definitions
│   └── models/              # Data models
│       ├── __init__.py
│       └── schemas.py       # Pydantic models
├── scripts/
│   └── precompute_percentiles.py  # Pre-compute player percentiles
├── requirements.txt
├── run.sh / run.bat         # Start scripts
└── test_api.py              # API test script
```

## Next Steps

1. **Run Percentile Pre-computation** (optional but recommended):
   ```bash
   cd backend/scripts
   python precompute_percentiles.py
   ```

2. **Check API Documentation**
   - Visit: http://localhost:8000/docs
   - Test the endpoints interactively

3. **Frontend Integration**
   - The API is CORS-enabled for localhost:3000
   - Use the `/api/forwards/recommend` endpoint for player recommendations
   - Use the `/api/forwards/pca-data` endpoint for visualization data