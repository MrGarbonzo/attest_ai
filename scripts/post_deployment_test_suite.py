#!/usr/bin/env python3
"""
Post-Deployment Test Suite for attest_ai SecretVM Deployment

Comprehensive testing suite that validates the complete deployment
after SecretVM deployment, ensuring all systems work end-to-end.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostDeploymentTestSuite:
    """Comprehensive post-deployment testing suite"""
    
    def __init__(self, vm_url: str, run_extended_tests: bool = False):
        self.vm_url = vm_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)
        self.run_extended_tests = run_extended_tests
        self.test_results = []
        self.test_session_id = f"test_session_{int(time.time())}"
        
        # Test configuration
        self.test_messages = [
            "Hello from the post-deployment test suite!",
            "Testing dual attestation capture in SecretVM environment.",
            "Validating cryptographic proof generation workflow.",
            "Final test message for end-to-end validation."
        ]
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, category: str, 
                       passed: bool, details: str = "", 
                       data: Optional[Dict] = None, 
                       duration_ms: float = 0):
        """Log test result with comprehensive details"""
        result = {
            'test_name': test_name,
            'category': category,
            'passed': passed,
            'details': details,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        duration_str = f"({duration_ms:.0f}ms)" if duration_ms > 0 else ""
        logger.info(f"{status}: {category}/{test_name} {duration_str} - {details}")
        
        return result
    
    async def test_deployment_readiness(self) -> bool:
        """Test basic deployment readiness"""
        logger.info("=== Testing Deployment Readiness ===")
        
        start_time = time.time()
        
        try:
            # Test 1: Health endpoint
            health_response = await self.client.get(f"{self.vm_url}:8000/health")
            health_time = (time.time() - start_time) * 1000
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                self.log_test_result(
                    "health_endpoint", "readiness", True,
                    f"Health endpoint responding with services: {', '.join(health_data.get('services', {}).keys())}",
                    health_data, health_time
                )
                
                # Check critical services
                services = health_data.get('services', {})
                self_attestation_available = services.get('self_attestation', {}).get('available', False)
                
                self.log_test_result(
                    "self_attestation_service", "readiness", self_attestation_available,
                    f"Self-attestation service: {'Available' if self_attestation_available else 'Unavailable'}"
                )
                
                return self_attestation_available
            else:
                self.log_test_result(
                    "health_endpoint", "readiness", False,
                    f"Health endpoint returned {health_response.status_code}",
                    duration_ms=health_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "health_endpoint", "readiness", False,
                f"Health endpoint failed: {str(e)}"
            )
            return False
    
    async def test_api_comprehensive(self) -> bool:
        """Comprehensive API endpoint testing"""
        logger.info("=== Testing API Endpoints Comprehensively ===")
        
        api_tests = [
            # Core endpoints
            ('/api', 'GET', 'API root documentation'),
            ('/health', 'GET', 'Application health check'),
            
            # Attestation endpoints
            ('/api/attestation/status', 'GET', 'Attestation service status'),
            ('/api/attestation/self', 'GET', 'Self-attestation data'),
            
            # Service health endpoints
            ('/api/secretai/health', 'GET', 'Secret AI service health'),
            ('/api/arweave/status', 'GET', 'Arweave service status'),
            
            # Proof system endpoints
            ('/api/proofs/validation-schema', 'GET', 'Proof validation schema'),
        ]
        
        api_success_count = 0
        
        for endpoint, method, description in api_tests:
            start_time = time.time()
            
            try:
                if method == 'GET':
                    response = await self.client.get(f"{self.vm_url}:8000{endpoint}")
                else:
                    continue  # Skip non-GET for now
                
                duration = (time.time() - start_time) * 1000
                success = response.status_code < 400
                
                if success:
                    api_success_count += 1
                
                # Try to parse JSON if possible
                response_data = None
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        response_data = response.json()
                except:
                    pass
                
                self.log_test_result(
                    f"api_{endpoint.replace('/', '_').strip('_')}", "api",
                    success,
                    f"{description}: {response.status_code}",
                    response_data, duration
                )
                
            except Exception as e:
                self.log_test_result(
                    f"api_{endpoint.replace('/', '_').strip('_')}", "api",
                    False,
                    f"{description}: Error - {str(e)}"
                )
        
        api_success_rate = (api_success_count / len(api_tests)) * 100
        overall_api_success = api_success_rate >= 80
        
        self.log_test_result(
            "overall_api_health", "api", overall_api_success,
            f"API success rate: {api_success_rate:.1f}% ({api_success_count}/{len(api_tests)})"
        )
        
        return overall_api_success
    
    async def test_chat_workflow_complete(self) -> bool:
        """Test complete chat workflow with multiple scenarios"""
        logger.info("=== Testing Complete Chat Workflow ===")
        
        workflow_tests = []
        
        for i, test_message in enumerate(self.test_messages):
            test_name = f"chat_workflow_{i+1}"
            start_time = time.time()
            
            try:
                # Test with different configurations
                configs = [
                    {"message": test_message, "upload_proof": False},
                    {"message": test_message, "upload_proof": True} if i == 0 else None  # Only test upload once
                ]
                
                for j, config in enumerate([c for c in configs if c is not None]):
                    variant_name = f"{test_name}_{'with_upload' if config.get('upload_proof') else 'no_upload'}"
                    
                    response = await self.client.post(
                        f"{self.vm_url}:8000/api/chat/",
                        json=config
                    )
                    
                    duration = (time.time() - start_time) * 1000
                    success = response.status_code == 200
                    
                    if success:
                        chat_data = response.json()
                        
                        # Validate response structure
                        has_chat_response = bool(chat_data.get('chat', {}).get('message'))
                        has_attestations = bool(chat_data.get('attestations', {}))
                        has_self_attestation = bool(chat_data.get('attestations', {}).get('self'))
                        
                        # Check proof upload if requested
                        proof_upload_success = True
                        if config.get('upload_proof'):
                            proof_upload = chat_data.get('proof_upload', {})
                            proof_upload_success = proof_upload.get('success', False)
                        
                        workflow_success = has_chat_response and has_attestations and has_self_attestation
                        if config.get('upload_proof'):
                            workflow_success = workflow_success and proof_upload_success
                        
                        details = f"Chat: {has_chat_response}, Attestations: {has_attestations}, Self: {has_self_attestation}"
                        if config.get('upload_proof'):
                            details += f", Upload: {proof_upload_success}"
                        
                        self.log_test_result(
                            variant_name, "workflow", workflow_success,
                            details, chat_data, duration
                        )
                        
                        workflow_tests.append(workflow_success)
                        
                    else:
                        self.log_test_result(
                            variant_name, "workflow", False,
                            f"Chat request failed: {response.status_code}",
                            duration_ms=duration
                        )
                        workflow_tests.append(False)
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
                
            except Exception as e:
                self.log_test_result(
                    test_name, "workflow", False,
                    f"Chat workflow failed: {str(e)}"
                )
                workflow_tests.append(False)
        
        # Overall workflow assessment
        workflow_success_rate = (sum(workflow_tests) / len(workflow_tests)) * 100 if workflow_tests else 0
        overall_workflow_success = workflow_success_rate >= 75
        
        self.log_test_result(
            "overall_chat_workflow", "workflow", overall_workflow_success,
            f"Chat workflow success rate: {workflow_success_rate:.1f}% ({sum(workflow_tests)}/{len(workflow_tests)})"
        )
        
        return overall_workflow_success
    
    async def test_proof_verification_system(self) -> bool:
        """Test proof verification system thoroughly"""
        logger.info("=== Testing Proof Verification System ===")
        
        try:
            # Step 1: Get validation schema
            start_time = time.time()
            schema_response = await self.client.get(f"{self.vm_url}:8000/api/proofs/validation-schema")
            schema_time = (time.time() - start_time) * 1000
            
            if schema_response.status_code != 200:
                self.log_test_result(
                    "validation_schema", "proof_verification", False,
                    f"Schema endpoint failed: {schema_response.status_code}",
                    duration_ms=schema_time
                )
                return False
            
            schema_data = schema_response.json()
            
            self.log_test_result(
                "validation_schema", "proof_verification", True,
                "Validation schema retrieved successfully",
                schema_data, schema_time
            )
            
            # Step 2: Test with example proof
            example_proof = schema_data.get('example_proof')
            if not example_proof:
                self.log_test_result(
                    "example_proof_availability", "proof_verification", False,
                    "No example proof in schema"
                )
                return False
            
            # Step 3: Verify example proof
            start_time = time.time()
            verify_response = await self.client.post(
                f"{self.vm_url}:8000/api/proofs/verify",
                json={
                    "proof_data": example_proof,
                    "strict_mode": False
                }
            )
            verify_time = (time.time() - start_time) * 1000
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                verification_valid = verify_data.get('valid', False)
                
                self.log_test_result(
                    "proof_verification", "proof_verification", True,
                    f"Proof verification completed, valid: {verification_valid}",
                    verify_data, verify_time
                )
                
                # Step 4: Test strict mode if extended tests enabled
                if self.run_extended_tests:
                    strict_response = await self.client.post(
                        f"{self.vm_url}:8000/api/proofs/verify",
                        json={
                            "proof_data": example_proof,
                            "strict_mode": True
                        }
                    )
                    
                    if strict_response.status_code == 200:
                        strict_data = strict_response.json()
                        self.log_test_result(
                            "proof_verification_strict", "proof_verification", True,
                            f"Strict verification: {strict_data.get('valid', False)}",
                            strict_data
                        )
                
                return True
                
            else:
                self.log_test_result(
                    "proof_verification", "proof_verification", False,
                    f"Proof verification failed: {verify_response.status_code}",
                    duration_ms=verify_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "proof_verification_system", "proof_verification", False,
                f"Proof verification system failed: {str(e)}"
            )
            return False
    
    async def test_ui_functionality(self) -> bool:
        """Test UI functionality and accessibility"""
        logger.info("=== Testing UI Functionality ===")
        
        try:
            start_time = time.time()
            ui_response = await self.client.get(f"{self.vm_url}:8000/")
            ui_time = (time.time() - start_time) * 1000
            
            if ui_response.status_code == 200:
                html_content = ui_response.text
                
                # Check for key UI components
                ui_components = {
                    'title': 'attest_ai' in html_content.lower(),
                    'description': 'cryptographic proof' in html_content.lower(),
                    'tabs': 'tab' in html_content.lower(),
                    'attestation_section': 'attestation' in html_content.lower(),
                    'chat_section': 'chat' in html_content.lower(),
                    'verification_section': 'verification' in html_content.lower(),
                    'javascript': '<script' in html_content.lower(),
                    'css': 'style' in html_content.lower(),
                }
                
                present_components = sum(ui_components.values())
                total_components = len(ui_components)
                ui_completeness = (present_components / total_components) * 100
                
                ui_success = ui_completeness >= 80
                
                self.log_test_result(
                    "ui_accessibility", "ui", ui_success,
                    f"UI components present: {present_components}/{total_components} ({ui_completeness:.1f}%)",
                    ui_components, ui_time
                )
                
                # Test static resources if extended tests enabled
                if self.run_extended_tests:
                    static_resources = ['/static/style.css', '/static/script.js']
                    
                    for resource in static_resources:
                        try:
                            resource_response = await self.client.get(f"{self.vm_url}:8000{resource}")
                            resource_success = resource_response.status_code == 200
                            
                            self.log_test_result(
                                f"static_resource_{resource.split('/')[-1]}", "ui",
                                resource_success,
                                f"Static resource {resource}: {resource_response.status_code}"
                            )
                        except:
                            pass  # Optional resources
                
                return ui_success
                
            else:
                self.log_test_result(
                    "ui_accessibility", "ui", False,
                    f"UI not accessible: {ui_response.status_code}",
                    duration_ms=ui_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "ui_functionality", "ui", False,
                f"UI test failed: {str(e)}"
            )
            return False
    
    async def test_performance_characteristics(self) -> bool:
        """Test performance characteristics under load"""
        logger.info("=== Testing Performance Characteristics ===")
        
        if not self.run_extended_tests:
            logger.info("Skipping performance tests (use --extended for full performance testing)")
            return True
        
        # Performance test configuration
        test_endpoints = [
            '/health',
            '/api/attestation/status',
            '/api/secretai/health',
            '/api/arweave/status'
        ]
        
        concurrent_requests = 5
        iterations = 3
        
        performance_results = []
        
        for iteration in range(iterations):
            logger.info(f"Performance test iteration {iteration + 1}/{iterations}")
            
            for endpoint in test_endpoints:
                # Test concurrent requests
                tasks = []
                start_time = time.time()
                
                for _ in range(concurrent_requests):
                    task = self.client.get(f"{self.vm_url}:8000{endpoint}")
                    tasks.append(task)
                
                try:
                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    total_time = (time.time() - start_time) * 1000
                    
                    successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code < 400]
                    success_rate = (len(successful_responses) / len(responses)) * 100
                    avg_response_time = total_time / len(responses)
                    
                    performance_results.append({
                        'endpoint': endpoint,
                        'iteration': iteration + 1,
                        'concurrent_requests': concurrent_requests,
                        'success_rate': success_rate,
                        'avg_response_time_ms': avg_response_time,
                        'total_time_ms': total_time
                    })
                    
                    self.log_test_result(
                        f"performance_{endpoint.replace('/', '_').strip('_')}_iter_{iteration + 1}",
                        "performance", success_rate >= 80,
                        f"Success: {success_rate:.1f}%, Avg time: {avg_response_time:.0f}ms",
                        duration_ms=avg_response_time
                    )
                    
                except Exception as e:
                    self.log_test_result(
                        f"performance_{endpoint.replace('/', '_').strip('_')}_iter_{iteration + 1}",
                        "performance", False,
                        f"Performance test failed: {str(e)}"
                    )
            
            # Brief pause between iterations
            await asyncio.sleep(2)
        
        # Analyze overall performance
        if performance_results:
            avg_success_rate = sum(r['success_rate'] for r in performance_results) / len(performance_results)
            avg_response_time = sum(r['avg_response_time_ms'] for r in performance_results) / len(performance_results)
            
            performance_acceptable = avg_success_rate >= 85 and avg_response_time <= 3000
            
            self.log_test_result(
                "overall_performance", "performance", performance_acceptable,
                f"Overall - Success: {avg_success_rate:.1f}%, Avg time: {avg_response_time:.0f}ms",
                {'detailed_results': performance_results}
            )
            
            return performance_acceptable
        
        return False
    
    async def test_error_handling_scenarios(self) -> bool:
        """Test error handling scenarios"""
        logger.info("=== Testing Error Handling Scenarios ===")
        
        error_tests = [
            # Invalid chat requests
            ('invalid_chat_empty_message', '/api/chat/', {'message': ''}),
            ('invalid_chat_no_message', '/api/chat/', {}),
            ('invalid_chat_invalid_type', '/api/chat/', {'message': 123}),
            
            # Invalid proof verification
            ('invalid_proof_empty', '/api/proofs/verify', {'proof_data': {}}),
            ('invalid_proof_malformed', '/api/proofs/verify', {'proof_data': 'invalid'}),
        ]
        
        error_handling_successes = 0
        
        for test_name, endpoint, payload in error_tests:
            try:
                start_time = time.time()
                response = await self.client.post(f"{self.vm_url}:8000{endpoint}", json=payload)
                duration = (time.time() - start_time) * 1000
                
                # We expect 4xx errors for invalid requests
                expected_error = 400 <= response.status_code < 500
                
                if expected_error:
                    error_handling_successes += 1
                    
                    # Try to get error details
                    error_details = None
                    try:
                        error_details = response.json()
                    except:
                        pass
                    
                    self.log_test_result(
                        test_name, "error_handling", True,
                        f"Properly rejected invalid request: {response.status_code}",
                        error_details, duration
                    )
                else:
                    self.log_test_result(
                        test_name, "error_handling", False,
                        f"Unexpected response to invalid request: {response.status_code}",
                        duration_ms=duration
                    )
                
            except Exception as e:
                self.log_test_result(
                    test_name, "error_handling", False,
                    f"Error handling test failed: {str(e)}"
                )
        
        error_handling_rate = (error_handling_successes / len(error_tests)) * 100
        error_handling_success = error_handling_rate >= 70
        
        self.log_test_result(
            "overall_error_handling", "error_handling", error_handling_success,
            f"Error handling success rate: {error_handling_rate:.1f}% ({error_handling_successes}/{len(error_tests)})"
        )
        
        return error_handling_success
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        
        # Categorize results
        categories = {}
        for result in self.test_results:
            category = result['category']
            if category not in categories:
                categories[category] = {'passed': 0, 'total': 0, 'failed_tests': []}
            
            categories[category]['total'] += 1
            if result['passed']:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed_tests'].append(result['test_name'])
        
        # Generate report
        report = f"""
