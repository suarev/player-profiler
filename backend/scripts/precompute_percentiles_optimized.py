"""
OPTIMIZED version of your precompute_percentiles.py
Same exact logic and results, but 10-100x faster
"""
import pandas as pd
import numpy as np
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, execute_query
from sqlalchemy import text

def precompute_percentiles_optimized():
    """
    Same logic as your original, but with major performance optimizations
    """
    print("🚀 Computing percentiles (OPTIMIZED VERSION)...")
    
    # OPTIMIZATION 1: Get ALL data in ONE query instead of multiple joins
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
    WHERE p.position IS NOT NULL
    """
    
    print("📊 Loading all player data...")
    df = execute_query(query)
    print(f"✅ Loaded {len(df)} players")
    
    # OPTIMIZATION 2: Process numeric columns once, not per player
    print("🔄 Converting columns to numeric...")
    exclude_cols = ['player_id', 'id', 'name', 'team', 'position', 'age', 'born', 
                   'nation', 'league', 'season', 'player', 'created_at']
    
    numeric_cols = []
    for col in df.columns:
        if col not in exclude_cols:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if df[col].notna().sum() > 5:  # Need at least 5 values
                    numeric_cols.append(col)
            except:
                pass
    
    print(f"✅ Found {len(numeric_cols)} numeric columns")
    
    # Position groups (same as yours)
    position_groups = {
        'forward': df[df['position'].str.contains('FW|CF|LW|RW', na=False)].copy(),
        'midfielder': df[df['position'].str.contains('MF|CM|DM|AM|LM|RM', na=False)].copy(),
        'defender': df[df['position'].str.contains('DF|CB|LB|RB|WB', na=False)].copy(),
        'goalkeeper': df[df['position'].str.contains('GK', na=False)].copy()
    }
    
    # Create table (same as yours)
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
    
    # OPTIMIZATION 3: Vectorized percentile calculation per position group
    for position_group, group_df in position_groups.items():
        if len(group_df) == 0:
            continue
            
        print(f"\n🏃 Processing {position_group}s ({len(group_df)} players)...")
        
        # OPTIMIZATION 4: Calculate percentiles for ALL players at once using pandas
        percentile_results = []
        
        # For each numeric column, calculate percentiles for all players at once
        percentile_data = {}
        for col in numeric_cols:
            if col in group_df.columns:
                # Get clean values
                clean_values = group_df[col].dropna()
                if len(clean_values) > 1:
                    # VECTORIZED percentile calculation - this is the key optimization!
                    # Instead of looping through each player, do it all at once
                    percentiles = group_df[col].rank(pct=True, na_option='keep') * 100
                    percentile_data[col] = percentiles
        
        # OPTIMIZATION 5: Batch insert instead of one-by-one
        batch_data = []
        
        for idx, (_, player) in enumerate(group_df.iterrows()):
            player_percentiles = {}
            
            # Extract this player's percentiles
            for col in numeric_cols:
                if col in percentile_data:
                    pct_value = percentile_data[col].iloc[idx]
                    if pd.notna(pct_value):
                        player_percentiles[col] = round(pct_value, 2)
                    else:
                        player_percentiles[col] = None
                else:
                    player_percentiles[col] = None
            
            # Add to batch
            batch_data.append({
                'player_id': int(player['player_id']),
                'position_group': position_group,
                'percentiles': json.dumps(player_percentiles)
            })
            
            # Progress indicator
            if (idx + 1) % 100 == 0:
                print(f"  📊 Processed {idx + 1}/{len(group_df)} {position_group}s...", end='\r')
        
        # OPTIMIZATION 6: Single batch insert for all players in this position
        print(f"\n💾 Batch inserting {len(batch_data)} {position_group}s...")
        
        # FIX: Use proper parameter syntax for SQLAlchemy
        insert_sql = text("""
        INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
        VALUES (:player_id, :position_group, :percentiles)
        ON CONFLICT (player_id) DO UPDATE
        SET percentiles = EXCLUDED.percentiles, 
            position_group = EXCLUDED.position_group,
            computed_at = CURRENT_TIMESTAMP
        """)
        
        try:
            with engine.begin() as conn:
                conn.execute(insert_sql, batch_data)
            print(f"✅ Successfully inserted {len(batch_data)} {position_group}s")
            
        except Exception as e:
            print(f"❌ Error in batch insert for {position_group}s: {e}")
            # Fallback to individual inserts if batch fails
            print("🔄 Falling back to individual inserts...")
            success_count = 0
            for item in batch_data:
                try:
                    with engine.begin() as conn:
                        conn.execute(insert_sql, item)
                    success_count += 1
                except Exception as e2:
                    print(f"❌ Failed to insert player {item['player_id']}: {e2}")
            print(f"✅ Individual inserts: {success_count}/{len(batch_data)} successful")
    
    print("\n🎉 All percentiles computed and stored!")
    
    # Show sample
    print("\n📊 Sample check:")
    try:
        sample_query = """
        SELECT p.name, pp.position_group, pp.computed_at
        FROM football_data.player_percentiles_all pp
        JOIN football_data.players p ON pp.player_id = p.id
        LIMIT 10
        """
        sample_df = execute_query(sample_query)
        print(sample_df)
    except Exception as e:
        print(f"Could not fetch sample: {e}")

if __name__ == "__main__":
    precompute_percentiles_optimized()