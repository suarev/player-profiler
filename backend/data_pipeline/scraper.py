# backend/data_pipeline/scraper.py
import soccerdata as sd
import ScraperFC as sfc
import pandas as pd
from datetime import datetime
import os
from database import DatabaseManager
from config import FBREF_STAT_TYPES, LEAGUES, SEASONS

class PlayerDataScraper:
    def __init__(self):
        self.db = DatabaseManager()
        self.fbref = sd.FBref(leagues=LEAGUES, seasons=SEASONS)
        self.transfermarkt = sfc.Transfermarkt()
        
    def scrape_and_store_all(self):
        """Main function to scrape all data"""
        # Connect to database
        self.db.connect()
        
        try:
            # Scrape each stat type from FBref
            for stat_type in FBREF_STAT_TYPES:
                print(f"\n📊 Scraping {stat_type} stats...")
                self._scrape_stat_type(stat_type)
                
            # Scrape Transfermarkt data
            print("\n💰 Scraping Transfermarkt data...")
            self._scrape_transfermarkt()
            
            print("\n✅ All scraping completed!")
            
        finally:
            self.db.close()
    
    def _scrape_stat_type(self, stat_type):
        """Scrape a specific stat type from FBref"""
        try:
            # Skip keeper_adv if keeper fails (they're related)
            if stat_type == 'keeper_adv' and hasattr(self, '_keeper_failed'):
                print(f"Skipping {stat_type} due to keeper stats failure")
                return
                
            # Scrape data
            df = self.fbref.read_player_season_stats(stat_type=stat_type)
            
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns]
            
            # Reset index to get player, team, league, season as columns
            df = df.reset_index()
            
            # Show what we found
            print(f"Found {len(df)} players with {len(df.columns)} columns")
            print(f"Sample columns: {list(df.columns)[:10]}...")
            
            # Create table name
            table_name = f"player_{stat_type}_stats"
            
            # Clean column names for PostgreSQL
            df.columns = [self._clean_column_name(col) for col in df.columns]
            
            # Create table if not exists
            if not self.db.table_exists('football_data', table_name):
                self.db.create_table_from_df(df, table_name)
                print(f"✅ Created table: {table_name}")
            
            # Insert data into table
            self._insert_data(df, table_name)
            
        except Exception as e:
            print(f"❌ Error scraping {stat_type}: {e}")
            if stat_type == 'keeper':
                self._keeper_failed = True
    
    def _clean_column_name(self, col_name):
        """Clean column names for PostgreSQL compatibility"""
        # Replace special characters
        replacements = {
            '+': 'plus',
            '-': '_',
            '/': '_',
            ' ': '_',
            '.': '',
            '%': 'pct',
            '(': '_',
            ')': '_',
            '#': 'num'
        }
        
        clean_name = col_name.lower()
        for old, new in replacements.items():
            clean_name = clean_name.replace(old, new)
        
        # Remove consecutive underscores
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        
        # Remove trailing underscores
        clean_name = clean_name.strip('_')
        
        return clean_name
    
    def _insert_data(self, df, table_name):
        """Insert data into the specified table"""
        cursor = self.db.connection.cursor()
        
        # Get column names
        columns = df.columns.tolist()
        
        # Prepare insert statement
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        insert_sql = f"""
        INSERT INTO football_data.{table_name} ({columns_str})
        VALUES ({placeholders})
        """
        
        # Insert data row by row
        inserted = 0
        for _, row in df.iterrows():
            try:
                values = [row[col] if pd.notna(row[col]) else None for col in columns]
                cursor.execute(insert_sql, values)
                inserted += 1
                
                # Commit every 100 rows
                if inserted % 100 == 0:
                    self.db.connection.commit()
                    print(f"  Inserted {inserted} rows...")
                    
            except Exception as e:
                print(f"  Warning: Could not insert row: {e}")
                self.db.connection.rollback()
        
        # Final commit
        self.db.connection.commit()
        print(f"✅ Inserted {inserted} rows into {table_name}")
    
    def _scrape_transfermarkt(self):
        """Scrape Transfermarkt data"""
        try:
            # Transfermarkt uses different season format
            tm_season = "24/25"  # for 2024-2025 season
            
            print(f"Scraping Transfermarkt data for {tm_season}...")
            tm_data = self.transfermarkt.scrape_players(tm_season, "EPL")
            
            if tm_data is None or len(tm_data) == 0:
                print("❌ No Transfermarkt data found")
                return
                
            print(f"Found {len(tm_data)} players with market values")
            print(f"Columns: {tm_data.columns.tolist()}")
            
            # Clean column names
            tm_data.columns = [self._clean_column_name(col) for col in tm_data.columns]
            
            # Create transfermarkt table
            table_name = "player_market_values"
            
            # Create table if not exists
            if not self.db.table_exists('football_data', table_name):
                self.db.create_table_from_df(tm_data, table_name)
                print(f"✅ Created table: {table_name}")
            
            # Insert data
            self._insert_data(tm_data, table_name)
            
        except Exception as e:
            print(f"❌ Error scraping Transfermarkt: {e}")
            import traceback
            traceback.print_exc()

# Run the scraper
if __name__ == "__main__":
    print("🚀 Starting Player Data Scraper...")
    
    # Test database connection first
    db = DatabaseManager()
    try:
        db.connect()
        print("✅ Database connection successful!")
        
        # Check if schema exists
        cursor = db.connection.cursor()
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'football_data'")
        if not cursor.fetchone():
            print("Creating football_data schema...")
            cursor.execute("CREATE SCHEMA football_data")
            db.connection.commit()
            print("✅ Schema created!")
        
        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        exit(1)
    
    # Run the scraper
    scraper = PlayerDataScraper()
    scraper.scrape_and_store_all()
    
    print("\n🎉 All done!")