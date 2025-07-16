# backend/check_player_metrics.py
import psycopg2
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CHANGE THESE VALUES TO CHECK DIFFERENT DATA
# ==========================================

# Player name (partial match is fine)
PLAYER_NAME = "Semenyo"  # Change to "Haaland", "De Bruyne", etc.

# Metrics to check (raw values from tables)
RAW_METRICS = [
    "performance_gls",      # Goals
    "performance_ast",      # Assists
    "expected_xg",          # Expected goals
    "standard_sh",          # Shots
    "kp",                   # Key passes
    "touches_att_pen",      # Touches in penalty area
    "aerial_duels_won",     # Aerial duels won
    "tackles_tklw",         # Tackles won
]

# Percentile metrics to check (these will have _pct suffix)
PERCENTILE_METRICS = [
    "performance_gls",      # Will check performance_gls percentile
    "expected_xg",          # Will check expected_xg percentile
    "kp",                   # Will check kp percentile
    "aerial_duels_wonpct",  # Will check aerial_duels_wonpct percentile
]

# ==========================================
# DON'T CHANGE BELOW THIS LINE
# ==========================================

def check_player_data():
    db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    
    print(f"\n🔍 CHECKING DATA FOR: {PLAYER_NAME}")
    print("=" * 80)
    
    # 1. Find the player
    query = f"""
    SELECT id, name, position, team, age 
    FROM football_data.players 
    WHERE name ILIKE '%{PLAYER_NAME}%'
    """
    
    players_df = pd.read_sql(query, conn)
    
    if players_df.empty:
        print(f"❌ No player found matching '{PLAYER_NAME}'")
        return
    
    print(f"\n✅ Found {len(players_df)} player(s):")
    for idx, player in players_df.iterrows():
        print(f"   {idx+1}. {player['name']} - {player['position']} - {player['team']}")
    
    # Use the first match
    player_id = players_df.iloc[0]['id']
    player_name = players_df.iloc[0]['name']
    player_position = players_df.iloc[0]['position']
    
    print(f"\n📊 Using: {player_name} (ID: {player_id})")
    
    # 2. Check raw metrics from tables
    print(f"\n{'='*80}")
    print("RAW METRIC VALUES FROM TABLES:")
    print(f"{'='*80}")
    
    # Build dynamic query based on which tables have which columns
    raw_query = f"""
    SELECT 
        p.name,
        s.performance_gls,
        s.performance_ast,
        s.expected_xg,
        s.expected_xag,
        s.performance_crdy,
        s.performance_crdr,
        sh.standard_sh,
        sh.standard_sot,
        sh.standard_dist,
        ps.total_cmp,
        ps.total_att,
        ps.total_cmppct,
        ps.kp,
        ps.prgp,
        gsc.sca_sca,
        gsc.gca_gca,
        pos.touches_att_pen,
        pos.carries_prgc,
        pos.take_ons_succ,
        m.aerial_duels_won,
        m.aerial_duels_wonpct,
        m.performance_recov,
        d.tackles_tklw,
        d.int,
        d.blocks_blocks
    FROM football_data.players p
    LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
    LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
    LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
    LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
    LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
    LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
    LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
    WHERE p.id = {player_id}
    """
    
    raw_df = pd.read_sql(raw_query, conn)
    
    if not raw_df.empty:
        print(f"\n📈 Raw metrics for {player_name}:")
        for metric in RAW_METRICS:
            if metric in raw_df.columns:
                value = raw_df.iloc[0][metric]
                print(f"   {metric:<25} = {value if pd.notna(value) else 'NULL'}")
            else:
                print(f"   {metric:<25} = COLUMN NOT FOUND")
    
    # 3. Check percentiles
    print(f"\n{'='*80}")
    print("PERCENTILE VALUES:")
    print(f"{'='*80}")
    
    pct_query = f"""
    SELECT percentiles, position_group
    FROM football_data.player_percentiles_all
    WHERE player_id = {player_id}
    """
    
    pct_df = pd.read_sql(pct_query, conn)
    
    if not pct_df.empty:
        percentiles = json.loads(pct_df.iloc[0]['percentiles'])
        position_group = pct_df.iloc[0]['position_group']
        
        print(f"\n📊 Percentiles for {player_name} ({position_group}):")
        
        # Show requested percentiles
        for metric in PERCENTILE_METRICS:
            if metric in percentiles:
                print(f"   {metric:<25} = {percentiles[metric]:.1f} percentile")
            else:
                print(f"   {metric:<25} = NOT COMPUTED")
        
        # Show all available percentiles
        print(f"\n📋 ALL AVAILABLE PERCENTILES ({len(percentiles)} total):")
        sorted_percentiles = sorted(percentiles.items(), key=lambda x: x[1], reverse=True)
        
        # Show top 10 and bottom 10
        print("\n   TOP 10 PERCENTILES:")
        for metric, value in sorted_percentiles[:10]:
            print(f"   {metric:<25} = {value:.1f} percentile")
        
        print("\n   BOTTOM 10 PERCENTILES:")
        for metric, value in sorted_percentiles[-10:]:
            print(f"   {metric:<25} = {value:.1f} percentile")
    else:
        print(f"❌ No percentiles found for player ID {player_id}")
    
    # 4. Position-specific composite metrics
    print(f"\n{'='*80}")
    print("COMPOSITE METRIC BREAKDOWN:")
    print(f"{'='*80}")
    
    # Import position metrics
    from app.core.position_metrics import POSITION_METRICS
    
    # Determine position group
    if 'FW' in player_position or 'CF' in player_position:
        pos_group = 'forward'
    elif 'MF' in player_position:
        pos_group = 'midfielder'
    elif 'DF' in player_position or 'CB' in player_position:
        pos_group = 'defender'
    elif 'GK' in player_position:
        pos_group = 'goalkeeper'
    else:
        pos_group = None
    
    if pos_group and pos_group in POSITION_METRICS:
        print(f"\n🎯 Composite metrics for {pos_group}:")
        
        for metric_id, metric_info in POSITION_METRICS[pos_group].items():
            print(f"\n   {metric_info['name']}:")
            print(f"   Description: {metric_info['description']}")
            print(f"   Components:")
            
            total_score = 0
            for col, weight in metric_info['weights'].items():
                if col in percentiles:
                    pct_value = percentiles[col]
                    # Handle negative weights
                    if weight < 0:
                        pct_value = 100 - pct_value
                        weight = abs(weight)
                    contribution = pct_value * weight
                    total_score += contribution
                    print(f"      - {col:<20} = {percentiles[col]:.1f}% × {weight} = {contribution:.1f}")
                else:
                    print(f"      - {col:<20} = MISSING")
            
            # Normalize by sum of weights
            sum_weights = sum(abs(w) for w in metric_info['weights'].values())
            if sum_weights > 0:
                final_score = total_score / sum_weights
                print(f"   FINAL SCORE: {final_score:.1f}/100")
    
    conn.close()

if __name__ == "__main__":
    check_player_data()