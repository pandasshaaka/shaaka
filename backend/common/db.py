from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import Settings
import logging
import os

Engine = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
Base = declarative_base()

def ensure_engine():
    global Engine
    if Engine is None:
        s = Settings()
        if not s.database_url:
            raise RuntimeError("DATABASE_URL not configured")
        
        try:
            # Force PostgreSQL connection using psycopg3
            connection_string = s.database_url
            if connection_string.startswith('postgresql://'):
                # Use psycopg3 driver for Python 3.13 compatibility
                Engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False,
                    pool_size=5,
                    max_overflow=10
                )
                
                # Test connection
                with Engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                
                logging.info("PostgreSQL connection successful")
                
                # Create tables if they don't exist
                Base.metadata.create_all(bind=Engine)
                logging.info("Database tables ensured")
                
            else:
                raise ValueError("Invalid database URL format - must be postgresql://")
                
        except Exception as e:
            logging.error(f"PostgreSQL connection failed: {e}")
            # Don't fallback to SQLite - we want to use Neon PostgreSQL
            raise RuntimeError(f"Failed to connect to PostgreSQL database: {e}")
        
        SessionLocal.configure(bind=Engine)