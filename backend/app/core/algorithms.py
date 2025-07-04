# backend/app/core/algorithms.py
# Generic algorithms that work for ALL positions

ALGORITHMS = {
    "weighted_score": {
        "name": "Weighted Score",
        "description": "Balanced approach - combines all metrics based on your preferences"
    },
    "multiplicative": {
        "name": "Multiplicative Scoring",
        "description": "Punishes weaknesses - low scores in any area significantly impact overall rating"
    },
    "threshold_weighted": {
        "name": "Threshold + Weighted",
        "description": "Ensures minimum standards - filters players below thresholds then ranks by weights"
    },
    "distance_based": {
        "name": "Distance-Based Matching",
        "description": "Finds closest match - calculates similarity to your ideal profile"
    },
    "pareto_optimal": {
        "name": "Pareto Optimal",
        "description": "Non-dominated players - finds players not clearly worse than others in all aspects"
    }
}