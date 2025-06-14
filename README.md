# attest_ai

Cryptographic proof generation for AI interactions in SecretVM's trusted execution environment.

## Overview

attest_ai generates cryptographic proofs of AI interactions by:
- **Dual Attestation**: Captures attestation data from TWO VMs (Secret AI VM + attest_ai VM)
- **Chat Integration**: Links AI conversations to cryptographic VM attestations
- **Arweave Storage**: Stores proof metadata on Arweave blockchain with smart mock logic
- **Web Interface**: Provides complete workflow demonstration with side-by-side attestation display

## Features (Phase 3 Complete - Production Ready!)

✅ **Self-Attestation**: Always-available VM attestation with comprehensive error handling  
✅ **Secret AI Integration**: Discovery, health checks, chat with robust retry logic  
✅ **Arweave Blockchain**: Smart upload with cost estimation and balance checking  
✅ **Enhanced UI**: Tabbed interface, loading states, progress bars, real-time feedback  
✅ **Proof Verification**: Cryptographic validation system with integrity checking  
✅ **Error Handling**: Comprehensive exception system with user-friendly messages  
✅ **Docker Integration**: Production-ready containerization with health checks  
✅ **Testing Suite**: Complete integration testing for deployment validation  

## Quick Start

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   # - SECRET_AI_API_KEY (from Secret AI docs)
   # - ARWEAVE_WALLET_JWK (JWK format wallet)
   ```

2. **Deploy with Docker**:
   ```bash
   docker-compose up --build
   ```

3. **Access Application**: http://localhost:8000

## Usage

### Enhanced Web Interface (Phase 3)
1. **Attestations Tab**: Dual VM attestations with real-time updates and error handling
2. **Chat & Proof Tab**: AI conversations with progress tracking and auto-verification
3. **Proof Verification Tab**: Cryptographic validation with detailed reporting
4. **Service Status Tab**: Comprehensive system monitoring and diagnostics

### API Workflow
```bash
# Check service health
curl http://localhost:8000/health

# Get self-attestation
curl http://localhost:8000/api/attestation/self

# Discover Secret AI instances
curl http://localhost:8000/api/secretai/instances

# Send chat with dual attestation
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello AI", "upload_proof": true}'

# Check Arweave status
curl http://localhost:8000/api/arweave/status
```

## API Endpoints

### Core Endpoints
- `GET /` - Web UI with dual attestation display
- `GET /health` - Service health check
- `GET /api` - API documentation

### Attestation
- `GET /api/attestation/self` - Self-attestation data
- `GET /api/attestation/status` - Attestation service status

### Chat & AI
- `POST /api/chat/` - Send message with dual attestation capture
- `GET /api/secretai/instances` - Discover Secret AI instances
- `GET /api/secretai/health` - Secret AI service health

### Arweave
- `GET /api/arweave/status` - Wallet status and funding
- `POST /api/arweave/upload` - Manual proof upload
- `POST /api/arweave/estimate-cost` - Upload cost estimation

### Proof Verification (New in Phase 3)
- `POST /api/proofs/verify` - Verify cryptographic proof integrity
- `GET /api/proofs/validation-schema` - Get proof validation requirements
- `GET /api/proofs/stats` - Verification system statistics

## Testing & Validation

### Integration Testing
```bash
# Run comprehensive Docker integration tests
./scripts/test_integration.sh

# Manual testing
python3 scripts/test_docker_integration.py
```

### Deployment Validation
```bash
# Validate environment configuration
python -c "from src.config import get_settings; get_settings().validate_environment()"

# Test all API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/proofs/validation-schema
```

## Smart Mock Strategy

- **Self-Attestation**: ✅ Always real (localhost:29343 available in SecretVM)
- **Secret AI**: 🔄 Mock when instances unavailable
- **Arweave Upload**: 🔄 Real if funded, mock if unfunded

## Development

### Local Setup
```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --reload
```

### Testing
```bash
pytest tests/
```

### Environment Variables

Key variables (see `.env.example`):
```bash
SECRET_AI_API_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1
ARWEAVE_WALLET_JWK={"kty":"RSA","e":"AQAB",...}
ENABLE_ARWEAVE_UPLOAD=true
MOCK_UNFUNDED_TRANSACTIONS=true
```

## Security

- All sensitive data in `.env` (never committed)
- Environment validation on startup
- Secure wallet handling with JWK format
- No hardcoded secrets in code

## Deployment

Ready for SecretVM deployment with single `docker-compose.yaml`:
- Health checks for monitoring
- Persistent volumes for templates/static
- Network configuration for attestation access
- Environment-based configuration