import os
from dotenv import load_dotenv

load_dotenv()

# Use Railway's database URL if available
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Parse DATABASE_URL to get components
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    
    DATABASE_CONFIG = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path[1:]  # Remove leading /
    }
else:
    # Fallback to individual env vars
    DATABASE_CONFIG = {
        'host': os.getenv('PGHOST', os.getenv('DB_HOST', 'localhost')),
        'port': os.getenv('PGPORT', os.getenv('DB_PORT', '5432')),
        'user': os.getenv('PGUSER', os.getenv('DB_USER', 'postgres')),
        'password': os.getenv('PGPASSWORD', os.getenv('DB_PASSWORD', '')),
        'database': os.getenv('PGDATABASE', os.getenv('DB_NAME', 'railway'))
    }
    
# FBref stat types (from documentation)
FBREF_STAT_TYPES = [
    'standard',
    'keeper',
    'keeper_adv',
    'shooting', 
    'passing',
    'passing_types',
    'goal_shot_creation',
    'defense',
    'possession',
    'playing_time',
    'misc'
]

# Leagues and seasons to scrape
LEAGUES = ["Big 5 European Leagues Combined"]
SEASONS = ["2024-2025"]  # Current season