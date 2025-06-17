# Secret Network Mainnet Endpoint Testing Guide

Based on the Secret Network API endpoints document, this guide helps test and validate mainnet LCD endpoints for the attest_ai project.

## **Target Configuration**
- **Chain ID**: `secret-4` (mainnet)  
- **Network**: Secret Network Mainnet
- **Protocol**: LCD (Light Client Daemon)

## **Available Mainnet LCD Endpoints**

### **Priority Endpoints for Testing:**

1. **🪐 Secret Saturn** (Primary)
   ```
   https://lcd.mainnet.secretsaturn.net
   ```

2. **🐝 Lavender.Five Nodes** (Backup)
   ```
   https://secretnetwork-api.lavenderfive.com:443
   ```

3. **1RPC (Automata Network)** (Backup)
   ```
   https://1rpc.io/scrt-lcd
   ```

4. **01node** (Backup)
   ```
   https://rest-secret.01node.com
   ```

5. **High Stakes 🇨🇭** (Backup)
   ```
   https://secretnetwork-api.highstakes.ch:1317
   ```

6. **Stakewolle** (Backup)
   ```
   https://public.stakewolle.com/cosmos/secretnetwork/rest
   ```

7. **Ankr** (Backup)
   ```
   https://rpc.ankr.com/http/scrt_cosmos
   ```

## **Endpoint Testing Script**

Create `tools/test_secret_network_endpoints.py`:

```python
#!/usr/bin/env python3
"""
Test Secret Network mainnet LCD endpoints for attest_ai.
Usage: python test_secret_network_endpoints.py
"""

import asyncio
import httpx
import time
from typing import List, Dict, Optional

MAINNET_ENDPOINTS = [
    {
        "name": "Secret Saturn",
        "url": "https://lcd.mainnet.secretsaturn.net",
        "provider": "🪐 Secret Saturn"
    },
    {
        "name": "Lavender Five",
        "url": "https://secretnetwork-api.lavenderfive.com:443",
        "provider": "🐝 Lavender.Five Nodes"
    },
    {
        "name": "1RPC",
        "url": "https://1rpc.io/scrt-lcd",
        "provider": "1RPC (Automata Network)"
    },
    {
        "name": "01node",
        "url": "https://rest-secret.01node.com",
        "provider": "01node"
    },
    {
        "name": "High Stakes",
        "url": "https://secretnetwork-api.highstakes.ch:1317",
        "provider": "High Stakes 🇨🇭"
    },
    {
        "name": "Stakewolle",
        "url": "https://public.stakewolle.com/cosmos/secretnetwork/rest",
        "provider": "Stakewolle"
    },
    {
        "name": "Ankr",
        "url": "https://rpc.ankr.com/http/scrt_cosmos",
        "provider": "Ankr"
    }
]

async def test_endpoint(client: httpx.AsyncClient, endpoint: Dict) -> Dict:
    """Test a single LCD endpoint"""
    result = {
        "name": endpoint["name"],
        "url": endpoint["url"],
        "provider": endpoint["provider"],
        "status": "FAILED",
        "response_time": None,
        "chain_id": None,
        "latest_block": None,
        "error": None
    }
    
    try:
        start_time = time.time()
        
        # Test basic connectivity with node info
        response = await client.get(f"{endpoint['url']}/cosmos/base/tendermint/v1beta1/node_info", timeout=10.0)
        
        response_time = time.time() - start_time
        result["response_time"] = round(response_time * 1000, 2)  # Convert to ms
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract chain ID
            if "default_node_info" in data and "network" in data["default_node_info"]:
                result["chain_id"] = data["default_node_info"]["network"]
                
                # Verify it's mainnet (secret-4)
                if result["chain_id"] == "secret-4":
                    result["status"] = "SUCCESS"
                    
                    # Get latest block height
                    try:
                        block_response = await client.get(f"{endpoint['url']}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=5.0)
                        if block_response.status_code == 200:
                            block_data = block_response.json()
                            if "block" in block_data and "header" in block_data["block"]:
                                result["latest_block"] = block_data["block"]["header"]["height"]
                    except Exception as e:
                        pass  # Block height is optional
                        
                else:
                    result["error"] = f"Wrong network: {result['chain_id']} (expected: secret-4)"
            else:
                result["error"] = "Could not extract chain ID from response"
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
            
    except asyncio.TimeoutError:
        result["error"] = "Connection timeout (>10s)"
    except Exception as e:
        result["error"] = str(e)
    
    return result

async def test_all_endpoints() -> List[Dict]:
    """Test all LCD endpoints concurrently"""
    async with httpx.AsyncClient() as client:
        tasks = [test_endpoint(client, endpoint) for endpoint in MAINNET_ENDPOINTS]
        results = await asyncio.gather(*tasks)
    return results

def print_results(results: List[Dict]):
    """Print formatted test results"""
    print("=" * 80)
    print("SECRET NETWORK MAINNET LCD ENDPOINT TESTING")
    print("=" * 80)
    print()
    
    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    
    print(f"✅ SUCCESSFUL ENDPOINTS: {len(successful)}/{len(results)}")
    print("-" * 40)
    
    for result in successful:
        print(f"✅ {result['name']} ({result['provider']})")
        print(f"   URL: {result['url']}")
        print(f"   Response Time: {result['response_time']}ms")
        print(f"   Chain ID: {result['chain_id']}")
        if result['latest_block']:
            print(f"   Latest Block: {result['latest_block']}")
        print()
    
    if failed:
        print(f"❌ FAILED ENDPOINTS: {len(failed)}")
        print("-" * 40)
        
        for result in failed:
            print(f"❌ {result['name']} ({result['provider']})")
            print(f"   URL: {result['url']}")
            print(f"   Error: {result['error']}")
            if result['response_time']:
                print(f"   Response Time: {result['response_time']}ms")
            print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    print("-" * 40)
    
    if successful:
        fastest = min(successful, key=lambda x: x['response_time'] or float('inf'))
        print(f"🚀 FASTEST: {fastest['name']} ({fastest['response_time']}ms)")
        print(f"   Use: SECRET_NODE_URL={fastest['url']}")
        print()
        
        print("🔄 BACKUP OPTIONS (in order of preference):")
        sorted_successful = sorted(successful, key=lambda x: x['response_time'] or float('inf'))
        for i, result in enumerate(sorted_successful[1:4], 2):  # Top 3 backups
            print(f"   {i}. {result['name']} - {result['response_time']}ms")
            print(f"      SECRET_NODE_URL={result['url']}")
    else:
        print("❌ NO WORKING ENDPOINTS FOUND!")
        print("   Check network connectivity or try again later.")

async def main():
    """Main testing function"""
    print("Testing Secret Network mainnet LCD endpoints...")
    print("This may take up to 30 seconds...\n")
    
    results = await test_all_endpoints()
    print_results(results)

if __name__ == "__main__":
    asyncio.run(main())
```

