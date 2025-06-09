from pydantic import BaseModel
from typing import List, Dict, Optional

class MetricWeight(BaseModel):
    """Single metric weight from frontend sliders"""
    metric: str
    weight: float  # 0-100 from slider

class RecommendationRequest(BaseModel):
    """Request body for player recommendations"""
    weights: List[MetricWeight]
    algorithm: str = "weighted_score"
    limit: int = 3

class PlayerRecommendation(BaseModel):
    """Single player recommendation"""
    player_id: int
    name: str
    team: str
    position: str
    match_score: float
    key_stats: Dict[str, float]
    percentile_ranks: Dict[str, float]

class RecommendationResponse(BaseModel):
    """Response with top player recommendations"""
    algorithm_used: str
    recommendations: List[PlayerRecommendation]

class PCAPoint(BaseModel):
    """Single point for PCA visualization"""
    player_id: int
    name: str
    team: str
    x: float
    y: float
    cluster: Optional[str] = None

class PCAResponse(BaseModel):
    """PCA data for visualization"""
    points: List[PCAPoint]
    explained_variance: List[float]

class Algorithm(BaseModel):
    """Algorithm description"""
    id: str
    name: str
    description: str

class ForwardMetric(BaseModel):
    """Metric definition for forwards"""
    id: str
    name: str
    description: str
    stat_columns: List[str]  # Which FBref columns contribute to this metric