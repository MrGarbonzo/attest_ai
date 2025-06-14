#!/usr/bin/env python3
"""
SecretVM Health Validation Script

Comprehensive health validation system for attest_ai deployment
with configurable thresholds and detailed reporting.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthValidator:
    """Comprehensive health validation for SecretVM deployment"""
    
    def __init__(self, vm_url: str, strict_mode: bool = False):
        self.vm_url = vm_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.strict_mode = strict_mode
        self.validation_results = []
        
        # Health thresholds
        self.thresholds = {
            'max_response_time_ms': 3000 if strict_mode else 5000,
            'min_availability_percent': 95 if strict_mode else 80,
            'max_error_rate_percent': 5 if strict_mode else 15,
            'required_services': ['self_attestation'] if strict_mode else [],
            'min_functionality_score': 80 if strict_mode else 60,
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def record_validation(self, category: str, test_name: str, 
                         passed: bool, score: float, 
                         details: str = "", critical: bool = True):
        """Record validation result"""
        self.validation_results.append({
            'category': category,
            'test': test_name,
            'passed': passed,
            'score': score,
            'details': details,
            'critical': critical,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        status = "✅ PASS" if passed else ("❌ FAIL" if critical else "⚠️  WARN")
        logger.info(f"{status}: {category}/{test_name} - Score: {score:.1f} - {details}")
    
    async def validate_basic_connectivity(self) -> Dict[str, Any]:
        """Validate basic connectivity and response"""
        results = {'category': 'connectivity', 'tests': []}
        
        try:
            start_time = time.time()
            response = await self.client.get(f"{self.vm_url}:8000/health")
            response_time = (time.time() - start_time) * 1000
            
            # Test 1: Basic connectivity
            connectivity_passed = response.status_code == 200
            connectivity_score = 100 if connectivity_passed else 0
            self.record_validation(
                'connectivity', 'basic_connectivity',
                connectivity_passed, connectivity_score,
                f"Status: {response.status_code}, Time: {response_time:.0f}ms"
            )
            
            # Test 2: Response time
            response_time_passed = response_time <= self.thresholds['max_response_time_ms']
            response_time_score = max(0, 100 - (response_time / self.thresholds['max_response_time_ms']) * 100)
            self.record_validation(
                'connectivity', 'response_time',
                response_time_passed, response_time_score,
                f"{response_time:.0f}ms (threshold: {self.thresholds['max_response_time_ms']}ms)",
                critical=self.strict_mode
            )
            
            results['tests'] = [
                {'name': 'basic_connectivity', 'passed': connectivity_passed, 'score': connectivity_score},
                {'name': 'response_time', 'passed': response_time_passed, 'score': response_time_score}
            ]
            
            if connectivity_passed:
                return {'success': True, 'response_data': response.json(), **results}
            else:
                return {'success': False, 'error': f"Status {response.status_code}", **results}
                
        except asyncio.TimeoutError:
            self.record_validation(
                'connectivity', 'basic_connectivity',
                False, 0, "Connection timeout"
            )
            return {'success': False, 'error': 'timeout', **results}
            
        except Exception as e:
            self.record_validation(
                'connectivity', 'basic_connectivity',
                False, 0, f"Connection error: {str(e)}"
            )
            return {'success': False, 'error': str(e), **results}
    
    async def validate_service_availability(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual service availability"""
        results = {'category': 'services', 'tests': []}
        
        services = health_data.get('services', {})
        service_scores = []
        
        # Define service criticality
        service_criticality = {
            'self_attestation': 'critical',
            'secret_ai': 'important',
            'arweave': 'optional'
        }
        
        for service_name, service_data in services.items():
            available = service_data.get('available', False)
            criticality = service_criticality.get(service_name, 'optional')
            
            # Calculate score based on availability and criticality
            if available:
                score = 100
            else:
                score = {'critical': 0, 'important': 30, 'optional': 70}.get(criticality, 50)
            
            is_critical = criticality == 'critical' or (self.strict_mode and criticality == 'important')
            
            self.record_validation(
                'services', f'{service_name}_availability',
                available, score,
                f"Available: {available}, Criticality: {criticality}",
                critical=is_critical
            )
            
            service_scores.append(score)
            results['tests'].append({
                'name': f'{service_name}_availability',
                'passed': available,
                'score': score,
                'criticality': criticality
            })
        
        # Overall service availability score
        overall_score = sum(service_scores) / len(service_scores) if service_scores else 0
        overall_passed = overall_score >= self.thresholds['min_availability_percent']
        
        self.record_validation(
            'services', 'overall_availability',
            overall_passed, overall_score,
            f"Average availability: {overall_score:.1f}%"
        )
        
        return {
            'success': overall_passed,
            'overall_score': overall_score,
            'service_count': len(services),
            **results
        }
    
    async def validate_api_endpoints(self) -> Dict[str, Any]:
        """Validate API endpoint availability and performance"""
        results = {'category': 'api_endpoints', 'tests': []}
        
        # Critical endpoints that must work
        critical_endpoints = [
            ('/health', 'Health Check'),
            ('/api', 'API Root'),
            ('/api/attestation/status', 'Attestation Status'),
        ]
        
        # Important endpoints (may fail in some environments)
        important_endpoints = [
            ('/api/attestation/self', 'Self Attestation'),
            ('/api/secretai/health', 'Secret AI Health'),
            ('/api/arweave/status', 'Arweave Status'),
            ('/api/proofs/validation-schema', 'Proof Validation Schema'),
        ]
        
        all_endpoints = critical_endpoints + important_endpoints
        endpoint_results = []
        response_times = []
        
        for endpoint_path, endpoint_name in all_endpoints:
            is_critical = (endpoint_path, endpoint_name) in critical_endpoints
            
            try:
                start_time = time.time()
                response = await self.client.get(f"{self.vm_url}:8000{endpoint_path}")
                response_time = (time.time() - start_time) * 1000
                
                # Check availability
                available = response.status_code < 400
                score = 100 if available else 0
                
                self.record_validation(
                    'api_endpoints', f'endpoint_{endpoint_path.replace("/", "_").strip("_")}',
                    available, score,
                    f"{endpoint_name}: {response.status_code} ({response_time:.0f}ms)",
                    critical=is_critical
                )
                
                if available:
                    response_times.append(response_time)
                
                endpoint_results.append({
                    'path': endpoint_path,
                    'name': endpoint_name,
                    'available': available,
                    'response_time_ms': response_time,
                    'status_code': response.status_code,
                    'critical': is_critical
                })
                
            except Exception as e:
                self.record_validation(
                    'api_endpoints', f'endpoint_{endpoint_path.replace("/", "_").strip("_")}',
                    False, 0,
                    f"{endpoint_name}: Error - {str(e)}",
                    critical=is_critical
                )
                
                endpoint_results.append({
                    'path': endpoint_path,
                    'name': endpoint_name,
                    'available': False,
                    'error': str(e),
                    'critical': is_critical
                })
        
        # Calculate overall API health
        available_count = sum(1 for ep in endpoint_results if ep.get('available', False))
        total_count = len(endpoint_results)
        availability_percent = (available_count / total_count * 100) if total_count > 0 else 0
        
        # Critical endpoints must be available
        critical_available = sum(1 for ep in endpoint_results if ep.get('critical', False) and ep.get('available', False))
        critical_total = sum(1 for ep in endpoint_results if ep.get('critical', False))
        
        critical_passed = critical_available == critical_total if critical_total > 0 else True
        overall_passed = availability_percent >= self.thresholds['min_availability_percent'] and critical_passed
        
        self.record_validation(
            'api_endpoints', 'overall_api_health',
            overall_passed, availability_percent,
            f"Available: {available_count}/{total_count} ({availability_percent:.1f}%), Critical: {critical_available}/{critical_total}"
        )
        
        # Performance validation
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            performance_passed = avg_response_time <= self.thresholds['max_response_time_ms']
            performance_score = max(0, 100 - (avg_response_time / self.thresholds['max_response_time_ms']) * 100)
            
            self.record_validation(
                'api_endpoints', 'api_performance',
                performance_passed, performance_score,
                f"Average response time: {avg_response_time:.0f}ms",
                critical=False
            )
        
        return {
            'success': overall_passed,
            'availability_percent': availability_percent,
            'critical_passed': critical_passed,
            'endpoint_results': endpoint_results,
            **results
        }
    
    async def validate_core_functionality(self) -> Dict[str, Any]:
        """Validate core application functionality"""
        results = {'category': 'functionality', 'tests': []}
        functionality_scores = []
        
        # Test 1: Chat functionality
        try:
            chat_payload = {
                "message": "Health validation test",
                "upload_proof": False
            }
            
            start_time = time.time()
            chat_response = await self.client.post(
                f"{self.vm_url}:8000/api/chat/",
                json=chat_payload
            )
            chat_time = (time.time() - start_time) * 1000
            
            chat_working = chat_response.status_code == 200
            chat_score = 100 if chat_working else 0
            
            if chat_working:
                chat_data = chat_response.json()
                has_chat_response = bool(chat_data.get('chat', {}).get('message'))
                has_attestations = bool(chat_data.get('attestations', {}))
                
                # Bonus points for complete workflow
                if has_chat_response and has_attestations:
                    chat_score = 100
                elif has_chat_response:
                    chat_score = 80
                else:
                    chat_score = 50
                
                details = f"Response: {chat_response.status_code}, Chat: {has_chat_response}, Attestations: {has_attestations}, Time: {chat_time:.0f}ms"
            else:
                details = f"Failed with status {chat_response.status_code}"
            
            self.record_validation(
                'functionality', 'chat_system',
                chat_working, chat_score, details,
                critical=True
            )
            
            functionality_scores.append(chat_score)
            
        except Exception as e:
            self.record_validation(
                'functionality', 'chat_system',
                False, 0, f"Chat test failed: {str(e)}",
                critical=True
            )
            functionality_scores.append(0)
        
        # Test 2: Proof verification system
        try:
            schema_response = await self.client.get(f"{self.vm_url}:8000/api/proofs/validation-schema")
            schema_working = schema_response.status_code == 200
            
            if schema_working:
                schema_data = schema_response.json()
                example_proof = schema_data.get('example_proof')
                
                if example_proof:
                    verify_response = await self.client.post(
                        f"{self.vm_url}:8000/api/proofs/verify",
                        json={
                            "proof_data": example_proof,
                            "strict_mode": False
                        }
                    )
                    
                    verification_working = verify_response.status_code == 200
                    if verification_working:
                        verify_data = verify_response.json()
                        has_validation_result = 'valid' in verify_data
                        proof_score = 100 if has_validation_result else 80
                    else:
                        proof_score = 50
                    
                    details = f"Schema: {schema_response.status_code}, Verification: {verify_response.status_code if 'verify_response' in locals() else 'N/A'}"
                else:
                    proof_score = 60
                    details = "Schema available but no example proof"
            else:
                proof_score = 0
                details = f"Schema endpoint failed: {schema_response.status_code}"
            
            self.record_validation(
                'functionality', 'proof_verification',
                schema_working, proof_score, details,
                critical=False
            )
            
            functionality_scores.append(proof_score)
            
        except Exception as e:
            self.record_validation(
                'functionality', 'proof_verification',
                False, 0, f"Proof verification test failed: {str(e)}",
                critical=False
            )
            functionality_scores.append(0)
        
        # Test 3: UI accessibility
        try:
            ui_response = await self.client.get(f"{self.vm_url}:8000/")
            ui_working = ui_response.status_code == 200
            
            if ui_working:
                html_content = ui_response.text.lower()
                ui_elements = [
                    'attest_ai',
                    'cryptographic proof',
                    'tab',
                    'attestation',
                    'chat'
                ]
                
                found_elements = sum(1 for element in ui_elements if element in html_content)
                ui_score = (found_elements / len(ui_elements)) * 100
                
                details = f"UI accessible, elements found: {found_elements}/{len(ui_elements)}"
            else:
                ui_score = 0
                details = f"UI not accessible: {ui_response.status_code}"
            
            self.record_validation(
                'functionality', 'ui_accessibility',
                ui_working, ui_score, details,
                critical=False
            )
            
            functionality_scores.append(ui_score)
            
        except Exception as e:
            self.record_validation(
                'functionality', 'ui_accessibility',
                False, 0, f"UI test failed: {str(e)}",
                critical=False
            )
            functionality_scores.append(0)
        
        # Overall functionality assessment
        overall_functionality_score = sum(functionality_scores) / len(functionality_scores) if functionality_scores else 0
        functionality_passed = overall_functionality_score >= self.thresholds['min_functionality_score']
        
        self.record_validation(
            'functionality', 'overall_functionality',
            functionality_passed, overall_functionality_score,
            f"Overall functionality score: {overall_functionality_score:.1f}%"
        )
        
        return {
            'success': functionality_passed,
            'overall_score': overall_functionality_score,
            'individual_scores': functionality_scores,
            **results
        }
    
    async def validate_secretvm_specific_features(self) -> Dict[str, Any]:
        """Validate SecretVM-specific features"""
        results = {'category': 'secretvm_features', 'tests': []}
        
        # Test 1: Real self-attestation (should work in SecretVM)
        try:
            attestation_response = await self.client.get(f"{self.vm_url}:8000/api/attestation/self")
            attestation_working = attestation_response.status_code == 200
            
            if attestation_working:
                attestation_data = attestation_response.json()
                
                # Check for real attestation data
                required_fields = ["mr_td", "rtmr0", "rtmr1", "rtmr2", "rtmr3", "report_data"]
                present_fields = [f for f in required_fields if f in attestation_data]
                
                # Check if data looks real (not mock)
                real_data_indicators = []
                for field in present_fields:
                    value = attestation_data.get(field, "")
                    if value and value != "0x0" and "mock" not in value.lower() and len(value) > 10:
                        real_data_indicators.append(field)
                
                if len(real_data_indicators) >= 4:
                    attestation_score = 100
                    details = f"Real attestation data detected ({len(real_data_indicators)} fields with real data)"
                elif len(present_fields) >= 4:
                    attestation_score = 70
                    details = f"Attestation structure complete but data may be mock ({len(real_data_indicators)} real fields)"
                else:
                    attestation_score = 30
                    details = f"Incomplete attestation data ({len(present_fields)} fields present)"
            else:
                attestation_score = 0
                details = f"Self-attestation failed: {attestation_response.status_code}"
            
            self.record_validation(
                'secretvm_features', 'real_self_attestation',
                attestation_working, attestation_score, details,
                critical=True  # Critical for SecretVM deployment
            )
            
        except Exception as e:
            self.record_validation(
                'secretvm_features', 'real_self_attestation',
                False, 0, f"Self-attestation test failed: {str(e)}",
                critical=True
            )
            attestation_score = 0
        
        # Test 2: SecretVM environment detection
        try:
            health_response = await self.client.get(f"{self.vm_url}:8000/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                services = health_data.get('services', {})
                self_attestation_service = services.get('self_attestation', {})
                
                environment_detected = self_attestation_service.get('available', False)
                environment_score = 100 if environment_detected else 50
                
                details = f"SecretVM environment detected: {environment_detected}"
            else:
                environment_score = 0
                details = "Health endpoint not accessible"
            
            self.record_validation(
                'secretvm_features', 'environment_detection',
                environment_detected if 'environment_detected' in locals() else False,
                environment_score, details,
                critical=False
            )
            
        except Exception as e:
            self.record_validation(
                'secretvm_features', 'environment_detection',
                False, 0, f"Environment detection failed: {str(e)}",
                critical=False
            )
            environment_score = 0
        
        return {
            'success': attestation_score > 50,  # Must have working attestation
            'attestation_score': attestation_score,
            'environment_score': environment_score if 'environment_score' in locals() else 0,
            **results
        }
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        
        # Calculate overall scores by category
        categories = {}
        for result in self.validation_results:
            category = result['category']
            if category not in categories:
                categories[category] = {'scores': [], 'passed': [], 'critical_failed': []}
            
            categories[category]['scores'].append(result['score'])
            categories[category]['passed'].append(result['passed'])
            
            if not result['passed'] and result['critical']:
                categories[category]['critical_failed'].append(result['test'])
        
        # Generate report
        report = f"""
╔═════════════════════════════════════════════════════════════════════
║ SecretVM Health Validation Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
║ Mode: {'STRICT' if self.strict_mode else 'STANDARD'}
╚═════════════════════════════════════════════════════════════════════
"""
        
        overall_scores = []
        critical_failures = []
        
        for category, data in categories.items():
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            passed_count = sum(data['passed'])
            total_count = len(data['passed'])
            
            overall_scores.append(avg_score)
            critical_failures.extend(data['critical_failed'])
            
            status_emoji = "✅" if avg_score >= 80 else ("⚠️" if avg_score >= 60 else "❌")
            
            report += f"\n{status_emoji} {category.upper().replace('_', ' ')}:\n"
            report += f"   Score: {avg_score:.1f}% | Passed: {passed_count}/{total_count} tests\n"
            
            if data['critical_failed']:
                report += f"   Critical Failures: {', '.join(data['critical_failed'])}\n"
        
        # Overall assessment
        overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        if critical_failures:
            overall_status = "❌ FAILED"
            status_reason = f"{len(critical_failures)} critical failures"
        elif overall_score >= 90:
            overall_status = "✅ EXCELLENT"
            status_reason = "All systems operating optimally"
        elif overall_score >= 80:
            overall_status = "✅ GOOD"
            status_reason = "System healthy with minor issues"
        elif overall_score >= 60:
            overall_status = "⚠️  WARNING"
            status_reason = "System functional but needs attention"
        else:
            overall_status = "❌ POOR"
            status_reason = "System has significant issues"
        
        report += f"\n🎯 OVERALL HEALTH: {overall_status}\n"
        report += f"   Overall Score: {overall_score:.1f}%\n"
        report += f"   Status: {status_reason}\n"
        
        if critical_failures:
            report += f"\n🚨 CRITICAL ISSUES TO ADDRESS:\n"
            for failure in critical_failures:
                report += f"   • {failure.replace('_', ' ').title()}\n"
        
        # Detailed test results
        report += f"\n📋 DETAILED TEST RESULTS:\n"
        for result in self.validation_results:
            status = "✅" if result['passed'] else ("❌" if result['critical'] else "⚠️")
            report += f"   {status} {result['category']}/{result['test']}: {result['score']:.1f}% - {result['details']}\n"
        
        report += f"\n" + "═" * 70
        
        return report
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary data"""
        categories = {}
        for result in self.validation_results:
            category = result['category']
            if category not in categories:
                categories[category] = {'scores': [], 'passed': [], 'critical_failed': 0}
            
            categories[category]['scores'].append(result['score'])
            categories[category]['passed'].append(result['passed'])
            
            if not result['passed'] and result['critical']:
                categories[category]['critical_failed'] += 1
        
        category_scores = {}
        for category, data in categories.items():
            category_scores[category] = {
                'average_score': sum(data['scores']) / len(data['scores']) if data['scores'] else 0,
                'passed_count': sum(data['passed']),
                'total_count': len(data['passed']),
                'critical_failures': data['critical_failed']
            }
        
        overall_score = sum(s['average_score'] for s in category_scores.values()) / len(category_scores) if category_scores else 0
        critical_failures = sum(s['critical_failures'] for s in category_scores.values())
        
        return {
            'overall_score': overall_score,
            'critical_failures': critical_failures,
            'category_scores': category_scores,
            'validation_passed': critical_failures == 0 and overall_score >= 70,
            'strict_mode': self.strict_mode,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete health validation"""
        logger.info("Starting comprehensive health validation...")
        
        # Step 1: Basic connectivity
        connectivity_result = await self.validate_basic_connectivity()
        if not connectivity_result['success']:
            logger.error("Basic connectivity failed - aborting validation")
            return {
                'success': False,
                'error': 'basic_connectivity_failed',
                'summary': self.get_validation_summary()
            }
        
        health_data = connectivity_result.get('response_data', {})
        
        # Step 2: Service availability
        await self.validate_service_availability(health_data)
        
        # Step 3: API endpoints
        await self.validate_api_endpoints()
        
        # Step 4: Core functionality
        await self.validate_core_functionality()
        
        # Step 5: SecretVM-specific features
        await self.validate_secretvm_specific_features()
        
        # Generate report
        report = self.generate_validation_report()
        print(report)
        
        # Return summary
        summary = self.get_validation_summary()
        
        return {
            'success': summary['validation_passed'],
            'summary': summary,
            'detailed_results': self.validation_results
        }


async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SecretVM Health Validator")
    parser.add_argument("--vm-url", help="SecretVM URL (or set SECRETVM_URL env var)")
    parser.add_argument("--strict", action="store_true", help="Enable strict validation mode")
    parser.add_argument("--save-results", help="Save validation results to JSON file")
    
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
    
    logger.info(f"Validating SecretVM deployment at: {vm_url}")
    if args.strict:
        logger.info("Running in STRICT mode - higher thresholds applied")
    
    async with HealthValidator(vm_url, strict_mode=args.strict) as validator:
        result = await validator.run_full_validation()
        
        if args.save_results:
            try:
                with open(args.save_results, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Results saved to {args.save_results}")
            except Exception as e:
                logger.error(f"Failed to save results: {e}")
        
        if result['success']:
            logger.info("🎉 VALIDATION PASSED - Deployment is healthy!")
            sys.exit(0)
        else:
            logger.error("❌ VALIDATION FAILED - Deployment needs attention")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())