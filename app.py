import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our modules
from secret_ai_client import SecretAIClient
from arweave_client import ArweaveClient
from attestation_client import AttestationClient
from encryption import EncryptionManager

# Initialize FastAPI
app = FastAPI(
    title="attest_ai",
    description="Cryptographic proofs for Secret AI interactions",
    version="1.0.0"
)

# Add CORS middleware for browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize clients
secret_ai = SecretAIClient()
arweave = ArweaveClient()
attestation = AttestationClient()
encryption = EncryptionManager()

# Request models
class ChatRequest(BaseModel):
    message: str
    password: str

class UploadRequest(BaseModel):
    proof: dict

class DecryptRequest(BaseModel):
    encrypted_proof: dict
    password: str

@app.get("/")
async def root():
    """Serve the main chat interface"""
    return FileResponse('static/index.html')

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "components": {
            "secret_ai": "ready",
            "attestation": "ready",
            "arweave": "ready",
            "encryption": "ready"
        }
    }

@app.get("/wallet-info")
async def wallet_info():
    """Get Arweave wallet information"""
    return await arweave.get_wallet_info()

@app.get("/self-attestation")
async def self_attestation():
    """Get self-attestation from attest_ai VM"""
    return await attestation.get_self_attestation()

@app.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with dual attestation"""
    try:
        # Validate inputs
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        if not request.password.strip():
            raise HTTPException(status_code=400, detail="Password cannot be empty")
        
        # 1. Send message to Secret AI
        print(f"Sending message to Secret AI: {request.message[:50]}...")
        ai_response = await secret_ai.send_message(request.message)
        
        # 2. Get self-attestation from our VM
        print("Getting self-attestation...")
        self_attest = await attestation.get_self_attestation()
        
        # 3. Attempt to get Secret AI VM attestation
        print("Getting Secret AI attestation...")
        secretai_attest = {"mock": True, "error": "Not implemented"}
        if not ai_response["mock"] and ai_response.get("instance_url"):
            secretai_attest = await secret_ai.get_attestation(ai_response["instance_url"])
        
        # 4. Encrypt conversation data
        print("Encrypting conversation...")
        encrypted_conversation = encryption.encrypt_conversation(
            request.message, 
            ai_response["response"], 
            request.password
        )
        
        # 5. Generate verification hashes
        message_hash = encryption.hash_data(request.message)
        response_hash = encryption.hash_data(ai_response["response"])
        interaction_hash = encryption.hash_data(f"{request.message}|{ai_response['response']}")
        
        # 6. Create complete proof
        proof = {
            "proof_id": f"proof_{int(datetime.utcnow().timestamp())}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "app_name": "attest_ai",
            
            # Encrypted conversation (only user can decrypt)
            "encrypted_conversation": encrypted_conversation,
            
            # Verification hashes (public)
            "verification": {
                "message_hash": message_hash,
                "response_hash": response_hash,
                "interaction_hash": interaction_hash
            },
            
            # Dual attestation
            "attestations": {
                "attest_ai_vm": {
                    "mr_td": self_attest.get("mr_td", ""),
                    "rtmr0": self_attest.get("rtmr0", ""),
                    "rtmr1": self_attest.get("rtmr1", ""),
                    "rtmr2": self_attest.get("rtmr2", ""),
                    "rtmr3": self_attest.get("rtmr3", ""),
                    "report_data": self_attest.get("report_data", ""),
                    "tls_fingerprint": self_attest.get("tls_fingerprint", ""),
                    "instance_url": "localhost:29343",
                    "status": "verified" if self_attest.get("success") else "error",
                    "timestamp": self_attest.get("timestamp", "")
                },
                "secret_ai_vm": {
                    "mr_td": secretai_attest.get("attestation", {}).get("mr_td", ""),
                    "rtmr0": secretai_attest.get("attestation", {}).get("rtmr0", ""),
                    "rtmr1": secretai_attest.get("attestation", {}).get("rtmr1", ""),
                    "rtmr2": secretai_attest.get("attestation", {}).get("rtmr2", ""),
                    "rtmr3": secretai_attest.get("attestation", {}).get("rtmr3", ""),
                    "instance_url": secretai_attest.get("instance_url", ""),
                    "model": ai_response.get("model", ""),
                    "status": "verified" if not secretai_attest.get("mock") else "mocked",
                    "timestamp": secretai_attest.get("attestation", {}).get("timestamp", "")
                }
            },
            
            # Cryptographic binding
            "cryptographic_binding": {
                "binding_hash": encryption.hash_data(
                    f"{interaction_hash}|{self_attest.get('mr_td', '')}|{secretai_attest.get('attestation', {}).get('mr_td', '')}"
                ),
                "method": "sha256_dual_attestation_v1"
            }
        }
        
        print("Proof generated successfully")
        
        return {
            "response": ai_response["response"],
            "proof": proof,
            "secret_ai_status": {
                "success": ai_response["success"],
                "mock": ai_response["mock"],
                "model": ai_response.get("model", ""),
                "instance_url": ai_response.get("instance_url", "")
            },
            "attestation_status": {
                "self_attestation": self_attest.get("success", False),
                "secret_ai_attestation": not secretai_attest.get("mock", True)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-to-arweave")
async def upload_to_arweave(request: UploadRequest):
    """Upload proof to Arweave"""
    try:
        if not request.proof:
            raise HTTPException(status_code=400, detail="No proof data provided")
            
        result = await arweave.upload_proof(request.proof)
        return result
    except Exception as e:
        print(f"Error uploading to Arweave: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decrypt-proof")
async def decrypt_proof(request: DecryptRequest):
    """Decrypt proof conversation data"""
    try:
        encrypted_data = request.encrypted_proof.get("encrypted_conversation", "")
        if not encrypted_data:
            raise HTTPException(status_code=400, detail="No encrypted conversation data found")
        
        # Attempt decryption
        try:
            conversation = encryption.decrypt_conversation(encrypted_data, request.password)
            
            return {
                "success": True,
                "conversation": conversation,
                "proof_metadata": {
                    "timestamp": request.encrypted_proof.get("timestamp"),
                    "proof_id": request.encrypted_proof.get("proof_id"),
                    "verification_hashes": request.encrypted_proof.get("verification", {})
                }
            }
        except Exception as decrypt_error:
            return {
                "success": False,
                "error": "Invalid password or corrupted proof data",
                "details": str(decrypt_error)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error decrypting proof: {e}")
        return {
            "success": False,
            "error": "Failed to decrypt proof",
            "details": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"Starting attest_ai on port {port} (debug={debug})")
    print(f"Secret AI API Key: {'Set' if os.getenv('SECRET_AI_API_KEY') else 'Not set'}")
    print(f"Arweave Mnemonic: {'Set' if os.getenv('ARWEAVE_MNEMONIC') else 'Not set'}")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=debug
    )