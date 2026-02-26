#!/bin/bash
set -e
echo "Starting Container"

cd Backend
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port "$PORT"
