"""
Training System Types, Enums, and Configuration Schemas
=======================================================
Structured dataclasses, enums, and type definitions for training configurations,
step results, metrics, and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import torch


class TrainingMode(str, Enum):
    """Execution mode for training loops."""
    STANDARD = "standard"
    DISTRIBUTED = "distributed"
    DEEPSPEED = "deepspeed"
    FSDP = "fsdp"
    OFFLOAD = "offload"


class PrecisionType(str, Enum):
    """Supported precision modes for mixed-precision training."""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    NONE = "none"

    @classmethod
    def to_torch_dtype(cls, precision: Union[str, PrecisionType]) -> Optional[torch.dtype]:
        """Convert precision identifier to corresponding torch.dtype."""
        p = str(precision).lower()
        if p in ("fp16", "float16", "16"):
            return torch.float16
        elif p in ("bf16", "bfloat16"):
            return torch.bfloat16
        elif p in ("fp32", "float32", "32"):
            return torch.float32
        return None


class CheckpointStrategy(str, Enum):
    """Retention strategies for checkpoint pruning."""
    KEEP_ALL = "keep_all"
    KEEP_BEST = "keep_best"
    KEEP_LAST_N = "keep_last_n"
    KEEP_TOP_K = "keep_top_k"
    INTERVAL = "interval"


class EMADecaySchedule(str, Enum):
    """Decay warmup scheduling algorithms for EMA."""
    CONSTANT = "constant"
    WARMUP_LINEAR = "warmup_linear"
    WARMUP_EXPONENTIAL = "warmup_exponential"


class TrackerBackend(str, Enum):
    """Supported experiment tracking backends."""
    CONSOLE = "console"
    LOGGER = "logger"
    TENSORBOARD = "tensorboard"
    WANDB = "wandb"
    MLFLOW = "mlflow"
    IN_MEMORY = "in_memory"
    NONE = "none"


@dataclass
class StepResult:
    """Detailed results from a single training step."""
    loss: float
    skipped: bool = False
    learning_rate: Optional[float] = None
    grad_norm: Optional[float] = None
    step_time_ms: Optional[float] = None
    extra_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpochResult:
    """Aggregated results from a completed training epoch."""
    epoch: int
    avg_loss: float
    num_steps: int
    elapsed_time: float
    samples_per_sec: Optional[float] = None
    eval_metrics: Optional[Dict[str, float]] = None
    extra_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationMetrics:
    """Structured metrics produced by Evaluator."""
    loss: float
    perplexity: Optional[float] = None
    accuracy: Optional[float] = None
    eval_time: float = 0.0
    num_samples: int = 0
    custom_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to a flat dictionary."""
        d = {"loss": self.loss, "eval_time": self.eval_time, "num_samples": float(self.num_samples)}
        if self.perplexity is not None:
            d["perplexity"] = self.perplexity
        if self.accuracy is not None:
            d["accuracy"] = self.accuracy
        d.update(self.custom_metrics)
        return d


@dataclass
class CheckpointMetadata:
    """Metadata describing a saved checkpoint."""
    checkpoint_path: str
    epoch: int
    step: int
    timestamp: float
    metric_value: Optional[float] = None
    metric_name: Optional[str] = None
    is_best: bool = False
    sha256: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EarlyStoppingConfig:
    """Configuration for early stopping."""
    patience: int = 5
    min_delta: float = 0.0
    mode: str = "min"  # "min" or "max"
    metric_name: str = "loss"
    restore_best_weights: bool = True


@dataclass
class TrainingLoopConfig:
    """Configuration for TrainingLoop."""
    use_amp: bool = False
    amp_dtype: Optional[Union[str, torch.dtype]] = None
    max_grad_norm: float = 1.0
    max_grad_val: Optional[float] = None
    grad_accum_steps: int = 1
    device: Optional[str] = None
    early_stopping: Optional[EarlyStoppingConfig] = None


@dataclass
class CheckpointConfig:
    """Configuration for CheckpointManager."""
    output_dir: Union[str, Path] = "./checkpoints"
    save_best: bool = True
    save_last: bool = True
    save_interval_epochs: Optional[int] = None
    save_interval_steps: Optional[int] = None
    max_to_keep: int = 3
    strategy: CheckpointStrategy = CheckpointStrategy.KEEP_TOP_K
    metric_name: str = "loss"
    mode: str = "min"
    save_optimizer: bool = True
    save_scheduler: bool = True
    save_scaler: bool = True
    save_rng: bool = True


@dataclass
class EMAConfig:
    """Configuration for EMAManager."""
    decay: float = 0.999
    enabled: bool = True
    offload_to_cpu: bool = False
    schedule: EMADecaySchedule = EMADecaySchedule.CONSTANT
    warmup_steps: int = 2000
    update_every_n_steps: int = 1


@dataclass
class EvaluatorConfig:
    """Configuration for Evaluator."""
    use_amp: bool = False
    amp_dtype: Optional[Union[str, torch.dtype]] = None
    device: Optional[str] = None
    compute_perplexity: bool = True


@dataclass
class TrackerConfig:
    """Configuration for ExperimentTracker."""
    trackers: List[str] = field(default_factory=lambda: ["console"])
    project: Optional[str] = "truthgpt"
    run_name: Optional[str] = None
    log_dir: Optional[str] = "./logs"
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class TrainingPipelineConfig:
    """Configuration for TrainingPipeline."""
    epochs: int = 10
    eval_every_epochs: int = 1
    log_every_steps: int = 10
    training_loop: TrainingLoopConfig = field(default_factory=TrainingLoopConfig)
    checkpointing: Optional[CheckpointConfig] = None
    ema: Optional[EMAConfig] = None
    evaluator: Optional[EvaluatorConfig] = None
    tracker: Optional[TrackerConfig] = None


@dataclass
class TrainingComponentInfo:
    """Metadata describing a registered training component."""
    name: str
    component_type: str
    class_name: str
    module: str
    description: str
    aliases: List[str] = field(default_factory=list)
