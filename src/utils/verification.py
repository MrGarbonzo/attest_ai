"""
Proof verification utilities for cryptographic validation
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

from .crypto import hash_data
from .exceptions import AttestAIException, ErrorCode

logger = logging.getLogger(__name__)


class VerificationResult(BaseModel):
    """Result of proof verification"""
    valid: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    proof_id: Optional[str] = None
    verification_hash: Optional[str] = None


class ProofVerifier:
    """Cryptographic proof verification system"""
    
    REQUIRED_PROOF_FIELDS = [
        "version", "timestamp", "attestations", "proof_hash"
    ]
    
    REQUIRED_ATTESTATION_FIELDS = [
        "mr_td", "rtmr0", "rtmr1", "rtmr2", "rtmr3", "report_data", 
        "timestamp", "source", "vm_type"
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def verify_proof(self, proof_data: Dict[str, Any]) -> VerificationResult:
        """
        Verify a complete attestation proof
        
        Args:
            proof_data: The proof data to verify
            
        Returns:
            VerificationResult with validation details
        """
        result = VerificationResult()
        
        try:
            # 1. Verify proof structure
            structure_check = self._verify_proof_structure(proof_data)
            result.checks.append(structure_check)
            
            if not structure_check["passed"]:
                result.valid = False
                result.errors.extend(structure_check.get("errors", []))
                return result
            
            # 2. Verify proof hash integrity
            hash_check = self._verify_proof_hash(proof_data)
            result.checks.append(hash_check)
            
            if not hash_check["passed"]:
                result.valid = False
                result.errors.extend(hash_check.get("errors", []))
            
            # 3. Verify attestation data
            attestation_check = self._verify_attestations(proof_data.get("attestations", {}))
            result.checks.append(attestation_check)
            
            if not attestation_check["passed"]:
                result.valid = False
                result.errors.extend(attestation_check.get("errors", []))
                result.warnings.extend(attestation_check.get("warnings", []))
            
            # 4. Verify timestamps
            timestamp_check = self._verify_timestamps(proof_data)
            result.checks.append(timestamp_check)
            
            if not timestamp_check["passed"]:
                result.warnings.extend(timestamp_check.get("warnings", []))
            
            # 5. Generate verification hash
            result.verification_hash = self._generate_verification_hash(proof_data, result)
            result.proof_id = proof_data.get("proof_hash", "unknown")[:16]
            
            # Overall validity
            result.valid = all(check["passed"] for check in result.checks if check.get("critical", True))
            
            self.logger.info(f"Proof verification completed: valid={result.valid}")
            
        except Exception as e:
            self.logger.error(f"Error during proof verification: {e}")
            result.valid = False
            result.errors.append(f"Verification failed: {str(e)}")
        
        return result
    
    def _verify_proof_structure(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the basic structure of the proof"""
        check = {
            "name": "proof_structure",
            "description": "Verify proof has required fields and structure",
            "passed": True,
            "critical": True,
            "errors": [],
            "details": {}
        }
        
        # Check required fields
        missing_fields = []
        for field in self.REQUIRED_PROOF_FIELDS:
            if field not in proof_data:
                missing_fields.append(field)
        
        if missing_fields:
            check["passed"] = False
            check["errors"].append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check version
        version = proof_data.get("version")
        if version != "1.0":
            check["errors"].append(f"Unsupported proof version: {version}")
            check["passed"] = False
        
        # Check attestations structure
        attestations = proof_data.get("attestations", {})
        if not isinstance(attestations, dict):
            check["passed"] = False
            check["errors"].append("Attestations must be a dictionary")
        elif "self" not in attestations:
            check["passed"] = False
            check["errors"].append("Missing self-attestation data")
        
        check["details"] = {
            "version": version,
            "has_attestations": "attestations" in proof_data,
            "attestation_sources": list(attestations.keys()) if isinstance(attestations, dict) else []
        }
        
        return check
    
    def _verify_proof_hash(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the proof hash integrity"""
        check = {
            "name": "proof_hash",
            "description": "Verify proof hash matches content",
            "passed": True,
            "critical": True,
            "errors": [],
            "details": {}
        }
        
        stored_hash = proof_data.get("proof_hash")
        if not stored_hash:
            check["passed"] = False
            check["errors"].append("No proof hash found")
            return check
        
        # Calculate expected hash (excluding the hash field itself)
        proof_copy = proof_data.copy()
        proof_copy.pop("proof_hash", None)
        
        try:
            calculated_hash = hash_data(proof_copy)
            
            if calculated_hash != stored_hash:
                check["passed"] = False
                check["errors"].append("Proof hash mismatch - data may have been tampered with")
            
            check["details"] = {
                "stored_hash": stored_hash,
                "calculated_hash": calculated_hash,
                "match": calculated_hash == stored_hash
            }
            
        except Exception as e:
            check["passed"] = False
            check["errors"].append(f"Failed to calculate proof hash: {str(e)}")
        
        return check
    
    def _verify_attestations(self, attestations: Dict[str, Any]) -> Dict[str, Any]:
        """Verify attestation data integrity"""
        check = {
            "name": "attestations",
            "description": "Verify attestation data completeness and format",
            "passed": True,
            "critical": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        verified_attestations = {}
        
        for source, attestation in attestations.items():
            if not attestation:
                check["errors"].append(f"Empty attestation data for {source}")
                check["passed"] = False
                continue
            
            # Check required fields
            missing_fields = []
            for field in self.REQUIRED_ATTESTATION_FIELDS:
                if field not in attestation:
                    missing_fields.append(field)
            
            if missing_fields:
                check["errors"].append(f"Missing fields in {source} attestation: {', '.join(missing_fields)}")
                check["passed"] = False
            
            # Verify hex register values
            hex_fields = ["mr_td", "rtmr0", "rtmr1", "rtmr2", "rtmr3", "report_data"]
            for field in hex_fields:
                value = attestation.get(field)
                if value and not self._is_valid_hex(value):
                    check["warnings"].append(f"Invalid hex format in {source}.{field}: {value}")
            
            # Verify source consistency
            expected_source = "self" if source == "self" else "secret_ai"
            actual_source = attestation.get("source", "")
            if not actual_source.startswith(expected_source):
                check["warnings"].append(f"Source mismatch in {source}: expected {expected_source}, got {actual_source}")
            
            verified_attestations[source] = {
                "valid": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "hex_fields_valid": all(
                    self._is_valid_hex(attestation.get(field, "")) 
                    for field in hex_fields
                ),
                "timestamp": attestation.get("timestamp"),
                "vm_type": attestation.get("vm_type")
            }
        
        check["details"] = {"attestations": verified_attestations}
        
        return check
    
    def _verify_timestamps(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify timestamp consistency and reasonableness"""
        check = {
            "name": "timestamps",
            "description": "Verify timestamp consistency across proof",
            "passed": True,
            "critical": False,  # Timestamp issues are warnings, not critical errors
            "warnings": [],
            "details": {}
        }
        
        try:
            proof_timestamp = proof_data.get("timestamp")
            if proof_timestamp:
                proof_time = datetime.fromisoformat(proof_timestamp.replace('Z', '+00:00'))
                now = datetime.utcnow()
                
                # Check if proof is too old (more than 1 week) or from the future
                age_days = (now - proof_time).days
                if age_days > 7:
                    check["warnings"].append(f"Proof is {age_days} days old - may be stale")
                elif age_days < 0:
                    check["warnings"].append("Proof timestamp is in the future")
                
                # Check attestation timestamps
                attestations = proof_data.get("attestations", {})
                for source, attestation in attestations.items():
                    att_timestamp = attestation.get("timestamp")
                    if att_timestamp:
                        att_time = datetime.fromisoformat(att_timestamp.replace('Z', '+00:00'))
                        time_diff = abs((proof_time - att_time).total_seconds())
                        
                        # Attestations should be close to proof time (within 1 hour)
                        if time_diff > 3600:
                            check["warnings"].append(
                                f"{source} attestation timestamp differs by {time_diff:.0f} seconds from proof"
                            )
                
                check["details"] = {
                    "proof_timestamp": proof_timestamp,
                    "age_days": age_days,
                    "future": age_days < 0
                }
        
        except Exception as e:
            check["warnings"].append(f"Error verifying timestamps: {str(e)}")
        
        return check
    
    def _is_valid_hex(self, value: str) -> bool:
        """Check if a value is a valid hexadecimal string"""
        if not value:
            return False
        
        # Remove 0x prefix if present
        hex_value = value[2:] if value.startswith('0x') else value
        
        try:
            int(hex_value, 16)
            return len(hex_value) > 0
        except ValueError:
            return False
    
    def _generate_verification_hash(self, proof_data: Dict[str, Any], result: VerificationResult) -> str:
        """Generate a hash for this verification"""
        verification_data = {
            "proof_hash": proof_data.get("proof_hash"),
            "verification_timestamp": result.timestamp.isoformat(),
            "checks_passed": [check["name"] for check in result.checks if check["passed"]],
            "valid": result.valid
        }
        
        return hash_data(verification_data)
    
    async def verify_arweave_transaction(self, transaction_id: str) -> VerificationResult:
        """
        Verify a proof stored on Arweave (placeholder for future implementation)
        
        Args:
            transaction_id: Arweave transaction ID
            
        Returns:
            VerificationResult
        """
        result = VerificationResult()
        result.valid = False
        result.errors.append("Arweave transaction verification not yet implemented")
        result.proof_id = transaction_id
        
        # TODO: Implement Arweave transaction fetching and verification
        # This would involve:
        # 1. Fetching the transaction data from Arweave
        # 2. Verifying the transaction signature
        # 3. Verifying the proof data within the transaction
        
        return result