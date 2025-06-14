#!/usr/bin/env python3
"""
Generate test JWK for development and testing
NOT FOR PRODUCTION USE
"""

import json
import base64
import os

def generate_test_jwk():
    """Generate a minimal test JWK that passes validation"""
    
    # This is a TEST JWK only - do not use in production
    test_jwk = {
        "kty": "RSA",
        "e": "AQAB",  # Standard RSA exponent (65537 in base64)
        "n": base64.urlsafe_b64encode(os.urandom(256)).decode().rstrip('='),  # Random modulus
        "d": base64.urlsafe_b64encode(os.urandom(256)).decode().rstrip('='),  # Random private exponent
        "p": base64.urlsafe_b64encode(os.urandom(128)).decode().rstrip('='),  # Random prime1
        "q": base64.urlsafe_b64encode(os.urandom(128)).decode().rstrip('='),  # Random prime2
        "dp": base64.urlsafe_b64encode(os.urandom(128)).decode().rstrip('='), # Random exponent1
        "dq": base64.urlsafe_b64encode(os.urandom(128)).decode().rstrip('='), # Random exponent2
        "qi": base64.urlsafe_b64encode(os.urandom(128)).decode().rstrip('=')  # Random coefficient
    }
    
    return test_jwk

def generate_minimal_test_jwk():
    """Generate minimal JWK for CI/CD testing"""
    # Minimal JWK that passes basic validation
    return {
        "kty": "RSA",
        "e": "AQAB",
        "n": "test_modulus_value",
        "d": "test_private_key_value"
    }

if __name__ == "__main__":
    print("Test JWK Generator")
    print("==================")
    print("\nWARNING: These JWKs are for testing only. Never use in production!")
    print("\nMinimal Test JWK (for CI/CD):")
    minimal_jwk = generate_minimal_test_jwk()
    print(json.dumps(minimal_jwk))
    
    print("\nFull Test JWK (for local testing):")
    full_jwk = generate_test_jwk()
    print(json.dumps(full_jwk, indent=2))
    
    print("\nEnvironment variable format:")
    print(f"export ARWEAVE_WALLET_JWK='{json.dumps(minimal_jwk)}'")
    
    print("\nFor production, generate a real Arweave wallet at:")
    print("https://arweave.app/wallet")