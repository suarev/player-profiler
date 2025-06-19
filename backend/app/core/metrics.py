# Metric definitions for forwards
FORWARD_METRICS = {
    "finishing": {
        "name": "Finishing",
        "description": "Goals, xG conversion rate",
        "columns": [
            "performance_gls", 
            "expected_npxg",
            "expected_npxg_per_sh"
        ],
        "weights": {  # Internal weights for combining columns
            "performance_gls": 10,
            "expected_npxg": 0.4,
            "expected_npxg_per_sh": 0.2,
        }
    },
    "physical": {
        "name": "Physical Presence", 
        "description": "Aerials won, duels",
        "columns": [
            "aerial_duels_wonpct",
            "aerial_duels_won"
        ],
        "weights": {
            "aerial_duels_wonpct": 0.3,
            "aerial_duels_won": 0.7
        }
    },
    "creativity": {
        "name": "Creativity",
        "description": "Assists, key passes, chance creation",
        "columns": [
            "performance_ast",
            "expected_xag",
            "kp",
            "sca_sca",
            "sca_types_passlive"
        ],
        "weights": {
            "performance_ast": 0.2,
            "expected_xag": 0.3,
            "kp": 0.2,
            "sca_sca": 0.3
        }
    },
    "pace_dribbling": {
        "name": "Pace & Dribbling",
        "description": "Take-ons, progressive carries",
        "columns": [
            "take_ons_succ",
            "carries_prgc",
            "carries_cpa",
            "carries_1_per_3"
        ],
        "weights": {
            "take_ons_succ": 0.4,
            "carries_prgc": 0.3,
            "carries_cpa":0.2,
            "carries_1_per_3":0.1
        }
    },
    "work_rate": {
        "name": "Work Rate",
        "description": "Pressing, defensive actions",
        "columns": [
            "performance_recov",
            "tackles_att_3rd",
            "blocks_pass"
        ],
        "weights": {
            "performance_recov": 0.3,
            "tackles_att_3rd": 0.6,
            "blocks_pass": 0.1
        }
    },
    "box_presence": {
        "name": "Box Presence",
        "description": "Touches in Penalty Area",
        "columns": [
            "touches_att_pen"
        ],
        "weights": {
            "touches_att_pen":1.0
        }
    }
}

# Algorithm definitions
ALGORITHMS = {
    "weighted_score": {
        "name": "Weighted Score",
        "description": "Balanced approach - combines all metrics based on your preferences"
    }
}