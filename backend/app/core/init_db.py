from app.core.database import engine
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def init_database():
    """Initialize database schema and tables"""
    try:
        with engine.connect() as conn:
            # Create schema
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS football_data"))
            conn.commit()
            
            # Create basic players table
            conn.execute(text("""
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
            """))
            conn.commit()
            
            # Create percentiles table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS football_data.player_percentiles_all (
                    player_id INTEGER PRIMARY KEY,
                    position_group VARCHAR(20),
                    percentiles JSONB,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")