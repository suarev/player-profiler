import psycopg2
import os

# Use PUBLIC URL for local railway run commands
db_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
print(f"Connecting to: {db_url[:50]}...")

conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'football_data'
    ORDER BY table_name
""")
tables = cur.fetchall()
print('Tables in database:')
for t in tables:
    print(f'  - {t[0]}')
    
# Also check row counts
print('\nTable row counts:')
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM football_data.{t[0]}")
    count = cur.fetchone()[0]
    print(f'  - {t[0]}: {count} rows')

conn.close()