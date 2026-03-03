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

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount static files for frontend
frontend_dir = os.path.join(os.path.dirname(backend_dir), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty response for favicon requests"""
    return Response(status_code=204)

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION}")
    print("=" * 60)
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
    print("Shutting down Chat Assistant API...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
