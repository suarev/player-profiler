# backend/app/core/generic_analyzer.py
import pandas as pd
import numpy as np
from typing import Dict, List
from app.core.database import execute_query
from app.core.position_metrics import POSITION_METRICS
from app.services.player_images import player_image_service

class GenericPlayerAnalyzer:
    def __init__(self, position: str):
        self.position = position
        self.metrics = POSITION_METRICS.get(position, {})
        self._load_data()
        
    def _load_data(self):
        """Load all player data for the position with precomputed percentiles"""
        try:
            position_mapping = {
                "forward": "forward",
                "midfielder": "midfielder", 
                "defender": "defender",
                "goalkeeper": "goalkeeper"
            }
            
            position_group = position_mapping.get(self.position)
            
            # Build position-specific query
            base_query = f"""
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                p.age,
                pp.percentiles
            """
            
            # Add position-specific stats
            if self.position == "goalkeeper":
                query = base_query + """
                    ,k.performance_saves
                    ,k.performance_savepct
                    ,k.performance_cs
                    ,k.performance_ga
                FROM football_data.players p
                JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
                LEFT JOIN football_data.player_keeper_stats k ON p.name = k.player
                WHERE pp.position_group = 'goalkeeper'
                """
            else:
                query = base_query + """
                    ,s.performance_gls
                    ,s.performance_ast
                    ,s.expected_xg
                    ,s.playing_time_90s
                FROM football_data.players p
                JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
                LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
                WHERE pp.position_group = %s
                """ % f"'{position_group}'"
            
            self.df = execute_query(query)
            
            # Expand percentiles
            if not self.df.empty and 'percentiles' in self.df.columns:
                import json
                
                percentile_data = {}
                for idx, row in self.df.iterrows():
                    percentiles = json.loads(row['percentiles']) if isinstance(row['percentiles'], str) else row['percentiles']
                    for key, value in percentiles.items():
                        col_name = f"{key}_pct"
                        if col_name not in percentile_data:
                            percentile_data[col_name] = {}
                        percentile_data[col_name][idx] = value
                
                if percentile_data:
                    percentile_df = pd.DataFrame.from_dict(percentile_data)
                    percentile_df.index = self.df.index
                    self.df = pd.concat([self.df, percentile_df], axis=1)
            
            print(f"Loaded {len(self.df)} {self.position}s with precomputed percentiles")
            
        except Exception as e:
            print(f"Error loading {self.position} data: {e}")
            self.df = pd.DataFrame()  # Empty fallback

    def calculate_metric_scores(self, metric_weights: Dict[str, float]) -> pd.DataFrame:
        """Calculate composite scores for each metric based on user preferences"""
        scores_df = self.df[['player_id', 'name', 'team', 'position', 'age']].copy()
        
        for metric_id, user_weight in metric_weights.items():
            if metric_id in self.metrics:
                metric_info = self.metrics[metric_id]
                
                # Calculate composite score for this metric
                metric_score = pd.Series([0] * len(self.df), index=self.df.index)
                valid_cols = 0
                
                for col, col_weight in metric_info['weights'].items():
                    pct_col = f"{col}_pct"
                    if pct_col in self.df.columns:
                        col_values = self.df[pct_col].fillna(50)
                        
                        # Handle negative weights (for metrics where lower is better)
                        if col_weight < 0:
                            col_values = 100 - col_values
                            col_weight = abs(col_weight)
                        
                        metric_score += col_values * col_weight
                        valid_cols += 1
                
                if valid_cols == 0:
                    print(f"Warning: No percentile data found for metric {metric_id}")
                    metric_score = pd.Series([50] * len(self.df), index=self.df.index)
                
                scores_df[f"{metric_id}_score"] = metric_score * (user_weight / 100)
        
        return scores_df
    
    def apply_algorithm(self, scores_df: pd.DataFrame, algorithm: str) -> pd.DataFrame:
        """Apply the selected algorithm to rank players"""
        score_cols = [col for col in scores_df.columns if col.endswith('_score')]
        
        if algorithm == "weighted_score":
            scores_df['final_score'] = scores_df[score_cols].sum(axis=1)
            max_possible = len(score_cols) * 100
            scores_df['final_score'] = (scores_df['final_score'] / max_possible) * 1000
        
        return scores_df.sort_values('final_score', ascending=False)

    def get_recommendations(self, weights: Dict[str, float], algorithm: str = "weighted_score", limit: int = 10):
        """Get top player recommendations"""
        try:
            scores_df = self.calculate_metric_scores(weights)
            ranked_df = self.apply_algorithm(scores_df, algorithm)
            
            recommendations = []
            ranked_df = ranked_df.drop_duplicates(subset=['player_id'])
            
            for _, player in ranked_df.head(limit).iterrows():
                player_data = self.df[self.df['player_id'] == player['player_id']].iloc[0]
                
                player_name = player['name']
                player_team = player.get('team', 'Unknown')
                
                # Get player image
                player_image = None
                try:
                    player_image = player_image_service.search_player_image(player_name, player_team)
                    if not player_image:
                        player_image = player_image_service.get_fallback_image(player_name)
                except Exception as e:
                    print(f"Error getting image for {player_name}: {e}")
                    player_image = player_image_service.get_fallback_image(player_name)
                
                # Get position-specific key stats
                key_stats = self._get_key_stats(player_data)
                
                # Get percentile ranks
                percentiles = {}
                for metric_id in weights.keys():
                    if metric_id in self.metrics:
                        cols = self.metrics[metric_id]['columns']
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
                            percentiles[metric_id] = 50.0
                
                # Add raw percentiles for visualization
                self._add_raw_percentiles(player_data, percentiles)
                
                recommendations.append({
                    "player_id": int(player['player_id']),
                    "name": player_name,
                    "team": player_team,
                    "position": player.get('position', self.position.upper()[:2]),
                    "match_score": float(player.get('final_score', 0)),
                    "key_stats": key_stats,
                    "percentile_ranks": percentiles,
                    "image_url": player_image
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in get_recommendations for {self.position}: {e}")
            return []
    
    def _get_key_stats(self, player_data) -> Dict[str, float]:
        """Get position-specific key stats"""
        if self.position == "forward":
            return {
                "goals": float(player_data.get('performance_gls', 0)) if pd.notna(player_data.get('performance_gls')) else 0.0,
                "xG": float(player_data.get('expected_xg', 0)) if pd.notna(player_data.get('expected_xg')) else 0.0,
                "shots": float(player_data.get('standard_sh', 0)) if pd.notna(player_data.get('standard_sh')) else 0.0,
                "assists": float(player_data.get('performance_ast', 0)) if pd.notna(player_data.get('performance_ast')) else 0.0
            }
        elif self.position == "midfielder":
            return {
                "passes": float(player_data.get('total_cmp_pct', 50)) if pd.notna(player_data.get('total_cmp_pct')) else 50.0,
                "key_passes": float(player_data.get('kp_pct', 50)) if pd.notna(player_data.get('kp_pct')) else 50.0,
                "prog_carries": float(player_data.get('carries_prgc_pct', 50)) if pd.notna(player_data.get('carries_prgc_pct')) else 50.0,
                "tackles": float(player_data.get('tackles_tklw_pct', 50)) if pd.notna(player_data.get('tackles_tklw_pct')) else 50.0
            }
        elif self.position == "defender":
            return {
                "tackles": float(player_data.get('tackles_tklw_pct', 50)) if pd.notna(player_data.get('tackles_tklw_pct')) else 50.0,
                "interceptions": float(player_data.get('int_pct', 50)) if pd.notna(player_data.get('int_pct')) else 50.0,
                "aerial_won": float(player_data.get('aerial_duels_wonpct_pct', 50)) if pd.notna(player_data.get('aerial_duels_wonpct_pct')) else 50.0,
                "prog_passes": float(player_data.get('prgp_pct', 50)) if pd.notna(player_data.get('prgp_pct')) else 50.0
            }
        elif self.position == "goalkeeper":
            return {
                "save_pct": float(player_data.get('performance_savepct', 0)) if pd.notna(player_data.get('performance_savepct')) else 0.0,
                "saves": float(player_data.get('performance_saves', 0)) if pd.notna(player_data.get('performance_saves')) else 0.0,
                "clean_sheets": float(player_data.get('performance_cs', 0)) if pd.notna(player_data.get('performance_cs')) else 0.0,
                "goals_against": float(player_data.get('performance_ga', 0)) if pd.notna(player_data.get('performance_ga')) else 0.0
            }
        else:
            return {}
    
    def _add_raw_percentiles(self, player_data, percentiles):
        """Add position-specific raw percentiles for radar charts"""
        if self.position == "forward":
            raw_cols = [
                'performance_gls_pct', 'expected_npxg_pct', 'standard_sot_pct',
                'performance_ast_pct', 'expected_xag_pct', 'kp_pct',
                'take_ons_succ_pct', 'aerial_duels_wonpct_pct',
                'touches_att_pen_pct', 'carries_prgc_pct'
            ]
        elif self.position == "midfielder":
            raw_cols = [
                'total_cmppct_pct', 'prgp_pct', 'kp_pct',
                'carries_prgc_pct', 'tackles_tklw_pct', 'int_pct',
                'performance_ast_pct', 'touches_mid_3rd_pct',
                'performance_recov_pct', 'sca_sca_pct'
            ]
        elif self.position == "defender":
            raw_cols = [
                'tackles_tklw_pct', 'int_pct', 'blocks_blocks_pct',
                'aerial_duels_wonpct_pct', 'clr_pct', 'prgp_pct',
                'total_cmppct_pct', 'performance_recov_pct',
                'tackles_def_3rd_pct', 'err_pct'
            ]
        elif self.position == "goalkeeper":
            raw_cols = [
                'performance_savepct_pct', 'performance_cs_pct', 'crosses_stppct_pct',
                'launched_cmppct_pct', 'sweeper_numopa_per_90_pct', 'penalty_kicks_savepct_pct',
                'performance_sota_pct', 'performance_ga90_pct',
                'passes_avglen_pct', 'sweeper_avgdist_pct'
            ]
        else:
            raw_cols = []
        
        for pct_col in raw_cols:
            if pct_col in player_data.index:
                val = player_data[pct_col]
                if pd.notna(val):
                    percentiles[pct_col] = float(val)
                else:
                    percentiles[pct_col] = 50.0
            else:
                percentiles[pct_col] = 50.0