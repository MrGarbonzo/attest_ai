from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from ..utils.verification import ProofVerifier, VerificationResult

router = APIRouter()


class ProofVerificationRequest(BaseModel):
    """Request model for proof verification"""
    proof_data: Dict[str, Any] = Field(..., description="The proof data to verify")
    strict_mode: bool = Field(default=False, description="Enable strict verification mode")


class ArweaveVerificationRequest(BaseModel):
    """Request model for Arweave transaction verification"""
    transaction_id: str = Field(..., description="Arweave transaction ID")
    fetch_data: bool = Field(default=True, description="Fetch and verify the data")


@router.post("/verify", response_model=VerificationResult)
async def verify_proof(request: ProofVerificationRequest):
    """
    Verify a cryptographic proof for integrity and completeness
    
    This endpoint validates:
    - Proof structure and required fields
    - Cryptographic hash integrity
    - Attestation data completeness
    - Timestamp consistency
    """
    try:
        verifier = ProofVerifier()
        result = await verifier.verify_proof(request.proof_data)
        
        # In strict mode, treat warnings as errors
        if request.strict_mode and result.warnings:
            result.valid = False
            result.errors.extend([f"Warning (strict mode): {w}" for w in result.warnings])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/verify-arweave", response_model=VerificationResult)
async def verify_arweave_proof(request: ArweaveVerificationRequest):
    """
    Verify a proof stored on Arweave blockchain
    
    This endpoint:
    - Fetches proof data from Arweave transaction
    - Verifies transaction authenticity
    - Validates proof content
    """
    try:
        verifier = ProofVerifier()
        result = await verifier.verify_arweave_transaction(request.transaction_id)
        
        if not result.valid:
            # Return 422 for invalid proofs rather than 500
            raise HTTPException(
                status_code=422, 
                detail={
                    "message": "Proof verification failed",
                    "errors": result.errors,
                    "warnings": result.warnings
                }
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arweave verification failed: {str(e)}")


@router.get("/validation-schema")
async def get_validation_schema():
    """
    Get the validation schema for proof verification
    
    Returns the expected structure and requirements for valid proofs
    """
    return {
        "proof_structure": {
            "required_fields": ProofVerifier.REQUIRED_PROOF_FIELDS,
            "supported_versions": ["1.0"],
            "attestation_fields": ProofVerifier.REQUIRED_ATTESTATION_FIELDS
        },
        "validation_checks": [
            {
                "name": "proof_structure",
                "description": "Verify proof has required fields and structure",
                "critical": True
            },
            {
                "name": "proof_hash",
                "description": "Verify proof hash matches content",
                "critical": True
            },
            {
                "name": "attestations",
                "description": "Verify attestation data completeness and format",
                "critical": True
            },
            {
                "name": "timestamps",
                "description": "Verify timestamp consistency across proof",
                "critical": False
            }
        ],
        "example_proof": {
            "version": "1.0",
            "timestamp": "2025-01-01T00:00:00Z",
            "attestations": {
                "self": {
                    "mr_td": "0x1234567890abcdef",
                    "rtmr0": "0xabcdef1234567890",
                    "rtmr1": "0x1111111111111111",
                    "rtmr2": "0x2222222222222222",
                    "rtmr3": "0x3333333333333333",
                    "report_data": "0xdeadbeefdeadbeef",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "source": "self",
                    "vm_type": "attest_ai"
                },
                "secret_ai": {
                    "mr_td": "0x9876543210fedcba",
                    "rtmr0": "0xfedcba0987654321",
                    "rtmr1": "0x4444444444444444",
                    "rtmr2": "0x5555555555555555",
                    "rtmr3": "0x6666666666666666",
                    "report_data": "0xcafebabecafebabe",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "source": "secret_ai",
                    "vm_type": "secret_ai_vm"
                }
            },
            "chat": {
                "request": {"message": "Hello AI"},
                "response": {"message": "Hello human", "session_id": "test"}
            },
            "proof_hash": "calculated_sha256_hash_here"
        }
    }


@router.get("/stats")
async def get_verification_stats():
    """
    Get verification system statistics
    
    Returns metrics about proof verification performance
    """
    return {
        "system": "attest_ai_verification",
        "version": "1.0",
        "supported_operations": [
            "verify_proof",
            "verify_arweave",
            "validation_schema"
        ],
        "verification_levels": [
            "basic",  # Structure and hash only
            "standard",  # All checks, warnings allowed
            "strict"  # All checks, warnings treated as errors
        ],
        "note": "Verification statistics tracking not yet implemented"
    }