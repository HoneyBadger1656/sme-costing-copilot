#!/bin/bash
set -e
echo "Starting Container"

cd Backend

# Use python to run pip
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
