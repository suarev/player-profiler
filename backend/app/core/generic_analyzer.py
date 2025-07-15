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
            position_group = self.position
            
            # Build query based on what tables exist
            base_query = f"""
            SELECT 
                p.id as player_id,
                p.name,
                p.team,
                p.position,
                p.age,
                pp.percentiles
            FROM football_data.players p
            JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
            WHERE pp.position_group = '{position_group}'
            """
            
            self.df = execute_query(base_query)
            
            if self.df.empty:
                print(f"⚠️ No data found for {self.position}")
                self.df = pd.DataFrame()
                return
                
            print(f"✅ Loaded {len(self.df)} {self.position}s")
            
            # Expand percentiles properly
            if 'percentiles' in self.df.columns:
                import json
                
                # Initialize a dictionary to store all percentile data
                all_percentile_data = {f"{col}_pct": [] for col in self.get_all_metric_columns()}
                
                # Process each row
                for idx, row in self.df.iterrows():
                    try:
                        percentiles = json.loads(row['percentiles']) if isinstance(row['percentiles'], str) else row['percentiles']
                        
                        # Fill in values for each expected column
                        for col in self.get_all_metric_columns():
                            pct_col = f"{col}_pct"
                            if percentiles and col in percentiles:
                                all_percentile_data[pct_col].append(percentiles[col])
                            else:
                                all_percentile_data[pct_col].append(50.0)  # Default value
                                
                    except Exception as e:
                        # If error, fill with defaults
                        for col in self.get_all_metric_columns():
                            all_percentile_data[f"{col}_pct"].append(50.0)
                
                # Create DataFrame from percentile data
                percentile_df = pd.DataFrame(all_percentile_data)
                
                # Drop the percentiles column and concatenate
                self.df = self.df.drop(columns=['percentiles'])
                self.df = pd.concat([self.df, percentile_df], axis=1)
                
                print(f"✅ Expanded percentiles - DataFrame shape: {self.df.shape}")
            
        except Exception as e:
            print(f"❌ Error loading {self.position} data: {e}")
            import traceback
            traceback.print_exc()
            self.df = pd.DataFrame()

    def get_all_metric_columns(self):
        """Get all columns needed for this position's metrics"""
        all_cols = set()
        for metric_info in self.metrics.values():
            all_cols.update(metric_info['columns'])
        return list(all_cols)
    
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
                player_age = player.get('age', None)  # Get actual age
                
                # Get player image
                player_image = None
                try:
                    player_image = player_image_service.search_player_image(player_name, player_team)
                    if not player_image:
                        player_image = player_image_service.get_fallback_image(player_name)
                except Exception as e:
                    print(f"Error getting image for {player_name}: {e}")
                    player_image = player_image_service.get_fallback_image(player_name)
                
                # Get position-specific key stats with ACTUAL VALUES
                key_stats = self._get_key_stats(player_data)
                
                # Get percentile ranks for the sliders
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
                    "age": int(player_age) if player_age and pd.notna(player_age) else None,
                    "match_score": float(player.get('final_score', 0)),
                    "key_stats": key_stats,
                    "percentile_ranks": percentiles,
                    "image_url": player_image
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in get_recommendations for {self.position}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_key_stats(self, player_data) -> Dict[str, float]:
        """Get position-specific key stats with ACTUAL VALUES, not percentiles"""
        def safe_float(value, default=0.0):
            """Safely convert to float, handling None and NaN"""
            if pd.isna(value) or value is None:
                return default
            try:
                return float(value)
            except:
                return default
        
        if self.position == "forward":
            return {
                "goals": safe_float(player_data.get('performance_gls', 0)),
                "xG": safe_float(player_data.get('expected_xg', 0)),
                "shots": safe_float(player_data.get('standard_sh', 0)),
                "assists": safe_float(player_data.get('performance_ast', 0))
            }
        elif self.position == "midfielder":
            # Calculate pass completion % if we have the data
            passes_completed = safe_float(player_data.get('total_cmp', 0))
            passes_attempted = safe_float(player_data.get('total_att', 1))  # Avoid division by zero
            pass_pct = safe_float(player_data.get('total_cmppct', 0))
            
            # Use calculated or stored percentage
            if pass_pct == 0 and passes_attempted > 0:
                pass_pct = (passes_completed / passes_attempted) * 100
            
            return {
                "passes": pass_pct,
                "key_passes": safe_float(player_data.get('kp', 0)),
                "prog_carries": safe_float(player_data.get('carries_prgc', 0)),
                "tackles": safe_float(player_data.get('tackles_tklw', 0))
            }
        elif self.position == "defender":
            return {
                "tackles": safe_float(player_data.get('tackles_tklw', 0)),
                "interceptions": safe_float(player_data.get('int', 0)),
                "aerial_won": safe_float(player_data.get('aerial_duels_wonpct', 0)),
                "prog_passes": safe_float(player_data.get('prgp', 0))
            }
        elif self.position == "goalkeeper":
            # Convert save percentage to proper format if needed
            save_pct = safe_float(player_data.get('performance_savepct', 0))
            if save_pct > 0 and save_pct < 1:  # If it's stored as decimal
                save_pct = save_pct * 100
            
            return {
                "save_pct": save_pct,
                "saves": safe_float(player_data.get('performance_saves', 0)),
                "clean_sheets": safe_float(player_data.get('performance_cs', 0)),
                "goals_against": safe_float(player_data.get('performance_ga', 0))
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