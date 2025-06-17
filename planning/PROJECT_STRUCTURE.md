# attest_ai Project Structure Template

This document provides the complete directory structure and file descriptions for the attest_ai MVP implementation.

## **Root Directory Structure**

```
attest_ai/
├── 📁 src/                          # Main application source code
├── 📁 static/                       # Static web assets (HTML, CSS, JS)
├── 📁 downloads/                    # Local proof file storage (created at runtime)
├── 📁 tools/                        # Standalone utilities
├── 📁 tests/                        # Test suite
├── 📁 planning/                     # Project planning documents
├── 📁 documents/                    # Reference documentation
├── 📄 docker-compose.yaml          # SecretVM deployment configuration
├── 📄 Dockerfile                   # Container build configuration
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.template                # Environment variable template
├── 📄 .gitignore                   # Git ignore patterns
└── 📄 README.md                    # Project overview and setup
```

---

## **📁 src/ - Core Application**

```
src/
├── 📄 api.py                       # FastAPI main application
├── 📄 self_attestation_client.py   # Self VM attestation (localhost:29343)
├── 📄 secret_ai_client.py          # Secret AI SDK integration
├── 📄 encryption_client.py         # Proof encryption/decryption
├── 📄 proof_manager.py             # Proof file management
├── 📄 proof_generator.py           # Dual attestation proof creation
└── 📄 models.py                    # Pydantic data models
```

### **File Descriptions:**

**📄 api.py**
- FastAPI application setup and configuration
- Route definitions for all endpoints
- Middleware configuration (CORS, security)
- Startup/shutdown event handlers
- Health check endpoint

**📄 self_attestation_client.py**
- Connects to localhost:29343/cpu.html
- Parses HTML attestation reports
- Extracts MRTD, RTMR0-3, reportdata
- Caches attestation with TTL
- TLS fingerprint capture

**📄 secret_ai_client.py**
- Secret AI SDK integration
- Model discovery (`get_models()`, `get_urls()`)
- ChatSecret client management
- Multi-strategy attestation capture:
  - SDK method (when available)
  - Direct endpoint access
  - Mock fallback
- TLS certificate fingerprint extraction

**📄 encryption_client.py**
- Symmetric encryption using Fernet
- PBKDF2 key derivation from passwords
- Auto-generated key creation
- Encryption/decryption of proof data
- Support for multiple encryption methods

**📄 proof_manager.py**
- Proof file generation and storage
- File naming conventions
- Download endpoint management
- Cleanup of expired files
- File metadata tracking

**📄 proof_generator.py**
- Dual attestation proof creation
- Cryptographic hash generation
- SHA-256 binding of all components
- Proof structure validation
- Interaction data inclusion

**📄 models.py**
- Pydantic models for API requests/responses
- Data validation schemas
- Type definitions for attestation data
- Proof structure models

---

## **📁 static/ - Web Interface**

```
static/
├── 📄 index.html                   # Main web interface
├── 📄 style.css                    # Application styles
├── 📄 app.js                       # Frontend JavaScript
└── 📁 assets/                      # Images, icons, etc.
    ├── 📄 logo.png
    └── 📄 favicon.ico
```

### **File Descriptions:**

**📄 index.html**
- Single-page application layout
- Dual attestation panels
- Chat interface
- Proof generation controls
- Download links

**📄 style.css**
- Modern, responsive design
- Attestation panel styling
- Chat message formatting
- Dark/light theme support

**📄 app.js**
- API communication
- Real-time attestation updates
- Chat functionality
- Proof generation and download
- Error handling and user feedback

---

## **📁 tools/ - Standalone Utilities**

```
tools/
├── 📄 decrypt_proof.py             # Standalone proof decryption utility
├── 📄 verify_attestation.py        # Attestation verification tool
└── 📄 test_secret_ai.py            # Secret AI connection tester
```

### **File Descriptions:**

**📄 decrypt_proof.py**
- Command-line proof decryption
- Multiple output formats (JSON, HTML, text)
- Proof integrity verification
- Standalone operation (no server needed)

**📄 verify_attestation.py**
- Validates attestation data structure
- Re-computes and verifies hashes
- Checks cryptographic bindings
- Outputs verification report

**📄 test_secret_ai.py**
- Tests Secret AI connectivity
- Validates API key
- Lists available models and instances
- Troubleshooting helper

---

