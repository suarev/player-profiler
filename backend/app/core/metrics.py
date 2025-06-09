# Metric definitions for forwards
FORWARD_METRICS = {
    "finishing": {
        "name": "Finishing",
        "description": "Goals, xG conversion rate",
        "columns": [
            "performance_gls",
            "performance_g_pk", 
            "expected_xg",
            "expected_g_xg",
            "standard_g_per_sh",
            "standard_sotpct"
        ],
        "weights": {  # Internal weights for combining columns
            "performance_gls": 0.3,
            "performance_g_pk": 0.2,
            "expected_xg": 0.2,
            "expected_g_xg": 0.1,
            "standard_g_per_sh": 0.1,
            "standard_sotpct": 0.1
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
            "aerial_duels_wonpct": 0.6,
            "aerial_duels_won": 0.4
        }
    },
    "creativity": {
        "name": "Creativity",
        "description": "Assists, key passes, chance creation",
        "columns": [
            "performance_ast",
            "expected_xag",
            "kp",
            "ppa",
            "sca_sca90"
        ],
        "weights": {
            "performance_ast": 0.3,
            "expected_xag": 0.25,
            "kp": 0.2,
            "ppa": 0.15,
            "sca_sca90": 0.1
        }
    },
    "pace_dribbling": {
        "name": "Pace & Dribbling",
        "description": "Take-ons, progressive carries",
        "columns": [
            "take_ons_succ",
            "take_ons_succpct",
            "carries_prgc",
            "carries_prgdist"
        ],
        "weights": {
            "take_ons_succ": 0.3,
            "take_ons_succpct": 0.3,
            "carries_prgc": 0.2,
            "carries_prgdist": 0.2
        }
    },
    "work_rate": {
        "name": "Work Rate",
        "description": "Pressing, defensive actions",
        "columns": [
            "performance_recov",
            "tackles_tkl",
            "int",
            "performance_fls"
        ],
        "weights": {
            "performance_recov": 0.4,
            "tackles_tkl": 0.3,
            "int": 0.2,
            "performance_fls": 0.1
        }
    },
    "positioning": {
        "name": "Positioning",
        "description": "Box presence, shot locations",
        "columns": [
            "touches_att_pen",
            "touches_att_3rd",
            "standard_sh_per_90"
        ],
        "weights": {
            "touches_att_pen": 0.5,
            "touches_att_3rd": 0.3,
            "standard_sh_per_90": 0.2
        }
    },
    "linkup": {
        "name": "Link-up Play",
        "description": "Passing accuracy, combination play",
        "columns": [
            "total_cmppct",
            "short_cmppct",
            "medium_cmppct",
            "ast"
        ],
        "weights": {
            "total_cmppct": 0.3,
            "short_cmppct": 0.3,
            "medium_cmppct": 0.2,
            "ast": 0.2
        }
    }
}

# Algorithm definitions
ALGORITHMS = {
    "weighted_score": {
        "name": "Weighted Score",
        "description": "Balanced approach - combines all metrics based on your preferences"
    },
    "multiplicative": {
        "name": "Multiplicative Scoring", 
        "description": "Punishes weaknesses - better for finding complete players"
    },
    "threshold": {
        "name": "Threshold + Weighted",
        "description": "Ensures minimum standards - filters then ranks"
    }
}