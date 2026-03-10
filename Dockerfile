# Multi-stage build for production deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY index.html .

# Set Python path
ENV PYTHONPATH=/app/backend

# Initialize database and start server
WORKDIR /app/backend
RUN python init_db_complete.py

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]