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
COPY test.db ./test.db

# Create database if it doesn't exist
RUN python -c "from Backend.app.core.database import engine; from Backend.app.models.models import Base; Base.metadata.create_all(bind=engine)"

# Expose port
EXPOSE $PORT

# Start the application
CMD ["python", "-m", "uvicorn", "Backend.app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
