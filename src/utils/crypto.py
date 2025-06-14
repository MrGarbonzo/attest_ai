import hashlib
import json
from datetime import datetime
from typing import Any, Dict


def hash_data(data: Any) -> str:
    """
    Generate SHA256 hash of data
    
    Args:
        data: Data to hash (will be JSON serialized if not string)
        
    Returns:
        Hex string of SHA256 hash
    """
    if not isinstance(data, str):
        data = json.dumps(data, sort_keys=True, default=str)
    
    return hashlib.sha256(data.encode()).hexdigest()


def generate_proof_id(attestation_data: Dict[str, Any], chat_id: str = None) -> str:
    """
    Generate unique proof ID combining attestation and chat data
    
    Args:
        attestation_data: Attestation data dictionary
        chat_id: Optional chat session ID
        
    Returns:
        Unique proof ID
    """
    components = {
        "timestamp": datetime.utcnow().isoformat(),
        "attestation": attestation_data,
    }
    
    if chat_id:
        components["chat_id"] = chat_id
    
    return f"proof_{hash_data(components)[:16]}"