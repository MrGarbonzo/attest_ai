from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

router = APIRouter()


class ArweaveUploadRequest(BaseModel):
    """Request model for manual Arweave upload"""
    data: Dict[str, Any] = Field(..., description="Data to upload")
    tags: Optional[Dict[str, str]] = Field(None, description="Transaction tags")
    force_mock: bool = Field(default=False, description="Force mock upload")


@router.get("/status")
async def get_arweave_status():
    """Get Arweave wallet status and capabilities"""
    try:
        from ..main import arweave_client
    except ImportError:
        return {
            "service": "arweave",
            "status": "not_initialized",
            "error": "Arweave client not initialized"
        }
    
    try:
        wallet_info = await arweave_client.get_wallet_info()
        
        # Add service status
        wallet_info["service"] = "arweave"
        wallet_info["status"] = "healthy" if wallet_info.get("initialized") else "unhealthy"
        wallet_info["upload_enabled"] = arweave_client.settings.ENABLE_ARWEAVE_UPLOAD
        wallet_info["mock_unfunded"] = arweave_client.settings.MOCK_UNFUNDED_TRANSACTIONS
        
        return wallet_info
    except Exception as e:
        return {
            "service": "arweave",
            "status": "error",
            "error": str(e)
        }


@router.post("/upload")
async def upload_to_arweave(request: ArweaveUploadRequest):
    """
    Upload data to Arweave
    
    Smart upload logic:
    - Real upload if wallet is funded
    - Mock upload if wallet is unfunded (unless disabled)
    """
    try:
        from ..main import arweave_client
    except ImportError:
        raise HTTPException(status_code=503, detail="Arweave client not initialized")
    
    try:
        result = await arweave_client.upload_data(
            data=request.data,
            tags=request.tags,
            force_mock=request.force_mock
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.reason)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate-cost")
async def estimate_upload_cost(data_size_kb: float):
    """
    Estimate cost for uploading data
    
    Args:
        data_size_kb: Size of data in kilobytes
    """
    try:
        from ..main import arweave_client
    except ImportError:
        raise HTTPException(status_code=503, detail="Arweave client not initialized")
    
    try:
        data_size_bytes = int(data_size_kb * 1024)
        estimate = arweave_client.estimate_upload_cost(data_size_bytes)
        
        # Add current wallet balance for comparison
        wallet_info = await arweave_client.get_wallet_info()
        estimate["wallet_balance_ar"] = wallet_info.get("balance_ar", 0)
        estimate["sufficient_funds"] = (
            wallet_info.get("balance_ar", 0) > estimate["estimated_cost_ar"]
        )
        
        return estimate
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))