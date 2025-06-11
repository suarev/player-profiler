import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from app.core.database import execute_query
from app.core.metrics import FORWARD_METRICS

class PlayerAnalyzer:
    def __init__(self):
        self.position = "forward"
        self._load_data()
        
    def _load_data(self):
        """Load all forward data and compute percentiles"""
        try:
            # Get all forwards with their stats
            query = """
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                p.age
            FROM football_data.players p
            WHERE p.position LIKE '%FW%' OR p.position LIKE '%CF%' OR p.position LIKE '%LW%' OR p.position LIKE '%RW%'
            """
            
            # First try to get basic player info
            self.df = execute_query(query)
            
            # Then try to join stats tables if they exist
            stats_tables = [
                ("player_standard_stats", "s"),
                ("player_shooting_stats", "sh"),
                ("player_passing_stats", "ps"),
                ("player_passing_types_stats", "pt"),
                ("player_goal_shot_creation_stats", "gsc"),
                ("player_defense_stats", "d"),
                ("player_possession_stats", "pos"),
                ("player_misc_stats", "m"),
                ("player_playing_time_stats", "pl")
            ]
            
            for table, alias in stats_tables:
                try:
                    stats_query = f"""
                    SELECT p.name, {alias}.*
                    FROM football_data.players p
                    JOIN football_data.{table} {alias} ON p.name = {alias}.player
                    WHERE p.position LIKE '%FW%' OR p.position LIKE '%CF%' OR p.position LIKE '%LW%' OR p.position LIKE '%RW%'
                    """
                    stats_df = execute_query(stats_query)
                    if not stats_df.empty:
                        self.df = self.df.merge(stats_df, on='name', how='left', suffixes=('', '_dup'))
                        # Drop duplicate columns
                        self.df = self.df.loc[:, ~self.df.columns.str.endswith('_dup')]
                except Exception as e:
                    print(f"Warning: Could not load {table}: {e}")
            
            print(f"Loaded {len(self.df)} forwards")
            self._compute_percentiles()
            
        except Exception as e:
            print(f"Error loading data: {e}")
            # Create a minimal DataFrame for testing
            self.df = pd.DataFrame({
                'player_id': [1, 2, 3],
                'name': ['Test Player 1', 'Test Player 2', 'Test Player 3'],
                'team': ['Team A', 'Team B', 'Team C'],
                'position': ['FW', 'FW', 'FW'],
                'age': [25, 28, 23]
            })
            print("Using test data for now")
        
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
                metric_score = 0
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
                    metric_score = pd.Series([50] * len(self.df), index=self.df.index)
                
                # Apply user weight (convert from 0-100 to 0-1)
                scores_df[f"{metric_id}_score"] = metric_score * (user_weight / 100)
        
        return scores_df
    
    def apply_algorithm(self, scores_df: pd.DataFrame, algorithm: str) -> pd.DataFrame:
        """Apply the selected algorithm to rank players"""
        score_cols = [col for col in scores_df.columns if col.endswith('_score')]

        if algorithm == "weighted_score":
            # Simple sum of weighted scores
            scores_df['final_score'] = scores_df[score_cols].sum(axis=1)
            
        elif algorithm == "multiplicative":
            # Multiplicative - penalizes low scores
            # Normalize to 0-1 first to avoid huge numbers
            normalized = scores_df[score_cols] / 100
            scores_df['final_score'] = normalized.prod(axis=1) * 1000  # Scale back up
            
        elif algorithm == "threshold":
            # Filter players below 30th percentile in any heavily weighted metric
            # Then apply weighted scoring
            mask = pd.Series(True, index=scores_df.index)
            
            # Check each metric's weight from the original input
            for col in score_cols:
                metric_name = col.replace('_score', '')
                # Get the original weight for this metric (it's already applied in the score)
                # We'll consider metrics with score > 50 as "important"
                max_possible_score = 100  # Since we normalized to percentiles
                if scores_df[col].max() > 50:  # If any player has > 50 in this metric, it's weighted highly
                    mask &= (scores_df[col] > 30)
            
            scores_df.loc[~mask, 'final_score'] = 0
            scores_df.loc[mask, 'final_score'] = scores_df.loc[mask, score_cols].sum(axis=1)

        # NORMALIZE TO 0-100 RANGE
        max_score = scores_df['final_score'].max()
        min_score = scores_df['final_score'].min()

        if max_score > min_score:
            scores_df['final_score'] = ((scores_df['final_score'] - min_score) / (max_score - min_score)) * 100
        else:
            scores_df['final_score'] = 50  # All same score

        return scores_df.sort_values('final_score', ascending=False)

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
                
                key_stats = {
                    "goals": float(player_data.get('performance_gls', 0)) if pd.notna(player_data.get('performance_gls')) else 0.0,
                    "xG/90": float(player_data.get('expected_xg', 0)) / n_90s if pd.notna(player_data.get('expected_xg')) else 0.0,
                    "shots/90": float(player_data.get('standard_sh', 0)) / n_90s if pd.notna(player_data.get('standard_sh')) else 0.0,
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
                
                recommendations.append({
                    "player_id": int(player['player_id']),
                    "name": player['name'],
                    "team": player.get('team', 'Unknown'),
                    "position": player.get('position', 'FW'),
                    "match_score": float(player.get('final_score', 0)),
                    "key_stats": key_stats,
                    "percentile_ranks": percentiles
                })
            
            # If we don't have enough real recommendations, add mock data
            if len(recommendations) < limit:
                mock_players = [
                    {
                        "player_id": 999,
                        "name": "Sample Player",
                        "team": "Sample Team",
                        "position": "FW",
                        "match_score": 75.0,
                        "key_stats": {"goals": 15.0, "xG/90": 0.65, "shots/90": 3.2, "assists": 5.0},
                        "percentile_ranks": {k: 75.0 for k in weights.keys()}
                    }
                ]
                recommendations.extend(mock_players[:limit - len(recommendations)])
            
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
                    "key_stats": {"goals": 0.0, "xG/90": 0.0, "shots/90": 0.0, "assists": 0.0},
                    "percentile_ranks": {k: 50.0 for k in weights.keys()}
                }
            ]