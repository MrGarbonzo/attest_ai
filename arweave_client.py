import os
import json
import time
import random
import string
from typing import Dict, Any, Optional
# Optional import - will use mock if not available
try:
    from mnemonic import Mnemonic
    MNEMONIC_AVAILABLE = True
except ImportError:
    MNEMONIC_AVAILABLE = False
    print("⚠️ Warning: mnemonic library not available")

class ArweaveClient:
    def __init__(self):
        self.mnemonic = os.getenv("ARWEAVE_MNEMONIC")
        self.gateway = os.getenv("ARWEAVE_GATEWAY", "https://arweave.net")
        self.wallet = None
        self.wallet_initialized = False
        
        if not self.mnemonic:
            raise ValueError("ARWEAVE_MNEMONIC environment variable required")
        
        # Try to import arweave library
        self._init_arweave_lib()
    
    def _init_arweave_lib(self):
        """Initialize Arweave library with graceful fallback"""
        try:
            import arweave
            from arweave import Wallet, Transaction
            from arweave.utils import winston_to_ar, ar_to_winston
            
            self.arweave = arweave
            self.Wallet = Wallet
            self.Transaction = Transaction
            self.winston_to_ar = winston_to_ar
            self.ar_to_winston = ar_to_winston
            self.lib_available = True
            print("✅ Arweave Python SDK loaded successfully")
        except ImportError as e:
            print(f"⚠️ Warning: Arweave library not available: {e}")
            print("   Will use mock transactions for demonstration")
            self.lib_available = False
    
    async def initialize_wallet(self) -> bool:
        """Initialize Arweave wallet from mnemonic"""
        if not self.lib_available:
            print("Arweave library not available, using mock wallet")
            return False
            
        try:
            # For MVP, we'll create a mock JWK from mnemonic
            # In production, you'd derive the actual key from mnemonic
            if MNEMONIC_AVAILABLE:
                mnemo = Mnemonic("english")
                # Validate mnemonic
                if not mnemo.check(self.mnemonic):
                    print("Warning: Invalid mnemonic, using mock wallet")
                    return False
            else:
                print("Note: Mnemonic validation skipped (library not available)")
            
            # Create a mock JWK structure (in production, derive from mnemonic)
            # This is a placeholder - real implementation would derive RSA key from mnemonic
            mock_jwk = {
                "kty": "RSA",
                "e": "AQAB",
                "n": "mock_n_value_" + "x" * 300,
                "d": "mock_d_value_" + "x" * 300,
                "p": "mock_p_value_" + "x" * 150,
                "q": "mock_q_value_" + "x" * 150,
                "dp": "mock_dp_value_" + "x" * 150,
                "dq": "mock_dq_value_" + "x" * 150,
                "qi": "mock_qi_value_" + "x" * 150
            }
            
            # Try to create wallet from JWK data
            self.wallet = self.Wallet.from_data(mock_jwk)
            self.wallet_initialized = True
            return True
            
        except Exception as e:
            print(f"Wallet initialization failed: {e}")
            self.wallet_initialized = False
            return False
    
    async def get_wallet_info(self) -> Dict[str, Any]:
        """Get wallet address and balance"""
        if not self.lib_available:
            return self._create_mock_wallet_info("Arweave library not available")
            
        if not self.wallet_initialized:
            success = await self.initialize_wallet()
            if not success:
                return self._create_mock_wallet_info("Wallet initialization failed")
        
        try:
            # Get wallet address
            address = self.wallet.address if hasattr(self.wallet, 'address') else "mock_address"
            
            # Try to get balance (this will likely fail without real wallet)
            try:
                balance = self.wallet.balance
                balance_ar = f"{balance:.6f} AR"
            except Exception:
                balance = 0
                balance_ar = "0.000000 AR (unfunded)"
            
            return {
                "address": address,
                "balance": balance,
                "balance_ar": balance_ar,
                "success": True,
                "mock": address.startswith("mock_")
            }
        except Exception as e:
            return self._create_mock_wallet_info(str(e))
    
    async def upload_proof(self, proof_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload proof to Arweave or create mock transaction"""
        if not self.lib_available:
            return self._create_mock_transaction(proof_data, "Arweave library not available")
            
        if not self.wallet_initialized:
            success = await self.initialize_wallet()
            if not success:
                return self._create_mock_transaction(proof_data, "Wallet initialization failed")
        
        try:
            # Create transaction with proof data
            data_str = json.dumps(proof_data, indent=2)
            data_bytes = data_str.encode('utf-8')
            
            transaction = self.Transaction(
                self.wallet,
                data=data_bytes
            )
            
            # Add metadata tags following ANS-112 standard
            transaction.add_tag('Data-Protocol', 'Provenance-Confirmation')
            transaction.add_tag('Content-Type', 'application/json')
            transaction.add_tag('App-Name', 'attest_ai')
            transaction.add_tag('App-Version', '1.0.0')
            transaction.add_tag('Type', 'attestation-proof')
            transaction.add_tag('Attestation-Type', 'dual-vm')
            transaction.add_tag('Hashing-Algo', 'sha256')
            transaction.add_tag('Unix-Time', str(int(time.time())))
            
            # Add model info if available
            if 'attestations' in proof_data:
                model = proof_data['attestations'].get('secret_ai_vm', {}).get('model', '')
                if model:
                    transaction.add_tag('Model', model)
            
            # Add data hash
            import hashlib
            data_hash = hashlib.sha256(data_bytes).hexdigest()
            transaction.add_tag('Data-Hash', data_hash)
            
            # Sign transaction
            transaction.sign()
            
            # Try to send transaction
            try:
                transaction.send()
                
                # Calculate cost
                cost_winston = transaction.reward if hasattr(transaction, 'reward') else 0
                cost_ar = self.winston_to_ar(cost_winston) if cost_winston else 0.001
                
                return {
                    "success": True,
                    "transaction_id": transaction.id,
                    "arweave_url": f"{self.gateway}/{transaction.id}",
                    "cost_ar": cost_ar,
                    "mocked": False,
                    "data_size": len(data_bytes),
                    "tags": len(transaction.tags) if hasattr(transaction, 'tags') else 9
                }
            except Exception as send_error:
                # Transaction created but send failed (likely due to no funds)
                print(f"Transaction send failed: {send_error}")
                return self._create_mock_transaction(
                    proof_data, 
                    f"Transaction created but upload failed: {str(send_error)}",
                    transaction_id=transaction.id if hasattr(transaction, 'id') else None
                )
                
        except Exception as e:
            print(f"Transaction creation failed: {e}")
            return self._create_mock_transaction(proof_data, str(e))
    
    def _create_mock_wallet_info(self, error: str) -> Dict[str, Any]:
        """Create mock wallet info for demo"""
        mock_address = f"mock_{''.join(random.choices(string.ascii_letters + string.digits, k=43))}"
        return {
            "address": mock_address,
            "balance": 0,
            "balance_ar": "0.000000 AR (mock)",
            "success": False,
            "mock": True,
            "error": error
        }
    
    def _create_mock_transaction(
        self, 
        proof_data: Dict[str, Any], 
        error: str,
        transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create mock transaction for demo purposes"""
        # Generate mock transaction ID if not provided
        if not transaction_id:
            transaction_id = f"mock_{''.join(random.choices(string.ascii_letters + string.digits, k=43))}"
        
        data_str = json.dumps(proof_data, indent=2)
        data_size = len(data_str.encode('utf-8'))
        
        # Estimate cost based on data size (roughly 0.00001 AR per KB)
        estimated_cost = max(0.001, data_size / 100000)
        
        return {
            "success": False,
            "transaction_id": transaction_id,
            "arweave_url": f"{self.gateway}/{transaction_id}",
            "cost_ar": estimated_cost,
            "mocked": True,
            "error": error,
            "note": "Mock transaction - real upload requires funded wallet",
            "data_size": data_size,
            "tags": 9
        }