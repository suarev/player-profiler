import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# First create schema
import psycopg2

# Use DATABASE_URL, not DATABASE_PUBLIC_URL when running from Railway
db_url = os.getenv('DATABASE_PUBLIC_URL')
if not db_url:
    print("❌ No DATABASE_URL found! Make sure you're linked to the backend service.")
    sys.exit(1)

print(f"Connecting to database...")
conn = psycopg2.connect(db_url)
cur = conn.cursor()
print("CONNECTED")
cur.execute('CREATE SCHEMA IF NOT EXISTS football_data')
conn.commit()
print("✅ Schema created")

# Check if tables exist
cur.execute("""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'football_data'
""")
table_count = cur.fetchone()[0]
print(f"📊 Found {table_count} existing tables")

conn.close()

# Now run scraper
if table_count == 0:
    print("\n🚀 Starting data scrape...")
    from data_pipeline.scraper import PlayerDataScraper
    scraper = PlayerDataScraper()
    scraper.scrape_and_store_all()
else:
    print("ℹ️  Tables already exist, skipping scraper")

# Run percentiles
print("\n📈 Computing percentiles...")
import subprocess
subprocess.run([sys.executable, "scripts/precompute_percentiles_optimized.py"])
subprocess.run([sys.executable, "scripts/recompute_goalkeeper_percentiles.py"])

print("\n✅ Setup complete!")