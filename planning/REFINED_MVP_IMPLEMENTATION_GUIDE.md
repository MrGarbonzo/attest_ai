# Refined attest_ai MVP Implementation Plan

## Updated Project Goals (In Order of Priority)

1. ✅ **Must deploy in SecretVM using a single docker-compose.yaml**
2. ✅ **Must use Secret AI**
3. ✅ **Must use Arweave storage** (mnemonic in .env, mock final transaction if unfunded)
4. ✅ **Must have simple chat feature showing all attestation data** (some mock if unavailable)
5. ✅ **Two attestation reports**: Secret AI VM + attest_ai VM (self-attestation priority)

## Critical Updates to Original Plan

### **Security & Environment Configuration**
- **All sensitive data in .env** (excluded from GitHub)
- **Separate .env upload to SecretVM** for encrypted storage
- **Default wallet via mnemonic in .env**
- **No hardcoded secrets in public code**

### **Dual Attestation Architecture**
- **Self-attestation FIRST** (localhost:29343/cpu.html - always real)
- **Secret AI attestation** (remote instances - mock if unavailable)
- **Side-by-side attestation display in UI**

### **Smart Mock Strategy**
- **Arweave**: Mock final transaction if wallet unfunded, otherwise real upload
- **Attestation**: Only mock what cannot be retrieved remotely (per Secret AI limitations)
- **Everything else**: Real implementation

---

## Phase 1: Environment & Security Setup (Week 1)

### Task 1.1: Enhanced Environment Configuration

**Create comprehensive `.env.template`:**
```bash
# Secret AI Configuration (NEVER commit real values)
SECRET_AI_MASTER_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1

# Arweave Wallet Configuration (NEVER commit real mnemonic)
ARWEAVE_MNEMONIC=abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about
ARWEAVE_GATEWAY=https://arweave.net

# Application Configuration
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# SecretVM Self-Attestation
SELF_ATTESTATION_URL=http://localhost:29343
ATTESTATION_CACHE_TTL=300

# UI Configuration
ENABLE_ARWEAVE_UPLOAD=true
MOCK_UNFUNDED_TRANSACTIONS=true
```

**Create `.env` in .gitignore:**
```gitignore
.env
.env.local
.env.production
*.key
*.pem
*.p12
arweave_wallet.json
```

**Security Implementation:**
- Environment variable validation on startup
- Secure handling of mnemonic (never logged)
- Runtime checks for required secrets
- Clear separation of public/private config

### Task 1.2: Docker Configuration for SecretVM

**Enhanced `docker-compose.yaml`:**
```yaml
version: '3.8'
services:
  attest-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_AI_MASTER_KEY=${SECRET_AI_MASTER_KEY}
      - ARWEAVE_MNEMONIC=${ARWEAVE_MNEMONIC}
      - ARWEAVE_GATEWAY=${ARWEAVE_GATEWAY}
      - API_PORT=${API_PORT}
      - DEBUG=${DEBUG}
      - LOG_LEVEL=${LOG_LEVEL}
      - SELF_ATTESTATION_URL=${SELF_ATTESTATION_URL}
      - ATTESTATION_CACHE_TTL=${ATTESTATION_CACHE_TTL}
      - ENABLE_ARWEAVE_UPLOAD=${ENABLE_ARWEAVE_UPLOAD}
      - MOCK_UNFUNDED_TRANSACTIONS=${MOCK_UNFUNDED_TRANSACTIONS}
    volumes:
      - ./static:/app/static:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Enhanced `Dockerfile`:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements/ requirements/
RUN pip install -r requirements/requirements.txt

# Copy application code
COPY src/ src/
COPY static/ static/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Phase 2: Self-Attestation Implementation (Week 1-2)

### Task 2.1: Self-Attestation Client (PRIORITY)

**Create `src/self_attestation_client.py`:**

```python
class SelfAttestationClient:
    def __init__(self, attestation_url: str = "http://localhost:29343"):
        self.attestation_url = attestation_url
        self.cache_ttl = int(os.getenv("ATTESTATION_CACHE_TTL", "300"))
        self._cached_attestation = None
        self._cache_timestamp = None
    
    async def get_local_vm_attestation(self) -> Dict:
        """Get attestation from the VM that attest_ai runs on"""
        
    async def parse_cpu_html(self, html_content: str) -> Dict:
        """Parse CPU attestation from HTML format"""
        
    async def extract_attestation_quote(self, content: str) -> str:
        """Extract attestation quote from HTML"""
        
    async def parse_registers(self, quote: str) -> Dict:
        """Parse mr_td, rtmr0-3, report_data from quote"""
        
    async def get_tls_fingerprint(self) -> str:
        """Get TLS certificate fingerprint for MITM protection"""
        
    async def validate_attestation_freshness(self, attestation: Dict) -> bool:
        """Validate attestation timestamp is recent"""
        
    async def cache_attestation(self, attestation: Dict):
        """Cache attestation with TTL"""
        
    async def get_cached_attestation(self) -> Optional[Dict]:
        """Get cached attestation if still valid"""
