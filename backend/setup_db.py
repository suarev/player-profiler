import os
import psycopg2
from urllib.parse import urlparse

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("No DATABASE_URL found!")
    exit(1)

# Parse the URL
result = urlparse(DATABASE_URL)

# Connect
conn = psycopg2.connect(
    database=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port
)

cursor = conn.cursor()

# Create schema
cursor.execute("CREATE SCHEMA IF NOT EXISTS football_data")
conn.commit()

# Check tables
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'football_data'
""")

tables = cursor.fetchall()
print(f"Found {len(tables)} tables in football_data schema")
for table in tables:
    print(f"  - {table[0]}")

conn.close()