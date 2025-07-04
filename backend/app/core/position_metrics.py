# backend/app/core/position_metrics.py
"""
Centralized metrics configuration for all positions
Based on available FBref columns from your scrape
"""

# Color themes matching the position hover colors from positions.css
POSITION_COLORS = {
    "forward": "#1688CC",      # Blue
    "midfielder": "#DC273D",   # Red
    "defender": "#AFA15F",     # Yellow/Gold
    "goalkeeper": "#BE2F7A"    # Pink
}

# Metrics for each position based on your scraped columns
MIDFIELDER_METRICS = {
    "passing_ability": {
        "name": "Passing Ability",
        "description": "Pass completion, progressive passes",
        "columns": [
            "total_cmp",
            "total_cmppct", 
            "prgp",
            "kp",
            "ppa"
        ],
        "weights": {
            "total_cmp": 0.2,
            "total_cmppct": 0.3,
            "prgp": 0.2,
            "kp": 0.2,
            "ppa": 0.1
        }
    },
    "ball_progression": {
        "name": "Ball Progression",
        "description": "Carries, progressive distance",
        "columns": [
            "carries_prgc",
            "carries_prgdist",
            "carries_1_per_3",
            "total_prgdist"
        ],
        "weights": {
            "carries_prgc": 0.3,
            "carries_prgdist": 0.3,
            "carries_1_per_3": 0.2,
            "total_prgdist": 0.2
        }
    },
    "defensive_work": {
        "name": "Defensive Work",
        "description": "Tackles, interceptions, recoveries",
        "columns": [
            "tackles_tklw",
            "int",
            "performance_recov",
            "blocks_pass"
        ],
        "weights": {
            "tackles_tklw": 0.3,
            "int": 0.3,
            "performance_recov": 0.3,
            "blocks_pass": 0.1
        }
    },
    "creativity": {
        "name": "Creativity",
        "description": "Assists, chance creation",
        "columns": [
            "performance_ast",
            "expected_xag",
            "sca_sca",
            "gca_gca"
        ],
        "weights": {
            "performance_ast": 0.25,
            "expected_xag": 0.25,
            "sca_sca": 0.3,
            "gca_gca": 0.2
        }
    },
    "possession": {
        "name": "Possession Play",
        "description": "Touches, press resistance",
        "columns": [
            "touches_touches",
            "touches_mid_3rd",
            "receiving_rec",
            "carries_mis"  # Lower is better - we'll invert
        ],
        "weights": {
            "touches_touches": 0.3,
            "touches_mid_3rd": 0.3,
            "receiving_rec": 0.3,
            "carries_mis": -0.1  # Negative weight for miscontrols
        }
    },
    "goal_threat": {
        "name": "Goal Threat",
        "description": "Goals and shooting from midfield",
        "columns": [
            "performance_gls",
            "standard_sh",
            "standard_dist",
            "touches_att_3rd"
        ],
        "weights": {
            "performance_gls": 0.4,
            "standard_sh": 0.2,
            "standard_dist": -0.1,  # Prefer closer shots
            "touches_att_3rd": 0.3
        }
    }
}

DEFENDER_METRICS = {
    "defensive_actions": {
        "name": "Defensive Actions",
        "description": "Tackles, blocks, interceptions",
        "columns": [
            "tackles_tkl",
            "tackles_tklw",
            "blocks_blocks",
            "int",
            "clr"
        ],
        "weights": {
            "tackles_tkl": 0.2,
            "tackles_tklw": 0.3,
            "blocks_blocks": 0.2,
            "int": 0.2,
            "clr": 0.1
        }
    },
    "aerial_dominance": {
        "name": "Aerial Dominance",
        "description": "Aerial duels and headers",
        "columns": [
            "aerial_duels_won",
            "aerial_duels_wonpct"
        ],
        "weights": {
            "aerial_duels_won": 0.4,
            "aerial_duels_wonpct": 0.6
        }
    },
    "ball_playing": {
        "name": "Ball Playing",
        "description": "Passing from the back",
        "columns": [
            "total_cmp",
            "total_cmppct",
            "prgp",
            "long_cmp",
            "carries_prgc"
        ],
        "weights": {
            "total_cmp": 0.15,
            "total_cmppct": 0.25,
            "prgp": 0.3,
            "long_cmp": 0.15,
            "carries_prgc": 0.15
        }
    },
    "positional_play": {
        "name": "Positional Play",
        "description": "Defensive positioning and errors",
        "columns": [
            "tackles_def_3rd",
            "err",  # Lower is better
            "performance_og",  # Lower is better
            "touches_def_3rd"
        ],
        "weights": {
            "tackles_def_3rd": 0.4,
            "err": -0.3,
            "performance_og": -0.2,
            "touches_def_3rd": 0.1
        }
    },
    "recovery_speed": {
        "name": "Recovery & Speed",
        "description": "Ball recoveries and mobility",
        "columns": [
            "performance_recov",
            "challenges_lost",  # Lower is better
            "tackles_att_3rd"
        ],
        "weights": {
            "performance_recov": 0.5,
            "challenges_lost": -0.3,
            "tackles_att_3rd": 0.2
        }
    },
    "discipline": {
        "name": "Discipline",
        "description": "Cards and fouls",
        "columns": [
            "performance_crdy",
            "performance_crdr",
            "performance_fls"
        ],
        "weights": {
            "performance_crdy": -0.3,
            "performance_crdr": -0.4,
            "performance_fls": -0.3
        }
    }
}

