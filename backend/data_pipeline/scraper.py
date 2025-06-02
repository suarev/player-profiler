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
            # First, create players table if not exists
            self._create_players_table()
            
            # Scrape each stat type from FBref
            all_players = set()
            for stat_type in FBREF_STAT_TYPES:
                print(f"\n📊 Scraping {stat_type} stats...")
                players = self._scrape_stat_type(stat_type)
                if players is not None:
                    all_players.update(players)
                
            # Scrape Transfermarkt data
            print("\n💰 Scraping Transfermarkt data...")
            self._scrape_transfermarkt()
            
            print("\n✅ All scraping completed!")
            
        finally:
            self.db.close()
    
    def _create_players_table(self):
        """Create the main players table"""
        cursor = self.db.connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS football_data.players (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            position VARCHAR(50),
            age INTEGER,
            nationality VARCHAR(100),
            team VARCHAR(255),
            league VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.db.connection.commit()
        print("✅ Players table ready")
    
    def _scrape_stat_type(self, stat_type):
        """Scrape a specific stat type from FBref"""
        try:
            # Skip keeper_adv if keeper fails (they're related)
            if stat_type == 'keeper_adv' and hasattr(self, '_keeper_failed'):
                print(f"Skipping {stat_type} due to keeper stats failure")
                return None
                
            # Scrape data
            df = self.fbref.read_player_season_stats(stat_type=stat_type)
            
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns]
            
            # Reset index to get player names as column
            df = df.reset_index()

            #Replacing + with 'plus' because it causes errors
            df.columns = [col.lower().replace(' ', '_').replace('+', 'plus').replace('-', '_') for col in df.columns]

            df.columns = [f"{stat_type}_{col}" if col in ["season", "league", "team"] else col for col in df.columns]


            # Show what we found
            print(f"Found {len(df)} players with {len(df.columns)} columns")
            print(f"Sample columns: {list(df.columns)[:5]}...")
            
            # Create table name
            table_name = f"player_{stat_type}_stats"
            
            # Create table if not exists
            if not self.db.table_exists('football_data', table_name):
                self.db.create_table_from_df(df, table_name)
            
            # Insert players into main players table
            self._insert_players(df)
            
            # Return player names for tracking
            if 'player' in df.columns:
                return set(df['player'].unique())
            
        except Exception as e:
            print(f"❌ Error scraping {stat_type}: {e}")
            if stat_type == 'keeper':
                self._keeper_failed = True
            return None
    
    def _insert_players(self, df):
        """Insert unique players into the players table"""
        if 'player' not in df.columns:
            return
            
        cursor = self.db.connection.cursor()
        
        # Extract unique player info
        player_cols = ['player', 'team', 'nation', 'pos', 'age']
        available_cols = [col for col in player_cols if col in df.columns]
        
        if available_cols:
            players_df = df[available_cols].drop_duplicates(subset=['player'])
            
            for _, row in players_df.iterrows():
                try:
                    # Prepare values
                    values = {
                        'name': row.get('player', ''),
                        'team': row.get('team', ''),
                        'nationality': row.get('nation', ''),
                        'position': row.get('pos', ''),
                        'age': row.get('age', None)
                    }
                    
                    # Insert or update
                    cursor.execute("""
                    INSERT INTO football_data.players (name, team, nationality, position, age, league)
                    VALUES (%(name)s, %(team)s, %(nationality)s, %(position)s, %(age)s, %(league)s)
                    ON CONFLICT (name) DO UPDATE
                    SET team = EXCLUDED.team,
                        age = EXCLUDED.age
                    """, {**values, 'league': LEAGUES[0]})
                    
                except Exception as e:
                    print(f"Error inserting player {row.get('player', 'Unknown')}: {e}")
                    
        self.db.connection.commit()
    
    def _scrape_transfermarkt(self):
        """Scrape Transfermarkt data"""
        try:
            # Scrape current season data
            # Transfermarkt uses different season format (e.g., "24/25")
            tm_season = "24/25"  # for 2024-2025 season
            
            print(f"Scraping Transfermarkt data for {tm_season}...")
            tm_data = self.transfermarkt.scrape_players(tm_season, "EPL")
            
            print(f"Found {len(tm_data)} players with market values")
            
            # Create transfermarkt table
            table_name = "player_market_values"
            if not self.db.table_exists('football_data', table_name):
                # Clean column names for PostgreSQL
                tm_data.columns = [col.lower().replace(' ', '_') for col in tm_data.columns]
                self.db.create_table_from_df(tm_data, table_name)
            
            # TODO: Insert data into table
            
        except Exception as e:
            print(f"❌ Error scraping Transfermarkt: {e}")

# Test the scraper
if __name__ == "__main__":
    # First, test the connection
    print("Testing database connection...")
    db = DatabaseManager()
    try:
        db.connect()
        print("✅ Database connection successful!")
        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        exit(1)
    
    # Now run the scraper
    scraper = PlayerDataScraper()
    
    # Test with just one stat type first
    scraper.db.connect()
    scraper._create_players_table()
    scraper._scrape_stat_type('standard')
    scraper.db.close()