# backend/compute_all_percentiles_complete.py
import pandas as pd
import numpy as np
import json
import os
import psycopg2
from sqlalchemy import create_engine

def compute_all_percentiles():
    """Compute percentiles for ALL positions including goalkeepers"""
    
    db_url = os.getenv('DATABASE_PUBLIC_URL')
    conn = psycopg2.connect(db_url)
    engine = create_engine(db_url.replace('postgres://', 'postgresql://'))
    
    print("🚀 Computing percentiles for ALL positions...")
    
    # Different queries for different positions
    queries = {
        'forward': """
            SELECT DISTINCT
                p.id as player_id,
                p.name,
                p.position,
                -- Goals & Shooting
                COALESCE(s.performance_gls::numeric, 0) as performance_gls,
                COALESCE(s.expected_xg::numeric, 0) as expected_xg,
                COALESCE(sh.standard_sh::numeric, 0) as standard_sh,
                COALESCE(sh.standard_sot::numeric, 0) as standard_sot,
                -- Assists & Creation
                COALESCE(s.performance_ast::numeric, 0) as performance_ast,
                COALESCE(s.expected_xag::numeric, 0) as expected_xag,
                COALESCE(ps.kp::numeric, 0) as kp,
                COALESCE(gsc.sca_sca::numeric, 0) as sca_sca,
                -- Dribbling & Carries (if we have possession table)
                COALESCE(pos.take_ons_succ::numeric, 0) as take_ons_succ,
                COALESCE(pos.carries_prgc::numeric, 0) as carries_prgc,
                COALESCE(pos.carries_cpa::numeric, 0) as carries_cpa,
                COALESCE(pos.carries_1_per_3::numeric, 0) as carries_1_per_3,
                -- Physical (if we have misc table)
                COALESCE(m.aerial_duels_won::numeric, 0) as aerial_duels_won,
                COALESCE(m.aerial_duels_wonpct::numeric, 0) as aerial_duels_wonpct,
                -- Work Rate (if we have defense/misc tables)
                COALESCE(m.performance_recov::numeric, 0) as performance_recov,
                COALESCE(d.tackles_att_3rd::numeric, 0) as tackles_att_3rd,
                COALESCE(d.blocks_pass::numeric, 0) as blocks_pass,
                -- Box Presence
                COALESCE(pos.touches_att_pen::numeric, 0) as touches_att_pen
            FROM football_data.players p
            LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
            LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
            LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
            LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
            LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
            LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
            LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
            WHERE p.position LIKE '%FW%' OR p.position LIKE '%CF%' 
               OR p.position LIKE '%LW%' OR p.position LIKE '%RW%'
        """,
        
        'midfielder': """
            SELECT DISTINCT
                p.id as player_id,
                p.name,
                p.position,
                -- Passing
                COALESCE(ps.total_cmp::numeric, 0) as total_cmp,
                COALESCE(ps.total_cmppct::numeric, 0) as total_cmppct,
                COALESCE(ps.prgp::numeric, 0) as prgp,
                COALESCE(ps.kp::numeric, 0) as kp,
                COALESCE(ps.long_cmp::numeric, 0) as long_cmp,
                -- Creation
                COALESCE(s.performance_ast::numeric, 0) as performance_ast,
                COALESCE(s.expected_xag::numeric, 0) as expected_xag,
                COALESCE(gsc.sca_sca::numeric, 0) as sca_sca,
                COALESCE(gsc.gca_gca::numeric, 0) as gca_gca,
                -- Defense
                COALESCE(d.tackles_tkl::numeric, 0) as tackles_tkl,
                COALESCE(d.int::numeric, 0) as int,
                COALESCE(d.blocks_blocks::numeric, 0) as blocks_blocks,
                -- Possession
                COALESCE(pos.touches_touches::numeric, 0) as touches_touches,
                COALESCE(pos.touches_mid_3rd::numeric, 0) as touches_mid_3rd,
                COALESCE(pos.receiving_rec::numeric, 0) as receiving_rec,
                COALESCE(pos.carries_mis::numeric, 0) as carries_mis,
                -- Goal Threat
                COALESCE(s.performance_gls::numeric, 0) as performance_gls,
                COALESCE(sh.standard_sh::numeric, 0) as standard_sh,
                COALESCE(sh.standard_dist::numeric, 0) as standard_dist,
                COALESCE(pos.touches_att_3rd::numeric, 0) as touches_att_3rd
            FROM football_data.players p
            LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
            LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
            LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
            LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
            LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
            LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
            WHERE p.position LIKE '%MF%' OR p.position LIKE '%CM%' 
               OR p.position LIKE '%DM%' OR p.position LIKE '%AM%'
        """,
        
        'defender': """
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
                COALESCE(s.performance_og::numeric, 0) as performance_og,
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
               OR p.position LIKE '%LB%' OR p.position LIKE '%RB%'
        """,
        
        'goalkeeper': """
            SELECT DISTINCT
                p.id as player_id,
                p.name,
                p.position,
                -- Shot Stopping
                COALESCE(k.performance_saves::numeric, 0) as performance_saves,
                COALESCE(k.performance_savepct::numeric, 0) as performance_savepct,
                COALESCE(k.performance_sota::numeric, 0) as performance_sota,
                -- Command of Area
                COALESCE(ka.crosses_stp::numeric, 0) as crosses_stp,
                COALESCE(ka.crosses_stppct::numeric, 0) as crosses_stppct,
                COALESCE(ka.sweeper_avgdist::numeric, 0) as sweeper_avgdist,
                -- Distribution
                COALESCE(ka.launched_cmppct::numeric, 0) as launched_cmppct,
                COALESCE(ka.passes_launchpct::numeric, 0) as passes_launchpct,
                COALESCE(ka.passes_avglen::numeric, 0) as passes_avglen,
                COALESCE(ka.goal_kicks_avglen::numeric, 0) as goal_kicks_avglen,
                -- Sweeping
                COALESCE(ka.sweeper_numopa::numeric, 0) as sweeper_numopa,
                COALESCE(ka.sweeper_numopa_per_90::numeric, 0) as sweeper_numopa_per_90,
                -- Penalties
                COALESCE(k.penalty_kicks_pksv::numeric, 0) as penalty_kicks_pksv,
                COALESCE(k.penalty_kicks_savepct::numeric, 0) as penalty_kicks_savepct,
                -- Consistency
                COALESCE(k.performance_cs::numeric, 0) as performance_cs,
                COALESCE(k.performance_cspct::numeric, 0) as performance_cspct,
                COALESCE(k.performance_ga90::numeric, 0) as performance_ga90
            FROM football_data.players p
            LEFT JOIN football_data.player_keeper_stats k ON p.name = k.player
            LEFT JOIN football_data.player_keeper_adv_stats ka ON p.name = ka.player
            WHERE p.position LIKE '%GK%'
        """
    }
    
    # Create percentiles table
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
    
    # Process each position
    for position_group, query in queries.items():
        print(f"\n📊 Computing percentiles for {position_group}s...")
        
        # Use pandas for efficient computation
        df = pd.read_sql(query, engine)
        
        if len(df) == 0:
            print(f"⚠️ No {position_group}s found!")
            continue
            
        print(f"Found {len(df)} {position_group}s")
        
        # Get numeric columns (exclude id, name, position)
        numeric_cols = [col for col in df.columns if col not in ['player_id', 'name', 'position']]
        
        # Calculate percentiles for each numeric column
        percentiles = {}
        for col in numeric_cols:
            # Rank with proper handling of ties
            df[f'{col}_pct'] = df[col].rank(pct=True, method='average') * 100
            percentiles[col] = df[f'{col}_pct']
        
        # Insert into database
        for idx, row in df.iterrows():
            player_percentiles = {}
            for col in numeric_cols:
                pct_value = percentiles[col].iloc[idx]
                if pd.notna(pct_value):
                    player_percentiles[col] = round(pct_value, 2)
                else:
                    player_percentiles[col] = 50.0  # Default
            
            cur.execute("""
            INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
            VALUES (%s, %s, %s)
            ON CONFLICT (player_id) DO UPDATE
            SET percentiles = EXCLUDED.percentiles,
                position_group = EXCLUDED.position_group,
                computed_at = CURRENT_TIMESTAMP
            """, (int(row['player_id']), position_group, json.dumps(player_percentiles)))
        
        conn.commit()
        print(f"✅ Inserted percentiles for {len(df)} {position_group}s")
    
    conn.close()
    print("\n🎉 All percentiles computed successfully!")

if __name__ == "__main__":
    compute_all_percentiles()