```

**Implementation Requirements:**
- **Always real data** (never mocked since localhost:29343 is available)
- **Caching with TTL** (attestation shouldn't change often)
- **TLS fingerprint capture** for MITM protection
- **Comprehensive error handling** for network issues
- **Structured logging** for debugging

**Expected Result:** Working self-attestation from attest_ai's own SecretVM

### Task 2.2: Secret AI Client Enhancement

**Update `src/secret_ai_client.py` for mock support:**

```python
class SecretAIClient:
    def __init__(self, master_key: str):
        self.secret_client = Secret(master_key)
        self.mock_mode = False
        
    async def discover_instances_with_attestation(self) -> List[Dict]:
        """Discover instances and check attestation availability"""
        
    async def get_remote_attestation(self, instance_url: str) -> Dict:
        """Get attestation from Secret AI VM - mock if unavailable"""
        
    async def create_mock_attestation(self, instance_url: str) -> Dict:
        """Create mock attestation data when real data unavailable"""
        
    async def send_message_with_attestation(self, message: str, instance_url: str) -> Dict:
        """Send message and capture corresponding attestation"""
```

**Mock Strategy:**
- **Attempt real attestation first**
- **Fall back to mock only if real data unavailable**
- **Clear indication in response when data is mocked**
- **Use realistic SecretVM attestation data structure for mocks**

---

## Phase 3: Enhanced Arweave Integration (Week 2-3)

### Task 3.1: Wallet Integration with Mnemonic

**Create `src/arweave_client.py`:**

```python
class ArweaveClient:
    def __init__(self):
        self.mnemonic = os.getenv("ARWEAVE_MNEMONIC")
        self.gateway = os.getenv("ARWEAVE_GATEWAY", "https://arweave.net")
        self.wallet = None
        self.enable_upload = os.getenv("ENABLE_ARWEAVE_UPLOAD", "true").lower() == "true"
        self.mock_unfunded = os.getenv("MOCK_UNFUNDED_TRANSACTIONS", "true").lower() == "true"
        
    async def initialize_wallet(self):
        """Initialize wallet from mnemonic"""
        
    async def get_wallet_balance(self) -> float:
        """Get current wallet balance in AR"""
        
    async def estimate_upload_cost(self, data_size: int) -> float:
        """Estimate cost for uploading data"""
        
    async def upload_or_mock_proof(self, proof_data: Dict) -> Dict:
        """Upload proof if funded, otherwise mock transaction"""
        
    async def create_mock_transaction(self, proof_data: Dict) -> Dict:
        """Create realistic mock transaction for demo"""
        
    async def upload_proof_metadata(self, proof_data: Dict) -> str:
        """Real upload to Arweave"""
        
    async def verify_transaction(self, tx_id: str) -> Dict:
        """Verify transaction status"""
