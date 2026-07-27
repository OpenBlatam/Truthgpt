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

@router.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint"""
    if not ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    total_requests = state.metrics.get("requests_total", 0)
    total_duration = state.metrics.get("request_duration_ms", 0)
    avg_duration = total_duration / total_requests if total_requests > 0 else 0
    
    metrics_text = f\"\"\"# HELP inference_requests_total Total number of inference requests
# TYPE inference_requests_total counter
inference_requests_total {total_requests}

# HELP inference_request_duration_ms Average request duration in milliseconds
# TYPE inference_request_duration_ms gauge
inference_request_duration_ms {avg_duration:.2f}

# HELP inference_errors_5xx_total Total number of 5xx errors
# TYPE inference_errors_5xx_total counter
inference_errors_5xx_total {state.metrics.get("errors_5xx", 0)}

# HELP inference_cache_hits_total Total number of cache hits
# TYPE inference_cache_hits_total counter
inference_cache_hits_total {state.metrics.get("cache_hits", 0)}
\"\"\"
    
    return Response(content=metrics_text, media_type="text/plain")
