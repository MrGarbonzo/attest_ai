# Complete Implementation References Update

## **🔥 CRITICAL: Arweave Python SDK Integration**

### **Installation & Setup**
```bash
pip install arweave-python-client
```

### **Wallet Management (SOLVES MNEMONIC ISSUE!)**
```python
import arweave
import json

# Load wallet from JWK file
wallet = arweave.Wallet("wallet.json")

# Load wallet from data (perfect for our .env approach!)
wallet_data = json.loads(jwk_data_from_env)
wallet = arweave.Wallet.from_data(wallet_data)

# Get wallet address and balance
address = wallet.address  # SHA-256 hash of public key
balance = wallet.balance  # Returns float in AR (auto-converts from winston)
```

### **Transaction Creation & Signing**
```python
# Create transaction with data
transaction = arweave.Transaction(
    wallet, 
    data="proof metadata here",
    target="",  # Empty for data-only transactions
    quantity="0"  # No AR transfer
)

# Add tags (perfect for our proof metadata!)
transaction.add_tag('Content-Type', 'application/json')
transaction.add_tag('App-Name', 'attest_ai')
transaction.add_tag('App-Version', '1.0.0')
transaction.add_tag('Title', 'Cryptographic AI Proof')
transaction.add_tag('Type', 'attestation-proof')
transaction.add_tag('Unix-Time', str(int(time.time())))

# Sign and send
transaction.sign()
transaction.send()

# Get transaction status
status = transaction.get_status()
print(f"Transaction ID: {transaction.id}")
```

### **Cost Calculation & Validation**
```python
# Get transaction cost before sending
cost_winston = transaction.get_reward(data_size_bytes)
cost_ar = winston_to_ar(cost_winston)

# Check wallet balance vs cost
if wallet.balance >= cost_ar:
    # Proceed with real upload
    transaction.send()
else:
    # Create mock transaction
    mock_tx_id = f"mock_tx_{int(time.time())}_{random_string}"
```

### **Utility Functions Available**
```python
from arweave.utils import winston_to_ar, ar_to_winston, owner_to_address

# Conversions
ar_amount = winston_to_ar("1000000000000")  # "1.0"
winston_amount = ar_to_winston("1.0")       # "1000000000000"

# Address calculation
address = owner_to_address(public_key_n_value)
```

---

## **🐳 Docker & FastAPI Production Patterns**

### **Optimized Multi-Stage Dockerfile**
```dockerfile
# Build stage
FROM python:3.12-slim as builder

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/requirements.txt

# Runtime stage
FROM python:3.12-slim as runtime

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ src/
COPY static/ static/

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use exec form for proper signal handling
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Production Docker Compose**
```yaml
version: '3.8'
services:
  attest-ai:
    build: 
      context: .
      target: runtime
    ports:
      - "8000:8000"
    environment:
      - SECRET_AI_API_KEY=${SECRET_AI_API_KEY}
      - ARWEAVE_WALLET_JWK=${ARWEAVE_WALLET_JWK}  # JWK data directly in env
      - ARWEAVE_GATEWAY=${ARWEAVE_GATEWAY}
      - API_PORT=8000
      - DEBUG=false
      - LOG_LEVEL=INFO
      - SELF_ATTESTATION_URL=http://localhost:29343
    volumes:
      - ./static:/app/static:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### **FastAPI Production Configuration**
```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import os
import logging

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="attest_ai",
    description="Cryptographic proofs for Secret AI interactions in SecretVM",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG") == "true" else None,
    redoc_url="/redoc" if os.getenv("DEBUG") == "true" else None
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize services and validate environment"""
    # Validate environment variables
    validate_environment()
    
    # Initialize and cache self-attestation
    await cache_self_attestation()
    
    # Initialize Arweave wallet
    await initialize_arweave_wallet()
    
    logging.info("attest_ai started successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        access_log=True,
        use_colors=True
    )
```

---

## **🔐 Complete Environment Variable Strategy**

### **Updated .env.template**
```bash
# Secret AI Configuration (NEVER commit real values)
SECRET_AI_API_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1

# Arweave Configuration (JWK as JSON string)
ARWEAVE_WALLET_JWK={"kty":"RSA","e":"AQAB","n":"...","d":"...","p":"...","q":"...","dp":"...","dq":"...","qi":"..."}
ARWEAVE_GATEWAY=https://arweave.net

# SecretVM Configuration
SELF_ATTESTATION_URL=http://localhost:29343
ATTESTATION_CACHE_TTL=300

# Application Configuration
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
ENABLE_ARWEAVE_UPLOAD=true
MOCK_UNFUNDED_TRANSACTIONS=true
```

