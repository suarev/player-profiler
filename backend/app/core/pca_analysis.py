# backend/app/core/pca_analysis.py - Modified version

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from typing import Dict, List, Tuple
import json

class ForwardPCAAnalyzer:
    def __init__(self):
        self.pca = PCA(n_components=2)
        self.scaler = StandardScaler()
        self.optimal_clusters = None
        self.kmeans = None
        
    def find_optimal_clusters(self, X: np.ndarray, max_k: int = 10) -> int:
        """
        Find optimal number of clusters using multiple metrics
        """
        scores = {
            'silhouette': [],
            'davies_bouldin': [],
            'inertia': [],
            'gap': []
        }
        
        K_range = range(2, min(max_k + 1, len(X) // 5))  # At least 5 players per cluster
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            
            # Silhouette score (higher is better, -1 to 1)
            sil_score = silhouette_score(X, labels)
            scores['silhouette'].append(sil_score)
            
            # Davies-Bouldin score (lower is better)
            db_score = davies_bouldin_score(X, labels)
            scores['davies_bouldin'].append(db_score)
            
            # Inertia (within-cluster sum of squares)
            scores['inertia'].append(kmeans.inertia_)
            
        # Find elbow point in inertia
        if len(scores['inertia']) > 2:
            # Calculate rate of change
            deltas = np.diff(scores['inertia'])
            deltas_diff = np.diff(deltas)
            
            # Find elbow (where rate of change decreases most)
            elbow_idx = np.argmax(deltas_diff) + 2  # +2 because of double diff
            elbow_k = list(K_range)[min(elbow_idx, len(K_range)-1)]
        else:
            elbow_k = 4  # default
        
        # Find best silhouette score
        best_sil_idx = np.argmax(scores['silhouette'])
        best_sil_k = list(K_range)[best_sil_idx]
        
        # Weighted decision
        # Prefer silhouette score but consider elbow point
        if scores['silhouette'][best_sil_idx] > 0.35:  # Good separation
            optimal_k = best_sil_k
        else:
            # Average between silhouette and elbow
            optimal_k = (best_sil_k + elbow_k) // 2
        
        print(f"Optimal clusters analysis:")
        print(f"- Elbow method suggests: {elbow_k}")
        print(f"- Best silhouette score: {best_sil_k}")
        print(f"- Chosen: {optimal_k}")
        
        return optimal_k
    
    def ensure_spread_distribution(self, X: np.ndarray) -> np.ndarray:
        """
        Apply transformations to ensure points are well-distributed
        """
        # Check if points are clustered on one side
        x_coords = X[:, 0]
        y_coords = X[:, 1]
        
        # Calculate skewness
        x_skew = np.mean(x_coords) / np.std(x_coords) if np.std(x_coords) > 0 else 0
        y_skew = np.mean(y_coords) / np.std(y_coords) if np.std(y_coords) > 0 else 0
        
        # If data is too skewed, apply log or sqrt transformation
        if abs(x_skew) > 1:
            print(f"X-axis skewed ({x_skew:.2f}), applying transformation")
            # Shift to positive if needed
            if np.min(x_coords) < 0:
                x_coords = x_coords - np.min(x_coords) + 1
            # Apply sqrt transformation
            x_coords = np.sign(x_coords) * np.sqrt(np.abs(x_coords))
            X[:, 0] = x_coords
        
        if abs(y_skew) > 1:
            print(f"Y-axis skewed ({y_skew:.2f}), applying transformation")
            if np.min(y_coords) < 0:
                y_coords = y_coords - np.min(y_coords) + 1
            y_coords = np.sign(y_coords) * np.sqrt(np.abs(y_coords))
            X[:, 1] = y_coords
        
        # Re-center and scale
        X = StandardScaler().fit_transform(X)
        
        return X
    
    def compute_pca(self, df: pd.DataFrame) -> Dict:
        """
        Compute PCA with automatic optimal clustering
        """
        # Define metrics (same as before)
        feature_cols = [
            'performance_gls_pct', 'expected_xg_pct', 'expected_npxg_per_sh_pct', 'standard_sot_pct', #SHOOTING
            'aerial_duels_wonpct_pct', 'aerial_duels_won_pct', #AERIAL
            'performance_ast_pct', 'expected_xag_pct', 'kp_pct', 'sca_sca_pct', 'gca_gca_pct', 'sca_types_passlive_pct','sca_types_to_pct', 'sca_types_sho_pct','sca_types_fld_pct','sca_types_def_pct'#CREATING
            'take_ons_succ_pct', 'carries_prgc_pct', 'touches_att_pen_pct', 'carries_1_per_3_pct', #CARRYING/DRIBBLING
            'tackles_att_3rd_pct','performance_recov_pct' #DEFENDING
        ]
        
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
        
        # Find optimal number of clusters
        self.optimal_clusters = self.find_optimal_clusters(pca_coords)
        
        # Perform clustering with optimal k
        self.kmeans = KMeans(n_clusters=self.optimal_clusters, random_state=42, n_init=10)
        clusters = self.kmeans.fit_predict(pca_coords)
        
        # Simple generic labels (you can rename in frontend)
        cluster_labels = {i: f"Group {i+1}" for i in range(self.optimal_clusters)}
        
        # Calculate cluster characteristics for reference
        cluster_stats = self._get_cluster_characteristics(pca_df, clusters, available_cols)
        
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
        
        # Get feature loadings for interpretation
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
            "optimal_k": self.optimal_clusters,
            "cluster_characteristics": cluster_stats,  # So you can name them yourself
            "distribution_quality": self._assess_distribution(pca_coords)
        }
    
    def _get_cluster_characteristics(self, df: pd.DataFrame, clusters: np.ndarray, 
                                   feature_cols: List[str]) -> Dict:
        """
        Get top characteristics of each cluster for manual naming
        """
        cluster_chars = {}
        
        for cluster_id in range(self.optimal_clusters):
            cluster_mask = clusters == cluster_id
            cluster_players = df[cluster_mask]
            
            # Get mean percentiles
            cluster_means = {}
            for col in feature_cols:
                cluster_means[col] = cluster_players[col].mean()
            
            # Find top 3 defining characteristics
            top_features = sorted(cluster_means.items(), key=lambda x: x[1], reverse=True)[:3]
            
            cluster_chars[f"Group {cluster_id + 1}"] = {
                "size": int(cluster_mask.sum()),
                "top_features": [
                    {
                        "metric": feat[0].replace('_pct', ''),
                        "avg_percentile": round(feat[1], 1)
                    }
                    for feat in top_features
                ],
                "sample_players": cluster_players['name'].tolist()[:3]  # Show 3 example players
            }
        
        return cluster_chars
    
    def _assess_distribution(self, coords: np.ndarray) -> Dict:
        """
        Assess how well distributed the points are
        """
        x_coords = coords[:, 0]
        y_coords = coords[:, 1]
        
        return {
            "x_range": float(np.ptp(x_coords)),  # peak to peak
            "y_range": float(np.ptp(y_coords)),
            "x_skew": float(np.mean(x_coords) / np.std(x_coords) if np.std(x_coords) > 0 else 0),
            "y_skew": float(np.mean(y_coords) / np.std(y_coords) if np.std(y_coords) > 0 else 0),
            "quality": "good" if abs(np.mean(x_coords)) < 0.5 and abs(np.mean(y_coords)) < 0.5 else "skewed"
        }
    
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
        # Same as before - analyzes loadings to name axes
        interpretations = {}
        
        for pc in ['PC1', 'PC2']:
            top_positive = loadings[pc].nlargest(3)
            
            # You can refine this logic
            if 'performance_gls_pct' in top_positive.index[:2]:
                interpretations[pc] = "Goal Threat"
            elif 'expected_xag_pct' in top_positive.index[:2]:
                interpretations[pc] = "Creativity"
            elif 'aerial' in ' '.join(top_positive.index):
                interpretations[pc] = "Physical Presence"
            elif 'carries' in ' '.join(top_positive.index):
                interpretations[pc] = "Ball Progression"
            else:
                interpretations[pc] = f"Mixed Attributes"
        
        return interpretations