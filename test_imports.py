#!/usr/bin/env python3
"""
Test script to verify basic imports and structure
"""
import os
import sys
import json

print("=== attest_ai Import Test ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Test environment variables
print("\n=== Environment Variables ===")
env_vars = ['SECRET_AI_API_KEY', 'ARWEAVE_MNEMONIC', 'API_PORT', 'DEBUG']
for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'KEY' in var or 'MNEMONIC' in var:
            masked = value[:8] + '...' + value[-8:] if len(value) > 16 else '***'
            print(f"{var}: {masked}")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: Not set")

# Test basic Python modules
print("\n=== Basic Module Tests ===")
basic_modules = ['hashlib', 'json', 'datetime', 'base64', 're']
for module in basic_modules:
    try:
        __import__(module)
        print(f"✅ {module}: Available")
    except ImportError as e:
        print(f"❌ {module}: {e}")

# Test external dependencies
print("\n=== External Dependencies ===")
external_modules = [
    ('fastapi', 'FastAPI'),
    ('aiohttp', 'AsyncIO HTTP Client'),
    ('cryptography', 'Cryptography'),
    ('mnemonic', 'BIP39 Mnemonic'),
]

available_count = 0
for module, description in external_modules:
    try:
        __import__(module)
        print(f"✅ {module}: {description} - Available")
        available_count += 1
    except ImportError as e:
        print(f"❌ {module}: {description} - Not available ({e})")

print(f"\n=== Summary ===")
print(f"External dependencies available: {available_count}/{len(external_modules)}")

# Test our module structure
print("\n=== Module Structure Test ===")
our_modules = [
    'secret_ai_client.py',
    'arweave_client.py', 
    'attestation_client.py',
    'encryption.py',
    'app.py'
]

for module_file in our_modules:
    if os.path.exists(module_file):
        print(f"✅ {module_file}: Present")
        # Try to parse syntax
        try:
            with open(module_file, 'r') as f:
                content = f.read()
            compile(content, module_file, 'exec')
            print(f"   Syntax: Valid")
        except SyntaxError as e:
            print(f"   Syntax: Error - {e}")
    else:
        print(f"❌ {module_file}: Missing")

print("\n=== Static Files Test ===")
static_files = ['static/index.html', 'static/script.js', 'static/style.css']
for file_path in static_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {file_path}: Present ({size} bytes)")
    else:
        print(f"❌ {file_path}: Missing")

print("\n=== Configuration Files Test ===")
config_files = [
    'requirements.txt',
    'Dockerfile', 
    'docker-compose.yaml',
    '.env.template',
    '.env',
    '.gitignore'
]
for file_path in config_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {file_path}: Present ({size} bytes)")
    else:
        print(f"❌ {file_path}: Missing")

print("\n=== Test Complete ===")