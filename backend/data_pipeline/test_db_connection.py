# Create test_db_connection.py
import psycopg2
from config import DATABASE_CONFIG

try:
    conn = psycopg2.connect(**DATABASE_CONFIG)
    print("✅ Database connection successful!")
    
    # Test the schema
    cursor = conn.cursor()
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'football_data'")
    result = cursor.fetchone()
    
    if result:
        print("✅ football_data schema exists!")
    else:
        print("❌ Schema not found - creating it...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS football_data")
        conn.commit()
        print("✅ Schema created!")
    
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")