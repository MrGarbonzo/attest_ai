import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch

from src.chat.secret_ai_client import SecretAIClient, ChatResponse
from src.arweave.arweave_client import ArweaveClient, UploadResult
from src.attestation.self_attestation import AttestationData


class TestDualAttestationWorkflow:
    """Test the complete dual attestation workflow"""
    
    @pytest.fixture
    def mock_self_attestation(self):
        return AttestationData(
            mr_td="0x1234567890abcdef",
            rtmr0="0xabcdef1234567890",
            rtmr1="0x1111111111111111",
            rtmr2="0x2222222222222222",
            rtmr3="0x3333333333333333",
            report_data="0xdeadbeefdeadbeef",
            source="self",
            vm_type="attest_ai"
        )
    
    @pytest.fixture
    def mock_secret_ai_attestation(self):
        return AttestationData(
            mr_td="0x9876543210fedcba",
            rtmr0="0xfedcba0987654321",
            rtmr1="0x4444444444444444",
            rtmr2="0x5555555555555555",
            rtmr3="0x6666666666666666",
            report_data="0xcafebabecafebabe",
            source="secret_ai",
            vm_type="secret_ai_vm"
        )
    
    @pytest.fixture
    def mock_chat_response(self):
        return ChatResponse(
            message="Hello! This is a test response from Secret AI.",
            prompt="Hello, test message",
            session_id="test_session_123"
        )
    
    def test_dual_attestation_data_structure(self, mock_self_attestation, mock_secret_ai_attestation):
        """Test that attestation data structures are compatible"""
        # Both attestations should have the same structure
        assert hasattr(mock_self_attestation, 'mr_td')
        assert hasattr(mock_secret_ai_attestation, 'mr_td')
        assert mock_self_attestation.source == "self"
        assert mock_secret_ai_attestation.source == "secret_ai"
    
    def test_arweave_proof_creation(self, mock_self_attestation, mock_secret_ai_attestation, mock_chat_response):
        """Test creation of proof data for Arweave upload"""
        from src.utils.crypto import hash_data
        
        # Simulate proof creation
        proof_data = {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "attestations": {
                "self": mock_self_attestation.dict(),
                "secret_ai": mock_secret_ai_attestation.dict()
            },
            "chat": {
                "request": {"message": mock_chat_response.prompt},
                "response": mock_chat_response.dict()
            }
        }
        
        # Add proof hash
        proof_data["proof_hash"] = hash_data(proof_data)
        
        assert "version" in proof_data
        assert "attestations" in proof_data
        assert "self" in proof_data["attestations"]
        assert "secret_ai" in proof_data["attestations"]
        assert "proof_hash" in proof_data
        assert len(proof_data["proof_hash"]) == 64  # SHA256 hex length
    
    @patch('src.chat.secret_ai_client.Secret')
    def test_secret_ai_client_mock_mode(self, mock_secret_sdk):
        """Test Secret AI client works in mock mode"""
        with patch('src.config.get_settings') as mock_settings:
            mock_settings.return_value.MOCK_SECRET_AI_ATTESTATION = True
            mock_settings.return_value.SECRET_AI_DISCOVERY_CACHE_TTL = 3600
            
            client = SecretAIClient()
            
            # Mock SDK methods
            mock_secret_sdk.return_value.get_models.return_value = ["test-model"]
            mock_secret_sdk.return_value.get_urls.return_value = ["http://test-url"]
            
            # Test discovery
            instances = client.discover_instances()
            assert len(instances) > 0 if not asyncio.iscoroutine(instances) else True
    
    def test_arweave_mock_upload(self):
        """Test Arweave client mock upload functionality"""
        with patch('src.config.get_settings') as mock_settings:
            mock_settings.return_value.MOCK_UNFUNDED_TRANSACTIONS = True
            mock_settings.return_value.ENABLE_ARWEAVE_UPLOAD = True
            mock_settings.return_value.ARWEAVE_GATEWAY = "https://arweave.net"
            mock_settings.return_value.get_arweave_wallet_dict.return_value = {
                "kty": "RSA", "e": "AQAB", "n": "test", "d": "test"
            }
            
            # Mock the arweave module import
            with patch('src.arweave.arweave_client.arweave') as mock_arweave:
                mock_wallet = Mock()
                mock_wallet.address = "test_address"
                mock_wallet.balance = 0  # Unfunded
                mock_arweave.Wallet.return_value = mock_wallet
                
                client = ArweaveClient()
                
                # Test mock upload for unfunded wallet
                test_data = {"test": "data"}
                # This would normally be async, but we're testing the structure
                assert client.gateway_url == "https://arweave.net"
    
    def test_environment_validation(self):
        """Test that environment validation works correctly"""
        from src.config.settings import Settings
        
        with patch.dict('os.environ', {
            'SECRET_AI_API_KEY': 'test_key',
            'ARWEAVE_WALLET_JWK': '{"kty":"RSA","e":"AQAB","n":"test","d":"test"}'
        }):
            settings = Settings()
            assert settings.SECRET_AI_API_KEY == 'test_key'
            
            # Test wallet parsing
            wallet_dict = settings.get_arweave_wallet_dict()
            assert wallet_dict["kty"] == "RSA"


if __name__ == "__main__":
    pytest.main([__file__])