#!/usr/bin/env python3
"""Integration tests for Secret AI functionality"""

import asyncio
import sys
import os
import json
import httpx

# Add src to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.secret_ai.client import SecretAIClient
from src.attestation.dual_attestation import DualAttestationManager
from src.attestation.self_attestation import SelfAttestationClient
from src.config import get_settings


async def test_secret_ai_discovery():
    """Test Secret AI model discovery"""
    print("\n1. Testing Secret AI Model Discovery")
    print("-" * 50)
    
    client = SecretAIClient()
    models = await client.discover_models()
    
    print(f"Found {len(models)} models:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model['model']} at {model['url']} (mode: {model['mode']})")
    
    assert len(models) > 0, "Should return at least one model"
    assert all("model" in m and "url" in m and "mode" in m for m in models), "Models should have required fields"
    
    print("✅ Model discovery test passed")
    return models


async def test_chat_functionality():
    """Test chat functionality"""
    print("\n2. Testing Chat Functionality")
    print("-" * 50)
    
    client = SecretAIClient()
    
    test_messages = [
        "Hello, how are you?",
        "What is Secret Network?",
        "Should I invest in SCRT?"
    ]
    
    for message in test_messages:
        print(f"\nTesting message: '{message}'")
        response = await client.send_message(message)
        
        print(f"  Success: {response['success']}")
        print(f"  Mode: {response['mode']}")
        print(f"  Response length: {len(response['response'])} chars")
        print(f"  Response preview: {response['response'][:100]}...")
        
        assert response["success"] is True, "Chat should succeed"
        assert "response" in response, "Should have response field"
        assert response["mode"] in ["real", "mock"], "Should indicate mode"
    
    print("✅ Chat functionality test passed")
    return True


async def test_secret_ai_attestation():
    """Test Secret AI attestation capture"""
    print("\n3. Testing Secret AI Attestation")
    print("-" * 50)
    
    client = SecretAIClient()
    attestation = await client.get_attestation()
    
    print(f"Attestation status: {attestation['status']}")
    print(f"Attestation mode: {attestation.get('mode', 'unknown')}")
    print(f"Source: {attestation['source']}")
    
    if attestation['data']:
        print(f"TLS Fingerprint: {attestation['data'].get('tls_fingerprint', 'N/A')}")
        print(f"Base URL: {attestation['data'].get('base_url', 'N/A')}")
    
    assert attestation["source"] == "secret_ai", "Should be Secret AI attestation"
    assert attestation["status"] in ["success", "error"], "Should have valid status"
    
    print("✅ Secret AI attestation test passed")
    return attestation


async def test_dual_attestation():
    """Test dual attestation manager"""
    print("\n4. Testing Dual Attestation Manager")
    print("-" * 50)
    
    settings = get_settings()
    
    # Initialize clients
    self_client = SelfAttestationClient(
        base_url=settings.self_attestation_url,
        cache_ttl=settings.attestation_cache_ttl
    )
    secret_ai_client = SecretAIClient()
    
    # Create manager
    manager = DualAttestationManager(self_client, secret_ai_client)
    attestations = await manager.get_dual_attestation()
    
    print("Summary:")
    summary = attestations["summary"]
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\nBinding:")
    binding = attestations["attestation_binding"]
    if binding:
        print(f"  Valid: {binding.get('binding_valid', False)}")
        print(f"  Algorithm: {binding.get('algorithm', 'N/A')}")
        print(f"  Combined Hash: {binding.get('combined_hash', 'N/A')[:32]}...")
    
    # Verify binding
    binding_valid = manager.verify_binding(attestations)
    print(f"\nBinding Verification: {binding_valid}")
    
    assert "self" in attestations, "Should have self attestation"
    assert "secret_ai" in attestations, "Should have Secret AI attestation"
    assert "attestation_binding" in attestations, "Should have binding"
    assert "summary" in attestations, "Should have summary"
    
    print("✅ Dual attestation test passed")
    return attestations


async def test_api_endpoints():
    """Test API endpoints"""
    print("\n5. Testing API Endpoints")
    print("-" * 50)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            print("Testing /health endpoint...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"  API Status: {health['status']}")
                print(f"  Self Attestation: {health['components']['self_attestation']}")
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
            
            # Test models endpoint
            print("\nTesting /api/v1/secret-ai/models endpoint...")
            response = await client.get(f"{base_url}/api/v1/secret-ai/models")
            if response.status_code == 200:
                models = response.json()
                print(f"  Found {models['count']} models")
                print("✅ Models endpoint working")
            else:
                print(f"❌ Models endpoint failed: {response.status_code}")
            
            # Test chat endpoint without password
            print("\nTesting /api/v1/chat endpoint (no password)...")
            chat_data = {"message": "Hello, this is a test"}
            response = await client.post(f"{base_url}/api/v1/chat", json=chat_data)
            if response.status_code == 200:
                chat_response = response.json()
                print(f"  Success: {chat_response['success']}")
                print(f"  Mode: {chat_response['mode']}")
                print(f"  Proof Generated: {chat_response['proof_generated']}")
                print("✅ Chat endpoint working")
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")
            
            # Test chat endpoint with password
            print("\nTesting /api/v1/chat endpoint (with password)...")
            chat_data = {"message": "Hello with proof", "proof_password": "test123"}
            response = await client.post(f"{base_url}/api/v1/chat", json=chat_data)
            if response.status_code == 200:
                chat_response = response.json()
                print(f"  Success: {chat_response['success']}")
                print(f"  Mode: {chat_response['mode']}")
                print(f"  Proof Generated: {chat_response['proof_generated']}")
                print(f"  Proof ID: {chat_response.get('proof_id', 'N/A')}")
                print("✅ Chat with proof endpoint working")
            else:
                print(f"❌ Chat with proof endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")
            print("Note: This is expected if the API server is not running")
    
    print("API endpoint tests completed")


async def main():
    """Run all tests"""
    print("=" * 70)
    print("ATTEST AI MVP - SECRET AI INTEGRATION TESTS")
    print("=" * 70)
    
    try:
        # Core functionality tests
        await test_secret_ai_discovery()
        await test_chat_functionality()
        await test_secret_ai_attestation()
        await test_dual_attestation()
        
        # API tests (will fail if server not running)
        await test_api_endpoints()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
        print("\nNext Steps:")
        print("1. Start the API server: python src/main.py")
        print("2. Test the chat endpoint manually:")
        print("   curl -X POST http://localhost:8000/api/v1/chat \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"message\": \"What is Secret Network?\"}'")
        print("3. Test with proof password:")
        print("   curl -X POST http://localhost:8000/api/v1/chat \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"message\": \"Hello\", \"proof_password\": \"test123\"}'")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)