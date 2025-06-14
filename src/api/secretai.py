from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ..chat import SecretAIInstance

router = APIRouter()


@router.get("/instances", response_model=List[SecretAIInstance])
async def discover_instances(force_refresh: bool = False):
    """
    Discover available Secret AI instances
    
    Args:
        force_refresh: Force refresh bypassing cache
    """
    try:
        from ..main import secret_ai_client
    except ImportError:
        raise HTTPException(status_code=503, detail="Secret AI client not initialized")
    
    try:
        instances = await secret_ai_client.discover_instances(force_refresh=force_refresh)
        return instances
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_secret_ai_health():
    """Check Secret AI service health"""
    try:
        from ..main import secret_ai_client
    except ImportError:
        return {
            "service": "secret_ai",
            "status": "not_initialized",
            "error": "Secret AI client not initialized"
        }
    
    try:
        health = await secret_ai_client.check_health()
        return health
    except Exception as e:
        return {
            "service": "secret_ai",
            "status": "error",
            "error": str(e)
        }


@router.post("/select-instance")
async def select_instance(model: str = None):
    """
    Select a specific Secret AI instance
    
    Args:
        model: Model name to select
    """
    try:
        from ..main import secret_ai_client
    except ImportError:
        raise HTTPException(status_code=503, detail="Secret AI client not initialized")
    
    try:
        instance = await secret_ai_client.select_instance(model=model)
        if instance:
            return {
                "success": True,
                "instance": instance.dict()
            }
        else:
            raise HTTPException(status_code=404, detail="No suitable instance found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))