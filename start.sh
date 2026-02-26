#!/bin/bash
set -e

# Start backend
cd Backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port "$PORT" &
cd ..

# Start frontend
cd Frontend
npm install
npm run start
