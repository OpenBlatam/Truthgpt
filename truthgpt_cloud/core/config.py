"""
⚙️ TruthGPT Cloud - Composable Platform Configuration
Defines strongly-typed, validated, and serializable configuration dataclasses
for storage, caching, verification, routing, rate limiting, telemetry, and resilience.
"""

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

from .constants import (
    CLOUD_API_VERSION,
    CLOUD_PLATFORM_VERSION,
    DEFAULT_SLIDING_WINDOW_SECONDS,
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_TELEMETRY_MAX_HISTORY,
    DEFAULT_SMT_TIMEOUT_MS,
)
from .exceptions import TruthGPTCloudError


class CloudConfigValidationError(TruthGPTCloudError):
    """Raised when platform configuration fails validation constraints."""
    pass


@dataclass
class CloudStorageConfig:
    """Configuration for persistence storage engines."""
    backend_type: str = "json"  # "json", "sqlite", "atomic"
    file_path: Optional[str] = None
    db_url: Optional[str] = None
    debounce_flush_seconds: float = 0.5
    auto_snapshot: bool = False
    snapshot_interval_seconds: int = 3600

    def validate(self) -> None:
        """Validate storage configuration."""
        if self.backend_type not in ("json", "sqlite", "atomic"):
            raise CloudConfigValidationError(
                f"Unsupported storage backend_type '{self.backend_type}'. Expected 'json', 'sqlite', or 'atomic'."
            )
        if self.debounce_flush_seconds < 0:
            raise CloudConfigValidationError("debounce_flush_seconds must be non-negative.")


@dataclass
class CloudCacheConfig:
    """Configuration for L1 memory and L2 Redis proof caching."""
    l1_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES
    l2_redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    ttl_seconds: int = 86400
    warmup_on_start: bool = True

    def validate(self) -> None:
        """Validate cache configuration."""
        if self.l1_max_entries <= 0:
            raise CloudConfigValidationError("l1_max_entries must be greater than zero.")
        if self.ttl_seconds <= 0:
            raise CloudConfigValidationError("ttl_seconds must be positive.")


@dataclass
class CloudVerifierConfig:
    """Configuration for formal theorem proving and SMT verification."""
    smt_timeout_ms: int = DEFAULT_SMT_TIMEOUT_MS
    z3_enabled: bool = True
    sympy_enabled: bool = True
    export_lean4: bool = False
    export_coq: bool = False

    def validate(self) -> None:
        """Validate verifier configuration."""
        if self.smt_timeout_ms <= 0:
            raise CloudConfigValidationError("smt_timeout_ms must be positive.")


@dataclass
class CloudRoutingConfig:
    """Configuration for intelligent inference routing and model mapping."""
    default_model: str = "truthgpt-pro-smt"
    fallback_model: str = "deepseek-chat"
    max_context_window: int = 200000
    temperature: float = 0.2

    def validate(self) -> None:
        """Validate routing configuration."""
        if not (0.0 <= self.temperature <= 2.0):
            raise CloudConfigValidationError("temperature must be between 0.0 and 2.0.")
        if self.max_context_window <= 0:
            raise CloudConfigValidationError("max_context_window must be positive.")


@dataclass
class CloudRateLimiterConfig:
    """Configuration for rate limiting and concurrency enforcement."""
    algorithm: str = "sliding_window"  # "sliding_window", "token_bucket", "redis"
    default_window_seconds: int = DEFAULT_SLIDING_WINDOW_SECONDS
    default_burst_tokens: int = 100

    def validate(self) -> None:
        """Validate rate limiter configuration."""
        if self.algorithm not in ("sliding_window", "token_bucket", "redis"):
            raise CloudConfigValidationError(
                f"Unsupported rate limiter algorithm '{self.algorithm}'."
            )
        if self.default_window_seconds <= 0:
            raise CloudConfigValidationError("default_window_seconds must be positive.")


@dataclass
class CloudTelemetryConfig:
    """Configuration for Prometheus metrics and structured logging."""
    prometheus_enabled: bool = True
    structured_logging: bool = True
    max_history: int = DEFAULT_TELEMETRY_MAX_HISTORY

    def validate(self) -> None:
        """Validate telemetry configuration."""
        if self.max_history <= 0:
            raise CloudConfigValidationError("max_history must be positive.")


@dataclass
class CloudResilienceConfig:
    """Configuration for circuit breakers, backoff retries, and error budgets."""
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    retry_max_attempts: int = 3
    retry_backoff_base: float = 1.5

    def validate(self) -> None:
        """Validate resilience configuration."""
        if self.failure_threshold <= 0:
            raise CloudConfigValidationError("failure_threshold must be positive.")
        if self.recovery_timeout_seconds <= 0:
            raise CloudConfigValidationError("recovery_timeout_seconds must be positive.")
        if self.retry_max_attempts < 1:
            raise CloudConfigValidationError("retry_max_attempts must be at least 1.")


