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
            # Force PostgreSQL connection with fallback driver support
            connection_string = s.database_url
            if connection_string.startswith('postgresql://'):
                # Try psycopg3 first, fallback to psycopg2 if not available
                engines_to_try = []
                
                # Try psycopg3 (Python 3.13+ compatible)
                try:
                    import psycopg
                    psycopg3_connection_string = connection_string.replace('postgresql://', 'postgresql+psycopg://', 1)
                    engines_to_try.append(('psycopg3', psycopg3_connection_string))
                    logging.info("psycopg3 driver available")
                except ImportError:
                    logging.warning("psycopg3 not available, will try fallback drivers")
                
                # Try psycopg2 (widely available)
                try:
                    import psycopg2
                    psycopg2_connection_string = connection_string.replace('postgresql://', 'postgresql+psycopg2://', 1)
                    engines_to_try.append(('psycopg2', psycopg2_connection_string))
                    logging.info("psycopg2 driver available")
                except ImportError:
                    logging.warning("psycopg2 not available")
                
                # If no specific drivers available, use default postgresql driver
                if not engines_to_try:
                    engines_to_try.append(('default', connection_string))
                    logging.info("Using default PostgreSQL driver")
                
                # Try each engine in order
                connection_successful = False
                last_error = None
                
                for driver_name, test_connection_string in engines_to_try:
                    try:
                        # Force IPv4 by converting hostname to IPv4 address
                        ipv4_connection_string = force_ipv4_in_url(test_connection_string)
                        if ipv4_connection_string != test_connection_string:
                            logging.info(f"Using IPv4-forced connection string with {driver_name}")
                            test_connection_string = ipv4_connection_string
                        
                        logging.info(f"Testing connection with {driver_name} driver")
                        
                        Engine = create_engine(
                            test_connection_string,
                            pool_pre_ping=True,
                            pool_recycle=300,
                            echo=False,
                            pool_size=5,
                            max_overflow=10,
                            pool_timeout=30,
                            connect_args={
                                'connect_timeout': 10,
                                'application_name': 'shaaka_app',
                                'options': '-c statement_timeout=30000',
                                'target_session_attrs': 'read-write',
                                'load_balance_hosts': 'disable',
                                'sslmode': 'require',  # Force SSL for Neon.tech
                                'sslcert': None,       # No client cert required
                                'sslkey': None,        # No client key required
                                'sslrootcert': None,   # Use system CA certs
                                'hostaddr': '',
                                'keepalives': 1,
                                'keepalives_idle': 30,
                                'keepalives_interval': 10,
                                'keepalives_count': 3,
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
                                logging.info(f"PostgreSQL connection successful with {driver_name} on attempt {attempt + 1}")
                                connection_successful = True
                                break
                            except Exception as retry_error:
                                logging.warning(f"Connection attempt {attempt + 1} with {driver_name} failed: {retry_error}")
                                
                                # On final attempt, try fallback connection method
                                if attempt == max_retries - 1:
                                    logging.info(f"Trying fallback connection method with {driver_name}...")
                                    try:
                                        # Fallback: create new engine with simpler settings but keep SSL
                                        fallback_engine = create_engine(
                                            test_connection_string,
                                            pool_pre_ping=True,
                                            pool_recycle=300,
                                            echo=False,
                                            pool_size=1,
                                            max_overflow=0,
                                            pool_timeout=10,
                                            connect_args={
                                                'connect_timeout': 5,
                                                'application_name': 'shaaka_app_fallback',
                                                'sslmode': 'require',  # Keep SSL required for Neon.tech
                                            }
                                        )
                                        with fallback_engine.connect() as conn:
                                            result = conn.execute(text("SELECT 1"))
                                            result.fetchone()
                                        logging.info(f"Fallback connection with {driver_name} successful")
                                        Engine = fallback_engine  # Use fallback engine
                                        connection_successful = True
                                        break
                                    except Exception as fallback_error:
                                        logging.error(f"Fallback connection with {driver_name} also failed: {fallback_error}")
                                        last_error = fallback_error
                                
                                if attempt < max_retries - 1:
                                    logging.info(f"Retrying in {retry_delay} seconds...")
                                    time.sleep(retry_delay)
                                    retry_delay *= 2  # Exponential backoff
                        
                        if connection_successful:
                            break
                        else:
                            # Try next driver
                            logging.warning(f"Driver {driver_name} failed, trying next driver...")
                            continue
                            
                    except Exception as driver_error:
                        logging.error(f"Driver {driver_name} failed: {driver_error}")
                        last_error = driver_error
                        continue
                
                if not connection_successful and last_error:
                    raise last_error
                
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