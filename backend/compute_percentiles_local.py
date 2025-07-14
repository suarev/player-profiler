"""
Percentiles script that works with railway run
"""
import pandas as pd
import numpy as np
import json
import os
import sys
import psycopg2

def precompute_percentiles_railway():
    """
    Compute percentiles using PUBLIC URL for railway run
    """
    print("🚀 Computing percentiles (RAILWAY VERSION)...")
    
    # Use PUBLIC URL for railway run
    db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ No database URL found!")
        sys.exit(1)
    
    print(f"📊 Connecting to database...")
    conn = psycopg2.connect(db_url)
    
    # Get ALL data in ONE query
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
    df = pd.read_sql(query, conn)
    print(f"✅ Loaded {len(df)} players")
    
    # Process numeric columns
    print("🔄 Converting columns to numeric...")
    exclude_cols = ['player_id', 'id', 'name', 'team', 'position', 'age', 'born', 
                   'nation', 'league', 'season', 'player', 'created_at']
    
    numeric_cols = []
    for col in df.columns:
        if col not in exclude_cols:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if df[col].notna().sum() > 5:
                    numeric_cols.append(col)
            except:
                pass
    
    print(f"✅ Found {len(numeric_cols)} numeric columns")
    
    # Position groups
    position_groups = {
        'forward': df[df['position'].str.contains('FW|CF|LW|RW', na=False)].copy(),
        'midfielder': df[df['position'].str.contains('MF|CM|DM|AM|LM|RM', na=False)].copy(),
        'defender': df[df['position'].str.contains('DF|CB|LB|RB|WB', na=False)].copy(),
        'goalkeeper': df[df['position'].str.contains('GK', na=False)].copy()
    }
    
    # Create table
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS football_data.player_percentiles_all (
        player_id INTEGER PRIMARY KEY,
        position_group VARCHAR(20),
        percentiles JSONB,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    
    # Process each position group
    for position_group, group_df in position_groups.items():
        if len(group_df) == 0:
            continue
            
        print(f"\n🏃 Processing {position_group}s ({len(group_df)} players)...")
        
        # Calculate percentiles for all players at once
        percentile_data = {}
        for col in numeric_cols:
            if col in group_df.columns:
                clean_values = group_df[col].dropna()
                if len(clean_values) > 1:
                    percentiles = group_df[col].rank(pct=True, na_option='keep') * 100
                    percentile_data[col] = percentiles
        
        # Batch insert
        batch_data = []
        for idx, (_, player) in enumerate(group_df.iterrows()):
            player_percentiles = {}
            
            for col in numeric_cols:
                if col in percentile_data:
                    pct_value = percentile_data[col].iloc[idx]
                    if pd.notna(pct_value):
                        player_percentiles[col] = round(pct_value, 2)
                    else:
                        player_percentiles[col] = None
                else:
                    player_percentiles[col] = None
            
            batch_data.append((
                int(player['player_id']),
                position_group,
                json.dumps(player_percentiles)
            ))
        
        print(f"💾 Inserting {len(batch_data)} {position_group}s...")
        
        insert_sql = """
        INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
        VALUES (%s, %s, %s)
        ON CONFLICT (player_id) DO UPDATE
        SET percentiles = EXCLUDED.percentiles, 
            position_group = EXCLUDED.position_group,
            computed_at = CURRENT_TIMESTAMP
        """
        
        cur.executemany(insert_sql, batch_data)
        conn.commit()
        print(f"✅ Successfully inserted {len(batch_data)} {position_group}s")
    
    conn.close()
    print("\n🎉 All percentiles computed and stored!")

if __name__ == "__main__":
    precompute_percentiles_railway()