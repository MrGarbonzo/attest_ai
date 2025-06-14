"""
Environment API endpoints

Provides detailed environment detection, resource monitoring,
and optimization information for SecretVM deployments.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class EnvironmentInfo(BaseModel):
    """Environment information response model"""
    environment_type: str
    is_secretvm: bool
    confidence_score: float
    detected_features: list
    resource_status: str
    optimization_applied: str


class ResourceUsage(BaseModel):
    """Resource usage response model"""
    memory_percent: float
    cpu_percent: float
    available_memory_mb: float
    process_memory_mb: float
    status: str
    warnings: list
    errors: list


@router.get("/info", response_model=EnvironmentInfo)
async def get_environment_info(request: Request):
    """Get comprehensive environment detection information"""
    try:
        if not hasattr(request.app.state, 'environment_report'):
            raise HTTPException(status_code=503, detail="Environment detection not available")
        
        env_report = request.app.state.environment_report
        summary = env_report.get('summary', {})
        
        return EnvironmentInfo(
            environment_type=summary.get('environment_type', 'unknown'),
            is_secretvm=summary.get('environment_type') == 'SecretVM',
            confidence_score=summary.get('confidence_score', 0.0),
            detected_features=summary.get('detected_features', []),
            resource_status=summary.get('resource_status', 'unknown'),
            optimization_applied=summary.get('optimization_applied', 'none')
        )
        
    except Exception as e:
        logger.error(f"Failed to get environment info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_environment_report(request: Request):
    """Get detailed environment analysis report"""
    try:
        if not hasattr(request.app.state, 'environment_report'):
            raise HTTPException(status_code=503, detail="Environment detection not available")
        
        return request.app.state.environment_report
        
    except Exception as e:
        logger.error(f"Failed to get environment report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources", response_model=ResourceUsage)
async def get_resource_usage():
    """Get current system resource usage"""
    try:
        from ..utils.environment import EnvironmentDetector
        from ..config import get_settings
        
        settings = get_settings()
        
        async with EnvironmentDetector(settings) as detector:
            resources = detector.get_system_resources()
            constraints = detector.check_resource_constraints()
            
            if 'error' in resources:
                raise HTTPException(status_code=500, detail=resources['error'])
            
            return ResourceUsage(
                memory_percent=resources.get('memory', {}).get('percent', 0),
                cpu_percent=resources.get('cpu', {}).get('percent', 0),
                available_memory_mb=resources.get('memory', {}).get('available_mb', 0),
                process_memory_mb=resources.get('process', {}).get('memory_mb', 0),
                status=constraints.get('status', 'unknown'),
                warnings=constraints.get('warnings', []),
                errors=constraints.get('errors', [])
            )
            
    except Exception as e:
        logger.error(f"Failed to get resource usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimization")
async def get_optimization_settings(request: Request):
    """Get current optimization settings applied to the deployment"""
    try:
        if not hasattr(request.app.state, 'optimized_settings'):
            raise HTTPException(status_code=503, detail="Optimization settings not available")
        
        return request.app.state.optimized_settings
        
    except Exception as e:
        logger.error(f"Failed to get optimization settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_environment_detection(request: Request):
    """Refresh environment detection and optimization settings"""
    try:
        from ..utils.environment import EnvironmentDetector
        from ..config import get_settings
        
        settings = get_settings()
        
        async with EnvironmentDetector(settings) as detector:
            # Force refresh of environment detection
            env_report = await detector.get_comprehensive_environment_report()
            
            # Update app state
            request.app.state.environment_report = env_report
            request.app.state.optimized_settings = env_report['optimization']['recommended_settings']
            
            return {
                "status": "refreshed",
                "environment_type": env_report['summary']['environment_type'],
                "confidence_score": env_report['summary']['confidence_score'],
                "optimization_applied": env_report['summary']['optimization_applied'],
                "timestamp": env_report['timestamp']
            }
            
    except Exception as e:
        logger.error(f"Failed to refresh environment detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/secretvm/detection")
async def get_secretvm_detection_details():
    """Get detailed SecretVM environment detection results"""
    try:
        from ..utils.environment import EnvironmentDetector
        from ..config import get_settings
        
        settings = get_settings()
        
        async with EnvironmentDetector(settings) as detector:
            secretvm_detection = await detector.detect_secretvm_environment(force_refresh=True)
            return secretvm_detection
            
    except Exception as e:
        logger.error(f"Failed to get SecretVM detection details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/detailed")
async def get_detailed_health():
    """Get detailed health information including environment and resources"""
    try:
        from ..utils.environment import EnvironmentDetector
        from ..config import get_settings
        
        settings = get_settings()
        
        async with EnvironmentDetector(settings) as detector:
            resources = detector.get_system_resources()
            constraints = detector.check_resource_constraints()
            secretvm_detection = await detector.detect_secretvm_environment()
            
            return {
                "timestamp": resources.get('timestamp'),
                "environment": {
                    "is_secretvm": secretvm_detection['is_secretvm'],
                    "confidence_score": secretvm_detection['confidence_score'],
                    "detected_features": secretvm_detection['detected_features']
                },
                "resources": resources,
                "constraints": constraints,
                "overall_status": "healthy" if constraints['status'] == 'ok' else constraints['status']
            }
            
    except Exception as e:
        logger.error(f"Failed to get detailed health: {e}")
        raise HTTPException(status_code=500, detail=str(e))