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
import logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",  # Move docs to /api/v1/docs
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",  # Move redoc to /api/v1/redoc
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

# Define root route FIRST to ensure priority
@app.get("/", include_in_schema=False)
async def root():
    """Serve the frontend landing page"""
    from fastapi.responses import RedirectResponse
    
    # Redirect to the frontend landing page
    return RedirectResponse(url="/frontend/index.html", status_code=302)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount static files for frontend
# Get absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))  # app directory
backend_dir = os.path.dirname(current_dir)  # backend directory  
project_root = os.path.dirname(backend_dir)  # project root
frontend_dir = os.path.join(project_root, "frontend")

print(f"Current dir: {current_dir}")
print(f"Backend dir: {backend_dir}")
print(f"Project root: {project_root}")
print(f"Frontend dir: {frontend_dir}")

# Mount frontend directory at /frontend (this is working)
if os.path.exists(frontend_dir):
    print(f"[OK] Frontend directory found: {frontend_dir}")
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"[ERROR] Frontend directory not found: {frontend_dir}")

# Don't mount root as static files - we'll handle it with a route instead


# ===== LIFECYCLE EVENTS =====

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 60)
    print(f"[START] {settings.PROJECT_NAME} v{settings.VERSION}")
    print("=" * 60)
    
    # Initialize database
    try:
        from app.core.init_db import init_database
        init_database()
        print("  [OK] Database initialized")
    except Exception as e:
        print(f"  [ERROR] Database initialization failed: {e}")
        logger.error(f"Database initialization failed: {e}")
    
    # Run migrations
    try:
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, backend_dir)
        from run_migrations import run_all_migrations
        run_all_migrations()
        print("  [OK] Migrations completed")
    except Exception as e:
        print(f"  [ERROR] Migration failed: {e}")
        logger.error(f"Migration failed: {e}")
    
    # Start scheduler for proactive notifications
    try:
        from app.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        print("  [OK] Scheduler started")
        logger.info("[OK] Scheduler started")
    except ImportError as e:
        print(f"  [WARN] Scheduler not available: {e}")
        logger.warning(f"Scheduler not available: {e}")
    except Exception as e:
        print(f"  [ERROR] Scheduler failed to start: {e}")
        logger.error(f"Scheduler failed to start: {e}")
    
    print("Features:")
    print("  [OK] JWT Authentication")
    print("  [OK] Chat Assistant with LLM")
    print("  [OK] Activity Tracking")
    print("  [OK] Mood Logging")
    print()
    print(f"[DOCS] API Docs: http://localhost:8000{settings.API_V1_PREFIX}/docs")
    print(f"[DOCS] ReDoc: http://localhost:8000{settings.API_V1_PREFIX}/redoc")
    print(f"[WEB] Frontend: http://localhost:8000/login.html")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Application shutting down...")
    
    # Stop scheduler
    try:
        from app.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Scheduler stopped")
    except ImportError:
        logger.info("Scheduler was not available")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty response for favicon requests"""
    return Response(status_code=204)

@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "AI-Enhanced Fitness Coach API is running",
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
