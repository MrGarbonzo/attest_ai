import json
import os
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
    
    def validate_environment(self) -> None:
        """Validate that all required environment variables are set properly"""
        errors = []
        
        # Check API key
        if not self.SECRET_AI_API_KEY or self.SECRET_AI_API_KEY == "your_master_key_from_docs":
            errors.append("SECRET_AI_API_KEY must be set to a valid API key")
        
        # Check wallet
        try:
            wallet = self.get_arweave_wallet_dict()
            required_fields = ["kty", "e", "n", "d"]
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