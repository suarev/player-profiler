"""
Script to precompute percentile ranks for all players
Run this after scraping new data
"""
import sys
import os

# Add parent directory to path so we can import app modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pandas as pd
import numpy as np
import json
from sqlalchemy import text
from app.core.database import engine, execute_query

def precompute_percentiles():
    """Compute and store percentile ranks for all positions"""
    
    print("Computing percentiles for forwards...")
    
    # Get all forward stats
    query = """
    SELECT 
        p.id as player_id,
        p.name,
        p.team,
        p.position,
        s.n_90s,
        s.performance_gls,
        s.performance_ast,
        s.expected_xg,
        s.expected_xag,
        sh.standard_sh,
        sh.standard_sot,
        sh.standard_sotpct,
        ps.total_cmppct,
        ps.kp,
        ps.ppa,
        gsc.sca_sca90,
        d.tackles_tkl,
        d.int,
        pos.touches_att_pen,
        pos.touches_att_3rd,
        pos.take_ons_succ,
        pos.take_ons_succpct,
        pos.carries_prgc,
        pos.carries_prgdist,
        m.aerial_duels_wonpct,
        m.aerial_duels_won,
        m.performance_recov
    FROM football_data.players p
    LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
    LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
    LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
    LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
    LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
    LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
    LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
    WHERE p.position LIKE '%FW%' OR p.position LIKE '%CF%' OR p.position LIKE '%LW%' OR p.position LIKE '%RW%'
    AND s.n_90s IS NOT NULL AND CAST(s.n_90s AS FLOAT) > 5  -- Min 5 90s played
    """
    
    df = execute_query(query)
    print(f"Found {len(df)} forwards with sufficient playing time")
    
    # Convert numeric columns
    numeric_cols = df.columns.drop(['player_id', 'name', 'team', 'position'])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Compute percentiles
    percentiles_df = df[['player_id', 'name', 'team']].copy()
    
    for col in numeric_cols:
        if col != 'n_90s':  # Don't compute percentile for minutes played
            percentiles_df[f"{col}_pct"] = df[col].rank(pct=True, na_option='keep') * 100
    
    # Create percentiles table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS football_data.player_percentiles (
        player_id INTEGER PRIMARY KEY,
        position_group VARCHAR(20),
        data JSONB,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    with engine.begin() as conn:
        conn.execute(text(create_table_sql))
    
    # Store percentiles as JSON for each player
    print("Storing percentiles in database...")
    stored = 0
    
    for _, player in percentiles_df.iterrows():
        player_data = {
            col: float(player[col]) if pd.notna(player[col]) else None
            for col in player.index if col.endswith('_pct')
        }
        
        insert_sql = """
        INSERT INTO football_data.player_percentiles (player_id, position_group, data)
        VALUES (%(player_id)s, %(position_group)s, %(data)s)
        ON CONFLICT (player_id) DO UPDATE
        SET data = EXCLUDED.data, computed_at = CURRENT_TIMESTAMP
        """
        
        with engine.connect() as conn:
            conn.execute(insert_sql, {
                'player_id': int(player['player_id']),
                'position_group': 'forward',
                'data': json.dumps(player_data)
            })
            conn.commit()
        
        stored += 1
    
    print(f"✅ Stored percentiles for {stored} forwards")

if __name__ == "__main__":
    precompute_percentiles()