## **📁 tests/ - Test Suite**

```
tests/
├── 📄 __init__.py
├── 📄 conftest.py                  # Pytest configuration
├── 📄 test_api.py                  # API endpoint tests
├── 📄 test_attestation.py          # Attestation client tests
├── 📄 test_encryption.py           # Encryption/decryption tests
├── 📄 test_proof_generation.py     # Proof creation tests
├── 📁 fixtures/                    # Test data
│   ├── 📄 sample_attestation.json
│   ├── 📄 sample_proof.json
│   └── 📄 test_cert.pem
└── 📁 integration/                 # Integration tests
    ├── 📄 test_e2e_flow.py
    └── 📄 test_secretvm_deploy.py
```

---

## **📁 Configuration Files**

### **📄 docker-compose.yaml**
```yaml
# SecretVM deployment configuration
# Environment variable mapping
# Volume mounts for proof storage
# Health checks and restart policies
```

### **📄 Dockerfile**
```dockerfile
# Multi-stage build for production
# Python 3.12 slim base
# Non-root user configuration
# Health check integration
```

### **📄 requirements.txt**
```txt
# Core dependencies:
# - fastapi
# - uvicorn
# - httpx
# - pydantic
# - cryptography
# - secret-ai-sdk
# - beautifulsoup4
# - aiofiles
```

### **📄 .env.template**
```bash
# Secret AI configuration
# SecretVM attestation settings
# Application configuration
# Proof encryption settings
# (Never commit real .env file)
```

### **📄 .gitignore**
```
# Environment files
.env
.env.local
.env.production

# Python cache
__pycache__/
*.pyc
*.pyo

# IDE files
.vscode/
.idea/

# Local storage
downloads/
*.attestproof

# Logs
*.log
```

---

## **📁 planning/ - Project Documentation**

```
planning/
├── 📄 README.md                    # Planning overview
├── 📄 NEW_MVP_BUILD_PLAN.md        # Main implementation guide
├── 📄 UPDATED_IMPLEMENTATION_REFERENCES.md  # Technical patterns
├── 📄 SECRET_AI_ALIGNMENT_ANALYSIS.md       # Compatibility validation
├── 📄 PROJECT_STRUCTURE.md         # This document
└── 📁 .archive/                    # Archived planning documents
```

---

## **📁 documents/ - Reference Materials**

```
documents/
├── 📁 secretAI/                    # Secret AI documentation
├── 📁 secretVM/                    # SecretVM documentation
├── 📁 arweave/                     # Arweave documentation (future)
└── 📄 docker-best-practices.txt   # Docker optimization guidelines
```

---

## **Runtime Directories**

### **📁 downloads/ (Created at Runtime)**
```
downloads/
├── 📄 proof_2025-06-16_abc12345.attestproof
├── 📄 .mapping_uuid1.json          # File metadata
├── 📄 .mapping_uuid2.json
└── 📄 .cleanup_log.txt             # Cleanup activity log
```

**Purpose:** Temporary storage for encrypted proof files before download

---

## **Development Workflow Structure**

### **Local Development**
1. Clone repository
2. Copy `.env.template` to `.env`
3. Set `SECRET_AI_API_KEY`
4. Run `pip install -r requirements.txt`
5. Start with `uvicorn src.api:app --reload`

### **Testing**
1. Run unit tests: `pytest tests/`
2. Run integration tests: `pytest tests/integration/`
3. Test tools: `python tools/test_secret_ai.py`

### **Deployment**
1. Build container: `docker-compose build`
2. Deploy to SecretVM: `secretvm-cli vm create`
3. Upload environment: `secretvm-cli vm upload-env`
4. Verify deployment: Check health endpoint

---

## **Key Design Principles**

### **🔒 Security First**
- No secrets in source code
- Environment variable validation
- Secure file handling
- TLS certificate verification

### **🏗️ Modular Architecture**
- Clear separation of concerns
- Testable components
- Easy to extend (Arweave module later)
- Standard Python patterns

### **🚀 Deployment Ready**
- Single docker-compose deployment
- Health checks and monitoring
- Graceful shutdown handling
- Resource cleanup

### **🧪 Testing Focused**
- Comprehensive test coverage
- Mock data for CI/CD
- Integration test suite
- Verification tools

This project structure provides a solid foundation for the attest_ai MVP implementation with clear organization, comprehensive testing, and production readiness.
