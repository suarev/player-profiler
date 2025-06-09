from fastapi import APIRouter, HTTPException
from typing import Dict
from app.core.database import execute_query

router = APIRouter()

@router.get("/percentiles/{position}/{player_id}", response_model=Dict[str, float])
async def get_player_percentiles(position: str, player_id: int):
    """Get percentile ranks for a specific player"""
    # For now, return mock data
    return {
        "finishing": 95.5,
        "physical": 88.2,
        "creativity": 45.3,
        "pace_dribbling": 72.1,
        "work_rate": 65.8,
        "positioning": 92.3,
        "linkup": 58.9
    }