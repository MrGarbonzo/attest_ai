import asyncio
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)


class SelfAttestationClient:
    """Client for fetching self-attestation data from localhost:29343"""
    
    def __init__(self, base_url: str = "http://localhost:29343", cache_ttl: int = 300):
        self.base_url = base_url
        self.cache_ttl = cache_ttl  # Cache TTL in seconds
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[float] = None
        
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if self._cache is None or self._cache_timestamp is None:
            return False
        
        elapsed = time.time() - self._cache_timestamp
        return elapsed < self.cache_ttl
    
    async def get_attestation(self) -> Dict[str, Any]:
        """Fetch attestation data from localhost:29343/cpu.html"""
        # Return cached data if still valid
        if self._is_cache_valid():
            logger.info("Returning cached attestation data")
            return self._cache
        
        if not HTTPX_AVAILABLE:
            return self._get_error_attestation("httpx not available - install dependencies")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/cpu.html")
                response.raise_for_status()
                
                # Parse HTML to extract attestation data
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    attestation_data = self._parse_attestation_html(soup)
                else:
                    attestation_data = self._parse_attestation_text(response.text)
                
                # Update cache
                self._cache = attestation_data
                self._cache_timestamp = time.time()
                
                logger.info("Successfully fetched fresh attestation data")
                return attestation_data
                
        except Exception as e:
            if "httpx" in str(type(e).__module__):
                if "ConnectError" in str(type(e).__name__):
                    logger.error(f"Failed to connect to attestation service at {self.base_url}")
                    return self._get_error_attestation("Connection failed - attestation service not available")
                elif "TimeoutException" in str(type(e).__name__):
                    logger.error("Attestation request timed out")
                    return self._get_error_attestation("Attestation request timed out")
            
            logger.error(f"Unexpected error fetching attestation: {str(e)}")
            return self._get_error_attestation(f"Unexpected error: {str(e)}")
    
    def _parse_attestation_text(self, html_text: str) -> Dict[str, Any]:
        """Parse attestation data from raw HTML text (fallback when BS4 not available)"""
        try:
            attestation_data = {
                "source": "self",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                "data": {
                    "raw_html_preview": html_text[:500] + "..." if len(html_text) > 500 else html_text,
                    "html_length": len(html_text),
                    "parsing_method": "text_fallback"
                }
            }
            
            # Look for specific keywords in the HTML
            keywords_found = []
            for keyword in ['CPU', 'attestation', 'enclave', 'SGX', 'SEV', 'PCR', 'measurement']:
                if keyword.lower() in html_text.lower():
                    keywords_found.append(keyword)
            
            if keywords_found:
                attestation_data["data"]["keywords_found"] = keywords_found
            
            return attestation_data
            
        except Exception as e:
            logger.error(f"Error parsing attestation text: {str(e)}")
            return self._get_error_attestation(f"Text parsing error: {str(e)}")
    
    def _parse_attestation_html(self, soup) -> Dict[str, Any]:  # Remove BeautifulSoup type hint
        """Parse attestation data from HTML response"""
        try:
            # Look for specific attestation fields in the HTML
            attestation_data = {
                "source": "self",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                "data": {}
            }
            
            # Extract CPU information
            cpu_info = soup.find_all(text=lambda text: text and 'CPU' in text)
            if cpu_info:
                attestation_data["data"]["cpu_info"] = str(cpu_info[0]).strip()
            
            # Extract any attestation-specific elements
            # Look for elements with class or id containing 'attestation' or 'enclave'
            attestation_elements = soup.find_all(class_=lambda x: x and ('attestation' in x.lower() or 'enclave' in x.lower()))
            if attestation_elements:
                attestation_data["data"]["attestation_elements"] = [elem.get_text(strip=True) for elem in attestation_elements]
            
            # Look for PCR values, measurements, or other attestation markers
            pcr_elements = soup.find_all(text=lambda text: text and any(keyword in text.lower() for keyword in ['pcr', 'measurement', 'enclave', 'sgx', 'sev']))
            if pcr_elements:
                attestation_data["data"]["measurements"] = [elem.strip() for elem in pcr_elements]
            
            # Extract full HTML for debugging/verification
            attestation_data["data"]["raw_html_preview"] = str(soup)[:500] + "..." if len(str(soup)) > 500 else str(soup)
            
            return attestation_data
            
        except Exception as e:
            logger.error(f"Error parsing attestation HTML: {str(e)}")
            return self._get_error_attestation(f"HTML parsing error: {str(e)}")
    
    def _get_error_attestation(self, error_message: str) -> Dict[str, Any]:
        """Return attestation data structure for error cases"""
        return {
            "source": "self",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": error_message,
            "data": None
        }
    
    def clear_cache(self):
        """Clear cached attestation data"""
        self._cache = None
        self._cache_timestamp = None
        logger.info("Attestation cache cleared")


# Convenience function for testing
async def test_self_attestation():
    """Test function to verify self-attestation is working"""
    client = SelfAttestationClient()
    attestation = await client.get_attestation()
    
    print("Self-Attestation Results:")
    print(f"Status: {attestation['status']}")
    print(f"Timestamp: {attestation['timestamp']}")
    
    if attestation['status'] == 'success':
        print("Data retrieved successfully:")
        if attestation['data']:
            for key, value in attestation['data'].items():
                if key != 'raw_html_preview':
                    print(f"  {key}: {value}")
    else:
        print(f"Error: {attestation.get('error', 'Unknown error')}")
    
    return attestation


if __name__ == "__main__":
    # Run test when module is executed directly
    asyncio.run(test_self_attestation())