GOALKEEPER_METRICS = {
    "shot_stopping": {
        "name": "Shot Stopping",
        "description": "Saves and save percentage",
        "columns": [
            "performance_saves",
            "performance_savepct",
            "performance_sota"
        ],
        "weights": {
            "performance_saves": 0.3,
            "performance_savepct": 0.5,
            "performance_sota": 0.2
        }
    },
    "command_of_area": {
        "name": "Command of Area",
        "description": "Crosses and high balls",
        "columns": [
            "crosses_stp",
            "crosses_stppct",
            "sweeper_avgdist"
        ],
        "weights": {
            "crosses_stp": 0.3,
            "crosses_stppct": 0.5,
            "sweeper_avgdist": 0.2
        }
    },
    "distribution": {
        "name": "Distribution",
        "description": "Passing and launches",
        "columns": [
            "launched_cmppct",
            "passes_launchpct",
            "passes_avglen",
            "goal_kicks_avglen"
        ],
        "weights": {
            "launched_cmppct": 0.4,
            "passes_launchpct": -0.1,  # Prefer shorter passing
            "passes_avglen": -0.2,
            "goal_kicks_avglen": 0.3
        }
    },
    "sweeping": {
        "name": "Sweeper Keeping",
        "description": "Actions outside penalty area",
        "columns": [
            "sweeper_numopa",
            "sweeper_numopa_per_90",
            "sweeper_avgdist"
        ],
        "weights": {
            "sweeper_numopa": 0.3,
            "sweeper_numopa_per_90": 0.4,
            "sweeper_avgdist": 0.3
        }
    },
    "penalty_saving": {
        "name": "Penalty Expertise",
        "description": "Penalty saves",
        "columns": [
            "penalty_kicks_pksv",
            "penalty_kicks_savepct"
        ],
        "weights": {
            "penalty_kicks_pksv": 0.4,
            "penalty_kicks_savepct": 0.6
        }
    },
    "consistency": {
        "name": "Consistency",
        "description": "Clean sheets and goals against",
        "columns": [
            "performance_cs",
            "performance_cspct",
            "performance_ga90"
        ],
        "weights": {
            "performance_cs": 0.3,
            "performance_cspct": 0.4,
            "performance_ga90": -0.3  # Lower is better
        }
    }
}

# Export all metrics by position
POSITION_METRICS = {
    "forward": {
        # Import from existing metrics.py
        "finishing": {
            "name": "Finishing",
            "description": "Goals, xG conversion rate",
            "columns": ["performance_gls"],
            "weights": {"performance_gls": 1.0}
        },
        "physical": {
            "name": "Physical Presence",
            "description": "Aerials won, duels",
            "columns": ["aerial_duels_wonpct", "aerial_duels_won"],
            "weights": {"aerial_duels_wonpct": 0.3, "aerial_duels_won": 0.7}
        },
        "creativity": {
            "name": "Creativity",
            "description": "Assists, key passes, chance creation",
            "columns": ["performance_ast", "expected_xag", "kp", "sca_sca"],
            "weights": {"performance_ast": 0.2, "expected_xag": 0.3, "kp": 0.2, "sca_sca": 0.3}
        },
        "pace_dribbling": {
            "name": "Pace & Dribbling",
            "description": "Take-ons, progressive carries",
            "columns": ["take_ons_succ", "carries_prgc", "carries_cpa", "carries_1_per_3"],
            "weights": {"take_ons_succ": 0.4, "carries_prgc": 0.3, "carries_cpa": 0.2, "carries_1_per_3": 0.1}
        },
        "work_rate": {
            "name": "Work Rate",
            "description": "Pressing, defensive actions",
            "columns": ["performance_recov", "tackles_att_3rd", "blocks_pass"],
            "weights": {"performance_recov": 0.3, "tackles_att_3rd": 0.6, "blocks_pass": 0.1}
        },
        "box_presence": {
            "name": "Box Presence",
            "description": "Touches in penalty area",
            "columns": ["touches_att_pen"],
            "weights": {"touches_att_pen": 1.0}
        }
    },
    "midfielder": MIDFIELDER_METRICS,
    "defender": DEFENDER_METRICS,
    "goalkeeper": GOALKEEPER_METRICS
}