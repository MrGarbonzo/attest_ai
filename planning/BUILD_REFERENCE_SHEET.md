# attest_ai Build Reference Sheet

**Companion document to UNIFIED_AI_IMPLEMENTATION_GUIDE.md**  
**Purpose:** Quick reference for real implementation examples and critical details during build

---

## **🔥 Critical Implementation References**

### **Secret AI SDK - Real Integration Patterns**

#### **Environment & Setup**
```bash
# From secretAI-setting-up-envireonment.txt
export SECRET_AI_API_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1

# Required packages (from secret-ai-sdk requirements.txt)
secret-sdk>=1.8.1
langchain==0.3.13
langchain-ollama==0.2.2
```

#### **Exact SDK Usage Pattern**
```python
# From secret_ai_getting_started.py - EXACT working code
from secret_ai_sdk.secret_ai import ChatSecret
from secret_ai_sdk.secret import Secret

secret_client = Secret()
models = secret_client.get_models()
urls = secret_client.get_urls(model=models[0])

secret_ai_llm = ChatSecret(
    base_url=urls[0],
    model=models[0], 
    temperature=1.0
)

messages = [
    ("system", "You are my therapist. Help me with my issues."),
    ("human", "I miss my cat."),
]

response = secret_ai_llm.invoke(messages, stream=False)
print(response.content)
```

#### **SDK Configuration Details**
```python
# From _config.py - Default values to use
SECRET_CHAIN_ID_DEFAULT = 'pulsar-3'
SECRET_WORKER_SMART_CONTRACT_DEFAULT = 'secret18cy3cgnmkft3ayma4nr37wgtj4faxfnrnngrlq'
SECRET_NODE_URL_DEFAULT = 'https://pulsar.lcd.secretnodes.com'

# Environment variables the SDK expects
SECRET_AI_API_KEY = 'SECRET_AI_API_KEY'
SECRET_CHAIN_ID = 'SECRET_CHAIN_ID' 
SECRET_NODE_URL = 'SECRET_NODE_URL'
```

#### **Attestation Method Reality Check**
```python
# From secret_ai.py - get_attestation() exists but returns empty
def get_attestation(self) -> Dict:
    """ method returns the attestation report"""
    return {} # Not implemented yet
```
**CRITICAL:** Secret AI attestation is NOT implemented yet - plan for mock fallback!

---

## **🔗 Arweave Integration - Real Working Examples**

### **Wallet Management (JWK Format)**
```python
# From test_wallet.py - Proven working pattern
from arweave import Wallet
import json

# Load from JWK data (perfect for environment variables)
def test_create_from_data():
    with open("test_jwk_file.json", 'r') as f:
        from_data_wallet = Wallet.from_data(json.load(f))
    assert from_data_wallet.owner == wallet.owner
```

### **Real JWK Structure**
```json
// From test_jwk_file.json - Use this format for ARWEAVE_WALLET_JWK
{
  "kty": "RSA",
  "e": "AQAB",
  "n": "5Vcm1ZzaBzDJOHCybxKF0X...", // Public key modulus
  "d": "BXEK79iX58HFlHxAD5id6j...", // Private exponent
  "p": "-QJ6vuRu8SUMf9vhWU2WO...", // First prime factor
  "q": "68dRdFtM0CBIcQ5gtf45z...", // Second prime factor
  "dp": "H_z8jbdEtT_AKlCx00oPS...", // d mod (p-1)
  "dq": "DPdFD3UF4FwmH7F-uANnA...", // d mod (q-1)
  "qi": "Kcu2hX-ZciY3aEYTr_9mq..."  // q^(-1) mod p
}
```

### **Transaction Creation & Upload**
```python
# From transactions.py - Real working upload pattern
from arweave.arweave_lib import Wallet, Transaction

wallet = Wallet(jwk_file)
tx = Transaction(wallet, data=b'cheese is nice')
tx.add_tag('Test tx', "python-lib")
tx.sign()
tx.send()
```

### **Balance & Cost Checking**
```python
# From test_wallet.py - Balance checking pattern
@responses.activate
def test_get_balance():
    balance = wallet.balance  # Returns float in AR
    assert balance == winston_to_ar(mock_balance)

# From arweave-http-api.txt - Cost estimation
GET /price/{bytes}/{target}  # Get cost for data size
```

### **Key HTTP API Endpoints**
```bash
# From arweave-http-api.txt - Essential endpoints
GET  /info                     # Network status
GET  /wallet/{address}/balance # Wallet balance
GET  /tx_anchor               # Get transaction anchor
POST /tx                      # Submit transaction
GET  /tx/{id}                 # Get transaction
GET  /tx/{id}/status          # Transaction status
```

---

## **🛡️ SecretVM Attestation - Real Data Formats**

