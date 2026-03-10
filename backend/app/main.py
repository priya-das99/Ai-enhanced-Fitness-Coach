# app/main.py
# FastAPI application entry point

import sys
import os

# Add backend directory to path if running directly
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.router import api_router
from app.config import settings
from app.scheduler import start_scheduler, stop_scheduler
import logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Configure CORS - Allow all origins for demo (ngrok compatibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for ngrok demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount static files for frontend
frontend_dir = os.path.join(os.path.dirname(backend_dir), "frontend")
root_dir = os.path.dirname(backend_dir)

# Serve root index.html
if os.path.exists(os.path.join(root_dir, "index.html")):
    app.mount("/", StaticFiles(directory=root_dir, html=True), name="root")

# Also serve frontend directory
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# ===== LIFECYCLE EVENTS =====

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION}")
    print("=" * 60)
    
    # Initialize database
    try:
        from app.core.init_db import init_database
        init_database()
        print("  ✅ Database initialized")
    except Exception as e:
        print(f"  ❌ Database initialization failed: {e}")
        logger.error(f"Database initialization failed: {e}")
    
    # Start scheduler for proactive notifications
    try:
        start_scheduler()
        print("  ✅ Scheduler started")
        logger.info("✅ Scheduler started")
    except Exception as e:
        print(f"  ❌ Scheduler failed to start: {e}")
        logger.error(f"Scheduler failed to start: {e}")
    
    print("Features:")
    print("  ✅ JWT Authentication")
    print("  ✅ Chat Assistant with LLM")
    print("  ✅ Activity Tracking")
    print("  ✅ Mood Logging")
    print()
    print(f"📚 API Docs: http://localhost:8000{settings.API_V1_PREFIX}/docs")
    print(f"📖 ReDoc: http://localhost:8000{settings.API_V1_PREFIX}/redoc")
    print(f"🌐 Frontend: http://localhost:8000/login.html")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("👋 Application shutting down...")
    
    # Stop scheduler
    try:
        stop_scheduler()
        logger.info("❌ Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty response for favicon requests"""
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
