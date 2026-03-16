@echo off
echo ================================================================================
echo RESTARTING BACKEND SERVER
echo ================================================================================
echo.

echo Step 1: Stopping any running Python processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main.py*" 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__
if exist chat_assistant\__pycache__ rmdir /s /q chat_assistant\__pycache__
if exist app\__pycache__ rmdir /s /q app\__pycache__

echo Step 3: Starting backend server...
echo.
echo Backend will start in a new window...
echo Close this window when you see "Application startup complete"
echo.
start "MoodCapture Backend" cmd /k "python app/main.py"

echo.
echo ================================================================================
echo BACKEND RESTART INITIATED
echo ================================================================================
echo.
echo Wait 5 seconds for server to start, then run:
echo   python test_bot_quick.py
echo.
pause
