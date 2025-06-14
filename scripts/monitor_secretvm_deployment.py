#!/usr/bin/env python3
"""
SecretVM Deployment Monitoring Script

Real-time monitoring system for attest_ai deployment health,
performance metrics, and service availability in SecretVM.
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


class SecretVMMonitor:
    """Real-time monitoring for attest_ai deployment in SecretVM"""
    
    def __init__(self, vm_url: str, monitor_interval: int = 60):
        self.vm_url = vm_url.rstrip('/')
        self.monitor_interval = monitor_interval
        self.client = httpx.AsyncClient(timeout=30.0)
        self.metrics_history = []
        self.alert_thresholds = {
            'response_time_ms': 5000,  # 5 seconds
            'error_rate_percent': 10,   # 10% error rate
            'consecutive_failures': 3,   # 3 failures in a row
            'memory_usage_percent': 90,  # 90% memory usage
            'cpu_usage_percent': 95,     # 95% CPU usage
        }
        self.consecutive_failures = 0
        self.last_successful_check = None
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def check_service_health(self) -> Dict[str, Any]:
        """Comprehensive service health check"""
        health_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'unknown',
            'services': {},
            'metrics': {},
            'alerts': []
        }
        
        try:
            start_time = time.time()
            
            # Main health endpoint
            health_response = await self.client.get(f"{self.vm_url}:8000/health")
            response_time = (time.time() - start_time) * 1000
            
            if health_response.status_code == 200:
                health_json = health_response.json()
                health_data['status'] = 'healthy'
                health_data['services'] = health_json.get('services', {})
                health_data['metrics']['response_time_ms'] = response_time
                
                # Check individual service statuses
                services = health_data['services']
                
                # Self-attestation status (critical)
                self_attestation = services.get('self_attestation', {})
                if not self_attestation.get('available', False):
                    health_data['alerts'].append({
                        'severity': 'critical',
                        'message': 'Self-attestation service unavailable',
                        'component': 'self_attestation'
                    })
                
                # Secret AI status (warning if unavailable)
                secret_ai = services.get('secret_ai', {})
                if not secret_ai.get('available', False):
                    health_data['alerts'].append({
                        'severity': 'warning',
                        'message': 'Secret AI service unavailable',
                        'component': 'secret_ai'
                    })
                
                # Arweave status (info if unavailable)
                arweave = services.get('arweave', {})
                if not arweave.get('available', False):
                    health_data['alerts'].append({
                        'severity': 'info',
                        'message': 'Arweave service unavailable or unfunded',
                        'component': 'arweave'
                    })
                
                # Performance alerts
                if response_time > self.alert_thresholds['response_time_ms']:
                    health_data['alerts'].append({
                        'severity': 'warning',
                        'message': f'High response time: {response_time:.0f}ms',
                        'component': 'performance'
                    })
                
                self.consecutive_failures = 0
                self.last_successful_check = datetime.utcnow()
                
            else:
                health_data['status'] = 'unhealthy'
                health_data['metrics']['response_time_ms'] = response_time
                health_data['alerts'].append({
                    'severity': 'critical',
                    'message': f'Health endpoint returned {health_response.status_code}',
                    'component': 'application'
                })
                self.consecutive_failures += 1
                
        except asyncio.TimeoutError:
            health_data['status'] = 'timeout'
            health_data['alerts'].append({
                'severity': 'critical',
                'message': 'Health check timed out',
                'component': 'network'
            })
            self.consecutive_failures += 1
            
        except Exception as e:
            health_data['status'] = 'error'
            health_data['alerts'].append({
                'severity': 'critical',
                'message': f'Health check failed: {str(e)}',
                'component': 'monitoring'
            })
            self.consecutive_failures += 1
        
        # Check for consecutive failure alert
        if self.consecutive_failures >= self.alert_thresholds['consecutive_failures']:
            health_data['alerts'].append({
                'severity': 'critical',
                'message': f'{self.consecutive_failures} consecutive health check failures',
                'component': 'availability'
            })
        
        return health_data
    
    async def check_api_endpoints(self) -> Dict[str, Any]:
        """Check availability of key API endpoints"""
        endpoints = [
            ('/api', 'API Root'),
            ('/api/attestation/self', 'Self Attestation'),
            ('/api/attestation/status', 'Attestation Status'),
            ('/api/secretai/health', 'Secret AI Health'),
            ('/api/arweave/status', 'Arweave Status'),
            ('/api/proofs/validation-schema', 'Proof Validation'),
        ]
        
        endpoint_results = {}
        
        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = await self.client.get(f"{self.vm_url}:8000{endpoint}")
                response_time = (time.time() - start_time) * 1000
                
                endpoint_results[endpoint] = {
                    'name': name,
                    'status': response.status_code,
                    'response_time_ms': response_time,
                    'available': response.status_code < 400,
                    'content_type': response.headers.get('content-type', ''),
                }
                
            except Exception as e:
                endpoint_results[endpoint] = {
                    'name': name,
                    'status': 0,
                    'response_time_ms': 0,
                    'available': False,
                    'error': str(e)
                }
        
        return endpoint_results
    
    async def test_core_functionality(self) -> Dict[str, Any]:
        """Test core application functionality"""
        functionality_tests = {}
        
        try:
            # Test chat functionality
            chat_payload = {
                "message": "Health check test message",
                "upload_proof": False  # Don't upload during monitoring
            }
            
            start_time = time.time()
            chat_response = await self.client.post(
                f"{self.vm_url}:8000/api/chat/",
                json=chat_payload
            )
            chat_time = (time.time() - start_time) * 1000
            
            functionality_tests['chat'] = {
                'available': chat_response.status_code == 200,
                'response_time_ms': chat_time,
                'status_code': chat_response.status_code
            }
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                functionality_tests['chat']['has_response'] = bool(chat_data.get('chat', {}).get('message'))
                functionality_tests['chat']['has_attestations'] = bool(chat_data.get('attestations', {}))
            
        except Exception as e:
            functionality_tests['chat'] = {
                'available': False,
                'error': str(e)
            }
        
        try:
            # Test proof verification
            schema_response = await self.client.get(f"{self.vm_url}:8000/api/proofs/validation-schema")
            
            functionality_tests['proof_verification'] = {
                'schema_available': schema_response.status_code == 200,
                'status_code': schema_response.status_code
            }
            
            if schema_response.status_code == 200:
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
                    
                    functionality_tests['proof_verification']['verification_working'] = verify_response.status_code == 200
                    functionality_tests['proof_verification']['verify_status_code'] = verify_response.status_code
            
        except Exception as e:
            functionality_tests['proof_verification'] = {
                'available': False,
                'error': str(e)
            }
        
        return functionality_tests
    
    async def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance and resource metrics"""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'response_times': {},
            'availability': {}
        }
        
        # Test multiple endpoints for performance
        test_endpoints = [
            '/health',
            '/api/attestation/status',
            '/api/secretai/health',
            '/api/arweave/status'
        ]
        
        response_times = []
        
        for endpoint in test_endpoints:
            try:
                start_time = time.time()
                response = await self.client.get(f"{self.vm_url}:8000{endpoint}")
                response_time = (time.time() - start_time) * 1000
                
                response_times.append(response_time)
                metrics['response_times'][endpoint] = response_time
                metrics['availability'][endpoint] = response.status_code < 400
                
            except Exception as e:
                metrics['response_times'][endpoint] = -1
                metrics['availability'][endpoint] = False
        
        # Calculate aggregate metrics
        if response_times:
            metrics['avg_response_time_ms'] = sum(response_times) / len(response_times)
            metrics['max_response_time_ms'] = max(response_times)
            metrics['min_response_time_ms'] = min(response_times)
        
        available_endpoints = sum(1 for available in metrics['availability'].values() if available)
        total_endpoints = len(metrics['availability'])
        metrics['availability_percent'] = (available_endpoints / total_endpoints) * 100 if total_endpoints > 0 else 0
        
        return metrics
    
    def generate_status_report(self, health_data: Dict[str, Any], 
                              endpoint_data: Dict[str, Any], 
                              functionality_data: Dict[str, Any],
                              performance_data: Dict[str, Any]) -> str:
        """Generate comprehensive status report"""
        
        # Status summary
        overall_status = health_data.get('status', 'unknown')
        status_emoji = {
            'healthy': '✅',
            'unhealthy': '❌',
            'timeout': '⏰',
            'error': '💥',
            'unknown': '❓'
        }.get(overall_status, '❓')
        
        report = f"""
╔═════════════════════════════════════════════════════════════════════
║ SecretVM Deployment Status Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
╚═════════════════════════════════════════════════════════════════════

🎯 OVERALL STATUS: {status_emoji} {overall_status.upper()}

📊 SERVICE HEALTH:
"""
        
        # Service status
        services = health_data.get('services', {})
        for service_name, service_data in services.items():
            status = '✅ Available' if service_data.get('available') else '❌ Unavailable'
            report += f"   • {service_name.replace('_', ' ').title()}: {status}\n"
        
        # Performance metrics
        response_time = health_data.get('metrics', {}).get('response_time_ms', 0)
        if response_time > 0:
            report += f"\n⚡ PERFORMANCE:\n"
            report += f"   • Health Check Response Time: {response_time:.0f}ms\n"
            
            avg_response = performance_data.get('avg_response_time_ms', 0)
            if avg_response > 0:
                report += f"   • Average API Response Time: {avg_response:.0f}ms\n"
            
            availability = performance_data.get('availability_percent', 0)
            report += f"   • API Endpoint Availability: {availability:.1f}%\n"
        
        # API endpoints status
        available_endpoints = sum(1 for ep in endpoint_data.values() if ep.get('available', False))
        total_endpoints = len(endpoint_data)
        report += f"\n🔗 API ENDPOINTS ({available_endpoints}/{total_endpoints} available):\n"
        
        for endpoint, data in endpoint_data.items():
            status = '✅' if data.get('available') else '❌'
            response_time = data.get('response_time_ms', 0)
            name = data.get('name', endpoint)
            if response_time > 0:
                report += f"   • {name}: {status} ({response_time:.0f}ms)\n"
            else:
                report += f"   • {name}: {status}\n"
        
        # Functionality tests
        report += f"\n🧪 FUNCTIONALITY TESTS:\n"
        
        chat_test = functionality_data.get('chat', {})
        if chat_test.get('available'):
            chat_status = '✅ Working'
            if chat_test.get('has_response') and chat_test.get('has_attestations'):
                chat_status += ' (Full Workflow)'
        else:
            chat_status = '❌ Failed'
        report += f"   • Chat System: {chat_status}\n"
        
        proof_test = functionality_data.get('proof_verification', {})
        if proof_test.get('verification_working'):
            proof_status = '✅ Working'
        elif proof_test.get('schema_available'):
            proof_status = '⚠️  Schema Available (Verification Untested)'
        else:
            proof_status = '❌ Failed'
        report += f"   • Proof Verification: {proof_status}\n"
        
        # Alerts
        alerts = health_data.get('alerts', [])
        if alerts:
            report += f"\n🚨 ALERTS ({len(alerts)}):\n"
            for alert in alerts:
                severity_emoji = {
                    'critical': '🔴',
                    'warning': '🟡',
                    'info': '🔵'
                }.get(alert.get('severity'), '⚪')
                
                report += f"   • {severity_emoji} {alert.get('message')} ({alert.get('component')})\n"
        else:
            report += f"\n✅ NO ACTIVE ALERTS\n"
        
        # System info
        if self.last_successful_check:
            time_since_success = datetime.utcnow() - self.last_successful_check
            report += f"\n📈 MONITORING INFO:\n"
            report += f"   • Last Successful Check: {time_since_success.total_seconds():.0f} seconds ago\n"
            report += f"   • Consecutive Failures: {self.consecutive_failures}\n"
            report += f"   • Monitor Interval: {self.monitor_interval} seconds\n"
        
        report += f"\n" + "═" * 70
        
        return report
    
    async def run_single_check(self) -> Dict[str, Any]:
        """Run a single comprehensive monitoring check"""
        logger.info("Running comprehensive health check...")
        
        # Collect all monitoring data
        health_data = await self.check_service_health()
        endpoint_data = await self.check_api_endpoints()
        functionality_data = await self.test_core_functionality()
        performance_data = await self.collect_performance_metrics()
        
        # Combine into single report
        monitoring_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'health': health_data,
            'endpoints': endpoint_data,
            'functionality': functionality_data,
            'performance': performance_data
        }
        
        # Generate and print report
        report = self.generate_status_report(health_data, endpoint_data, functionality_data, performance_data)
        print(report)
        
        # Store metrics history
        self.metrics_history.append(monitoring_data)
        
        # Keep only last 100 entries
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        return monitoring_data
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring with specified interval"""
        logger.info(f"Starting continuous monitoring (interval: {self.monitor_interval}s)")
        logger.info(f"Monitoring URL: {self.vm_url}")
        
        try:
            while True:
                await self.run_single_check()
                logger.info(f"Next check in {self.monitor_interval} seconds...")
                await asyncio.sleep(self.monitor_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring failed: {e}")
            raise
    
    def save_metrics_history(self, output_file: str):
        """Save metrics history to JSON file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
            logger.info(f"Metrics history saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


async def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SecretVM Deployment Monitor")
    parser.add_argument("--vm-url", help="SecretVM URL (or set SECRETVM_URL env var)")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds (default: 60)")
    parser.add_argument("--single-check", action="store_true", help="Run single check instead of continuous monitoring")
    parser.add_argument("--save-metrics", help="Save metrics history to file (JSON)")
    
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
    
    logger.info(f"Monitoring SecretVM deployment at: {vm_url}")
    
    async with SecretVMMonitor(vm_url, args.interval) as monitor:
        if args.single_check:
            # Single check mode
            await monitor.run_single_check()
        else:
            # Continuous monitoring mode
            try:
                await monitor.run_continuous_monitoring()
            finally:
                if args.save_metrics:
                    monitor.save_metrics_history(args.save_metrics)


if __name__ == "__main__":
    asyncio.run(main())