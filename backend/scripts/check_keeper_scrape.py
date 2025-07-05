# backend/scripts/check_keeper_scrape.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import execute_query

print("=== CHECKING KEEPER ADVANCED STATS ===")

# Check if we have the keeper_adv table
query = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'football_data' 
AND table_name LIKE '%keeper%'
ORDER BY table_name
"""
tables = execute_query(query)
print("\nKeeper-related tables:")
for table in tables['table_name']:
    print(f"  - {table}")

# Check if keeper_adv table exists and has data
query = """
SELECT COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'football_data' 
AND table_name = 'player_keeper_adv_stats'
"""
result = execute_query(query)
if result.iloc[0]['count'] > 0:
    print("\n✅ player_keeper_adv_stats table EXISTS")
    
    # Check columns
    query = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'football_data' 
    AND table_name = 'player_keeper_adv_stats'
    ORDER BY ordinal_position
    """
    columns = execute_query(query)
    print("\nColumns in player_keeper_adv_stats:")
    for col in columns['column_name'][:20]:  # Show first 20
        print(f"  - {col}")
    
    # Check if it has data
    query = "SELECT COUNT(*) as count FROM football_data.player_keeper_adv_stats"
    count = execute_query(query)
    print(f"\nRows in keeper_adv table: {count.iloc[0]['count']}")
else:
    print("\n❌ player_keeper_adv_stats table NOT FOUND")
    print("\nThis table should contain:")
    print("  - crosses_stp, crosses_stppct")
    print("  - sweeper_numopa, sweeper_avgdist")
    print("  - launched_cmppct, passes_avglen")
    print("  - etc.")

# Check a sample keeper's data across tables
print("\n=== SAMPLE KEEPER DATA CHECK ===")
query = """
SELECT 
    p.name,
    CASE WHEN k.player IS NOT NULL THEN '✅' ELSE '❌' END as has_basic_stats,
    CASE WHEN ka.player IS NOT NULL THEN '✅' ELSE '❌' END as has_adv_stats
FROM football_data.players p
LEFT JOIN football_data.player_keeper_stats k ON p.name = k.player
LEFT JOIN football_data.player_keeper_adv_stats ka ON p.name = ka.player
WHERE p.position LIKE '%GK%'
LIMIT 5
"""
try:
    keepers = execute_query(query)
    print("\nSample goalkeepers:")
    print(keepers)
except:
    print("Could not check keeper data - keeper_adv table might not exist")