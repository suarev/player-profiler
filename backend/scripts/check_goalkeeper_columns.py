# backend/scripts/check_goalkeeper_columns.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import execute_query
import json

# Check what columns exist in keeper stats table
print("=== CHECKING KEEPER STATS TABLE COLUMNS ===")
query = """
SELECT column_name 
FROM information_schema.columns 
WHERE table_schema = 'football_data' 
AND table_name = 'player_keeper_stats'
ORDER BY ordinal_position
"""
columns = execute_query(query)
print("\nColumns in player_keeper_stats table:")
for col in columns['column_name']:
    print(f"  - {col}")

# Check what's in the percentiles
print("\n=== CHECKING GOALKEEPER PERCENTILES ===")
query = """
SELECT 
    p.name,
    pp.percentiles
FROM football_data.player_percentiles_all pp
JOIN football_data.players p ON pp.player_id = p.id
WHERE pp.position_group = 'goalkeeper'
LIMIT 1
"""

result = execute_query(query)
if not result.empty:
    print(f"\nSample Goalkeeper: {result.iloc[0]['name']}")
    
    # Handle both dict and string formats
    percentiles_data = result.iloc[0]['percentiles']
    if isinstance(percentiles_data, str):
        percentiles = json.loads(percentiles_data)
    else:
        percentiles = percentiles_data
    
    print("\nAll percentile columns:")
    keeper_cols = sorted([col for col in percentiles.keys() if col])
    for col in keeper_cols:
        print(f"  - {col}")
    
    # Check for expected columns from position_metrics.py
    print("\n=== CHECKING FOR EXPECTED METRICS ===")
    expected_metrics = {
        'shot_stopping': ['performance_saves', 'performance_savepct', 'performance_sota'],
        'command_of_area': ['crosses_stp', 'crosses_stppct', 'sweeper_avgdist'],
        'distribution': ['launched_cmppct', 'passes_launchpct', 'passes_avglen', 'goal_kicks_avglen'],
        'sweeping': ['sweeper_numopa', 'sweeper_numopa_per_90', 'sweeper_avgdist'],
        'penalty_saving': ['penalty_kicks_pksv', 'penalty_kicks_savepct'],
        'consistency': ['performance_cs', 'performance_cspct', 'performance_ga90']
    }
    
    for metric, cols in expected_metrics.items():
        print(f"\n{metric}:")
        found_any = False
        for col in cols:
            if col in percentiles:
                print(f"  ✅ {col} - FOUND")
                found_any = True
            else:
                print(f"  ❌ {col} - MISSING")
        if not found_any:
            print(f"  ⚠️  NO COLUMNS FOUND FOR {metric}!")