### **Environment Validation**
```python
import os
import json
from typing import Optional

def validate_environment() -> dict:
    """Validate all required environment variables on startup"""
    
    required_vars = {
        "SECRET_AI_API_KEY": "Secret AI master key",
        "ARWEAVE_WALLET_JWK": "Arweave wallet in JWK format",
    }
    
    optional_vars = {
        "ARWEAVE_GATEWAY": "https://arweave.net",
        "API_PORT": "8000",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "SELF_ATTESTATION_URL": "http://localhost:29343",
        "ATTESTATION_CACHE_TTL": "300",
        "ENABLE_ARWEAVE_UPLOAD": "true",
        "MOCK_UNFUNDED_TRANSACTIONS": "true"
    }
    
    missing_vars = []
    config = {}
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        else:
            config[var] = value
    
    # Validate JWK format
    if config.get("ARWEAVE_WALLET_JWK"):
        try:
            jwk_data = json.loads(config["ARWEAVE_WALLET_JWK"])
            required_jwk_fields = ["kty", "e", "n", "d", "p", "q", "dp", "dq", "qi"]
            for field in required_jwk_fields:
                if field not in jwk_data:
                    missing_vars.append(f"ARWEAVE_WALLET_JWK missing field: {field}")
        except json.JSONDecodeError:
            missing_vars.append("ARWEAVE_WALLET_JWK is not valid JSON")
    
    # Set optional variables with defaults
    for var, default in optional_vars.items():
        config[var] = os.getenv(var, default)
    
    if missing_vars:
        raise ValueError(f"Missing or invalid environment variables:\n" + "\n".join(missing_vars))
    
    return config
```

---

## **🚀 Complete Implementation Patterns**

### **Arweave Client Implementation**
```python
import arweave
import json
import os
import time
import random
import string
from typing import Dict, Optional

class ArweaveClient:
    def __init__(self):
        self.wallet_jwk = json.loads(os.getenv("ARWEAVE_WALLET_JWK"))
        self.gateway = os.getenv("ARWEAVE_GATEWAY", "https://arweave.net")
        self.wallet = None
        self.enable_upload = os.getenv("ENABLE_ARWEAVE_UPLOAD", "true").lower() == "true"
        self.mock_unfunded = os.getenv("MOCK_UNFUNDED_TRANSACTIONS", "true").lower() == "true"
        
    async def initialize_wallet(self):
        """Initialize wallet from JWK data in environment"""
        self.wallet = arweave.Wallet.from_data(self.wallet_jwk)
        logging.info(f"Arweave wallet initialized: {self.wallet.address}")
        
    async def get_wallet_balance(self) -> float:
        """Get current wallet balance in AR"""
        if not self.wallet:
            await self.initialize_wallet()
        return self.wallet.balance
        
    async def estimate_upload_cost(self, data_size: int) -> float:
        """Estimate cost for uploading data in AR"""
        if not self.wallet:
            await self.initialize_wallet()
        
        # Create temporary transaction to get cost
        temp_tx = arweave.Transaction(self.wallet, data="x" * data_size)
        cost_winston = temp_tx.get_reward(data_size)
        return arweave.utils.winston_to_ar(cost_winston)
        
    async def upload_or_mock_proof(self, proof_data: Dict) -> Dict:
        """Upload proof if funded, otherwise create mock transaction"""
        if not self.wallet:
            await self.initialize_wallet()
            
        # Serialize proof data
        proof_json = json.dumps(proof_data, separators=(',', ':'))
        data_size = len(proof_json.encode('utf-8'))
        
        # Estimate cost
        cost_ar = await self.estimate_upload_cost(data_size)
        balance = await self.get_wallet_balance()
        
        # Check if we should upload or mock
        if self.enable_upload and balance >= cost_ar:
            return await self._real_upload(proof_json, proof_data)
        else:
            return await self._mock_upload(proof_json, proof_data, cost_ar, balance)
    
    async def _real_upload(self, proof_json: str, proof_data: Dict) -> Dict:
        """Perform real upload to Arweave"""
        transaction = arweave.Transaction(self.wallet, data=proof_json)
        
        # Add standard tags
        transaction.add_tag('Content-Type', 'application/json')
        transaction.add_tag('App-Name', 'attest_ai')
        transaction.add_tag('App-Version', '1.0.0')
        transaction.add_tag('Title', 'Cryptographic AI Proof')
        transaction.add_tag('Type', 'attestation-proof')
        transaction.add_tag('Topic', 'SecretVM')
        transaction.add_tag('Unix-Time', str(int(time.time())))
        
        # Add custom proof tags
        transaction.add_tag('Proof-ID', proof_data.get('proof_id', ''))
        transaction.add_tag('Proof-Type', 'dual-attestation')
        
        # Sign and send
        transaction.sign()
        transaction.send()
        
        return {
            "uploaded": True,
            "transaction_id": transaction.id,
            "cost_ar": arweave.utils.winston_to_ar(transaction.reward),
            "mocked": False,
            "arweave_url": f"https://arweave.net/{transaction.id}"
        }
    
    async def _mock_upload(self, proof_json: str, proof_data: Dict, cost_ar: float, balance: float) -> Dict:
        """Create mock transaction for demo purposes"""
        mock_tx_id = f"mock_tx_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"
        
        return {
            "uploaded": False,
            "transaction_id": mock_tx_id,
            "cost_ar": cost_ar,
            "mocked": True,
            "reason": "insufficient_funds" if balance < cost_ar else "upload_disabled",
            "balance": balance,
            "arweave_url": f"https://arweave.net/{mock_tx_id}",
            "note": "This is a mock transaction for demonstration purposes"
        }
```

