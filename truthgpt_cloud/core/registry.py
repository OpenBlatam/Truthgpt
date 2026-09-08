"""
🏛️ TruthGPT Cloud - Central Thread-Safe Component Registry
Enables dynamic discovery and runtime registration of custom verifiers, storage backends,
proof caches, rate limiters, payment gateways, intelligence routers, and swarm topologies.
"""

import threading
from typing import Dict, Any, Type, Callable, Optional, List


class CloudRegistry:
    """Thread-safe dynamic component registry for TruthGPT Cloud ecosystem."""

    _lock = threading.Lock()
    _verifiers: Dict[str, Type[Any]] = {}
    _storage_backends: Dict[str, Type[Any]] = {}
    _cache_backends: Dict[str, Type[Any]] = {}
    _rate_limiters: Dict[str, Type[Any]] = {}
    _payment_gateways: Dict[str, Type[Any]] = {}
    _swarm_topologies: Dict[str, Any] = {}
    _routers: Dict[str, Type[Any]] = {}
    _builtins_initialized: bool = False

    # -------------------------------------------------------------------------
    # Verifiers
    # -------------------------------------------------------------------------
    @classmethod
    def register_verifier(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Formal Verifier class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._verifiers[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_verifier(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered verifier class by name."""
        cls._ensure_builtins()
        with cls._lock:
            return cls._verifiers.get(name.lower())

    @classmethod
    def list_verifiers(cls) -> List[str]:
        """List names of all registered formal verifiers."""
        cls._ensure_builtins()
        with cls._lock:
            return sorted(list(cls._verifiers.keys()))

    # -------------------------------------------------------------------------
    # Storage Backends
    # -------------------------------------------------------------------------
    @classmethod
    def register_storage_backend(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Storage Backend class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._storage_backends[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_storage_backend(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered storage backend class by name."""
        cls._ensure_builtins()
        with cls._lock:
            return cls._storage_backends.get(name.lower())

    @classmethod
    def list_storage_backends(cls) -> List[str]:
        """List names of all registered storage backends."""
        cls._ensure_builtins()
        with cls._lock:
            return sorted(list(cls._storage_backends.keys()))

    # -------------------------------------------------------------------------
    # Cache Backends
    # -------------------------------------------------------------------------
    @classmethod
    def register_cache_backend(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Proof Cache Backend class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._cache_backends[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_cache_backend(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered cache backend class by name."""
        cls._ensure_builtins()
        with cls._lock:
            return cls._cache_backends.get(name.lower())

    @classmethod
    def list_cache_backends(cls) -> List[str]:
        """List names of all registered proof cache backends."""
        cls._ensure_builtins()
        with cls._lock:
            return sorted(list(cls._cache_backends.keys()))

    # -------------------------------------------------------------------------
    # Rate Limiters
    # -------------------------------------------------------------------------
    @classmethod
    def register_rate_limiter(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Rate Limiter class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._rate_limiters[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_rate_limiter(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered rate limiter class by name."""
        cls._ensure_builtins()
        with cls._lock:
            return cls._rate_limiters.get(name.lower())

    @classmethod
    def list_rate_limiters(cls) -> List[str]:
        """List names of all registered rate limiters."""
        cls._ensure_builtins()
        with cls._lock:
            return sorted(list(cls._rate_limiters.keys()))

    # -------------------------------------------------------------------------
    # Payment Gateways
    # -------------------------------------------------------------------------
    @classmethod
    def register_payment_gateway(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Payment Gateway class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._payment_gateways[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_payment_gateway(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered payment gateway class by name."""
        cls._ensure_builtins()
        with cls._lock:
            return cls._payment_gateways.get(name.lower())

    @classmethod
    def list_payment_gateways(cls) -> List[str]:
        """List names of all registered payment gateways."""
        cls._ensure_builtins()
        with cls._lock:
            return sorted(list(cls._payment_gateways.keys()))

    # -------------------------------------------------------------------------
    # Swarm Topologies
    # -------------------------------------------------------------------------
    @classmethod
    def register_swarm_topology(cls, name: str) -> Callable[[Any], Any]:
        """Decorator to register a custom Swarm Topology handler or class."""
        def decorator(handler: Any) -> Any:
            with cls._lock:
                cls._swarm_topologies[name.lower()] = handler
            return handler
        return decorator

    @classmethod
    def get_swarm_topology(cls, name: str) -> Optional[Any]:
        """Retrieve a registered swarm topology handler by name."""
        cls._ensure_builtins()
        with cls._lock:
            return cls._swarm_topologies.get(name.lower())

    @classmethod
    def list_swarm_topologies(cls) -> List[str]:
        """List names of all registered swarm topologies."""
        cls._ensure_builtins()
        with cls._lock:
            return sorted(list(cls._swarm_topologies.keys()))

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    @classmethod
    def register_router(cls, name: str) -> Callable[[Type[Any]], Type[Any]]:
        """Decorator to register a custom Intelligence Router class."""
        def decorator(subclass: Type[Any]) -> Type[Any]:
            with cls._lock:
                cls._routers[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_router(cls, name: str) -> Optional[Type[Any]]:
        """Retrieve a registered intelligence router class by name."""
        cls._ensure_builtins()
        with cls._lock:
            return cls._routers.get(name.lower())

    @classmethod
    def list_routers(cls) -> List[str]:
        """List names of all registered intelligence routers."""
        cls._ensure_builtins()
        with cls._lock:
            return sorted(list(cls._routers.keys()))

    # -------------------------------------------------------------------------
    # Lifecycle & Built-ins
    # -------------------------------------------------------------------------
    @classmethod
    def reset(cls) -> None:
        """Reset the registry to uninitialized state (primarily for testing)."""
        with cls._lock:
            cls._verifiers.clear()
            cls._storage_backends.clear()
            cls._cache_backends.clear()
            cls._rate_limiters.clear()
            cls._payment_gateways.clear()
            cls._swarm_topologies.clear()
            cls._routers.clear()
            cls._builtins_initialized = False

    @classmethod
    def _ensure_builtins(cls) -> None:
        """Ensure core platform built-in components are pre-registered."""
        if cls._builtins_initialized:
            return

        with cls._lock:
            if cls._builtins_initialized:
                return

            # Built-in Storage Backends
            try:
                from ..storage.json_storage import JsonFileStorageBackend
                cls._storage_backends["json"] = JsonFileStorageBackend
            except ImportError:
                pass
            try:
                from ..storage.sqlite_storage import SqliteStorageBackend
                cls._storage_backends["sqlite"] = SqliteStorageBackend
            except ImportError:
                pass
            try:
                from ..storage.atomic import AtomicJsonStorage
                cls._storage_backends["atomic"] = AtomicJsonStorage
            except ImportError:
                pass

            # Built-in Caches
            try:
                from ..cache.proof_cache import CloudProofCache
                cls._cache_backends["memory"] = CloudProofCache
                cls._cache_backends["in_memory"] = CloudProofCache
            except ImportError:
                pass
            try:
                from ..cache.redis_cache import RedisProofCacheBackend
                cls._cache_backends["redis"] = RedisProofCacheBackend
            except ImportError:
                pass

            # Built-in Verifiers
            try:
                from ..verification.verifier import CloudFormalVerifier
                cls._verifiers["smt"] = CloudFormalVerifier
                cls._verifiers["formal"] = CloudFormalVerifier
                cls._verifiers["default"] = CloudFormalVerifier
            except ImportError:
                pass
            try:
                from ..verification.smt_engine import Z3TheoremSolver
                cls._verifiers["z3"] = Z3TheoremSolver
            except ImportError:
                pass

            # Built-in Rate Limiters
            try:
                from ..rate_limiting import (
                    TokenBucketRateLimiter,
                    SlidingWindowRateLimiter,
                )
                cls._rate_limiters["token_bucket"] = TokenBucketRateLimiter
                cls._rate_limiters["sliding_window"] = SlidingWindowRateLimiter
            except ImportError:
                pass
            try:
                from ..rate_limiting.redis_limiter import (
                    RedisSlidingWindowRateLimiter,
                    RedisTokenBucketRateLimiter,
                )
                cls._rate_limiters["redis"] = RedisSlidingWindowRateLimiter
                cls._rate_limiters["redis_sliding"] = RedisSlidingWindowRateLimiter
                cls._rate_limiters["redis_token_bucket"] = RedisTokenBucketRateLimiter
            except ImportError:
                pass

            # Built-in Gateways
            try:
                from ..billing.gateways import PaymentGatewayService
                cls._payment_gateways["stripe"] = PaymentGatewayService
                cls._payment_gateways["crypto"] = PaymentGatewayService
                cls._payment_gateways["mock"] = PaymentGatewayService
            except ImportError:
                pass

            # Built-in Routers
            try:
                from ..routing.router import CloudIntelligenceRouter
                cls._routers["default"] = CloudIntelligenceRouter
                cls._routers["cloud"] = CloudIntelligenceRouter
            except ImportError:
                pass

            # Built-in Swarm Topologies
            try:
                from ..swarm.orchestrator import CloudSwarmOrchestrator
                cls._swarm_topologies["hierarchical"] = CloudSwarmOrchestrator
                cls._swarm_topologies["peer_to_peer"] = CloudSwarmOrchestrator
                cls._swarm_topologies["adversarial"] = CloudSwarmOrchestrator
            except ImportError:
                pass

            cls._builtins_initialized = True


__all__ = ["CloudRegistry"]
