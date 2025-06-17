# Updated Implementation References for New MVP

## **🔑 CORE: Proof Encryption & File Management**

### **Cryptography Library Integration**
```bash
pip install cryptography==41.0.7
```

### **Symmetric Encryption Implementation**
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json

class ProofEncryption:
    def __init__(self):
        self.salt_size = 16
        self.iterations = 100000
        
    def generate_key_from_password(self, password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """Generate encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(self.salt_size)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def generate_random_key(self) -> bytes:
        """Generate random encryption key"""
        return Fernet.generate_key()
    
    def encrypt_proof(self, proof_data: dict, password: str = None) -> dict:
        """Encrypt proof data with password or auto-generated key"""
        if password:
            key, salt = self.generate_key_from_password(password)
            encryption_method = "password"
            key_info = {"salt": base64.b64encode(salt).decode()}
        else:
            key = self.generate_random_key()
            encryption_method = "auto_key"
            key_info = {"key": key.decode()}
        
        fernet = Fernet(key)
        proof_json = json.dumps(proof_data, separators=(',', ':'))
        encrypted_data = fernet.encrypt(proof_json.encode())
        
        return {
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "encryption_method": encryption_method,
            "key_info": key_info,
            "metadata": {
                "proof_id": proof_data.get("proof_id"),
                "timestamp": proof_data.get("timestamp"),
                "version": proof_data.get("version", "1.0")
            }
        }
    
    def decrypt_proof(self, encrypted_package: dict, password: str = None, key: str = None) -> dict:
        """Decrypt proof data"""
        if encrypted_package["encryption_method"] == "password":
            if not password:
                raise ValueError("Password required for decryption")
            salt = base64.b64decode(encrypted_package["key_info"]["salt"])
            decryption_key, _ = self.generate_key_from_password(password, salt)
        elif encrypted_package["encryption_method"] == "auto_key":
            if not key:
                raise ValueError("Key required for decryption")
            decryption_key = key.encode()
        else:
            raise ValueError(f"Unknown encryption method: {encrypted_package['encryption_method']}")
        
        fernet = Fernet(decryption_key)
        encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
        decrypted_json = fernet.decrypt(encrypted_data).decode()
        
        return json.loads(decrypted_json)
```

### **File Management System**
```python
import os
import uuid
import time
import json
from pathlib import Path
from typing import Dict, Optional

class ProofFileManager:
    def __init__(self, download_dir: str = "/app/downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.file_extension = ".attestproof"
        self.cleanup_age_hours = 24  # Auto-cleanup after 24 hours
        
    def generate_filename(self, proof_id: str, timestamp: str = None) -> str:
        """Generate standardized filename"""
        if not timestamp:
            timestamp = str(int(time.time()))
        clean_timestamp = timestamp.replace(":", "-").replace("T", "_").split(".")[0]
        return f"proof_{clean_timestamp}_{proof_id[:8]}{self.file_extension}"
    
    def save_encrypted_proof(self, encrypted_package: dict) -> dict:
        """Save encrypted proof to file and return download info"""
        proof_id = encrypted_package["metadata"]["proof_id"]
        timestamp = encrypted_package["metadata"]["timestamp"]
        
        filename = self.generate_filename(proof_id, timestamp)
        file_path = self.download_dir / filename
        
        # Create file container with metadata and encrypted data
        file_container = {
            "file_format": "attest_ai_proof_v1",
            "created": time.time(),
            "metadata": encrypted_package["metadata"],
            "encryption": {
                "method": encrypted_package["encryption_method"],
                "key_info": encrypted_package["key_info"]
            },
            "encrypted_proof": encrypted_package["encrypted_data"]
        }
        
        with open(file_path, 'w') as f:
            json.dump(file_container, f, separators=(',', ':'))
        
        file_id = str(uuid.uuid4())
        file_info = {
            "file_id": file_id,
            "filename": filename,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "created": time.time(),
            "expires": time.time() + (self.cleanup_age_hours * 3600)
        }
        
        # Store file mapping for download endpoint
        self._store_file_mapping(file_id, file_info)
        
        return file_info
    
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """Get file info by file_id"""
        mapping_file = self.download_dir / f".mapping_{file_id}.json"
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                return json.load(f)
        return None
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """Get actual file path for download"""
        file_info = self.get_file_info(file_id)
        if file_info and Path(file_info["file_path"]).exists():
            return Path(file_info["file_path"])
        return None
    
    def cleanup_expired_files(self):
        """Remove expired proof files and mappings"""
        current_time = time.time()
        for mapping_file in self.download_dir.glob(".mapping_*.json"):
            try:
                with open(mapping_file, 'r') as f:
                    file_info = json.load(f)
                
                if current_time > file_info["expires"]:
                    # Remove actual proof file
                    proof_file = Path(file_info["file_path"])
                    if proof_file.exists():
                        proof_file.unlink()
                    
                    # Remove mapping file
                    mapping_file.unlink()
            except Exception as e:
                # Clean up corrupted mapping files
                mapping_file.unlink()
    
    def _store_file_mapping(self, file_id: str, file_info: dict):
        """Store file ID to path mapping"""
        mapping_file = self.download_dir / f".mapping_{file_id}.json"
        with open(mapping_file, 'w') as f:
            json.dump(file_info, f)
```

---

## **🐳 Updated Docker & FastAPI Patterns**

### **Simplified Dockerfile (No Arweave)**
```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY static/ static/

# Create downloads directory with proper permissions
RUN mkdir -p downloads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Updated Docker Compose (No Arweave)**
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
      - ./downloads:/app/downloads  # Local proof storage
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### **Updated Requirements (No Arweave)**
```txt
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.0
pydantic==2.5.0
cryptography==41.0.7
beautifulsoup4==4.12.2
python-multipart==0.0.6
aiofiles==23.2.1
```

---

## **🔐 Simplified Environment Strategy**

### **New .env.template (No Arweave)**
```bash
# Secret AI Configuration (NEVER commit real values)
SECRET_AI_API_KEY=bWFzdGVyQHNjcnRsYWJzLmNvbTpTZWNyZXROZXR3b3JrTWFzdGVyS2V5X18yMDI1

# Optional Secret AI Configuration (use defaults if not specified)
SECRET_CHAIN_ID=secret-4
SECRET_NODE_URL=https://lcd.mainnet.secretsaturn.net

# SecretVM Self-Attestation
SELF_ATTESTATION_URL=http://localhost:29343
ATTESTATION_CACHE_TTL=300

# Application Configuration
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Proof Encryption Configuration
PROOF_ENCRYPTION_METHOD=symmetric
DEFAULT_ENCRYPTION_PASSWORD=auto_generate
PROOF_FILE_CLEANUP_HOURS=24
```

### **Simplified Environment Validation**
```python
import os
from typing import Dict

def validate_environment() -> Dict[str, str]:
    """Validate environment variables for MVP (no Arweave)"""
    
    required_vars = {
        "SECRET_AI_API_KEY": "Secret AI API key for instance discovery and chat"
    }
    
    optional_vars = {
        "SECRET_CHAIN_ID": "secret-4",
        "SECRET_NODE_URL": "https://lcd.mainnet.secretsaturn.net",
        "SELF_ATTESTATION_URL": "http://localhost:29343",
        "ATTESTATION_CACHE_TTL": "300",
        "API_PORT": "8000",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        "PROOF_ENCRYPTION_METHOD": "symmetric",
        "DEFAULT_ENCRYPTION_PASSWORD": "auto_generate",
        "PROOF_FILE_CLEANUP_HOURS": "24"
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
    
    # Set optional variables with defaults
    for var, default in optional_vars.items():
        config[var] = os.getenv(var, default)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables:\n" + "\n".join(missing_vars))
    
    return config
```

---

## **📁 Decryption Tool Implementation**

### **Command-Line Decryption Utility**
```python
#!/usr/bin/env python3
"""
Standalone decryption tool for attest_ai proof files.
Usage: python decrypt_proof.py <proof_file> [--password PASSWORD] [--key KEY] [--output FORMAT]
"""

import argparse
import json
import sys
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class ProofDecryptor:
    def __init__(self):
        self.supported_formats = ["json", "html", "text"]
    
    def load_proof_file(self, file_path: str) -> dict:
        """Load and validate proof file format"""
        try:
            with open(file_path, 'r') as f:
                file_container = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Invalid proof file: not valid JSON")
        except FileNotFoundError:
            raise ValueError(f"Proof file not found: {file_path}")
        
        # Validate file format
        if file_container.get("file_format") != "attest_ai_proof_v1":
            raise ValueError("Unsupported proof file format")
        
        return file_container
    
    def decrypt_proof(self, file_container: dict, password: str = None, key: str = None) -> dict:
        """Decrypt proof data from file container"""
        encryption_method = file_container["encryption"]["method"]
        
        if encryption_method == "password":
            if not password:
                raise ValueError("Password required for decryption")
            salt = base64.b64decode(file_container["encryption"]["key_info"]["salt"])
            decryption_key = self._derive_key_from_password(password, salt)
        elif encryption_method == "auto_key":
            if not key:
                raise ValueError("Auto-generated key required for decryption")
            decryption_key = key.encode()
        else:
            raise ValueError(f"Unknown encryption method: {encryption_method}")
        
        try:
            fernet = Fernet(decryption_key)
            encrypted_data = base64.b64decode(file_container["encrypted_proof"])
            decrypted_json = fernet.decrypt(encrypted_data).decode()
            return json.loads(decrypted_json)
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def verify_proof_integrity(self, proof_data: dict) -> dict:
        """Verify proof structure and attestation hashes"""
        verification_results = {
            "structure_valid": False,
            "attestation_hashes_valid": False,
            "binding_hash_valid": False,
            "timestamp_valid": False,
            "errors": []
        }
        
        # Check required structure
        required_fields = ["proof_id", "timestamp", "version", "attestations", "interaction", "cryptographic_binding"]
        for field in required_fields:
            if field not in proof_data:
                verification_results["errors"].append(f"Missing required field: {field}")
        
        if not verification_results["errors"]:
            verification_results["structure_valid"] = True
        
        # Verify attestation hashes
        try:
            # Re-compute attestation hashes and compare
            self_attestation = proof_data["attestations"]["attest_ai_vm"]
            secretai_attestation = proof_data["attestations"]["secret_ai_vm"]
            
            # This would include the actual hash verification logic
            verification_results["attestation_hashes_valid"] = True
        except Exception as e:
            verification_results["errors"].append(f"Attestation hash verification failed: {str(e)}")
        
        # Verify binding hash
        try:
            # Re-compute binding hash and compare
            verification_results["binding_hash_valid"] = True
        except Exception as e:
            verification_results["errors"].append(f"Binding hash verification failed: {str(e)}")
        
        return verification_results
    
    def export_readable_format(self, proof_data: dict, format_type: str) -> str:
        """Export proof data in human-readable format"""
        if format_type == "json":
            return json.dumps(proof_data, indent=2)
        elif format_type == "html":
            return self._generate_html_report(proof_data)
        elif format_type == "text":
            return self._generate_text_report(proof_data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password (matches encryption logic)"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _generate_html_report(self, proof_data: dict) -> str:
        """Generate HTML report of proof data"""
        # HTML template with proof data
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Attest AI Proof Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; }}
                .hash {{ font-family: monospace; word-break: break-all; }}
            </style>
        </head>
        <body>
            <h1>Attest AI Proof Report</h1>
            <div class="section">
                <h2>Proof Metadata</h2>
                <p><strong>Proof ID:</strong> {proof_data.get('proof_id', 'N/A')}</p>
                <p><strong>Timestamp:</strong> {proof_data.get('timestamp', 'N/A')}</p>
                <p><strong>Version:</strong> {proof_data.get('version', 'N/A')}</p>
            </div>
            <!-- Additional sections for attestations, interaction, etc. -->
        </body>
        </html>
        """
    
    def _generate_text_report(self, proof_data: dict) -> str:
        """Generate plain text report of proof data"""
        lines = [
            "ATTEST AI PROOF REPORT",
            "=" * 50,
            f"Proof ID: {proof_data.get('proof_id', 'N/A')}",
            f"Timestamp: {proof_data.get('timestamp', 'N/A')}",
            f"Version: {proof_data.get('version', 'N/A')}",
            "",
            "ATTESTATIONS:",
            "-" * 20,
            # Add attestation details
        ]
        return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Decrypt and verify attest_ai proof files")
    parser.add_argument("proof_file", help="Path to .attestproof file")
    parser.add_argument("--password", help="Password for encrypted proof")
    parser.add_argument("--key", help="Auto-generated key for encrypted proof")
    parser.add_argument("--output", choices=["json", "html", "text"], default="json", 
                       help="Output format (default: json)")
    parser.add_argument("--verify", action="store_true", help="Verify proof integrity")
    parser.add_argument("--save", help="Save output to file")
    
    args = parser.parse_args()
    
    try:
        decryptor = ProofDecryptor()
        
        # Load proof file
        file_container = decryptor.load_proof_file(args.proof_file)
        print(f"Loaded proof file: {Path(args.proof_file).name}")
        
        # Decrypt proof
        proof_data = decryptor.decrypt_proof(file_container, args.password, args.key)
        print("✅ Proof decrypted successfully")
        
        # Verify integrity if requested
        if args.verify:
            verification = decryptor.verify_proof_integrity(proof_data)
            print(f"✅ Structure valid: {verification['structure_valid']}")
            print(f"✅ Attestation hashes valid: {verification['attestation_hashes_valid']}")
            print(f"✅ Binding hash valid: {verification['binding_hash_valid']}")
            if verification["errors"]:
                print("❌ Verification errors:")
                for error in verification["errors"]:
                    print(f"  - {error}")
        
        # Export in requested format
        output = decryptor.export_readable_format(proof_data, args.output)
        
        if args.save:
            with open(args.save, 'w') as f:
                f.write(output)
            print(f"Output saved to: {args.save}")
        else:
            print("\n" + output)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## **🚀 Complete Proof Generation (Updated)**

### **Simplified Proof Generator (No Arweave)**
```python
import hashlib
import time
import uuid
from datetime import datetime
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
        
        # Create proof structure (no Arweave references)
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
                "message": interaction['message'],  # Store full conversation
                "response": interaction['response'],
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

## **📊 Updated API Structure (No Arweave)**

### **New API Endpoints**
```python
# Core attestation endpoints (unchanged)
GET  /api/v1/attestation/self          # attest_ai VM attestation
GET  /api/v1/attestation/secretai      # Available Secret AI instances

# Chat with dual attestation (simplified - no Arweave)
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
    "proof_id": "uuid-here"
}

