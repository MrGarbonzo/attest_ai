#!/usr/bin/env python3
"""Test script to verify self-attestation functionality"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.attestation.self_attestation import test_self_attestation


async def main():
    """Run attestation test"""
    print("=" * 60)
    print("Testing Self-Attestation Service")
    print("=" * 60)
    
    result = await test_self_attestation()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    
    # Return exit code based on result
    return 0 if result['status'] == 'success' else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)