# **Redesigned attest_ai MVP Build Plan**

## **New Success Criteria Priority**
1. ✅ **App runs on SecretVM** 
2. ✅ **Secret AI powered chatbot**
3. ✅ **Dual machine attestation** (chatbot VM + Secret AI VM)
4. ✅ **Generate encrypted proof** with chat + attestation data
5. ✅ **Downloadable chat proof** 
6. ✅ **Decryption tool**
7. ✅ **Demo UI website**

---

## **Phase 1: Foundation & Environment (Week 1)**

### **Task 1.1: Simplified Environment Setup**
**Remove Arweave complexity, focus on core:**

**New `.env.template`:**
```bash
# Secret AI Configuration (NEVER commit real values)
SECRET_AI_API_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1

# Optional Secret AI Configuration
SECRET_CHAIN_ID=secret-4
SECRET_NODE_URL=https://lcd.mainnet.secretsaturn.net

# SecretVM Self-Attestation
SELF_ATTESTATION_URL=http://localhost:29343
ATTESTATION_CACHE_TTL=300

# Application Configuration
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# NEW: Proof Encryption Configuration
PROOF_ENCRYPTION_METHOD=symmetric  # symmetric|asymmetric
DEFAULT_ENCRYPTION_PASSWORD=auto_generate  # or user-provided
PROOF_FILE_CLEANUP_HOURS=24
```

**Simplified `docker-compose.yaml`:**
```yaml
version: '3.8'
services:
  attest-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_AI_API_KEY=${SECRET_AI_API_KEY}
      - SECRET_CHAIN_ID=${SECRET_CHAIN_ID:-secret-4}
      - SECRET_NODE_URL=${SECRET_NODE_URL:-https://lcd.mainnet.secretsaturn.net}
      - SELF_ATTESTATION_URL=${SELF_ATTESTATION_URL:-http://localhost:29343}
      - ATTESTATION_CACHE_TTL=${ATTESTATION_CACHE_TTL:-300}
      - API_PORT=${API_PORT:-8000}
      - DEBUG=${DEBUG:-false}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - PROOF_ENCRYPTION_METHOD=${PROOF_ENCRYPTION_METHOD:-symmetric}
      - DEFAULT_ENCRYPTION_PASSWORD=${DEFAULT_ENCRYPTION_PASSWORD:-auto_generate}
      - PROOF_FILE_CLEANUP_HOURS=${PROOF_FILE_CLEANUP_HOURS:-24}
    volumes:
      - ./static:/app/static:ro
      - ./downloads:/app/downloads  # NEW: Local proof storage
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### **Task 1.2: Updated Docker Configuration**
**Remove Arweave dependencies, add crypto libraries:**

**Updated `requirements.txt` with Secret AI SDK:**
```txt
# Core FastAPI Framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.10.4
pydantic_core==2.27.2

# HTTP & Async Operations
httpx==0.27.2
httpcore==1.0.7
aiofiles==23.2.1
python-multipart==0.0.6
anyio==4.7.0

# Secret AI SDK Dependencies (from official requirements)
secret-sdk>=1.8.1
secret-ai-sdk
langchain==0.3.13
langchain-core==0.3.28
langchain-ollama==0.2.2
langchain-text-splitters==0.3.4
langsmith==0.2.4
ollama==0.4.4

# Cryptography (Secret AI uses newer version)
cryptography==44.0.0

# Secret Network Dependencies
bech32==1.2.0
ecdsa==0.16.1
secp256k1==0.14.0
mnemonic==0.19
protobuf==3.20.3

# HTTP & Network
aiohttp==3.11.11
aiosignal==1.3.2
requests==2.32.3
requests-toolbelt==1.0.0
certifi==2024.12.14
charset-normalizer==3.4.0
idna==3.10
urllib3==2.2.3

# HTML Parsing for Attestation
beautifulsoup4==4.12.2

# JSON & Data Processing
orjson==3.10.12
jsonpatch==1.33
jsonpointer==3.0.0
PyYAML==6.0.2

# Utilities
typing_extensions==4.12.2
packaging==24.2
setuptools==75.1.0
six==1.17.0
sniffio==1.3.1
tenacity==9.0.0
```

---

## **Phase 2: Self-Attestation Implementation (Week 1-2)**

### **Task 2.1: Self-Attestation Client (UNCHANGED - PRIORITY)**
**Keep the same implementation from original plan:**
- Always real data from localhost:29343
- Caching with TTL
- TLS fingerprint capture
- Error handling and logging

### **Task 2.2: Secret AI Client Enhancement (SIMPLIFIED)**
**Implement correct SDK pattern with attestation strategy:**

**Core Implementation:**
- **Correct SDK initialization**: `Secret()` with API key from environment
- **Model discovery**: `get_models()` and `get_urls(model)` pattern
- **Chat functionality**: `ChatSecret(base_url, model, temperature)` pattern
- **Attestation strategy**: Attempt direct endpoint access, fallback to mock
- **NO Arweave upload logic**

**Attestation Approach:**
1. **Try SDK method**: `secret_ai_llm.get_attestation()` (may return empty)
2. **Try direct endpoint**: `GET https://{base_url}:29343/cpu.html`
3. **Fallback to mock**: Generate realistic attestation structure
4. **Always capture**: TLS fingerprint from base_url connection

