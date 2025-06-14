from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..attestation import AttestationData

router = APIRouter()


@router.get("/self", response_model=AttestationData)
async def get_self_attestation(force_refresh: bool = False):
    """
    Get self-attestation data from the current VM
    
    Args:
        force_refresh: Force refresh bypassing cache
    
    Returns:
        AttestationData with VM registers
    """
    from ..main import attestation_client
    
    if not attestation_client:
        raise HTTPException(status_code=503, detail="Attestation client not initialized")
    
    try:
        attestation = await attestation_client.fetch_attestation(force_refresh=force_refresh)
        return attestation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/self/cache")
async def get_cache_info():
    """Get information about the attestation cache"""
    from ..main import attestation_client
    
    if not attestation_client:
        raise HTTPException(status_code=503, detail="Attestation client not initialized")
    
    return attestation_client.get_cache_info()


@router.get("/status")
async def get_attestation_status():
    """Get overall attestation service status"""
    from ..main import attestation_client
    
    status = {
        "self_attestation": {
            "available": False,
            "endpoint": "http://localhost:29343/cpu.html"
        },
        "secret_ai_attestation": {
            "available": False,
            "note": "Not implemented yet"
        }
    }
    
    if attestation_client:
        status["self_attestation"]["available"] = await attestation_client.verify_availability()
    
    return status