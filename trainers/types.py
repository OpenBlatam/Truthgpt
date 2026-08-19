"""
Core type definitions, aliases, protocols, and dataclasses for the trainers package.

Provides strongly typed data structures for step states, metrics, hardware specifications,
gradient diagnostics, profiling summaries, trainer status tracking, and generic container types.

Modernized with:
- StrEnum with Python 3.10 fallback
- frozen/slots dataclasses for immutable value objects
- Type guards and domain constants
- Rich __repr__, merge, and lifecycle helpers
"""
from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

# ---------------------------------------------------------------------------
# StrEnum fallback (Python 3.11+ native, else polyfill)
# ---------------------------------------------------------------------------
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    class StrEnum(str, Enum):
        """String-valued enum polyfill for Python < 3.11."""

        @staticmethod
        def _generate_next_value_(name: str, start: int, count: int, last_values: list) -> str:
            return name.lower()

        def __str__(self) -> str:
            return self.value


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
MAX_GRAD_NORM_DEFAULT: float = 1.0
DEFAULT_WARMUP_RATIO: float = 0.06
DEFAULT_LEARNING_RATE: float = 5e-5
DEFAULT_WEIGHT_DECAY: float = 0.01
DEFAULT_EMA_DECAY: float = 0.999
DEFAULT_SEED: int = 42
DEFAULT_BLOCK_SIZE: int = 512
DEFAULT_LOG_INTERVAL: int = 50
DEFAULT_EVAL_INTERVAL: int = 500
PERPLEXITY_CLAMP_MIN: float = -20.0
PERPLEXITY_CLAMP_MAX: float = 20.0


# ---------------------------------------------------------------------------
# General domain type aliases
# ---------------------------------------------------------------------------
DeviceType = Union[str, Any]  # torch.device or string representation
PrecisionType = Literal["none", "fp16", "bf16"]
OptimizerType = Literal["adamw", "adam", "sgd", "adafactor", "lion", "came", "sophia"]
SchedulerType = Literal[
    "cosine", "linear", "cosine_with_restarts", "polynomial",
    "constant_with_warmup", "one_cycle",
]

BatchType = Dict[str, Any]
LossType = Any  # torch.Tensor or float
MetricsDict = Dict[str, float]
StateDict = Dict[str, Any]
ParamGroupList = List[Dict[str, Any]]

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Type guards
# ---------------------------------------------------------------------------
def is_cuda_device(device: Any) -> bool:
    """Check whether *device* refers to a CUDA accelerator."""
    if hasattr(device, "type"):
        return device.type == "cuda"
    return str(device).startswith("cuda")


def is_finite_loss(loss: Any) -> bool:
    """Return ``True`` if *loss* is a finite scalar (float or tensor)."""
    try:
        if hasattr(loss, "item"):
            val = loss.item()
        else:
            val = float(loss)
        return math.isfinite(val)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ExecutionMode(StrEnum):
    """Execution mode enum for trainer operations."""
    TRAIN = "train"
    EVAL = "eval"
    PREDICT = "predict"


class TrainerStage(StrEnum):
    """Lifecycle stages of trainer workflow."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    TRAINING = "training"
    EVALUATING = "evaluating"
    CHECKPOINTING = "checkpointing"
    COMPLETED = "completed"
    FAILED = "failed"


class PrecisionMode(StrEnum):
    """Precision modes supported for training."""
    NONE = "none"
    FP16 = "fp16"
    BF16 = "bf16"


class SchedulerKind(StrEnum):
    """Supported learning rate scheduler kinds."""
    COSINE = "cosine"
    LINEAR = "linear"
    COSINE_WITH_RESTARTS = "cosine_with_restarts"
    POLYNOMIAL = "polynomial"
    CONSTANT_WITH_WARMUP = "constant_with_warmup"
    ONE_CYCLE = "one_cycle"


class ErrorSeverity(StrEnum):
    """Severity classification for trainer exceptions."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ---------------------------------------------------------------------------
