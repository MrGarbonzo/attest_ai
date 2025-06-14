import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cachetools import TTLCache
import httpx
from pydantic import BaseModel, Field

from ..config import get_settings
from ..utils.exceptions import (
    SelfAttestationError, 
    ErrorCode, 
    handle_network_error,
    handle_validation_error
)

logger = logging.getLogger(__name__)


class AttestationData(BaseModel):
    """Structured attestation data from SecretVM"""
    mr_td: str = Field(..., description="TD measurement register")
    rtmr0: str = Field(..., description="Runtime measurement register 0")
    rtmr1: str = Field(..., description="Runtime measurement register 1")
    rtmr2: str = Field(..., description="Runtime measurement register 2")
    rtmr3: str = Field(..., description="Runtime measurement register 3")
    report_data: str = Field(..., description="Custom report data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="self", description="Source of attestation")
    vm_type: str = Field(default="attest_ai", description="Type of VM")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SelfAttestationClient:
    """Client for fetching self-attestation from localhost:29343"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.SELF_ATTESTATION_URL
        self.cache = TTLCache(maxsize=10, ttl=self.settings.CACHE_TTL_SECONDS)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def fetch_attestation(self, force_refresh: bool = False) -> AttestationData:
        """
        Fetch attestation data from localhost:29343/cpu.html
        
        Args:
            force_refresh: Force refresh bypassing cache
            
        Returns:
            AttestationData with parsed VM registers
        """
        cache_key = "self_attestation"
        
        # Check cache first unless force refresh
        if not force_refresh and cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            logger.info(f"Fetching self-attestation from {self.base_url}/cpu.html")
            
            # Fetch attestation HTML with retry logic
            response = await self.client.get(f"{self.base_url}/cpu.html")
            response.raise_for_status()
            
            if not response.text.strip():
                raise SelfAttestationError(
                    message="Empty response from self-attestation endpoint",
                    error_code=ErrorCode.SELF_ATTESTATION_PARSE_ERROR,
                    details={"url": f"{self.base_url}/cpu.html"}
                )
            
            html_content = response.text
            logger.debug(f"Received HTML content: {len(html_content)} characters")
            
            # Parse attestation data from HTML
            attestation_data = self._parse_attestation_html(html_content)
            
            # Cache the result
            self.cache[cache_key] = attestation_data
            logger.info("Successfully cached self-attestation data")
            
            return attestation_data
            
        except httpx.TimeoutException as e:
            raise SelfAttestationError(
                message="Timeout while fetching self-attestation",
                error_code=ErrorCode.SELF_ATTESTATION_TIMEOUT,
                details={"url": f"{self.base_url}/cpu.html", "timeout": 30.0},
                retryable=True
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise SelfAttestationError(
                    message="Self-attestation endpoint not found - may not be running in SecretVM",
                    error_code=ErrorCode.SELF_ATTESTATION_UNAVAILABLE,
                    details={"url": f"{self.base_url}/cpu.html", "status_code": 404},
                    retryable=True
                )
            else:
                raise SelfAttestationError(
                    message=f"HTTP error {e.response.status_code} from self-attestation endpoint",
                    error_code=ErrorCode.SELF_ATTESTATION_UNAVAILABLE,
                    details={"url": f"{self.base_url}/cpu.html", "status_code": e.response.status_code},
                    retryable=True
                )
        except httpx.RequestError as e:
            raise handle_network_error(e, "self-attestation fetch")
        except SelfAttestationError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in self-attestation: {e}")
            raise SelfAttestationError(
                message=f"Unexpected error processing attestation data: {str(e)}",
                error_code=ErrorCode.INTERNAL_ERROR,
                details={"original_error": str(e)},
                retryable=False
            )
    
    def _parse_attestation_html(self, html: str) -> AttestationData:
        """
        Parse attestation data from HTML content with comprehensive error handling
        
        Expected format in HTML:
        <td>mr_td</td><td>0x...</td>
        <td>rtmr0</td><td>0x...</td>
        etc.
        """
        if not html or not html.strip():
            raise SelfAttestationError(
                message="Empty HTML content received",
                error_code=ErrorCode.SELF_ATTESTATION_PARSE_ERROR,
                details={"html_length": len(html)}
            )
        
        # Regex patterns for extracting register values
        patterns = {
            'mr_td': r'<td>mr_td</td>\s*<td>(0x[0-9a-fA-F]+)</td>',
            'rtmr0': r'<td>rtmr0</td>\s*<td>(0x[0-9a-fA-F]+)</td>',
            'rtmr1': r'<td>rtmr1</td>\s*<td>(0x[0-9a-fA-F]+)</td>',
            'rtmr2': r'<td>rtmr2</td>\s*<td>(0x[0-9a-fA-F]+)</td>',
            'rtmr3': r'<td>rtmr3</td>\s*<td>(0x[0-9a-fA-F]+)</td>',
            'report_data': r'<td>report_data</td>\s*<td>(0x[0-9a-fA-F]+)</td>'
        }
        
        extracted_data = {}
        missing_fields = []
        
        for key, pattern in patterns.items():
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1)
                # Validate hex format
                if not re.match(r'^0x[0-9a-fA-F]+$', value):
                    logger.warning(f"Invalid hex format for {key}: {value}")
                extracted_data[key] = value
            else:
                # Try alternative pattern without 0x prefix
                alt_pattern = pattern.replace('(0x', '(0x)?')
                match = re.search(alt_pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1)
                    if value and not value.startswith('0x'):
                        value = f'0x{value}'
                    # Validate the corrected value
                    if value and re.match(r'^0x[0-9a-fA-F]+$', value):
                        extracted_data[key] = value
                    else:
                        missing_fields.append(key)
                else:
                    missing_fields.append(key)
        
        # Check if we have all required fields
        if missing_fields:
            raise SelfAttestationError(
                message=f"Missing required attestation fields: {', '.join(missing_fields)}",
                error_code=ErrorCode.SELF_ATTESTATION_PARSE_ERROR,
                details={
                    "missing_fields": missing_fields,
                    "found_fields": list(extracted_data.keys()),
                    "html_sample": html[:500] if len(html) > 500 else html
                }
            )
        
        try:
            return AttestationData(**extracted_data)
        except Exception as e:
            raise SelfAttestationError(
                message=f"Failed to create attestation data: {str(e)}",
                error_code=ErrorCode.SELF_ATTESTATION_PARSE_ERROR,
                details={"extracted_data": extracted_data, "validation_error": str(e)}
            )
    
    async def verify_availability(self) -> bool:
        """Check if self-attestation endpoint is available"""
        try:
            response = await self.client.get(f"{self.base_url}/cpu.html")
            return response.status_code == 200
        except:
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache state"""
        return {
            "cache_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl_seconds": self.cache.ttl,
            "has_cached_data": "self_attestation" in self.cache
        }