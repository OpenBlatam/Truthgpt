"""
🚀 TruthGPT Cloud - Production FastAPI Server Entrypoint
Refactored to modular architecture: imports and delegates to the canonical truthgpt_cloud.server subpackage.
Maintains 100% backward compatibility for all existing imports and test suites.
"""

import sys
from pathlib import Path

# Ensure paths
_current = Path(__file__).resolve().parent
if str(_current) not in sys.path:
    sys.path.insert(0, str(_current))

__test__ = False

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

# Canonical imports from truthgpt_cloud.server
from truthgpt_cloud.server import (
    app,
    create_app,
    resolve_user,
    require_tier,
    verify_api_key_or_token,
    billing_router,
    inference_router,
    verification_router,
    swarm_router,
    cache_router,
    papers_router,
    telemetry_router,
)
from truthgpt_cloud.server.models import (
    UserAuthRequest,
    UpgradeRequest,
    ChatCompletionRequest,
    BatchChatRequest,
    OpenAIChatMessage,
    OpenAIChatRequest,
    FormalVerifyRequest,
    BatchFormalVerifyRequest,
    ExportProofRequest,
    VerifyContractRequest,
    VerifyCertificateRequest,
    SwarmExecuteRequest,
    WebhookRegisterRequest,
    WebhookTestTriggerRequest,
    WebhookVerifyRequest,
    ApplyPaperRequest,
    IssueTokenRequest,
    RegisterAlertRuleRequest,
    TensorShapesVerifyRequest,
    NumericalStabilityVerifyRequest,
    AttentionInvariantsVerifyRequest,
    QuantizationSafetyVerifyRequest,
    OptimizerConvergenceVerifyRequest,
    MerkleExclusionRequest,
    SwarmDebateRequest,
    DifferentialPrivacyVerifyRequest,
    ExportSmt2Request,
    RawSmt2Request,
    ApplyPromoRequest,
    MatrixVerifyRequest,
    ODEVerifyRequest,
    LoopVerifyRequest,
    CodePurityVerifyRequest,
    SynthesizeTheoremRequest,
    SpectralNormVerifyRequest,
    LipschitzVerifyRequest,
    MOEVerifyRequest,
    ROPEVerifyRequest,
    FlashAttentionVerifyRequest,
    MicroscalingFP8VerifyRequest,
)

from truthgpt_cloud import (
    CloudTier,
    get_all_tiers,
    get_tier_config,
    subscription_manager,
    cloud_router,
    cloud_verifier,
    cloud_swarm,
    cloud_telemetry,
    proof_cache,
    token_bucket_limiter,
    get_all_papers,
    cloud_paper_compiler,
    webhook_manager,
    TruthGPTCloudClient,
    format_prometheus_metrics,
    create_session_jwt,
    verify_session_jwt,
    get_system_metrics,
    cloud_health_checker,
    cloud_secrets,
)


def start_server(host: str = "0.0.0.0", port: int = 8080):
    """Run TruthGPT Cloud FastAPI Server with Executive Dashboard and Payment Gateway."""
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    print("=" * 72)
    print(f">> [TruthGPT Cloud] Server starting on http://localhost:{port}")
    print(f">> [Dashboard] Panel Ejecutivo de Cobros y Churn: http://localhost:{port}/dashboard")
    print(f">> [API Docs] Swagger / OpenAPI: http://localhost:{port}/docs")
    print("=" * 72)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server(port=8080)


__all__ = [
    "app",
    "create_app",
    "resolve_user",
    "require_tier",
    "verify_api_key_or_token",
    "start_server",
    "billing_router",
    "inference_router",
    "verification_router",
    "swarm_router",
    "cache_router",
    "papers_router",
    "telemetry_router",
    "UserAuthRequest",
    "UpgradeRequest",
    "ChatCompletionRequest",
    "BatchChatRequest",
    "OpenAIChatMessage",
    "OpenAIChatRequest",
    "FormalVerifyRequest",
    "BatchFormalVerifyRequest",
    "ExportProofRequest",
    "VerifyContractRequest",
    "VerifyCertificateRequest",
    "SwarmExecuteRequest",
    "WebhookRegisterRequest",
    "WebhookTestTriggerRequest",
    "WebhookVerifyRequest",
    "ApplyPaperRequest",
    "IssueTokenRequest",
    "RegisterAlertRuleRequest",
    "TensorShapesVerifyRequest",
    "NumericalStabilityVerifyRequest",
    "AttentionInvariantsVerifyRequest",
    "QuantizationSafetyVerifyRequest",
    "OptimizerConvergenceVerifyRequest",
    "MerkleExclusionRequest",
    "SwarmDebateRequest",
    "DifferentialPrivacyVerifyRequest",
    "ExportSmt2Request",
    "RawSmt2Request",
    "ApplyPromoRequest",
    "MatrixVerifyRequest",
    "ODEVerifyRequest",
    "LoopVerifyRequest",
    "CodePurityVerifyRequest",
    "SynthesizeTheoremRequest",
    "SpectralNormVerifyRequest",
    "LipschitzVerifyRequest",
    "MOEVerifyRequest",
    "ROPEVerifyRequest",
    "FlashAttentionVerifyRequest",
    "MicroscalingFP8VerifyRequest",
    "CloudTier",
    "get_all_tiers",
    "get_tier_config",
    "subscription_manager",
    "cloud_router",
    "cloud_verifier",
    "cloud_swarm",
    "cloud_telemetry",
    "proof_cache",
    "token_bucket_limiter",
    "get_all_papers",
    "cloud_paper_compiler",
    "webhook_manager",
    "TruthGPTCloudClient",
    "format_prometheus_metrics",
    "create_session_jwt",
    "verify_session_jwt",
    "get_system_metrics",
    "cloud_health_checker",
    "cloud_secrets",
]
