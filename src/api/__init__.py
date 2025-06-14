from fastapi import APIRouter

from .attestation import router as attestation_router
from .chat import router as chat_router
from .secretai import router as secretai_router
from .arweave import router as arweave_router
from .proofs import router as proofs_router
from .environment import router as environment_router

router = APIRouter()

# Include sub-routers
router.include_router(attestation_router, prefix="/attestation", tags=["attestation"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(secretai_router, prefix="/secretai", tags=["secretai"])
router.include_router(arweave_router, prefix="/arweave", tags=["arweave"])
router.include_router(proofs_router, prefix="/proofs", tags=["proofs"])
router.include_router(environment_router, prefix="/environment", tags=["environment"])

@router.get("/")
async def api_info():
    """API information endpoint"""
    return {
        "name": "attest_ai API",
        "version": "0.1.0",
        "endpoints": {
            "attestation": "/api/attestation",
            "chat": "/api/chat",
            "secretai": "/api/secretai",
            "arweave": "/api/arweave",
            "proofs": "/api/proofs",
            "environment": "/api/environment",
            "health": "/health"
        }
    }

__all__ = ["router"]