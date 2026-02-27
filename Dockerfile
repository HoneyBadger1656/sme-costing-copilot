# Multi-stage build for production
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Backend stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY Backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY Backend/ ./Backend/

# Copy built frontend
COPY --from=frontend-build /app/frontend/out ./frontend/static
COPY --from=frontend-build /app/frontend/public ./frontend/static

# Set PYTHONPATH to include Backend directory
ENV PYTHONPATH=/app/Backend

# Change to Backend directory for database operations
WORKDIR /app/Backend

# Create database if it doesn't exist
RUN python -c "from app.core.database import engine; from app.models.models import Base; Base.metadata.create_all(bind=engine)" || echo "Database creation skipped - will be created on startup"

# Go back to root for script execution
WORKDIR /app

# Expose port
EXPOSE 8000

# Create a production startup script
RUN echo '#!/bin/bash' > start.sh && \
    echo 'set -e' >> start.sh && \
    echo 'PORT=${PORT:-8000}' >> start.sh && \
    echo 'echo "Starting SME Costing Copilot on port $PORT"' >> start.sh && \
    echo 'export PYTHONPATH=/app/Backend:$PYTHONPATH' >> start.sh && \
    echo 'export DATABASE_URL=${DATABASE_URL:-"sqlite:///app.db"}' >> start.sh && \
    echo 'cd /app/Backend' >> start.sh && \
    echo 'python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1' >> start.sh && \
    chmod +x start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start the application
CMD ["./start.sh"]
