import json
import os
import platform
import subprocess
from functools import lru_cache
from typing import Optional, Dict, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Secret AI Configuration
    SECRET_AI_API_KEY: str = Field(..., description="Master key for Secret AI SDK")
    SECRET_AI_DISCOVERY_CACHE_TTL: int = Field(
        default=3600,
        description="Cache TTL for Secret AI instance discovery in seconds"
    )
    
    # Arweave Configuration
    ARWEAVE_WALLET_JWK: str = Field(..., description="Arweave wallet in JWK format")
    ARWEAVE_GATEWAY: str = Field(
        default="https://arweave.net",
        description="Arweave gateway URL"
    )
    ENABLE_ARWEAVE_UPLOAD: bool = Field(
        default=True,
        description="Enable Arweave uploads"
    )
    MOCK_UNFUNDED_TRANSACTIONS: bool = Field(
        default=True,
        description="Mock transactions when wallet is unfunded"
    )
    
    # Self-attestation Configuration
    SELF_ATTESTATION_URL: str = Field(
        default="http://localhost:29343",
        description="URL for self-attestation endpoint"
    )
    
    # Application Configuration
    APP_HOST: str = Field(default="0.0.0.0", description="Application host")
    APP_PORT: int = Field(default=8000, description="Application port")
    APP_DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Cache Configuration
    CACHE_TTL_SECONDS: int = Field(
        default=300,
        description="Cache TTL for attestation data in seconds"
    )
    
    # Mock Configuration
    MOCK_SECRET_AI_ATTESTATION: bool = Field(
        default=False,
        description="Mock Secret AI attestation if unavailable"
    )
    MOCK_ARWEAVE_UPLOAD: bool = Field(
        default=False,
        description="Mock Arweave upload if unfunded"
    )
    
    # SecretVM-specific Configuration
    DEPLOYMENT_ENVIRONMENT: str = Field(
        default="development",
        description="Deployment environment (development, staging, production)"
    )
    SECRETVM_DEPLOYMENT: bool = Field(
        default=False,
        description="Whether this is a SecretVM deployment"
    )
    MAX_MEMORY_MB: int = Field(
        default=2048,
        description="Maximum memory usage in MB"
    )
    MAX_CPU_PERCENT: int = Field(
        default=90,
        description="Maximum CPU usage percentage"
    )
    HEALTH_CHECK_INTERVAL: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    HEALTH_CHECK_TIMEOUT: int = Field(
        default=10,
        description="Health check timeout in seconds"
    )
    HEALTH_CHECK_RETRIES: int = Field(
        default=3,
        description="Number of health check retries"
    )
    
    @field_validator("ARWEAVE_WALLET_JWK")
    def validate_arweave_wallet(cls, v: str) -> str:
        try:
            wallet_data = json.loads(v)
            if not isinstance(wallet_data, dict) or "kty" not in wallet_data:
                raise ValueError("Invalid JWK format")
        except json.JSONDecodeError:
            raise ValueError("ARWEAVE_WALLET_JWK must be valid JSON")
        return v
    
    def get_arweave_wallet_dict(self) -> Dict[str, Any]:
        return json.loads(self.ARWEAVE_WALLET_JWK)
    
    @property
    def is_production(self) -> bool:
        return not self.APP_DEBUG
    
    @property
    def is_secretvm_environment(self) -> bool:
        """Detect if running in SecretVM environment"""
        if self.SECRETVM_DEPLOYMENT:
            return True
        
        # Auto-detect SecretVM environment
        return self._detect_secretvm_environment()
    
    def _detect_secretvm_environment(self) -> bool:
        """Auto-detect SecretVM environment"""
        try:
            # Check if self-attestation endpoint is available
            try:
                import requests
                response = requests.get(self.SELF_ATTESTATION_URL, timeout=5)
                if response.status_code == 200:
                    html_content = response.text.lower()
                    # Look for SecretVM-specific content
                    if any(keyword in html_content for keyword in ['mr_td', 'rtmr', 'report_data']):
                        return True
            except Exception:
                pass
            
            # Check for SecretVM-specific environment variables
            if os.environ.get('SECRETVM_INSTANCE_ID'):
                return True
            
            # Check for container environment indicators
            if os.path.exists('/.dockerenv') and os.environ.get('DEPLOYMENT_ENVIRONMENT') == 'production':
                return True
            
            return False
            
        except Exception:
            return False
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get comprehensive environment information"""
        return {
            'deployment_environment': self.DEPLOYMENT_ENVIRONMENT,
            'is_production': self.is_production,
            'is_secretvm': self.is_secretvm_environment,
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'container_env': os.path.exists('/.dockerenv'),
            'attestation_url': self.SELF_ATTESTATION_URL,
            'max_memory_mb': self.MAX_MEMORY_MB,
            'max_cpu_percent': self.MAX_CPU_PERCENT,
        }
    
    def get_optimized_settings(self) -> Dict[str, Any]:
        """Get settings optimized for current environment"""
        settings = {}
        
        if self.is_secretvm_environment:
            # SecretVM optimizations
            settings.update({
                'cache_ttl_seconds': min(self.CACHE_TTL_SECONDS, 180),  # Shorter cache for real data
                'discovery_cache_ttl': min(self.SECRET_AI_DISCOVERY_CACHE_TTL, 1800),  # 30 min max
                'mock_secret_ai_attestation': False,  # Always try real in SecretVM
                'enable_arweave_upload': self.ENABLE_ARWEAVE_UPLOAD,
                'health_check_interval': self.HEALTH_CHECK_INTERVAL,
                'optimized_for': 'secretvm'
            })
        else:
            # Development/local optimizations
            settings.update({
                'cache_ttl_seconds': max(self.CACHE_TTL_SECONDS, 60),  # Longer cache for stability
                'discovery_cache_ttl': self.SECRET_AI_DISCOVERY_CACHE_TTL,
                'mock_secret_ai_attestation': self.MOCK_SECRET_AI_ATTESTATION,
                'enable_arweave_upload': self.ENABLE_ARWEAVE_UPLOAD,
                'health_check_interval': max(self.HEALTH_CHECK_INTERVAL, 60),
                'optimized_for': 'development'
            })
        
        return settings
    
    def validate_environment(self) -> None:
        """Validate that all required environment variables are set properly"""
        errors = []
        
        # Check API key
        if not self.SECRET_AI_API_KEY or self.SECRET_AI_API_KEY == "your_master_key_from_docs":
            errors.append("SECRET_AI_API_KEY must be set to a valid API key")
        
        # Check wallet
        try:
            wallet = self.get_arweave_wallet_dict()
            # In production, require all fields. In debug/test, just require basic structure
            if self.is_production:
                required_fields = ["kty", "e", "n", "d"]
            else:
                required_fields = ["kty"]  # Minimal requirement for testing
            
            missing = [f for f in required_fields if f not in wallet]
            if missing:
                errors.append(f"ARWEAVE_WALLET_JWK missing fields: {missing}")
        except Exception as e:
            errors.append(f"Invalid ARWEAVE_WALLET_JWK: {str(e)}")
        
        if errors:
            raise ValueError(f"Environment validation failed:\\n" + "\\n".join(errors))


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Only validate in production mode
    if settings.is_production:
        settings.validate_environment()
    
    return settings