---

## **Phase 3: NEW - Proof Encryption & Download System (Week 2-3)**

### **Task 3.1: Proof Encryption Engine**
**NEW component replacing Arweave integration:**

**Core Features:**
- **Symmetric encryption** with user-provided or auto-generated passwords
- **Asymmetric option** for advanced users (generate keypair)
- **Proof serialization** to encrypted file format
- **Metadata headers** for proof identification
- **Integrity verification** with checksums

**Expected Implementation Areas:**
- `src/encryption_client.py` - Core encryption/decryption logic
- `src/proof_manager.py` - Proof generation and file management
- File format: `.attestproof` encrypted container

### **Task 3.2: Download & File Management System**
**NEW component for local proof storage:**

**Core Features:**
- **Proof file generation** after each chat interaction
- **Download endpoint** for proof files
- **Local storage management** (temporary files, cleanup)
- **Proof metadata tracking** (proof ID, timestamp, size)
- **File naming convention** with timestamps and IDs

**Expected Implementation Areas:**
- `/api/v1/proofs/{proof_id}/download` endpoint
- Local file storage in `/downloads` volume
- Proof indexing and metadata storage

---

## **Phase 4: Decryption Tool Development (Week 3)**

### **Task 4.1: Standalone Decryption Utility**
**NEW standalone tool:**

**Tool Options:**
1. **Command-line utility** (`decrypt_proof.py`)
2. **Simple web interface** (separate from main app)
3. **Python library** for programmatic access

**Core Features:**
- **Decrypt `.attestproof` files** with password/key
- **Verify proof integrity** and attestation data
- **Extract chat conversation** in readable format
- **Validate attestation hashes** and bindings
- **Export to JSON/HTML** for human reading

### **Task 4.2: Proof Verification Logic**
**NEW verification system:**

**Verification Steps:**
1. **Decrypt proof file** successfully
2. **Validate proof structure** and required fields
3. **Verify attestation hashes** match computed values
4. **Check cryptographic bindings** between components
5. **Validate timestamps** and freshness
6. **Display verification results** with clear status

---

## **Phase 5: Simplified UI Implementation (Week 3-4)**

### **Task 5.1: Core Functionality Implementation**
**SIMPLIFIED: Focus on 4 key features (see SIMPLIFIED_UI_REQUIREMENTS.md)**

**Core Requirements:**
1. **Automatic proof generation** (if password provided)
2. **Simple download button** for latest proof  
3. **Upload & decrypt area** for proof files
4. **Attestation reports** with expandable details

**Simple Layout Structure:**
```html
<div class="container">
    <header>
        <h1>Attest AI</h1>
        <p>Privacy-Preserving AI Chat with Attestation</p>
    </header>
    
    <!-- 1. Proof Password Setting -->
    <section class="proof-password-section">
        <label for="proofPassword">Proof Password (optional):</label>
        <input type="password" id="proofPassword" 
               placeholder="Enter password to enable automatic proof generation">
        <small>Leave blank to disable proof generation</small>
    </section>
    
    <!-- Chat Interface -->
    <section class="chat-section">
        <div id="chatMessages"></div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Type your message...">
            <button id="sendMessage">Send</button>
        </div>
    </section>
</div>
```

### **Task 5.2: Attestation Reports with Details**
**Simple status display with expandable details:**

```html
<!-- 4. Attestation Reports -->
<section class="attestation-reports">
    <h3>Attestation Status</h3>
    
    <!-- Host Machine Attestation -->
    <div class="attestation-item">
        <div class="attestation-summary">
            <span class="status-indicator success">✓</span>
            <span class="attestation-title">Host Machine Attestation</span>
            <span class="attestation-status">Active</span>
        </div>
        <button class="details-btn" data-target="host-details">View Details</button>
        <div id="host-details" class="attestation-details hidden">
            <!-- Detailed attestation data -->
        </div>
    </div>
    
    <!-- Secret AI Attestation -->
    <div class="attestation-item">
        <div class="attestation-summary">
            <span class="status-indicator warning">⚠</span>
            <span class="attestation-title">Secret AI Attestation</span>
            <span class="attestation-status">Mock Data</span>
        </div>
        <button class="details-btn" data-target="secretai-details">View Details</button>
        <div id="secretai-details" class="attestation-details hidden">
            <!-- Detailed attestation data -->
        </div>
    </div>
</section>
```

