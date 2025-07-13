import psycopg2
from psycopg2 import sql
import pandas as pd
from data_pipeline.config import DATABASE_CONFIG, DATABASE_URL, FBREF_STAT_TYPES, LEAGUES, SEASONS

class DatabaseManager:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**DATABASE_CONFIG)
            print("✅ Connected to database")
            return self.connection
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
            
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            
    def table_exists(self, schema, table_name):
        """Check if table exists"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            )
        """, (schema, table_name))
        return cursor.fetchone()[0]
    
    def create_table_from_df(self, df, table_name, schema='football_data'):
        """Automatically create table based on DataFrame columns"""
        cursor = self.connection.cursor()
        
        # Map pandas dtypes to PostgreSQL types
        type_mapping = {
            'int64': 'INTEGER',
            'float64': 'DECIMAL(10,2)',
            'object': 'VARCHAR(255)',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP'
        }
        
        # Build column definitions
        columns = []
        for col in df.columns:
            pg_type = type_mapping.get(str(df[col].dtype), 'TEXT')
            # Clean column name (remove special characters)
            clean_col = col.lower().replace(' ', '_').replace('-', '_').replace('/', '_').replace('%', 'pct')
            columns.append(f"{clean_col} {pg_type}")
        
        # Create table SQL
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
            id SERIAL PRIMARY KEY,
            player_id INTEGER,
            season VARCHAR(20),
            {', '.join(columns)},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES {schema}.players(id)
        )
        """
        
        print(f"Creating table {schema}.{table_name}...")
        cursor.execute(create_sql)
        self.connection.commit()
        print(f"✅ Table {table_name} created successfully")