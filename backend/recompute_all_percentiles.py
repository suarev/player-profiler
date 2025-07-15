# backend/recompute_all_percentiles.py
import pandas as pd
import numpy as np
import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def recompute_all_percentiles():
    print("🚀 Recomputing ALL percentiles with complete data...")
    
    conn = psycopg2.connect(os.getenv("DATABASE_PUBLIC_URL"))
    
    # Now we can use ALL columns including the newly scraped ones
    query = """
    SELECT DISTINCT
        p.id as player_id,
        p.name,
        p.team,
        p.position,
        -- Standard stats
        s.performance_gls,
        s.performance_ast,
        s.expected_xg,
        s.expected_xag,
        s.playing_time_90s,
        s.performance_crdy,
        s.performance_crdr,
        -- Shooting stats
        sh.standard_sh,
        sh.standard_sot,
        sh.standard_dist,
        -- Passing stats
        ps.total_cmp,
        ps.total_att,
        ps.total_cmppct,
        ps.kp,
        ps.prgp,
        ps.long_cmp,
        -- Goal/Shot Creation
        gsc.sca_sca,
        gsc.gca_gca,
        -- Defense stats (NOW AVAILABLE!)
        d.tackles_tkl,
        d.tackles_tklw,
        d.tackles_def_3rd,
        d.tackles_mid_3rd,
        d.tackles_att_3rd,
        d.int,
        d.blocks_blocks,
        d.blocks_pass,
        d.clr,
        d.err,
        -- Possession stats (NOW AVAILABLE!)
        pos.touches_touches,
        pos.touches_def_3rd,
        pos.touches_mid_3rd,
        pos.touches_att_3rd,
        pos.touches_att_pen,
        pos.carries_carries,
        pos.carries_prgc,
        pos.carries_cpa,
        pos.carries_1_per_3,
        pos.carries_mis,
        pos.take_ons_succ,
        pos.receiving_rec,
        -- Playing time stats (NOW AVAILABLE!)
        pt.playing_time_mp,
        pt.playing_time_min,
        pt.playing_time_90s as pt_90s,
        -- Misc stats (NOW AVAILABLE!)
        m.performance_crdy as m_crdy,
        m.performance_crdr as m_crdr,
        m.performance_fls,
        m.performance_fld,
        m.performance_og,
        m.performance_recov,
        m.aerial_duels_won,
        m.aerial_duels_wonpct,
        m.aerial_duels_lost
    FROM football_data.players p
    LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
    LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
    LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
    LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
    LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
    LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
    LEFT JOIN football_data.player_playing_time_stats pt ON p.name = pt.player
    LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
    WHERE p.position IS NOT NULL
    """
    
    print("📊 Loading ALL player data...")
    df = pd.read_sql(query, conn)
    print(f"✅ Loaded {len(df)} players")
    
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
    
    print(f"✅ Found {len(numeric_cols)} numeric columns (should be way more now!)")
    
    # Position groups
    position_groups = {
        'forward': df[df['position'].str.contains('FW|CF|LW|RW', na=False)],
        'midfielder': df[df['position'].str.contains('MF|CM|DM|AM|LM|RM', na=False)],
        'defender': df[df['position'].str.contains('DF|CB|LB|RB|WB', na=False)],
        'goalkeeper': df[df['position'].str.contains('GK', na=False)]
    }
    
    # Create/update percentiles table
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
        
        # Calculate percentiles for ALL columns
        percentile_data = {}
        for col in numeric_cols:
            if col in group_df.columns:
                clean_values = group_df[col].dropna()
                if len(clean_values) > 1:
                    percentiles = group_df[col].rank(pct=True, na_option='keep') * 100
                    percentile_data[col] = percentiles
        
        # Insert into database
        for idx, (_, player) in enumerate(group_df.iterrows()):
            player_percentiles = {}
            
            for col in numeric_cols:
                if col in percentile_data:
                    pct_value = percentile_data[col].iloc[idx]
                    if pd.notna(pct_value):
                        player_percentiles[col] = round(pct_value, 2)
            
            cur.execute("""
            INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
            VALUES (%s, %s, %s)
            ON CONFLICT (player_id) DO UPDATE
            SET percentiles = EXCLUDED.percentiles,
                position_group = EXCLUDED.position_group,
                computed_at = CURRENT_TIMESTAMP
            """, (int(player['player_id']), position_group, json.dumps(player_percentiles)))
        
        conn.commit()
        print(f"✅ Computed percentiles for {len(group_df)} {position_group}s")
    
    conn.close()
    print("\n🎉 ALL percentiles computed successfully!")

if __name__ == "__main__":
    recompute_all_percentiles()