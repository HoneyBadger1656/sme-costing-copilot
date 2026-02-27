FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY Backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY Backend/ ./Backend/

# Set PYTHONPATH to include Backend directory
ENV PYTHONPATH=/app/Backend

# Change to Backend directory
WORKDIR /app/Backend

# Create database if it doesn't exist
RUN python -c "from app.core.database import engine; from app.models.models import Base; Base.metadata.create_all(bind=engine)" || echo "Database creation skipped - will be created on startup"

# Go back to root for script execution
WORKDIR /app

# Expose port
EXPOSE 8000

# Create a startup script with proper bash and correct paths
RUN echo '#!/bin/bash' > start.sh && \
    echo 'set -e' >> start.sh && \
    echo 'PORT=${PORT:-8000}' >> start.sh && \
    echo 'echo "Starting server on port $PORT"' >> start.sh && \
    echo 'export PYTHONPATH=/app/Backend:$PYTHONPATH' >> start.sh && \
    echo 'cd /app/Backend' >> start.sh && \
    echo 'python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT' >> start.sh && \
    chmod +x start.sh

# Start the application
CMD ["./start.sh"]
