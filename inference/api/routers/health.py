import time
import os
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse
from ..dependencies import state

router = APIRouter()
ENABLE_METRICS = os.environ.get("ENABLE_METRICS", "true").lower() == "true"

@router.get("/health")
async def health():
    """Health check endpoint"""
    model_loaded = state.model is not None
    batch_processor_running = state.batch_processor.running if state.batch_processor else False
    
    health_status = {
        "status": "healthy" if model_loaded and batch_processor_running else "degraded",
        "timestamp": int(time.time()),
        "checks": {
            "model": "loaded" if model_loaded else "not_loaded",
            "batch_processor": "running" if batch_processor_running else "stopped"
        }
    }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@router.get("/ready")
async def ready():
    """Readiness check"""
    if state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}

from ...middleware.telemetry import get_metrics_text

@router.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    if not ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    metrics_text = get_metrics_text()
    return Response(content=metrics_text, media_type="text/plain")