# Dataclasses — value objects
# ---------------------------------------------------------------------------

@dataclass
class GradientInfo:
    """Encapsulates gradient diagnostics for a single optimizer step."""
    norm: Optional[float] = None
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    is_finite: bool = True
    clipped: bool = False
    max_grad_norm: float = MAX_GRAD_NORM_DEFAULT
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __repr__(self) -> str:
        status = "✓" if self.is_finite else "✗"
        norm_str = f"{self.norm:.4f}" if self.norm is not None else "N/A"
        return f"GradientInfo(norm={norm_str}, finite={status}, clipped={self.clipped})"


@dataclass
class HardwareInfo:
    """Snapshot of hardware capabilities at trainer init time."""
    device_type: str = "cpu"
    device_name: str = "cpu"
    gpu_count: int = 0
    total_vram_mb: float = 0.0
    cuda_version: str = ""
    torch_version: str = ""
    is_distributed: bool = False
    world_size: int = 1
    rank: int = 0

    @classmethod
    def detect(cls) -> "HardwareInfo":
        """Auto-detect hardware from current environment."""
        try:
            import torch as _torch
            info = cls(torch_version=_torch.__version__)
            if _torch.cuda.is_available():
                info.device_type = "cuda"
                info.device_name = _torch.cuda.get_device_name(0)
                info.gpu_count = _torch.cuda.device_count()
                info.total_vram_mb = _torch.cuda.get_device_properties(0).total_mem / (1024 ** 2)
                info.cuda_version = getattr(_torch.version, "cuda", "") or ""
            elif hasattr(_torch.backends, "mps") and _torch.backends.mps.is_available():
                info.device_type = "mps"
                info.device_name = "Apple MPS"
            if _torch.distributed.is_available() and _torch.distributed.is_initialized():
                info.is_distributed = True
                info.world_size = _torch.distributed.get_world_size()
                info.rank = _torch.distributed.get_rank()
            return info
        except Exception:
            return cls()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __repr__(self) -> str:
        return (
            f"HardwareInfo(device={self.device_type}, name={self.device_name!r}, "
            f"gpus={self.gpu_count}, vram={self.total_vram_mb:.0f}MB)"
        )


@dataclass
class DataLoaderSpec:
    """Describes the resolved configuration of a DataLoader."""
    num_samples: int = 0
    num_batches: int = 0
    batch_size: int = 1
    num_workers: int = 0
    pin_memory: bool = False
    prefetch_factor: Optional[int] = None
    persistent_workers: bool = False
    drop_last: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Step & evaluation state
# ---------------------------------------------------------------------------

