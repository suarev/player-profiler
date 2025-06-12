"""
Script to precompute percentile ranks for ALL players and ALL metrics
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
    
    print("Computing percentiles for all players and all metrics...")
    
    # Get all players with ALL their stats
    query = """
    SELECT 
        p.id as player_id,
        p.name,
        p.team,
        p.position,
        s.*,
        sh.*,
        ps.*,
        pt.*,
        gsc.*,
        d.*,
        pos.*,
        m.*,
        pl.*
    FROM football_data.players p
    LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
    LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
    LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
    LEFT JOIN football_data.player_passing_types_stats pt ON p.name = pt.player
    LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
    LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
    LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
    LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
    LEFT JOIN football_data.player_playing_time_stats pl ON p.name = pl.player
    """
    
    df = execute_query(query)
    print(f"Found {len(df)} players with sufficient playing time")
    print(f"Total columns: {len(df.columns)}")
    
    # Identify position groups
    position_groups = {
        'forward': df[df['position'].str.contains('FW|CF|LW|RW', na=False)].copy(),
        'midfielder': df[df['position'].str.contains('MF|CM|DM|AM|LM|RM', na=False)].copy(),
        'defender': df[df['position'].str.contains('DF|CB|LB|RB|WB', na=False)].copy(),
        'goalkeeper': df[df['position'].str.contains('GK', na=False)].copy()
    }
    
    # Create percentiles table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS football_data.player_percentiles_all (
        player_id INTEGER PRIMARY KEY,
        position_group VARCHAR(20),
        percentiles JSONB,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    with engine.begin() as conn:
        conn.execute(text(create_table_sql))
    
    # Process each position group
    for position_group, group_df in position_groups.items():
        if len(group_df) == 0:
            continue
            
        print(f"\nProcessing {position_group}s ({len(group_df)} players)...")
        
        # Get numeric columns (exclude IDs, names, etc.)
        exclude_cols = ['player_id', 'id', 'name', 'team', 'position', 'age', 'born', 
                       'nation', 'league', 'season', 'player', 'created_at']
        
        numeric_cols = []
        for col in group_df.columns:
            if col not in exclude_cols:
                try:
                    # Try to convert to numeric
                    group_df.loc[:, col] = pd.to_numeric(group_df[col], errors='coerce')
                    # Only keep if it has some numeric values
                    if group_df[col].notna().sum() > 0:
                        numeric_cols.append(col)
                except:
                    pass
        
        print(f"Found {len(numeric_cols)} numeric columns to compute percentiles for")
        
        # Compute percentiles for each numeric column
        stored_count = 0
        
        for idx, (_, player) in enumerate(group_df.iterrows()):
            player_percentiles = {}
            
            for col in numeric_cols:
                # Get this player's value
                player_value = player[col]
                
                if pd.notna(player_value):
                    # Calculate percentile rank
                    values = group_df[col].dropna()
                    if len(values) > 0:
                        percentile = (values < player_value).sum() / len(values) * 100
                        player_percentiles[col] = round(percentile, 2)
                    else:
                        player_percentiles[col] = 50.0  # Default to middle
                else:
                    player_percentiles[col] = None
            
            # Store in database
            insert_sql = """
            INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
            VALUES (:player_id, :position_group, :percentiles)
            ON CONFLICT (player_id) DO UPDATE
            SET percentiles = EXCLUDED.percentiles, 
                position_group = EXCLUDED.position_group,
                computed_at = CURRENT_TIMESTAMP
            """
            
            try:
                with engine.begin() as conn:
                    conn.execute(text(insert_sql), {
                        'player_id': int(player['player_id']),
                        'position_group': position_group,
                        'percentiles': json.dumps(player_percentiles)
                    })
                stored_count += 1
                
                # Progress indicator
                if (idx + 1) % 100 == 0:
                    print(f"  Processed {idx + 1}/{len(group_df)} {position_group}s...", end='\r')
                    
            except Exception as e:
                print(f"\n  Error storing player {player['name']}: {e}")
                continue
        
        print(f"\n✅ Computed and stored percentiles for {stored_count} {position_group}s")
    
    # Show sample of what was computed
    print("\n📊 Sample percentiles stored:")
    sample_query = """
    SELECT p.name, pp.position_group, 
           jsonb_object_keys(pp.percentiles) as metric
    FROM football_data.player_percentiles_all pp
    JOIN football_data.players p ON pp.player_id = p.id
    LIMIT 5
    """
    
    try:
        sample_df = execute_query(sample_query)
        print(f"Sample data: {sample_df.head()}")
    except:
        print("Could not fetch sample data")
    
    print("\n✅ All percentiles computed successfully!")
    print("You can now use ANY metric in your analysis!")

if __name__ == "__main__":
    precompute_percentiles()