### **Self-Attestation URL**
```bash
# From secretVM_full_verification.txt
http://localhost:29343/cpu.html  # Always available in SecretVM
```

### **Expected Register Structure**
```bash
# From secretVM_full_verification.txt - Sample output format
MRTD: ba87a347454466680bfd267446df89d8117c04ea9f28234dd3d84e1a8a957d5a
RTMR0: b6941a8c47be7050bdba6220b915e141c5e33b9c32d9446f743fe5e73cc7612f
RTMR1: 4afcac4edf01c068d1a623ec69519c9c3a7abc91e3e71a578a5ba346e60c0231
RTMR2: c8f67a1007adb5759cbb5d57b2136bcc54c2d2e4d3bac763b9de4cab78729752
RTMR3: 9959d12cfe7a120fe363e47e7accb9bd15fba4665bdb8b5186a2b57d7bf19996
```

### **HTML Parsing Pattern**
```html
<!-- Expected format from cpu.html -->
<td>mr_td</td><td>ba87a347454466680bfd267446df89d8117c04ea9f28234dd3d84e1a8a957d5a</td>
<td>rtmr0</td><td>b6941a8c47be7050bdba6220b915e141c5e33b9c32d9446f743fe5e73cc7612f</td>
```

### **TLS Fingerprint Capture**
```bash
# From secretVM_full_verification.txt
# Rule out Man-in-the-Middle Attacks
# Verify that the first part of the report_data field matches 
# the fingerprint of the TLS certificate
```

---

## **🐳 Docker & FastAPI - Proven Patterns**

### **Simple Dockerfile (from fast-api-docker.txt)**
```dockerfile
FROM python:3.9
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

### **FastAPI Best Practices**
```python
# From fast-api-docker.txt - Use exec form for proper signal handling
CMD ["fastapi", "run", "app/main.py", "--port", "80"]  # ✅ Correct
# CMD fastapi run app/main.py --port 80                # ❌ Wrong

# Docker cache optimization - copy requirements first
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app  # Copy app code last for better caching
```

### **Docker Best Practices (from docker-best-practices.txt)**
```dockerfile
# Use slim base images
FROM python:3.11-slim

# Combine RUN commands to reduce layers
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Use .dockerignore
*.md
.git
__pycache__
*.pyc
```

---

## **⚙️ SecretVM CLI Commands**

### **Authentication**
```bash
# From Authentication Commands.txt
secretvm-cli auth login -w <wallet-address>
secretvm-cli auth logout
secretvm-cli status  # Check login status
```

### **VM Management**
```bash
# From Virtual Machine Commands.txt
secretvm-cli vm create -n "attest-ai-mvp" -t "medium" -d "./docker-compose.yaml"
secretvm-cli vm ls                    # List VMs
secretvm-cli vm status <vmUUID>       # Detailed VM info
secretvm-cli vm start <vmId>          # Start VM
secretvm-cli vm stop <vmId>           # Stop VM
secretvm-cli vm remove <vmId>         # Delete VM
secretvm-cli vm logs <vmId>           # View logs
secretvm-cli vm attestation <vmId>    # Get CPU attestation
```

---

## **🔧 Critical Implementation Notes**

### **Secret AI Reality Check**
- ✅ **Models discovery works**: `secret_client.get_models()`
- ✅ **URL discovery works**: `secret_client.get_urls(model)`
- ✅ **Chat invocation works**: `ChatSecret.invoke(messages)`
- ❌ **Attestation NOT implemented**: `get_attestation()` returns `{}`
- **Strategy**: Always attempt real, gracefully fall back to mock

### **Arweave Wallet Strategy**
- ✅ **JWK format in environment variable works**
- ✅ **Wallet.from_data() is the correct method**
- ✅ **Transaction creation and signing works**
- ⚠️ **Upload may fail if unfunded** - handle gracefully
- **Strategy**: Try real upload first, mock if fails

### **Self-Attestation Reality**
- ✅ **localhost:29343/cpu.html always available in SecretVM**
- ✅ **HTML parsing required** for register extraction
- ✅ **TLS fingerprint capture needed** for security
- **Strategy**: Always real data, never mock (should always work)

### **Docker Build Optimization**
- ✅ **Copy requirements.txt first** for better caching
- ✅ **Use exec form CMD** for proper signal handling
- ✅ **Use slim base images** to reduce size
- ✅ **Combine RUN commands** to reduce layers

---

## **🔧 Critical Missing Implementation Details**

### **Arweave Python SDK - Real Method Names**

#### **Wallet Creation from JWK Data**
```python
# From arweave_lib.py - EXACT method to use
@classmethod
def from_data(cls, jwk_data):
    wallet = cls.__new__(cls)
    wallet.jwk_data = jwk_data
    wallet._set_jwk_params()
    return wallet

