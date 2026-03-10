#!/usr/bin/env python3
"""
Check if MoodCapture is ready for ngrok demo
"""

import os
import sys
import sqlite3
import subprocess

def check_item(name, condition, fix_hint=""):
    """Check and print status of an item"""
    status = "✅" if condition else "❌"
    print(f"{status} {name}")
    if not condition and fix_hint:
        print(f"   Fix: {fix_hint}")
    return condition

def main():
    print("\n" + "="*60)
    print("🔍 MoodCapture Demo Readiness Check")
    print("="*60 + "\n")
    
    all_good = True
    
    # Check 1: Backend files exist
    print("📁 Backend Files:")
    backend_exists = os.path.exists("backend/app/main.py")
    all_good &= check_item(
        "Backend code exists",
        backend_exists,
        "Make sure you're in the MoodCapture directory"
    )
    
    # Check 2: Database exists
    print("\n💾 Database:")
    db_exists = os.path.exists("backend/mood_capture.db")
    all_good &= check_item(
        "Database file exists",
        db_exists,
        "Run: python backend/init_db_complete.py"
    )
    
    if db_exists:
        # Check demo user
        try:
            conn = sqlite3.connect('backend/mood_capture.db')
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE username = 'demo'")
            demo_user = cursor.fetchone()
            conn.close()
            
            all_good &= check_item(
                "Demo user exists",
                demo_user is not None,
                "Run: python backend/create_demo_user.py"
            )
        except Exception as e:
            all_good &= check_item(
                "Demo user exists",
                False,
                f"Database error: {e}"
            )
    
    # Check 3: Dependencies
    print("\n📦 Dependencies:")
    try:
        import fastapi
        all_good &= check_item("FastAPI installed", True)
    except ImportError:
        all_good &= check_item(
            "FastAPI installed",
            False,
            "Run: pip install -r requirements.txt"
        )
    
    try:
        import openai
        all_good &= check_item("OpenAI installed", True)
    except ImportError:
        all_good &= check_item(
            "OpenAI installed",
            False,
            "Run: pip install openai"
        )
    
    # Check 4: Environment
    print("\n🔑 Environment:")
    env_exists = os.path.exists("backend/.env")
    all_good &= check_item(
        ".env file exists",
        env_exists,
        "Copy backend/.env.example to backend/.env"
    )
    
    if env_exists:
        with open("backend/.env", "r") as f:
            env_content = f.read()
            has_openai_key = "OPENAI_API_KEY" in env_content and "sk-" in env_content
            check_item(
                "OpenAI API key configured",
                has_openai_key,
                "Add your OpenAI API key to backend/.env"
            )
    
    # Check 5: ngrok
    print("\n🌐 ngrok:")
    try:
        result = subprocess.run(
            ["where", "ngrok"] if sys.platform == "win32" else ["which", "ngrok"],
            capture_output=True,
            text=True
        )
        ngrok_installed = result.returncode == 0
        all_good &= check_item(
            "ngrok installed",
            ngrok_installed,
            "Download from https://ngrok.com/download"
        )
    except Exception:
        all_good &= check_item(
            "ngrok installed",
            False,
            "Download from https://ngrok.com/download"
        )
    
    # Check 6: Server running
    print("\n🚀 Server Status:")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        server_running = response.status_code == 200
        check_item(
            "Backend server running",
            server_running,
            "Run: python backend/start_no_reload.py"
        )
    except Exception:
        check_item(
            "Backend server running",
            False,
            "Run: python backend/start_no_reload.py"
        )
    
    # Summary
    print("\n" + "="*60)
    if all_good:
        print("✅ ALL CHECKS PASSED! Ready for ngrok demo!")
        print("\nNext steps:")
        print("1. Start backend: python backend/start_no_reload.py")
        print("2. Start ngrok: ngrok http 8000")
        print("3. Share the ngrok URL!")
    else:
        print("⚠️  Some issues found. Fix them and run this check again.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
