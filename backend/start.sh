#!/bin/bash
# Startup script for production deployment

echo "🚀 Starting MoodCapture Backend..."

# Run migrations first
echo "📦 Running database migrations..."
python run_migrations.py

# Check if migrations succeeded
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migrations failed"
    exit 1
fi

# Start the application
echo "🌟 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}