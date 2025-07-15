# backend/scrape_missing_tables.py
import asyncio
from scrapers.fbref_scraper import FBrefScraper
import os
from dotenv import load_dotenv

load_dotenv()

async def scrape_missing_tables():
    """Scrape only the 4 missing stat types"""
    scraper = FBrefScraper()
    
    # Only scrape the missing ones
    MISSING_STAT_TYPES = [
        'defense',
        'possession', 
        'playing_time',
        'misc'
    ]
    
    print("🚀 Starting to scrape missing tables...")
    print(f"📊 Will scrape: {MISSING_STAT_TYPES}")
    
    for stat_type in MISSING_STAT_TYPES:
        print(f"\n{'='*50}")
        print(f"📊 Scraping {stat_type} stats...")
        print(f"{'='*50}")
        
        try:
            await scraper.scrape_stat_type(stat_type)
            print(f"✅ Successfully scraped {stat_type} stats!")
        except Exception as e:
            print(f"❌ Error scraping {stat_type}: {e}")
            continue
    
    print("\n🎉 Finished scraping missing tables!")

if __name__ == "__main__":
    asyncio.run(scrape_missing_tables())