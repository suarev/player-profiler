# backend/check_player_data.py
import psycopg2
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
conn = psycopg2.connect(db_url)

# Check Antoine Semenyo's data
print("🔍 Checking Antoine Semenyo's data...")

# 1. Check raw stats
query = """
SELECT 
    p.name,
    s.performance_gls,
    s.performance_ast,
    s.expected_xg,
    sh.standard_sh,
    sh.standard_sot
FROM football_data.players p
LEFT JOIN football_data.player_standard_stats s ON p.name = s.player
LEFT JOIN football_data.player_shooting_stats sh ON p.name = sh.player
WHERE p.name LIKE '%Semenyo%'
"""

df = pd.read_sql(query, conn)
print("\n📊 Raw stats for Semenyo:")
print(df)

# 2. Check his percentiles
query2 = """
SELECT 
    p.name,
    pp.percentiles
FROM football_data.players p
JOIN football_data.player_percentiles_all pp ON p.id = pp.player_id
WHERE p.name LIKE '%Semenyo%'
"""

df2 = pd.read_sql(query2, conn)
if not df2.empty:
    percentiles = json.loads(df2.iloc[0]['percentiles'])
    print("\n📈 Percentiles for Semenyo:")
    print(f"  - performance_gls: {percentiles.get('performance_gls', 'MISSING')}")
    print(f"  - standard_sh: {percentiles.get('standard_sh', 'MISSING')}")
    print(f"  - expected_xg: {percentiles.get('expected_xg', 'MISSING')}")

conn.close()