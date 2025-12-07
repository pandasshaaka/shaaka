#!/usr/bin/env python3
"""
Enhanced database connection test script with IPv4 forcing and retry logic
"""
import sys
import os
import logging
import socket
import time
import urllib.parse

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.config import Settings
from sqlalchemy import create_engine, text

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def resolve_ipv4_only(hostname):
    """Force IPv4 resolution and return IPv4 address only"""
    try:
        logging.info(f"Resolving IPv4 for hostname: {hostname}")
        addresses = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if addresses:
            ipv4 = addresses[0][4][0]
            logging.info(f"Resolved {hostname} to IPv4: {ipv4}")
            return ipv4
        else:
            ipv4 = socket.gethostbyname(hostname)
            logging.info(f"Fallback resolved {hostname} to IPv4: {ipv4}")
            return ipv4
    except Exception as e:
        logging.error(f"Failed to resolve IPv4 for {hostname}: {e}")
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
                logging.info(f"Converted URL from {database_url} to {new_url}")
                return new_url
    except Exception as e:
        logging.error(f"Failed to force IPv4 in URL: {e}")
    return database_url

def test_connection_with_retry(connection_string, max_retries=3, driver_name="unknown"):
    """Test database connection with retry logic"""
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Connection attempt {attempt + 1} of {max_retries} with {driver_name}")
            
            # Create engine with aggressive IPv4 settings
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=True,  # Enable SQL echo for debugging
                pool_size=1,
                max_overflow=0,
                pool_timeout=10,
                connect_args={
                    'connect_timeout': 5,
                    'application_name': 'shaaka_diagnostic',
                    'options': '-c statement_timeout=30000',
                    # Aggressive IPv4 forcing
                    'target_session_attrs': 'read-write',
                    'load_balance_hosts': 'disable',
                    'sslmode': 'require',  # Force SSL for Neon.tech
                    'sslcert': None,       # No client cert required
                    'sslkey': None,        # No client key required
                    'sslrootcert': None,   # Use system CA certs
                    'hostaddr': '',
                    # Additional IPv4-specific settings
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 3,
                    'tcp_user_timeout': 10000,
                }
            )
            
            # Test the connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                value = result.fetchone()[0]
                logging.info(f"✅ Connection successful with {driver_name}! SELECT 1 returned: {value}")
                return True
                
        except Exception as e:
            logging.error(f"❌ Connection attempt {attempt + 1} with {driver_name} failed: {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logging.error(f"All connection attempts with {driver_name} failed")
                return False
    
    return False

def test_fallback_connection(connection_string):
    """Test with minimal fallback settings"""
    try:
        logging.info("Testing fallback connection with minimal settings")
        
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=True,
            pool_size=1,
            max_overflow=0,
            pool_timeout=5,
            connect_args={
                'connect_timeout': 3,
                'application_name': 'shaaka_diagnostic_fallback',
                'sslmode': 'require',  # Keep SSL required for Neon.tech
            }
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.fetchone()[0]
            logging.info(f"✅ Fallback connection successful! SELECT 1 returned: {value}")
            return True
            
    except Exception as e:
        logging.error(f"❌ Fallback connection failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    logging.info("🚀 Starting enhanced database connection diagnostic")
    
    # Load settings
    s = Settings()
    if not s.database_url:
        logging.error("❌ DATABASE_URL not configured")
        return False
    
    original_url = s.database_url
    logging.info(f"Original DATABASE_URL: {original_url}")
    
    # Test multiple drivers with fallback
    drivers_to_test = []
    
    # Check available drivers
    try:
        import psycopg
        drivers_to_test.append(('psycopg3', 'postgresql+psycopg://'))
        logging.info("✅ psycopg3 driver available")
    except ImportError:
        logging.warning("❌ psycopg3 not available")
    
    try:
        import psycopg2
        drivers_to_test.append(('psycopg2', 'postgresql+psycopg2://'))
        logging.info("✅ psycopg2 driver available")
    except ImportError:
        logging.warning("❌ psycopg2 not available")
    
    # Always test with default driver as last resort
    drivers_to_test.append(('default', 'postgresql://'))
    
    for driver_name, driver_prefix in drivers_to_test:
        try:
            # Convert URL for this driver
            if original_url.startswith('postgresql://'):
                test_url = original_url.replace('postgresql://', driver_prefix, 1)
                logging.info(f"Testing {driver_name} connection: {test_url}")
                
                # Test 1: Driver with original settings
                if test_connection_with_retry(test_url, driver_name=driver_name):
                    return True
                
                # Test 2: Force IPv4 by converting hostname to IP
                ipv4_url = force_ipv4_in_url(test_url)
                if ipv4_url != test_url:
                    logging.info(f"Testing {driver_name} IPv4-forced connection: {ipv4_url}")
                    
                    if test_connection_with_retry(ipv4_url, driver_name=driver_name):
                        return True
                
                # Test 3: Fallback with minimal settings
                if test_fallback_connection(test_url):
                    return True
                
                # Test 4: Fallback with IPv4 and minimal settings
                if ipv4_url != test_url:
                    if test_fallback_connection(ipv4_url):
                        return True
                        
        except Exception as e:
            logging.error(f"Driver {driver_name} testing failed: {e}")
            continue
    
    logging.error("❌ All connection tests failed")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)