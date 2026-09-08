"""
🧪 Unit Test Suite for TruthGPT Cloud Core Architecture
Validates abstract lifecycle interfaces, dynamic thread-safe CloudRegistry,
composable CloudPlatformConfig, unified CloudFactory, and root exports.
"""

import os
import tempfile
import pytest
from pathlib import Path

import truthgpt_cloud
from truthgpt_cloud.core.interfaces import (
    IStorageBackend,
    IProofCache,
    IFormalVerifier,
    ISwarmOrchestrator,
    IIntelligenceRouter,
    IRateLimiter,
    ISubscriptionManager,
    IPaymentGateway,
    ITelemetryCollector,
    ICircuitBreaker,
    IWebhookManager,
    IPaperCompiler,
)
from truthgpt_cloud.core.registry import CloudRegistry
from truthgpt_cloud.core.config import (
    CloudPlatformConfig,
    CloudStorageConfig,
    CloudCacheConfig,
    CloudVerifierConfig,
    CloudRoutingConfig,
    CloudRateLimiterConfig,
    CloudTelemetryConfig,
    CloudResilienceConfig,
    CloudConfigValidationError,
)
from truthgpt_cloud.core.factory import CloudFactory
from truthgpt_cloud.storage.base import StorageBackend
from truthgpt_cloud.cache.base import BaseProofCache


class TestCloudInterfaces:
    """Validate abstract lifecycle contracts and subclassing constraints."""

    def test_abstract_interfaces_cannot_be_instantiated(self):
        """Verify that ABCs cannot be directly instantiated."""
        interfaces = [
            IStorageBackend,
            IProofCache,
            IFormalVerifier,
            ISwarmOrchestrator,
            IIntelligenceRouter,
            IRateLimiter,
            ISubscriptionManager,
            IPaymentGateway,
            ITelemetryCollector,
            ICircuitBreaker,
            IWebhookManager,
            IPaperCompiler,
        ]
        for iface in interfaces:
            with pytest.raises(TypeError):
                iface()

    def test_subsystem_base_classes_inherit_from_core_interfaces(self):
        """Verify existing storage and cache base classes inherit from core interfaces."""
        assert issubclass(StorageBackend, IStorageBackend)
        assert issubclass(BaseProofCache, IProofCache)

    def test_concrete_verifier_implements_interface(self):
        """Verify CloudFormalVerifier conforms to IFormalVerifier."""
        from truthgpt_cloud.verification.verifier import CloudFormalVerifier
        assert issubclass(CloudFormalVerifier, IFormalVerifier)

    def test_concrete_cache_implements_interface(self):
        """Verify CloudProofCache conforms to IProofCache."""
        from truthgpt_cloud.cache.proof_cache import CloudProofCache
        assert issubclass(CloudProofCache, IProofCache)


class TestCloudRegistry:
    """Validate dynamic thread-safe component registration and discovery."""

    def test_builtin_storage_backends_registered(self):
        """Verify standard storage backends are discovered in registry."""
        backends = CloudRegistry.list_storage_backends()
        assert "json" in backends
        assert "sqlite" in backends
        assert "atomic" in backends
        assert CloudRegistry.get_storage_backend("json") is not None

    def test_builtin_verifiers_registered(self):
        """Verify standard verifiers are discovered in registry."""
        verifiers = CloudRegistry.list_verifiers()
        assert "smt" in verifiers
        assert "z3" in verifiers
        assert CloudRegistry.get_verifier("smt") is not None

    def test_builtin_caches_registered(self):
        """Verify standard caches are discovered in registry."""
        caches = CloudRegistry.list_cache_backends()
        assert "memory" in caches
        assert "redis" in caches
        assert CloudRegistry.get_cache_backend("memory") is not None

    def test_builtin_rate_limiters_registered(self):
        """Verify standard rate limiters are discovered in registry."""
        limiters = CloudRegistry.list_rate_limiters()
        assert "sliding_window" in limiters
        assert "token_bucket" in limiters
        assert "redis_sliding" in limiters
        assert CloudRegistry.get_rate_limiter("sliding_window") is not None

    def test_custom_component_registration(self):
        """Verify custom verifier, storage, and limiter decorators work cleanly."""
        @CloudRegistry.register_verifier("custom_mock_verifier")
        class CustomMockVerifier:
            pass

        @CloudRegistry.register_storage_backend("custom_mock_storage")
        class CustomMockStorage:
            pass

        @CloudRegistry.register_rate_limiter("custom_mock_limiter")
        class CustomMockLimiter:
            pass

        assert CloudRegistry.get_verifier("custom_mock_verifier") is CustomMockVerifier
        assert CloudRegistry.get_storage_backend("custom_mock_storage") is CustomMockStorage
        assert CloudRegistry.get_rate_limiter("custom_mock_limiter") is CustomMockLimiter


