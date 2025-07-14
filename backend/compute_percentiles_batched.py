import pandas as pd
import numpy as np
import json
import os
import sys
import psycopg2
import time

def precompute_percentiles_batched():
    print("🚀 Computing percentiles (BATCHED VERSION)...")
    
    db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    
    # FIXED QUERY - Remove duplicates with DISTINCT
    query = """
    SELECT DISTINCT
        p.id as player_id,
        p.name,
        p.team,
        p.position,
        s.performance_gls,
        s.performance_ast,
        s.expected_xg,
        s.playing_time_90s,
        sh.standard_sh,
        sh.standard_sot,
        ps.total_cmp,
        ps.total_cmppct,
        ps.kp,
        ps.prgp,
        gsc.sca_sca,
        gsc.gca_gca,
        d.tackles_tklw,
        d.int,
        d.blocks_blocks,
        pos.carries_prgc,
        pos.touches_touches,
        m.aerial_duels_won,
        m.aerial_duels_wonpct,
        m.performance_recov
    FROM football_data.players p
    LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
    LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
    LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
    LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
    LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
    LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
    LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
    WHERE p.position IS NOT NULL
    """
    
    print("📊 Loading player data (with DISTINCT)...")
    df = pd.read_sql(query, conn)
    print(f"✅ Loaded {len(df)} players (should be ~3k now)")
    
    # Convert to numeric
    numeric_cols = []
    for col in df.columns:
        if col not in ['player_id', 'name', 'team', 'position']:
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
    
    # Process each position group in SMALL BATCHES
    for position_group, group_df in position_groups.items():
        if len(group_df) == 0:
            continue
            
        print(f"\n🏃 Processing {position_group}s ({len(group_df)} players)...")
        
        # Calculate percentiles
        percentile_data = {}
        for col in numeric_cols:
            if col in group_df.columns:
                clean_values = group_df[col].dropna()
                if len(clean_values) > 1:
                    percentiles = group_df[col].rank(pct=True, na_option='keep') * 100
                    percentile_data[col] = percentiles
        
        # Insert in SMALL batches of 100
        batch_size = 100
        total_players = len(group_df)
        
        for start_idx in range(0, total_players, batch_size):
            end_idx = min(start_idx + batch_size, total_players)
            batch_df = group_df.iloc[start_idx:end_idx]
            
            batch_data = []
            for batch_idx, (_, player) in enumerate(batch_df.iterrows()):
                actual_idx = start_idx + batch_idx
                player_percentiles = {}
                
                for col in numeric_cols:
                    if col in percentile_data:
                        pct_value = percentile_data[col].iloc[actual_idx]
                        if pd.notna(pct_value):
                            player_percentiles[col] = round(pct_value, 2)
                
                batch_data.append((
                    int(player['player_id']),
                    position_group,
                    json.dumps(player_percentiles)
                ))
            
            # Insert this batch
            insert_sql = """
            INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
            VALUES (%s, %s, %s)
            ON CONFLICT (player_id) DO UPDATE
            SET percentiles = EXCLUDED.percentiles
            """
            
            cur.executemany(insert_sql, batch_data)
            conn.commit()
            print(f"  ✅ Batch {start_idx+1}-{end_idx} inserted")
            
            # Small delay to avoid overwhelming the connection
            time.sleep(0.5)
    
    conn.close()
    print("\n🎉 All percentiles computed!")

if __name__ == "__main__":
    precompute_percentiles_batched()