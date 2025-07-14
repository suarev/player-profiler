# backend/data_pipeline/scraper.py
import soccerdata as sd
import ScraperFC as sfc
import pandas as pd
from datetime import datetime
import os
import re
from data_pipeline.database import DatabaseManager
from data_pipeline.config import DATABASE_CONFIG, DATABASE_URL, FBREF_STAT_TYPES, LEAGUES, SEASONS

class PlayerDataScraper:
    def __init__(self):
        self.db = DatabaseManager()
        self.fbref = sd.FBref(leagues=LEAGUES, seasons=SEASONS)
        
    def scrape_and_store_all(self):
        """Main function to scrape all data with better error handling"""
        print("🚀 Starting Player Data Scraper...")
        
        # Connect to database
        self.db.connect()
        
        try:
            # First, create players table if not exists
            self._create_players_table()
            
            # Scrape each stat type with individual error handling
            all_players = set()
            for stat_type in FBREF_STAT_TYPES:
                print(f"\n📊 Scraping {stat_type} stats...")
                
                try:
                    # Create a fresh connection for each stat type
                    self.db.close()
                    self.db.connect()
                    
                    players = self._scrape_stat_type(stat_type)
                    if players is not None:
                        all_players.update(players)
                        print(f"✅ {stat_type} completed successfully")
                    else:
                        print(f"⚠️ {stat_type} failed but continuing...")
                        
                except Exception as e:
                    print(f"❌ Error with {stat_type}: {e}")
                    print("🔄 Continuing with next stat type...")
                    continue
            
            print(f"\n✅ Scraping completed! Total unique players: {len(all_players)}")
            
            # Show final table count
            self.db.close()
            self.db.connect()
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'football_data'
            """)
            table_count = cursor.fetchone()[0]
            print(f"📊 Final table count: {table_count}")
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.db.connection.rollback()
        finally:
            self.db.close()

    def _clean_column_name(self, col):
        """Clean column name for PostgreSQL compatibility"""
        # Replace special characters
        clean = col.lower()
        clean = clean.replace(' ', '_')
        clean = clean.replace('-', '_')
        clean = clean.replace('/', '_per_')
        clean = clean.replace('%', 'pct')
        clean = clean.replace('+', 'plus')
        clean = clean.replace('(', '_')
        clean = clean.replace(')', '_')
        clean = clean.replace('.', '_')
        clean = clean.replace(':', '_')
        clean = clean.replace(',', '_')
        clean = clean.replace('#', 'num')  # Add this for keeper_adv stats
        clean = clean.replace('__', '_')  # Remove double underscores
        
        # Remove trailing underscores
        clean = clean.rstrip('_')
        
        # If column starts with a number, prepend 'n_'
        if clean and clean[0].isdigit():
            clean = 'n_' + clean
        
        # PostgreSQL reserved words
        reserved_words = ['user', 'order', 'group', 'table', 'column', 'select', 'from', 'where']
        if clean in reserved_words:
            clean = clean + '_col'
            
        return clean
    
    def _create_players_table(self):
        """Create the main players table"""
        try:
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
        except Exception as e:
            print(f"❌ Error creating players table: {e}")
            self.db.connection.rollback()
    
    def _scrape_stat_type(self, stat_type):
        """Scrape a specific stat type from FBref"""
        try:
            # Skip keeper_adv if keeper fails (they're related)
            if stat_type == 'keeper_adv' and hasattr(self, '_keeper_failed'):
                print(f"⏭️  Skipping {stat_type} due to keeper stats failure")
                return None
                
            # Scrape data
            df = self.fbref.read_player_season_stats(stat_type=stat_type)
            
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join([str(c) for c in col if c]).strip('_') for col in df.columns]
            
            # Reset index to get player names as column
            df = df.reset_index()
            
            # Show what we found
            print(f"✅ Found {len(df)} players with {len(df.columns)} columns")
            print(f"📋 Sample columns: {list(df.columns)[:5]}...")
            
            # Create table name
            table_name = f"player_{stat_type}_stats"
            
            # Store the data
            success = self._store_stat_data(df, table_name, stat_type)
            
            if success:
                # Insert players into main players table
                self._insert_players(df)
                
                # Return player names for tracking
                if 'player' in df.columns:
                    return set(df['player'].unique())
            else:
                if stat_type == 'keeper':
                    self._keeper_failed = True
                return None
            
        except Exception as e:
            print(f"❌ Error scraping {stat_type}: {e}")
            if stat_type == 'keeper':
                self._keeper_failed = True
            return None
    
    def _store_stat_data(self, df, table_name, stat_type):
        """Store stat data in database with proper error handling"""
        try:
            cursor = self.db.connection.cursor()
            
            # First, drop the table if it exists to avoid column conflicts
            cursor.execute(f"DROP TABLE IF EXISTS football_data.{table_name} CASCADE")
            
            # Create a mapping of original to clean column names
            column_mapping = {}
            clean_columns = []
            
            for col in df.columns:
                clean_col = self._clean_column_name(col)
                # Ensure unique column names
                if clean_col in [c[1] for c in clean_columns]:
                    suffix = 2
                    while f"{clean_col}_{suffix}" in [c[1] for c in clean_columns]:
                        suffix += 1
                    clean_col = f"{clean_col}_{suffix}"
                column_mapping[col] = clean_col
                clean_columns.append((col, clean_col))
            
            # Map pandas dtypes to PostgreSQL types
            type_mapping = {
                'int64': 'INTEGER',
                'float64': 'DECIMAL(10,2)',
                'object': 'TEXT',
                'bool': 'BOOLEAN',
                'datetime64[ns]': 'TIMESTAMP'
            }
            
            # Build column definitions
            columns_sql = []
            for orig_col, clean_col in clean_columns:
                pg_type = type_mapping.get(str(df[orig_col].dtype), 'TEXT')
                columns_sql.append(f"{clean_col} {pg_type}")
            
            # Create table SQL
            create_sql = f"""
            CREATE TABLE football_data.{table_name} (
                id SERIAL PRIMARY KEY,
                {', '.join(columns_sql)},
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            print(f"📝 Creating table {table_name}...")
            cursor.execute(create_sql)
            
            # Now insert the data
            print(f"💾 Inserting data into {table_name}...")
            
            # Rename columns in dataframe
            df_copy = df.copy()
            df_copy.columns = [column_mapping[col] for col in df.columns]
            
            # Prepare insert statement
            cols = list(df_copy.columns)
            placeholders = ', '.join(['%s'] * len(cols))
            insert_sql = f"""
                INSERT INTO football_data.{table_name} ({', '.join(cols)})
                VALUES ({placeholders})
            """
            
            # Insert data in batches
            batch_size = 100
            total_rows = len(df_copy)
            
            for i in range(0, total_rows, batch_size):
                batch = df_copy.iloc[i:i+batch_size]
                values = []
                
                for _, row in batch.iterrows():
                    # Convert NaN to None for proper NULL handling
                    row_values = []
                    for val in row.values:
                        if pd.isna(val):
                            row_values.append(None)
                        else:
                            row_values.append(val)
                    values.append(tuple(row_values))
                
                cursor.executemany(insert_sql, values)
                print(f"  ✅ Inserted {min(i+batch_size, total_rows)}/{total_rows} rows", end='\r')
            
            print(f"\n✅ Successfully stored {total_rows} rows in {table_name}")
            self.db.connection.commit()
            
            # Show sample of what was stored
            cursor.execute(f"SELECT * FROM football_data.{table_name} LIMIT 1")
            print(f"📊 Sample columns in table: {[desc[0] for desc in cursor.description][:10]}...")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error storing data in {table_name}: {e}")
            self.db.connection.rollback()
            return False
    
    def _insert_players(self, df):
        """Insert unique players into the players table"""
        if 'player' not in df.columns:
            return
            
        try:
            cursor = self.db.connection.cursor()
            
            # Extract unique player info
            player_cols = ['player', 'team', 'nation', 'pos', 'age']
            # Handle different column name variations
            col_mapping = {
                'player': 'player',
                'team': 'team',
                'nation': 'nation',
                'pos': 'pos',
                'age': 'age'
            }
            
            # Check for variations in column names
            for key in col_mapping:
                if key not in df.columns:
                    # Try with underscore suffix
                    if f"{key}_" in df.columns:
                        col_mapping[key] = f"{key}_"
                    # Try other variations
                    elif key == 'nation' and 'nationality' in df.columns:
                        col_mapping[key] = 'nationality'
                    elif key == 'pos' and 'position' in df.columns:
                        col_mapping[key] = 'position'
            
            available_cols = [col_mapping[col] for col in player_cols if col_mapping[col] in df.columns]
            
            if 'player' in df.columns and available_cols:
                players_df = df[available_cols].drop_duplicates(subset=[col_mapping['player']])
                
                inserted = 0
                for _, row in players_df.iterrows():
                    try:
                        # Prepare values
                        values = {
                            'name': row.get(col_mapping['player'], ''),
                            'team': row.get(col_mapping.get('team', 'team'), ''),
                            'nationality': row.get(col_mapping.get('nation', 'nation'), ''),
                            'position': row.get(col_mapping.get('pos', 'pos'), ''),
                            'age': None
                        }
                        
                        # Handle age conversion
                        age_val = row.get(col_mapping.get('age', 'age'))
                        if pd.notna(age_val):
                            try:
                                values['age'] = int(float(str(age_val)))
                            except:
                                values['age'] = None
                        
                        # Insert or update
                        cursor.execute("""
                        INSERT INTO football_data.players (name, team, nationality, position, age, league)
                        VALUES (%(name)s, %(team)s, %(nationality)s, %(position)s, %(age)s, %(league)s)
                        ON CONFLICT (name) DO UPDATE
                        SET team = EXCLUDED.team,
                            age = EXCLUDED.age,
                            position = EXCLUDED.position
                        """, {**values, 'league': LEAGUES[0]})
                        inserted += 1
                        
                    except Exception as e:
                        print(f"\n⚠️  Error inserting player {row.get(col_mapping['player'], 'Unknown')}: {e}")
                        
                self.db.connection.commit()
                print(f"✅ Inserted/updated {inserted} players in main players table")
                
        except Exception as e:
            print(f"❌ Error in _insert_players: {e}")
            self.db.connection.rollback()
    
    def _scrape_transfermarkt(self):
        """Scrape Transfermarkt data"""
        try:
            print(f"📊 Attempting to scrape Transfermarkt data...")
            
            # Initialize Transfermarkt scraper
            tm = sfc.Transfermarkt()
            
            # According to the documentation, we need to use:
            # tm.scrape_players(year, league)
            # where year is like "23/24" and league is like "EPL"
            
            tm_data = tm.scrape_players("24/25", "EPL")
            
            if tm_data is not None and not tm_data.empty:
                print(f"✅ Found {len(tm_data)} players with market values")
                
                # Store the data
                table_name = "player_market_values"
                success = self._store_transfermarkt_data(tm_data, table_name)
                
                if success:
                    print(f"✅ Transfermarkt data stored successfully")
            else:
                print("⚠️  No Transfermarkt data found")
                
        except Exception as e:
            print(f"❌ Error scraping Transfermarkt: {e}")
            print("💡 Transfermarkt scraping failed - this is optional data, continuing...")
    
    def _store_transfermarkt_data(self, df, table_name):
        """Store Transfermarkt data with proper handling"""
        try:
            cursor = self.db.connection.cursor()
            
            # Drop existing table
            cursor.execute(f"DROP TABLE IF EXISTS football_data.{table_name} CASCADE")
            
            # Clean column names
            column_mapping = {}
            clean_columns = []
            
            for col in df.columns:
                clean_col = self._clean_column_name(col)
                # Ensure unique column names
                if clean_col in [c[1] for c in clean_columns]:
                    suffix = 2
                    while f"{clean_col}_{suffix}" in [c[1] for c in clean_columns]:
                        suffix += 1
                    clean_col = f"{clean_col}_{suffix}"
                column_mapping[col] = clean_col
                clean_columns.append((col, clean_col))
            
            # Create table based on DataFrame
            columns_sql = []
            type_mapping = {
                'int64': 'INTEGER',
                'float64': 'DECIMAL(15,2)',
                'object': 'TEXT',
                'bool': 'BOOLEAN',
                'datetime64[ns]': 'TIMESTAMP'
            }
            
            for orig_col, clean_col in clean_columns:
                pg_type = type_mapping.get(str(df[orig_col].dtype), 'TEXT')
                columns_sql.append(f"{clean_col} {pg_type}")
            
            create_sql = f"""
            CREATE TABLE football_data.{table_name} (
                id SERIAL PRIMARY KEY,
                {', '.join(columns_sql)},
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_sql)
            
            # Insert data
            df_copy = df.copy()
            df_copy.columns = [column_mapping[col] for col in df.columns]
            
            cols = list(df_copy.columns)
            placeholders = ', '.join(['%s'] * len(cols))
            insert_sql = f"""
                INSERT INTO football_data.{table_name} ({', '.join(cols)})
                VALUES ({placeholders})
            """
            
            values = []
            for _, row in df_copy.iterrows():
                row_values = []
                for val in row.values:
                    if pd.isna(val):
                        row_values.append(None)
                    else:
                        row_values.append(val)
                values.append(tuple(row_values))
            
            cursor.executemany(insert_sql, values)
            
            self.db.connection.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error storing Transfermarkt data: {e}")
            self.db.connection.rollback()
            return False

# Run the scraper
if __name__ == "__main__":
    # First, test the connection
    print("🔌 Testing database connection...")
    db = DatabaseManager()
    try:
        db.connect()
        print("✅ Database connection successful!")
        
        # Check if schema exists
        cursor = db.connection.cursor()
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'football_data'")
        if not cursor.fetchone():
            print("📁 Creating football_data schema...")
            cursor.execute("CREATE SCHEMA football_data")
            db.connection.commit()
            print("✅ Schema created!")
        
        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        exit(1)
    
    # Now run the full scraper
    scraper = PlayerDataScraper()
    scraper.scrape_and_store_all()