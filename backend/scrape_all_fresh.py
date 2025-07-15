# backend/scrape_all_fresh.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_pipeline.scraper import PlayerDataScraper
from data_pipeline.config import FBREF_STAT_TYPES
import psycopg2

def reset_and_scrape():
    """Complete reset and fresh scrape"""
    
    # Step 1: Reset database
    print("🗑️ STEP 1: Resetting database...")
    db_url = os.getenv('DATABASE_PUBLIC_URL')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        cur.execute("DROP SCHEMA IF EXISTS football_data CASCADE")
        cur.execute("CREATE SCHEMA football_data")
        conn.commit()
        print("✅ Database reset complete")
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return
    finally:
        conn.close()
    
    # Step 2: Scrape everything
    print("\n🚀 STEP 2: Scraping ALL data...")
    scraper = PlayerDataScraper()
    scraper.scrape_and_store_all()
    
    # Step 3: Verify what we got
    print("\n🔍 STEP 3: Verifying scraped data...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM football_data.players) as players,
               COUNT(*) as table_count
        FROM information_schema.tables 
        WHERE table_schema = 'football_data'
        GROUP BY table_name
        ORDER BY table_name
    """)
    
    print("\nFinal table inventory:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[2]} rows")
    
    conn.close()

if __name__ == "__main__":
    reset_and_scrape()