╔═════════════════════════════════════════════════════════════════════
║ Post-Deployment Test Suite Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
║ Test Session: {self.test_session_id}
║ Extended Tests: {'ENABLED' if self.run_extended_tests else 'DISABLED'}
╚═════════════════════════════════════════════════════════════════════
"""
        
        total_tests = len(self.test_results)
        total_passed = sum(1 for r in self.test_results if r['passed'])
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Category summary
        for category, data in categories.items():
            success_rate = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
            status_emoji = "✅" if success_rate >= 80 else ("⚠️" if success_rate >= 60 else "❌")
            
            report += f"\n{status_emoji} {category.upper().replace('_', ' ')}:\n"
            report += f"   Passed: {data['passed']}/{data['total']} tests ({success_rate:.1f}%)\n"
            
            if data['failed_tests']:
                report += f"   Failed: {', '.join(data['failed_tests'])}\n"
        
        # Overall assessment
        if overall_success_rate >= 90:
            overall_status = "✅ EXCELLENT"
            deployment_status = "Deployment is production-ready with excellent performance"
        elif overall_success_rate >= 80:
            overall_status = "✅ GOOD"
            deployment_status = "Deployment is ready with good performance"
        elif overall_success_rate >= 70:
            overall_status = "⚠️  ACCEPTABLE"
            deployment_status = "Deployment is functional but needs optimization"
        elif overall_success_rate >= 50:
            overall_status = "⚠️  POOR"
            deployment_status = "Deployment has significant issues"
        else:
            overall_status = "❌ FAILED"
            deployment_status = "Deployment is not ready for production"
        
        report += f"\n🎯 OVERALL RESULTS: {overall_status}\n"
        report += f"   Success Rate: {overall_success_rate:.1f}% ({total_passed}/{total_tests} tests)\n"
        report += f"   Status: {deployment_status}\n"
        
        # Performance summary
        performance_tests = [r for r in self.test_results if r['category'] == 'performance']
        if performance_tests:
            avg_duration = sum(r['duration_ms'] for r in performance_tests if r['duration_ms'] > 0) / len([r for r in performance_tests if r['duration_ms'] > 0])
            report += f"   Average Response Time: {avg_duration:.0f}ms\n"
        
        # Critical failures
        critical_failures = [r for r in self.test_results if not r['passed'] and r['category'] in ['readiness', 'workflow']]
        if critical_failures:
            report += f"\n🚨 CRITICAL ISSUES:\n"
            for failure in critical_failures:
                report += f"   • {failure['test_name']}: {failure['details']}\n"
        
        report += f"\n" + "═" * 70
        
        return report
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete post-deployment test suite"""
        logger.info(f"Starting post-deployment test suite for {self.vm_url}")
        logger.info(f"Extended tests: {'ENABLED' if self.run_extended_tests else 'DISABLED'}")
        
        start_time = time.time()
        
        # Test sequence
        test_sequence = [
            ("Deployment Readiness", self.test_deployment_readiness),
            ("API Comprehensive", self.test_api_comprehensive),
            ("Chat Workflow Complete", self.test_chat_workflow_complete),
            ("Proof Verification System", self.test_proof_verification_system),
            ("UI Functionality", self.test_ui_functionality),
            ("Error Handling Scenarios", self.test_error_handling_scenarios),
        ]
        
        if self.run_extended_tests:
            test_sequence.append(("Performance Characteristics", self.test_performance_characteristics))
        
        # Run all tests
        test_outcomes = []
        
        for test_name, test_function in test_sequence:
            logger.info(f"\n--- Starting {test_name} ---")
            try:
                result = await test_function()
                test_outcomes.append(result)
                logger.info(f"--- {test_name} {'PASSED' if result else 'FAILED'} ---")
            except Exception as e:
                logger.error(f"--- {test_name} FAILED with exception: {e} ---")
                test_outcomes.append(False)
                self.log_test_result(
                    test_name.lower().replace(' ', '_'), "system", False,
                    f"Test suite error: {str(e)}"
                )
        
        total_duration = (time.time() - start_time) * 1000
        
        # Generate and print report
        report = self.generate_test_report()
        print(report)
        
        # Calculate overall success
        overall_success_rate = (sum(test_outcomes) / len(test_outcomes) * 100) if test_outcomes else 0
        suite_passed = overall_success_rate >= 80
        
        return {
            'success': suite_passed,
            'overall_success_rate': overall_success_rate,
            'test_count': len(self.test_results),
            'passed_count': sum(1 for r in self.test_results if r['passed']),
            'duration_ms': total_duration,
            'session_id': self.test_session_id,
            'detailed_results': self.test_results
        }


