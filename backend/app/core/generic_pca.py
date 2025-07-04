# backend/app/core/generic_pca.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from typing import Optional, Dict, List
import json

class GenericPCAAnalyzer:
    def __init__(self, position: str):
        self.position = position
        self.pca = PCA(n_components=2)
        self.scaler = StandardScaler()
        self.optimal_clusters = None
        self.kmeans = None
        
    def find_optimal_clusters(self, X: np.ndarray, max_k: int = 10) -> int:
        """Find optimal number of clusters using multiple metrics"""
        scores = {
            'silhouette': [],
            'davies_bouldin': [],
            'inertia': []
        }
        
        K_range = range(2, min(max_k + 1, len(X) // 5))
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            
            scores['silhouette'].append(silhouette_score(X, labels))
            scores['davies_bouldin'].append(davies_bouldin_score(X, labels))
            scores['inertia'].append(kmeans.inertia_)
        
        # Find elbow point
        if len(scores['inertia']) > 2:
            deltas = np.diff(scores['inertia'])
            deltas_diff = np.diff(deltas)
            elbow_idx = np.argmax(deltas_diff) + 2
            elbow_k = list(K_range)[min(elbow_idx, len(K_range)-1)]
        else:
            elbow_k = 4
        
        best_sil_idx = np.argmax(scores['silhouette'])
        best_sil_k = list(K_range)[best_sil_idx]
        
        if scores['silhouette'][best_sil_idx] > 0.35:
            optimal_k = best_sil_k
        else:
            optimal_k = (best_sil_k + elbow_k) // 2
        
        print(f"Optimal clusters for {self.position}: {optimal_k}")
        return optimal_k
    
    def ensure_spread_distribution(self, X: np.ndarray) -> np.ndarray:
        """Apply transformations to ensure points are well-distributed"""
        x_coords = X[:, 0]
        y_coords = X[:, 1]
        
        x_skew = np.mean(x_coords) / np.std(x_coords) if np.std(x_coords) > 0 else 0
        y_skew = np.mean(y_coords) / np.std(y_coords) if np.std(y_coords) > 0 else 0
        
        if abs(x_skew) > 1:
            if np.min(x_coords) < 0:
                x_coords = x_coords - np.min(x_coords) + 1
            x_coords = np.sign(x_coords) * np.sqrt(np.abs(x_coords))
            X[:, 0] = x_coords
        
        if abs(y_skew) > 1:
            if np.min(y_coords) < 0:
                y_coords = y_coords - np.min(y_coords) + 1
            y_coords = np.sign(y_coords) * np.sqrt(np.abs(y_coords))
            X[:, 1] = y_coords
        
        X = StandardScaler().fit_transform(X)
        return X
    
    def compute_pca(self, df: pd.DataFrame, custom_k: Optional[int] = None) -> Dict:
        """Compute PCA with automatic or custom clustering"""
        # Define position-specific features
        feature_cols = self._get_position_features()
        
        # Filter to available columns
        available_cols = [col for col in feature_cols if col in df.columns]
        
        # Prepare data
        pca_df = df.dropna(subset=available_cols, thresh=len(available_cols)*0.7).copy()
        
        # Extract features and standardize
        X = pca_df[available_cols].fillna(50).values
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform PCA
        pca_coords = self.pca.fit_transform(X_scaled)
        
        # Ensure good distribution
        pca_coords = self.ensure_spread_distribution(pca_coords)
        
        # Determine number of clusters
        if custom_k and 2 <= custom_k <= 10:
            self.optimal_clusters = custom_k
        else:
            self.optimal_clusters = self.find_optimal_clusters(pca_coords)
        
        # Perform clustering
        self.kmeans = KMeans(n_clusters=self.optimal_clusters, random_state=42, n_init=10)
        clusters = self.kmeans.fit_predict(pca_coords)
        
        # Generate cluster labels based on position
        cluster_labels = self._get_cluster_labels()
        
        # Create response data
        points = []
        for idx, (_, player) in enumerate(pca_df.iterrows()):
            points.append({
                "player_id": int(player['player_id']),
                "name": player['name'],
                "team": player.get('team', 'Unknown'),
                "x": float(pca_coords[idx, 0]),
                "y": float(pca_coords[idx, 1]),
                "cluster": cluster_labels[clusters[idx]],
                "cluster_id": int(clusters[idx])
            })
        
        # Get feature loadings
        loadings = pd.DataFrame(
            self.pca.components_.T,
            columns=['PC1', 'PC2'],
            index=available_cols
        )
        
        return {
            "points": points,
            "explained_variance": self.pca.explained_variance_ratio_.tolist(),
            "pc_interpretation": self._interpret_components(loadings),
            "cluster_centers": self._get_cluster_centers(pca_coords, clusters, cluster_labels),
            "optimal_k": self.optimal_clusters
        }
    
    def _get_position_features(self) -> List[str]:
        """Get position-specific features for PCA"""
        if self.position == "forward":
            return [
                'performance_gls_pct', 'expected_npxg_pct', 'expected_npxg_per_sh_pct', 
                'standard_sot_pct', 'aerial_duels_wonpct_pct', 'aerial_duels_won_pct',
                'performance_ast_pct', 'expected_xag_pct', 'kp_pct', 'sca_sca_pct',
                'take_ons_succ_pct', 'carries_prgc_pct', 'touches_att_pen_pct',
                'tackles_att_3rd_pct', 'performance_recov_pct'
            ]
        elif self.position == "midfielder":
            return [
                'total_cmp_pct', 'total_cmppct_pct', 'prgp_pct', 'kp_pct', 'ppa_pct',
                'carries_prgc_pct', 'carries_prgdist_pct', 'touches_mid_3rd_pct',
                'tackles_tklw_pct', 'int_pct', 'performance_recov_pct',
                'performance_ast_pct', 'expected_xag_pct', 'sca_sca_pct',
                'performance_gls_pct', 'touches_touches_pct'
            ]
        elif self.position == "defender":
            return [
                'tackles_tkl_pct', 'tackles_tklw_pct', 'blocks_blocks_pct',
                'int_pct', 'clr_pct', 'aerial_duels_won_pct', 'aerial_duels_wonpct_pct',
                'total_cmp_pct', 'total_cmppct_pct', 'prgp_pct', 'long_cmp_pct',
                'tackles_def_3rd_pct', 'performance_recov_pct', 'err_pct',
                'performance_crdy_pct', 'performance_fls_pct'
            ]
        elif self.position == "goalkeeper":
            return [
                'performance_saves_pct', 'performance_savepct_pct', 'performance_sota_pct',
                'performance_cs_pct', 'performance_cspct_pct', 'performance_ga90_pct',
                'crosses_stp_pct', 'crosses_stppct_pct', 'sweeper_avgdist_pct',
                'launched_cmppct_pct', 'passes_launchpct_pct', 'passes_avglen_pct',
                'sweeper_numopa_pct', 'penalty_kicks_savepct_pct'
            ]
        else:
            return []
    
    def _get_cluster_labels(self) -> Dict[int, str]:
        """Generate position-specific cluster labels"""
        if self.position == "forward":
            labels = ["Target Men", "Poachers", "Complete Forwards", "False 9s", "Wingers", 
                     "Pressing Forwards", "Clinical Finishers", "Creative Forwards"]
        elif self.position == "midfielder":
            labels = ["Box-to-Box", "Deep Playmakers", "Defensive Mids", "Attacking Mids",
                     "Ball Carriers", "Creators", "Workhorses", "Tempo Controllers"]
        elif self.position == "defender":
            labels = ["Ball-Playing CBs", "Defensive Walls", "Fullbacks", "Sweepers",
                     "Aerial Dominators", "Progressive Defenders", "Aggressive Stoppers", "Versatile Defenders"]
        elif self.position == "goalkeeper":
            labels = ["Shot Stoppers", "Sweeper Keepers", "Traditional", "Modern Distributors",
                     "Penalty Specialists", "Command Box", "Reflexive", "Complete Keepers"]
        else:
            labels = [f"Group {i+1}" for i in range(10)]
        
        return {i: labels[i] if i < len(labels) else f"Group {i+1}" 
                for i in range(self.optimal_clusters)}
    
    def _get_cluster_centers(self, pca_coords: np.ndarray, clusters: np.ndarray, 
                           cluster_labels: Dict[int, str]) -> List[Dict]:
        """Calculate cluster centers for visualization"""
        centers = []
        for cluster_id, label in cluster_labels.items():
            cluster_mask = clusters == cluster_id
            if cluster_mask.any():
                center_x = pca_coords[cluster_mask, 0].mean()
                center_y = pca_coords[cluster_mask, 1].mean()
                centers.append({
                    "cluster_id": cluster_id,
                    "label": label,
                    "x": float(center_x),
                    "y": float(center_y),
                    "count": int(cluster_mask.sum())
                })
        return centers
    
    def _interpret_components(self, loadings: pd.DataFrame) -> Dict[str, str]:
        """Auto-interpret what each PC represents"""
        interpretations = {}
        
        for pc in ['PC1', 'PC2']:
            top_positive = loadings[pc].nlargest(3)
            
            # Position-specific interpretations
            if self.position == "forward":
                if any('gls' in idx or 'xg' in idx for idx in top_positive.index):
                    interpretations[pc] = "Goal Threat"
                elif any('ast' in idx or 'xa' in idx for idx in top_positive.index):
                    interpretations[pc] = "Creativity"
                elif any('aerial' in idx for idx in top_positive.index):
                    interpretations[pc] = "Physical Presence"
                else:
                    interpretations[pc] = "Overall Impact"
            
            elif self.position == "midfielder":
                if any('pass' in idx or 'cmp' in idx for idx in top_positive.index):
                    interpretations[pc] = "Passing Quality"
                elif any('carries' in idx or 'prg' in idx for idx in top_positive.index):
                    interpretations[pc] = "Ball Progression"
                elif any('tkl' in idx or 'int' in idx for idx in top_positive.index):
                    interpretations[pc] = "Defensive Actions"
                else:
                    interpretations[pc] = "All-Round Play"
            
            elif self.position == "defender":
                if any('tkl' in idx or 'blocks' in idx for idx in top_positive.index):
                    interpretations[pc] = "Defensive Actions"
                elif any('pass' in idx or 'prg' in idx for idx in top_positive.index):
                    interpretations[pc] = "Ball Playing"
                elif any('aerial' in idx for idx in top_positive.index):
                    interpretations[pc] = "Aerial Ability"
                else:
                    interpretations[pc] = "Defensive Impact"
            
            elif self.position == "goalkeeper":
                if any('save' in idx for idx in top_positive.index):
                    interpretations[pc] = "Shot Stopping"
                elif any('pass' in idx or 'launch' in idx for idx in top_positive.index):
                    interpretations[pc] = "Distribution"
                elif any('sweep' in idx for idx in top_positive.index):
                    interpretations[pc] = "Sweeping Actions"
                else:
                    interpretations[pc] = "Overall Keeping"
            
            else:
                interpretations[pc] = f"Component {pc[-1]}"
        
        return interpretations