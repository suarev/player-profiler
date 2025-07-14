import os
import psycopg2

db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
print("🗑️ Clearing database...")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Drop the entire schema and recreate it
cur.execute("DROP SCHEMA IF EXISTS football_data CASCADE")
cur.execute("CREATE SCHEMA football_data")
conn.commit()

print("✅ Database cleared and schema recreated")
conn.close()