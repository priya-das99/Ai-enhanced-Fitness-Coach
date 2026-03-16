"""
Restart Backend and Run Tests
==============================

This script helps restart the backend server to pick up code changes.
"""

import subprocess
import sys
import time
import os
import signal

print("="*80)
print("BACKEND RESTART HELPER")
print("="*80)
print()

# Step 1: Find and kill existing Python processes running main.py
print("Step 1: Checking for running backend...")
try:
    if sys.platform == "win32":
        # Windows
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
            capture_output=True,
            text=True
        )
        if 'python.exe' in result.stdout:
            print("  Found running Python processes")
            print("  Please manually stop the backend server (Ctrl+C in its window)")
            print("  Then run this script again")
            sys.exit(1)
        else:
            print("  ✓ No backend running")
    else:
        # Unix-like
        result = subprocess.run(
            ['pgrep', '-f', 'main.py'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"  Found {len(pids)} backend process(es)")
            for pid in pids:
                print(f"  Killing PID {pid}...")
                os.kill(int(pid), signal.SIGTERM)
            time.sleep(2)
            print("  ✓ Backend stopped")
        else:
            print("  ✓ No backend running")
except Exception as e:
    print(f"  Warning: Could not check for running processes: {e}")

print()

# Step 2: Clear Python cache
print("Step 2: Clearing Python cache...")
cache_dirs = [
    '__pycache__',
    'chat_assistant/__pycache__',
    'app/__pycache__',
    'app/api/__pycache__',
    'app/services/__pycache__',
]

for cache_dir in cache_dirs:
    if os.path.exists(cache_dir):
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"  ✓ Cleared {cache_dir}")
        except Exception as e:
            print(f"  Warning: Could not clear {cache_dir}: {e}")

print()

# Step 3: Instructions
print("Step 3: Start backend manually")
print("="*80)
print()
print("IMPORTANT: You need to start the backend in a separate terminal:")
print()
print("  cd backend")
print("  python app/main.py")
print()
print("Wait until you see 'Application startup complete'")
print()
print("Then run the test:")
print("  python test_bot_quick.py")
print()
print("="*80)
print()
print("Why manual restart?")
print("- Ensures you can see backend logs")
print("- Easier to stop/restart if needed")
print("- Better for debugging")
print()
