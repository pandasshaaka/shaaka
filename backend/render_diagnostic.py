#!/usr/bin/env python3
"""
Render Deployment Diagnostic Tool
Helps diagnose and fix common database connection issues on Render
"""

import os
import sys
import logging
from urllib.parse import urlparse

def check_database_url():
    """Check if DATABASE_URL is properly configured"""
    database_url = os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        print("   Please set DATABASE_URL in your Render environment variables")
        return False
    
    print(f"✅ DATABASE_URL found: {database_url[:50]}...")
    
    # Parse the URL to check for common issues
    try:
        parsed = urlparse(database_url)
        
        if parsed.scheme not in ['postgresql', 'postgres']:
            print(f"❌ ERROR: Invalid database scheme: {parsed.scheme}")
            print("   Expected: postgresql:// or postgres://")
            return False
        
        if not parsed.hostname:
            print("❌ ERROR: No hostname found in DATABASE_URL")
            return False
        
        # Check for IPv6 addresses which can cause connectivity issues
        if ':' in parsed.hostname and not parsed.hostname.startswith('['):
            print(f"⚠️  WARNING: IPv6 address detected: {parsed.hostname}")
            print("   This may cause connectivity issues on some networks")
            print("   Consider using IPv4 address or hostname instead")
        
        print(f"✅ Hostname: {parsed.hostname}")
        print(f"✅ Port: {parsed.port or 5432}")
        print(f"✅ Database: {parsed.path[1:] if parsed.path else 'Not specified'}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to parse DATABASE_URL: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        from common.db import ensure_engine
        from sqlalchemy import text
        
        print("🔍 Testing database connection...")
        engine = ensure_engine()
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection test failed")
                return False
                
    except ImportError as e:
        print(f"❌ ERROR: Failed to import required modules: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Database connection failed: {e}")
        
        # Provide specific guidance based on error type
        error_msg = str(e).lower()
        if "network is unreachable" in error_msg:
            print("\n💡 SUGGESTION: This is likely an IPv6 connectivity issue")
            print("   Try these solutions:")
            print("   1. Use an IPv4 address instead of IPv6")
            print("   2. Check if your database provider supports IPv4")
            print("   3. Contact your database provider about IPv6 support")
        elif "connection refused" in error_msg:
            print("\n💡 SUGGESTION: Connection refused")
            print("   1. Verify the database server is running")
            print("   2. Check firewall settings")
            print("   3. Verify the connection details are correct")
        elif "timeout" in error_msg:
            print("\n💡 SUGGESTION: Connection timeout")
            print("   1. Check network connectivity")
            print("   2. Verify database server is accessible")
            print("   3. Consider increasing timeout values")
        
        return False

def suggest_render_fixes():
    """Suggest fixes for Render deployment"""
    print("\n🔧 RENDER DEPLOYMENT FIXES:")
    print("1. Update render.yaml to include database service:")
    print("   Add this to your render.yaml:")
    print("""
   databases:
     - name: shaaka-db
       databaseName: shaaka
       user: shaaka
       plan: starter
""")
    print("\n2. Update your web service to depend on the database:")
    print("   Add to your web service section:")
    print("""
   envVars:
     - key: DATABASE_URL
       fromDatabase:
         name: shaaka-db
         property: connectionString
""")
    print("\n3. Alternative: Use external database service")
    print("   Set DATABASE_URL environment variable manually in Render dashboard")

def main():
    """Main diagnostic function"""
    print("🚀 Render Database Diagnostic Tool")
    print("=" * 50)
    
    # Check environment
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"DATABASE_URL present: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")
    print()
    
    # Run diagnostics
    url_ok = check_database_url()
    
    if url_ok:
        conn_ok = test_connection()
        
        if not conn_ok:
            suggest_render_fixes()
    
    print("\n" + "=" * 50)
    if url_ok and 'conn_ok' in locals() and conn_ok:
        print("✅ All diagnostics passed!")
        return 0
    else:
        print("❌ Some diagnostics failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Add backend to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    exit(main())