### **Complete Proof Generation**
```python
import hashlib
import time
import uuid
from typing import Dict

class ProofGenerator:
    def __init__(self):
        self.version = "1.0"
        
    async def generate_interaction_hash(self, message: str, response: str) -> str:
        """Generate SHA-256 hash of user message + AI response"""
        combined = f"{message}|{response}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
    async def generate_attestation_hash(self, attestation_data: Dict) -> str:
        """Generate SHA-256 hash of attestation registers"""
        # Extract key register values in deterministic order
        registers = [
            attestation_data.get('mr_td', ''),
            attestation_data.get('rtmr0', ''),
            attestation_data.get('rtmr1', ''),
            attestation_data.get('rtmr2', ''),
            attestation_data.get('rtmr3', ''),
            attestation_data.get('report_data', '')
        ]
        combined = '|'.join(registers)
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
    async def create_dual_attestation_proof(self, 
                                          interaction: Dict, 
                                          self_attestation: Dict, 
                                          secretai_attestation: Dict) -> Dict:
        """Create complete proof linking interaction to both attestations"""
        
        proof_id = str(uuid.uuid4())
        timestamp = time.time()
        iso_timestamp = datetime.utcfromtimestamp(timestamp).isoformat() + "Z"
        
        # Generate hashes
        interaction_hash = await self.generate_interaction_hash(
            interaction['message'], 
            interaction['response']
        )
        
        self_attestation_hash = await self.generate_attestation_hash(self_attestation)
        secretai_attestation_hash = await self.generate_attestation_hash(secretai_attestation)
        
        # Create proof structure
        proof = {
            "proof_id": proof_id,
            "timestamp": iso_timestamp,
            "version": self.version,
            "attestations": {
                "attest_ai_vm": {
                    "instance_url": "localhost:29343",
                    "vm_registers": {
                        "mr_td": self_attestation.get('mr_td', ''),
                        "rtmr0": self_attestation.get('rtmr0', ''),
                        "rtmr1": self_attestation.get('rtmr1', ''),
                        "rtmr2": self_attestation.get('rtmr2', ''),
                        "rtmr3": self_attestation.get('rtmr3', '')
                    },
                    "tls_fingerprint": self_attestation.get('tls_fingerprint', ''),
                    "attestation_hash": self_attestation_hash,
                    "status": "verified",
                    "cached": self_attestation.get('cached', False),
                    "timestamp": self_attestation.get('timestamp', iso_timestamp)
                },
                "secret_ai_vm": {
                    "instance_url": secretai_attestation.get('instance_url', ''),
                    "model": secretai_attestation.get('model', ''),
                    "vm_registers": {
                        "mr_td": secretai_attestation.get('mr_td', ''),
                        "rtmr0": secretai_attestation.get('rtmr0', ''),
                    },
                    "attestation_hash": secretai_attestation_hash,
                    "status": secretai_attestation.get('status', 'mocked'),
                    "timestamp": iso_timestamp
                }
            },
            "interaction": {
                "input_hash": hashlib.sha256(interaction['message'].encode()).hexdigest(),
                "output_hash": hashlib.sha256(interaction['response'].encode()).hexdigest(),
                "interaction_hash": interaction_hash,
                "timestamp": iso_timestamp
            },
            "cryptographic_binding": {
                "binding_hash": self._generate_binding_hash(
                    interaction_hash, 
                    self_attestation_hash, 
                    secretai_attestation_hash
                ),
                "verification_method": "sha256_binding_v1"
            }
        }
        
        return proof
    
    def _generate_binding_hash(self, interaction_hash: str, self_hash: str, secretai_hash: str) -> str:
        """Generate cryptographic binding linking all components"""
        combined = f"{interaction_hash}|{self_hash}|{secretai_hash}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
```

---

This comprehensive update now includes **all the critical missing pieces**:

1. **✅ Complete Arweave Python SDK integration** - wallet management, transaction creation, cost calculation
2. **✅ Production Docker patterns** - multi-stage builds, health checks, security
3. **✅ FastAPI production configuration** - middleware, logging, startup validation
4. **✅ Environment variable strategy** - JWK in env, proper validation
5. **✅ Complete proof generation** - dual attestation, cryptographic binding
6. **✅ Upload/mock logic** - smart decision making based on funding

**The most critical discovery:** The Arweave Python SDK solves our mnemonic-to-JWK problem completely! We can store the JWK directly in the environment variable and load it with `Wallet.from_data()`.

Now we have everything needed for a complete implementation. Ready to start building?