```

**Smart Upload Logic:**
1. **Check wallet balance**
2. **Estimate upload cost**
3. **If funded AND upload enabled**: Real upload
4. **If unfunded OR upload disabled**: Mock transaction
5. **Generate realistic mock transaction IDs**
6. **Log all actions for transparency**

### Task 3.2: Upload Toggle Feature

**Add UI toggle for upload behavior:**
- **"Upload to Arweave" checkbox** in UI
- **Balance display** showing current wallet funds
- **Cost estimation** before upload
- **Clear indication** when transaction is mocked
- **Option to queue uploads** for later when funded

---

## Phase 4: Dual Attestation UI (Week 3-4)

### Task 4.1: Enhanced Web Interface

**UI Layout for Dual Attestation:**

```html
<!-- Self-Attestation Panel (Generated once, cached) -->
<div class="attestation-panel self-attestation">
    <h3>attest_ai VM Attestation</h3>
    <div class="attestation-status">✅ Verified SecretVM</div>
    <div class="attestation-details">
        <div>mr_td: <code>ba87a347...</code></div>
        <div>rtmr0: <code>b6941a8c...</code></div>
        <div>TLS Fingerprint: <code>sha256:abc123...</code></div>
        <div>Last Updated: <span>2025-06-13 10:30:00</span></div>
    </div>
</div>

<!-- Secret AI Attestation Panel (Generated per chat) -->
<div class="attestation-panel secretai-attestation">
    <h3>Secret AI VM Attestation</h3>
    <div class="attestation-status">✅ Verified SecretVM</div>
    <div class="attestation-details">
        <div>Instance: <code>secret-ai-instance-1</code></div>
        <div>Model: <code>deepseek-r1</code></div>
        <div>mr_td: <code>ba87a347...</code></div>
        <div>Status: <span class="real-data">Real Data</span></div>
    </div>
</div>

<!-- Chat Interface -->
<div class="chat-interface">
    <!-- Message input and response display -->
</div>

<!-- Arweave Upload Section -->
<div class="arweave-section">
    <div class="wallet-info">
        <span>Balance: 0.5 AR</span>
        <span>Upload Cost: ~0.001 AR</span>
    </div>
    <label>
        <input type="checkbox" id="uploadToArweave" checked> 
        Upload to Arweave
    </label>
    <div class="upload-status">
        <span id="uploadResult">Ready to upload</span>
        <a id="arweaveLink" target="_blank" style="display:none">View on Arweave</a>
    </div>
</div>
```

**UI Behavior:**
1. **Self-attestation loads once** on page load, cached for session
2. **Secret AI attestation updates** with each chat interaction
3. **Clear visual distinction** between real and mocked data
4. **Side-by-side comparison** of both attestations
5. **Progressive disclosure** - details expandable/collapsible

### Task 4.2: Enhanced API Endpoints

**Updated API structure:**

```python
# Attestation endpoints
GET  /api/v1/attestation/self          # attest_ai VM attestation
GET  /api/v1/attestation/secretai      # Available Secret AI instances

# Chat with dual attestation
POST /api/v1/chat
{
    "message": "Should I invest in SCRT?",
    "instance_url": "secret-ai-instance-1",
    "model": "deepseek-r1",
    "capture_attestation": true
}

Response:
{
    "response": "Based on analysis...",
    "attestations": {
        "self": { /* attest_ai VM attestation */ },
        "secretai": { /* Secret AI VM attestation */ }
    },
    "proof": { /* Combined proof structure */ },
    "arweave": {
        "uploaded": true|false,
        "transaction_id": "real_or_mock_id",
        "cost_ar": 0.001,
        "mocked": false
    }
}

