"""
🌐 TruthGPT Cloud - Central Dependency Injection & Platform Context
Provides unified encapsulation of cloud subsystems (billing, verification, swarm,
routing, telemetry, caching, security, webhooks, papers), enabling global singleton access
and fully isolated test/multi-tenant instances.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..billing.subscription import SubscriptionManager
    from ..billing.webhooks import WebhookManager
    from ..verification.verifier import CloudFormalVerifier
    from ..swarm.orchestrator import CloudSwarmOrchestrator
    from ..routing.router import CloudIntelligenceRouter
    from ..telemetry.collector import CloudTelemetryCollector
    from ..cache.proof_cache import CloudProofCache
    from ..security.manager import CloudSecurityManager
    from ..papers.compiler import CloudPaperCompiler
    from ..storage.base import StorageBackend


@dataclass
class TruthGPTCloudContext:
    """
    Encapsulates all active TruthGPT Cloud subsystems.
    Facilitates dependency injection, lifecycle control, and isolated testing.
    """
    subscription_manager: SubscriptionManager
    verifier: CloudFormalVerifier
    swarm: CloudSwarmOrchestrator
    router: CloudIntelligenceRouter
    telemetry: CloudTelemetryCollector
    cache: CloudProofCache
    security: CloudSecurityManager
    paper_compiler: CloudPaperCompiler
    webhooks: WebhookManager

    def get_status(self) -> dict[str, Any]:
        """Return diagnostic health and status dictionary for all subsystems in this context."""
        return {
            "subscriptions_active": len(getattr(self.subscription_manager, "_users", {})),
            "cached_proofs": len(self.cache),
            "swarm_agents": len(getattr(self.swarm, "active_nodes", {})),
            "telemetry_metrics_collected": len(getattr(self.telemetry, "_metrics_buffer", [])),
            "papers_catalog_size": len(getattr(self.paper_compiler, "get_all_papers", lambda: [])()),
        }


# Global lazy-initialized singleton context
_GLOBAL_CLOUD_CONTEXT: Optional[TruthGPTCloudContext] = None


def get_cloud_context() -> TruthGPTCloudContext:
    """
    Retrieve the global singleton TruthGPT Cloud Platform context.
    Initializes subsystems with default singletons on first invocation.
    """
    global _GLOBAL_CLOUD_CONTEXT
    if _GLOBAL_CLOUD_CONTEXT is None:
        from ..billing.subscription import subscription_manager
        from ..billing.webhooks import webhook_manager
        from ..verification.verifier import cloud_verifier
        from ..swarm.orchestrator import cloud_swarm
        from ..routing.router import cloud_router
        from ..telemetry.collector import cloud_telemetry
        from ..cache.proof_cache import proof_cache
        from ..security.manager import cloud_security
        from ..papers.compiler import cloud_paper_compiler

        _GLOBAL_CLOUD_CONTEXT = TruthGPTCloudContext(
            subscription_manager=subscription_manager,
            verifier=cloud_verifier,
            swarm=cloud_swarm,
            router=cloud_router,
            telemetry=cloud_telemetry,
            cache=proof_cache,
            security=cloud_security,
            paper_compiler=cloud_paper_compiler,
            webhooks=webhook_manager,
        )
    return _GLOBAL_CLOUD_CONTEXT


def set_cloud_context(context: TruthGPTCloudContext) -> None:
    """Explicitly set or override the global default cloud context."""
    global _GLOBAL_CLOUD_CONTEXT
    _GLOBAL_CLOUD_CONTEXT = context


def reset_cloud_context() -> None:
    """Reset the global cloud context so it will be lazily reinstantiated on next access."""
    global _GLOBAL_CLOUD_CONTEXT
    _GLOBAL_CLOUD_CONTEXT = None


def create_isolated_context(
    storage_backend: Optional[StorageBackend] = None,
    custom_storage_path: Optional[str] = None,
    isolated_cache_capacity: int = 100,
) -> TruthGPTCloudContext:
    """
    Instantiate a completely isolated TruthGPT Cloud Context.
    Ideal for unit tests, isolated sandbox simulations, or multi-tenant tenants.
    Guarantees no state leakage into the primary persistent database.
    """
    from ..billing.subscription import SubscriptionManager
    from ..billing.webhooks import WebhookManager
    from ..verification.verifier import CloudFormalVerifier
    from ..swarm.orchestrator import CloudSwarmOrchestrator
    from ..routing.router import CloudIntelligenceRouter
    from ..telemetry.collector import CloudTelemetryCollector
    from ..cache.proof_cache import CloudProofCache
    from ..security.manager import CloudSecurityManager
    from ..papers.compiler import CloudPaperCompiler

    if storage_backend is None and custom_storage_path is None:
        test_dir = os.path.join(tempfile.gettempdir(), "truthgpt_context_isolated")
        os.makedirs(test_dir, exist_ok=True)
        custom_storage_path = os.path.join(test_dir, f"sub_test_{os.getpid()}_{id(test_dir)}.json")

    sub_mgr = SubscriptionManager(storage_path=custom_storage_path, storage=storage_backend)
    sec_mgr = CloudSecurityManager()
    cache = CloudProofCache(max_entries=isolated_cache_capacity)
    verifier = CloudFormalVerifier(enable_smt=True, cache=cache)
    swarm = CloudSwarmOrchestrator()
    router = CloudIntelligenceRouter(verifier=verifier, swarm=swarm, subscription_manager=sub_mgr)
    telem = CloudTelemetryCollector()
    compiler = CloudPaperCompiler()
    webhooks = WebhookManager()

    return TruthGPTCloudContext(
        subscription_manager=sub_mgr,
        verifier=verifier,
        swarm=swarm,
        router=router,
        telemetry=telem,
        cache=cache,
        security=sec_mgr,
        paper_compiler=compiler,
        webhooks=webhooks,
    )


__all__ = [
    "TruthGPTCloudContext",
    "get_cloud_context",
    "set_cloud_context",
    "reset_cloud_context",
    "create_isolated_context",
]
