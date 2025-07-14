from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import pandas as pd
from app.core.config import settings
import os

# Use Railway's DATABASE_URL directly
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Railway uses postgresql:// but SQLAlchemy needs postgresql+psycopg2://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
else:
    # Fallback for local development
    DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, poolclass=NullPool)
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
    with engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        
        if result.returns_rows:
            return pd.DataFrame(result.fetchall(), columns=result.keys())
        else:
            return pd.DataFrame()