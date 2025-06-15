import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class SecretAIClient:
    def __init__(self):
        self.api_key = os.getenv("SECRET_AI_API_KEY")
        if not self.api_key:
            raise ValueError("SECRET_AI_API_KEY environment variable required")
        
        # Initialize Secret client
        self._init_secret_client()
        
    def _init_secret_client(self):
        """Initialize the Secret client with proper imports"""
        try:
            # Try to import Secret AI SDK
            from secret_ai_sdk.secret_ai import ChatSecret
            from secret_ai_sdk.secret import Secret
            self.ChatSecret = ChatSecret
            self.secret_client = Secret()
            self.sdk_available = True
            print("✅ Secret AI SDK loaded successfully")
        except ImportError as e:
            print(f"⚠️ Warning: Secret AI SDK not available: {e}")
            print("   Will use mock responses for demonstration")
            self.sdk_available = False
            self.secret_client = None
            self.ChatSecret = None
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Get list of available models from Secret AI"""
        if not self.sdk_available:
            return {"models": [], "success": False, "error": "Secret AI SDK not available"}
            
        try:
            models = self.secret_client.get_models()
            return {"models": models, "success": True}
        except Exception as e:
            return {"models": [], "success": False, "error": str(e)}
    
    async def get_model_urls(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get available instance URLs for a model"""
        if not self.sdk_available:
            return {"urls": [], "success": False, "error": "Secret AI SDK not available"}
            
        try:
            models = self.secret_client.get_models()
            if not models:
                return {"urls": [], "success": False, "error": "No models available"}
            
            target_model = model or models[0]
            urls = self.secret_client.get_urls(model=target_model)
            return {"urls": urls, "model": target_model, "success": True}
        except Exception as e:
            return {"urls": [], "success": False, "error": str(e)}
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """Send message to Secret AI and get response"""
        if not self.sdk_available:
            return self._create_mock_response(message, "Secret AI SDK not available")
            
        try:
            # Get available models and URLs
            model_info = await self.get_model_urls()
            if not model_info["success"] or not model_info["urls"]:
                return self._create_mock_response(message, "No Secret AI instances available")
            
            # Create ChatSecret client
            secret_ai_llm = self.ChatSecret(
                base_url=model_info["urls"][0],
                model=model_info["model"],
                temperature=1.0
            )
            
            # Send message
            messages = [
                ("system", "You are a helpful AI assistant."),
                ("human", message)
            ]
            
            response = secret_ai_llm.invoke(messages, stream=False)
            
            return {
                "response": response.content,
                "success": True,
                "mock": False,
                "model": model_info["model"],
                "instance_url": model_info["urls"][0]
            }
            
        except Exception as e:
            return self._create_mock_response(message, str(e))
    
    async def get_attestation(self, instance_url: str) -> Dict[str, Any]:
        """
        Attempt to get attestation from Secret AI VM.
        Currently returns mock data as the feature is not implemented yet.
        Will automatically use real attestation when Secret AI adds the feature.
        """
        if not self.sdk_available:
            return self._create_mock_attestation(instance_url, "Secret AI SDK not available")
            
        try:
            # Create ChatSecret instance for attestation
            secret_ai_llm = self.ChatSecret(
                base_url=instance_url, 
                model="mock",  # Model doesn't matter for attestation
                temperature=1.0
            )
            
            # Try to get attestation - this will be empty dict {} for now
            attestation = secret_ai_llm.get_attestation()
            
            # Check if we got real attestation data
            if attestation and isinstance(attestation, dict) and len(attestation) > 0:
                # Real attestation data received! 
                print(f"Successfully received real attestation from Secret AI: {list(attestation.keys())}")
                return {
                    "attestation": attestation,
                    "success": True,
                    "mock": False,
                    "instance_url": instance_url,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                # Empty attestation, use mock for now
                print("Secret AI attestation not yet implemented, using mock data")
                return self._create_mock_attestation(
                    instance_url, 
                    "Secret AI attestation feature not yet available"
                )
                
        except Exception as e:
            print(f"Error getting attestation: {e}")
            return self._create_mock_attestation(instance_url, str(e))
    
    def _create_mock_response(self, message: str, error: str) -> Dict[str, Any]:
        """Create a mock AI response for demo purposes"""
        return {
            "response": f"Mock AI Response: I understand you asked '{message}'. This is a demo response since Secret AI is unavailable.",
            "success": False,
            "mock": True,
            "error": error
        }
    
    def _create_mock_attestation(self, instance_url: str, reason: str) -> Dict[str, Any]:
        """
        Create mock attestation data with realistic structure.
        This mimics what real Secret AI attestation will look like.
        """
        return {
            "attestation": {
                "mr_td": "mock_td_" + "a" * 58,  # 64 char hex string
                "rtmr0": "mock_rtmr0_" + "b" * 56,  # 64 char hex string
                "rtmr1": "mock_rtmr1_" + "c" * 56,  # 64 char hex string
                "rtmr2": "mock_rtmr2_" + "d" * 56,  # 64 char hex string
                "rtmr3": "mock_rtmr3_" + "e" * 56,  # 64 char hex string
                "report_data": "mock_report_" + "f" * 52,  # 64 char hex string
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "instance_url": instance_url
            },
            "success": False,
            "mock": True,
            "reason": reason,
            "note": "Using mock attestation - real Secret AI attestation coming soon!"
        }