# Usage:
wallet_data = json.loads(os.getenv("ARWEAVE_WALLET_JWK"))
wallet = Wallet.from_data(wallet_data)
```

#### **Transaction Methods and Properties**
```python
# From arweave_lib.py - Real working transaction pattern
tx = Transaction(wallet, data=b'your_data_here')
tx.add_tag('Content-Type', 'application/json')
tx.add_tag('App-Name', 'attest_ai')
tx.sign()  # Creates signature and ID
tx.send()  # Submits to network

# Properties available:
tx.id          # Transaction ID (generated after sign())
tx.reward      # Cost in winston
tx.data_size   # Size of data
tx.owner       # Wallet public key
tx.signature   # Transaction signature
```

#### **Balance and Cost Methods**
```python
# From arweave_lib.py - Real balance checking
balance_ar = wallet.balance        # Returns float in AR
balance_winston = wallet.balance   # Internally converts

# Cost estimation
cost_winston = tx.get_reward(data_size_bytes)
cost_ar = winston_to_ar(cost_winston)
```

#### **Utility Functions Available**
```python
# From utils.py - Essential conversion functions
from arweave.utils import winston_to_ar, ar_to_winston, owner_to_address

ar_amount = winston_to_ar("1000000000000")  # "1.0" 
winston_amount = ar_to_winston("1.0")        # "1000000000000"
address = owner_to_address(public_key_n_value)
```

---

### **Secret AI SDK - Complete Authentication Pattern**

#### **Real Client Creation (from _client.py)**
```python
# From _client.py - How SecretAI clients are actually created
from secret_ai_sdk._client import SecretAIClient, SecretAIAsyncClient

# The Secret AI SDK uses Ollama clients with Bearer auth
class SecretAIClient(OllamaClient):
    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None, **kwargs):
        if api_key is None:
            api_key = os.getenv(_config.API_KEY)  # 'SECRET_AI_API_KEY'
        
        auth: dict = {'Authorization': f'Bearer {api_key}'}
        kwargs['headers'] = auth
        super().__init__(host, **kwargs)
```

#### **Exact Test Pattern (from test_secret_ai.py)**
```python
# Known working values for testing
TEST_KNOWN_API_KEY = 'bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1'
TEST_KNOWN_MODEL = 'deepseek-r1:70b'

# Exact working test pattern
os.environ['SECRET_AI_API_KEY'] = TEST_KNOWN_API_KEY
secret_client = Secret()
models = secret_client.get_models()
urls = secret_client.get_urls(model=TEST_KNOWN_MODEL)

secret_ai_llm = ChatSecret(
    base_url=urls[0],
    model=TEST_KNOWN_MODEL,
    temperature=1.0
)

messages = [
    ("system", "You are a helpful assistant that translates English to French."),
    ("human", "I love programming."),
]
response = secret_ai_llm.invoke(messages)
```

---

### **ANS Standards - Arweave Tagging Best Practices**

#### **ANS-112 Digital Provenance (Perfect for attest_ai!)**
```python
# From ANS-112.md - Ideal tagging standard for our use case
transaction.add_tag('Data-Protocol', 'Provenance-Confirmation')
transaction.add_tag('Hashing-Algo', 'sha256')  # Default
transaction.add_tag('Data-Hash', proof_hash)
transaction.add_tag('Model', 'deepseek-r1')  # AI model used
transaction.add_tag('Uploaded-For', 'attestation-proof')
# Optional but useful:
transaction.add_tag('Prompt-Hash', user_message_hash)
```

#### **Our attest_ai Specific Tags**
```python
# Combine ANS-112 with our specific needs
transaction.add_tag('Data-Protocol', 'Provenance-Confirmation')
transaction.add_tag('Content-Type', 'application/json')
transaction.add_tag('App-Name', 'attest_ai')
transaction.add_tag('App-Version', '1.0.0')
transaction.add_tag('Type', 'attestation-proof')
transaction.add_tag('Attestation-Type', 'dual-vm')
transaction.add_tag('Model', ai_model_name)
transaction.add_tag('Data-Hash', proof_hash)
transaction.add_tag('Unix-Time', str(int(time.time())))
```

#### **ANS-104 Bundling (Future Enhancement)**
```python
# From ANS-104.md - For bundling multiple proofs later
transaction.add_tag('Bundle-Format', 'binary')
transaction.add_tag('Bundle-Version', '2.0.0')
```

---

### **Complete Error Handling Patterns**

#### **Arweave Transaction Error Handling**
```python
# From arweave_lib.py - Real exception handling
from arweave.arweave_lib import ArweaveTransactionException

try:
    balance = wallet.balance
except ArweaveTransactionException as e:
    # Handle specific Arweave errors
    logger.error(f"Arweave error: {e}")
    return mock_balance_response()
