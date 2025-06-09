from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import pandas as pd
from app.core.config import settings

# Use NullPool to avoid connection issues
engine = create_engine(settings.DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def execute_query(query: str, params: dict = None):
    """Execute a SQL query and return results as DataFrame"""
    # Use text() for SQLAlchemy 1.4 compatibility
    with engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        
        # Convert to DataFrame
        if result.returns_rows:
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        else:
            return pd.DataFrame()