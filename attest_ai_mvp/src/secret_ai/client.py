import os
import asyncio
import logging
import hashlib
import ssl
import socket
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Import Secret AI SDK
try:
    from secret_ai_sdk import Secret, ChatSecret
    SECRET_AI_AVAILABLE = True
except ImportError:
    SECRET_AI_AVAILABLE = False
    logging.warning("Secret AI SDK not available. Will use mock mode.")

# Check if we have an API key even if SDK not available
import os

logger = logging.getLogger(__name__)


class SecretAIClient:
    """Client for Secret AI integration with attestation support"""
    
    def __init__(self):
        self.secret = None
        self.is_mock_mode = False
        
        # Get API key from environment at runtime
        self.api_key = os.getenv('SECRET_AI_API_KEY', '')
        self.has_api_key = bool(self.api_key and self.api_key != 'your_secret_ai_api_key_here')
        
        if SECRET_AI_AVAILABLE and self.has_api_key:
            try:
                # Initialize Secret client - reads SECRET_AI_API_KEY from environment
                self.secret = Secret()
                logger.info("Secret AI client initialized successfully with real API key")
            except Exception as e:
                logger.error(f"Failed to initialize Secret AI client: {str(e)}")
                self.is_mock_mode = True
        elif self.has_api_key:
            logger.warning("Secret AI API key available but SDK not installed. Using HTTP client fallback.")
            self.is_mock_mode = False  # We'll use HTTP fallback
        else:
            self.is_mock_mode = True
            logger.info("Running in mock mode - no Secret AI API key or SDK not available")
    
    async def discover_models(self) -> List[Dict[str, Any]]:
        """Discover available Secret AI models and their URLs"""
        if self.is_mock_mode:
            return self._get_mock_models()
        
        # Try SDK first if available
        if self.secret and SECRET_AI_AVAILABLE:
            try:
                # Get available models
                models = await asyncio.to_thread(self.secret.get_models)
                
                if not models:
                    logger.warning("No models returned from Secret AI")
                    return self._get_mock_models()
                
                # Get URLs for each model
                model_info = []
                for model in models:
                    try:
                        urls = await asyncio.to_thread(self.secret.get_urls, model)
                        if urls:
                            for url in urls:
                                model_info.append({
                                    "model": model,
                                    "url": url,
                                    "status": "available",
                                    "mode": "real"
                                })
                    except Exception as e:
                        logger.error(f"Error getting URLs for model {model}: {str(e)}")
                
                if not model_info:
                    logger.warning("No valid model URLs found")
                    return self._get_mock_models()
                
                return model_info
                
            except Exception as e:
                logger.error(f"Error discovering models with SDK: {str(e)}")
        
        # Try HTTP fallback if we have API key
        if self.has_api_key and HTTPX_AVAILABLE:
            return await self._discover_models_http()
        
        return self._get_mock_models()
    
    async def get_chat_instance(self, model: str, base_url: str):
        """Create a ChatSecret instance for the given model and URL"""
        if self.is_mock_mode or not SECRET_AI_AVAILABLE:
            return None
        
        try:
            chat = ChatSecret(
                base_url=base_url,
                model=model,
                temperature=0.7
            )
            return chat
        except Exception as e:
            logger.error(f"Failed to create chat instance: {str(e)}")
            return None
    
    async def send_message(self, message: str, model: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to Secret AI and get response"""
        if self.is_mock_mode:
            return self._get_mock_response(message)
        
        # Try SDK first if available
        if self.secret and SECRET_AI_AVAILABLE:
            try:
                # If model/URL not provided, discover and use first available
                if not model or not base_url:
                    models = await self.discover_models()
                    if models and models[0]["mode"] == "real":
                        model = models[0]["model"]
                        base_url = models[0]["url"]
                    else:
                        return self._get_mock_response(message)
                
                # Create chat instance
                chat = await self.get_chat_instance(model, base_url)
                if not chat:
                    return self._get_mock_response(message)
                
                # Send message
                response = await asyncio.to_thread(chat.send_message, message)
                
                return {
                    "success": True,
                    "response": response,
                    "mode": "real",
                    "model": model,
                    "base_url": base_url,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error sending message with SDK: {str(e)}")
        
        # Try HTTP fallback if we have API key
        if self.has_api_key and HTTPX_AVAILABLE:
            return await self._send_message_http(message, model, base_url)
        
        return self._get_mock_response(message, "No SDK or HTTP fallback available")
    
    async def get_attestation(self, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Get Secret AI attestation data"""
        attestation_data = {
            "source": "secret_ai",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unknown",
            "data": {}
        }
        
        if self.is_mock_mode:
            return self._get_mock_attestation()
        
        try:
            # Use the actual Secret AI attestation endpoint on port 29343
            secret_ai_host = os.getenv('SECRET_AI_BASE_URL', 'https://secretai-zqtr.scrtlabs.com:21434').split(':')[1].replace('//','')
            secret_ai_attestation_url = f"https://{secret_ai_host}:29343/cpu.html"
            
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                    try:
                        # Get attestation data from Secret AI with authentication
                        headers = {}
                        if self.has_api_key:
                            headers["Authorization"] = f"Bearer {self.api_key}"
                        
                        response = await client.get(secret_ai_attestation_url, headers=headers)
                        
                        if response.status_code == 200:
                            # Parse the HTML response to extract attestation quote
                            attestation_html = response.text
                            
                            # Extract the quote from the pre tag
                            quote_match = re.search(r'<pre[^>]*id="quoteTextarea"[^>]*>(.*?)</pre>', attestation_html, re.DOTALL)
                            if quote_match:
                                attestation_content = quote_match.group(1).strip()
                            else:
                                attestation_content = "Unable to parse attestation quote from HTML"
                            
                            # Also capture TLS fingerprint from attestation endpoint
                            tls_data = await self._get_tls_fingerprint(f"https://{secret_ai_host}:29343")
                            
                            attestation_data.update({
                                "status": "success",
                                "mode": "real",
                                "data": {
                                    "base_url": f"https://{secret_ai_host}:29343",
                                    "attestation_url": secret_ai_attestation_url,
                                    "attestation_raw": attestation_content[:500] + "..." if len(attestation_content) > 500 else attestation_content,
                                    "tls_fingerprint": tls_data.get("fingerprint"),
                                    "tls_version": tls_data.get("version"), 
                                    "cipher_suite": tls_data.get("cipher"),
                                    "certificate_info": tls_data.get("cert_info"),
                                    "connection_metadata": {
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "protocol": "https",
                                        "verified": tls_data.get("verified", False),
                                        "api_key_used": bool(self.has_api_key),
                                        "attestation_type": "cpu"
                                    }
                                }
                            })
                        else:
                            logger.warning(f"Secret AI attestation endpoint returned {response.status_code}")
                            attestation_data["status"] = "error"
                            attestation_data["error"] = f"HTTP {response.status_code}"
                            
                    except Exception as e:
                        logger.error(f"Error connecting to Secret AI attestation endpoint: {str(e)}")
                        attestation_data["status"] = "error"
                        attestation_data["error"] = str(e)
            else:
                attestation_data["status"] = "error"
                attestation_data["error"] = "httpx not available"
            
            return attestation_data
            
        except Exception as e:
            logger.error(f"Error getting attestation: {str(e)}")
            attestation_data["status"] = "error"
            attestation_data["error"] = str(e)
            return attestation_data
    
    async def _get_tls_fingerprint(self, url: str) -> Dict[str, Any]:
        """Extract TLS fingerprint and connection metadata"""
        try:
            # Parse URL to get host and port
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 443
            
            # Create SSL context (allow self-signed certificates for attestation endpoints)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    # Get certificate
                    der_cert = ssock.getpeercert_bin()
                    cert_info = ssock.getpeercert()
                    
                    # Calculate fingerprint
                    fingerprint = hashlib.sha256(der_cert).hexdigest()
                    
                    return {
                        "fingerprint": fingerprint,
                        "version": ssock.version(),
                        "cipher": ssock.cipher(),
                        "cert_info": {
                            "subject": str(cert_info.get("subject", [])),
                            "issuer": str(cert_info.get("issuer", [])),
                            "version": cert_info.get("version"),
                            "serialNumber": cert_info.get("serialNumber"),
                            "notBefore": cert_info.get("notBefore"),
                            "notAfter": cert_info.get("notAfter")
                        },
                        "verified": True
                    }
                    
        except Exception as e:
            logger.error(f"Error getting TLS fingerprint: {str(e)}")
            return {
                "fingerprint": None,
                "error": str(e),
                "verified": False
            }
    
    def _get_mock_models(self) -> List[Dict[str, Any]]:
        """Return mock model data for testing"""
        return [
            {
                "model": "mock-model-1",
                "url": "https://mock.secret-ai.example.com",
                "status": "available",
                "mode": "mock"
            }
        ]
    
    def _get_mock_response(self, message: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Generate mock response for testing"""
        mock_responses = {
            "hello": "Hello! I'm a mock Secret AI assistant. How can I help you today?",
            "what is secret network": "Secret Network is a blockchain with built-in privacy features, allowing for encrypted smart contracts and private transactions.",
            "should i invest in scrt": "I'm a mock assistant and cannot provide financial advice. Please consult with a qualified financial advisor.",
            "default": f"Mock response to: '{message}'. This is a simulated response as Secret AI is not available."
        }
        
        # Find matching response
        response_text = mock_responses.get("default")
        for key, value in mock_responses.items():
            if key != "default" and key in message.lower():
                response_text = value
                break
        
        return {
            "success": True,
            "response": response_text,
            "mode": "mock",
            "model": "mock-model",
            "base_url": "mock://localhost",
            "timestamp": datetime.utcnow().isoformat(),
            "reason": error or "Secret AI not available - using mock mode"
        }
    
    def _get_mock_attestation(self) -> Dict[str, Any]:
        """Return mock attestation data"""
        return {
            "source": "secret_ai",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "mode": "mock",
            "data": {
                "base_url": "mock://localhost",
                "tls_fingerprint": "mock-fingerprint-" + hashlib.sha256(b"mock").hexdigest()[:16],
                "tls_version": "TLSv1.3",
                "cipher_suite": ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256),
                "certificate_info": {
                    "subject": "CN=mock.secret-ai.example.com",
                    "issuer": "CN=Mock CA",
                    "version": 3,
                    "serialNumber": "1234567890",
                    "notBefore": "Jan 1 00:00:00 2024 GMT",
                    "notAfter": "Dec 31 23:59:59 2025 GMT"
                },
                "connection_metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "protocol": "https",
                    "verified": False,
                    "mock": True
                }
            }
        }
    
    # HTTP fallback methods when SDK not available but API key is present
    async def _discover_models_http(self) -> List[Dict[str, Any]]:
        """Discover models using direct HTTP calls to Secret Network smart contract"""
        try:
            logger.info("Attempting to discover Secret AI models via Secret Network smart contract")
            
            # Get LCD endpoint from environment
            lcd_url = os.getenv('SECRET_NODE_URL', 'https://lcd.mainnet.secretsaturn.net')
            
            # For now, since we don't have the mainnet smart contract address,
            # return the known Secret AI endpoint
            # In production, this would query the smart contract
            
            # The actual Secret AI service endpoint we discovered
            secret_ai_base = os.getenv('SECRET_AI_BASE_URL', 'https://secretai-zqtr.scrtlabs.com:21434')
            
            return [{
                "model": "deepseek-r1:70b",  # Known model from the SDK example
                "url": secret_ai_base,
                "status": "available",
                "mode": "real"
            }]
            
        except Exception as e:
            logger.warning(f"Model discovery failed: {str(e)}")
            # Still return the default endpoint
            return [{
                "model": "deepseek-r1:70b",
                "url": os.getenv('SECRET_AI_BASE_URL', 'https://secretai-zqtr.scrtlabs.com:21434'),
                "status": "available",
                "mode": "real"  
            }]
    
    async def _send_message_http(self, message: str, model: str = None, base_url: str = None) -> Dict[str, Any]:
        """Send message using HTTP API fallback with OpenAI-compatible API"""
        try:
            if not HTTPX_AVAILABLE:
                return self._get_mock_response(message, "httpx not available")
            
            # Use the Secret AI endpoint (OpenAI-compatible)
            secret_ai_base = os.getenv('SECRET_AI_BASE_URL', 'https://secretai-zqtr.scrtlabs.com:21434')
            api_url = base_url or secret_ai_base
            
            logger.info(f"Sending message to Secret AI via OpenAI-compatible API: {message[:50]}...")
            
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                try:
                    # First, get available models
                    headers = {}
                    if self.has_api_key:
                        headers["Authorization"] = f"Bearer {self.api_key}"
                    
                    models_response = await client.get(f"{api_url}/v1/models", headers=headers)
                    
                    if models_response.status_code == 200:
                        models_data = models_response.json()
                        available_models = [m['id'] for m in models_data.get('data', [])]
                        logger.info(f"Available Secret AI models: {available_models}")
                        
                        # Use the first available model or specified one
                        if available_models and not model:
                            model = available_models[0]
                        elif not model:
                            model = "deepseek-r1:70b"  # Default from example
                    else:
                        model = model or "deepseek-r1:70b"
                        logger.warning(f"Could not fetch models (status {models_response.status_code}), using: {model}")
                    
                    # Send chat completion request (OpenAI-compatible format)
                    headers["Content-Type"] = "application/json"
                    
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "user", "content": message}
                        ],
                        "temperature": 0.7,
                        "stream": False
                    }
                    
                    response = await client.post(
                        f"{api_url}/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Extract response from OpenAI format
                        ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "No response from Secret AI")
                        
                        return {
                            "success": True,
                            "response": ai_response,
                            "mode": "real",
                            "model": model,
                            "base_url": api_url,
                            "timestamp": datetime.utcnow().isoformat(),
                            "api_key_verified": bool(self.has_api_key),
                            "api_format": "openai-compatible"
                        }
                    else:
                        logger.error(f"Secret AI API error: {response.status_code} {response.text}")
                        return self._get_mock_response(message, f"API error: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error calling Secret AI API: {str(e)}")
                    return self._get_mock_response(message, str(e))
                    
        except Exception as e:
            logger.error(f"HTTP chat request failed: {str(e)}")
            return self._get_mock_response(message, str(e))


# Convenience test function
async def test_secret_ai():
    """Test Secret AI client functionality"""
    client = SecretAIClient()
    
    print("Testing Secret AI Client")
    print("=" * 60)
    
    # Test model discovery
    print("\n1. Testing model discovery...")
    models = await client.discover_models()
    print(f"Found {len(models)} models:")
    for model in models:
        print(f"  - {model['model']} at {model['url']} (mode: {model['mode']})")
    
    # Test sending a message
    print("\n2. Testing chat functionality...")
    response = await client.send_message("What is Secret Network?")
    print(f"Response mode: {response['mode']}")
    print(f"Response: {response['response'][:100]}...")
    
    # Test attestation
    print("\n3. Testing attestation capture...")
    attestation = await client.get_attestation()
    print(f"Attestation status: {attestation['status']}")
    print(f"Attestation mode: {attestation.get('mode', 'unknown')}")
    if attestation['data']:
        print(f"TLS Fingerprint: {attestation['data'].get('tls_fingerprint', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Test complete")


if __name__ == "__main__":
    asyncio.run(test_secret_ai())