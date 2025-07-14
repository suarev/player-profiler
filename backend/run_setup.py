import os
import sys
import subprocess
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from sqlalchemy import create_engine, inspect, text
import pandas as pd

# =========================
# 🔌 Step 1: Connect to DB
# =========================
db_url = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")
if not db_url:
    print("❌ No database URL found! Set DATABASE_PUBLIC_URL or DATABASE_URL.")
    sys.exit(1)

print("Connecting to database...")
conn = psycopg2.connect(db_url)
cur = conn.cursor()
print("CONNECTED")

# ================================
# 🏗️ Step 2: Create Schema
# ================================
cur.execute("CREATE SCHEMA IF NOT EXISTS football_data")
conn.commit()
print("✅ Schema created")

# ================================
# 📊 Step 3: Check Existing Tables
# ================================
cur.execute("""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'football_data'
""")
table_count = cur.fetchone()[0]
print(f"📊 Found {table_count} existing tables")
conn.close()

# ================================
# 🕸️ Step 4: Scrape Player Data
# ================================
if table_count == 0:
    print("\n🚀 Starting data scrape...")
    from data_pipeline.scraper import PlayerDataScraper
    scraper = PlayerDataScraper()
    scraper.scrape_and_store_all()
else:
    print("ℹ️  Tables already exist, skipping scraper")

# ======================================
# 📈 Step 5: Compute General Percentiles
# ======================================
print("\n📈 Computing percentiles...")
subprocess.run([sys.executable, "scripts/precompute_percentiles_optimized.py"])

# ===========================================
# 🧠 Step 6: If table exists, run GK script
# ===========================================
print("\n🧠 Checking if goalkeeper recompute is needed...")

engine = create_engine(db_url)

with engine.begin() as conn:
    inspector = inspect(conn)
    has_gk_table = inspector.has_table("player_percentiles_all", schema="football_data")

if has_gk_table:
    print("✅ player_percentiles_all found. Running goalkeeper recompute...")
    subprocess.run([sys.executable, "scripts/recompute_goalkeeper_percentiles.py"])
else:
    print("⚠️ Skipping goalkeeper recompute: player_percentiles_all table not found")

# ===========================================
# 🔍 Step 7: Final row count check
# ===========================================
print("\n🔍 Verifying data presence in players table...")
with engine.begin() as conn:
    try:
        result = conn.execute(text("SELECT COUNT(*) FROM football_data.players"))
        print(f"✅ Total players in DB: {result.scalar()}")
    except Exception as e:
        print(f"❌ Could not check players table: {e}")

print("\n✅ Setup complete!")
