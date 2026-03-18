# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Create necessary directories
RUN mkdir -p /app/data

# Make scripts executable
RUN chmod +x run_migrations.py start.sh

# Expose port
EXPOSE 8000

# Use startup script that runs migrations first
CMD ["./start.sh"]