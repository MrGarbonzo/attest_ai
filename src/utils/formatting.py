from typing import Dict, Any
from datetime import datetime


def format_attestation_for_display(attestation: Dict[str, Any]) -> str:
    """
    Format attestation data for human-readable display
    
    Args:
        attestation: Attestation data dictionary
        
    Returns:
        Formatted string representation
    """
    lines = [
        "=== Attestation Data ===",
        f"Source: {attestation.get('source', 'unknown')}",
        f"VM Type: {attestation.get('vm_type', 'unknown')}",
        f"Timestamp: {attestation.get('timestamp', 'N/A')}",
        "",
        "Registers:",
        f"  mr_td: {attestation.get('mr_td', 'N/A')}",
        f"  rtmr0: {attestation.get('rtmr0', 'N/A')}",
        f"  rtmr1: {attestation.get('rtmr1', 'N/A')}",
        f"  rtmr2: {attestation.get('rtmr2', 'N/A')}",
        f"  rtmr3: {attestation.get('rtmr3', 'N/A')}",
        f"  report_data: {attestation.get('report_data', 'N/A')}",
    ]
    
    return "\\n".join(lines)