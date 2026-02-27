FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY Backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY Backend/ ./Backend/

# Create database if it doesn't exist
RUN python -c "import sys; sys.path.append('./Backend'); from app.core.database import engine; from app.models.models import Base; Base.metadata.create_all(bind=engine)" || echo "Database creation skipped - will be created on startup"

# Expose port
EXPOSE $PORT

# Start the application
CMD ["python", "-m", "uvicorn", "Backend.app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