@dataclass
class CloudPlatformConfig:
    """Master platform configuration for TruthGPT Cloud services."""
    storage: CloudStorageConfig = field(default_factory=CloudStorageConfig)
    cache: CloudCacheConfig = field(default_factory=CloudCacheConfig)
    verifier: CloudVerifierConfig = field(default_factory=CloudVerifierConfig)
    routing: CloudRoutingConfig = field(default_factory=CloudRoutingConfig)
    rate_limiter: CloudRateLimiterConfig = field(default_factory=CloudRateLimiterConfig)
    telemetry: CloudTelemetryConfig = field(default_factory=CloudTelemetryConfig)
    resilience: CloudResilienceConfig = field(default_factory=CloudResilienceConfig)
    environment: str = "development"
    default_tier: str = "pro"
    api_version: str = CLOUD_API_VERSION
    platform_version: str = CLOUD_PLATFORM_VERSION

    def validate(self) -> None:
        """Validate all sub-configurations."""
        self.storage.validate()
        self.cache.validate()
        self.verifier.validate()
        self.routing.validate()
        self.rate_limiter.validate()
        self.telemetry.validate()
        self.resilience.validate()
        if self.environment.lower() not in ("development", "staging", "production", "test"):
            raise CloudConfigValidationError(
                f"Invalid environment '{self.environment}'. Must be one of: development, staging, production, test."
            )
        if self.default_tier.lower() not in ("free", "pro", "ultra", "enterprise"):
            raise CloudConfigValidationError(
                f"Invalid default_tier '{self.default_tier}'. Must be one of: free, pro, ultra, enterprise."
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CloudPlatformConfig":
        """Create configuration from dictionary."""
        storage_data = data.get("storage", {})
        cache_data = data.get("cache", {})
        verifier_data = data.get("verifier", {})
        routing_data = data.get("routing", {})
        rate_limiter_data = data.get("rate_limiter", {})
        telemetry_data = data.get("telemetry", {})
        resilience_data = data.get("resilience", {})

        config = cls(
            storage=CloudStorageConfig(**storage_data),
            cache=CloudCacheConfig(**cache_data),
            verifier=CloudVerifierConfig(**verifier_data),
            routing=CloudRoutingConfig(**routing_data),
            rate_limiter=CloudRateLimiterConfig(**rate_limiter_data),
            telemetry=CloudTelemetryConfig(**telemetry_data),
            resilience=CloudResilienceConfig(**resilience_data),
            environment=data.get("environment", "development"),
            default_tier=data.get("default_tier", "pro"),
            api_version=data.get("api_version", CLOUD_API_VERSION),
            platform_version=data.get("platform_version", CLOUD_PLATFORM_VERSION),
        )
        config.validate()
        return config

    @classmethod
    def from_env(cls) -> "CloudPlatformConfig":
        """Load platform configuration with environment variable overrides."""
        config = cls()

        # Environment
        if "TRUTHGPT_ENV" in os.environ:
            config.environment = os.environ["TRUTHGPT_ENV"].lower()
        elif "ENVIRONMENT" in os.environ:
            config.environment = os.environ["ENVIRONMENT"].lower()

        # Storage env overrides
        if "TRUTHGPT_STORAGE_PATH" in os.environ:
            config.storage.file_path = os.environ["TRUTHGPT_STORAGE_PATH"]
        if "TRUTHGPT_STORAGE_BACKEND" in os.environ:
            config.storage.backend_type = os.environ["TRUTHGPT_STORAGE_BACKEND"].lower()
        if "TRUTHGPT_DB_URL" in os.environ:
            config.storage.db_url = os.environ["TRUTHGPT_DB_URL"]

        # Cache env overrides
        if "REDIS_URL" in os.environ:
            config.cache.redis_url = os.environ["REDIS_URL"]
            config.cache.l2_redis_enabled = True
        if "TRUTHGPT_CACHE_MAX_ENTRIES" in os.environ:
            try:
                config.cache.l1_max_entries = int(os.environ["TRUTHGPT_CACHE_MAX_ENTRIES"])
            except ValueError:
                pass

        # Verifier env overrides
        if "TRUTHGPT_SMT_TIMEOUT_MS" in os.environ:
            try:
                config.verifier.smt_timeout_ms = int(os.environ["TRUTHGPT_SMT_TIMEOUT_MS"])
            except ValueError:
                pass

        # Tier override
        if "TRUTHGPT_DEFAULT_TIER" in os.environ:
            config.default_tier = os.environ["TRUTHGPT_DEFAULT_TIER"].lower()

        config.validate()
        return config

    def save_json(self, path: str) -> None:
        """Serialize configuration to a JSON file."""
        self.validate()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: str) -> "CloudPlatformConfig":
        """Load and deserialize configuration from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


__all__ = [
    "CloudConfigValidationError",
    "CloudStorageConfig",
    "CloudCacheConfig",
    "CloudVerifierConfig",
    "CloudRoutingConfig",
    "CloudRateLimiterConfig",
    "CloudTelemetryConfig",
    "CloudResilienceConfig",
    "CloudPlatformConfig",
]
