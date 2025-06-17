import asyncio
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from src.attestation.self_attestation import SelfAttestationClient
from src.secret_ai.client import SecretAIClient

logger = logging.getLogger(__name__)


class DualAttestationManager:
    """Manages dual attestation from both self (host VM) and Secret AI"""
    
    def __init__(self, self_attestation_client: SelfAttestationClient, secret_ai_client: SecretAIClient):
        self.self_attestation_client = self_attestation_client
        self.secret_ai_client = secret_ai_client
    
    async def get_dual_attestation(self, secret_ai_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get attestation from both sources concurrently
        
        Args:
            secret_ai_url: Optional Secret AI base URL to use for attestation
            
        Returns:
            Dictionary containing both attestations and cryptographic binding
        """
        try:
            # Run both attestations concurrently
            results = await asyncio.gather(
                self.self_attestation_client.get_attestation(),
                self.secret_ai_client.get_attestation(secret_ai_url),
                return_exceptions=True
            )
            
            # Process results
            self_attestation = results[0] if not isinstance(results[0], Exception) else self._error_attestation("self", str(results[0]))
            secretai_attestation = results[1] if not isinstance(results[1], Exception) else self._error_attestation("secret_ai", str(results[1]))
            
            # Create attestation binding
            binding = self._create_attestation_binding(self_attestation, secretai_attestation)
            
            # Compose final attestation package
            dual_attestation = {
                "timestamp": datetime.utcnow().isoformat(),
                "self": self_attestation,
                "secret_ai": secretai_attestation,
                "attestation_binding": binding,
                "summary": self._create_summary(self_attestation, secretai_attestation)
            }
            
            logger.info(f"Dual attestation completed - Self: {self_attestation['status']}, Secret AI: {secretai_attestation['status']}")
            
            return dual_attestation
            
        except Exception as e:
            logger.error(f"Critical error in dual attestation: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "self": self._error_attestation("self", "Failed to get attestation"),
                "secret_ai": self._error_attestation("secret_ai", "Failed to get attestation"),
                "attestation_binding": None,
                "error": str(e)
            }
    
    def _create_attestation_binding(self, self_attestation: Dict[str, Any], secretai_attestation: Dict[str, Any]) -> Dict[str, Any]:
        """Create cryptographic binding between two attestations"""
        try:
            # Create canonical representation of attestations
            self_canonical = json.dumps(self_attestation, sort_keys=True)
            secretai_canonical = json.dumps(secretai_attestation, sort_keys=True)
            
            # Calculate individual hashes
            self_hash = hashlib.sha256(self_canonical.encode()).hexdigest()
            secretai_hash = hashlib.sha256(secretai_canonical.encode()).hexdigest()
            
            # Create combined hash
            combined = f"{self_hash}:{secretai_hash}:{datetime.utcnow().isoformat()}"
            combined_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            binding = {
                "version": "1.0",
                "algorithm": "sha256",
                "self_hash": self_hash,
                "secret_ai_hash": secretai_hash,
                "combined_hash": combined_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "binding_valid": True
            }
            
            return binding
            
        except Exception as e:
            logger.error(f"Error creating attestation binding: {str(e)}")
            return {
                "version": "1.0",
                "algorithm": "sha256",
                "error": str(e),
                "binding_valid": False
            }
    
    def _create_summary(self, self_attestation: Dict[str, Any], secretai_attestation: Dict[str, Any]) -> Dict[str, Any]:
        """Create human-readable summary of attestation statuses"""
        summary = {
            "self_status": self_attestation.get("status", "unknown"),
            "self_mode": "real" if self_attestation.get("status") == "success" else "error",
            "secret_ai_status": secretai_attestation.get("status", "unknown"),
            "secret_ai_mode": secretai_attestation.get("mode", "unknown"),
            "both_successful": (
                self_attestation.get("status") == "success" and 
                secretai_attestation.get("status") == "success"
            ),
            "attestation_quality": self._determine_quality(self_attestation, secretai_attestation)
        }
        
        # Add specific details if available
        if self_attestation.get("status") == "success" and self_attestation.get("data"):
            summary["self_details"] = "Host VM attestation captured successfully"
        else:
            summary["self_details"] = self_attestation.get("error", "Host VM attestation failed")
            
        if secretai_attestation.get("status") == "success":
            if secretai_attestation.get("mode") == "real":
                summary["secret_ai_details"] = "Secret AI attestation captured from live instance"
            else:
                summary["secret_ai_details"] = "Secret AI using mock attestation (service unavailable)"
        else:
            summary["secret_ai_details"] = secretai_attestation.get("error", "Secret AI attestation failed")
        
        return summary
    
    def _determine_quality(self, self_attestation: Dict[str, Any], secretai_attestation: Dict[str, Any]) -> str:
        """Determine overall attestation quality"""
        self_ok = self_attestation.get("status") == "success"
        secretai_ok = secretai_attestation.get("status") == "success"
        secretai_real = secretai_attestation.get("mode") == "real"
        
        if self_ok and secretai_ok and secretai_real:
            return "high"
        elif self_ok and secretai_ok:
            return "medium"
        elif self_ok or secretai_ok:
            return "low"
        else:
            return "none"
    
    def _error_attestation(self, source: str, error: str) -> Dict[str, Any]:
        """Create error attestation structure"""
        return {
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": error,
            "data": None
        }
    
    def verify_binding(self, dual_attestation: Dict[str, Any]) -> bool:
        """Verify the attestation binding is valid"""
        try:
            binding = dual_attestation.get("attestation_binding", {})
            if not binding or not binding.get("binding_valid"):
                return False
            
            # Recalculate hashes
            self_attestation = dual_attestation.get("self", {})
            secretai_attestation = dual_attestation.get("secret_ai", {})
            
            self_canonical = json.dumps(self_attestation, sort_keys=True)
            secretai_canonical = json.dumps(secretai_attestation, sort_keys=True)
            
            self_hash = hashlib.sha256(self_canonical.encode()).hexdigest()
            secretai_hash = hashlib.sha256(secretai_canonical.encode()).hexdigest()
            
            # Verify individual hashes match
            if self_hash != binding.get("self_hash") or secretai_hash != binding.get("secret_ai_hash"):
                logger.warning("Attestation binding verification failed - hash mismatch")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying attestation binding: {str(e)}")
            return False


# Test function
async def test_dual_attestation():
    """Test dual attestation functionality"""
    from src.config import get_settings
    
    settings = get_settings()
    
    # Initialize clients
    self_client = SelfAttestationClient(
        base_url=settings.self_attestation_url,
        cache_ttl=settings.attestation_cache_ttl
    )
    secret_ai_client = SecretAIClient()
    
    # Create manager
    manager = DualAttestationManager(self_client, secret_ai_client)
    
    print("Testing Dual Attestation Manager")
    print("=" * 60)
    
    # Get dual attestation
    attestation = await manager.get_dual_attestation()
    
    print(f"\nSummary:")
    summary = attestation["summary"]
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"\nBinding:")
    binding = attestation["attestation_binding"]
    if binding:
        print(f"  Valid: {binding.get('binding_valid', False)}")
        print(f"  Combined Hash: {binding.get('combined_hash', 'N/A')[:32]}...")
    
    # Verify binding
    print(f"\nBinding Verification: {manager.verify_binding(attestation)}")
    
    print("\n" + "=" * 60)
    print("Test complete")
    
    return attestation


if __name__ == "__main__":
    asyncio.run(test_dual_attestation())