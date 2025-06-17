import os
import json
import uuid
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProofManager:
    """Manages encrypted proof generation, storage, and decryption"""
    
    def __init__(self, downloads_dir: str = "./downloads", cleanup_hours: int = 24):
        self.downloads_dir = downloads_dir
        self.cleanup_hours = cleanup_hours
        
        # Ensure downloads directory exists
        os.makedirs(self.downloads_dir, exist_ok=True)
        
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Cryptography library not available. Proof encryption will be disabled.")
    
    async def generate_proof(self, chat_data: Dict[str, Any], attestations: Dict[str, Any], password: str) -> str:
        """
        Generate an encrypted proof file from chat data and attestations
        
        Args:
            chat_data: Dictionary containing message, response, and metadata
            attestations: Dual attestation data from DualAttestationManager
            password: User-provided password for encryption
            
        Returns:
            proof_id: Unique identifier for the generated proof
        """
        try:
            # Generate unique proof ID
            proof_id = str(uuid.uuid4())
            
            # Create proof structure
            proof_data = self._create_proof_structure(proof_id, chat_data, attestations)
            
            # Encrypt the proof data
            encrypted_data = self._encrypt_proof_data(proof_data, password)
            
            # Save to file
            file_path = self._save_proof_file(encrypted_data, proof_id)
            
            logger.info(f"Generated proof {proof_id} at {file_path}")
            
            return proof_id
            
        except Exception as e:
            logger.error(f"Error generating proof: {str(e)}")
            raise
    
    def _create_proof_structure(self, proof_id: str, chat_data: Dict[str, Any], attestations: Dict[str, Any]) -> Dict[str, Any]:
        """Create the standardized proof data structure"""
        timestamp = datetime.utcnow().isoformat()
        
        # Create chat hash
        chat_canonical = json.dumps(chat_data, sort_keys=True)
        chat_hash = hashlib.sha256(chat_canonical.encode()).hexdigest()
        
        # Create attestation hash
        attestation_canonical = json.dumps(attestations, sort_keys=True)
        attestation_hash = hashlib.sha256(attestation_canonical.encode()).hexdigest()
        
        # Create combined hash
        combined = f"{chat_hash}:{attestation_hash}:{timestamp}"
        combined_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        proof_structure = {
            "metadata": {
                "version": "1.0",
                "timestamp": timestamp,
                "proof_id": proof_id,
                "file_format": "attestproof",
                "generator": "attest-ai-mvp"
            },
            "chat_data": {
                "messages": [
                    {
                        "role": "user",
                        "content": chat_data.get("message", ""),
                        "timestamp": timestamp
                    },
                    {
                        "role": "ai", 
                        "content": chat_data.get("response", ""),
                        "timestamp": timestamp
                    }
                ],
                "secret_ai_metadata": {
                    "model": chat_data.get("model", "unknown"),
                    "base_url": chat_data.get("base_url", "unknown"),
                    "mode": chat_data.get("mode", "unknown")
                }
            },
            "attestations": attestations,
            "integrity": {
                "chat_hash": chat_hash,
                "attestation_hash": attestation_hash,
                "combined_hash": combined_hash,
                "algorithm": "sha256"
            }
        }
        
        return proof_structure
    
    def _encrypt_proof_data(self, proof_data: Dict[str, Any], password: str) -> bytes:
        """Encrypt proof data using password-based encryption"""
        if not CRYPTOGRAPHY_AVAILABLE:
            # Fallback to base64 encoding (not secure, for testing only)
            logger.warning("Using base64 encoding instead of encryption (cryptography not available)")
            json_data = json.dumps(proof_data, indent=2)
            return base64.b64encode(json_data.encode())
        
        try:
            # Convert proof data to JSON
            json_data = json.dumps(proof_data, indent=2)
            
            # Generate salt
            salt = os.urandom(16)
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Encrypt the data
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(json_data.encode())
            
            # Combine salt and encrypted data
            combined_data = salt + encrypted_data
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error encrypting proof data: {str(e)}")
            raise
    
    def _save_proof_file(self, encrypted_data: bytes, proof_id: str) -> str:
        """Save encrypted proof data to file"""
        try:
            filename = f"{proof_id}.attestproof"
            file_path = os.path.join(self.downloads_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving proof file: {str(e)}")
            raise
    
    def decrypt_proof_file(self, file_data: bytes, password: str) -> Dict[str, Any]:
        """
        Decrypt an uploaded proof file
        
        Args:
            file_data: Raw bytes from uploaded .attestproof file
            password: Password for decryption
            
        Returns:
            Decrypted proof data structure
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            # Fallback base64 decoding
            logger.warning("Using base64 decoding instead of decryption (cryptography not available)")
            try:
                json_data = base64.b64decode(file_data).decode()
                return json.loads(json_data)
            except Exception as e:
                raise ValueError(f"Failed to decode proof file: {str(e)}")
        
        try:
            # Extract salt and encrypted data
            salt = file_data[:16]
            encrypted_data = file_data[16:]
            
            # Derive key from password using same parameters
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Decrypt the data
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse JSON
            proof_data = json.loads(decrypted_data.decode())
            
            # Verify integrity
            if not self._verify_proof_integrity(proof_data):
                logger.warning("Proof integrity verification failed")
            
            return proof_data
            
        except Exception as e:
            logger.error(f"Error decrypting proof file: {str(e)}")
            raise ValueError(f"Failed to decrypt proof file. Check password and file integrity.")
    
    def _verify_proof_integrity(self, proof_data: Dict[str, Any]) -> bool:
        """Verify the integrity hashes in the proof data"""
        try:
            integrity = proof_data.get("integrity", {})
            chat_data = proof_data.get("chat_data", {})
            attestations = proof_data.get("attestations", {})
            
            # Recalculate chat hash
            chat_canonical = json.dumps(chat_data, sort_keys=True)
            calculated_chat_hash = hashlib.sha256(chat_canonical.encode()).hexdigest()
            
            # Recalculate attestation hash
            attestation_canonical = json.dumps(attestations, sort_keys=True)
            calculated_attestation_hash = hashlib.sha256(attestation_canonical.encode()).hexdigest()
            
            # Verify hashes match
            return (
                integrity.get("chat_hash") == calculated_chat_hash and
                integrity.get("attestation_hash") == calculated_attestation_hash
            )
            
        except Exception as e:
            logger.error(f"Error verifying proof integrity: {str(e)}")
            return False
    
    def get_proof_file_path(self, proof_id: str) -> str:
        """Get the file path for a proof ID"""
        filename = f"{proof_id}.attestproof"
        return os.path.join(self.downloads_dir, filename)
    
    def proof_exists(self, proof_id: str) -> bool:
        """Check if a proof file exists"""
        return os.path.exists(self.get_proof_file_path(proof_id))
    
    def cleanup_old_files(self) -> int:
        """Remove proof files older than cleanup_hours"""
        try:
            cleaned_count = 0
            cutoff_time = datetime.now() - timedelta(hours=self.cleanup_hours)
            
            for filename in os.listdir(self.downloads_dir):
                if filename.endswith('.attestproof'):
                    file_path = os.path.join(self.downloads_dir, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old proof file: {filename}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old proof files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0
    
    def list_proof_files(self) -> list:
        """List all available proof files"""
        try:
            proof_files = []
            for filename in os.listdir(self.downloads_dir):
                if filename.endswith('.attestproof'):
                    file_path = os.path.join(self.downloads_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    proof_files.append({
                        "filename": filename,
                        "proof_id": filename.replace('.attestproof', ''),
                        "size": file_stat.st_size,
                        "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
            
            return sorted(proof_files, key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing proof files: {str(e)}")
            return []


# Test function
async def test_proof_manager():
    """Test proof manager functionality"""
    print("Testing Proof Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = ProofManager(downloads_dir="./test_downloads")
    
    # Sample chat data
    chat_data = {
        "message": "What is Secret Network?",
        "response": "Secret Network is a blockchain with built-in privacy features.",
        "model": "test-model",
        "base_url": "https://test.example.com",
        "mode": "mock"
    }
    
    # Sample attestations
    attestations = {
        "self": {
            "source": "self",
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"test": "data"}
        },
        "secret_ai": {
            "source": "secret_ai", 
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "mock",
            "data": {"test": "data"}
        },
        "attestation_binding": {
            "binding_valid": True,
            "combined_hash": "test-hash"
        }
    }
    
    password = "test123"
    
    try:
        # Test proof generation
        print("\n1. Testing proof generation...")
        proof_id = await manager.generate_proof(chat_data, attestations, password)
        print(f"Generated proof ID: {proof_id}")
        
        # Test file exists
        print(f"Proof file exists: {manager.proof_exists(proof_id)}")
        
        # Test decryption
        print("\n2. Testing proof decryption...")
        file_path = manager.get_proof_file_path(proof_id)
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        decrypted_data = manager.decrypt_proof_file(file_data, password)
        print(f"Decrypted successfully: {decrypted_data['metadata']['proof_id'] == proof_id}")
        print(f"Chat message matches: {decrypted_data['chat_data']['messages'][0]['content'] == chat_data['message']}")
        
        # Test wrong password
        print("\n3. Testing wrong password...")
        try:
            manager.decrypt_proof_file(file_data, "wrong_password")
            print("❌ Should have failed with wrong password")
        except ValueError:
            print("✅ Correctly rejected wrong password")
        
        print("\n4. Listing proof files...")
        files = manager.list_proof_files()
        print(f"Found {len(files)} proof files")
        
        print("\n✅ Proof manager tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_proof_manager())