# attest_ai Deployment Guide

## 🚀 Quick Deployment Checklist

### 1. Pre-deployment Verification
- [ ] All files present and syntax valid
- [ ] Environment variables configured
- [ ] Docker build successful
- [ ] Health endpoints responding

### 2. Environment Setup
```bash
# Copy and edit environment file
cp .env.template .env

# Required environment variables:
# SECRET_AI_API_KEY=your_secret_ai_master_key
# ARWEAVE_MNEMONIC="your twelve word mnemonic phrase here"
# ARWEAVE_GATEWAY=https://arweave.net
# API_PORT=8000
# DEBUG=false
```

### 3. Local Testing
```bash
# Build Docker image
docker-compose build

# Start application
docker-compose up

# Test health endpoint
curl http://localhost:8000/health

# Test wallet info
curl http://localhost:8000/wallet-info

# Test self-attestation (will fail outside SecretVM)
curl http://localhost:8000/self-attestation

# Open web interface
open http://localhost:8000
```

### 4. SecretVM Deployment

#### Option A: Using SecretVM CLI
```bash
# Login to SecretVM
secretvm-cli auth login -w <your-wallet-address>

# Create VM with docker-compose
secretvm-cli vm create -n "attest-ai-mvp" -t "medium" -d "./docker-compose.yaml"

# Check VM status
secretvm-cli vm ls
secretvm-cli vm status <vmUUID>

# View logs
secretvm-cli vm logs <vmId>

# Get attestation
secretvm-cli vm attestation <vmId>
```

#### Option B: Using Pre-built Image
```bash
# If image is pushed to GHCR
secretvm-cli vm create -n "attest-ai-mvp" -t "medium" -i "ghcr.io/your-org/attest_ai:latest"
```

### 5. Post-deployment Verification

#### Essential Health Checks
```bash
# Replace <vm-ip> with your SecretVM IP
VM_IP=<your-vm-ip>

# 1. Health check
curl http://${VM_IP}:8000/health

# 2. Wallet status
curl http://${VM_IP}:8000/wallet-info

# 3. Self-attestation (should work in SecretVM)
curl http://${VM_IP}:8000/self-attestation

# 4. Web interface
open http://${VM_IP}:8000
```

#### Functional Testing
1. **Open web interface**: `http://<vm-ip>:8000`
2. **Check status cards**: All should show proper status
3. **Send test message**: "Hello attest_ai" with password "test123"
4. **Verify proof generation**: Should create complete proof
5. **Download proof**: JSON file should download
6. **Upload to Arweave**: Should succeed or show graceful mock

## 🔧 Troubleshooting

### Common Issues

#### 1. Dependencies Not Found
```bash
# If external libraries missing, rebuild Docker image
docker-compose build --no-cache
```

#### 2. Environment Variables Not Loading
```bash
# Check .env file format (quotes around mnemonic)
cat .env
source .env && echo "API Key length: ${#SECRET_AI_API_KEY}"
```

#### 3. Self-Attestation Fails
```bash
# Only works in SecretVM - check if localhost:29343 is available
curl http://localhost:29343/cpu.html
```

#### 4. Secret AI Connection Issues
- Verify API key is correct
- Check if Secret AI instances are available
- Application gracefully falls back to mock responses

#### 5. Arweave Upload Issues
- Verify wallet mnemonic is valid
- Check if wallet is funded
- Application gracefully falls back to mock transactions

### Log Analysis
```bash
# View application logs
secretvm-cli vm logs <vmId>

# Look for these indicators:
# "Starting attest_ai on port 8000"
# "Secret AI API Key: Set"
# "Arweave Mnemonic: Set"
```

## 📊 Expected Behavior

### In SecretVM (Production)
- ✅ Self-attestation: Real data from localhost:29343
- ⚠️ Secret AI attestation: Mock (until Secret AI implements)
- ✅ Secret AI chat: Real responses from Secret AI
- ⚠️ Arweave upload: Real or mock (depends on funding)

### Outside SecretVM (Development)
- ❌ Self-attestation: Fails gracefully
- ❌ Secret AI attestation: Mock
- ✅ Secret AI chat: Real responses from Secret AI
- ⚠️ Arweave upload: Mock (no real attestation data)

## 🎯 Success Criteria

### Must Work
- [x] Application starts without errors
- [x] Health endpoint returns 200
- [x] Web interface loads
- [x] Chat generates encrypted proofs
- [x] Proof download works
- [x] All status indicators functional

### Should Work (if properly configured)
- [x] Secret AI integration (with real API key)
- [x] Self-attestation (in SecretVM)
- [x] Arweave uploads (with funded wallet)

### Will Be Added Later
- [ ] Real Secret AI VM attestation (when implemented)

## 🔄 Updating Deployment

### Code Updates
```bash
# 1. Update code
git pull origin main

# 2. Rebuild image
docker-compose build

# 3. Restart VM
secretvm-cli vm stop <vmId>
secretvm-cli vm start <vmId>
```

### Environment Updates
```bash
# 1. Update .env file
vim .env

# 2. Restart application
secretvm-cli vm stop <vmId>
secretvm-cli vm start <vmId>
```

## 📋 Pre-Production Checklist

### Security
- [ ] No secrets in code or logs
- [ ] Environment variables properly loaded
- [ ] HTTPS configured (if needed)
- [ ] Error messages don't leak sensitive info

### Functionality  
- [ ] All endpoints respond correctly
- [ ] Proof generation works end-to-end
- [ ] Download/upload functions work
- [ ] Graceful fallbacks for unavailable services

### Performance
- [ ] Application starts within 30 seconds
- [ ] Chat responses within reasonable time
- [ ] No memory leaks during extended use
- [ ] Proper error handling for network issues

### Documentation
- [ ] README.md complete and accurate
- [ ] Environment variables documented
- [ ] API endpoints documented
- [ ] Troubleshooting guide available

## 🎉 Go Live!

Once all checks pass:
1. ✅ **Application is ready for use**
2. ✅ **Users can create cryptographic proofs**
3. ✅ **System demonstrates core concepts**
4. ✅ **Ready for Secret AI attestation when available**

---

**Need help?** Check the main [README.md](README.md) or implementation guides in the `planning/` directory.