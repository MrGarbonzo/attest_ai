import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field

try:
    import arweave
except ImportError:
    # Mock for development
    class MockWallet:
        def __init__(self, jwk_data):
            self.jwk_data = jwk_data
            self.balance = 0
            self.address = "mock_address_1234567890"
        
        def sign(self, transaction):
            transaction.signature = "mock_signature"
            return transaction
    
    class MockTransaction:
        def __init__(self, wallet, **kwargs):
            self.id = f"mock_tx_{datetime.utcnow().timestamp()}"
            self.data = kwargs.get('data', '')
            self.tags = kwargs.get('tags', {})
            self.reward = 1000000  # Mock reward in winston
            self.signature = None
    
    class arweave:
        @staticmethod
        def Wallet(jwk_data):
            return MockWallet(jwk_data)
        
        Transaction = MockTransaction

from ..config import get_settings
from ..utils import hash_data

logger = logging.getLogger(__name__)


class ArweaveTransaction(BaseModel):
    """Represents an Arweave transaction"""
    id: str
    data: Dict[str, Any]
    tags: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cost_winston: int = 0
    cost_ar: float = 0.0
    status: str = "pending"  # pending, submitted, confirmed, mocked


class UploadResult(BaseModel):
    """Result of an Arweave upload attempt"""
    success: bool
    transaction_id: Optional[str] = None
    transaction_url: Optional[str] = None
    mocked: bool = False
    reason: Optional[str] = None
    cost_ar: Optional[float] = None
    wallet_balance_ar: Optional[float] = None


