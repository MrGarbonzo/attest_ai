import aiohttp
import ssl
import hashlib
import re
import os
import socket
from datetime import datetime
from typing import Dict, Any, Optional

class AttestationClient:
    def __init__(self, attestation_url: str = None):
        if attestation_url:
            self.attestation_url = attestation_url
        else:
            # Get from environment or use autodiscovery
            self.attestation_url = self._get_attestation_url()
    
    def _get_attestation_url(self) -> str:
        """Get attestation URL from environment or autodiscovery"""
        # 1. Check environment variable
        env_url = os.environ.get('ATTESTATION_URL')
        if env_url:
            return env_url
        
        # 2. Try to discover the public IP of the machine
        public_ip = self._get_public_ip()
        if public_ip:
            # Use standard SecretVM attestation port
            return f"https://{public_ip}:29343"
        
        # 3. Default to localhost
        return "https://localhost:29343"
    
    def _get_public_ip(self) -> Optional[str]:
        """Try to discover the public IP of this machine"""
        try:
            # Method 1: Use metadata service (works on cloud providers)
            import aiohttp
            import asyncio
            
            async def get_aws_ip():
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=aiohttp.ClientTimeout(total=2)) as resp:
                        if resp.status == 200:
                            return await resp.text()
                return None
            
            # Try AWS metadata
            loop = asyncio.new_event_loop()
            ip = loop.run_until_complete(get_aws_ip())
            if ip:
                return ip.strip()
            
        except:
            pass
        
        try:
            # Method 2: Use external service to get public IP
            import urllib.request
            response = urllib.request.urlopen('https://api.ipify.org', timeout=2)
            return response.read().decode('utf8').strip()
        except:
            pass
        
        return None
        
    async def get_self_attestation(self) -> Dict[str, Any]:
        """Get real attestation from attest_ai's own VM"""
        try:
            # Create SSL context that doesn't verify certificates (for self-signed certs)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            async with aiohttp.ClientSession() as session:
                # Get CPU attestation HTML
                async with session.get(
                    f"{self.attestation_url}/cpu.html",
                    ssl=ssl_context if self.attestation_url.startswith("https") else None
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Attestation endpoint returned {resp.status}")
                    
                    html_content = await resp.text()
                    
                    # Parse attestation data from HTML
                    attestation_data = self.parse_cpu_html(html_content)
                    
                    # Get TLS fingerprint for MITM protection
                    tls_fingerprint = await self.get_tls_fingerprint()
                    
                    return {
                        "mr_td": attestation_data.get("mr_td", ""),
                        "rtmr0": attestation_data.get("rtmr0", ""),
                        "rtmr1": attestation_data.get("rtmr1", ""),
                        "rtmr2": attestation_data.get("rtmr2", ""),
                        "rtmr3": attestation_data.get("rtmr3", ""),
                        "report_data": attestation_data.get("report_data", ""),
                        "tls_fingerprint": tls_fingerprint,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "instance_url": self.attestation_url.replace("https://", "").replace("http://", ""),
                        "success": True,
                        "mock": False
                    }
                    
        except Exception as e:
            # Self-attestation should always work in SecretVM, but handle errors gracefully
            print(f"Error getting self-attestation: {e}")
            return {
                "mr_td": "",
                "rtmr0": "",
                "rtmr1": "",
                "rtmr2": "",
                "rtmr3": "",
                "report_data": "",
                "tls_fingerprint": "",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "instance_url": "localhost:29343",
                "success": False,
                "mock": False,
                "error": str(e)
            }
    
    def parse_cpu_html(self, html_content: str) -> Dict[str, str]:
        """Parse attestation registers from HTML"""
        attestation_data = {}
        
        # Look for register values in HTML
        # Format: <td>mr_td</td><td>ba87a347454466680bfd267446df89d8117c04ea9f28234dd3d84e1a8a957d5a</td>
        patterns = {
            "mr_td": r"<td>mr_td</td><td>([a-fA-F0-9]+)</td>",
            "rtmr0": r"<td>rtmr0</td><td>([a-fA-F0-9]+)</td>",
            "rtmr1": r"<td>rtmr1</td><td>([a-fA-F0-9]+)</td>",
            "rtmr2": r"<td>rtmr2</td><td>([a-fA-F0-9]+)</td>",
            "rtmr3": r"<td>rtmr3</td><td>([a-fA-F0-9]+)</td>",
            "report_data": r"<td>report_data</td><td>([a-fA-F0-9]+)</td>"
        }
        
        for register, pattern in patterns.items():
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                attestation_data[register] = match.group(1)
            else:
                # Try alternative formats (e.g., with spaces or different case)
                alt_pattern = pattern.replace("td>", r"td\s*>")
                match = re.search(alt_pattern, html_content, re.IGNORECASE)
                if match:
                    attestation_data[register] = match.group(1)
                    
        return attestation_data
    
    async def get_tls_fingerprint(self) -> str:
        """Get TLS certificate fingerprint for MITM protection"""
        try:
            # For HTTPS attestation endpoint, get cert fingerprint
            if self.attestation_url.startswith("https"):
                # Create SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.attestation_url}/cpu.html",
                        ssl=ssl_context if self.attestation_url.startswith("https") else None
                    ) as resp:
                        # Get the peer certificate
                        transport = resp.connection.transport
                        if hasattr(transport, 'get_extra_info'):
                            peercert = transport.get_extra_info('peercert_bin')
                            if peercert:
                                # Calculate SHA256 fingerprint
                                fingerprint = hashlib.sha256(peercert).hexdigest()
                                return f"sha256:{fingerprint[:16]}..."
            
            # For HTTP or if we can't get the cert, return empty
            return ""
            
        except Exception as e:
            print(f"Could not get TLS fingerprint: {e}")
            return ""