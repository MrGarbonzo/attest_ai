from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from ..attestation import AttestationData
from ..chat import ChatResponse
from ..arweave import UploadResult

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="Message to send to AI")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    user: str = Field(default="user", description="User identifier")
    upload_proof: bool = Field(default=True, description="Upload proof to Arweave")


class ChatResponseWithProof(BaseModel):
    """Response model with chat response and proof data"""
    chat: ChatResponse
    attestations: Dict[str, Any]
    proof_upload: Optional[UploadResult] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@router.post("/", response_model=ChatResponseWithProof)
async def send_chat_message(request: ChatRequest):
    """
    Send a message to Secret AI and capture dual attestation
    
    This endpoint:
    1. Captures self-attestation from the current VM
    2. Sends message to Secret AI
    3. Captures Secret AI attestation
    4. Optionally uploads proof to Arweave
    """
    from ..main import attestation_client
    
    # Import clients (they'll be initialized in main.py)
    try:
        from ..main import secret_ai_client, arweave_client
    except ImportError:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        # 1. Get self-attestation (always available)
        self_attestation = await attestation_client.fetch_attestation()
        
        # 2. Send message to Secret AI and get attestation
        chat_response, secret_ai_attestation = await secret_ai_client.send_message(
            prompt=request.message,
            user=request.user,
            session_id=request.session_id
        )
        
        # 3. Prepare attestations
        attestations = {
            "self": self_attestation.dict(),
            "secret_ai": secret_ai_attestation.dict() if secret_ai_attestation else None
        }
        
        # 4. Upload proof if requested
        proof_upload = None
        if request.upload_proof and arweave_client:
            chat_data = {
                "request": request.dict(),
                "response": chat_response.dict()
            }
            
            proof_upload = await arweave_client.create_attestation_proof(
                self_attestation=attestations["self"],
                secret_ai_attestation=attestations["secret_ai"],
                chat_data=chat_data
            )
        
        return ChatResponseWithProof(
            chat=chat_response,
            attestations=attestations,
            proof_upload=proof_upload
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """List available chat sessions"""
    # This is a placeholder - implement session management as needed
    return {
        "sessions": [],
        "note": "Session management not yet implemented"
    }


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    # This is a placeholder - implement history storage as needed
    return {
        "session_id": session_id,
        "messages": [],
        "note": "History storage not yet implemented"
    }