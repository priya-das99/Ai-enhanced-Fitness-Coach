#!/usr/bin/env python
"""
Startup script WITHOUT auto-reload (Windows-friendly)
Run from backend directory: python start_no_reload.py
"""

import sys
import os

# Ensure we're in the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# Add backend to Python path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    print("=" * 60)
    print("[START] Starting FastAPI Chat Assistant (No Auto-Reload)")
    print("=" * 60)
    print(f"Working directory: {current_dir}")
    print()

    try:
        import uvicorn
        
        # Run WITHOUT reload to avoid Windows multiprocessing issues
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disabled for Windows compatibility
            log_level="info"
        )
    except ImportError as e:
        print("[ERROR] Missing dependencies")
        print(f"   {e}")
        print()
        print("Please install requirements:")
        print("   pip install -r requirements-fastapi.txt")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
