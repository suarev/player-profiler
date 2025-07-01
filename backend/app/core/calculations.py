import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from app.core.database import execute_query
from app.core.metrics import FORWARD_METRICS
from app.services.player_images import player_image_service

class PlayerAnalyzer:
    def __init__(self):
        self.position = "forward"
        self._load_data()
        
    def _load_data(self):
        """Load all forward data with precomputed percentiles"""
        try:
            # Get forwards with their precomputed percentiles AND stats
            query = """
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                p.age,
                pp.percentiles,
                s.performance_gls,
                s.performance_ast,
                s.expected_xg,
                sh.standard_sh,
                pos.touches_att_pen
            FROM football_data.players p
            JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
            LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
            LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
            LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
            WHERE pp.position_group = 'forward'
            """
            
            self.df = execute_query(query)
            
            # Expand the JSON percentiles into columns more efficiently
            if not self.df.empty and 'percentiles' in self.df.columns:
                import json
                
                # Method 1: Collect all percentile data first, then create DataFrame
                percentile_data = {}
                
                for idx, row in self.df.iterrows():
                    percentiles = json.loads(row['percentiles']) if isinstance(row['percentiles'], str) else row['percentiles']
                    for key, value in percentiles.items():
                        col_name = f"{key}_pct"
                        if col_name not in percentile_data:
                            percentile_data[col_name] = {}
                        percentile_data[col_name][idx] = value
                
                # Create a new DataFrame from the collected data and join it all at once
                if percentile_data:
                    percentile_df = pd.DataFrame.from_dict(percentile_data)
                    percentile_df.index = self.df.index
                    # Join all columns at once to avoid fragmentation
                    self.df = pd.concat([self.df, percentile_df], axis=1)
            
            print(f"Loaded {len(self.df)} forwards with precomputed percentiles")
            
            # Convert numeric columns
            numeric_cols = ['performance_gls', 'performance_ast', 'expected_xg', 'n_90s', 'standard_sh', 'touches_att_pen']
            for col in numeric_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
            
        except Exception as e:
            print(f"Error loading data: {e}")
            # Fallback
            self._load_data_fallback()
                        
    def _compute_percentiles(self):
        """Compute percentile ranks for all numeric columns"""
        # First, identify truly numeric columns by trying to convert them
        for col in self.df.columns:
            if col not in ['player_id', 'id', 'age', 'name', 'team', 'position', 'player', 'nation', 'born', 'league', 'season']:
                try:
                    # Try to convert to numeric
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                except:
                    pass
        
        # Now get numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col not in ['player_id', 'id', 'age']:
                # Create percentile column
                self.df[f"{col}_pct"] = self.df[col].rank(pct=True, na_option='keep') * 100

    def calculate_metric_scores(self, metric_weights: Dict[str, float]) -> pd.DataFrame:
        """Calculate composite scores for each metric based on user preferences"""
        scores_df = self.df[['player_id', 'name', 'team', 'position', 'age']].copy()
        
        for metric_id, user_weight in metric_weights.items():
            if metric_id in FORWARD_METRICS:
                metric_info = FORWARD_METRICS[metric_id]
                
                # Calculate composite score for this metric
                metric_score = pd.Series([0] * len(self.df), index=self.df.index)
                valid_cols = 0
                
                for col, col_weight in metric_info['weights'].items():
                    pct_col = f"{col}_pct"
                    if pct_col in self.df.columns:
                        # Fill NaN with 50th percentile (average)
                        col_values = self.df[pct_col].fillna(50)
                        metric_score += col_values * col_weight
                        valid_cols += 1
                
                # If no valid columns found, use a default score
                if valid_cols == 0:
                    print(f"Warning: No percentile data found for metric {metric_id}")
                    metric_score = pd.Series([50] * len(self.df), index=self.df.index)
                
                # Apply user weight (0-100 scale)
                # If user_weight is 0, the metric won't contribute
                scores_df[f"{metric_id}_score"] = metric_score * (user_weight / 100)
        
        return scores_df            
        
    def apply_algorithm(self, scores_df: pd.DataFrame, algorithm: str) -> pd.DataFrame:
        """Apply the selected algorithm to rank players"""
        score_cols = [col for col in scores_df.columns if col.endswith('_score')]
        
        if algorithm == "weighted_score":
            # Simple sum of weighted scores
            scores_df['final_score'] = scores_df[score_cols].sum(axis=1)
            
            # Scale to a more meaningful range (0-1000)
            max_possible = len(score_cols) * 100  # If all metrics at 100
            scores_df['final_score'] = (scores_df['final_score'] / max_possible) * 1000
        
        return scores_df.sort_values('final_score', ascending=False)

    # Update the get_recommendations method (partial update showing the changed section)
    def get_recommendations(self, weights: Dict[str, float], algorithm: str = "weighted_score", limit: int = 3):
        """Get top player recommendations"""
        try:
            scores_df = self.calculate_metric_scores(weights)
            ranked_df = self.apply_algorithm(scores_df, algorithm)
            
            recommendations = []
            ranked_df = ranked_df.drop_duplicates(subset=['player_id'])
            for _, player in ranked_df.head(limit).iterrows():  
                # Get key stats for this player
                player_data = self.df[self.df['player_id'] == player['player_id']].iloc[0]
                
                # Safely get stats with defaults
                n_90s = float(player_data.get('n_90s', 1)) if pd.notna(player_data.get('n_90s')) else 1.0
                n_90s = max(n_90s, 0.1)  # Avoid division by zero
                
                # Get player name and team
                player_name = player['name']
                player_team = player.get('team', 'Unknown')
                
                # Get player image
                player_image = None
                try:
                    # Try to get image from Google Custom Search
                    player_image = player_image_service.search_player_image(player_name, player_team)
                    
                    # If no image found, use fallback
                    if not player_image:
                        player_image = player_image_service.get_fallback_image(player_name)
                        
                except Exception as e:
                    print(f"Error getting image for {player_name}: {e}")
                    player_image = player_image_service.get_fallback_image(player_name)
                
                key_stats = {
                    "goals": float(player_data.get('performance_gls', 0)) if pd.notna(player_data.get('performance_gls')) else 0.0,
                    "xG": float(player_data.get('expected_xg', 0)) if pd.notna(player_data.get('expected_xg')) else 0.0,
                    "shots": float(player_data.get('standard_sh', 0)) if pd.notna(player_data.get('standard_sh')) else 0.0,
                    "assists": float(player_data.get('performance_ast', 0)) if pd.notna(player_data.get('performance_ast')) else 0.0
                }
                
                # Get percentile ranks for display
                percentiles = {}
                for metric_id in weights.keys():
                    if metric_id in FORWARD_METRICS:
                        # Average percentile across the metric's columns
                        cols = FORWARD_METRICS[metric_id]['columns']
                        pct_values = []
                        for col in cols:
                            pct_col = f"{col}_pct"
                            if pct_col in player_data:
                                val = player_data[pct_col]
                                if pd.notna(val):
                                    pct_values.append(float(val))
                        
                        if pct_values:
                            percentiles[metric_id] = np.mean(pct_values)
                        else:
                            percentiles[metric_id] = 50.0  # Default to average
                
                # Add raw percentiles for radar chart
                raw_percentiles = [
                    'performance_gls_pct',
                    'expected_npxg_pct', 
                    'standard_sot_pct',
                    'performance_ast_pct',
                    'expected_xag_pct',
                    'kp_pct',
                    'take_ons_succ_pct',
                    'aerial_duels_wonpct_pct',
                    'touches_att_pen_pct',
                    'carries_prgc_pct'
                ]

                for pct_col in raw_percentiles:
                    if pct_col in player_data.index:
                        val = player_data[pct_col]
                        if pd.notna(val):
                            percentiles[pct_col] = float(val)
                        else:
                            percentiles[pct_col] = 50.0
                    else:
                        percentiles[pct_col] = 50.0
                
                recommendations.append({
                    "player_id": int(player['player_id']),
                    "name": player_name,
                    "team": player_team,
                    "position": player.get('position', 'FW'),
                    "match_score": float(player.get('final_score', 0)),
                    "key_stats": key_stats,
                    "percentile_ranks": percentiles,
                    "image_url": player_image  # ADD THIS LINE
                })
        
            return recommendations
            
        except Exception as e:
            print(f"Error in get_recommendations: {e}")
            # Return mock data on error
            return [
                {
                    "player_id": 1,
                    "name": "Error - Check Database",
                    "team": "N/A",
                    "position": "FW",
                    "match_score": 0.0,
                    "key_stats": {"goals": 0.0, "xG": 0.0, "shots": 0.0, "assists": 0.0},
                    "percentile_ranks": {k: 50.0 for k in weights.keys()},
                    "image_url": None
                }
            ]