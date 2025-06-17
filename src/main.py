import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import get_settings
from src.attestation import SelfAttestationClient
from src.attestation.dual_attestation import DualAttestationManager
from src.secret_ai.client import SecretAIClient
from src.encryption.proof_manager import ProofManager

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
self_attestation_client: SelfAttestationClient = None
secret_ai_client: SecretAIClient = None
dual_attestation_manager: DualAttestationManager = None
proof_manager: ProofManager = None


# Request/Response Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="The chat message")
    proof_password: Optional[str] = Field(None, description="Password for automatic proof generation")
    model: Optional[str] = Field(None, description="Specific Secret AI model to use")
    base_url: Optional[str] = Field(None, description="Specific Secret AI base URL to use")


class ChatResponse(BaseModel):
    success: bool
    response: str
    attestations: dict
    proof_generated: bool = False
    proof_id: Optional[str] = None
    timestamp: str
    mode: str = "unknown"


class DecryptRequest(BaseModel):
    password: str = Field(..., description="Password for decryption")


class ProofStatusResponse(BaseModel):
    exists: bool
    proof_id: str
    file_size: Optional[int] = None
    created: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global self_attestation_client, secret_ai_client, dual_attestation_manager, proof_manager
    
    # Startup
    logger.info("Starting Attest AI MVP application...")
    
    # Initialize clients
    self_attestation_client = SelfAttestationClient(
        base_url=settings.self_attestation_url,
        cache_ttl=settings.attestation_cache_ttl
    )
    
    secret_ai_client = SecretAIClient()
    
    dual_attestation_manager = DualAttestationManager(
        self_attestation_client=self_attestation_client,
        secret_ai_client=secret_ai_client
    )
    
    proof_manager = ProofManager(
        downloads_dir=settings.downloads_dir,
        cleanup_hours=settings.proof_file_cleanup_hours
    )
    
    # Test connections on startup
    logger.info("Testing self-attestation connection...")
    attestation = await self_attestation_client.get_attestation()
    if attestation['status'] == 'success':
        logger.info("Self-attestation service connected successfully")
    else:
        logger.warning(f"Self-attestation service not available: {attestation.get('error', 'Unknown error')}")
    
    logger.info("Testing Secret AI connection...")
    models = await secret_ai_client.discover_models()
    if models and models[0].get("mode") == "real":
        logger.info(f"Secret AI connected - {len(models)} models available")
    else:
        logger.info("Secret AI using mock mode")
    
    # Create directories if needed
    os.makedirs(settings.downloads_dir, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Attest AI MVP application...")


# Create FastAPI app
app = FastAPI(
    title="Attest AI MVP",
    description="Privacy-preserving AI chat with cryptographic attestation",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root(request: Request):
    """Root endpoint - serves the main UI"""
    # Try to serve HTML file if it exists, otherwise return API info
    html_path = "templates/index.html"
    if os.path.exists(html_path):
        return FileResponse(html_path)
    else:
        return JSONResponse(
            content={
                "message": "Attest AI MVP API",
                "version": "0.1.0",
                "endpoints": {
                    "health": "/health",
                    "api_docs": "/docs",
                    "chat": "/api/v1/chat",
                    "models": "/api/v1/secret-ai/models",
                    "attestation_self": "/api/v1/attestation/self",
                    "attestation_dual": "/api/v1/attestation/dual",
                    "proof_download": "/api/v1/proof/download/{proof_id}",
                    "proof_decrypt": "/api/v1/proof/decrypt",
                    "proof_status": "/api/v1/proof/status/{proof_id}",
                    "proof_list": "/api/v1/proof/list"
                }
            }
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check self-attestation status
    attestation_status = "unknown"
    if self_attestation_client:
        attestation = await self_attestation_client.get_attestation()
        attestation_status = attestation['status']
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "components": {
            "api": "operational",
            "self_attestation": attestation_status,
            "downloads_dir": os.path.exists(settings.downloads_dir)
        }
    }


@app.get("/api/v1/attestation/self")
async def get_self_attestation():
    """Get self-attestation data"""
    if not self_attestation_client:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Self-attestation client not initialized",
                "status": "error"
            }
        )
    
    attestation = await self_attestation_client.get_attestation()
    return attestation


