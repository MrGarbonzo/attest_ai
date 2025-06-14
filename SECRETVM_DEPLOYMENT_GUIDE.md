# SecretVM Deployment Guide

Complete guide for deploying attest_ai to SecretVM trusted execution environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Preparation](#environment-preparation)
3. [Deployment Process](#deployment-process)
4. [Validation & Testing](#validation--testing)
5. [Monitoring & Management](#monitoring--management)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

## Prerequisites

### SecretVM CLI Setup

1. **Install SecretVM CLI**:
   ```bash
   # Follow the latest installation guide from Secret Network
   curl -sSL https://get.scrt.network/secretvm-cli | bash
   ```

2. **Authenticate with SecretVM**:
   ```bash
   secretvm-cli auth login -w <your_wallet_address>
   ```

3. **Verify authentication**:
   ```bash
   secretvm-cli auth status
   ```

### Local Environment

1. **Required tools**:
   - Docker and Docker Compose
   - Python 3.9+ (for testing scripts)
   - jq (for JSON processing)
   - curl (for health checks)

2. **Install dependencies**:
   ```bash
   pip install httpx asyncio pydantic psutil
   ```

## Environment Preparation

### 1. Create Production Environment File

```bash
# Copy the production template
cp .env.production.example .env.production

# Edit with your actual credentials
nano .env.production
```

### 2. Configure Required Credentials

#### Secret AI Configuration
```bash
# Get your master API key from Secret Network documentation
SECRET_AI_API_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1
```

#### Arweave Configuration
```bash
# Use JWK format wallet (not mnemonic phrase)
# Generate at: https://arweave.app/wallet
ARWEAVE_WALLET_JWK={"kty":"RSA","e":"AQAB","n":"..."}
```

#### SecretVM-Specific Settings
```bash
# Production environment flags
DEPLOYMENT_ENVIRONMENT=production
SECRETVM_DEPLOYMENT=true
APP_DEBUG=false

# Resource constraints for SecretVM
MAX_MEMORY_MB=1024
MAX_CPU_PERCENT=80
```

### 3. Validate Configuration

```bash
# Test configuration locally first
python -c "from src.config import get_settings; get_settings().validate_environment()"
```

## Deployment Process

### Automated Deployment (Recommended)

```bash
# Run the automated deployment script
./scripts/deploy_secretvm.sh

# The script will:
# 1. Check prerequisites
# 2. Validate environment configuration
# 3. Create SecretVM instance
# 4. Upload encrypted environment file
# 5. Deploy application container
# 6. Run validation tests
# 7. Display management information
```

### Manual Deployment Steps

#### 1. Create SecretVM Instance

```bash
# Create VM with medium resources
secretvm-cli vm create \
  -n "attest-ai-mvp" \
  -t "medium" \
  -d "./docker-compose.yaml" \
  --wait-for-ready
```

#### 2. Upload Environment Configuration

```bash
# Get VM ID from creation output
VM_ID="<vm_id_from_creation>"

# Upload encrypted environment file
secretvm-cli vm upload-env "$VM_ID" ".env.production"
```

#### 3. Monitor Deployment

```bash
# Check deployment status
secretvm-cli vm status "$VM_ID"

# View logs if needed
secretvm-cli vm logs "$VM_ID" --tail 50
```

#### 4. Get VM URL

```bash
# Extract VM URL
VM_URL=$(secretvm-cli vm status "$VM_ID" --format json | jq -r '.url')
echo "Application URL: ${VM_URL}:8000"
```

## Validation & Testing

### 1. Basic Health Check

```bash
# Check health endpoint
curl "${VM_URL}:8000/health" | jq

# Expected response:
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "self_attestation": {"available": true},
    "secret_ai": {"status": "available"},
    "arweave": {"initialized": true, "funded": true}
  },
  "environment": {
    "type": "SecretVM",
    "is_secretvm": true,
    "confidence_score": 0.95
  }
}
```

### 2. Run Validation Scripts

#### SecretVM-Specific Validation
```bash
# Run SecretVM deployment validation
python3 scripts/test_secretvm_deployment.py --vm-url "$VM_URL"

# Expected output:
# ✅ PASS: secretvm_environment_detection
# ✅ PASS: real_self_attestation  
# ✅ PASS: complete_workflow_secretvm
```

#### Health Validation
```bash
# Run comprehensive health validation
python3 scripts/health_validator.py --vm-url "$VM_URL" --strict

# For production, use strict mode
python3 scripts/health_validator.py --vm-url "$VM_URL" --strict --save-results validation_results.json
```

#### Post-Deployment Test Suite
```bash
# Run complete test suite
python3 scripts/post_deployment_test_suite.py --vm-url "$VM_URL" --extended

# Save results for analysis
python3 scripts/post_deployment_test_suite.py --vm-url "$VM_URL" --extended --save-results test_results.json
```

### 3. Functional Testing

#### Test Chat Workflow
```bash
# Test complete chat workflow with dual attestation
curl -X POST "${VM_URL}:8000/api/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello SecretVM!", "upload_proof": true}' | jq
```

#### Test Self-Attestation
```bash
# Verify real attestation data
curl "${VM_URL}:8000/api/attestation/self" | jq

# Should return SecretVM attestation registers
# Look for mr_td, rtmr0-3, report_data fields
```

#### Test Proof Verification
```bash
# Get validation schema
curl "${VM_URL}:8000/api/proofs/validation-schema" | jq

# Test proof verification
curl -X POST "${VM_URL}:8000/api/proofs/verify" \
  -H "Content-Type: application/json" \
  -d '{"proof_data": {...}, "strict_mode": false}' | jq
```

## Monitoring & Management

### 1. Continuous Monitoring

```bash
# Start continuous monitoring (runs every 60 seconds)
python3 scripts/monitor_secretvm_deployment.py --vm-url "$VM_URL" --interval 60

# Single health check
python3 scripts/monitor_secretvm_deployment.py --vm-url "$VM_URL" --single-check

# Save monitoring history
python3 scripts/monitor_secretvm_deployment.py --vm-url "$VM_URL" --save-metrics monitoring_history.json
```

### 2. Performance Monitoring

#### Key Metrics to Monitor
- **Response Times**: Health endpoint < 2s, API endpoints < 5s
- **Availability**: Self-attestation service must be available
- **Resource Usage**: Memory < 80%, CPU < 90%
- **Error Rates**: < 5% for critical operations

#### Monitoring Endpoints
```bash
# Environment detection and optimization
curl "${VM_URL}:8000/api/environment/info" | jq
curl "${VM_URL}:8000/api/environment/resources" | jq
curl "${VM_URL}:8000/api/environment/health/detailed" | jq

# Service health
curl "${VM_URL}:8000/health" | jq
curl "${VM_URL}:8000/api/attestation/status" | jq
curl "${VM_URL}:8000/api/secretai/health" | jq
curl "${VM_URL}:8000/api/arweave/status" | jq
```

### 3. VM Management Commands

```bash
# Check VM status
secretvm-cli vm status "$VM_ID"

# View logs
secretvm-cli vm logs "$VM_ID" --tail 100

# Restart VM
secretvm-cli vm restart "$VM_ID"

# Stop VM
secretvm-cli vm stop "$VM_ID"

# Delete VM (WARNING: Irreversible)
secretvm-cli vm delete "$VM_ID"
```

### 4. Environment Optimization

```bash
# Refresh environment detection
curl -X POST "${VM_URL}:8000/api/environment/refresh" | jq

# Get current optimization settings
curl "${VM_URL}:8000/api/environment/optimization" | jq

# Check SecretVM detection details
curl "${VM_URL}:8000/api/environment/secretvm/detection" | jq
```

## Troubleshooting

### Common Issues

#### 1. Self-Attestation Not Available
```bash
# Check if attestation endpoint is accessible
curl "${VM_URL}:8000/api/attestation/status"

# Verify SecretVM attestation endpoint
curl "http://localhost:29343/cpu.html" # (from within VM)

# Check environment detection
curl "${VM_URL}:8000/api/environment/secretvm/detection"
```

#### 2. High Resource Usage
```bash
# Check resource constraints
curl "${VM_URL}:8000/api/environment/resources"

# View detailed system information
python3 scripts/health_validator.py --vm-url "$VM_URL" --save-results resource_check.json
```

#### 3. Service Unavailability
```bash
# Check individual service health
curl "${VM_URL}:8000/api/secretai/health"
curl "${VM_URL}:8000/api/arweave/status"

# View application logs
secretvm-cli vm logs "$VM_ID" --tail 50
```

#### 4. Network Connectivity Issues
```bash
# Test external connectivity from VM
curl "${VM_URL}:8000/api/environment/health/detailed"

# Check network characteristics
python3 scripts/test_secretvm_deployment.py --vm-url "$VM_URL"
```

### Debugging Commands

```bash
# Get comprehensive environment report
curl "${VM_URL}:8000/api/environment/report" | jq > environment_report.json

# Run full validation with detailed output
python3 scripts/health_validator.py --vm-url "$VM_URL" --strict --save-results debug_validation.json

# Monitor resource usage over time
python3 scripts/monitor_secretvm_deployment.py --vm-url "$VM_URL" --interval 30 --save-metrics debug_monitoring.json
```

### Log Analysis

```bash
# Search for errors in logs
secretvm-cli vm logs "$VM_ID" | grep -i error

# Look for attestation issues
secretvm-cli vm logs "$VM_ID" | grep -i attestation

# Check startup sequence
secretvm-cli vm logs "$VM_ID" --since 10m | head -50
```

## Security Considerations

### 1. Credential Management

- **Never commit `.env.production` to version control**
- **Use SecretVM's encrypted environment upload**: `secretvm-cli vm upload-env`
- **Rotate credentials regularly**: Update API keys and wallet keys periodically
- **Monitor for credential exposure**: Check logs for any credential leaks

### 2. Network Security

- **Restricted external access**: SecretVM environments may have limited outbound connectivity
- **Attestation endpoint security**: localhost:29343 is only accessible within the VM
- **API endpoint protection**: Consider rate limiting and authentication for production

### 3. Data Security

- **Proof data encryption**: All proof data includes cryptographic attestations
- **Wallet security**: Arweave wallet keys are encrypted at rest in SecretVM
- **Attestation integrity**: Real attestation data cannot be forged

### 4. Monitoring Security

- **No sensitive data in logs**: Ensure no credentials appear in application logs
- **Secure monitoring endpoints**: Protect `/api/environment/*` endpoints in production
- **Regular security audits**: Review monitoring data for security anomalies

### 5. Production Hardening

```bash
# Verify security settings in production environment
grep -E "(DEBUG|LOG_LEVEL|CORS)" .env.production

# Expected production values:
APP_DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=<specific_origins>
ENABLE_SECURITY_HEADERS=true
```

## Success Criteria

### Deployment Success Indicators

✅ **Health Check Passing**: `/health` returns status "healthy"  
✅ **Self-Attestation Working**: Real attestation data available  
✅ **Environment Detection**: SecretVM detected with >0.8 confidence  
✅ **Service Integration**: Secret AI and/or Arweave services accessible  
✅ **Performance Acceptable**: Response times <5s, resource usage <80%  
✅ **Validation Tests**: >80% test pass rate with no critical failures  

### Production Readiness Checklist

- [ ] All validation scripts pass
- [ ] Monitoring endpoints accessible
- [ ] Resource usage within limits
- [ ] Real attestation data captured
- [ ] Error handling functional
- [ ] Security settings applied
- [ ] Documentation complete
- [ ] Management procedures tested

## Support and Resources

### Documentation Links
- [SecretVM CLI Documentation](https://docs.scrt.network/secret-network-documentation/development/tools-and-libraries/secret-vm-cli)
- [Secret AI SDK Documentation](https://docs.scrt.network/secret-network-documentation/development/tools-and-libraries/secret-ai-sdk)
- [Arweave Developer Documentation](https://docs.arweave.org/)

### Monitoring Tools
- `scripts/monitor_secretvm_deployment.py` - Continuous monitoring
- `scripts/health_validator.py` - Health validation
- `scripts/post_deployment_test_suite.py` - Comprehensive testing

### Management Commands
```bash
# Quick status check
curl "${VM_URL}:8000/health" | jq '.status'

# Resource usage check  
curl "${VM_URL}:8000/api/environment/resources" | jq '.status'

# Environment type verification
curl "${VM_URL}:8000/api/environment/info" | jq '.environment_type'
```

---

**Note**: This deployment guide assumes a production SecretVM environment. For development and testing, refer to the standard Docker deployment instructions in the main README.md.