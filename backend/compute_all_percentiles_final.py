# backend/compute_all_percentiles_final.py
import pandas as pd
import numpy as np
import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def compute_all_percentiles_complete():
    """Compute percentiles for EVERY SINGLE NUMERIC COLUMN"""
    
    db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    
    print("🚀 Computing percentiles for ALL metrics (no cherry-picking!)")
    
    # Get ALL data with ALL columns
    query = """
    SELECT 
        p.id as player_id,
        p.name,
        p.position,
        -- Just select EVERYTHING from each table
        s.*,
        sh.*,
        ps.*,
        pt.*,
        gsc.*,
        d.*,
        pos.*,
        m.*
    FROM football_data.players p
    LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
    LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
    LEFT JOIN football_data.player_passing_stats ps ON p.name = ps.player
    LEFT JOIN football_data.player_passing_types_stats pt ON p.name = pt.player
    LEFT JOIN football_data.player_goal_shot_creation_stats gsc ON p.name = gsc.player
    LEFT JOIN football_data.player_defense_stats d ON p.name = d.player
    LEFT JOIN football_data.player_possession_stats pos ON p.name = pos.player
    LEFT JOIN football_data.player_playing_time_stats plt ON p.name = plt.player
    LEFT JOIN football_data.player_misc_stats m ON p.name = m.player
    WHERE p.position IS NOT NULL
    """
    
    print("📊 Loading ALL player data...")
    df = pd.read_sql(query, conn)
    print(f"✅ Loaded {len(df)} players with {len(df.columns)} columns")
    
    # Remove duplicate columns (from the JOIN)
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Identify position groups
    def get_position_group(pos):
        if pd.isna(pos):
            return None
        pos = str(pos).upper()
        if any(x in pos for x in ['FW', 'CF', 'LW', 'RW', 'ST']):
            return 'forward'
        elif any(x in pos for x in ['MF', 'CM', 'DM', 'AM', 'LM', 'RM', 'CAM', 'CDM']):
            return 'midfielder'
        elif any(x in pos for x in ['DF', 'CB', 'LB', 'RB', 'WB', 'FB']):
            return 'defender'
        elif 'GK' in pos:
            return 'goalkeeper'
        return None
    
    df['position_group'] = df['position'].apply(get_position_group)
    
    # Get all numeric columns (excluding IDs and metadata)
    exclude_cols = ['player_id', 'id', 'name', 'position', 'position_group', 'team', 
                   'nation', 'league', 'season', 'player', 'pos', 'age', 'born', 
                   'created_at', 'club']
    
    numeric_cols = []
    for col in df.columns:
        if col not in exclude_cols:
            try:
                # Try to convert to numeric
                test = pd.to_numeric(df[col], errors='coerce')
                # If more than 10% are valid numbers, consider it numeric
                if test.notna().sum() > len(df) * 0.1:
                    df[col] = test
                    numeric_cols.append(col)
            except:
                pass
    
    print(f"✅ Found {len(numeric_cols)} numeric columns to compute percentiles for")
    print(f"📋 Sample columns: {numeric_cols[:10]}...")
    
    # Create/reset percentiles table
    cur = conn.cursor()
    cur.execute("""
    DROP TABLE IF EXISTS football_data.player_percentiles_all;
    CREATE TABLE football_data.player_percentiles_all (
        player_id INTEGER PRIMARY KEY,
        position_group VARCHAR(20),
        percentiles JSONB,
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    print("✅ Reset percentiles table")
    
    # Process each position group
    position_groups = df.groupby('position_group')
    
    for position_group, group_df in position_groups:
        if position_group is None:
            continue
            
        print(f"\n📊 Computing percentiles for {position_group}s ({len(group_df)} players)...")
        
        # Compute percentiles for ALL numeric columns in this position group
        percentile_data = {}
        computed_cols = []
        
        for col in numeric_cols:
            if col in group_df.columns:
                # Get non-null values
                valid_values = group_df[col].dropna()
                
                if len(valid_values) > 5:  # Need at least 5 values to compute meaningful percentiles
                    # Compute percentiles
                    percentiles = group_df[col].rank(pct=True, method='average') * 100
                    percentile_data[col] = percentiles
                    computed_cols.append(col)
        
        print(f"✅ Computed percentiles for {len(computed_cols)} metrics")
        
        # Insert into database
        inserted = 0
        for idx, row in group_df.iterrows():
            player_percentiles = {}
            
            # Get percentile for each column
            for col in computed_cols:
                if col in percentile_data:
                    pct_value = percentile_data[col].loc[idx]
                    if pd.notna(pct_value):
                        player_percentiles[col] = round(float(pct_value), 2)
            
            # Only insert if we have percentiles
            if player_percentiles and not pd.isna(row['player_id']):
                try:
                    cur.execute("""
                    INSERT INTO football_data.player_percentiles_all 
                    (player_id, position_group, percentiles)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (player_id) DO UPDATE
                    SET percentiles = EXCLUDED.percentiles,
                        position_group = EXCLUDED.position_group,
                        computed_at = CURRENT_TIMESTAMP
                    """, (int(row['player_id']), position_group, json.dumps(player_percentiles)))
                    inserted += 1
                except Exception as e:
                    print(f"⚠️ Error inserting player {row.get('name', 'Unknown')}: {e}")
        
        conn.commit()
        print(f"✅ Inserted {inserted} {position_group}s with percentiles")
        
        # Show sample of what we computed
        if computed_cols:
            print(f"📋 Sample metrics computed: {computed_cols[:15]}...")
    
    # Add goalkeeper percentiles if they exist
    print("\n📊 Computing goalkeeper percentiles...")
    
    gk_query = """
    SELECT 
        p.id as player_id,
        p.name,
        p.position,
        k.*,
        ka.*
    FROM football_data.players p
    LEFT JOIN football_data.player_keeper_stats k ON p.name = k.player
    LEFT JOIN football_data.player_keeper_adv_stats ka ON p.name = ka.player
    WHERE p.position LIKE '%GK%'
    """
    
    gk_df = pd.read_sql(gk_query, conn)
    if not gk_df.empty:
        gk_df = gk_df.loc[:, ~gk_df.columns.duplicated()]
        
        # Get numeric columns for goalkeepers
        gk_numeric_cols = []
        for col in gk_df.columns:
            if col not in exclude_cols:
                try:
                    test = pd.to_numeric(gk_df[col], errors='coerce')
                    if test.notna().sum() > len(gk_df) * 0.1:
                        gk_df[col] = test
                        gk_numeric_cols.append(col)
                except:
                    pass
        
        print(f"✅ Found {len(gk_numeric_cols)} goalkeeper-specific metrics")
        
        # Compute percentiles
        gk_percentile_data = {}
        for col in gk_numeric_cols:
            valid_values = gk_df[col].dropna()
            if len(valid_values) > 3:
                percentiles = gk_df[col].rank(pct=True, method='average') * 100
                gk_percentile_data[col] = percentiles
        
        # Update goalkeeper records
        for idx, row in gk_df.iterrows():
            player_percentiles = {}
            for col, percentiles in gk_percentile_data.items():
                pct_value = percentiles.loc[idx]
                if pd.notna(pct_value):
                    player_percentiles[col] = round(float(pct_value), 2)
            
            if player_percentiles and not pd.isna(row['player_id']):
                cur.execute("""
                UPDATE football_data.player_percentiles_all
                SET percentiles = percentiles || %s::jsonb
                WHERE player_id = %s
                """, (json.dumps(player_percentiles), int(row['player_id'])))
        
        conn.commit()
        print(f"✅ Updated goalkeeper percentiles")
    
    # Final summary
    cur.execute("""
    SELECT 
        position_group,
        COUNT(*) as count,
        AVG(jsonb_array_length(jsonb_object_keys(percentiles))) as avg_metrics
    FROM football_data.player_percentiles_all
    GROUP BY position_group
    """)
    
    print("\n📊 FINAL SUMMARY:")
    print("-" * 50)
    for row in cur.fetchall():
        print(f"{row[0]}: {row[1]} players")
    
    # Check a sample player to see all metrics
    cur.execute("""
    SELECT name, position_group, percentiles
    FROM football_data.player_percentiles_all pp
    JOIN football_data.players p ON pp.player_id = p.id
    WHERE position_group = 'forward'
    LIMIT 1
    """)
    
    sample = cur.fetchone()
    if sample:
        percentiles = json.loads(sample[2])
        print(f"\n📋 Sample: {sample[0]} has {len(percentiles)} percentile values")
        print(f"Including: {list(percentiles.keys())[:20]}...")
    
    conn.close()
    print("\n🎉 All percentiles computed successfully!")

if __name__ == "__main__":
    compute_all_percentiles_complete()