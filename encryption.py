import hashlib
import base64
import json
from datetime import datetime
from cryptography.fernet import Fernet
from abc import ABC, abstractmethod
from typing import Dict, Any

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
        # Use a fixed salt for simplicity in MVP (in production, use random salt)
        salt = b'attest_ai_salt_v1'
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        # Fernet requires URL-safe base64-encoded 32-byte key
        return base64.urlsafe_b64encode(key[:32])
    
    def encrypt(self, data: str, password: str) -> str:
        """Encrypt data with password"""
        try:
            key = self.derive_key_from_password(password)
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str, password: str) -> str:
        """Decrypt data with password"""
        try:
            key = self.derive_key_from_password(password)
            fernet = Fernet(key)
            decrypted = fernet.decrypt(base64.b64decode(encrypted_data))
            return decrypted.decode()
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

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
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return self.provider.encrypt(json.dumps(conversation_data), password)
    
    def decrypt_conversation(self, encrypted_data: str, password: str) -> Dict[str, Any]:
        """Decrypt conversation data"""
        try:
            decrypted_json = self.provider.decrypt(encrypted_data, password)
            return json.loads(decrypted_json)
        except Exception as e:
            raise Exception(f"Failed to decrypt conversation: {str(e)}")
    
    def hash_data(self, data: str) -> str:
        """Create SHA256 hash of data"""
        return hashlib.sha256(data.encode()).hexdigest()