@app.get("/api/v1/secret-ai/models")
async def get_secret_ai_models():
    """Get available Secret AI models"""
    if not secret_ai_client:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Secret AI client not initialized",
                "status": "error"
            }
        )
    
    models = await secret_ai_client.discover_models()
    return {
        "models": models,
        "count": len(models),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with dual attestation and automatic proof generation"""
    
    # Validate message length
    if len(request.message) > settings.max_message_length:
        raise HTTPException(
            status_code=400,
            detail=f"Message too long. Maximum length is {settings.max_message_length} characters."
        )
    
    # Check if required services are available
    if not secret_ai_client or not dual_attestation_manager:
        raise HTTPException(
            status_code=503,
            detail="Required services not initialized"
        )
    
    try:
        logger.info(f"Processing chat request: '{request.message[:50]}...'")
        
        # Send message to Secret AI
        chat_response = await secret_ai_client.send_message(
            message=request.message,
            model=request.model,
            base_url=request.base_url
        )
        
        if not chat_response["success"]:
            raise HTTPException(
                status_code=500,
                detail="Failed to get AI response"
            )
        
        # Get dual attestation
        attestations = await dual_attestation_manager.get_dual_attestation(
            secret_ai_url=request.base_url or chat_response.get("base_url")
        )
        
        # Handle proof generation logic
        proof_generated = False
        proof_id = None
        
        if request.proof_password:
            try:
                # Create chat data for proof
                proof_chat_data = {
                    "message": request.message,
                    "response": chat_response["response"],
                    "model": chat_response.get("model", "unknown"),
                    "base_url": chat_response.get("base_url", "unknown"),
                    "mode": chat_response.get("mode", "unknown")
                }
                
                # Generate actual encrypted proof
                proof_id = await proof_manager.generate_proof(
                    chat_data=proof_chat_data,
                    attestations=attestations,
                    password=request.proof_password
                )
                proof_generated = True
                logger.info(f"Proof generated successfully with ID: {proof_id}")
                
            except Exception as e:
                logger.error(f"Failed to generate proof: {str(e)}")
                # Continue without proof generation
                proof_generated = False
                proof_id = None
        
        # Construct response
        response = ChatResponse(
            success=True,
            response=chat_response["response"],
            attestations=attestations,
            proof_generated=proof_generated,
            proof_id=proof_id,
            timestamp=datetime.utcnow().isoformat(),
            mode=chat_response.get("mode", "unknown")
        )
        
        logger.info(f"Chat response completed - Mode: {response.mode}, Proof: {proof_generated}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}" if settings.debug else "Internal server error"
        )


@app.get("/api/v1/attestation/dual")
async def get_dual_attestation():
    """Get dual attestation from both sources"""
    if not dual_attestation_manager:
        raise HTTPException(
            status_code=503,
            detail="Dual attestation manager not initialized"
        )
    
    attestation = await dual_attestation_manager.get_dual_attestation()
    return attestation


@app.get("/api/v1/proof/download/{proof_id}")
async def download_proof(proof_id: str):
    """Download a proof file by ID"""
    if not proof_manager:
        raise HTTPException(
            status_code=503,
            detail="Proof manager not initialized"
        )
    
    try:
        file_path = proof_manager.get_proof_file_path(proof_id)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Proof file not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=f"{proof_id}.attestproof",
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading proof {proof_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download proof file"
        )


@app.post("/api/v1/proof/decrypt")
async def decrypt_proof(
    file: UploadFile = File(...),
    password: str = Form(...)
):
    """Decrypt an uploaded proof file"""
    if not proof_manager:
        raise HTTPException(
            status_code=503,
            detail="Proof manager not initialized"
        )
    
    # Validate file extension
    if not file.filename.endswith('.attestproof'):
        raise HTTPException(
            status_code=400,
            detail="File must be a .attestproof file"
        )
    
    try:
        # Read file data
        file_data = await file.read()
        
        # Decrypt the proof
        decrypted_data = proof_manager.decrypt_proof_file(file_data, password)
        
        return {
            "success": True,
            "filename": file.filename,
            "proof_data": decrypted_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        # Decryption failed (wrong password, corrupted file, etc.)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error decrypting proof file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to decrypt proof file"
        )


@app.get("/api/v1/proof/status/{proof_id}", response_model=ProofStatusResponse)
async def get_proof_status(proof_id: str):
    """Get status of a proof file"""
    if not proof_manager:
        raise HTTPException(
            status_code=503,
            detail="Proof manager not initialized"
        )
    
    try:
        file_path = proof_manager.get_proof_file_path(proof_id)
        
        if os.path.exists(file_path):
            file_stat = os.stat(file_path)
            return ProofStatusResponse(
                exists=True,
                proof_id=proof_id,
                file_size=file_stat.st_size,
                created=datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            )
        else:
            return ProofStatusResponse(
                exists=False,
                proof_id=proof_id
            )
            
    except Exception as e:
        logger.error(f"Error checking proof status {proof_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check proof status"
        )


@app.get("/api/v1/proof/list")
async def list_proofs():
    """List all available proof files"""
    if not proof_manager:
        raise HTTPException(
            status_code=503,
            detail="Proof manager not initialized"
        )
    
    try:
        proof_files = proof_manager.list_proof_files()
        return {
            "proof_files": proof_files,
            "count": len(proof_files),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing proofs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list proof files"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )