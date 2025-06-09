from fastapi import APIRouter, HTTPException
from typing import List
import os
from app.models.schemas import (
    RecommendationRequest, 
    RecommendationResponse,
    ForwardMetric,
    PCAResponse
)
from app.core.metrics import FORWARD_METRICS

router = APIRouter()

# Lazy initialization
_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        # Only import when needed to avoid startup issues
        from app.core.calculations import PlayerAnalyzer
        _analyzer = PlayerAnalyzer()
    return _analyzer

@router.get("/metrics", response_model=List[ForwardMetric])
async def get_forward_metrics():
    """Get all available metrics for forwards with descriptions"""
    metrics = []
    for metric_id, info in FORWARD_METRICS.items():
        metrics.append(ForwardMetric(
            id=metric_id,
            name=info["name"],
            description=info["description"],
            stat_columns=info["columns"]
        ))
    return metrics

@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """Get top forward recommendations based on preferences"""
    try:
        # Convert weights to dict format
        weights = {w.metric: w.weight for w in request.weights}
        
        # Validate metrics
        for metric in weights.keys():
            if metric not in FORWARD_METRICS:
                raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")
        
        # Get recommendations
        analyzer = get_analyzer()
        recommendations = analyzer.get_recommendations(
            weights=weights,
            algorithm=request.algorithm,
            limit=request.limit
        )
        
        return RecommendationResponse(
            algorithm_used=request.algorithm,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pca-data", response_model=PCAResponse)
async def get_pca_data():
    """Get PCA coordinates for all forwards"""
    # For now, return mock data - we'll implement PCA computation later
    return PCAResponse(
        points=[
            {"player_id": 1, "name": "Haaland", "team": "Man City", "x": 0.8, "y": 0.2, "cluster": "target_forward"},
            {"player_id": 2, "name": "Kane", "team": "Bayern", "x": 0.6, "y": 0.4, "cluster": "complete_forward"},
            {"player_id": 3, "name": "Jesus", "team": "Arsenal", "x": 0.2, "y": 0.7, "cluster": "false_nine"},
        ],
        explained_variance=[0.35, 0.25]
    )