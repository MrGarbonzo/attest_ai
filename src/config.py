import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Secret AI Configuration
    secret_ai_api_key: str = Field(
        default="",
        env="SECRET_AI_API_KEY",
        description="API key for Secret AI"
    )
    secret_ai_base_url: str = Field(
        default="https://secretai-zqtr.scrtlabs.com:21434",
        env="SECRET_AI_BASE_URL",
        description="Secret AI base URL for attestation"
    )
    secret_chain_id: str = Field(
        default="secret-4",
        env="SECRET_CHAIN_ID",
        description="Secret Network chain ID"
    )
    secret_node_url: str = Field(
        default="https://lcd.mainnet.secretsaturn.net",
        env="SECRET_NODE_URL",
        description="Secret Network node URL"
    )
    
    # Self-Attestation
    self_attestation_url: str = Field(
        default="http://localhost:29343",
        env="SELF_ATTESTATION_URL",
        description="URL for self-attestation service"
    )
    attestation_cache_ttl: int = Field(
        default=300,
        env="ATTESTATION_CACHE_TTL",
        description="Attestation cache TTL in seconds"
    )
    
    # Application
    api_port: int = Field(
        default=8000,
        env="API_PORT",
        description="Port for the API server"
    )
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    # Proof Management
    proof_file_cleanup_hours: int = Field(
        default=24,
        env="PROOF_FILE_CLEANUP_HOURS",
        description="Hours before cleaning up proof files"
    )
    downloads_dir: str = Field(
        default="./downloads",
        env="DOWNLOADS_DIR",
        description="Directory for storing proof downloads"
    )
    
    # Chat Configuration
    chat_timeout: int = Field(
        default=30,
        env="CHAT_TIMEOUT",
        description="Chat request timeout in seconds"
    )
    max_message_length: int = Field(
        default=2000,
        env="MAX_MESSAGE_LENGTH", 
        description="Maximum chat message length"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def validate_settings(self) -> bool:
        """Validate critical settings"""
        errors = []
        
        # Check if downloads directory exists or can be created
        if not os.path.exists(self.downloads_dir):
            try:
                os.makedirs(self.downloads_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create downloads directory: {e}")
        
        # Warn if no Secret AI API key is set
        if not self.secret_ai_api_key:
            print("WARNING: No SECRET_AI_API_KEY set. Secret AI features will use mock data.")
        
        # Check if port is valid
        if not (1 <= self.api_port <= 65535):
            errors.append(f"Invalid API port: {self.api_port}")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True


# Create a singleton instance
settings = Settings()

# Validate settings on import
if not settings.validate_settings():
    print("WARNING: Some configuration issues detected. Application may not work correctly.")


def get_settings() -> Settings:
    """Get application settings"""
    return settings