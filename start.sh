#!/bin/bash
set -e

# Start backend
cd Backend
# Example: uvicorn main:app --host 0.0.0.0 --port $PORT
uvicorn main:app --host 0.0.0.0 --port 8000 &
cd ..

# Start frontend
cd Frontend
# Example: npm install && npm run start
npm install
npm run start
chmod +x start.sh
git add start.sh
git commit -m "Add start.sh for Railpack"
git push
