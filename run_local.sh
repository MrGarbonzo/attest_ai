#!/bin/bash
# Local development startup script

echo "Starting Attest AI MVP in local development mode..."

# Check if .env exists, if not copy from template
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.template .env
    echo "Please update .env with your Secret AI API key if available"
fi

# Create necessary directories
mkdir -p downloads logs static templates

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting FastAPI application..."
export PYTHONPATH=$PWD
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload