"""
🚀 Modular Production-Ready Inference API
Enterprise-grade FastAPI server with batching, streaming, observability, and resilience.
"""

import os
import time
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api.dependencies import state
from .api.routers import health, inference, webhooks
from ..configs.loader import load_config
from .core.engine_factory import create_inference_engine, EngineType
from .middleware.cache_manager import CacheManager
from .middleware.rate_limiter import rate_limiter
from .batch.advanced_batcher import ContinuousBatcher

# Configuration
CONFIG_PATH = os.environ.get(
    "TRUTHGPT_CONFIG",
    os.path.join(os.path.dirname(__file__), "..", "configs", "llm_default.yaml"),
)
BATCH_MAX_SIZE = int(os.environ.get("BATCH_MAX_SIZE", "32"))
BATCH_FLUSH_TIMEOUT_MS = int(os.environ.get("BATCH_FLUSH_TIMEOUT_MS", "20"))
RATE_LIMIT_RPM = int(os.environ.get("RATE_LIMIT_RPM", "600"))
ENABLE_METRICS = os.environ.get("ENABLE_METRICS", "true").lower() == "true"
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

async def metrics_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "unknown")
    start_time = time.time()
    
    response = await call_next(request)
    
    latency_ms = (time.time() - start_time) * 1000
    state.metrics["requests_total"] += 1
    state.metrics["request_duration_ms"] += latency_ms
    
    if response.status_code >= 500:
        state.metrics["errors_5xx"] += 1
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{latency_ms:.2f}"
    
    return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Modular Inference API...")
    
    state.cache = CacheManager(max_memory_size=1000, use_disk_cache=False)
    rate_limiter.configure_endpoint("default", requests_per_minute=RATE_LIMIT_RPM)
    
    print(f"📦 Loading model from {CONFIG_PATH}...")
    cfg = load_config(CONFIG_PATH, overrides=None)
    model_id = getattr(cfg.model, "path", None) or cfg.model.family
    state.model = create_inference_engine(model=model_id, engine_type=EngineType.AUTO)
    print("✅ Model loaded successfully")
    
    def process_batch_fn(items):
        if not items:
            return []
        prompts = [i.get("prompt") for i in items]
        params = items[0].get("params", {})
        results = state.model.generate(prompts, **params)
        return results if isinstance(results, list) else [results]
    
    state.batch_processor = ContinuousBatcher(
        processor=process_batch_fn,
        max_batch_size=BATCH_MAX_SIZE,
        max_wait_time=BATCH_FLUSH_TIMEOUT_MS / 1000.0
    )
    state.batch_processor.start()
    print("✅ Batch processor started")
    
    yield
    print("🛑 Shutting down...")

app = FastAPI(
    title="Frontier-Model-Run Modular Inference API",
    description="Enterprise-grade inference API with batching, streaming, and observability",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if ENABLE_METRICS:
    app.middleware("http")(metrics_middleware)

# Include routers
app.include_router(health.router)
app.include_router(inference.router)
app.include_router(webhooks.router)

if __name__ == "__main__":
    uvicorn.run(
        "optimization_core.inference.api:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        reload=os.environ.get("ENVIRONMENT", "production") == "development"
    )
