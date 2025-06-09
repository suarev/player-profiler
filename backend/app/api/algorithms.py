from fastapi import APIRouter
from typing import List
from app.models.schemas import Algorithm
from app.core.metrics import ALGORITHMS

router = APIRouter()

@router.get("/list", response_model=List[Algorithm])
async def get_algorithms():
    """Get all available recommendation algorithms"""
    return [
        Algorithm(
            id=algo_id,
            name=info["name"],
            description=info["description"]
        )
        for algo_id, info in ALGORITHMS.items()
    ]