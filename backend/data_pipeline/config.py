# backend/data_pipeline/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'dev_user'),
    'password': os.getenv('DB_PASSWORD', 'dev_password'),
    'database': os.getenv('DB_NAME', 'player_profiler_db')
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
LEAGUES = ["ENG-Premier League"]
SEASONS = ["2024-2025"]  # Current season