## **Quick Manual Testing**

Test endpoints manually with curl:

```bash
# Test Secret Saturn (primary)
curl -s "https://lcd.mainnet.secretsaturn.net/cosmos/base/tendermint/v1beta1/node_info" | jq '.default_node_info.network'

# Should return: "secret-4"
```

## **Integration with Secret AI SDK**

### **Updated Environment Variables:**
```bash
# Mainnet Configuration
SECRET_CHAIN_ID=secret-4
SECRET_NODE_URL=https://lcd.mainnet.secretsaturn.net  # Primary
```

### **Fallback Configuration:**
```python
# In code, implement fallback logic:
MAINNET_LCD_ENDPOINTS = [
    "https://lcd.mainnet.secretsaturn.net",
    "https://secretnetwork-api.lavenderfive.com:443", 
    "https://1rpc.io/scrt-lcd",
    "https://rest-secret.01node.com"
]

async def get_working_endpoint():
    """Find first working LCD endpoint"""
    for endpoint in MAINNET_LCD_ENDPOINTS:
        try:
            # Test connectivity
            response = await httpx.get(f"{endpoint}/cosmos/base/tendermint/v1beta1/node_info")
            if response.status_code == 200:
                data = response.json()
                if data.get("default_node_info", {}).get("network") == "secret-4":
                    return endpoint
        except:
            continue
    raise Exception("No working mainnet LCD endpoints found")
```

## **Validation Steps**

1. **Run endpoint test**: `python tools/test_secret_network_endpoints.py`
2. **Choose fastest endpoint** from results
3. **Update .env**: Set `SECRET_NODE_URL` to chosen endpoint
4. **Test Secret AI connectivity**: Verify `get_models()` works
5. **Set backup endpoints** in deployment configuration

## **Expected Results**

- **Chain ID**: Must be `secret-4` (mainnet)
- **Response time**: < 2000ms preferred
- **Latest block**: Should be recent (within minutes)
- **Secret AI models**: Should discover available models via smart contract

This ensures we're connecting to the correct mainnet network for production Secret AI usage.
