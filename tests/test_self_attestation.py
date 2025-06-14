import pytest
from datetime import datetime
from src.attestation.self_attestation import SelfAttestationClient, AttestationData


class TestSelfAttestationParsing:
    """Test attestation HTML parsing logic"""
    
    def test_parse_attestation_html(self):
        """Test parsing of attestation HTML content"""
        client = SelfAttestationClient()
        
        # Sample HTML content similar to what we expect from localhost:29343/cpu.html
        sample_html = """
        <html>
        <body>
        <table>
            <tr><td>mr_td</td><td>0x1234567890abcdef1234567890abcdef</td></tr>
            <tr><td>rtmr0</td><td>0xabcdef1234567890abcdef1234567890</td></tr>
            <tr><td>rtmr1</td><td>0x1111111111111111111111111111111</td></tr>
            <tr><td>rtmr2</td><td>0x2222222222222222222222222222222</td></tr>
            <tr><td>rtmr3</td><td>0x3333333333333333333333333333333</td></tr>
            <tr><td>report_data</td><td>0xdeadbeefdeadbeefdeadbeefdeadbeef</td></tr>
        </table>
        </body>
        </html>
        """
        
        attestation = client._parse_attestation_html(sample_html)
        
        assert isinstance(attestation, AttestationData)
        assert attestation.mr_td == "0x1234567890abcdef1234567890abcdef"
        assert attestation.rtmr0 == "0xabcdef1234567890abcdef1234567890"
        assert attestation.rtmr1 == "0x1111111111111111111111111111111"
        assert attestation.rtmr2 == "0x2222222222222222222222222222222"
        assert attestation.rtmr3 == "0x3333333333333333333333333333333"
        assert attestation.report_data == "0xdeadbeefdeadbeefdeadbeefdeadbeef"
        assert attestation.source == "self"
        assert attestation.vm_type == "attest_ai"
        assert isinstance(attestation.timestamp, datetime)
    
    def test_parse_attestation_html_without_0x_prefix(self):
        """Test parsing when hex values don't have 0x prefix"""
        client = SelfAttestationClient()
        
        sample_html = """
        <table>
            <tr><td>mr_td</td><td>1234567890abcdef</td></tr>
            <tr><td>rtmr0</td><td>abcdef1234567890</td></tr>
            <tr><td>rtmr1</td><td>1111111111111111</td></tr>
            <tr><td>rtmr2</td><td>2222222222222222</td></tr>
            <tr><td>rtmr3</td><td>3333333333333333</td></tr>
            <tr><td>report_data</td><td>deadbeefdeadbeef</td></tr>
        </table>
        """
        
        attestation = client._parse_attestation_html(sample_html)
        
        # Should add 0x prefix automatically
        assert attestation.mr_td.startswith("0x")
        assert attestation.rtmr0.startswith("0x")
    
    def test_parse_attestation_missing_field(self):
        """Test parsing fails gracefully when required field is missing"""
        client = SelfAttestationClient()
        
        incomplete_html = """
        <table>
            <tr><td>mr_td</td><td>0x1234567890abcdef</td></tr>
            <tr><td>rtmr0</td><td>0xabcdef1234567890</td></tr>
            <!-- Missing other fields -->
        </table>
        """
        
        with pytest.raises(ValueError, match="Could not find"):
            client._parse_attestation_html(incomplete_html)