@dataclass
class StepState:
    """Encapsulates state and metrics for a single training step."""
    epoch: int
    step: int
    global_step: int
    loss: float
    learning_rate: float
    tokens_per_sec: float = 0.0
    grad_norm: Optional[float] = None
    grad_info: Optional[GradientInfo] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert step state to dictionary format for callback dispatching."""
        d: Dict[str, Any] = {
            "epoch": self.epoch,
            "step": self.step,
            "global_step": self.global_step,
            "loss": self.loss,
            "learning_rate": self.learning_rate,
            "tokens_per_sec": self.tokens_per_sec,
            "grad_norm": self.grad_norm,
            "timestamp": self.timestamp,
        }
        if self.grad_info is not None:
            d["grad_info"] = self.grad_info.to_dict()
        return d

    def to_json(self) -> str:
        """Serialize step state to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepState":
        """Reconstruct StepState from dictionary representation."""
        grad_info_raw = data.get("grad_info")
        grad_info = None
        if isinstance(grad_info_raw, dict):
            grad_info = GradientInfo(**{k: v for k, v in grad_info_raw.items() if k in GradientInfo.__dataclass_fields__})
        return cls(
            epoch=int(data.get("epoch", 0)),
            step=int(data.get("step", 0)),
            global_step=int(data.get("global_step", 0)),
            loss=float(data.get("loss", 0.0)),
            learning_rate=float(data.get("learning_rate", 0.0)),
            tokens_per_sec=float(data.get("tokens_per_sec", 0.0)),
            grad_norm=float(data["grad_norm"]) if data.get("grad_norm") is not None else None,
            grad_info=grad_info,
            timestamp=float(data.get("timestamp", time.time())),
        )

    def __repr__(self) -> str:
        return (
            f"StepState(epoch={self.epoch}, step={self.step}, global={self.global_step}, "
            f"loss={self.loss:.4f}, lr={self.learning_rate:.2e})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StepState):
            return NotImplemented
        return self.global_step == other.global_step and self.epoch == other.epoch

    def __hash__(self) -> int:
        return hash((self.global_step, self.epoch, self.step))


@dataclass
class EvalMetrics:
    """Encapsulates validation evaluation metrics."""
    loss: float
    perplexity: float
    additional_metrics: Dict[str, float] = field(default_factory=dict)
    num_samples: int = 0
    eval_duration_sec: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to flat dictionary format."""
        metrics: Dict[str, Any] = {
            "val_loss": self.loss,
            "perplexity": self.perplexity,
            "loss": self.loss,
            "num_samples": float(self.num_samples),
            "eval_duration_sec": self.eval_duration_sec,
        }
        metrics.update(self.additional_metrics)
        return metrics

    def to_json(self) -> str:
        """Serialize evaluation metrics to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvalMetrics":
        """Reconstruct EvalMetrics from dictionary."""
        val_loss = float(data.get("val_loss", data.get("loss", 0.0)))
        ppl = float(data.get("perplexity", 0.0))
        reserved = {"val_loss", "perplexity", "loss", "timestamp", "num_samples", "eval_duration_sec"}
        extra = {k: float(v) for k, v in data.items() if k not in reserved and isinstance(v, (int, float))}
        return cls(
            loss=val_loss,
            perplexity=ppl,
            additional_metrics=extra,
            num_samples=int(data.get("num_samples", 0)),
            eval_duration_sec=float(data.get("eval_duration_sec", 0.0)),
            timestamp=float(data.get("timestamp", time.time())),
        )

    def merge(self, other: "EvalMetrics") -> "EvalMetrics":
        """Merge two EvalMetrics (e.g. from distributed evaluation) via weighted average."""
        total_samples = self.num_samples + other.num_samples
        if total_samples == 0:
            return EvalMetrics(loss=0.0, perplexity=0.0)
        w_self = self.num_samples / max(1, total_samples)
        w_other = other.num_samples / max(1, total_samples)
        merged_loss = self.loss * w_self + other.loss * w_other
        try:
            merged_ppl = math.exp(min(PERPLEXITY_CLAMP_MAX, max(PERPLEXITY_CLAMP_MIN, merged_loss)))
        except Exception:
            merged_ppl = float("inf")
        merged_additional: Dict[str, float] = {}
        all_keys = set(self.additional_metrics) | set(other.additional_metrics)
        for k in all_keys:
            v1 = self.additional_metrics.get(k, 0.0)
            v2 = other.additional_metrics.get(k, 0.0)
            merged_additional[k] = v1 * w_self + v2 * w_other
        return EvalMetrics(
            loss=merged_loss,
            perplexity=merged_ppl,
            additional_metrics=merged_additional,
            num_samples=total_samples,
            eval_duration_sec=max(self.eval_duration_sec, other.eval_duration_sec),
        )

    def __repr__(self) -> str:
        return f"EvalMetrics(loss={self.loss:.4f}, ppl={self.perplexity:.2f}, samples={self.num_samples})"


# ---------------------------------------------------------------------------
# Trainer lifecycle state
# ---------------------------------------------------------------------------

@dataclass
class TrainerState:
    """Encapsulates the global state of the trainer lifecycle."""
    global_step: int = 0
    epoch: int = 0
    best_metric: float = float("inf")
    best_val_loss: float = float("inf")
    bad_epochs: int = 0
    is_training: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    stage: TrainerStage = TrainerStage.UNINITIALIZED
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_steps: Optional[int] = None

    def elapsed_seconds(self) -> float:
        """Calculate elapsed training time in seconds."""
        if self.start_time is None:
            return 0.0
        ref_time = self.end_time if self.end_time is not None else time.time()
        return max(0.0, ref_time - self.start_time)

    def mark_stage(self, stage: TrainerStage) -> None:
        """Transition to a new lifecycle stage."""
        self.stage = stage

    def mark_ready(self) -> None:
        """Mark trainer as ready for execution."""
        self.stage = TrainerStage.READY

    def mark_training(self) -> None:
        """Mark training as started."""
        self.is_training = True
        self.start_time = time.time()
        self.stage = TrainerStage.TRAINING

    def mark_completed(self) -> None:
        """Mark training as successfully completed."""
        self.is_training = False
        self.end_time = time.time()
        self.stage = TrainerStage.COMPLETED

    def mark_failed(self, reason: str = "") -> None:
        """Mark training as failed with optional reason."""
        self.is_training = False
        self.end_time = time.time()
        self.stage = TrainerStage.FAILED
        if reason:
            self.metadata["failure_reason"] = reason

    @property
    def should_stop_by_max_steps(self) -> bool:
        """Check if max_steps limit has been reached."""
        if self.max_steps is None:
            return False
        return self.global_step >= self.max_steps

    def to_dict(self) -> Dict[str, Any]:
        """Serialize trainer state to dictionary."""
        return {
            "global_step": self.global_step,
            "epoch": self.epoch,
            "best_metric": self.best_metric,
            "best_val_loss": self.best_val_loss,
            "bad_epochs": self.bad_epochs,
            "is_training": self.is_training,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "stage": self.stage.value if isinstance(self.stage, TrainerStage) else str(self.stage),
            "metadata": dict(self.metadata),
            "max_steps": self.max_steps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainerState":
        """Reconstruct TrainerState from dictionary."""
        stage_val = data.get("stage", TrainerStage.UNINITIALIZED.value)
        try:
            stage = TrainerStage(stage_val)
        except ValueError:
            stage = TrainerStage.UNINITIALIZED

        return cls(
            global_step=int(data.get("global_step", 0)),
            epoch=int(data.get("epoch", 0)),
            best_metric=float(data.get("best_metric", float("inf"))),
            best_val_loss=float(data.get("best_val_loss", float("inf"))),
            bad_epochs=int(data.get("bad_epochs", 0)),
            is_training=bool(data.get("is_training", False)),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            stage=stage,
            metadata=dict(data.get("metadata", {})),
            max_steps=data.get("max_steps"),
        )

    def __repr__(self) -> str:
        return (
            f"TrainerState(step={self.global_step}, epoch={self.epoch}, "
            f"stage={self.stage.value}, best_loss={self.best_val_loss:.4f})"
        )


# ---------------------------------------------------------------------------
# Checkpoint metadata
# ---------------------------------------------------------------------------

@dataclass
class CheckpointMetadata:
    """Encapsulates metadata associated with a saved checkpoint."""
    filepath: str
    step: int
    epoch: int
    val_loss: Optional[float] = None
    metric_value: Optional[float] = None
    is_best: bool = False
    checksum: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint metadata to dictionary."""
        return {
            "filepath": self.filepath,
            "step": self.step,
            "epoch": self.epoch,
            "val_loss": self.val_loss,
            "metric_value": self.metric_value,
            "is_best": self.is_best,
            "checksum": self.checksum,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointMetadata":
        """Reconstruct CheckpointMetadata from dictionary."""
        return cls(
            filepath=str(data.get("filepath", "")),
            step=int(data.get("step", 0)),
            epoch=int(data.get("epoch", 0)),
            val_loss=float(data["val_loss"]) if data.get("val_loss") is not None else None,
            metric_value=float(data["metric_value"]) if data.get("metric_value") is not None else None,
            is_best=bool(data.get("is_best", False)),
            checksum=data.get("checksum"),
            timestamp=float(data.get("timestamp", time.time())),
        )

    def __repr__(self) -> str:
        best_tag = " ★" if self.is_best else ""
        return f"CheckpointMetadata(step={self.step}, loss={self.val_loss}{best_tag})"


# ---------------------------------------------------------------------------
# Profiling summary
# ---------------------------------------------------------------------------

@dataclass
class ProfilingSummary:
    """Summarises profiling data collected during a training run."""
    total_elapsed_sec: float = 0.0
    total_steps: int = 0
    total_tokens: int = 0
    avg_tokens_per_sec: float = 0.0
    avg_step_sec: float = 0.0
    peak_cuda_mem_mb: float = 0.0
    flops_per_step: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfilingSummary":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __repr__(self) -> str:
        return (
            f"ProfilingSummary(steps={self.total_steps}, "
            f"tps={self.avg_tokens_per_sec:.0f}, "
            f"step={self.avg_step_sec:.3f}s, "
            f"peak_mem={self.peak_cuda_mem_mb:.0f}MB)"
        )


# ---------------------------------------------------------------------------
# Training metrics container
# ---------------------------------------------------------------------------

@dataclass
class TrainingMetrics:
    """Unified container for a training run's aggregate metrics."""
    total_steps: int = 0
    total_epochs: int = 0
    final_train_loss: float = float("inf")
    best_val_loss: float = float("inf")
    best_perplexity: float = float("inf")
    total_tokens_processed: int = 0
    total_training_time_sec: float = 0.0
    avg_tokens_per_sec: float = 0.0
    hardware: Optional[HardwareInfo] = None
    profiling: Optional[ProfilingSummary] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.hardware is not None:
            d["hardware"] = self.hardware.to_dict()
        if self.profiling is not None:
            d["profiling"] = self.profiling.to_dict()
        return d

    def __repr__(self) -> str:
        return (
            f"TrainingMetrics(steps={self.total_steps}, epochs={self.total_epochs}, "
            f"best_val_loss={self.best_val_loss:.4f})"
        )


# ---------------------------------------------------------------------------
# __all__
# ---------------------------------------------------------------------------

__all__ = [
    # Type aliases
    "DeviceType",
    "PrecisionType",
    "OptimizerType",
    "SchedulerType",
    "BatchType",
    "LossType",
    "MetricsDict",
    "StateDict",
    "ParamGroupList",
    # Enums
    "ExecutionMode",
    "TrainerStage",
    "PrecisionMode",
    "SchedulerKind",
    "ErrorSeverity",
    # Type guards
    "is_cuda_device",
    "is_finite_loss",
    # Constants
    "MAX_GRAD_NORM_DEFAULT",
    "DEFAULT_WARMUP_RATIO",
    "DEFAULT_LEARNING_RATE",
    "DEFAULT_WEIGHT_DECAY",
    "DEFAULT_EMA_DECAY",
    "DEFAULT_SEED",
    "DEFAULT_BLOCK_SIZE",
    "DEFAULT_LOG_INTERVAL",
    "DEFAULT_EVAL_INTERVAL",
    "PERPLEXITY_CLAMP_MIN",
    "PERPLEXITY_CLAMP_MAX",
    # Dataclasses
    "GradientInfo",
    "HardwareInfo",
    "DataLoaderSpec",
    "StepState",
    "EvalMetrics",
    "TrainerState",
    "CheckpointMetadata",
    "ProfilingSummary",
    "TrainingMetrics",
]

_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
