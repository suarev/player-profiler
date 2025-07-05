# backend/app/api/positions.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import pandas as pd
from app.models.schemas import (
    RecommendationRequest, 
    RecommendationResponse,
    ForwardMetric,
    PCAResponse
)
from app.core.position_metrics import POSITION_METRICS, POSITION_COLORS
from app.core.database import execute_query

router = APIRouter()

# Lazy initialization for each position
_analyzers = {}
_pca_analyzers = {}

def get_analyzer(position: str):
    if position not in _analyzers:
        from app.core.generic_analyzer import GenericPlayerAnalyzer
        _analyzers[position] = GenericPlayerAnalyzer(position)
    return _analyzers[position]

def get_pca_analyzer(position: str):
    if position not in _pca_analyzers:
        from app.core.generic_pca import GenericPCAAnalyzer
        _pca_analyzers[position] = GenericPCAAnalyzer(position)
    return _pca_analyzers[position]

@router.get("/{position}/metrics", response_model=List[ForwardMetric])
async def get_position_metrics(position: str):
    """Get all available metrics for a position"""
    if position not in POSITION_METRICS:
        raise HTTPException(status_code=404, detail=f"Position {position} not found")
    
    metrics = []
    for metric_id, info in POSITION_METRICS[position].items():
        metrics.append(ForwardMetric(
            id=metric_id,
            name=info["name"],
            description=info["description"],
            stat_columns=info["columns"]
        ))
    return metrics

@router.post("/{position}/recommend", response_model=RecommendationResponse)
async def get_recommendations(position: str, request: RecommendationRequest):
    """Get top player recommendations for any position"""
    if position not in POSITION_METRICS:
        raise HTTPException(status_code=404, detail=f"Position {position} not found")
    
    try:
        # Convert weights to dict format
        weights = {w.metric: w.weight for w in request.weights}
        
        # Validate metrics for this position
        for metric in weights.keys():
            if metric not in POSITION_METRICS[position]:
                raise HTTPException(status_code=400, detail=f"Invalid metric for {position}: {metric}")
        
        # Get recommendations
        analyzer = get_analyzer(position)
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

@router.get("/{position}/pca-data", response_model=PCAResponse)
async def get_pca_data(position: str, k: Optional[int] = None):
    """Get PCA coordinates for all players in a position"""
    if position not in POSITION_METRICS:
        raise HTTPException(status_code=404, detail=f"Position {position} not found")
    
    try:
        # Map position to position_group in database
        position_mapping = {
            "forward": "forward",
            "midfielder": "midfielder", 
            "defender": "defender",
            "goalkeeper": "goalkeeper"
        }
        
        position_group = position_mapping.get(position)
        if not position_group:
            raise HTTPException(status_code=400, detail=f"Invalid position: {position}")
        
        # Get the data
        query = f"""
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                pp.percentiles,
                s.playing_time_90s
            FROM football_data.players p
            JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
            LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
            WHERE pp.position_group = '{position_group}'
            AND pp.percentiles IS NOT NULL
            AND CAST(s.playing_time_90s AS FLOAT) >= 10
        """
        
        # Add position-specific filters
        if position == "goalkeeper":
            query = f"""
                SELECT 
                    p.id as player_id,
                    p.name,
                    p.team,
                    p.position,
                    pp.percentiles,
                    CAST(k.playing_time_min AS FLOAT) / 90 as playing_time_90s
                FROM football_data.players p
                JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
                LEFT JOIN football_data.player_keeper_stats k ON p.name = k.player
                WHERE pp.position_group = 'goalkeeper'
                AND pp.percentiles IS NOT NULL
                AND CAST(k.playing_time_min AS FLOAT) >= 900  -- 10 games worth of minutes
            """
        
        df = execute_query(query)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No {position} data found")
        
        # Expand percentiles
        import json
        percentile_data = {}
        
        for idx, row in df.iterrows():
            percentiles = json.loads(row['percentiles']) if isinstance(row['percentiles'], str) else row['percentiles']
            for key, value in percentiles.items():
                if value is not None:
                    col_name = f"{key}_pct"
                    if col_name not in percentile_data:
                        percentile_data[col_name] = {}
                    percentile_data[col_name][idx] = value
        
        if percentile_data:
            percentile_df = pd.DataFrame.from_dict(percentile_data)
            percentile_df.index = df.index
            df = pd.concat([df, percentile_df], axis=1)
        
        # Get PCA analyzer and compute
        pca_analyzer = get_pca_analyzer(position)
        pca_results = pca_analyzer.compute_pca(df, custom_k=k)
        
        return PCAResponse(
            points=pca_results["points"],
            explained_variance=pca_results["explained_variance"],
            pc_interpretation=pca_results["pc_interpretation"],
            cluster_centers=pca_results.get("cluster_centers", [])
        )
        
    except Exception as e:
        print(f"PCA Error for {position}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{position}/color")
async def get_position_color(position: str):
    """Get the theme color for a position"""
    if position not in POSITION_COLORS:
        raise HTTPException(status_code=404, detail=f"Position {position} not found")
    
    return {"color": POSITION_COLORS[position]}