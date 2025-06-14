#!/usr/bin/env python3
"""
SecretVM Deployment Validation Script

This script validates the attest_ai deployment in SecretVM environment,
focusing on SecretVM-specific functionality and real attestation data.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecretVMValidator:
    """Validates attest_ai deployment in SecretVM environment"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
        # Test configuration
        self.test_chat_message = "Hello from SecretVM! This is a test of the dual attestation system."
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def record_test(self, test_name: str, success: bool, details: str = "", critical: bool = True):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "critical": critical,
            "timestamp": time.time()
        })
        
        status = "✅ PASS" if success else ("❌ FAIL" if critical else "⚠️  WARN")
        logger.info(f"{status}: {test_name} - {details}")
    
    async def test_secretvm_environment_detection(self) -> bool:
        """Test that application detects SecretVM environment correctly"""
        try:
            response = await self.client.get(f"{self.base_url}:8000/health")
            
            if response.status_code != 200:
                self.record_test(
                    "secretvm_environment_detection",
                    False,
                    f"Health endpoint returned {response.status_code}"
                )
                return False
            
            health_data = response.json()
            
            # Check if application is aware it's running in SecretVM
            # This would be indicated by successful self-attestation or environment flags
            services = health_data.get("services", {})
            self_attestation = services.get("self_attestation", {})
            
            if self_attestation.get("available"):
                self.record_test(
                    "secretvm_environment_detection",
                    True,
                    "Application successfully detected SecretVM environment (self-attestation available)"
                )
                return True
            else:
                self.record_test(
                    "secretvm_environment_detection",
                    False,
                    "Self-attestation not available - may not be in SecretVM environment",
                    critical=True  # This is critical for SecretVM deployment
                )
                return False
                
        except Exception as e:
            self.record_test(
                "secretvm_environment_detection",
                False,
                f"Failed to check environment: {str(e)}"
            )
            return False
    
    async def test_real_self_attestation(self) -> bool:
        """Test real self-attestation data retrieval from SecretVM"""
        try:
            response = await self.client.get(f"{self.base_url}:8000/api/attestation/self")
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"detail": response.text}
                self.record_test(
                    "real_self_attestation",
                    False,
                    f"Self-attestation failed: {error_data.get('detail', 'Unknown error')}"
                )
                return False
            
            attestation_data = response.json()
            
            # Validate attestation data structure
            required_fields = ["mr_td", "rtmr0", "rtmr1", "rtmr2", "rtmr3", "report_data"]
            missing_fields = [f for f in required_fields if f not in attestation_data]
            
            if missing_fields:
                self.record_test(
                    "real_self_attestation",
                    False,
                    f"Attestation missing required fields: {missing_fields}"
                )
                return False
            
            # Validate that we have real data (not mock/placeholder values)
            real_data_indicators = []
            
            # Check for non-zero, non-placeholder values
            for field in required_fields:
                value = attestation_data.get(field, "")
                if value and value != "0x0" and "mock" not in value.lower() and len(value) > 10:
                    real_data_indicators.append(field)
            
            if len(real_data_indicators) >= 4:  # At least 4 fields should have real data
                self.record_test(
                    "real_self_attestation",
                    True,
                    f"Real attestation data retrieved from SecretVM (fields with real data: {len(real_data_indicators)})"
                )
                return True
            else:
                self.record_test(
                    "real_self_attestation",
                    False,
                    f"Attestation data appears to be mock/placeholder (only {len(real_data_indicators)} fields with real data)"
                )
                return False
                
        except Exception as e:
            self.record_test(
                "real_self_attestation",
                False,
                f"Self-attestation test failed: {str(e)}"
            )
            return False
    
    async def test_secretvm_network_connectivity(self) -> bool:
        """Test external network connectivity from SecretVM"""
        try:
            # Test Secret AI connectivity
            secretai_response = await self.client.get(f"{self.base_url}:8000/api/secretai/health")
            secretai_working = secretai_response.status_code == 200
            
            # Test Arweave connectivity
            arweave_response = await self.client.get(f"{self.base_url}:8000/api/arweave/status")
            arweave_working = arweave_response.status_code == 200
            
            connectivity_results = []
            if secretai_working:
                connectivity_results.append("Secret AI")
            if arweave_working:
                connectivity_results.append("Arweave")
            
            if len(connectivity_results) >= 1:
                self.record_test(
                    "secretvm_network_connectivity",
                    True,
                    f"External connectivity working: {', '.join(connectivity_results)}"
                )
                return True
            else:
                self.record_test(
                    "secretvm_network_connectivity",
                    False,
                    "No external connectivity detected"
                )
                return False
                
        except Exception as e:
            self.record_test(
                "secretvm_network_connectivity",
                False,
                f"Network connectivity test failed: {str(e)}"
            )
            return False
    
    async def test_complete_workflow_in_secretvm(self) -> bool:
        """Test the complete workflow in SecretVM environment"""
        try:
            # Send a chat message with proof upload
            chat_payload = {
                "message": self.test_chat_message,
                "upload_proof": True
            }
            
            response = await self.client.post(
                f"{self.base_url}:8000/api/chat/",
                json=chat_payload
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"detail": response.text}
                self.record_test(
                    "complete_workflow_secretvm",
                    False,
                    f"Chat workflow failed: {error_data.get('detail', 'Unknown error')}"
                )
                return False
            
            workflow_data = response.json()
            
            # Validate workflow components
            components_working = []
            
            # Check chat response
            if workflow_data.get("chat", {}).get("message"):
                components_working.append("Chat")
            
            # Check attestations
            attestations = workflow_data.get("attestations", {})
            if attestations.get("self"):
                components_working.append("Self-Attestation")
            if attestations.get("secret_ai"):
                components_working.append("Secret AI Attestation")
            
            # Check proof upload
            proof_upload = workflow_data.get("proof_upload", {})
            if proof_upload.get("success"):
                if proof_upload.get("mocked"):
                    components_working.append("Proof Upload (Mocked)")
                else:
                    components_working.append("Proof Upload (Real)")
            
            if len(components_working) >= 2:  # At least chat and one attestation
                self.record_test(
                    "complete_workflow_secretvm",
                    True,
                    f"Workflow components working: {', '.join(components_working)}"
                )
                return True
            else:
                self.record_test(
                    "complete_workflow_secretvm",
                    False,
                    f"Insufficient workflow components working: {', '.join(components_working)}"
                )
                return False
                
        except Exception as e:
            self.record_test(
                "complete_workflow_secretvm",
                False,
                f"Complete workflow test failed: {str(e)}"
            )
            return False
    
    async def test_proof_verification_in_secretvm(self) -> bool:
        """Test proof verification system in SecretVM"""
        try:
            # Get validation schema
            schema_response = await self.client.get(f"{self.base_url}:8000/api/proofs/validation-schema")
            
            if schema_response.status_code != 200:
                self.record_test(
                    "proof_verification_secretvm",
                    False,
                    "Could not fetch validation schema"
                )
                return False
            
            schema = schema_response.json()
            example_proof = schema.get("example_proof")
            
            if not example_proof:
                self.record_test(
                    "proof_verification_secretvm",
                    False,
                    "No example proof in validation schema"
                )
                return False
            
            # Test proof verification
            verify_response = await self.client.post(
                f"{self.base_url}:8000/api/proofs/verify",
                json={
                    "proof_data": example_proof,
                    "strict_mode": False
                }
            )
            
            if verify_response.status_code != 200:
                self.record_test(
                    "proof_verification_secretvm",
                    False,
                    f"Proof verification failed with status {verify_response.status_code}"
                )
                return False
            
            verification_result = verify_response.json()
            
            if "valid" in verification_result and "checks" in verification_result:
                self.record_test(
                    "proof_verification_secretvm",
                    True,
                    f"Proof verification working (result: {verification_result.get('valid')})"
                )
                return True
            else:
                self.record_test(
                    "proof_verification_secretvm",
                    False,
                    "Proof verification response missing required fields"
                )
                return False
                
        except Exception as e:
            self.record_test(
                "proof_verification_secretvm",
                False,
                f"Proof verification test failed: {str(e)}"
            )
            return False
    
    async def test_performance_in_secretvm(self) -> bool:
        """Test performance characteristics in SecretVM"""
        try:
            # Test response times for key endpoints
            endpoints = [
                "/health",
                "/api/attestation/self",
                "/api/secretai/health",
                "/api/arweave/status"
            ]
            
            response_times = []
            
            for endpoint in endpoints:
                start_time = time.time()
                try:
                    response = await self.client.get(f"{self.base_url}:8000{endpoint}")
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000  # Convert to ms
                    response_times.append({
                        "endpoint": endpoint,
                        "response_time_ms": response_time,
                        "status_code": response.status_code
                    })
                except Exception as e:
                    response_times.append({
                        "endpoint": endpoint,
                        "response_time_ms": -1,
                        "error": str(e)
                    })
            
            # Calculate average response time for successful requests
            successful_times = [rt["response_time_ms"] for rt in response_times if rt["response_time_ms"] > 0]
            avg_response_time = sum(successful_times) / len(successful_times) if successful_times else 0
            
            if avg_response_time > 0 and avg_response_time < 5000:  # Less than 5 seconds
                self.record_test(
                    "performance_secretvm",
                    True,
                    f"Performance acceptable (avg: {avg_response_time:.0f}ms)",
                    critical=False
                )
                return True
            else:
                self.record_test(
                    "performance_secretvm",
                    False,
                    f"Performance issues detected (avg: {avg_response_time:.0f}ms)",
                    critical=False
                )
                return False
                
        except Exception as e:
            self.record_test(
                "performance_secretvm",
                False,
                f"Performance test failed: {str(e)}",
                critical=False
            )
            return False
    
    async def test_ui_accessibility_in_secretvm(self) -> bool:
        """Test UI accessibility in SecretVM"""
        try:
            # Test main UI endpoint
            response = await self.client.get(f"{self.base_url}:8000/")
            
            if response.status_code != 200:
                self.record_test(
                    "ui_accessibility_secretvm",
                    False,
                    f"UI not accessible (status: {response.status_code})"
                )
                return False
            
            html_content = response.text
            
            # Check for key UI elements
            ui_elements = [
                "attest_ai",  # Title
                "Cryptographic Proof Generation",  # Subtitle
                "tab",  # Tab interface
                "attestation",  # Attestation content
                "chat",  # Chat interface
            ]
            
            found_elements = [element for element in ui_elements if element.lower() in html_content.lower()]
            
            if len(found_elements) >= 4:
                self.record_test(
                    "ui_accessibility_secretvm",
                    True,
                    f"UI accessible with key elements: {', '.join(found_elements)}"
                )
                return True
            else:
                self.record_test(
                    "ui_accessibility_secretvm",
                    False,
                    f"UI missing key elements (found: {', '.join(found_elements)})"
                )
                return False
                
        except Exception as e:
            self.record_test(
                "ui_accessibility_secretvm",
                False,
                f"UI accessibility test failed: {str(e)}"
            )
            return False
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        critical_tests = [r for r in self.test_results if r.get("critical", True)]
        critical_passed = sum(1 for r in critical_tests if r["success"])
        critical_failed = len(critical_tests) - critical_passed
        
        print("\n" + "="*70)
        print("SECRETVM DEPLOYMENT VALIDATION SUMMARY")
        print("="*70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        print(f"Critical Tests: {len(critical_tests)}")
        print(f"Critical Passed: {critical_passed}")
        print(f"Critical Failed: {critical_failed}")
        print(f"Critical Success Rate: {(critical_passed/len(critical_tests))*100:.1f}%")
        print("="*70)
        
        if critical_failed > 0:
            print("\nCRITICAL FAILURES:")
            for result in self.test_results:
                if not result["success"] and result.get("critical", True):
                    print(f"❌ {result['test']}: {result['details']}")
        
        print("\nALL TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else ("❌" if result.get("critical", True) else "⚠️ ")
            print(f"{status} {result['test']}: {result['details']}")
        
        return critical_failed == 0
    
    async def run_all_tests(self) -> bool:
        """Run all SecretVM validation tests"""
        logger.info("Starting SecretVM deployment validation...")
        
        try:
            # Test sequence - ordered by importance
            tests = [
                ("SecretVM Environment Detection", self.test_secretvm_environment_detection),
                ("Real Self-Attestation", self.test_real_self_attestation),
                ("Network Connectivity", self.test_secretvm_network_connectivity),
                ("Complete Workflow", self.test_complete_workflow_in_secretvm),
                ("Proof Verification", self.test_proof_verification_in_secretvm),
                ("UI Accessibility", self.test_ui_accessibility_in_secretvm),
                ("Performance", self.test_performance_in_secretvm),
            ]
            
            for test_name, test_func in tests:
                logger.info(f"\n--- Running {test_name} Test ---")
                try:
                    await test_func()
                except Exception as e:
                    logger.error(f"{test_name} test failed with exception: {e}")
                    self.record_test(test_name.lower().replace(" ", "_"), False, str(e))
            
            return self.print_summary()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            return False


async def main():
    """Main validation function"""
    # Get SecretVM URL from environment or command line
    secretvm_url = os.environ.get("SECRETVM_URL")
    
    if not secretvm_url and len(sys.argv) > 1:
        secretvm_url = sys.argv[1]
    
    if not secretvm_url:
        # Try to read from .vm_url file
        vm_url_file = Path(__file__).parent.parent / ".vm_url"
        if vm_url_file.exists():
            secretvm_url = vm_url_file.read_text().strip()
    
    if not secretvm_url:
        logger.error("SecretVM URL not provided. Use:")
        logger.error("  SECRETVM_URL=<url> python3 test_secretvm_deployment.py")
        logger.error("  python3 test_secretvm_deployment.py <url>")
        logger.error("  Or ensure .vm_url file exists with the URL")
        sys.exit(1)
    
    logger.info(f"Validating SecretVM deployment at: {secretvm_url}")
    
    async with SecretVMValidator(secretvm_url) as validator:
        success = await validator.run_all_tests()
        
        if success:
            logger.info("\n🎉 ALL CRITICAL TESTS PASSED! SecretVM deployment is successful.")
            sys.exit(0)
        else:
            logger.error("\n❌ CRITICAL TESTS FAILED. SecretVM deployment needs attention.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())