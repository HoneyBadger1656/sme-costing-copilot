#!/bin/bash
set -e

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r Backend/requirements.txt

# Start the backend server
cd Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
