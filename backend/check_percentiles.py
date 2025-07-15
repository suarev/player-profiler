import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to database
conn = psycopg2.connect(os.getenv("DATABASE_PUBLIC_URL"))
cur = conn.cursor()

# Check percentile data
cur.execute("""
    SELECT 
        position_group, 
        COUNT(*) as player_count,
        COUNT(CASE WHEN percentiles IS NOT NULL THEN 1 END) as has_percentiles
    FROM football_data.player_percentiles_all
    GROUP BY position_group
""")

print("\n📊 Percentile Data Status:")
print("-" * 50)
for row in cur.fetchall():
    position, total, with_percentiles = row
    print(f"{position}: {with_percentiles}/{total} players have percentiles")

# Check for specific missing metrics
cur.execute("""
    SELECT percentiles::text 
    FROM football_data.player_percentiles_all 
    WHERE position_group = 'defender' 
    LIMIT 1
""")

sample = cur.fetchone()
if sample:
    import json
    percentiles = json.loads(sample[0])
    print(f"\n📋 Sample defender metrics available: {list(percentiles.keys())[:10]}...")
    
    # Check for specific metrics
    missing_metrics = ['discipline', 'box_presence', 'positional_play']
    for metric in missing_metrics:
        found = any(metric in key for key in percentiles.keys())
        print(f"  - {metric}: {'❌ NOT FOUND' if not found else '✅ Found'}")

conn.close()