async def main():
    """Main test suite runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Post-Deployment Test Suite")
    parser.add_argument("--vm-url", help="SecretVM URL (or set SECRETVM_URL env var)")
    parser.add_argument("--extended", action="store_true", help="Run extended tests including performance")
    parser.add_argument("--save-results", help="Save test results to JSON file")
    
    args = parser.parse_args()
    
    # Get VM URL
    vm_url = args.vm_url or os.environ.get("SECRETVM_URL")
    
    if not vm_url:
        # Try to read from .vm_url file
        vm_url_file = Path(__file__).parent.parent / ".vm_url"
        if vm_url_file.exists():
            vm_url = vm_url_file.read_text().strip()
    
    if not vm_url:
        logger.error("SecretVM URL not provided. Use:")
        logger.error("  --vm-url <url>")
        logger.error("  SECRETVM_URL=<url> environment variable")
        logger.error("  Or ensure .vm_url file exists")
        sys.exit(1)
    
    logger.info(f"Running post-deployment tests for: {vm_url}")
    
    async with PostDeploymentTestSuite(vm_url, run_extended_tests=args.extended) as test_suite:
        result = await test_suite.run_complete_test_suite()
        
        if args.save_results:
            try:
                with open(args.save_results, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Test results saved to {args.save_results}")
            except Exception as e:
                logger.error(f"Failed to save results: {e}")
        
        if result['success']:
            logger.info("🎉 POST-DEPLOYMENT TESTS PASSED - System is ready!")
            sys.exit(0)
        else:
            logger.error("❌ POST-DEPLOYMENT TESTS FAILED - System needs attention")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())