except Exception as e:
    # Handle network/other errors
    logger.error(f"Network error: {e}")
    return mock_balance_response()
```

#### **Secret AI Error Handling**
```python
# From secret_ai_sdk - Real exception types
from secret_ai_sdk.secret_ai_ex import SecretAIAPIKeyMissingError

try:
    secret_client = Secret()
    models = secret_client.get_models()
except SecretAIAPIKeyMissingError:
    raise ValueError("SECRET_AI_API_KEY environment variable required")
except Exception as e:
    logger.warning(f"Secret AI unavailable: {e}")
    return mock_models_response()
```

---

### **Proven File Structure Patterns**

#### **From arweave-python-sdk test structure**
```
test/
├── test_wallet.py         # Wallet functionality tests
├── transactions.py        # Transaction creation/upload
├── test_jwk_file.json    # Real JWK format example
├── testfile0.bin         # Binary data testing
└── test_utils.py         # Utility function tests
```

#### **From secret-ai-sdk structure**
```
secret_ai_sdk/
├── secret.py              # Smart contract interaction
├── secret_ai.py           # Chat interface (extends ChatOllama)
├── _client.py             # HTTP client with auth
├── _config.py             # Environment variable names
└── secret_ai_ex.py        # Exception definitions
```

---

### **Production Deployment Considerations**

#### **From Arweave SDK - Large File Handling**
```python
# From transactions.py - Handle large data uploads
with open(file_path, "rb", buffering=0) as file_handler:
    tx = Transaction(wallet, file_handler=file_handler, file_path=file_path)
    tx.add_tag('Content-Type', 'application/bin')
    tx.sign()
    
    # Use uploader for large files
    uploader = get_uploader(tx, file_handler)
    while not uploader.is_complete:
        uploader.upload_chunk()
        logger.info(f"{uploader.pct_complete}% complete")
```

#### **Semantic Versioning (from BP-106.md)**
```python
# Use semantic versioning for all components
APP_VERSION = "1.0.0"  # MAJOR.MINOR.PATCH
PROOF_VERSION = "1.0.0"
API_VERSION = "v1"

# Include in proof metadata
proof = {
    "version": PROOF_VERSION,
    "app_version": APP_VERSION,
    # ... rest of proof
}
```

---

## **🚨 Common Pitfalls to Avoid**

### **GitHub Actions Capitalization**
```yaml
# ❌ Wrong - github.repository may be MixedCase
image: ghcr.io/${{ github.repository }}

# ✅ Correct - always convert to lowercase
- name: Set lowercase repo name
  run: echo "REPO_LOWER=$(echo ${{ github.repository }} | tr '[:upper:]' '[:lower:]')" >> $GITHUB_ENV
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    tags: ghcr.io/${{ env.REPO_LOWER }}:latest
```

### **Environment Variable Handling**
```python
# ❌ Don't hardcode secrets
SECRET_AI_API_KEY = "real_key_here"

# ✅ Always use environment variables
SECRET_AI_API_KEY = os.getenv("SECRET_AI_API_KEY")
if not SECRET_AI_API_KEY:
    raise ValueError("SECRET_AI_API_KEY environment variable required")
```

### **Error Handling Strategy**
```python
# ❌ Don't crash on missing external services
response = secret_ai.get_attestation()  # Fails hard

# ✅ Graceful fallback with clear indication
try:
    response = secret_ai.get_attestation()
    if not response:
        response = create_mock_attestation()
except Exception:
    response = create_mock_attestation()
```

---

## **📋 Quick Implementation Checklist**

### **Secret AI Integration**
- [ ] Use exact SDK pattern from `secret_ai_getting_started.py`
- [ ] Handle missing attestation gracefully (not implemented)
- [ ] Include proper error handling for network issues
- [ ] Test with real Secret AI master key

### **Arweave Integration**
- [ ] Store JWK in environment variable as JSON string
- [ ] Use `Wallet.from_data(json.loads(jwk_data))`
- [ ] Add proper tags to transactions
- [ ] Implement mock fallback for unfunded uploads

### **Self-Attestation**
- [ ] Parse HTML from `localhost:29343/cpu.html`
- [ ] Extract mr_td, rtmr0-3 registers with regex
- [ ] Capture TLS fingerprint for security
- [ ] Cache results appropriately

### **Docker Deployment**
- [ ] Use slim Python base image
- [ ] Copy requirements.txt first for caching
- [ ] Use exec form CMD
- [ ] Test local build before SecretVM deployment

### **GitHub Actions**
- [ ] Convert repository name to lowercase
- [ ] Build and push to GHCR only (no deployment)
- [ ] Test image builds successfully

This reference sheet should be used alongside the main implementation guide for quick lookups of real working patterns and critical implementation details.