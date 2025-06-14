"""
Environment Detection and Optimization Utilities

Provides comprehensive environment detection, optimization,
and monitoring capabilities for SecretVM deployments.
"""

import asyncio
import logging
import os
import platform
import psutil
import resource
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import httpx

logger = logging.getLogger(__name__)


class EnvironmentDetector:
    """Comprehensive environment detection and optimization"""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = httpx.AsyncClient(timeout=10.0)
        self._detection_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached detection result is still valid"""
        if cache_key not in self._detection_cache:
            return False
        
        cached_time = self._detection_cache[cache_key].get('timestamp', 0)
        return (time.time() - cached_time) < self._cache_ttl
    
    async def detect_secretvm_environment(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Comprehensive SecretVM environment detection"""
        cache_key = 'secretvm_detection'
        
        if not force_refresh and self._is_cache_valid(cache_key):
            return self._detection_cache[cache_key]['data']
        
        detection_result = {
            'is_secretvm': False,
            'confidence_score': 0.0,
            'indicators': {},
            'detected_features': [],
            'timestamp': time.time()
        }
        
        # Test 1: Self-attestation endpoint availability
        attestation_score = await self._test_attestation_endpoint()
        detection_result['indicators']['attestation_endpoint'] = attestation_score
        if attestation_score > 0.7:
            detection_result['detected_features'].append('attestation_endpoint')
        
        # Test 2: Environment variables
        env_score = self._test_environment_variables()
        detection_result['indicators']['environment_variables'] = env_score
        if env_score > 0.5:
            detection_result['detected_features'].append('secretvm_env_vars')
        
        # Test 3: Container environment
        container_score = self._test_container_environment()
        detection_result['indicators']['container_environment'] = container_score
        if container_score > 0.5:
            detection_result['detected_features'].append('container_environment')
        
        # Test 4: Network characteristics
        network_score = await self._test_network_characteristics()
        detection_result['indicators']['network_characteristics'] = network_score
        if network_score > 0.3:
            detection_result['detected_features'].append('network_characteristics')
        
        # Test 5: System characteristics
        system_score = self._test_system_characteristics()
        detection_result['indicators']['system_characteristics'] = system_score
        if system_score > 0.3:
            detection_result['detected_features'].append('system_characteristics')
        
        # Calculate overall confidence
        weights = {
            'attestation_endpoint': 0.4,  # Most important
            'environment_variables': 0.25,
            'container_environment': 0.15,
            'network_characteristics': 0.1,
            'system_characteristics': 0.1
        }
        
        confidence_score = sum(
            detection_result['indicators'][key] * weights[key]
            for key in weights.keys()
        )
        
        detection_result['confidence_score'] = confidence_score
        detection_result['is_secretvm'] = confidence_score > 0.6
        
        # Cache result
        self._detection_cache[cache_key] = {
            'data': detection_result,
            'timestamp': time.time()
        }
        
        return detection_result
    
    async def _test_attestation_endpoint(self) -> float:
        """Test self-attestation endpoint for SecretVM indicators"""
        try:
            response = await self.client.get(self.settings.SELF_ATTESTATION_URL)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for SecretVM-specific attestation fields
                secretvm_indicators = [
                    'mr_td', 'rtmr0', 'rtmr1', 'rtmr2', 'rtmr3',
                    'report_data', 'attestation', 'measurement'
                ]
                
                found_indicators = sum(1 for indicator in secretvm_indicators if indicator in content)
                score = min(1.0, found_indicators / len(secretvm_indicators))
                
                # Additional checks for real vs mock data
                if any(real_indicator in content for real_indicator in ['0x', 'sha256', 'base64']):
                    score = min(1.0, score + 0.3)
                
                return score
            else:
                return 0.0
                
        except Exception as e:
            logger.debug(f"Attestation endpoint test failed: {e}")
            return 0.0
    
    def _test_environment_variables(self) -> float:
        """Test for SecretVM-specific environment variables"""
        secretvm_env_vars = [
            'SECRETVM_INSTANCE_ID',
            'SECRETVM_DEPLOYMENT',
            'SECRET_NETWORK_CHAIN_ID',
            'SCRT_ENCLAVE_DIR',
        ]
        
        production_indicators = [
            'DEPLOYMENT_ENVIRONMENT',
            'APP_DEBUG',
        ]
        
        score = 0.0
        
        # Check for explicit SecretVM variables
        found_secretvm_vars = sum(1 for var in secretvm_env_vars if os.environ.get(var))
        if found_secretvm_vars > 0:
            score += 0.8
        
        # Check for production environment indicators
        if os.environ.get('DEPLOYMENT_ENVIRONMENT') == 'production':
            score += 0.3
        
        if os.environ.get('APP_DEBUG', '').lower() in ['false', '0', '']:
            score += 0.2
        
        return min(1.0, score)
    
    def _test_container_environment(self) -> float:
        """Test container environment characteristics"""
        score = 0.0
        
        # Check for Docker environment
        if os.path.exists('/.dockerenv'):
            score += 0.5
        
        # Check for container-specific mount points
        container_mounts = ['/proc/1/cgroup', '/sys/fs/cgroup']
        for mount in container_mounts:
            try:
                if os.path.exists(mount):
                    with open(mount, 'r') as f:
                        content = f.read()
                        if 'docker' in content or 'container' in content:
                            score += 0.2
                            break
            except:
                pass
        
        # Check process tree (PID 1 should be init or container entry point)
        try:
            with open('/proc/1/comm', 'r') as f:
                pid1_process = f.read().strip()
                if pid1_process in ['python', 'uvicorn', 'gunicorn', 'hypercorn']:
                    score += 0.3
        except:
            pass
        
        return min(1.0, score)
    
    async def _test_network_characteristics(self) -> float:
        """Test network characteristics typical of SecretVM"""
        score = 0.0
        
        try:
            # Test for restricted network access (common in secure environments)
            test_urls = [
                'https://api.github.com',
                'https://registry.npmjs.org',
                'https://pypi.org'
            ]
            
            accessible_count = 0
            for url in test_urls:
                try:
                    response = await self.client.get(url, timeout=3)
                    if response.status_code < 400:
                        accessible_count += 1
                except:
                    pass
            
            # Limited external access might indicate secure environment
            if accessible_count < len(test_urls):
                score += 0.3
            
            # Test for localhost services (common in SecretVM)
            localhost_services = [
                f'http://localhost:{port}' for port in [26657, 1317, 9090, 9091]
            ]
            
            for service_url in localhost_services:
                try:
                    response = await self.client.get(service_url, timeout=1)
                    if response.status_code < 500:  # Any response indicates service
                        score += 0.1
                        break
                except:
                    pass
            
        except Exception as e:
            logger.debug(f"Network characteristics test failed: {e}")
        
        return min(1.0, score)
    
    def _test_system_characteristics(self) -> float:
        """Test system characteristics"""
        score = 0.0
        
        try:
            # Check platform information
            platform_info = platform.platform().lower()
            
            # Linux is common for SecretVM deployments
            if 'linux' in platform_info:
                score += 0.2
            
            # Check for virtualization indicators
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpu_info = f.read().lower()
                    if any(virt in cpu_info for virt in ['hypervisor', 'vmware', 'kvm', 'xen']):
                        score += 0.3
            except:
                pass
            
            # Check memory constraints (SecretVM instances often have limited memory)
            try:
                memory_gb = psutil.virtual_memory().total / (1024**3)
                if 0.5 <= memory_gb <= 8:  # Typical SecretVM memory range
                    score += 0.2
            except:
                pass
            
        except Exception as e:
            logger.debug(f"System characteristics test failed: {e}")
        
        return min(1.0, score)
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get process-specific resources
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'memory': {
                    'total_mb': memory.total / (1024**2),
                    'available_mb': memory.available / (1024**2),
                    'used_mb': memory.used / (1024**2),
                    'percent': memory.percent
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                'process': {
                    'memory_mb': process_memory.rss / (1024**2),
                    'memory_percent': process.memory_percent(),
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads(),
                    'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None
                },
                'disk': {
                    'usage': psutil.disk_usage('/'),
                    'io': psutil.disk_io_counters()
                } if hasattr(psutil, 'disk_usage') else {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            return {'error': str(e)}
    
    def check_resource_constraints(self) -> Dict[str, Any]:
        """Check if system is within configured resource constraints"""
        resources = self.get_system_resources()
        
        if 'error' in resources:
            return {'status': 'error', 'details': resources['error']}
        
        warnings = []
        errors = []
        
        # Check memory constraints
        memory_percent = resources.get('memory', {}).get('percent', 0)
        if memory_percent > 95:
            errors.append(f"Critical memory usage: {memory_percent:.1f}%")
        elif memory_percent > 85:
            warnings.append(f"High memory usage: {memory_percent:.1f}%")
        
        # Check CPU constraints
        cpu_percent = resources.get('cpu', {}).get('percent', 0)
        if cpu_percent > self.settings.MAX_CPU_PERCENT:
            errors.append(f"CPU usage exceeds limit: {cpu_percent:.1f}% > {self.settings.MAX_CPU_PERCENT}%")
        elif cpu_percent > (self.settings.MAX_CPU_PERCENT * 0.8):
            warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        # Check available memory
        available_mb = resources.get('memory', {}).get('available_mb', 0)
        if available_mb < 100:
            errors.append(f"Low available memory: {available_mb:.1f}MB")
        elif available_mb < 500:
            warnings.append(f"Limited available memory: {available_mb:.1f}MB")
        
        return {
            'status': 'error' if errors else ('warning' if warnings else 'ok'),
            'errors': errors,
            'warnings': warnings,
            'resource_usage': resources
        }
    
    async def get_comprehensive_environment_report(self) -> Dict[str, Any]:
        """Get comprehensive environment analysis report"""
        
        # Gather all environment data
        secretvm_detection = await self.detect_secretvm_environment()
        system_resources = self.get_system_resources()
        resource_constraints = self.check_resource_constraints()
        environment_info = self.settings.get_environment_info()
        optimized_settings = self.settings.get_optimized_settings()
        
        # Performance recommendations
        recommendations = []
        
        if secretvm_detection['is_secretvm']:
            if secretvm_detection['confidence_score'] > 0.8:
                recommendations.append("High-confidence SecretVM environment detected - using optimized settings")
            else:
                recommendations.append("SecretVM environment detected with medium confidence - verify deployment")
            
            # SecretVM-specific recommendations
            if system_resources.get('memory', {}).get('total_mb', 0) < 2048:
                recommendations.append("Consider reducing cache TTL for memory-constrained environment")
            
            recommendations.append("Enable real attestation data capture")
            recommendations.append("Use shorter health check intervals for production monitoring")
            
        else:
            recommendations.append("Development environment detected - using relaxed settings")
            recommendations.append("Consider enabling mock services for unreliable external dependencies")
        
        # Resource-based recommendations
        if resource_constraints['status'] != 'ok':
            if resource_constraints.get('errors'):
                recommendations.extend([f"CRITICAL: {error}" for error in resource_constraints['errors']])
            if resource_constraints.get('warnings'):
                recommendations.extend([f"WARNING: {warning}" for warning in resource_constraints['warnings']])
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'environment_detection': {
                'secretvm': secretvm_detection,
                'system_info': environment_info,
            },
            'resource_analysis': {
                'current_usage': system_resources,
                'constraint_check': resource_constraints,
            },
            'optimization': {
                'recommended_settings': optimized_settings,
                'recommendations': recommendations,
            },
            'summary': {
                'environment_type': 'SecretVM' if secretvm_detection['is_secretvm'] else 'Development',
                'confidence_score': secretvm_detection['confidence_score'],
                'resource_status': resource_constraints['status'],
                'detected_features': secretvm_detection['detected_features'],
                'optimization_applied': optimized_settings.get('optimized_for', 'none')
            }
        }