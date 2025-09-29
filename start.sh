#!/bin/bash
# Render.com startup script for KMRL Backend

echo "🚀 Starting KMRL Backend..."
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Navigate to Backend directory
cd Backend

echo "Installing requirements..."
pip install -r requirements.txt

echo "Starting uvicorn server..."
python -m uvicorn app.demo_main:app --host 0.0.0.0 --port $PORT