# backend/scripts/recompute_goalkeeper_percentiles.py
import pandas as pd
import numpy as np
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, execute_query
from sqlalchemy import text

def recompute_goalkeeper_percentiles():
    """Recompute percentiles ONLY for goalkeepers with proper tables"""
    print("🚀 Recomputing goalkeeper percentiles with correct data...")
    
    # Get goalkeeper data INCLUDING keeper-specific tables
    query = """
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
    AND k.player IS NOT NULL
    """
    
    print("📊 Loading goalkeeper data from keeper-specific tables...")
    df = execute_query(query)
    
    if df.empty:
        print("❌ No goalkeeper data found!")
        return
        
    print(f"✅ Loaded {len(df)} goalkeepers")
    
    # Clean numeric columns
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
    print("\nSample keeper-specific columns found:")
    keeper_cols = [col for col in numeric_cols if any(x in col for x in ['saves', 'ga', 'cs', 'crosses', 'sweep', 'launch', 'penalty'])]
    for col in keeper_cols[:10]:
        print(f"  - {col}")
    
    # Calculate percentiles
    percentile_data = {}
    for col in numeric_cols:
        clean_values = df[col].dropna()
        if len(clean_values) > 1:
            percentiles = df[col].rank(pct=True, na_option='keep') * 100
            percentile_data[col] = percentiles
    
    # Prepare batch update
    batch_data = []
    for idx, (_, player) in enumerate(df.iterrows()):
        player_percentiles = {}
        
        for col in numeric_cols:
            if col in percentile_data:
                pct_value = percentile_data[col].iloc[idx]
                if pd.notna(pct_value):
                    player_percentiles[col] = round(pct_value, 2)
    
        batch_data.append({
            'player_id': int(player['player_id']),
            'position_group': 'goalkeeper',
            'percentiles': json.dumps(player_percentiles)
        })
        
        if (idx + 1) % 100 == 0:
            print(f"  📊 Processed {idx + 1}/{len(df)} goalkeepers...", end='\r')
    
    # Update database
    print(f"\n💾 Updating {len(batch_data)} goalkeeper percentiles...")
    
    update_sql = text("""
    INSERT INTO football_data.player_percentiles_all (player_id, position_group, percentiles)
    VALUES (:player_id, :position_group, :percentiles)
    ON CONFLICT (player_id) DO UPDATE
    SET percentiles = EXCLUDED.percentiles,
        position_group = EXCLUDED.position_group,
        computed_at = CURRENT_TIMESTAMP
    """)
    
    try:
        with engine.begin() as conn:
            conn.execute(update_sql, batch_data)
        print(f"✅ Successfully updated {len(batch_data)} goalkeepers")
    except Exception as e:
        print(f"❌ Error updating: {e}")
    
    # Verify
    print("\n📊 Verification:")
    verify_query = """
    SELECT 
        p.name,
        pp.percentiles::text
    FROM football_data.player_percentiles_all pp
    JOIN football_data.players p ON pp.player_id = p.id
    WHERE pp.position_group = 'goalkeeper'
    LIMIT 1
    """
    
    result = execute_query(verify_query)
    if not result.empty:
        percentiles = json.loads(result.iloc[0]['percentiles'])
        print(f"\nSample keeper: {result.iloc[0]['name']}")
        print("Keeper-specific percentile columns:")
        keeper_specific = [col for col in percentiles.keys() if any(x in col for x in ['saves', 'ga', 'cs', 'crosses', 'sweep', 'launch'])]
        for col in keeper_specific[:10]:
            print(f"  - {col}")

if __name__ == "__main__":
    recompute_goalkeeper_percentiles()