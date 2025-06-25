# backend/app/api/forwards.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional  # ADD Optional here
import pandas as pd
from app.models.schemas import (
    RecommendationRequest, 
    RecommendationResponse,
    ForwardMetric,
    PCAResponse
)
from app.core.metrics import FORWARD_METRICS
from app.core.database import execute_query

router = APIRouter()

# Lazy initialization
_analyzer = None
_pca_analyzer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        from app.core.calculations import PlayerAnalyzer
        _analyzer = PlayerAnalyzer()
    return _analyzer

def get_pca_analyzer():
    global _pca_analyzer
    if _pca_analyzer is None:
        from app.core.pca_analysis import ForwardPCAAnalyzer
        _pca_analyzer = ForwardPCAAnalyzer()
    return _pca_analyzer

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
async def get_pca_data(k: Optional[int] = None):
    """
    Get PCA coordinates for all forwards
    Args:
        k: Optional number of clusters (if not provided, uses optimal)
    """
    try:
        # Get the data - reuse the same data structure from PlayerAnalyzer
        query = """
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                pp.percentiles,
                -- Add these for filtering
                s.performance_gls,
                s.playing_time_90s
            FROM football_data.players p
            JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
            LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
            WHERE pp.position_group = 'forward'
            AND pp.percentiles IS NOT NULL
            -- ADD FILTERS HERE:
            AND CAST(s.performance_gls AS FLOAT) >= 5  -- Min 5 goals
            AND CAST(s.playing_time_90s AS FLOAT) >= 10  -- Min 10 90s played
        """
        
        df = execute_query(query)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No forward data found")
        
        # Expand percentiles JSON into columns more efficiently
        import json
        
        # Collect all percentile columns first
        percentile_data = {}
        
        for idx, row in df.iterrows():
            percentiles = json.loads(row['percentiles']) if isinstance(row['percentiles'], str) else row['percentiles']
            for key, value in percentiles.items():
                if value is not None:  # Only add non-null percentiles
                    col_name = f"{key}_pct"
                    if col_name not in percentile_data:
                        percentile_data[col_name] = {}
                    percentile_data[col_name][idx] = value
        
        # Convert to DataFrame and join all at once
        if percentile_data:
            percentile_df = pd.DataFrame.from_dict(percentile_data)
            percentile_df.index = df.index
            df = pd.concat([df, percentile_df], axis=1)
        
        # Get PCA analyzer and compute with custom k if provided
        pca_analyzer = get_pca_analyzer()
        print(f"Computing PCA with k={k}")  # Debug log
        pca_results = pca_analyzer.compute_pca(df, custom_k=k)  # Pass the k parameter
        
        # Format for response
        return PCAResponse(
            points=pca_results["points"],
            explained_variance=pca_results["explained_variance"],
            pc_interpretation=pca_results["pc_interpretation"],
            cluster_centers=pca_results.get("cluster_centers", [])
        )
        
    except ValueError as e:
        # Not enough data for PCA
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"PCA Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        # Return the fallback mock data...