### **Task 5.3: Download & Decrypt Sections**
**Simple download and file handling:**

```html
<!-- 2. Download Section -->
<section class="download-section">
    <h3>Download Latest Proof</h3>
    <button id="downloadProof" disabled>Download Proof File</button>
    <div id="downloadStatus">No proof available</div>
</section>

<!-- 3. Upload & Decrypt Section -->
<section class="decrypt-section">
    <h3>Decrypt Proof File</h3>
    <div class="upload-area">
        <input type="file" id="proofFile" accept=".attestproof">
        <label for="proofFile">Choose proof file to decrypt</label>
    </div>
    <div class="decrypt-password">
        <input type="password" id="decryptPassword" placeholder="Enter decryption password">
        <button id="decryptButton">Decrypt & View</button>
    </div>
    <div id="decryptedContent" class="hidden">
        <!-- Decrypted proof content will be displayed here -->
    </div>
</section>
```

### **Task 5.4: Simple Functionality Logic**
**Core JavaScript functionality for 4 key features:**

**Automatic Proof Generation:**
```javascript
// Check password field on every chat response
function handleChatResponse(response) {
    const proofPassword = document.getElementById('proofPassword').value;
    
    if (proofPassword) {
        // Auto-generate proof in background
        generateProofAutomatically(response, proofPassword);
        updateDownloadButton(true);
    }
}
```

**Download Management:**
```javascript
// Enable/disable download button based on proof availability
function updateDownloadButton(hasProof) {
    const downloadBtn = document.getElementById('downloadProof');
    const status = document.getElementById('downloadStatus');
    
    if (hasProof) {
        downloadBtn.disabled = false;
        downloadBtn.textContent = 'Download Proof File';
        status.textContent = 'Proof ready for download';
    } else {
        downloadBtn.disabled = true;
        status.textContent = 'No proof available';
    }
}
```

**Attestation Details Toggle:**
```javascript
// Show/hide attestation details
function toggleDetails(targetId) {
    const details = document.getElementById(targetId);
    details.classList.toggle('hidden');
}
```

### **Task 5.5: Updated API Endpoints**
**Simplified API for automatic proof generation:**

```python
# Chat with automatic proof generation
POST /api/v1/chat
{
    "message": "Should I invest in SCRT?",
    "proof_password": "optional-password"  # If provided, auto-generate proof
}

Response:
{
    "response": "Based on analysis...",
    "attestations": { /* attestation data */ },
    "proof_generated": true,  # if password was provided
    "proof_id": "uuid-here"   # for download
}

# Simple download endpoint
GET /api/v1/proof/download/{proof_id}
# Returns encrypted .attestproof file

# Decrypt endpoint (for uploaded files)
POST /api/v1/proof/decrypt
{
    "file_data": "base64-encoded-file",
    "password": "decryption-password"
}

Response:
{
    "success": true,
    "chat_history": [ /* messages */ ],
    "attestations": { /* attestation data */ },
    "timestamp": "2025-06-17T10:30:00Z"
}
```

### **Task 5.6: Simple User Workflow**
**Streamlined user experience:**

**User Steps:**
1. **Optional**: Enter proof password to enable automatic proof generation
2. **Chat**: Send messages to Secret AI (proofs auto-generated if password set)
3. **Download**: Click download button to get latest proof file  
4. **Decrypt**: Upload any proof file with password to view contents
5. **Attestation**: View status summaries, expand for technical details

**Status Indicators:**
- **✓ (green)**: Real attestation data available
- **⚠ (yellow)**: Using mock/fallback data  
- **✗ (red)**: Attestation failed or unavailable

### **Task 5.7: Simple UI Testing**
**Functional testing of 4 core features:**

**Proof Generation Testing:**
- [ ] **Password field** controls automatic proof generation
- [ ] **No password** = no proof generated
- [ ] **With password** = proof auto-generated after each chat

**Download Testing:**
- [ ] **Download button** enabled when proof exists
- [ ] **Download button** disabled when no proof available
- [ ] **File download** provides .attestproof file

**Decrypt Testing:**
- [ ] **File upload** accepts .attestproof files
- [ ] **Correct password** decrypts and shows content
- [ ] **Wrong password** shows error message

**Attestation Testing:**
- [ ] **Status summaries** show current attestation state
- [ ] **View Details** buttons expand to show full data
- [ ] **Host attestation** attempts real data from localhost:29343
- [ ] **Secret AI attestation** shows real or mock data as available

---

## **Phase 6: Integration & SecretVM Deployment (Week 4-5)**

### **Task 6.1: SecretVM Deployment (SIMPLIFIED)**
**Remove Arweave complexity from deployment:**

