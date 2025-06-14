"""
Custom exceptions and error handling utilities for attest_ai
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for better error handling"""
    
    # Self-attestation errors
    SELF_ATTESTATION_UNAVAILABLE = "SELF_ATTESTATION_UNAVAILABLE"
    SELF_ATTESTATION_PARSE_ERROR = "SELF_ATTESTATION_PARSE_ERROR"
    SELF_ATTESTATION_TIMEOUT = "SELF_ATTESTATION_TIMEOUT"
    
    # Secret AI errors
    SECRET_AI_NO_INSTANCES = "SECRET_AI_NO_INSTANCES"
    SECRET_AI_CONNECTION_ERROR = "SECRET_AI_CONNECTION_ERROR"
    SECRET_AI_INVALID_RESPONSE = "SECRET_AI_INVALID_RESPONSE"
    SECRET_AI_TIMEOUT = "SECRET_AI_TIMEOUT"
    
    # Arweave errors
    ARWEAVE_WALLET_ERROR = "ARWEAVE_WALLET_ERROR"
    ARWEAVE_UPLOAD_FAILED = "ARWEAVE_UPLOAD_FAILED"
    ARWEAVE_INSUFFICIENT_FUNDS = "ARWEAVE_INSUFFICIENT_FUNDS"
    ARWEAVE_NETWORK_ERROR = "ARWEAVE_NETWORK_ERROR"
    
    # Configuration errors
    CONFIG_INVALID_ENV = "CONFIG_INVALID_ENV"
    CONFIG_MISSING_KEY = "CONFIG_MISSING_KEY"
    CONFIG_VALIDATION_ERROR = "CONFIG_VALIDATION_ERROR"
    
    # General errors
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class AttestAIException(Exception):
    """Base exception for all attest_ai errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: ErrorCode, 
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.retryable = retryable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": True,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "retryable": self.retryable
        }


class SelfAttestationError(AttestAIException):
    """Errors related to self-attestation"""
    pass


class SecretAIError(AttestAIException):
    """Errors related to Secret AI operations"""
    pass


class ArweaveError(AttestAIException):
    """Errors related to Arweave operations"""
    pass


class ConfigurationError(AttestAIException):
    """Configuration and environment errors"""
    pass


def handle_network_error(error: Exception, operation: str, retryable: bool = True) -> AttestAIException:
    """Convert network errors to standardized exceptions"""
    if "timeout" in str(error).lower():
        return AttestAIException(
            message=f"Network timeout during {operation}",
            error_code=ErrorCode.NETWORK_TIMEOUT,
            details={"operation": operation, "original_error": str(error)},
            retryable=retryable
        )
    
    return AttestAIException(
        message=f"Network error during {operation}: {str(error)}",
        error_code=ErrorCode.INTERNAL_ERROR,
        details={"operation": operation, "original_error": str(error)},
        retryable=retryable
    )


def handle_validation_error(field: str, value: Any, expected: str) -> AttestAIException:
    """Create validation error with details"""
    return AttestAIException(
        message=f"Validation failed for {field}: expected {expected}",
        error_code=ErrorCode.VALIDATION_ERROR,
        details={
            "field": field,
            "value": str(value),
            "expected": expected
        },
        retryable=False
    )