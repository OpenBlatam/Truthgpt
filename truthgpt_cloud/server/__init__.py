"""
🚀 TruthGPT Cloud Server - Modular Enterprise FastAPI Application
Provides factory methods, lifecycle handlers, exception handlers, and modular sub-routers.
"""

from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import *
from .dependencies import resolve_user, require_tier, verify_api_key_or_token
from .routers import (
    billing_router,
    inference_router,
    verification_router,
    swarm_router,
    cache_router,
    papers_router,
    telemetry_router,
)
from ..core.config import CloudPlatformConfig
from ..core.exceptions import (
    QuotaExceededError,
    RateLimitExceededError,
    TierUnauthorizedError,
    VerificationError,
)


def create_app(config: Optional[CloudPlatformConfig] = None) -> FastAPI:
    """
    Application factory for TruthGPT Cloud FastAPI platform.
    Assembles global exception handlers, CORS, and modular domain sub-routers.
    """
    cfg = config or CloudPlatformConfig()

    app_instance = FastAPI(
        title="TruthGPT Cloud Platform API",
        version=cfg.api_version,
        description="Frontier Cloud Platform with Z3 SMT Formal Verification, Multi-Agent Swarm, Streaming SSE, and Tiered Subscriptions."
    )

    # -----------------------------------------------------------------------
    # 🌐 CORS Middleware
    # -----------------------------------------------------------------------
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # 🛡️ Global Exception Handlers
    # -----------------------------------------------------------------------
    @app_instance.exception_handler(QuotaExceededError)
    async def quota_exceeded_handler(request: Request, exc: QuotaExceededError):
        return JSONResponse(
            status_code=402,
            content={
                "success": False,
                "error": "QUOTA_EXCEEDED",
                "detail": exc.message,
                "consumed": getattr(exc, "consumed", 0),
                "limit": getattr(exc, "limit", 0),
            }
        )

    @app_instance.exception_handler(RateLimitExceededError)
    async def rate_limit_handler(request: Request, exc: RateLimitExceededError):
        retry_after = getattr(exc, "retry_after_seconds", 60.0)
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "RATE_LIMIT_EXCEEDED",
                "detail": exc.message,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(int(retry_after))}
        )

    @app_instance.exception_handler(TierUnauthorizedError)
    async def tier_unauthorized_handler(request: Request, exc: TierUnauthorizedError):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "TIER_UNAUTHORIZED",
                "detail": exc.message,
                "required_tier": getattr(exc, "required_tier", "pro"),
            }
        )

    # -----------------------------------------------------------------------
    # 🔌 Mount Sub-Routers
    # -----------------------------------------------------------------------
    app_instance.include_router(telemetry_router)
    app_instance.include_router(billing_router)
    app_instance.include_router(inference_router)
    app_instance.include_router(verification_router)
    app_instance.include_router(swarm_router)
    app_instance.include_router(cache_router)
    app_instance.include_router(papers_router)

    return app_instance


# Default global application instance
app = create_app()

__all__ = [
    "create_app",
    "app",
    "resolve_user",
    "require_tier",
    "verify_api_key_or_token",
    "billing_router",
    "inference_router",
    "verification_router",
    "swarm_router",
    "cache_router",
    "papers_router",
    "telemetry_router",
]
