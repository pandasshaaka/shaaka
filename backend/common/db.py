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
                # Convert to psycopg3 driver for Python 3.13 compatibility
                # Replace postgresql:// with postgresql+psycopg://
                psycopg3_connection_string = connection_string.replace('postgresql://', 'postgresql+psycopg://', 1)
                
                Engine = create_engine(
                    psycopg3_connection_string,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,  # Reduced from default 30 to 15 seconds
                    connect_args={
                        'connect_timeout': 10,  # Connection timeout in seconds
                        'application_name': 'shaaka_app',
                        'options': '-c statement_timeout=30000',  # 30 second statement timeout
                        # Force IPv4 to avoid IPv6 connectivity issues
                        'target_session_attrs': 'read-write',
                        'load_balance_hosts': 'disable',
                        'sslmode': 'prefer',  # Prefer SSL but allow non-SSL
                        'hostaddr': '',  # Force DNS resolution to avoid IPv6 issues
                    }
                )
                
                # Test connection
                with Engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                
                logging.info("PostgreSQL connection successful")
                
                # Create tables if they don't exist
                Base.metadata.create_all(bind=Engine)
                logging.info("Database tables ensured")
                
                # Run profile photo migration
                from .migrations import run_profile_photo_migration
                run_profile_photo_migration(SessionLocal())
                
            else:
                raise ValueError("Invalid database URL format - must be postgresql://")
                
        except Exception as e:
            logging.error(f"PostgreSQL connection failed: {e}")
            error_msg = str(e)
            
            # Provide more specific error messages for common issues
            if "Network is unreachable" in error_msg:
                raise RuntimeError(
                    "Database connection failed: Network is unreachable. "
                    "This may be due to IPv6 connectivity issues. "
                    "Please ensure your database URL uses an IPv4 address or is accessible from your network."
                )
            elif "connection timeout" in error_msg.lower():
                raise RuntimeError(
                    "Database connection failed: Connection timeout. "
                    "The database server may be unreachable or overloaded. "
                    "Please check your database URL and network connectivity."
                )
            elif "refused" in error_msg.lower():
                raise RuntimeError(
                    "Database connection failed: Connection refused. "
                    "Please ensure your database server is running and accessible."
                )
            else:
                raise RuntimeError(f"Failed to connect to PostgreSQL database: {e}")
        
        SessionLocal.configure(bind=Engine)