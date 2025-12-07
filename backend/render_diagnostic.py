#!/usr/bin/env python3
"""
Render Deployment Diagnostic Script
Tests database connection and provides detailed error reporting
"""

import os
import sys
import logging
import traceback
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_connection():
    """Test database connection with detailed diagnostics"""
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logging.error("❌ DATABASE_URL environment variable is not set")
        logging.info("Please ensure DATABASE_URL is configured in your Render environment variables")
        return False
    
    logging.info(f"Testing connection with DATABASE_URL: {database_url[:50]}...")
    
    try:
        # Test basic connection
        logging.info("Creating engine...")
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=True,
            connect_args={
                'connect_timeout': 10,
                'application_name': 'shaaka_diagnostic',
                'sslmode': 'require',  # Force SSL for Neon.tech
            }
        )
        
        logging.info("Testing connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.fetchone()[0]
            logging.info(f"✅ Connection successful! SELECT 1 returned: {value}")
            
            # Test more complex query
            logging.info("Testing more complex query...")
            result = conn.execute(text("SELECT current_database(), current_user, version()"))
            db_info = result.fetchone()
            logging.info(f"Database: {db_info[0]}, User: {db_info[1]}")
            logging.info(f"PostgreSQL Version: {db_info[2][:60]}...")
            
            return True
            
    except SQLAlchemyError as e:
        logging.error(f"❌ Database connection failed: {e}")
        logging.error(f"Error type: {type(e).__name__}")
        
        # Provide specific guidance based on error type
        if "ssl" in str(e).lower():
            logging.info("💡 SSL-related error detected. Ensure sslmode is set correctly for your database provider.")
        elif "connection" in str(e).lower():
            logging.info("💡 Connection error detected. Check your DATABASE_URL format and network connectivity.")
        elif "authentication" in str(e).lower():
            logging.info("💡 Authentication error detected. Verify your database credentials.")
        
        return False
        
    except Exception as e:
        logging.error(f"❌ Unexpected error: {e}")
        logging.error(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment configuration"""
    logging.info("=== Environment Diagnostic ===")
    
    # Check Python version
    logging.info(f"Python version: {sys.version}")
    
    # Check environment variables
    env_vars = ['DATABASE_URL', 'JWT_SECRET', 'JWT_ALGORITHM']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var == 'DATABASE_URL':
                logging.info(f"{var}: {'*' * min(20, len(value))} (length: {len(value)})")
            else:
                logging.info(f"{var}: {value}")
        else:
            logging.warning(f"{var}: Not set")
    
    # Check for common database drivers
    drivers = ['psycopg', 'psycopg2', 'psycopg2-binary']
    for driver in drivers:
        try:
            __import__(driver)
            logging.info(f"✅ {driver} is available")
        except ImportError:
            logging.info(f"❌ {driver} is not available")

if __name__ == "__main__":
    logging.info("🚀 Starting Render Deployment Diagnostic")
    
    # Test environment
    test_environment()
    
    # Test database connection
    logging.info("\n=== Database Connection Test ===")
    success = test_connection()
    
    if success:
        logging.info("\n✅ All tests passed! Database connection is working.")
    else:
        logging.info("\n❌ Database connection failed. Please check the error messages above.")
        
    logging.info("\n=== Recommendations ===")
    logging.info("1. Ensure DATABASE_URL is set in Render environment variables")
    logging.info("2. For Neon.tech: Use sslmode=require in connection string")
    logging.info("3. Check database provider's SSL requirements")
    logging.info("4. Verify network connectivity to database host")