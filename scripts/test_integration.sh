#!/bin/bash

# Docker Integration Testing Script
# This script runs comprehensive integration tests for attest_ai

set -e

echo "🚀 Starting attest_ai Docker Integration Tests"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

# Change to project root
cd "$(dirname "$0")/.."

echo "📋 Pre-test checks:"
echo "  ✅ Docker is running"
echo "  ✅ docker-compose is available"
echo "  ✅ Project root: $(pwd)"

# Create test environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating test environment file..."
    cp .env.example .env
    
    # Update with test values
    sed -i 's/your_master_key_from_docs/test_key_for_integration_testing/' .env
    sed -i 's/"kty":"RSA","e":"AQAB","n":"...","d":"..."/"kty":"RSA","e":"AQAB","n":"test","d":"test"/' .env
    
    echo "  ✅ Test .env file created"
fi

echo ""
echo "🧪 Running Python integration tests..."
echo "======================================"

# Run the Python integration test script
python3 scripts/test_docker_integration.py

echo ""
echo "🎯 Integration testing complete!"