**Simplified environment handling:**
- Secret AI API key in environment (not constructor parameter)
- Optional chain_id and node_url configuration
- No wallet management
- Simplified validation logic
- Focus on attestation endpoints availability

### **Task 6.2: End-to-End Validation (UPDATED)**

**New Validation Checklist:**

**Local Testing:**
- [ ] Self-attestation retrieval from localhost:29343
- [ ] Secret AI instance discovery and chat
- [ ] Dual attestation capture and display
- [ ] Proof encryption with different methods
- [ ] Proof file download functionality
- [ ] Decryption tool works on generated proofs
- [ ] **NEW: Simple UI with 4 core features working**
- [ ] **NEW: Automatic proof generation based on password**
- [ ] **NEW: Download button provides .attestproof files**
- [ ] **NEW: Upload & decrypt functionality works**
- [ ] **NEW: Attestation details expandable with View Details buttons**
- [ ] Docker container builds and runs locally

**SecretVM Deployment Testing:**
- [ ] GitHub Actions deploys successfully
- [ ] Environment variables loaded securely (no Arweave vars)
- [ ] Self-attestation works in SecretVM environment
- [ ] Secret AI discovery from within SecretVM
- [ ] Proof generation and download work in SecretVM
- [ ] Web UI loads and functions correctly

**Security & Proof Validation:**
- [ ] No sensitive data in GitHub repository
- [ ] Environment variables properly encrypted in SecretVM
- [ ] Proof files properly encrypted
- [ ] Decryption tool validates all proof components
- [ ] Attestation verification works correctly

---

## **Updated Success Criteria**

### **Priority 1: SecretVM Deployment** ✅
- Single docker-compose.yaml deploys successfully
- Simplified environment variables (no Arweave)
- Application runs in SecretVM environment

### **Priority 2: Secret AI Chatbot** ✅  
- Instance discovery works from within SecretVM
- Chat functionality with real AI responses
- Fallback to mock when instances unavailable

### **Priority 3: Dual Machine Attestation** ✅
- Self-attestation from attest_ai VM (always real)
- Secret AI attestation (real when available, mock fallback)
- Both attestations displayed side-by-side in UI

### **Priority 4: Encrypted Proof Generation** ✅
- Generate encrypted proof files after chat interactions
- Multiple encryption options (password, auto-key, keypair)
- Cryptographic binding of chat + dual attestation data

### **Priority 5: Downloadable Proofs** ✅
- Download encrypted proof files locally
- Proper file naming and metadata
- Temporary storage with cleanup

### **Priority 6: Decryption Tool** ✅
- Standalone utility to decrypt proof files
- Verify proof integrity and attestation data
- Extract readable chat conversation

### **Priority 7: Simple Functional Interface** ✅
- **Automatic proof generation** when password provided
- **Simple download button** for latest proof files
- **Upload & decrypt area** for proof verification
- **Attestation status display** with expandable details
- **Clean, functional UI** focused on core features
- **No complex interactions** - straightforward workflow

---

## **Implementation Notes**

### **Development Order:**
1. **Week 1**: Environment setup + Self-attestation (same as before)
2. **Week 2**: Secret AI integration + Proof encryption engine
3. **Week 3**: **NEW: Simple UI with 4 core features** + Decryption tool
4. **Week 4**: **Functional testing & refinement** + Integration testing
5. **Week 5**: SecretVM deployment + Final validation

### **Key Changes from Original:**
- **Removed**: All Arweave integration, wallet management, upload logic
- **Added**: Proof encryption, file download, decryption tool
- **Added**: **Simple functional UI** with automatic proof generation
- **Added**: **Upload & decrypt functionality** for proof verification
- **Added**: **Expandable attestation details** with summary view
- **Simplified**: Environment setup, deployment pipeline
- **Focus**: Core attestation, Secret AI functionality, **and simple usability**

### **Technology Stack Changes:**
- **Removed**: `arweave-python-client`
- **Added**: `cryptography` for encryption
- **Added**: File management and download endpoints
- **Added**: Standalone decryption utility

---

## **Future Arweave Module Integration**

### **Modular Design for Later Addition:**
The current architecture is designed to cleanly accept Arweave as a separate module:

**Current Flow:**
```
Chat → Dual Attestation → Encrypted Proof → Local Download
```

**Future Flow (when Arweave added):**
```
Chat → Dual Attestation → Encrypted Proof → [Local Download + Arweave Upload]
```

### **Clean Integration Points:**
- **Environment variables**: Add Arweave vars without changing existing ones
- **API endpoints**: Extend current responses to include Arweave data
- **Storage layer**: Add `src/storage/arweave_storage.py` alongside `local_storage.py`
- **UI toggles**: Add "Also upload to Arweave" option
- **Zero breaking changes**: Existing functionality preserved

This modular approach ensures the MVP is fully functional now, with Arweave becoming a value-add feature later without disrupting the core system.