class ArweaveClient:
    """Client for Arweave blockchain operations"""
    
    WINSTON_PER_AR = 1_000_000_000_000  # 1 AR = 10^12 winston
    
    def __init__(self):
        self.settings = get_settings()
        self.wallet = None
        self.gateway_url = self.settings.ARWEAVE_GATEWAY
        
        # Initialize wallet from JWK
        self._initialize_wallet()
    
    def _initialize_wallet(self):
        """Initialize Arweave wallet from JWK in environment"""
        try:
            wallet_jwk = self.settings.get_arweave_wallet_dict()
            self.wallet = arweave.Wallet(wallet_jwk)
            logger.info(f"Initialized Arweave wallet: {self.wallet.address}")
        except Exception as e:
            logger.error(f"Failed to initialize Arweave wallet: {e}")
            self.wallet = None
    
    async def get_wallet_info(self) -> Dict[str, Any]:
        """
        Get wallet information including balance
        
        Returns:
            Dictionary with wallet info
        """
        if not self.wallet:
            return {
                "initialized": False,
                "error": "Wallet not initialized"
            }
        
        try:
            # Get wallet balance
            balance_winston = self.wallet.balance
            balance_ar = balance_winston / self.WINSTON_PER_AR
            
            return {
                "initialized": True,
                "address": self.wallet.address,
                "balance_winston": balance_winston,
                "balance_ar": balance_ar,
                "funded": balance_ar > 0.01,  # Consider funded if > 0.01 AR
                "gateway": self.gateway_url
            }
        except Exception as e:
            logger.error(f"Error getting wallet info: {e}")
            return {
                "initialized": True,
                "address": self.wallet.address,
                "error": str(e)
            }
    
    def estimate_upload_cost(self, data_size_bytes: int) -> Dict[str, Any]:
        """
        Estimate cost for uploading data to Arweave
        
        Args:
            data_size_bytes: Size of data in bytes
            
        Returns:
            Cost estimation
        """
        # Rough estimation: ~0.00001 AR per KB
        # This is a simplified estimation - actual costs vary
        cost_per_byte = 0.00001 / 1024  # AR per byte
        estimated_cost_ar = data_size_bytes * cost_per_byte
        estimated_cost_winston = int(estimated_cost_ar * self.WINSTON_PER_AR)
        
        return {
            "data_size_bytes": data_size_bytes,
            "data_size_kb": data_size_bytes / 1024,
            "estimated_cost_winston": estimated_cost_winston,
            "estimated_cost_ar": estimated_cost_ar
        }
    
    async def create_transaction(
        self,
        data: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None
    ) -> ArweaveTransaction:
        """
        Create an Arweave transaction
        
        Args:
            data: Data to store (will be JSON serialized)
            tags: Optional tags for the transaction
            
        Returns:
            ArweaveTransaction object
        """
        if not self.wallet:
            raise Exception("Wallet not initialized")
        
        # Serialize data
        data_str = json.dumps(data, sort_keys=True, default=str)
        
        # Default tags
        default_tags = {
            "Content-Type": "application/json",
            "App-Name": "attest_ai",
            "App-Version": "0.1.0",
            "Type": "attestation-proof"
        }
        
        if tags:
            default_tags.update(tags)
        
        try:
            # Create transaction
            tx = arweave.Transaction(
                wallet=self.wallet,
                data=data_str,
                tags=default_tags
            )
            
            # Get transaction cost
            reward_winston = getattr(tx, 'reward', 0)
            reward_ar = reward_winston / self.WINSTON_PER_AR
            
            transaction = ArweaveTransaction(
                id=tx.id,
                data=data,
                tags=default_tags,
                cost_winston=reward_winston,
                cost_ar=reward_ar
            )
            
            # Store the raw transaction for later use
            transaction._raw_tx = tx
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    async def upload_data(
        self,
        data: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
        force_mock: bool = False
    ) -> UploadResult:
        """
        Upload data to Arweave with smart mock logic
        
        Args:
            data: Data to upload
            tags: Optional transaction tags
            force_mock: Force mock upload regardless of funding
            
        Returns:
            UploadResult with transaction details
        """
        if not self.settings.ENABLE_ARWEAVE_UPLOAD:
            return UploadResult(
                success=False,
                mocked=True,
                reason="Arweave uploads disabled"
            )
        
        # Get wallet info
        wallet_info = await self.get_wallet_info()
        
        if not wallet_info.get("initialized"):
            return UploadResult(
                success=False,
                reason="Wallet not initialized"
            )
        
        try:
            # Create transaction
            transaction = await self.create_transaction(data, tags)
            
            # Check if we should mock
            should_mock = force_mock or (
                self.settings.MOCK_UNFUNDED_TRANSACTIONS and 
                not wallet_info.get("funded", False)
            )
            
            if should_mock:
                # Mock upload
                logger.info(f"Mocking Arweave upload (unfunded wallet)")
                
                mock_id = f"mock_{hash_data(data)[:16]}_{datetime.utcnow().timestamp()}"
                
                return UploadResult(
                    success=True,
                    transaction_id=mock_id,
                    transaction_url=f"{self.gateway_url}/mock/{mock_id}",
                    mocked=True,
                    reason="Wallet unfunded - transaction mocked",
                    cost_ar=transaction.cost_ar,
                    wallet_balance_ar=wallet_info.get("balance_ar", 0)
                )
            
            # Real upload
            logger.info(f"Uploading to Arweave (transaction cost: {transaction.cost_ar:.6f} AR)")
            
            # Sign and send transaction
            raw_tx = transaction._raw_tx
            self.wallet.sign(raw_tx)
            raw_tx.send()
            
            return UploadResult(
                success=True,
                transaction_id=transaction.id,
                transaction_url=f"{self.gateway_url}/{transaction.id}",
                mocked=False,
                cost_ar=transaction.cost_ar,
                wallet_balance_ar=wallet_info.get("balance_ar", 0)
            )
            
        except Exception as e:
            logger.error(f"Error uploading to Arweave: {e}")
            
            # Try mock if real upload fails and mocking is enabled
            if self.settings.MOCK_UNFUNDED_TRANSACTIONS:
                mock_id = f"mock_error_{hash_data(data)[:16]}"
                return UploadResult(
                    success=True,
                    transaction_id=mock_id,
                    transaction_url=f"{self.gateway_url}/mock/{mock_id}",
                    mocked=True,
                    reason=f"Upload failed, mocked: {str(e)}",
                    wallet_balance_ar=wallet_info.get("balance_ar", 0)
                )
            
            return UploadResult(
                success=False,
                reason=str(e)
            )
    
    async def create_attestation_proof(
        self,
        self_attestation: Dict[str, Any],
        secret_ai_attestation: Optional[Dict[str, Any]],
        chat_data: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """
        Create and upload a complete attestation proof
        
        Args:
            self_attestation: Self VM attestation data
            secret_ai_attestation: Secret AI VM attestation data
            chat_data: Optional chat interaction data
            
        Returns:
            UploadResult
        """
        # Build proof data
        proof_data = {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "attestations": {
                "self": self_attestation,
                "secret_ai": secret_ai_attestation
            },
            "proof_hash": None  # Will be set after hashing
        }
        
        if chat_data:
            proof_data["chat"] = chat_data
        
        # Generate proof hash
        proof_data["proof_hash"] = hash_data(proof_data)
        
        # Create tags
        tags = {
            "Proof-Type": "dual-attestation",
            "Has-Chat": "true" if chat_data else "false",
            "Timestamp": datetime.utcnow().isoformat()
        }
        
        # Upload to Arweave
        return await self.upload_data(proof_data, tags)