class TestCloudConfig:
    """Validate composable configuration dataclasses and validation rules."""

    def test_default_config_validates(self):
        """Verify default configuration passes validation."""
        cfg = CloudPlatformConfig()
        cfg.validate()
        assert cfg.default_tier == "pro"
        assert cfg.storage.backend_type == "json"
        assert cfg.verifier.smt_timeout_ms == 5000

    def test_invalid_tier_raises_validation_error(self):
        """Verify invalid tier specification raises CloudConfigValidationError."""
        cfg = CloudPlatformConfig(default_tier="invalid_super_tier")
        with pytest.raises(CloudConfigValidationError):
            cfg.validate()

    def test_invalid_storage_type_raises(self):
        """Verify invalid storage backend raises validation error."""
        cfg = CloudStorageConfig(backend_type="unsupported_engine")
        with pytest.raises(CloudConfigValidationError):
            cfg.validate()

    def test_dict_serialization_roundtrip(self):
        """Verify full configuration dict serialization and deserialization."""
        original = CloudPlatformConfig(
            storage=CloudStorageConfig(debounce_flush_seconds=1.2),
            verifier=CloudVerifierConfig(smt_timeout_ms=8000),
            default_tier="ultra",
        )
        data = original.to_dict()
        assert data["default_tier"] == "ultra"
        assert data["verifier"]["smt_timeout_ms"] == 8000

        restored = CloudPlatformConfig.from_dict(data)
        assert restored.default_tier == "ultra"
        assert restored.verifier.smt_timeout_ms == 8000
        assert restored.storage.debounce_flush_seconds == 1.2

    def test_json_file_persistence_roundtrip(self, tmp_path):
        """Verify JSON save and load roundtrip."""
        json_path = str(tmp_path / "cloud_config.json")
        original = CloudPlatformConfig(default_tier="enterprise")
        original.save_json(json_path)

        assert os.path.exists(json_path)
        loaded = CloudPlatformConfig.load_json(json_path)
        assert loaded.default_tier == "enterprise"

    def test_env_variable_overrides(self, monkeypatch):
        """Verify environment variables override defaults in from_env()."""
        monkeypatch.setenv("TRUTHGPT_STORAGE_BACKEND", "sqlite")
        monkeypatch.setenv("TRUTHGPT_SMT_TIMEOUT_MS", "12000")
        monkeypatch.setenv("TRUTHGPT_DEFAULT_TIER", "ultra")

        env_cfg = CloudPlatformConfig.from_env()
        assert env_cfg.storage.backend_type == "sqlite"
        assert env_cfg.verifier.smt_timeout_ms == 12000
        assert env_cfg.default_tier == "ultra"


class TestCloudFactory:
    """Validate unified factory creation of platform subsystems."""

    def test_create_storage_backend(self, tmp_path):
        """Verify factory creates functional storage backend."""
        db_file = str(tmp_path / "factory_db.json")
        cfg = CloudStorageConfig(backend_type="json", file_path=db_file)
        storage = CloudFactory.create_storage_backend(cfg)

        assert isinstance(storage, IStorageBackend)
        storage.set("test_coll", "key1", {"val": 42})
        record = storage.get("test_coll", "key1")
        assert record == {"val": 42}

    def test_create_proof_cache(self):
        """Verify factory creates warmed-up proof cache."""
        cfg = CloudCacheConfig(l1_max_entries=20, warmup_on_start=True)
        cache = CloudFactory.create_proof_cache(cfg)

        assert isinstance(cache, IProofCache)
        assert len(cache) >= 2
        stats = cache.get_stats()
        assert stats["cached_entries"] >= 2

    def test_create_formal_verifier(self):
        """Verify factory creates operational formal verifier."""
        cfg = CloudVerifierConfig(smt_timeout_ms=3000)
        verifier = CloudFactory.create_formal_verifier(cfg)

        assert isinstance(verifier, IFormalVerifier)
        cert = verifier.verify_claim("a + b == b + a")
        assert cert.status in ("PROVEN_VALID", "VERIFIED_SYMBOLIC")

    def test_create_rate_limiter(self):
        """Verify factory creates operational rate limiter."""
        cfg = CloudRateLimiterConfig(algorithm="sliding_window")
        limiter = CloudFactory.create_rate_limiter(cfg)

        assert isinstance(limiter, IRateLimiter)
        assert limiter.check_rate_limit("test_user_factory") is True

    def test_create_cloud_client(self):
        """Verify factory creates configured TruthGPTCloudClient SDK."""
        from truthgpt_cloud import CloudTier, TruthGPTCloudClient
        client = CloudFactory.create_cloud_client(tier=CloudTier.ULTRA)

        assert isinstance(client, TruthGPTCloudClient)
        assert client.tier == CloudTier.ULTRA

    def test_create_platform_assembly(self, tmp_path):
        """Verify factory creates full platform dictionary."""
        db_file = str(tmp_path / "full_platform_db.json")
        cfg = CloudPlatformConfig(
            storage=CloudStorageConfig(file_path=db_file),
            default_tier="pro",
        )
        platform = CloudFactory.create_platform(cfg)

        assert "config" in platform
        assert "storage" in platform
        assert "cache" in platform
        assert "verifier" in platform
        assert "router" in platform
        assert "rate_limiter" in platform
        assert "swarm" in platform
        assert "subscription_manager" in platform


class TestTopLevelArchitectureExports:
    """Validate root namespace re-exports of core architectural components."""

    def test_root_re_exports_interfaces_and_registry(self):
        """Verify all new architectural abstractions are exposed from truthgpt_cloud."""
        expected_exports = [
            "CloudRegistry",
            "CloudFactory",
            "CloudPlatformConfig",
            "CloudStorageConfig",
            "CloudCacheConfig",
            "CloudVerifierConfig",
            "CloudRoutingConfig",
            "CloudRateLimiterConfig",
            "CloudTelemetryConfig",
            "CloudResilienceConfig",
            "IStorageBackend",
            "IProofCache",
            "IFormalVerifier",
            "ISwarmOrchestrator",
            "IIntelligenceRouter",
            "IRateLimiter",
            "ISubscriptionManager",
            "IPaymentGateway",
            "ITelemetryCollector",
            "ICircuitBreaker",
            "IWebhookManager",
            "IPaperCompiler",
        ]

        for export_name in expected_exports:
            assert hasattr(truthgpt_cloud, export_name), f"Missing '{export_name}' in truthgpt_cloud"
            assert export_name in truthgpt_cloud.__all__, f"'{export_name}' not in truthgpt_cloud.__all__"
