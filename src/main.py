import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .config import get_settings
from .api import router as api_router
from .attestation import SelfAttestationClient
from .chat import SecretAIClient
from .arweave import ArweaveClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global clients
attestation_client = None
secret_ai_client = None
arweave_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global attestation_client, secret_ai_client, arweave_client
    
    # Startup
    logger.info("Starting attest_ai application...")
    settings = get_settings()
    
    # Initialize self-attestation client
    attestation_client = SelfAttestationClient()
    await attestation_client.__aenter__()
    
    # Verify self-attestation availability
    if await attestation_client.verify_availability():
        logger.info("Self-attestation endpoint is available")
    else:
        logger.warning("Self-attestation endpoint is not available")
    
    # Initialize Secret AI client
    try:
        secret_ai_client = SecretAIClient()
        health = await secret_ai_client.check_health()
        logger.info(f"Secret AI client initialized: {health['status']}")
    except Exception as e:
        logger.warning(f"Secret AI client initialization failed: {e}")
        secret_ai_client = None
    
    # Initialize Arweave client
    try:
        arweave_client = ArweaveClient()
        wallet_info = await arweave_client.get_wallet_info()
        if wallet_info.get("initialized"):
            logger.info(f"Arweave client initialized: {wallet_info['address']}")
        else:
            logger.warning("Arweave wallet not properly initialized")
    except Exception as e:
        logger.warning(f"Arweave client initialization failed: {e}")
        arweave_client = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down attest_ai application...")
    if attestation_client:
        await attestation_client.__aexit__(None, None, None)


# Create FastAPI app
app = FastAPI(
    title="attest_ai",
    description="Cryptographic proof generation for AI interactions in SecretVM",
    version="0.1.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    template_path = Path(__file__).parent.parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>attest_ai</title>
        </head>
        <body>
            <h1>attest_ai</h1>
            <p>Cryptographic proof generation for AI interactions in SecretVM</p>
            <p>API available at <a href="/api">/api</a></p>
        </body>
        </html>
        """)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/monitoring"""
    global attestation_client, secret_ai_client, arweave_client
    
    health_status = {
        "status": "healthy",
        "version": "0.1.0",
        "services": {}
    }
    
    # Check self-attestation
    if attestation_client:
        health_status["services"]["self_attestation"] = {
            "available": await attestation_client.verify_availability()
        }
    else:
        health_status["services"]["self_attestation"] = {"available": False}
    
    # Check Secret AI
    if secret_ai_client:
        secret_ai_health = await secret_ai_client.check_health()
        health_status["services"]["secret_ai"] = secret_ai_health
    else:
        health_status["services"]["secret_ai"] = {"status": "not_initialized"}
    
    # Check Arweave
    if arweave_client:
        arweave_status = await arweave_client.get_wallet_info()
        health_status["services"]["arweave"] = {
            "initialized": arweave_status.get("initialized", False),
            "funded": arweave_status.get("funded", False)
        }
    else:
        health_status["services"]["arweave"] = {"initialized": False}
    
    # Overall status
    critical_services_ok = health_status["services"]["self_attestation"]["available"]
    if not critical_services_ok:
        health_status["status"] = "degraded"
    
    return health_status


def run():
    """Run the application"""
    settings = get_settings()
    
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level="info" if settings.APP_DEBUG else "warning"
    )


if __name__ == "__main__":
    run()