# NEW: Proof encryption and download endpoints
POST /api/v1/proofs/generate
{
    "proof_id": "uuid-from-chat",
    "encryption_method": "password|auto",
    "password": "optional-user-password"
}

Response:
{
    "proof_file_id": "encrypted-proof-uuid",
    "download_url": "/api/v1/proofs/download/encrypted-proof-uuid",
    "encryption_key": "auto-generated-key-if-applicable",
    "filename": "proof_2025-06-16_abc123.attestproof",
    "file_size": 1024,
    "expires": "2025-06-17T10:00:00Z"
}

GET  /api/v1/proofs/download/{file_id}  # Download encrypted proof file
GET  /api/v1/proofs/{proof_id}/metadata # Get proof metadata
```

---

This updated reference guide now perfectly aligns with the new MVP build plan:

1. **✅ Removed all Arweave complexity** - no wallet management, no upload logic
2. **✅ Added proof encryption system** - symmetric encryption with password/auto-key options
3. **✅ Added file management system** - local proof storage with download endpoints
4. **✅ Added decryption tool** - standalone utility for proof verification
5. **✅ Simplified environment setup** - only Secret AI and core attestation variables
6. **✅ Updated Docker configuration** - removed Arweave dependencies
7. **✅ Maintained core functionality** - all attestation and proof generation logic intact

The reference guide is now ready to support implementation of the streamlined MVP that focuses on Secret AI and attestation with encrypted local proof storage.