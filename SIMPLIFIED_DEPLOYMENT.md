# Simplified Deployment Guide

This guide covers the simplified CI/CD process that focuses on building and publishing Docker images to GitHub Container Registry (ghcr.io).

## Overview

The simplified CI/CD pipeline:
- ✅ Automatically builds Docker images on every push to main
- ✅ Publishes images to GitHub Container Registry (ghcr.io)
- ✅ Creates multi-platform images (amd64 and arm64)
- ✅ Generates deployment artifacts (docker-compose.yml)
- ❌ No SecretVM CLI integration
- ❌ No automatic deployment

## GitHub Actions Workflow

The single workflow `build-and-publish.yml` handles everything:

### Triggers
- **Push to main branch** → Builds and publishes image with `main` and `latest` tags
- **Pull requests** → Builds image but doesn't push (for testing)
- **Git tags (v*)** → Builds and publishes with semantic version tags
- **Manual trigger** → Build on demand

### Image Tags

The workflow automatically creates these tags:
- `latest` - Always points to the latest main branch build
- `main` - Latest build from main branch
- `sha-XXXXXXX` - Specific commit builds
- `v1.0.0`, `v1.0`, `v1` - Semantic version tags (when you create git tags)

## Usage

### 1. Enable GitHub Packages

In your repository settings:
1. Go to Settings → Actions → General
2. Under "Workflow permissions", select "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests"

### 2. Build and Publish

The workflow runs automatically on push to main. To manually trigger:
1. Go to Actions tab
2. Select "Build and Publish Docker Image"
3. Click "Run workflow"

### 3. Pull the Image

Once built, pull your image:

```bash
# Latest version
docker pull ghcr.io/YOUR_USERNAME/attest_ai:latest

# Specific version
docker pull ghcr.io/YOUR_USERNAME/attest_ai:v1.0.0

# Specific commit
docker pull ghcr.io/YOUR_USERNAME/attest_ai:sha-abc1234
```

### 4. Deploy Manually

The workflow generates a `docker-compose.deployment.yml` that you can download from the workflow artifacts:

```yaml
version: '3.8'

services:
  attest_ai:
    image: ghcr.io/YOUR_USERNAME/attest_ai:latest
    container_name: attest_ai
    ports:
      - "8000:8000"
    environment:
      - SECRET_AI_API_KEY=${SECRET_AI_API_KEY}
      - ARWEAVE_WALLET_JWK=${ARWEAVE_WALLET_JWK}
      # ... other environment variables
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Manual Deployment Steps

### 1. Prepare Environment

```bash
# Create deployment directory
mkdir attest_ai_deployment
cd attest_ai_deployment

# Create .env file with your credentials
cat > .env << 'EOF'
SECRET_AI_API_KEY=your_actual_api_key
ARWEAVE_WALLET_JWK={"kty":"RSA","e":"AQAB","n":"...","d":"..."}
DEPLOYMENT_ENVIRONMENT=production
SECRETVM_DEPLOYMENT=true
APP_DEBUG=false
LOG_LEVEL=WARNING
EOF
```

### 2. Deploy with Docker Compose

```bash
# Download the docker-compose.deployment.yml from GitHub Actions artifacts
# Or create it manually with the image tag you want

# Pull the latest image
docker pull ghcr.io/YOUR_USERNAME/attest_ai:latest

# Start the service
docker-compose -f docker-compose.deployment.yml up -d

# Check logs
docker-compose logs -f

# Verify health
curl http://localhost:8000/health
```

### 3. Update Deployment

To update to a new version:

```bash
# Pull new image
docker pull ghcr.io/YOUR_USERNAME/attest_ai:latest

# Restart service
docker-compose down
docker-compose -f docker-compose.deployment.yml up -d
```

## Environment Variables

Create a `.env` file with these required variables:

```bash
# Required
SECRET_AI_API_KEY=your_secret_ai_api_key
ARWEAVE_WALLET_JWK={"kty":"RSA",...}  # Full JWK JSON

# Optional (with defaults)
DEPLOYMENT_ENVIRONMENT=production
SECRETVM_DEPLOYMENT=true
APP_DEBUG=false
LOG_LEVEL=WARNING
APP_HOST=0.0.0.0
APP_PORT=8000
CACHE_TTL_SECONDS=300
SECRET_AI_DISCOVERY_CACHE_TTL=3600
ARWEAVE_GATEWAY=https://arweave.net
ENABLE_ARWEAVE_UPLOAD=true
MOCK_UNFUNDED_TRANSACTIONS=true
MAX_MEMORY_MB=1024
MAX_CPU_PERCENT=80
```

## Container Registry Authentication

### Public Images

By default, images are public. Anyone can pull them:
```bash
docker pull ghcr.io/YOUR_USERNAME/attest_ai:latest
```

### Private Images

To make images private:
1. Go to https://github.com/users/YOUR_USERNAME/packages/container/attest_ai/settings
2. Change visibility to "Private"
3. Authenticate to pull:

```bash
# Login to ghcr.io
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Now you can pull private images
docker pull ghcr.io/YOUR_USERNAME/attest_ai:latest
```

## Monitoring

Once deployed, monitor your service:

```bash
# Health check
curl http://localhost:8000/health

# Environment info
curl http://localhost:8000/api/environment/info

# Resource usage
curl http://localhost:8000/api/environment/resources

# View logs
docker logs attest_ai

# Follow logs
docker logs -f attest_ai
```

## Advantages of This Approach

1. **Simplicity**: One workflow, one purpose
2. **Flexibility**: Deploy anywhere Docker runs
3. **Security**: No credentials in CI/CD
4. **Control**: Manual deployment when you're ready
5. **Portability**: Use the same image anywhere

## Migration from Complex CI/CD

If you were using the complex SecretVM deployment workflow:

1. **Remove old workflows**: Delete the complex deployment workflows
2. **Keep only**: `build-and-publish.yml`
3. **Manual deployment**: Use docker-compose locally or on your server
4. **No SecretVM CLI**: Just use standard Docker commands

## Quick Reference

```bash
# Build trigger (automatic on push to main)
git push origin main

# Tag a release
git tag v1.0.0
git push origin v1.0.0

# Pull latest image
docker pull ghcr.io/YOUR_USERNAME/attest_ai:latest

# Run with docker
docker run -d \
  --name attest_ai \
  -p 8000:8000 \
  --env-file .env \
  ghcr.io/YOUR_USERNAME/attest_ai:latest

# Run with docker-compose
docker-compose -f docker-compose.deployment.yml up -d

# Check health
curl http://localhost:8000/health

# View logs
docker logs attest_ai
```

This simplified approach gives you a reliable CI/CD pipeline for building images while maintaining full control over when and where you deploy them.