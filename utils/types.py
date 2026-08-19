"""
Standardized Types, Enums, and Schemas for Optimization Core Utilities.
=======================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field


class UtilityCategory(str, Enum):
    """Categories of utility subsystems in optimization_core."""
    TRUTHGPT = "truthgpt"
    OPTIMIZER = "optimizer"
    SYSTEM = "system"
    TRAINING_TOOL = "training_tool"
    HARDWARE = "hardware"
    RESILIENCE = "resilience"
    METRIC = "metric"
    LOGGING = "logging"
    MEMORY = "memory"
    SECURITY = "security"
    CONFIG = "config"
    CONCURRENCY = "concurrency"
    AI = "ai"
    GENERAL = "general"


try:
    from .truthgpt.core import OptimizationLevel, DeviceType, PrecisionType
except (ImportError, ValueError):
    try:
        from truthgpt.core import OptimizationLevel, DeviceType, PrecisionType
    except (ImportError, ValueError):
        from utils.truthgpt.core import OptimizationLevel, DeviceType, PrecisionType


# Aliases for compatibility
HardwareDevice = DeviceType
ComputePrecision = PrecisionType


class CudaKernelType(str, Enum):
    """CUDA kernel optimization levels."""
    BASIC = "basic"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"
    LEGENDARY = "legendary"
    TRANSCENDENT = "transcendent"
    DIVINE = "divine"
    OMNIPOTENT = "omnipotent"
    INFINITE = "infinite"
    ULTIMATE = "ultimate"
    ABSOLUTE = "absolute"
    PERFECT = "perfect"


class OptimizationStrategy(str, Enum):
    """High-level optimization goals and profiles."""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    MAX_THROUGHPUT = "max_throughput"
    MIN_LATENCY = "min_latency"
    MEMORY_EFFICIENT = "memory_efficient"


class HealthStatus(str, Enum):
    """System and component health status codes."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(str, Enum):
    """Circuit breaker operational state."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class TaskStatus(str, Enum):
    """Status lifecycle of scheduled tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SerializationFormat(str, Enum):
    """Supported serialization file formats."""
    JSON = "json"
    YAML = "yaml"
    PICKLE = "pickle"
    SAFETENSORS = "safetensors"
    TOML = "toml"


class LogLevel(str, Enum):
    """Standard logging level identifiers."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TrackerBackend(str, Enum):
    """Supported experiment tracking backends."""
    CONSOLE = "console"
    IN_MEMORY = "in_memory"
    WANDB = "wandb"
    TENSORBOARD = "tensorboard"
    MLFLOW = "mlflow"
    JSON_FILE = "json_file"


class CachePolicy(str, Enum):
    """Activation and tensor cache eviction policies."""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    NONE = "none"


@dataclass
class UtilityMetadata:
    """Metadata describing a registered utility component."""
    name: str
    category: UtilityCategory
    version: str = "1.0.0"
    description: str = ""
    author: str = "TruthGPT Team"
    tags: List[str] = field(default_factory=list)
    hardware_requirements: List[HardwareDevice] = field(default_factory=lambda: [HardwareDevice.CPU])
    thread_safe: bool = True
    config_schema: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "category": self.category.value if isinstance(self.category, Enum) else str(self.category),
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tags": list(self.tags),
            "hardware_requirements": [d.value if isinstance(d, Enum) else str(d) for d in self.hardware_requirements],
            "thread_safe": self.thread_safe,
        }


@dataclass
class HardwareInfo:
    """Detailed specifications of compute device hardware."""
    device: HardwareDevice = HardwareDevice.CPU
    available: bool = False
    device_count: int = 0
    name: str = "CPU"
    total_memory_mb: float = 0.0
    allocated_memory_mb: float = 0.0
    reserved_memory_mb: float = 0.0
    compute_capability: Optional[Tuple[int, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert hardware info to dictionary."""
        return {
            "device": self.device.value if isinstance(self.device, Enum) else str(self.device),
            "available": self.available,
            "device_count": self.device_count,
            "name": self.name,
            "total_memory_mb": round(self.total_memory_mb, 2),
            "allocated_memory_mb": round(self.allocated_memory_mb, 2),
            "reserved_memory_mb": round(self.reserved_memory_mb, 2),
            "compute_capability": self.compute_capability,
        }


@dataclass
class ExecutionStats:
    """Benchmark and runtime execution metrics."""
    iterations: int = 1
    elapsed_sec: float = 0.0
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    throughput_per_sec: float = 0.0
    memory_delta_mb: float = 0.0
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "iterations": self.iterations,
            "elapsed_sec": round(self.elapsed_sec, 6),
            "avg_ms": round(self.avg_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
            "throughput_per_sec": round(self.throughput_per_sec, 2),
            "memory_delta_mb": round(self.memory_delta_mb, 2),
            "success": self.success,
            "error": self.error,
        }


# Alias
BenchmarkResult = ExecutionStats


