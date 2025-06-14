import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from cachetools import TTLCache
from pydantic import BaseModel, Field

try:
    from secret_ai_sdk.secret import Secret
    from secret_ai_sdk.secret_ai import ChatSecret
except ImportError:
    # Mock classes for development when SDK not available
    class Secret:
        def get_models(self):
            return ["mock-model"]
        def get_urls(self, model):
            return ["http://mock-secret-ai.local"]
    
    class ChatSecret:
        def __init__(self, base_url, model):
            self.base_url = base_url
            self.model = model
        
        def get_attestation_report(self):
            return {"mock": True, "data": "mock_attestation"}
        
        def receive(self, prompt, user="user", session_id=None):
            return {"response": f"Mock response to: {prompt}"}

from ..config import get_settings
from ..attestation import AttestationData

logger = logging.getLogger(__name__)


class SecretAIInstance(BaseModel):
    """Represents a discovered Secret AI instance"""
    model: str
    base_url: str
    available: bool = True
    last_checked: datetime = Field(default_factory=datetime.utcnow)


class ChatResponse(BaseModel):
    """Response from Secret AI chat"""
    message: str
    prompt: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attestation: Optional[Dict[str, Any]] = None
    instance_info: Optional[SecretAIInstance] = None


class SecretAIClient:
    """Client for Secret AI SDK operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.secret_client = Secret()
        self.chat_client: Optional[ChatSecret] = None
        self.current_instance: Optional[SecretAIInstance] = None
        
        # Cache for instance discovery
        self.discovery_cache = TTLCache(
            maxsize=10,
            ttl=self.settings.SECRET_AI_DISCOVERY_CACHE_TTL
        )
        
        # Initialize with API key
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Secret AI client with API key"""
        # The SDK should pick up the API key from environment
        # or we can set it explicitly if needed
        logger.info("Initializing Secret AI client")
    
    async def discover_instances(self, force_refresh: bool = False) -> List[SecretAIInstance]:
        """
        Discover available Secret AI instances
        
        Args:
            force_refresh: Force refresh bypassing cache
            
        Returns:
            List of available instances
        """
        cache_key = "secret_ai_instances"
        
        if not force_refresh and cache_key in self.discovery_cache:
            logger.info("Returning cached Secret AI instances")
            return self.discovery_cache[cache_key]
        
        try:
            # Get available models
            models = self.secret_client.get_models()
            logger.info(f"Found {len(models)} Secret AI models")
            
            instances = []
            
            for model in models:
                try:
                    # Get URLs for this model
                    urls = self.secret_client.get_urls(model=model)
                    
                    for url in urls:
                        instance = SecretAIInstance(
                            model=model,
                            base_url=url,
                            available=True
                        )
                        instances.append(instance)
                        logger.info(f"Discovered instance: {model} at {url}")
                
                except Exception as e:
                    logger.error(f"Error discovering URLs for model {model}: {e}")
            
            # Cache the results
            self.discovery_cache[cache_key] = instances
            
            return instances
            
        except Exception as e:
            logger.error(f"Error discovering Secret AI instances: {e}")
            
            # Return mock instance if discovery fails and mocking is enabled
            if self.settings.MOCK_SECRET_AI_ATTESTATION:
                mock_instance = SecretAIInstance(
                    model="mock-model",
                    base_url="http://mock-secret-ai.local",
                    available=False
                )
                return [mock_instance]
            
            return []
    
    async def select_instance(self, model: Optional[str] = None) -> Optional[SecretAIInstance]:
        """
        Select a Secret AI instance for chat
        
        Args:
            model: Specific model to select (optional)
            
        Returns:
            Selected instance or None
        """
        instances = await self.discover_instances()
        
        if not instances:
            logger.error("No Secret AI instances available")
            return None
        
        # Filter by model if specified
        if model:
            instances = [i for i in instances if i.model == model]
        
        # Select first available instance
        for instance in instances:
            if instance.available:
                self.current_instance = instance
                
                # Initialize chat client
                self.chat_client = ChatSecret(
                    base_url=instance.base_url,
                    model=instance.model
                )
                
                logger.info(f"Selected instance: {instance.model} at {instance.base_url}")
                return instance
        
        # Use first instance even if not available (for mocking)
        if instances:
            self.current_instance = instances[0]
            self.chat_client = ChatSecret(
                base_url=instances[0].base_url,
                model=instances[0].model
            )
            return instances[0]
        
        return None
    
    async def get_attestation(self) -> Optional[AttestationData]:
        """
        Get attestation from current Secret AI instance
        
        Returns:
            AttestationData or None
        """
        if not self.chat_client:
            logger.error("No chat client initialized")
            return None
        
        try:
            # Get attestation report from Secret AI
            attestation_report = self.chat_client.get_attestation_report()
            
            # Parse attestation data (format may vary)
            # This is a simplified version - adjust based on actual SDK response
            attestation = AttestationData(
                mr_td=attestation_report.get("mr_td", "0x0"),
                rtmr0=attestation_report.get("rtmr0", "0x0"),
                rtmr1=attestation_report.get("rtmr1", "0x0"),
                rtmr2=attestation_report.get("rtmr2", "0x0"),
                rtmr3=attestation_report.get("rtmr3", "0x0"),
                report_data=attestation_report.get("report_data", "0x0"),
                source="secret_ai",
                vm_type="secret_ai_vm"
            )
            
            return attestation
            
        except Exception as e:
            logger.error(f"Error getting Secret AI attestation: {e}")
            
            # Return mock attestation if enabled
            if self.settings.MOCK_SECRET_AI_ATTESTATION:
                return AttestationData(
                    mr_td="0xmock_secret_ai_mr_td",
                    rtmr0="0xmock_secret_ai_rtmr0",
                    rtmr1="0xmock_secret_ai_rtmr1",
                    rtmr2="0xmock_secret_ai_rtmr2",
                    rtmr3="0xmock_secret_ai_rtmr3",
                    report_data="0xmock_secret_ai_report",
                    source="secret_ai_mock",
                    vm_type="secret_ai_vm"
                )
            
            return None
    
    async def send_message(
        self,
        prompt: str,
        user: str = "user",
        session_id: Optional[str] = None
    ) -> Tuple[ChatResponse, Optional[AttestationData]]:
        """
        Send a message to Secret AI and get response with attestation
        
        Args:
            prompt: Message to send
            user: User identifier
            session_id: Session ID for conversation tracking
            
        Returns:
            Tuple of (ChatResponse, AttestationData)
        """
        if not self.chat_client:
            # Try to select an instance
            instance = await self.select_instance()
            if not instance:
                raise Exception("No Secret AI instance available")
        
        try:
            # Send message to Secret AI
            response_data = self.chat_client.receive(
                prompt=prompt,
                user=user,
                session_id=session_id
            )
            
            # Get attestation for this interaction
            attestation = await self.get_attestation()
            
            # Create response
            response = ChatResponse(
                message=response_data.get("response", ""),
                prompt=prompt,
                session_id=session_id or f"session_{datetime.utcnow().timestamp()}",
                attestation=attestation.dict() if attestation else None,
                instance_info=self.current_instance
            )
            
            return response, attestation
            
        except Exception as e:
            logger.error(f"Error sending message to Secret AI: {e}")
            
            # Return mock response if mocking is enabled
            if self.settings.MOCK_SECRET_AI_ATTESTATION:
                mock_response = ChatResponse(
                    message=f"Mock response to: {prompt}",
                    prompt=prompt,
                    session_id=session_id or "mock_session",
                    instance_info=self.current_instance
                )
                mock_attestation = await self.get_attestation()
                return mock_response, mock_attestation
            
            raise
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health of Secret AI service"""
        try:
            instances = await self.discover_instances()
            available_count = sum(1 for i in instances if i.available)
            
            return {
                "service": "secret_ai",
                "status": "healthy" if available_count > 0 else "degraded",
                "instances_discovered": len(instances),
                "instances_available": available_count,
                "current_instance": self.current_instance.dict() if self.current_instance else None,
                "mock_mode": self.settings.MOCK_SECRET_AI_ATTESTATION
            }
        except Exception as e:
            return {
                "service": "secret_ai",
                "status": "unhealthy",
                "error": str(e),
                "mock_mode": self.settings.MOCK_SECRET_AI_ATTESTATION
            }