# Proof management
GET  /api/v1/proofs/{proof_id}         # Get specific proof
POST /api/v1/proofs/verify             # Verify proof integrity
```

---

## Phase 5: Integration & SecretVM Deployment (Week 4-5)

### Task 5.1: SecretVM Deployment Pipeline

**Enhanced `.github/workflows/deploy-secretvm.yml`:**

```yaml
name: Deploy to SecretVM

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Validate docker-compose
      run: docker-compose config
      
    - name: Setup Node.js for SecretVM CLI
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        
    - name: Install SecretVM CLI
      run: |
        npm install -g secretvm-cli
        
    - name: Login to SecretVM
      run: |
        secretvm-cli auth login -w ${{ secrets.SECRETVM_WALLET_ADDRESS }}
        
    - name: Deploy to SecretVM
      run: |
        secretvm-cli vm create \
          -n "attest-ai-mvp" \
          -t "medium" \
          -d "./docker-compose.yaml"
          
    - name: Upload environment file
      run: |
        # Upload .env separately for encryption
        secretvm-cli vm upload-env $VM_ID .env.production
        
    - name: Verify deployment
      run: |
        sleep 60  # Wait for deployment
        curl -f "https://${VM_DOMAIN}:8000/health"
```

**Environment File Handling:**
1. **Create `.env.production`** with real secrets (not in repo)
2. **Upload via SecretVM CLI** separately from main deployment
3. **Encrypted storage** in SecretVM
4. **Validation endpoints** to ensure secrets loaded correctly

### Task 5.2: Complete Integration Testing

**End-to-End Validation Checklist:**

**Local Testing:**
- [ ] Self-attestation retrieval from localhost:29343
- [ ] Secret AI instance discovery and chat
- [ ] Dual attestation capture and display
- [ ] Arweave wallet initialization from mnemonic
- [ ] Mock vs real transaction logic
- [ ] UI showing both attestations side-by-side
- [ ] Docker container builds and runs locally

**SecretVM Deployment Testing:**
- [ ] GitHub Actions deploys successfully
- [ ] Environment variables loaded securely
- [ ] Self-attestation works in SecretVM environment
- [ ] Secret AI discovery from within SecretVM
- [ ] Attestation endpoints accessible on port 29343
- [ ] Web UI loads and functions correctly
- [ ] Real Arweave uploads (if wallet funded)
- [ ] Mock transactions (if wallet unfunded)

**Security Validation:**
- [ ] No sensitive data in GitHub repository
- [ ] Environment variables properly encrypted in SecretVM
- [ ] TLS certificate fingerprints captured correctly
- [ ] No sensitive data stored permanently
- [ ] Proof generation cryptographically sound

---

## Updated Success Criteria

### **Priority 1: SecretVM Deployment** ✅
- Single docker-compose.yaml deploys successfully
- Environment variables handled securely
- Application runs in SecretVM environment

### **Priority 2: Secret AI Integration** ✅  
- Instance discovery works from within SecretVM
- Chat functionality with real AI responses
- Fallback to mock when instances unavailable

### **Priority 3: Arweave Integration** ✅
- Wallet initialization from mnemonic in .env
- Smart upload logic (real if funded, mock if not)
- Toggle for upload behavior in UI

### **Priority 4: Chat with Attestation Display** ✅
- Simple chat interface
- Both attestations displayed side-by-side
- Clear indication of real vs mocked data
- Self-attestation cached, Secret AI per-chat

### **Priority 5: Dual Attestation Reports** ✅
- Self-attestation from attest_ai VM (always real)
- Secret AI attestation (real when available, mock fallback)
- Combined proof structure linking both
- UI showing both attestations clearly

---

## Implementation Notes

### **Development Order:**
1. **Week 1**: Environment setup + Self-attestation (highest priority)
2. **Week 2**: Secret AI integration + Arweave wallet setup
3. **Week 3**: Dual attestation UI + Smart upload logic
4. **Week 4**: Integration testing + SecretVM deployment
5. **Week 5**: Final validation + documentation

### **Mock Strategy:**
- **Never mock**: Self-attestation (localhost:29343 always available)
- **Mock when necessary**: Secret AI attestation if remote unavailable
- **Smart mocking**: Arweave uploads based on wallet funding
- **Clear labeling**: All mocked data clearly marked in UI

### **Security Priority:**
- **All secrets in .env** (never committed to GitHub)
- **Separate .env upload** to SecretVM for encryption
- **Runtime validation** of required environment variables
- **No hardcoded sensitive data** anywhere in codebase

This refined plan addresses all your priority requirements while maintaining security best practices and providing a clear path to a working MVP in 5 weeks.