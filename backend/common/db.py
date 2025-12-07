from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import Settings
import logging
import os
import socket
import time
import urllib.parse

Engine = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
Base = declarative_base()

def resolve_ipv4_only(hostname):
    """Force IPv4 resolution and return IPv4 address only"""
    try:
        # Get all addresses for the hostname
        addresses = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if addresses:
            # Return first IPv4 address
            return addresses[0][4][0]
        else:
            # Fallback: try to resolve directly
            return socket.gethostbyname(hostname)
    except Exception as e:
        logging.warning(f"Failed to resolve IPv4 for {hostname}: {e}")
        return None

def force_ipv4_in_url(database_url):
    """Convert database URL to use IPv4 address instead of hostname"""
    try:
        parsed = urllib.parse.urlparse(database_url)
        if parsed.hostname:
            ipv4 = resolve_ipv4_only(parsed.hostname)
            if ipv4:
                # Replace hostname with IPv4 address
                netloc = parsed.netloc.replace(parsed.hostname, ipv4)
                new_url = parsed._replace(netloc=netloc).geturl()
                logging.info(f"Converted {parsed.hostname} to IPv4: {ipv4}")
                return new_url
    except Exception as e:
        logging.warning(f"Failed to force IPv4 in URL: {e}")
    return database_url

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
                
                # Force IPv4 by converting hostname to IPv4 address
                ipv4_connection_string = force_ipv4_in_url(psycopg3_connection_string)
                if ipv4_connection_string != psycopg3_connection_string:
                    logging.info("Using IPv4-forced connection string")
                    psycopg3_connection_string = ipv4_connection_string
                
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
                        # Aggressive IPv4 forcing to avoid IPv6 connectivity issues
                        'target_session_attrs': 'read-write',
                        'load_balance_hosts': 'disable',
                        'sslmode': 'prefer',  # Prefer SSL but allow non-SSL
                        'hostaddr': '',  # Force DNS resolution to avoid IPv6 issues
                        # Additional IPv4-specific settings
                        'keepalives': 1,
                        'keepalives_idle': 30,
                        'keepalives_interval': 10,
                        'keepalives_count': 3,
                        # Disable IPv6 completely
                        'tcp_user_timeout': 10000,
                    }
                )
                
                # Test connection with retry logic and fallback
                max_retries = 3
                retry_delay = 2
                connection_successful = False
                
                for attempt in range(max_retries):
                    try:
                        with Engine.connect() as conn:
                            result = conn.execute(text("SELECT 1"))
                            result.fetchone()
                        logging.info(f"PostgreSQL connection successful on attempt {attempt + 1}")
                        connection_successful = True
                        break
                    except Exception as retry_error:
                        logging.warning(f"Connection attempt {attempt + 1} failed: {retry_error}")
                        
                        # On final attempt, try fallback connection method
                        if attempt == max_retries - 1:
                            logging.info("Trying fallback connection method...")
                            try:
                                # Fallback: create new engine with simpler settings
                                fallback_engine = create_engine(
                                    psycopg3_connection_string,
                                    pool_pre_ping=True,
                                    pool_recycle=300,
                                    echo=False,
                                    pool_size=1,
                                    max_overflow=0,
                                    pool_timeout=10,
                                    connect_args={
                                        'connect_timeout': 5,
                                        'application_name': 'shaaka_app_fallback',
                                        'sslmode': 'disable',  # Disable SSL for fallback
                                    }
                                )
                                with fallback_engine.connect() as conn:
                                    result = conn.execute(text("SELECT 1"))
                                    result.fetchone()
                                logging.info("Fallback connection successful")
                                Engine = fallback_engine  # Use fallback engine
                                connection_successful = True
                                break
                            except Exception as fallback_error:
                                logging.error(f"Fallback connection also failed: {fallback_error}")
                        
                        if attempt < max_retries - 1:
                            logging.info(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                
                if not connection_successful:
                    raise RuntimeError("All connection attempts failed, including fallback")
                
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