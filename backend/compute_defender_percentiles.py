# backend/compute_defender_percentiles.py
import pandas as pd
import numpy as np
import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def compute_defender_percentiles():
    """Compute percentiles ONLY for defenders with corrected column references"""
    
    db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    
    print("🚀 Computing percentiles for defenders (with correct columns)...")
    
    # FIXED QUERY - performance_og is in misc table (m), not standard (s)
    query = """
        SELECT DISTINCT
            p.id as player_id,
            p.name,
            p.position,
            -- Defensive Actions
            COALESCE(d.tackles_tkl::numeric, 0) as tackles_tkl,
            COALESCE(d.tackles_tklw::numeric, 0) as tackles_tklw,
            COALESCE(d.blocks_blocks::numeric, 0) as blocks_blocks,
            COALESCE(d.int::numeric, 0) as int,
            COALESCE(d.clr::numeric, 0) as clr,
            -- Aerial
            COALESCE(m.aerial_duels_won::numeric, 0) as aerial_duels_won,
            COALESCE(m.aerial_duels_wonpct::numeric, 0) as aerial_duels_wonpct,
            -- Ball Playing
            COALESCE(ps.total_cmp::numeric, 0) as total_cmp,
            COALESCE(ps.total_cmppct::numeric, 0) as total_cmppct,
            COALESCE(ps.prgp::numeric, 0) as prgp,
            COALESCE(ps.long_cmp::numeric, 0) as long_cmp,
            COALESCE(pos.carries_prgc::numeric, 0) as carries_prgc,
            -- Positional
            COALESCE(d.tackles_def_3rd::numeric, 0) as tackles_def_3rd,
            COALESCE(d.err::numeric, 0) as err,
            COALESCE(m.performance_og::numeric, 0) as performance_og,  -- FIXED: m. not s.
            COALESCE(pos.touches_def_3rd::numeric, 0) as touches_def_3rd,
            -- Recovery
            COALESCE(m.performance_recov::numeric, 0) as performance_recov,
            COALESCE(d.challenges_lost::numeric, 0) as challenges_lost,
            COALESCE(d.tackles_att_3rd::numeric, 0) as tackles_att_3rd,
            -- Discipline
            COALESCE(s.performance_crdy::numeric, 0) as performance_crdy,
            COALESCE(s.performance_crdr::numeric, 0) as performance_crdr,
            COALESCE(m.performance_fls::numeric, 0) as performance_fls
        FROM football_data.players p
        LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
        LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
        LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
        LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
        LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
        WHERE p.position LIKE '%DF%' OR p.position LIKE '%CB%' 
           OR p.position LIKE '%LB%' OR p.position LIKE '%RB%' OR p.position LIKE '%WB%'
    """
    
    cur = conn.cursor()
    
    try:
        # Use pandas read_sql with psycopg2 connection
        df = pd.read_sql(query, conn)
        
        print(f"Found {len(df)} defenders")
        
        if len(df) == 0:
            print("⚠️ No defenders found!")
            return
        
        # Get numeric columns
        numeric_cols = [col for col in df.columns if col not in ['player_id', 'name', 'position']]
        
        # Calculate percentiles
        percentiles = {}
        for col in numeric_cols:
            df[f'{col}_pct'] = df[col].rank(pct=True, method='average') * 100
            percentiles[col] = df[f'{col}_pct']
        
        # Insert into database
        batch_size = 100
        inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            for idx, row in batch.iterrows():
                player_percentiles = {}
                for col in numeric_cols:
                    pct_value = percentiles[col].iloc[idx]
                    if pd.notna(pct_value):
                        player_percentiles[col] = round(pct_value, 2)
                    else:
                        player_percentiles[col] = 50.0
                
                cur.execute("""
                INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
                VALUES (%s, %s, %s)
                ON CONFLICT (player_id) DO UPDATE
                SET percentiles = EXCLUDED.percentiles,
                    position_group = EXCLUDED.position_group,
                    computed_at = CURRENT_TIMESTAMP
                """, (int(row['player_id']), 'defender', json.dumps(player_percentiles)))
            
            conn.commit()
            inserted += len(batch)
            print(f"  Processed {inserted}/{len(df)} defenders...")
        
        print(f"✅ Completed defenders - {len(df)} players processed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    compute_defender_percentiles()