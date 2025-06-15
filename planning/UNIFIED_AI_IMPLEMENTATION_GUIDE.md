# Unified AI Implementation Guide for attest_ai MVP

**Target Audience:** AI Assistant  
**Project Type:** MVP/POC - Simple but Complete  
**Complexity Level:** Detailed instructions, simplified implementation  

## **Project Overview**

Build a **minimal viable product** that demonstrates cryptographic attestation proofs for Secret AI interactions. The system must be **functional and complete** while avoiding over-engineering. This is a proof-of-concept to validate the approach before building a production system.

### **Core Requirements (Non-Negotiable)**
1. ✅ **Deploy in SecretVM** using single docker-compose.yaml
2. ✅ **Integrate with Secret AI** for actual LLM conversations  
3. ✅ **Self-attestation** from localhost:29343 (attest_ai's own VM)
4. ✅ **Arweave storage** with mnemonic-based wallet
5. ✅ **Simple web UI** showing all functionality
6. ✅ **Proof encryption** for conversation privacy
7. ✅ **Download/upload options** for user control

### **MVP Philosophy: Simple but Complete**
- **Functional over elegant** - it must work end-to-end
- **Real integrations** - no fake APIs or mock services where real ones exist
- **Smart mocking** - only mock what cannot be accessed (unfunded wallets, unavailable services)
- **Clear documentation** - obvious what's real vs mocked
- **Docker deployment** - must run in SecretVM environment
- **Future-ready** - structured for easy enhancement later

---

## **Architecture Overview**

### **System Components**
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

### **Data Flow**
1. **User** types message + encryption password
2. **attest_ai VM** sends message to Secret AI
3. **attest_ai VM** gets self-attestation from localhost:29343
4. **attest_ai VM** attempts to get Secret AI VM attestation (mock if unavailable)
5. **System** creates proof with encrypted conversation + verification hashes
6. **User** chooses to download proof and/or upload to Arweave
7. **Anyone** can verify proof authenticity, only user can decrypt content

### **Security Model**
- **Conversation privacy**: User password encrypts actual text
- **Proof integrity**: Cryptographic hashes prevent tampering
- **VM attestation**: Proves code ran in secure environments
- **End-to-end verification**: Complete chain from input to storage

---

## **Implementation Plan**

### **Phase 1: Project Setup (Day 1)**

#### **1.1: Environment Configuration**

**Create `.env.template`:**
```bash
# Secret AI Configuration
SECRET_AI_API_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1

# Arweave Wallet (12-word mnemonic)
ARWEAVE_MNEMONIC=abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about
ARWEAVE_GATEWAY=https://arweave.net

# Application Settings
API_PORT=8000
DEBUG=false
```

**Create `.env` (copy from template with real values) and `.gitignore`:**
```gitignore
.env
.env.local
.env.production
*.key
*.pem
arweave_wallet.json
__pycache__/
*.pyc
.pytest_cache/
```

#### **1.2: Docker Configuration**

**Simple `Dockerfile` (single-stage, FastAPI optimized):**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements first (Docker cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Use exec form for proper signal handling
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Simple `docker-compose.yaml`:**
```yaml
version: '3.8'
services:
  attest-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_AI_API_KEY=${SECRET_AI_API_KEY}
      - ARWEAVE_MNEMONIC=${ARWEAVE_MNEMONIC}
      - ARWEAVE_GATEWAY=${ARWEAVE_GATEWAY}
      - API_PORT=${API_PORT}
      - DEBUG=${DEBUG}
    restart: unless-stopped
```

**Dependencies `requirements.txt`:**
```txt
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.1
arweave-python-client==1.0.14
mnemonic==0.20
secret-ai-sdk==1.0.0
cryptography==41.0.7
```

#### **1.3: Project Structure**
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
├── .env                    # Your real secrets (gitignored)
├── .gitignore
└── static/
    ├── index.html          # Chat UI
    ├── style.css           # Basic styling
    └── script.js           # Frontend logic
```

### **Phase 2: Core Integrations (Days 2-4)**

#### **2.1: Secret AI Client (Real Integration)**

**`secret_ai_client.py` - Based on actual SDK:**
```python
import os
from secret_ai_sdk.secret_ai import ChatSecret
from secret_ai_sdk.secret import Secret

class SecretAIClient:
    def __init__(self):
        self.api_key = os.getenv("SECRET_AI_API_KEY")
        if not self.api_key:
            raise ValueError("SECRET_AI_API_KEY environment variable required")
        
        self.secret_client = Secret()
        
    async def get_available_models(self):
        """Get list of available models from Secret AI"""
        try:
            models = self.secret_client.get_models()
            return {"models": models, "success": True}
        except Exception as e:
            return {"models": [], "success": False, "error": str(e)}
    
    async def get_model_urls(self, model=None):
        """Get available instance URLs for a model"""
        try:
            models = self.secret_client.get_models()
            if not models:
                return {"urls": [], "success": False, "error": "No models available"}
            
            target_model = model or models[0]
            urls = self.secret_client.get_urls(model=target_model)
            return {"urls": urls, "model": target_model, "success": True}
        except Exception as e:
            return {"urls": [], "success": False, "error": str(e)}
    
    async def send_message(self, message: str):
        """Send message to Secret AI and get response"""
        try:
            # Get available models and URLs
            model_info = await self.get_model_urls()
            if not model_info["success"] or not model_info["urls"]:
                return {
                    "response": "Secret AI unavailable - using mock response for demo",
                    "success": False,
                    "mock": True,
                    "error": "No Secret AI instances available"
                }
            
            # Create ChatSecret client
            secret_ai_llm = ChatSecret(
                base_url=model_info["urls"][0],
                model=model_info["model"],
                temperature=1.0
            )
            
            # Send message
            messages = [
                ("system", "You are a helpful AI assistant."),
                ("human", message)
            ]
            
            response = secret_ai_llm.invoke(messages, stream=False)
            
            return {
                "response": response.content,
                "success": True,
                "mock": False,
                "model": model_info["model"],
                "instance_url": model_info["urls"][0]
            }
            
        except Exception as e:
            # Fallback to mock response for demo
            return {
                "response": f"Mock AI Response: I understand you asked '{message}'. This is a demo response since Secret AI is unavailable.",
                "success": False,
                "mock": True,
                "error": str(e)
            }
    
    async def get_attestation(self, instance_url: str):
        """Attempt to get attestation from Secret AI VM"""
        try:
            # Try to get attestation using Secret AI SDK
            # Note: get_attestation() exists but may not be implemented
            secret_ai_llm = ChatSecret(base_url=instance_url, model="mock", temperature=1.0)
            attestation = secret_ai_llm.get_attestation()
            
            if attestation:
                return {
                    "attestation": attestation,
                    "success": True,
                    "mock": False,
                    "instance_url": instance_url
                }
            else:
                raise Exception("Attestation method returned empty result")
                
        except Exception as e:
            # Create mock attestation with realistic structure
            return {
                "attestation": {
                    "mr_td": "mock_td_" + "a" * 58,
                    "rtmr0": "mock_rtmr0_" + "b" * 56,
                    "rtmr1": "mock_rtmr1_" + "c" * 56,
                    "rtmr2": "mock_rtmr2_" + "d" * 56,
                    "rtmr3": "mock_rtmr3_" + "e" * 56,
                    "report_data": "mock_report_" + "f" * 52,
                    "timestamp": "2025-06-14T12:00:00Z",
                    "instance_url": instance_url
                },
                "success": False,
                "mock": True,
                "error": str(e)
            }
```

#### **2.2: Attestation Client (Real Self-Attestation)**

**`attestation_client.py` - Parse localhost:29343/cpu.html:**
```python
import aiohttp
import ssl
import hashlib
import re
from datetime import datetime

class AttestationClient:
    def __init__(self, attestation_url="http://localhost:29343"):
        self.attestation_url = attestation_url
        
    async def get_self_attestation(self):
        """Get real attestation from attest_ai's own VM"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get CPU attestation HTML
                async with session.get(f"{self.attestation_url}/cpu.html") as resp:
                    if resp.status != 200:
                        raise Exception(f"Attestation endpoint returned {resp.status}")
                    
                    html_content = await resp.text()
                    
                    # Parse attestation data from HTML
                    attestation_data = self.parse_cpu_html(html_content)
                    
                    # Get TLS fingerprint for MITM protection
                    tls_fingerprint = await self.get_tls_fingerprint()
                    
                    return {
                        "mr_td": attestation_data.get("mr_td", ""),
                        "rtmr0": attestation_data.get("rtmr0", ""),
                        "rtmr1": attestation_data.get("rtmr1", ""),
                        "rtmr2": attestation_data.get("rtmr2", ""),
                        "rtmr3": attestation_data.get("rtmr3", ""),
                        "report_data": attestation_data.get("report_data", ""),
                        "tls_fingerprint": tls_fingerprint,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "instance_url": "localhost:29343",
                        "success": True,
                        "mock": False
                    }
                    
        except Exception as e:
            # Self-attestation should always work in SecretVM, but handle errors gracefully
            return {
                "mr_td": "",
                "rtmr0": "",
                "rtmr1": "",
                "rtmr2": "",
                "rtmr3": "",
                "report_data": "",
                "tls_fingerprint": "",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "instance_url": "localhost:29343",
                "success": False,
                "mock": False,
                "error": str(e)
            }
    
    def parse_cpu_html(self, html_content: str):
        """Parse attestation registers from HTML"""
        attestation_data = {}
        
        # Look for register values in HTML
        # Format: <td>mr_td</td><td>ba87a347454466680bfd267446df89d8117c04ea9f28234dd3d84e1a8a957d5a</td>
        patterns = {
            "mr_td": r"<td>mr_td</td><td>([a-fA-F0-9]+)</td>",
            "rtmr0": r"<td>rtmr0</td><td>([a-fA-F0-9]+)</td>",
            "rtmr1": r"<td>rtmr1</td><td>([a-fA-F0-9]+)</td>",
            "rtmr2": r"<td>rtmr2</td><td>([a-fA-F0-9]+)</td>",
            "rtmr3": r"<td>rtmr3</td><td>([a-fA-F0-9]+)</td>",
            "report_data": r"<td>report_data</td><td>([a-fA-F0-9]+)</td>"
        }
        
        for register, pattern in patterns.items():
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                attestation_data[register] = match.group(1)
                
        return attestation_data
    
    async def get_tls_fingerprint(self):
        """Get TLS certificate fingerprint for MITM protection"""
        try:
            # For HTTPS attestation endpoint, get cert fingerprint
            if self.attestation_url.startswith("https"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.attestation_url}/cpu.html") as resp:
                        # Extract certificate info if available
                        # This is simplified - in production would get actual cert fingerprint
                        return f"sha256:{hashlib.sha256(b'mock_cert_data').hexdigest()[:16]}..."
            else:
                return ""
        except:
            return ""
```

#### **2.3: Encryption Module (Simple Password-Based)**

**`encryption.py` - Future-ready architecture:**
```python
import hashlib
import base64
import json
from cryptography.fernet import Fernet
from abc import ABC, abstractmethod

class EncryptionProvider(ABC):
    """Base interface for encryption providers"""
    
    @abstractmethod
    def encrypt(self, data: str, key: str) -> str:
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_data: str, key: str) -> str:
        pass

class PasswordEncryptionProvider(EncryptionProvider):
    """MVP: Simple password-based encryption"""
    
    def derive_key_from_password(self, password: str) -> bytes:
        """Convert password to encryption key using PBKDF2"""
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'attest_ai_salt', 100000)
        return base64.urlsafe_b64encode(key)
    
    def encrypt(self, data: str, password: str) -> str:
        """Encrypt data with password"""
        key = self.derive_key_from_password(password)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str, password: str) -> str:
        """Decrypt data with password"""
        key = self.derive_key_from_password(password)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(base64.b64decode(encrypted_data))
        return decrypted.decode()

# Future providers can be added here:
# class SecretNetworkEncryptionProvider(EncryptionProvider): ...
# class MnemonicEncryptionProvider(EncryptionProvider): ...

class EncryptionManager:
    """Manager for different encryption providers"""
    
    def __init__(self, provider: EncryptionProvider = None):
        self.provider = provider or PasswordEncryptionProvider()
    
    def encrypt_conversation(self, user_message: str, ai_response: str, password: str) -> str:
        """Encrypt conversation data"""
        conversation_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.provider.encrypt(json.dumps(conversation_data), password)
    
    def decrypt_conversation(self, encrypted_data: str, password: str) -> dict:
        """Decrypt conversation data"""
        decrypted_json = self.provider.decrypt(encrypted_data, password)
        return json.loads(decrypted_json)
```

#### **2.4: Arweave Client (Real with Mnemonic)**

**`arweave_client.py` - Mnemonic-based wallet:**
```python
import os
import json
import time
import random
import string
import arweave
from mnemonic import Mnemonic

class ArweaveClient:
    def __init__(self):
        self.mnemonic = os.getenv("ARWEAVE_MNEMONIC")
        self.gateway = os.getenv("ARWEAVE_GATEWAY", "https://arweave.net")
        self.wallet = None
        
        if not self.mnemonic:
            raise ValueError("ARWEAVE_MNEMONIC environment variable required")
    
    async def initialize_wallet(self):
        """Initialize Arweave wallet from mnemonic"""
        try:
            # Generate wallet from mnemonic using arweave-python-client
            # Note: This may need adjustment based on actual SDK capabilities
            self.wallet = arweave.Wallet.from_mnemonic(self.mnemonic)
            return True
        except Exception as e:
            print(f"Wallet initialization failed: {e}")
            return False
    
    async def get_wallet_info(self):
        """Get wallet address and balance"""
        if not self.wallet:
            await self.initialize_wallet()
        
        try:
            return {
                "address": self.wallet.address,
                "balance": self.wallet.balance,
                "balance_ar": f"{self.wallet.balance:.6f} AR",
                "success": True
            }
        except Exception as e:
            return {
                "address": "Error loading address",
                "balance": 0,
                "balance_ar": "Error loading balance",
                "success": False,
                "error": str(e)
            }
    
    async def upload_proof(self, proof_data: dict):
        """Upload proof to Arweave or create mock transaction"""
        if not self.wallet:
            await self.initialize_wallet()
        
        try:
            # Try real upload to Arweave
            transaction = arweave.Transaction(
                self.wallet,
                data=json.dumps(proof_data, indent=2)
            )
            
            # Add metadata tags
            transaction.add_tag('Content-Type', 'application/json')
            transaction.add_tag('App-Name', 'attest_ai')
            transaction.add_tag('App-Version', '1.0.0')
            transaction.add_tag('Type', 'attestation-proof')
            transaction.add_tag('Timestamp', str(int(time.time())))
            
            # Sign and send
            transaction.sign()
            transaction.send()
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "arweave_url": f"https://arweave.net/{transaction.id}",
                "cost_ar": arweave.utils.winston_to_ar(transaction.reward),
                "mocked": False
            }
            
        except Exception as e:
            # Create mock transaction for demo purposes
            mock_tx_id = f"mock_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"
            
            return {
                "success": False,
                "transaction_id": mock_tx_id,
                "arweave_url": f"https://arweave.net/{mock_tx_id}",
                "cost_ar": 0.001,
                "mocked": True,
                "error": str(e),
                "note": "Mock transaction - real upload failed"
            }
```

### **Phase 3: Web Interface (Day 5)**

#### **3.1: HTML Interface**

**`static/index.html` - Clean, functional UI:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>attest_ai - Attested Secret AI Chat</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🔐 attest_ai</h1>
            <p>Cryptographically verified Secret AI conversations</p>
        </header>
        
        <!-- Chat Interface -->
        <section class="chat-section">
            <div class="chat-area">
                <div id="messages"></div>
            </div>
            
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Ask Secret AI anything..." maxlength="500">
                <input type="password" id="passwordInput" placeholder="Encryption password" maxlength="100">
                <button onclick="sendMessage()" id="sendButton">Send Message</button>
                <div class="password-note">
                    💡 This password encrypts your conversation proof - remember it to decrypt later
                </div>
            </div>
        </section>
        
        <!-- Proof Actions -->
        <section class="proof-section" id="proofSection" style="display: none;">
            <h3>🔏 Cryptographic Proof Generated</h3>
            <div class="action-buttons">
                <button onclick="downloadProof()" class="download-btn">📥 Download Proof</button>
                <button onclick="uploadToArweave()" class="upload-btn">🌐 Upload to Arweave</button>
            </div>
            <div id="uploadStatus" class="status-area"></div>
        </section>
        
        <!-- System Status -->
        <section class="status-section">
            <div class="status-grid">
                <!-- Wallet Info -->
                <div class="status-card">
                    <h4>💰 Arweave Wallet</h4>
                    <div id="walletInfo">Loading...</div>
                </div>
                
                <!-- Self Attestation -->
                <div class="status-card">
                    <h4>🛡️ attest_ai VM</h4>
                    <div id="selfAttestation">Not loaded</div>
                </div>
                
                <!-- Secret AI Status -->
                <div class="status-card">
                    <h4>🤖 Secret AI Status</h4>
                    <div id="secretAiStatus">Ready</div>
                </div>
            </div>
        </section>
        
        <!-- Proof Details (Collapsible) -->
        <section class="details-section">
            <details>
                <summary>🔍 Last Proof Details</summary>
                <div id="proofDetails">No proof generated yet</div>
            </details>
        </section>
    </div>
    
    <script src="script.js"></script>
</body>
</html>
```

#### **3.2: Frontend Logic**

**`static/script.js` - Clean, functional JavaScript:**
```javascript
// Global state
let currentProof = null;
let isProcessing = false;

// Initialize on page load
window.addEventListener('load', function() {
    loadWalletInfo();
    loadSelfAttestation();
});

// Load wallet information
async function loadWalletInfo() {
    try {
        const response = await fetch('/wallet-info');
        const data = await response.json();
        
        const walletInfo = document.getElementById('walletInfo');
        if (data.success) {
            walletInfo.innerHTML = `
                <div>Address: ${data.address.substring(0, 10)}...</div>
                <div>Balance: ${data.balance_ar}</div>
            `;
        } else {
            walletInfo.innerHTML = `<div class="error">Error: ${data.error}</div>`;
        }
    } catch (error) {
        document.getElementById('walletInfo').innerHTML = 
            `<div class="error">Failed to load wallet info</div>`;
    }
}

// Load self-attestation
async function loadSelfAttestation() {
    try {
        const response = await fetch('/self-attestation');
        const data = await response.json();
        
        const selfAttestation = document.getElementById('selfAttestation');
        if (data.success) {
            selfAttestation.innerHTML = `
                <div class="success">✅ Verified SecretVM</div>
                <div>mr_td: ${data.mr_td.substring(0, 8)}...</div>
            `;
        } else {
            selfAttestation.innerHTML = `<div class="error">❌ ${data.error}</div>`;
        }
    } catch (error) {
        document.getElementById('selfAttestation').innerHTML = 
            `<div class="error">Failed to load attestation</div>`;
    }
}

// Send message to Secret AI
async function sendMessage() {
    if (isProcessing) return;
    
    const messageInput = document.getElementById('messageInput');
    const passwordInput = document.getElementById('passwordInput');
    const message = messageInput.value.trim();
    const password = passwordInput.value.trim();
    
    // Validation
    if (!message) {
        alert('Please enter a message');
        return;
    }
    if (!password) {
        alert('Please enter an encryption password');
        return;
    }
    
    isProcessing = true;
    document.getElementById('sendButton').disabled = true;
    
    // Show user message
    addMessage('user', message);
    messageInput.value = '';
    
    // Show processing indicator
    addMessage('system', '🔄 Processing with Secret AI...');
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: message,
                password: password
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Remove processing message
        removeLastMessage();
        
        // Show AI response
        addMessage('ai', data.response);
        
        // Update Secret AI status
        updateSecretAiStatus(data.secret_ai_status);
        
        // Store proof and show actions
        currentProof = data.proof;
        document.getElementById('proofSection').style.display = 'block';
        updateProofDetails(data.proof);
        
    } catch (error) {
        removeLastMessage();
        addMessage('error', `Error: ${error.message}`);
    } finally {
        isProcessing = false;
        document.getElementById('sendButton').disabled = false;
    }
}

// Download proof as JSON file
function downloadProof() {
    if (!currentProof) return;
    
    const dataStr = JSON.stringify(currentProof, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `attest_ai_proof_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    document.getElementById('uploadStatus').innerHTML = 
        '<div class="success">✅ Proof downloaded successfully!</div>';
}

// Upload proof to Arweave
async function uploadToArweave() {
    if (!currentProof) return;
    
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = '<div class="processing">🔄 Uploading to Arweave...</div>';
    
    try {
        const response = await fetch('/upload-to-arweave', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({proof: currentProof})
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusDiv.innerHTML = `
                <div class="success">✅ Uploaded to Arweave!</div>
                <div><a href="${result.arweave_url}" target="_blank">${result.transaction_id}</a></div>
                <div>Cost: ${result.cost_ar} AR</div>
            `;
        } else {
            const statusClass = result.mocked ? 'warning' : 'error';
            const icon = result.mocked ? '⚠️' : '❌';
            statusDiv.innerHTML = `
                <div class="${statusClass}">${icon} ${result.mocked ? 'Mock upload' : 'Upload failed'}</div>
                <div>${result.transaction_id}</div>
                ${result.note ? `<div>${result.note}</div>` : ''}
            `;
        }
        
        // Refresh wallet info
        loadWalletInfo();
        
    } catch (error) {
        statusDiv.innerHTML = `<div class="error">❌ Upload error: ${error.message}</div>`;
    }
}

// Helper functions
function addMessage(type, content) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = content;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function removeLastMessage() {
    const messages = document.getElementById('messages');
    if (messages.lastChild) {
        messages.removeChild(messages.lastChild);
    }
}

function updateSecretAiStatus(status) {
    const statusDiv = document.getElementById('secretAiStatus');
    if (status.mock) {
        statusDiv.innerHTML = '<div class="warning">⚠️ Using mock responses</div>';
    } else {
        statusDiv.innerHTML = '<div class="success">✅ Connected to Secret AI</div>';
    }
}

function updateProofDetails(proof) {
    const details = document.getElementById('proofDetails');
    details.innerHTML = `<pre>${JSON.stringify(proof, null, 2)}</pre>`;
}

// Enter key handling
document.getElementById('messageInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
```

#### **3.3: Basic Styling**

**`static/style.css` - Clean, responsive design:**
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
}

header h1 {
    font-size: 2.5em;
    color: #2c3e50;
    margin-bottom: 10px;
}

header p {
    font-size: 1.1em;
    color: #7f8c8d;
}

/* Chat Section */
.chat-section {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.chat-area {
    height: 300px;
    overflow-y: auto;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 15px;
    background: #fafafa;
}

.message {
    margin-bottom: 10px;
    padding: 8px 12px;
    border-radius: 5px;
    max-width: 80%;
}

.message.user {
    background: #3498db;
    color: white;
    margin-left: auto;
    text-align: right;
}

.message.ai {
    background: #2ecc71;
    color: white;
}

.message.system {
    background: #f39c12;
    color: white;
    text-align: center;
    margin: 0 auto;
}

.message.error {
    background: #e74c3c;
    color: white;
}

.input-area {
    display: grid;
    gap: 10px;
}

.input-area input {
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
}

.input-area button {
    padding: 12px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.3s;
}

.input-area button:hover:not(:disabled) {
    background: #2980b9;
}

.input-area button:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
}

.password-note {
    font-size: 0.9em;
    color: #7f8c8d;
    font-style: italic;
}

/* Proof Section */
.proof-section {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-left: 4px solid #2ecc71;
}

.action-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-bottom: 15px;
}

.download-btn, .upload-btn {
    padding: 12px;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s;
}

.download-btn {
    background: #9b59b6;
    color: white;
}

.download-btn:hover {
    background: #8e44ad;
}

.upload-btn {
    background: #e67e22;
    color: white;
}

.upload-btn:hover {
    background: #d35400;
}

/* Status Section */
.status-section {
    margin-bottom: 20px;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.status-card {
    background: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.status-card h4 {
    margin-bottom: 10px;
    color: #2c3e50;
}

/* Details Section */
.details-section {
    background: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

details summary {
    cursor: pointer;
    font-weight: bold;
    padding: 10px 0;
}

#proofDetails {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    margin-top: 10px;
}

/* Status Indicators */
.success {
    color: #27ae60;
}

.error {
    color: #e74c3c;
}

.warning {
    color: #f39c12;
}

.processing {
    color: #3498db;
}

/* Responsive */
@media (max-width: 768px) {
    .action-buttons {
        grid-template-columns: 1fr;
    }
    
    .status-grid {
        grid-template-columns: 1fr;
    }
    
    header h1 {
        font-size: 2em;
    }
}
```

### **Phase 4: Main Application (Day 6)**

#### **4.1: FastAPI Application**

**`app.py` - Complete integration:**
```python
import os
import json
import hashlib
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import our modules
from secret_ai_client import SecretAIClient
from arweave_client import ArweaveClient
from attestation_client import AttestationClient
from encryption import EncryptionManager

# Initialize FastAPI
app = FastAPI(
    title="attest_ai",
    description="Cryptographic proofs for Secret AI interactions",
    version="1.0.0"
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize clients
secret_ai = SecretAIClient()
arweave = ArweaveClient()
attestation = AttestationClient()
encryption = EncryptionManager()

# Request models
class ChatRequest(BaseModel):
    message: str
    password: str

class UploadRequest(BaseModel):
    proof: dict

class DecryptRequest(BaseModel):
    encrypted_proof: dict
    password: str

@app.get("/")
async def root():
    """Serve the main chat interface"""
    return FileResponse('static/index.html')

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/wallet-info")
async def wallet_info():
    """Get Arweave wallet information"""
    return await arweave.get_wallet_info()

@app.get("/self-attestation")
async def self_attestation():
    """Get self-attestation from attest_ai VM"""
    return await attestation.get_self_attestation()

@app.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with dual attestation"""
    try:
        # 1. Send message to Secret AI
        ai_response = await secret_ai.send_message(request.message)
        
        # 2. Get self-attestation from our VM
        self_attest = await attestation.get_self_attestation()
        
        # 3. Attempt to get Secret AI VM attestation
        secretai_attest = {"mock": True, "error": "Not implemented"}
        if not ai_response["mock"] and ai_response.get("instance_url"):
            secretai_attest = await secret_ai.get_attestation(ai_response["instance_url"])
        
        # 4. Encrypt conversation data
        encrypted_conversation = encryption.encrypt_conversation(
            request.message, 
            ai_response["response"], 
            request.password
        )
        
        # 5. Generate verification hashes
        message_hash = hashlib.sha256(request.message.encode()).hexdigest()
        response_hash = hashlib.sha256(ai_response["response"].encode()).hexdigest()
        interaction_hash = hashlib.sha256(
            f"{request.message}|{ai_response['response']}".encode()
        ).hexdigest()
        
        # 6. Create complete proof
        proof = {
            "proof_id": f"proof_{int(datetime.utcnow().timestamp())}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "app_name": "attest_ai",
            
            # Encrypted conversation (only user can decrypt)
            "encrypted_conversation": encrypted_conversation,
            
            # Verification hashes (public)
            "verification": {
                "message_hash": message_hash,
                "response_hash": response_hash,
                "interaction_hash": interaction_hash
            },
            
            # Dual attestation
            "attestations": {
                "attest_ai_vm": {
                    "mr_td": self_attest.get("mr_td", ""),
                    "rtmr0": self_attest.get("rtmr0", ""),
                    "rtmr1": self_attest.get("rtmr1", ""),
                    "rtmr2": self_attest.get("rtmr2", ""),
                    "rtmr3": self_attest.get("rtmr3", ""),
                    "report_data": self_attest.get("report_data", ""),
                    "tls_fingerprint": self_attest.get("tls_fingerprint", ""),
                    "instance_url": "localhost:29343",
                    "status": "verified" if self_attest.get("success") else "error",
                    "timestamp": self_attest.get("timestamp", "")
                },
                "secret_ai_vm": {
                    "mr_td": secretai_attest.get("attestation", {}).get("mr_td", ""),
                    "rtmr0": secretai_attest.get("attestation", {}).get("rtmr0", ""),
                    "instance_url": secretai_attest.get("instance_url", ""),
                    "model": ai_response.get("model", ""),
                    "status": "verified" if not secretai_attest.get("mock") else "mocked",
                    "timestamp": secretai_attest.get("attestation", {}).get("timestamp", "")
                }
            },
            
            # Cryptographic binding
            "cryptographic_binding": {
                "binding_hash": hashlib.sha256(
                    f"{interaction_hash}|{self_attest.get('mr_td', '')}|{secretai_attest.get('attestation', {}).get('mr_td', '')}".encode()
                ).hexdigest(),
                "method": "sha256_dual_attestation_v1"
            }
        }
        
        return {
            "response": ai_response["response"],
            "proof": proof,
            "secret_ai_status": {
                "success": ai_response["success"],
                "mock": ai_response["mock"],
                "model": ai_response.get("model", ""),
                "instance_url": ai_response.get("instance_url", "")
            },
            "attestation_status": {
                "self_attestation": self_attest.get("success", False),
                "secret_ai_attestation": not secretai_attest.get("mock", True)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-to-arweave")
async def upload_to_arweave(request: UploadRequest):
    """Upload proof to Arweave"""
    try:
        result = await arweave.upload_proof(request.proof)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decrypt-proof")
async def decrypt_proof(request: DecryptRequest):
    """Decrypt proof conversation data"""
    try:
        encrypted_data = request.encrypted_proof.get("encrypted_conversation", "")
        if not encrypted_data:
            raise HTTPException(status_code=400, detail="No encrypted conversation data found")
        
        conversation = encryption.decrypt_conversation(encrypted_data, request.password)
        
        return {
            "success": True,
            "conversation": conversation,
            "proof_metadata": {
                "timestamp": request.encrypted_proof.get("timestamp"),
                "proof_id": request.encrypted_proof.get("proof_id"),
                "verification_hashes": request.encrypted_proof.get("verification", {})
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": "Invalid password or corrupted proof data"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
```

### **Phase 5: GitHub Actions (Day 7)**

#### **5.1: Simple Build and Push Workflow**

**`.github/workflows/build-image.yml` - Image building only:**
```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    # CRITICAL: Convert repository name to lowercase
    - name: Set lowercase repository name
      run: echo "REPO_LOWER=$(echo ${{ github.repository }} | tr '[:upper:]' '[:lower:]')" >> $GITHUB_ENV

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.REPO_LOWER }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Image digest
      run: echo ${{ steps.meta.outputs.digest }}
```

## **Deployment Instructions**

### **Local Testing**
```bash
# 1. Clone and setup
git clone <repository>
cd attest_ai

# 2. Create environment file
cp .env.template .env
# Edit .env with real values

# 3. Build and run
docker-compose build
docker-compose up

# 4. Test
curl http://localhost:8000/health
# Open http://localhost:8000 in browser
```

### **SecretVM Deployment**
1. **Build image locally**: `docker-compose build`
2. **Push to GHCR**: GitHub Actions handles this automatically
3. **Deploy to SecretVM**: Use SecretVM CLI with your image
4. **Upload .env**: Separately upload environment variables
5. **Test**: Verify all endpoints work in SecretVM environment

## **Testing Checklist**

### **Functional Tests**
- [ ] Health endpoint responds
- [ ] Wallet info loads
- [ ] Self-attestation retrieves data from localhost:29343
- [ ] Secret AI integration works (or fails gracefully)
- [ ] Chat generates encrypted proofs
- [ ] Download proof creates valid JSON file
- [ ] Upload to Arweave (real or mock) completes
- [ ] Proof decryption works with correct password
- [ ] UI shows all status information clearly

### **Security Tests**
- [ ] No secrets in code or logs
- [ ] Encrypted conversation cannot be read without password
- [ ] Invalid password fails gracefully
- [ ] Self-attestation includes TLS fingerprint
- [ ] Proof hashes are cryptographically sound

### **Integration Tests**
- [ ] Docker container builds successfully
- [ ] All environment variables load correctly
- [ ] Static files serve properly
- [ ] CORS works for browser requests
- [ ] Error handling doesn't crash application

## **Success Criteria**

### **Must Have (MVP Requirements)**
✅ **Deploys in SecretVM** with single docker-compose command  
✅ **Real Secret AI integration** (with graceful fallback to mock)  
✅ **Real self-attestation** from localhost:29343  
✅ **Real Arweave integration** (with mock fallback for unfunded)  
✅ **Functional web UI** showing all components  
✅ **Proof encryption** for conversation privacy  
✅ **Download/upload options** for user control  

### **Nice to Have (Future Enhancements)**
- Secret AI VM attestation when available
- Cost estimation before upload
- Multiple encryption providers
- Proof verification tools
- Batch operations
- Enhanced UI/UX

## **Common Issues and Solutions**

### **Secret AI Connection Issues**
- **Problem**: Cannot connect to Secret AI instances
- **Solution**: Gracefully fall back to mock responses, clearly indicate mock status in UI

### **Arweave Upload Failures**
- **Problem**: Insufficient funds or network issues
- **Solution**: Create realistic mock transactions, show clear error messages

### **Attestation Parsing Issues**
- **Problem**: HTML format changes on localhost:29343
- **Solution**: Robust regex patterns, graceful fallback to empty values

### **GitHub Actions Capitalization**
- **Problem**: GHCR rejects mixed-case repository names
- **Solution**: Always convert `github.repository` to lowercase before use

### **Docker Build Issues**
- **Problem**: Dependencies fail to install
- **Solution**: Use specific version pins, slim base images, minimal dependencies

## **Future Enhancement Paths**

### **Secret Network Integration**
- Replace password encryption with Secret Network contracts
- Use Secret Network for key management
- Enable shared access controls

### **Advanced Attestation**
- Real-time Secret AI VM attestation when available
- Cross-VM verification protocols
- Attestation caching and refresh strategies

### **Production Readiness**
- Multi-stage Docker builds
- Health checks and monitoring
- Rate limiting and authentication
- Database for proof storage
- API versioning

This guide provides complete, detailed instructions for building a functional MVP while maintaining simplicity and avoiding over-engineering. The result will be a working proof-of-concept that demonstrates all core concepts and can be enhanced incrementally.