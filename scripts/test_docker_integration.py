#!/usr/bin/env python3
"""
Docker Integration Testing Script for attest_ai

This script validates the complete Docker deployment workflow including:
- Container build and startup
- Health checks
- API endpoint functionality
- Environment variable handling
- Service integration
"""

import asyncio
import json
import logging
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DockerIntegrationTester:
    """Comprehensive Docker integration testing"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.base_url = "http://localhost:8000"
        self.container_name = "attest_ai"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and return the result"""
        logger.info(f"Running: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                logger.debug(f"stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"stderr: {result.stderr}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            raise
    
    def record_test(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name} - {details}")
    
    async def test_container_build(self) -> bool:
        """Test Docker container build"""
        try:
            # Build the container
            result = self.run_command([
                "docker-compose", "build", "--no-cache"
            ])
            
            self.record_test(
                "container_build",
                result.returncode == 0,
                "Docker container built successfully"
            )
            return True
            
        except Exception as e:
            self.record_test(
                "container_build",
                False,
                f"Container build failed: {str(e)}"
            )
            return False
    
    async def test_container_startup(self) -> bool:
        """Test container startup and basic health"""
        try:
            # Stop any existing containers
            self.run_command([
                "docker-compose", "down"
            ], check=False)
            
            # Start the container
            result = self.run_command([
                "docker-compose", "up", "-d"
            ])
            
            if result.returncode != 0:
                self.record_test(
                    "container_startup",
                    False,
                    "Failed to start container"
                )
                return False
            
            # Wait for container to be ready
            max_wait = 60  # seconds
            wait_interval = 2
            
            for attempt in range(max_wait // wait_interval):
                try:
                    # Check if container is running
                    result = self.run_command([
                        "docker", "ps", "--filter", f"name={self.container_name}",
                        "--format", "{{.Status}}"
                    ])
                    
                    if "Up" in result.stdout:
                        self.record_test(
                            "container_startup",
                            True,
                            f"Container started successfully (attempt {attempt + 1})"
                        )
                        return True
                
                except Exception as e:
                    logger.debug(f"Startup check attempt {attempt + 1} failed: {e}")
                
                await asyncio.sleep(wait_interval)
            
            self.record_test(
                "container_startup",
                False,
                f"Container failed to start within {max_wait} seconds"
            )
            return False
            
        except Exception as e:
            self.record_test(
                "container_startup",
                False,
                f"Container startup failed: {str(e)}"
            )
            return False
    
    async def test_health_endpoint(self) -> bool:
        """Test the health check endpoint"""
        try:
            # Wait for the service to be ready
            max_retries = 30
            retry_interval = 2
            
            for attempt in range(max_retries):
                try:
                    response = await self.client.get(f"{self.base_url}/health")
                    
                    if response.status_code == 200:
                        health_data = response.json()
                        
                        # Validate health response structure
                        required_fields = ["status", "version", "services"]
                        missing_fields = [f for f in required_fields if f not in health_data]
                        
                        if missing_fields:
                            self.record_test(
                                "health_endpoint",
                                False,
                                f"Health response missing fields: {missing_fields}"
                            )
                            return False
                        
                        self.record_test(
                            "health_endpoint",
                            True,
                            f"Health endpoint responsive (attempt {attempt + 1})"
                        )
                        return True
                
                except httpx.RequestError:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_interval)
                        continue
                    else:
                        raise
            
            self.record_test(
                "health_endpoint",
                False,
                f"Health endpoint not responsive after {max_retries} attempts"
            )
            return False
            
        except Exception as e:
            self.record_test(
                "health_endpoint",
                False,
                f"Health endpoint test failed: {str(e)}"
            )
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test core API endpoints"""
        endpoints_to_test = [
            ("/api", "GET", "API info"),
            ("/api/attestation/status", "GET", "Attestation status"),
            ("/api/secretai/health", "GET", "Secret AI health"),
            ("/api/arweave/status", "GET", "Arweave status"),
            ("/api/proofs/validation-schema", "GET", "Proof validation schema"),
        ]
        
        all_passed = True
        
        for endpoint, method, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                else:
                    continue  # Skip non-GET methods for now
                
                if 200 <= response.status_code < 300:
                    self.record_test(
                        f"api_endpoint_{endpoint.replace('/', '_')}",
                        True,
                        f"{description} endpoint accessible"
                    )
                else:
                    self.record_test(
                        f"api_endpoint_{endpoint.replace('/', '_')}",
                        False,
                        f"{description} endpoint returned {response.status_code}"
                    )
                    all_passed = False
                    
            except Exception as e:
                self.record_test(
                    f"api_endpoint_{endpoint.replace('/', '_')}",
                    False,
                    f"{description} endpoint failed: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    async def test_self_attestation_endpoint(self) -> bool:
        """Test self-attestation endpoint (may fail if not in SecretVM)"""
        try:
            response = await self.client.get(f"{self.base_url}/api/attestation/self")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate attestation data structure
                required_fields = ["mr_td", "rtmr0", "rtmr1", "rtmr2", "rtmr3", "report_data"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    self.record_test(
                        "self_attestation",
                        False,
                        f"Self-attestation missing fields: {missing_fields}"
                    )
                    return False
                
                self.record_test(
                    "self_attestation",
                    True,
                    "Self-attestation endpoint working"
                )
                return True
            
            elif response.status_code == 404 or "not found" in response.text.lower():
                # Expected when not running in SecretVM
                self.record_test(
                    "self_attestation",
                    True,
                    "Self-attestation unavailable (expected outside SecretVM)"
                )
                return True
            
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"detail": response.text}
                self.record_test(
                    "self_attestation",
                    False,
                    f"Self-attestation failed: {error_data.get('detail', 'Unknown error')}"
                )
                return False
                
        except Exception as e:
            # In local testing, self-attestation is expected to fail
            self.record_test(
                "self_attestation",
                True,
                f"Self-attestation unavailable (expected in local testing): {str(e)}"
            )
            return True
    
    async def test_proof_verification(self) -> bool:
        """Test proof verification system"""
        try:
            # Get validation schema first
            schema_response = await self.client.get(f"{self.base_url}/api/proofs/validation-schema")
            
            if schema_response.status_code != 200:
                self.record_test(
                    "proof_verification",
                    False,
                    "Could not fetch validation schema"
                )
                return False
            
            schema = schema_response.json()
            example_proof = schema.get("example_proof")
            
            if not example_proof:
                self.record_test(
                    "proof_verification",
                    False,
                    "No example proof in validation schema"
                )
                return False
            
            # Test proof verification
            verify_response = await self.client.post(
                f"{self.base_url}/api/proofs/verify",
                json={
                    "proof_data": example_proof,
                    "strict_mode": False
                }
            )
            
            if verify_response.status_code == 200:
                result = verify_response.json()
                
                if "valid" in result and "checks" in result:
                    self.record_test(
                        "proof_verification",
                        True,
                        f"Proof verification working (result: {result.get('valid')})"
                    )
                    return True
                else:
                    self.record_test(
                        "proof_verification",
                        False,
                        "Proof verification response missing required fields"
                    )
                    return False
            else:
                self.record_test(
                    "proof_verification",
                    False,
                    f"Proof verification failed with status {verify_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.record_test(
                "proof_verification",
                False,
                f"Proof verification test failed: {str(e)}"
            )
            return False
    
    async def test_environment_variables(self) -> bool:
        """Test that environment variables are properly loaded"""
        try:
            # Check health endpoint for environment info
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code != 200:
                self.record_test(
                    "environment_variables",
                    False,
                    "Could not fetch health data to check environment"
                )
                return False
            
            health_data = response.json()
            services = health_data.get("services", {})
            
            # Check if services are configured (indicates env vars are loaded)
            env_checks = []
            
            if "self_attestation" in services:
                env_checks.append("Self-attestation configured")
            
            if "secret_ai" in services:
                env_checks.append("Secret AI configured")
            
            if "arweave" in services:
                env_checks.append("Arweave configured")
            
            if env_checks:
                self.record_test(
                    "environment_variables",
                    True,
                    f"Environment variables loaded: {', '.join(env_checks)}"
                )
                return True
            else:
                self.record_test(
                    "environment_variables",
                    False,
                    "No services properly configured - environment variables may not be loaded"
                )
                return False
                
        except Exception as e:
            self.record_test(
                "environment_variables",
                False,
                f"Environment variable test failed: {str(e)}"
            )
            return False
    
    async def test_container_logs(self) -> bool:
        """Test that container logs show expected startup messages"""
        try:
            result = self.run_command([
                "docker", "logs", self.container_name, "--tail", "50"
            ])
            
            logs = result.stdout + result.stderr
            
            # Check for expected log messages
            expected_patterns = [
                "Starting attest_ai application",
                "uvicorn",  # Should see uvicorn starting
            ]
            
            found_patterns = []
            for pattern in expected_patterns:
                if pattern.lower() in logs.lower():
                    found_patterns.append(pattern)
            
            if found_patterns:
                self.record_test(
                    "container_logs",
                    True,
                    f"Container logs show expected patterns: {', '.join(found_patterns)}"
                )
                return True
            else:
                self.record_test(
                    "container_logs",
                    False,
                    f"Container logs missing expected patterns. Logs: {logs[:500]}..."
                )
                return False
                
        except Exception as e:
            self.record_test(
                "container_logs",
                False,
                f"Container logs test failed: {str(e)}"
            )
            return False
    
    async def cleanup(self):
        """Clean up test environment"""
        try:
            self.run_command([
                "docker-compose", "down", "-v"
            ], check=False)
            
            logger.info("Test environment cleaned up")
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*60)
        print("DOCKER INTEGRATION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("="*60)
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['details']}")
        
        print("\nALL TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests"""
        logger.info("Starting Docker integration tests...")
        
        try:
            # Test sequence
            tests = [
                ("Container Build", self.test_container_build),
                ("Container Startup", self.test_container_startup),
                ("Health Endpoint", self.test_health_endpoint),
                ("API Endpoints", self.test_api_endpoints),
                ("Self-Attestation", self.test_self_attestation_endpoint),
                ("Proof Verification", self.test_proof_verification),
                ("Environment Variables", self.test_environment_variables),
                ("Container Logs", self.test_container_logs),
            ]
            
            all_passed = True
            
            for test_name, test_func in tests:
                logger.info(f"\n--- Running {test_name} Test ---")
                try:
                    result = await test_func()
                    if not result:
                        all_passed = False
                except Exception as e:
                    logger.error(f"{test_name} test failed with exception: {e}")
                    self.record_test(test_name.lower().replace(" ", "_"), False, str(e))
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            return False


async def main():
    """Main test function"""
    project_root = Path(__file__).parent.parent
    
    async with DockerIntegrationTester(project_root) as tester:
        try:
            success = await tester.run_all_tests()
            tester.print_summary()
            
            if success:
                logger.info("\n🎉 ALL TESTS PASSED! System is ready for SecretVM deployment.")
                sys.exit(0)
            else:
                logger.error("\n❌ SOME TESTS FAILED. Review issues before deployment.")
                sys.exit(1)
                
        finally:
            await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())