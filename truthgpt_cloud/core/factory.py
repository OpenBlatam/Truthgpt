"""
🏭 TruthGPT Cloud - Unified Component Factory
Provides factory methods to assemble and instantiate configured cloud components
(storage, cache, verifier, router, limiter, swarm, subscription manager, client).
"""

from typing import Optional, Any, Dict
from pathlib import Path

from .config import (
    CloudPlatformConfig,
    CloudStorageConfig,
    CloudCacheConfig,
    CloudVerifierConfig,
    CloudRoutingConfig,
    CloudRateLimiterConfig,
)
from .registry import CloudRegistry
from .interfaces import (
    IStorageBackend,
    IProofCache,
    IFormalVerifier,
    IIntelligenceRouter,
    IRateLimiter,
    ISwarmOrchestrator,
    ISubscriptionManager,
)
from .tiers import CloudTier


class CloudFactory:
    """Factory for instantiating TruthGPT Cloud architectural components."""

    @classmethod
    def create_storage_backend(
        cls,
        config: Optional[CloudStorageConfig] = None,
    ) -> IStorageBackend:
        """Instantiate a storage backend according to configuration."""
        cfg = config or CloudStorageConfig()
        cfg.validate()

        backend_cls = CloudRegistry.get_storage_backend(cfg.backend_type)
        if not backend_cls:
            raise ValueError(f"No storage backend registered for type '{cfg.backend_type}'")

        if cfg.backend_type == "json":
            file_path = cfg.file_path or str(
                Path(__file__).resolve().parent.parent / "cloud_subscriptions_db.json"
            )
            return backend_cls(file_path=file_path, debounce_seconds=cfg.debounce_flush_seconds)
        elif cfg.backend_type == "sqlite":
            db_path = cfg.file_path or cfg.db_url or ":memory:"
            return backend_cls(db_path=db_path)
        elif cfg.backend_type in ("memory", "in_memory"):
            return backend_cls()
        else:
            file_path = cfg.file_path or str(
                Path(__file__).resolve().parent.parent / "cloud_subscriptions_db.json"
            )
            return backend_cls(file_path=file_path)

    @classmethod
    def create_proof_cache(
        cls,
        config: Optional[CloudCacheConfig] = None,
    ) -> IProofCache:
        """Instantiate a proof cache backend according to configuration."""
        cfg = config or CloudCacheConfig()
        cfg.validate()

        if cfg.l2_redis_enabled:
            redis_cls = CloudRegistry.get_cache_backend("redis")
            if redis_cls:
                return redis_cls(redis_url=cfg.redis_url, ttl_seconds=cfg.ttl_seconds)

        mem_cls = CloudRegistry.get_cache_backend("memory")
        if not mem_cls:
            from ..cache.proof_cache import CloudProofCache
            mem_cls = CloudProofCache

        cache = mem_cls(max_entries=cfg.l1_max_entries)
        if cfg.warmup_on_start:
            cache.warm_up()
        return cache

    @classmethod
    def create_formal_verifier(
        cls,
        config: Optional[CloudVerifierConfig] = None,
    ) -> IFormalVerifier:
        """Instantiate a formal theorem verifier according to configuration."""
        cfg = config or CloudVerifierConfig()
        cfg.validate()

        verifier_cls = CloudRegistry.get_verifier("smt")
        if not verifier_cls:
            from ..verification.verifier import CloudFormalVerifier
            verifier_cls = CloudFormalVerifier

        return verifier_cls(
            smt_timeout_ms=cfg.smt_timeout_ms,
            export_lean4=cfg.export_lean4,
            export_coq=cfg.export_coq,
        )

    @classmethod
    def create_intelligence_router(
        cls,
        config: Optional[CloudRoutingConfig] = None,
    ) -> IIntelligenceRouter:
        """Instantiate an intelligence router according to configuration."""
        cfg = config or CloudRoutingConfig()
        cfg.validate()

        router_cls = CloudRegistry.get_router("default")
        if not router_cls:
            from ..routing.router import CloudIntelligenceRouter
            router_cls = CloudIntelligenceRouter

        return router_cls()

    @classmethod
    def create_rate_limiter(
        cls,
        config: Optional[CloudRateLimiterConfig] = None,
    ) -> IRateLimiter:
        """Instantiate a rate limiter according to configuration."""
        cfg = config or CloudRateLimiterConfig()
        cfg.validate()

        limiter_cls = CloudRegistry.get_rate_limiter(cfg.algorithm)
        if not limiter_cls:
            from ..rate_limiting import SlidingWindowRateLimiter
            limiter_cls = SlidingWindowRateLimiter

        return limiter_cls()

    @classmethod
    def create_swarm_orchestrator(
        cls,
        topology: str = "hierarchical",
    ) -> ISwarmOrchestrator:
        """Instantiate a multi-agent swarm orchestrator."""
        swarm_cls = CloudRegistry.get_swarm_topology(topology)
        if not swarm_cls:
            from ..swarm.orchestrator import CloudSwarmOrchestrator
            swarm_cls = CloudSwarmOrchestrator

        return swarm_cls()

    @classmethod
    def create_subscription_manager(
        cls,
        storage_path: Optional[str] = None,
    ) -> ISubscriptionManager:
        """Instantiate a subscription manager."""
        from ..billing.subscription import SubscriptionManager
        return SubscriptionManager(storage_path=storage_path)

    @classmethod
    def create_cloud_client(
        cls,
        tier: Optional[CloudTier] = None,
        api_key: Optional[str] = None,
        config: Optional[CloudPlatformConfig] = None,
    ) -> Any:
        """Instantiate a high-level TruthGPTCloudClient SDK."""
        from ..client.client import TruthGPTCloudClient
        cfg = config or CloudPlatformConfig.from_env()
        resolved_tier = tier or CloudTier(cfg.default_tier)
        return TruthGPTCloudClient(api_key=api_key, tier=resolved_tier)

    @classmethod
    def create_platform(
        cls,
        config: Optional[CloudPlatformConfig] = None,
    ) -> Dict[str, Any]:
        """Assemble all core services for TruthGPT Cloud platform hub."""
        cfg = config or CloudPlatformConfig.from_env()
        cfg.validate()

        storage = cls.create_storage_backend(cfg.storage)
        cache = cls.create_proof_cache(cfg.cache)
        verifier = cls.create_formal_verifier(cfg.verifier)
        router = cls.create_intelligence_router(cfg.routing)
        rate_limiter = cls.create_rate_limiter(cfg.rate_limiter)
        swarm = cls.create_swarm_orchestrator()
        subscription_mgr = cls.create_subscription_manager(cfg.storage.file_path)

        return {
            "config": cfg,
            "storage": storage,
            "cache": cache,
            "verifier": verifier,
            "router": router,
            "rate_limiter": rate_limiter,
            "swarm": swarm,
            "subscription_manager": subscription_mgr,
        }


__all__ = ["CloudFactory"]