@dataclass
class HealthReport:
    """Comprehensive diagnostic health report."""
    status: HealthStatus = HealthStatus.HEALTHY
    checks: Dict[str, bool] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    uptime_sec: float = 0.0
    error_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert health report to dictionary."""
        return {
            "status": self.status.value if isinstance(self.status, Enum) else str(self.status),
            "checks": dict(self.checks),
            "timestamp": self.timestamp,
            "uptime_sec": round(self.uptime_sec, 2),
            "error_count": self.error_count,
            "details": dict(self.details),
        }


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker pattern."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    failure_threshold: int = Field(default=5, ge=1, description="Consecutive failures to open circuit")
    success_threshold: int = Field(default=2, ge=1, description="Consecutive successes in half-open state to close")
    timeout: float = Field(default=60.0, gt=0, description="Cooldown timeout before half-open attempt in seconds")
    expected_exception: type = Field(default=Exception, description="Exception class to trigger failure count")


class RetryConfig(BaseModel):
    """Configuration for exponential backoff retries."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    max_attempts: int = Field(default=3, ge=1, description="Maximum retry attempts")
    initial_delay: float = Field(default=1.0, ge=0.0, description="Initial delay in seconds")
    backoff_factor: float = Field(default=2.0, ge=1.0, description="Backoff multiplier per retry")
    max_delay: float = Field(default=60.0, ge=0.0, description="Upper bound for retry delay")
    jitter: bool = Field(default=True, description="Add random jitter to delay")
    retry_exceptions: tuple = Field(default=(Exception,), description="Tuple of exceptions to catch for retry")


class RateLimiterConfig(BaseModel):
    """Configuration for token bucket / sliding window rate limiting."""
    max_requests: int = Field(default=100, ge=1, description="Allowed requests within time window")
    time_window_sec: float = Field(default=60.0, gt=0, description="Time window in seconds")
    burst_limit: Optional[int] = Field(default=None, description="Max burst request capacity")


class ResilienceConfig(BaseModel):
    """Consolidated resilience configuration."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    enable_circuit_breaker: bool = True
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    enable_retry: bool = True
    retry: RetryConfig = Field(default_factory=RetryConfig)
    enable_rate_limiter: bool = False
    rate_limiter: RateLimiterConfig = Field(default_factory=RateLimiterConfig)


class TaskMetadata(BaseModel):
    """Metadata and execution state for a scheduled task."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration: Optional[float] = None
    result: Any = None
    error: Optional[str] = None


class UtilityPipelineConfig(BaseModel):
    """Configuration for a fluent utility execution pipeline."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    pipeline_name: str = "StandardUtilityPipeline"
    device: HardwareDevice = HardwareDevice.AUTO
    precision: ComputePrecision = ComputePrecision.FP32
    resilience: ResilienceConfig = Field(default_factory=ResilienceConfig)
    log_telemetry: bool = True
    benchmark_iterations: int = 1


@dataclass
class UtilityConfig:
    """Base configuration for optimization core utilities."""
    name: str = "default_utility"
    enabled: bool = True
    device: DeviceType = DeviceType.AUTO
    precision: PrecisionType = PrecisionType.FP32
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "device": self.device.value if isinstance(self.device, Enum) else str(self.device),
            "precision": self.precision.value if isinstance(self.precision, Enum) else str(self.precision),
            "metadata": self.metadata,
        }


@dataclass
class SystemMetrics:
    """Standardized snapshot of system and hardware utilization."""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    gpu_available: bool = False
    gpu_name: Optional[str] = None
    gpu_used_mb: float = 0.0
    gpu_total_mb: float = 0.0
    gpu_utilization_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_used_gb": round(self.memory_used_gb, 2),
            "memory_total_gb": round(self.memory_total_gb, 2),
            "gpu_available": self.gpu_available,
            "gpu_name": self.gpu_name,
            "gpu_used_mb": round(self.gpu_used_mb, 2),
            "gpu_total_mb": round(self.gpu_total_mb, 2),
            "gpu_utilization_percent": round(self.gpu_utilization_percent, 2),
        }


@dataclass
class MemoryProfile:
    """Memory usage breakdown for a training or inference run."""
    peak_gpu_memory_mb: float = 0.0
    allocated_gpu_memory_mb: float = 0.0
    reserved_gpu_memory_mb: float = 0.0
    system_ram_used_gb: float = 0.0
    tensor_pool_allocated_mb: float = 0.0
    activation_cache_size_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peak_gpu_memory_mb": round(self.peak_gpu_memory_mb, 2),
            "allocated_gpu_memory_mb": round(self.allocated_gpu_memory_mb, 2),
            "reserved_gpu_memory_mb": round(self.reserved_gpu_memory_mb, 2),
            "system_ram_used_gb": round(self.system_ram_used_gb, 2),
            "tensor_pool_allocated_mb": round(self.tensor_pool_allocated_mb, 2),
            "activation_cache_size_mb": round(self.activation_cache_size_mb, 2),
        }


@dataclass
class CheckpointSummary:
    """Metadata summary of a saved checkpoint."""
    name: str
    path: str
    size_mb: float
    is_best: bool = False
    is_last: bool = False
    is_dir: bool = False
    step: Optional[int] = None
    epoch: Optional[int] = None
    metric_value: Optional[float] = None
    modified: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "size_mb": round(self.size_mb, 2),
            "is_best": self.is_best,
            "is_last": self.is_last,
            "is_dir": self.is_dir,
            "step": self.step,
            "epoch": self.epoch,
            "metric_value": self.metric_value,
            "modified": self.modified,
        }


@dataclass
class RunInfo:
    """Structured information regarding an entire training experiment run."""
    name: str
    path: str
    exists: bool = True
    checkpoints: List[CheckpointSummary] = field(default_factory=list)
    total_size_mb: float = 0.0
    has_best: bool = False
    has_last: bool = False
    config: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "exists": self.exists,
            "checkpoints": [c.to_dict() if hasattr(c, "to_dict") else c for c in self.checkpoints],
            "total_size_mb": round(self.total_size_mb, 2),
            "has_best": self.has_best,
            "has_last": self.has_last,
            "config": self.config,
            "metrics": self.metrics,
        }
