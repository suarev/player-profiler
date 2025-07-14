import os
import sys
import subprocess
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting COMPLETE setup from scratch...")

# =========================
# 🗑️ Step 1: Reset Database
# =========================
import psycopg2

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ No database URL found!")
    sys.exit(1)

print("🗑️ Resetting database...")
conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("DROP SCHEMA IF EXISTS football_data CASCADE")
cur.execute("CREATE SCHEMA football_data")
conn.commit()
conn.close()
print("✅ Database reset complete")

# ================================
# 🕸️ Step 2: Fresh Scrape
# ================================
print("\n🚀 Starting fresh scrape of ALL data...")
from data_pipeline.scraper import PlayerDataScraper
scraper = PlayerDataScraper()
scraper.scrape_and_store_all()

# ================================
# 📈 Step 3: Compute Percentiles
# ================================
print("\n📈 Computing percentiles...")
subprocess.run([sys.executable, "scripts/precompute_percentiles_optimized.py"])

print("\n✅ COMPLETE setup finished!")