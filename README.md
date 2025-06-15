# attest_ai MVP

**Cryptographic attestation proofs for Secret AI conversations in SecretVM**

This is a minimal viable product that demonstrates how to create verifiable proofs of AI conversations by combining Secret AI chat with VM attestation technology and storing encrypted proofs on Arweave.

## 🎯 Project Overview

attest_ai creates cryptographic proofs that demonstrate:
- **Real AI conversations** happened with Secret AI
- **Secure execution** in verified SecretVM environments
- **Tamper-proof storage** on Arweave with user-controlled encryption
- **Verifiable attestation** from both VMs (attest_ai + Secret AI)

## ✨ Key Features

- 🤖 **Real Secret AI Integration** - Chat with actual Secret AI models
- 🛡️ **Dual VM Attestation** - Self-attestation + Secret AI attestation  
- 🔐 **User-Controlled Encryption** - Password-based conversation privacy
- 🌐 **Arweave Storage** - Permanent, verifiable proof storage
- 📱 **Simple Web UI** - Clean interface showing all components
- 🐳 **Docker Deployment** - Single docker-compose.yaml for SecretVM

## 🚀 Quick Start

### Prerequisites
- SecretVM environment (for production)
- Docker and docker-compose
- Secret AI API key
- Arweave wallet mnemonic (optional - will use mock if unfunded)

### Local Development

1. **Clone and setup**
   ```bash
   git clone <repository>
   cd attest_ai
   ```

2. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env with your real values:
   # - SECRET_AI_API_KEY: Your Secret AI master key
   # - ARWEAVE_MNEMONIC: Your 12-word Arweave wallet mnemonic
   ```

3. **Run with Docker**
   ```bash
   docker-compose build
   docker-compose up
   ```

4. **Test the application**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Open web interface
   open http://localhost:8000
   ```

## 🏗️ Architecture

```
┌─── User Browser ───┐
│  Chat Interface    │
│  + Encryption UI   │
└───────────────────┘
           │
           ▼
┌─── attest_ai VM ───┐    ┌─── Secret AI VM ───┐
│  FastAPI App      │◄──►│  LLM Service       │
│  Self-Attestation │    │  Remote Attestation│
│  Arweave Client   │    └────────────────────┘
└───────────────────┘
           │
           ▼
┌─── Arweave Network ─┐
│  Encrypted Proofs   │
│  Public Verification│
└────────────────────┘
```

## 🔧 Implementation Status

### ✅ Completed Features
- [x] FastAPI backend with health check
- [x] Secret AI integration (with graceful mock fallback)
- [x] Self-attestation from localhost:29343
- [x] Password-based conversation encryption
- [x] Arweave upload (with mock fallback for unfunded wallets)
- [x] Web UI with real-time status indicators
- [x] Proof generation and download
- [x] Docker deployment setup
- [x] GitHub Actions for image building

### 🔄 In Progress
- [ ] **Secret AI attestation** - Currently mocked (Secret AI team adding this feature)
- [ ] Complete end-to-end testing in SecretVM

### 🎯 Future Enhancements
- [ ] Secret Network integration for enhanced encryption
- [ ] Real-time Secret AI VM attestation (when available)
- [ ] Proof verification tools
- [ ] Batch operations
- [ ] Enhanced UI/UX

## 📁 Project Structure

```
attest_ai/
├── app.py                  # Main FastAPI application
├── secret_ai_client.py     # Secret AI integration
├── arweave_client.py       # Arweave upload/wallet
├── attestation_client.py   # Self-attestation from VM
├── encryption.py           # Password-based encryption
├── requirements.txt        
├── Dockerfile
├── docker-compose.yaml
├── .env.template
├── .gitignore
├── static/
│   ├── index.html          # Chat UI
│   ├── style.css           # Basic styling
│   └── script.js           # Frontend logic
└── .github/workflows/
    └── build-image.yml     # Docker image building
```

## 🔐 Security Model

- **Conversation Privacy**: User password encrypts actual chat content
- **Proof Integrity**: Cryptographic hashes prevent tampering
- **VM Attestation**: Proves code ran in secure environments
- **End-to-End Verification**: Complete chain from input to storage

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/health` | GET | System health check |
| `/wallet-info` | GET | Arweave wallet status |
| `/self-attestation` | GET | VM attestation data |
| `/chat` | POST | Send message, get proof |
| `/upload-to-arweave` | POST | Upload proof to Arweave |
| `/decrypt-proof` | POST | Decrypt conversation |

## 🎮 Usage Flow

1. **Start Chat**: Enter message + encryption password
2. **AI Response**: Get response from Secret AI (or mock)
3. **Generate Proof**: System creates cryptographic proof with:
   - Encrypted conversation (user password)
   - Verification hashes (public)
   - VM attestation data (both VMs)
   - Cryptographic binding
4. **Download/Upload**: User controls proof distribution

## 🔍 Proof Structure

```json
{
  "proof_id": "proof_1671234567",
  "timestamp": "2025-06-15T01:23:45Z",
  "version": "1.0.0",
  "encrypted_conversation": "...",
  "verification": {
    "message_hash": "sha256...",
    "response_hash": "sha256...",
    "interaction_hash": "sha256..."
  },
  "attestations": {
    "attest_ai_vm": { "mr_td": "...", "rtmr0": "...", ... },
    "secret_ai_vm": { "mr_td": "...", "rtmr0": "...", ... }
  },
  "cryptographic_binding": {
    "binding_hash": "sha256...",
    "method": "sha256_dual_attestation_v1"
  }
}
```

## 🧪 Testing

```bash
# Test project structure
python3 test_imports.py

# Test Docker build
docker-compose build

# Test health endpoint
curl http://localhost:8000/health

# Test wallet info
curl http://localhost:8000/wallet-info

# Test self-attestation
curl http://localhost:8000/self-attestation
```

## 🚢 SecretVM Deployment

1. **Build image locally**
   ```bash
   docker-compose build
   ```

2. **Push to registry** (GitHub Actions handles this)

3. **Deploy to SecretVM**
   ```bash
   secretvm-cli vm create -n "attest-ai-mvp" -t "medium" -d "./docker-compose.yaml"
   ```

4. **Upload environment** (separately upload .env file)

## 📊 Current Limitations

- **Secret AI Attestation**: Not yet implemented by Secret AI team (using mock)
- **Arweave Uploads**: May fail if wallet unfunded (graceful mock fallback)
- **Self-Attestation**: HTML parsing dependent on localhost:29343 format

## 🤝 Contributing

This is an MVP focused on demonstrating core concepts. For production deployment:

1. Enhanced error handling
2. Database for proof storage  
3. Rate limiting and authentication
4. Multi-stage Docker builds
5. Comprehensive test suite

## 📄 License

[Add your license here]

## 🔗 Related Documentation

- [UNIFIED_AI_IMPLEMENTATION_GUIDE.md](planning/UNIFIED_AI_IMPLEMENTATION_GUIDE.md) - Complete implementation guide
- [BUILD_REFERENCE_SHEET.md](planning/BUILD_REFERENCE_SHEET.md) - Technical reference sheet

---

**Note**: This is an MVP demonstrating technical feasibility. Secret AI attestation feature is coming soon!