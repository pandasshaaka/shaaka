from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
import os

# Add the backend directory to Python path for proper imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth.router import router as auth_router
from services.user.router import router as user_router
from services.files.router import router as files_router
import logging
import os

#
logging.basicConfig(level=logging.INFO)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"]
)
app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/user")
app.include_router(files_router, prefix="/files")

# Create uploads directory if it doesn't exist
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/files/static", StaticFiles(directory=uploads_dir), name="files-static")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify database connectivity"""
    try:
        from common.db import ensure_engine
        from sqlalchemy import text
        
        # Try to get database engine
        engine = ensure_engine()
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            db_status = "connected" if result.fetchone() else "disconnected"
        
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": "2024-12-07T12:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": "2024-12-07T12:00:00Z"
        }

# Global exception handler for database connection errors
@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    """Handle runtime errors including database connection failures"""
    if "database" in str(exc).lower() or "connection" in str(exc).lower():
        return {
            "detail": "Database connection failed. Please try again later.",
            "error": str(exc),
            "suggestion": "The database may be temporarily unavailable. Please contact support if this persists."
        }, 503  # Service Unavailable
    
    # Re-raise other runtime errors
    raise exc