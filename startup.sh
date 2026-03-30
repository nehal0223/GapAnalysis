#!/bin/bash
# Azure Web App startup script for FastAPI application

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start the FastAPI application
python -m uvicorn api:app --host 0.0.0.0 --port 8000
