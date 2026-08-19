"""
Configuration module for trainer.

Provides composable, validated, and serializable configuration dataclasses.
Fully backward compatible with property delegates and legacy flat config attributes.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import sys
import json
import os
import logging

from .exceptions import ConfigurationError, ConfigValidationError

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for model architecture, checkpoints, and LoRA adaptation."""
    name_or_path: str = "gpt2"
    gradient_checkpointing: bool = True
    lora_enabled: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate model configuration attributes."""
        if not self.name_or_path or not isinstance(self.name_or_path, str):
            raise ConfigurationError("Model name_or_path must be a non-empty string.")
        if self.lora_r <= 0:
            raise ConfigurationError(f"lora_r must be positive, got {self.lora_r}")
        if self.lora_alpha <= 0:
            raise ConfigurationError(f"lora_alpha must be positive, got {self.lora_alpha}")
        if not (0.0 <= self.lora_dropout < 1.0):
            raise ConfigurationError(f"lora_dropout must be in range [0.0, 1.0), got {self.lora_dropout}")


@dataclass
class TrainingConfig:
    """Configuration for training hyperparameters and schedules."""
    epochs: int = 3
    train_batch_size: int = 8
    eval_batch_size: int = 8
    grad_accum_steps: int = 2
    max_grad_norm: float = 1.0
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.06
    scheduler: str = "cosine"  # cosine|linear|cosine_with_restarts|polynomial|constant_with_warmup
    mixed_precision: str = "bf16"  # none|fp16|bf16
    early_stopping_patience: int = 2
    log_interval: int = 50
    eval_interval: int = 500
    select_best_by: str = "loss"  # loss|ppl
    max_steps: Optional[int] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate training hyperparameter bounds."""
        if self.epochs <= 0:
            raise ConfigurationError(f"epochs must be positive, got {self.epochs}")
        if self.train_batch_size <= 0:
            raise ConfigurationError(f"train_batch_size must be positive, got {self.train_batch_size}")
        if self.eval_batch_size <= 0:
            raise ConfigurationError(f"eval_batch_size must be positive, got {self.eval_batch_size}")
        if self.grad_accum_steps <= 0:
            raise ConfigurationError(f"grad_accum_steps must be positive, got {self.grad_accum_steps}")
        if self.learning_rate <= 0:
            raise ConfigurationError(f"learning_rate must be positive, got {self.learning_rate}")
        if not (0.0 <= self.warmup_ratio <= 1.0):
            raise ConfigurationError(f"warmup_ratio must be in range [0.0, 1.0], got {self.warmup_ratio}")
        if self.max_steps is not None and self.max_steps <= 0:
            raise ConfigurationError(f"max_steps must be positive if specified, got {self.max_steps}")
        valid_precision = {"none", "fp16", "bf16"}
        if str(self.mixed_precision).lower() not in valid_precision:
            raise ConfigurationError(f"mixed_precision must be one of {valid_precision}, got '{self.mixed_precision}'")
        valid_best_by = {"loss", "ppl", "perplexity"}
        if str(self.select_best_by).lower() not in valid_best_by:
            raise ConfigurationError(f"select_best_by must be one of {valid_best_by}, got '{self.select_best_by}'")


@dataclass
class HardwareConfig:
    """Configuration for hardware acceleration, compilation, and data workers."""
    device: str = "auto"  # auto|cuda|cpu|mps
    multi_gpu: bool = False
    ddp: bool = False
    allow_tf32: bool = True
    torch_compile: bool = False
    compile_mode: str = "default"  # default|reduce-overhead|max-autotune
    fused_adamw: bool = True
    detect_anomaly: bool = False
    use_profiler: bool = False
    num_workers: int = 4
    prefetch_factor: int = 2
    persistent_workers: bool = True

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate hardware setting bounds."""
        if self.num_workers < 0:
            raise ConfigurationError(f"num_workers cannot be negative, got {self.num_workers}")
        if self.prefetch_factor < 1:
            raise ConfigurationError(f"prefetch_factor must be >= 1, got {self.prefetch_factor}")


@dataclass
class CheckpointConfig:
    """Configuration for checkpoint intervals, pruning, and state persistence."""
    interval_steps: int = 1000
    keep_last: int = 3
    save_safetensors: bool = True
    resume_enabled: bool = False
    resume_checkpoint_dir: Optional[str] = None
    resume_from_checkpoint: Optional[str] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate checkpointing setting bounds."""
        if self.interval_steps <= 0:
            raise ConfigurationError(f"interval_steps must be positive, got {self.interval_steps}")
        if self.keep_last < 0:
            raise ConfigurationError(f"keep_last cannot be negative, got {self.keep_last}")


@dataclass
class EMAConfig:
    """Configuration for Exponential Moving Average (EMA) parameter tracking."""
    enabled: bool = True
    decay: float = 0.999
    offload_to_cpu: bool = False

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate EMA setting bounds."""
        if not (0.0 < self.decay < 1.0):
            raise ConfigurationError(f"EMA decay must be in range (0.0, 1.0), got {self.decay}")


@dataclass
class TrainerConfig:
    """
    Master trainer configuration object composed of specialized sub-configs.
    
    Provides full backward compatibility via property delegates.
    """
    seed: int = 42
    run_name: str = "run"
    output_dir: str = "runs/run"
    
    # Composition of specialized configs
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    ema: EMAConfig = field(default_factory=EMAConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate configuration settings across composed sub-configs."""
        if not self.output_dir:
            raise ConfigurationError("output_dir must be specified")
        if not hasattr(self, "metadata") or self.metadata is None:
            self.metadata = {}
        if hasattr(self.model, "validate"):
            self.model.validate()
        if hasattr(self.training, "validate"):
            self.training.validate()
        if hasattr(self.hardware, "validate"):
            self.hardware.validate()
        if hasattr(self.checkpoint, "validate"):
            self.checkpoint.validate()
        if hasattr(self.ema, "validate"):
            self.ema.validate()

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TrainerConfig":
        """Construct a validated TrainerConfig instance from a dictionary."""
        if not isinstance(config_dict, dict):
            raise ConfigurationError(f"Expected dict for config, got {type(config_dict)}")

        seed = config_dict.get("seed", 42)
        run_name = config_dict.get("run_name", "run")
        output_dir = config_dict.get("output_dir", "runs/run")
        metadata = dict(config_dict.get("metadata", {}))

        model_dict = config_dict.get("model", {})
        model = ModelConfig(
            name_or_path=model_dict.get("name_or_path", config_dict.get("model_name", "gpt2")),
            gradient_checkpointing=model_dict.get("gradient_checkpointing", config_dict.get("gradient_checkpointing", True)),
            lora_enabled=model_dict.get("lora", {}).get("enabled", config_dict.get("lora_enabled", False)),
            lora_r=model_dict.get("lora", {}).get("r", config_dict.get("lora_r", 16)),
            lora_alpha=model_dict.get("lora", {}).get("alpha", config_dict.get("lora_alpha", 32)),
            lora_dropout=model_dict.get("lora", {}).get("dropout", config_dict.get("lora_dropout", 0.05)),
        )

        training_dict = config_dict.get("training", {})
        training = TrainingConfig(
            epochs=training_dict.get("epochs", config_dict.get("epochs", 3)),
            train_batch_size=training_dict.get("train_batch_size", config_dict.get("train_batch_size", 8)),
            eval_batch_size=training_dict.get("eval_batch_size", config_dict.get("eval_batch_size", 8)),
            grad_accum_steps=training_dict.get("grad_accum_steps", config_dict.get("grad_accum_steps", 2)),
            max_grad_norm=training_dict.get("max_grad_norm", config_dict.get("max_grad_norm", 1.0)),
            learning_rate=training_dict.get("learning_rate", config_dict.get("learning_rate", 5e-5)),
            weight_decay=training_dict.get("weight_decay", config_dict.get("weight_decay", 0.01)),
            warmup_ratio=training_dict.get("warmup_ratio", config_dict.get("warmup_ratio", 0.06)),
            scheduler=training_dict.get("scheduler", config_dict.get("scheduler", "cosine")),
            mixed_precision=training_dict.get("mixed_precision", config_dict.get("mixed_precision", "bf16")),
            early_stopping_patience=training_dict.get("early_stopping_patience", config_dict.get("early_stopping_patience", 2)),
            log_interval=training_dict.get("log_interval", config_dict.get("log_interval", 50)),
            eval_interval=training_dict.get("eval_interval", config_dict.get("eval_interval", 500)),
            select_best_by=config_dict.get("eval", {}).get("select_best_by", training_dict.get("select_best_by", config_dict.get("select_best_by", "loss"))),
            max_steps=training_dict.get("max_steps", config_dict.get("max_steps")),
        )

        hardware_dict = config_dict.get("hardware", {})
        training_dict_hw = training_dict
        hardware = HardwareConfig(
            device=hardware_dict.get("device", config_dict.get("device", "auto")),
            multi_gpu=training_dict_hw.get("multi_gpu", hardware_dict.get("multi_gpu", config_dict.get("multi_gpu", False))),
            ddp=training_dict_hw.get("ddp", hardware_dict.get("ddp", config_dict.get("ddp", False))),
            allow_tf32=training_dict_hw.get("allow_tf32", hardware_dict.get("allow_tf32", config_dict.get("allow_tf32", True))),
            torch_compile=training_dict_hw.get("torch_compile", hardware_dict.get("torch_compile", config_dict.get("torch_compile", False))),
            compile_mode=training_dict_hw.get("compile_mode", hardware_dict.get("compile_mode", config_dict.get("compile_mode", "default"))),
            fused_adamw=training_dict_hw.get("fused_adamw", hardware_dict.get("fused_adamw", config_dict.get("fused_adamw", True))),
            detect_anomaly=training_dict_hw.get("detect_anomaly", hardware_dict.get("detect_anomaly", config_dict.get("detect_anomaly", False))),
            use_profiler=training_dict_hw.get("use_profiler", hardware_dict.get("use_profiler", config_dict.get("use_profiler", False))),
            num_workers=config_dict.get("data", {}).get("num_workers", hardware_dict.get("num_workers", config_dict.get("num_workers", 4))),
            prefetch_factor=config_dict.get("data", {}).get("prefetch_factor", hardware_dict.get("prefetch_factor", config_dict.get("prefetch_factor", 2))),
            persistent_workers=config_dict.get("data", {}).get("persistent_workers", hardware_dict.get("persistent_workers", config_dict.get("persistent_workers", True))),
        )

        checkpoint_dict = config_dict.get("checkpoint", {})
        resume_dict = config_dict.get("resume", {})
        checkpoint = CheckpointConfig(
            interval_steps=checkpoint_dict.get("interval_steps", config_dict.get("ckpt_interval_steps", 1000)),
            keep_last=checkpoint_dict.get("keep_last", config_dict.get("ckpt_keep_last", 3)),
            save_safetensors=training_dict_hw.get("save_safetensors", checkpoint_dict.get("save_safetensors", config_dict.get("save_safetensors", True))),
            resume_enabled=resume_dict.get("enabled", checkpoint_dict.get("resume_enabled", config_dict.get("resume_enabled", False))),
            resume_checkpoint_dir=resume_dict.get("checkpoint_dir", checkpoint_dict.get("resume_checkpoint_dir", config_dict.get("resume_checkpoint_dir"))),
            resume_from_checkpoint=checkpoint_dict.get("resume_from_checkpoint", config_dict.get("resume_from_checkpoint")),
        )

        ema_dict = config_dict.get("ema", {})
        ema = EMAConfig(
            enabled=ema_dict.get("enabled", config_dict.get("ema_enabled", True)),
            decay=ema_dict.get("decay", config_dict.get("ema_decay", 0.999)),
            offload_to_cpu=ema_dict.get("offload_to_cpu", config_dict.get("offload_to_cpu", False)),
        )

        return cls(
            seed=seed,
            run_name=run_name,
            output_dir=output_dir,
            model=model,
            training=training,
            hardware=hardware,
            checkpoint=checkpoint,
            ema=ema,
            metadata=metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert TrainerConfig to standard dictionary representation."""
        meta = getattr(self, "metadata", {})
        return {
            "seed": self.seed,
            "run_name": self.run_name,
            "output_dir": self.output_dir,
            "model": {
                "name_or_path": self.model.name_or_path,
                "gradient_checkpointing": self.model.gradient_checkpointing,
                "lora": {
                    "enabled": self.model.lora_enabled,
                    "r": self.model.lora_r,
                    "alpha": self.model.lora_alpha,
                    "dropout": self.model.lora_dropout,
                },
            },
            "training": {
                "epochs": self.training.epochs,
                "train_batch_size": self.training.train_batch_size,
                "eval_batch_size": self.training.eval_batch_size,
                "grad_accum_steps": self.training.grad_accum_steps,
                "max_grad_norm": self.training.max_grad_norm,
                "learning_rate": self.training.learning_rate,
                "weight_decay": self.training.weight_decay,
                "warmup_ratio": self.training.warmup_ratio,
                "scheduler": self.training.scheduler,
                "mixed_precision": self.training.mixed_precision,
                "early_stopping_patience": self.training.early_stopping_patience,
                "log_interval": self.training.log_interval,
                "eval_interval": self.training.eval_interval,
                "select_best_by": self.training.select_best_by,
                "max_steps": self.training.max_steps,
            },
            "hardware": {
                "device": self.hardware.device,
                "multi_gpu": self.hardware.multi_gpu,
                "ddp": self.hardware.ddp,
                "allow_tf32": self.hardware.allow_tf32,
                "torch_compile": self.hardware.torch_compile,
                "compile_mode": self.hardware.compile_mode,
                "fused_adamw": self.hardware.fused_adamw,
                "detect_anomaly": self.hardware.detect_anomaly,
                "use_profiler": self.hardware.use_profiler,
                "num_workers": self.hardware.num_workers,
                "prefetch_factor": self.hardware.prefetch_factor,
                "persistent_workers": self.hardware.persistent_workers,
            },
            "checkpoint": {
                "interval_steps": self.checkpoint.interval_steps,
                "keep_last": self.checkpoint.keep_last,
                "save_safetensors": self.checkpoint.save_safetensors,
                "resume_enabled": self.checkpoint.resume_enabled,
                "resume_checkpoint_dir": self.checkpoint.resume_checkpoint_dir,
                "resume_from_checkpoint": self.checkpoint.resume_from_checkpoint,
            },
            "ema": {
                "enabled": self.ema.enabled,
                "decay": self.ema.decay,
                "offload_to_cpu": self.ema.offload_to_cpu,
            },
            "metadata": meta,
        }

    def to_json(self, filepath: Optional[str] = None) -> str:
        """Serialize configuration to JSON string or file."""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2)
        if filepath:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str

    @classmethod
    def from_json(cls, json_str_or_path: str) -> "TrainerConfig":
        """Deserialize configuration from JSON string or file path."""
        if os.path.exists(json_str_or_path):
            with open(json_str_or_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(json_str_or_path)
        return cls.from_dict(data)

    def to_yaml(self, filepath: Optional[str] = None) -> str:
        """Serialize configuration to YAML string or file."""
        try:
            import yaml
        except ImportError:
            raise ConfigurationError("PyYAML is required to serialize configuration to YAML.")
        data = self.to_dict()
        yaml_str = yaml.dump(data, sort_keys=False)
        if filepath:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(yaml_str)
        return yaml_str

    @classmethod
    def from_yaml(cls, yaml_str_or_path: str) -> "TrainerConfig":
        """Deserialize configuration from YAML string or file path."""
        try:
            import yaml
        except ImportError:
            raise ConfigurationError("PyYAML is required to deserialize configuration from YAML.")
        if os.path.exists(yaml_str_or_path):
            with open(yaml_str_or_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml.safe_load(yaml_str_or_path)
        return cls.from_dict(data)

    # Property delegates for flat backward compatibility
    @property
    def name_or_path(self) -> str:
        return self.model.name_or_path

    @name_or_path.setter
    def name_or_path(self, value: str) -> None:
        self.model.name_or_path = value

    @property
    def model_name(self) -> str:
        return self.model.name_or_path

    @model_name.setter
    def model_name(self, value: str) -> None:
        self.model.name_or_path = value

    @property
    def gradient_checkpointing(self) -> bool:
        return self.model.gradient_checkpointing

    @gradient_checkpointing.setter
    def gradient_checkpointing(self, value: bool) -> None:
        self.model.gradient_checkpointing = value

    @property
    def lora_enabled(self) -> bool:
        return self.model.lora_enabled

    @lora_enabled.setter
    def lora_enabled(self, value: bool) -> None:
        self.model.lora_enabled = value

    @property
    def lora_r(self) -> int:
        return self.model.lora_r

    @lora_r.setter
    def lora_r(self, value: int) -> None:
        self.model.lora_r = value

    @property
    def lora_alpha(self) -> int:
        return self.model.lora_alpha

    @lora_alpha.setter
    def lora_alpha(self, value: int) -> None:
        self.model.lora_alpha = value

    @property
    def lora_dropout(self) -> float:
        return self.model.lora_dropout

    @lora_dropout.setter
    def lora_dropout(self, value: float) -> None:
        self.model.lora_dropout = value

    @property
    def epochs(self) -> int:
        return self.training.epochs

    @epochs.setter
    def epochs(self, value: int) -> None:
        self.training.epochs = value

    @property
    def train_batch_size(self) -> int:
        return self.training.train_batch_size

    @train_batch_size.setter
    def train_batch_size(self, value: int) -> None:
        self.training.train_batch_size = value

    @property
    def eval_batch_size(self) -> int:
        return self.training.eval_batch_size

    @eval_batch_size.setter
    def eval_batch_size(self, value: int) -> None:
        self.training.eval_batch_size = value

    @property
    def grad_accum_steps(self) -> int:
        return self.training.grad_accum_steps

    @grad_accum_steps.setter
    def grad_accum_steps(self, value: int) -> None:
        self.training.grad_accum_steps = value

    @property
    def max_grad_norm(self) -> float:
        return self.training.max_grad_norm

    @max_grad_norm.setter
    def max_grad_norm(self, value: float) -> None:
        self.training.max_grad_norm = value

    @property
    def learning_rate(self) -> float:
        return self.training.learning_rate

    @learning_rate.setter
    def learning_rate(self, value: float) -> None:
        self.training.learning_rate = value

    @property
    def weight_decay(self) -> float:
        return self.training.weight_decay

    @weight_decay.setter
    def weight_decay(self, value: float) -> None:
        self.training.weight_decay = value

    @property
    def warmup_ratio(self) -> float:
        return self.training.warmup_ratio

    @warmup_ratio.setter
    def warmup_ratio(self, value: float) -> None:
        self.training.warmup_ratio = value

    @property
    def scheduler(self) -> str:
        return self.training.scheduler

    @scheduler.setter
    def scheduler(self, value: str) -> None:
        self.training.scheduler = value

    @property
    def mixed_precision(self) -> str:
        return self.training.mixed_precision

    @mixed_precision.setter
    def mixed_precision(self, value: str) -> None:
        self.training.mixed_precision = value

    @property
    def early_stopping_patience(self) -> int:
        return self.training.early_stopping_patience

    @early_stopping_patience.setter
    def early_stopping_patience(self, value: int) -> None:
        self.training.early_stopping_patience = value

    @property
    def log_interval(self) -> int:
        return self.training.log_interval

    @log_interval.setter
    def log_interval(self, value: int) -> None:
        self.training.log_interval = value

    @property
    def eval_interval(self) -> int:
        return self.training.eval_interval

    @eval_interval.setter
    def eval_interval(self, value: int) -> None:
        self.training.eval_interval = value

    @property
    def select_best_by(self) -> str:
        return self.training.select_best_by

    @select_best_by.setter
    def select_best_by(self, value: str) -> None:
        self.training.select_best_by = value

    @property
    def max_steps(self) -> Optional[int]:
        return self.training.max_steps

    @max_steps.setter
    def max_steps(self, value: Optional[int]) -> None:
        self.training.max_steps = value

    @property
    def device(self) -> str:
        return self.hardware.device

    @device.setter
    def device(self, value: str) -> None:
        self.hardware.device = value

    @property
    def multi_gpu(self) -> bool:
        return self.hardware.multi_gpu

    @multi_gpu.setter
    def multi_gpu(self, value: bool) -> None:
        self.hardware.multi_gpu = value

    @property
    def ddp(self) -> bool:
        return self.hardware.ddp

    @ddp.setter
    def ddp(self, value: bool) -> None:
        self.hardware.ddp = value

    @property
    def allow_tf32(self) -> bool:
        return self.hardware.allow_tf32

    @allow_tf32.setter
    def allow_tf32(self, value: bool) -> None:
        self.hardware.allow_tf32 = value

    @property
    def torch_compile(self) -> bool:
        return self.hardware.torch_compile

    @torch_compile.setter
    def torch_compile(self, value: bool) -> None:
        self.hardware.torch_compile = value

    @property
    def compile_mode(self) -> str:
        return self.hardware.compile_mode

    @compile_mode.setter
    def compile_mode(self, value: str) -> None:
        self.hardware.compile_mode = value

    @property
    def fused_adamw(self) -> bool:
        return self.hardware.fused_adamw

    @fused_adamw.setter
    def fused_adamw(self, value: bool) -> None:
        self.hardware.fused_adamw = value

    @property
    def detect_anomaly(self) -> bool:
        return self.hardware.detect_anomaly

    @detect_anomaly.setter
    def detect_anomaly(self, value: bool) -> None:
        self.hardware.detect_anomaly = value

    @property
    def use_profiler(self) -> bool:
        return self.hardware.use_profiler

    @use_profiler.setter
    def use_profiler(self, value: bool) -> None:
        self.hardware.use_profiler = value

    @property
    def num_workers(self) -> int:
        return self.hardware.num_workers

    @num_workers.setter
    def num_workers(self, value: int) -> None:
        self.hardware.num_workers = value

    @property
    def prefetch_factor(self) -> int:
        return self.hardware.prefetch_factor

    @prefetch_factor.setter
    def prefetch_factor(self, value: int) -> None:
        self.hardware.prefetch_factor = value

    @property
    def persistent_workers(self) -> bool:
        return self.hardware.persistent_workers

    @persistent_workers.setter
    def persistent_workers(self, value: bool) -> None:
        self.hardware.persistent_workers = value

    @property
    def ckpt_interval_steps(self) -> int:
        return self.checkpoint.interval_steps

    @ckpt_interval_steps.setter
    def ckpt_interval_steps(self, value: int) -> None:
        self.checkpoint.interval_steps = value

    @property
    def ckpt_keep_last(self) -> int:
        return self.checkpoint.keep_last

    @ckpt_keep_last.setter
    def ckpt_keep_last(self, value: int) -> None:
        self.checkpoint.keep_last = value

    @property
    def save_safetensors(self) -> bool:
        return self.checkpoint.save_safetensors

    @save_safetensors.setter
    def save_safetensors(self, value: bool) -> None:
        self.checkpoint.save_safetensors = value

    @property
    def resume_enabled(self) -> bool:
        return self.checkpoint.resume_enabled

    @resume_enabled.setter
    def resume_enabled(self, value: bool) -> None:
        self.checkpoint.resume_enabled = value

    @property
    def resume_checkpoint_dir(self) -> Optional[str]:
        return self.checkpoint.resume_checkpoint_dir

    @resume_checkpoint_dir.setter
    def resume_checkpoint_dir(self, value: Optional[str]) -> None:
        self.checkpoint.resume_checkpoint_dir = value

    @property
    def resume_from_checkpoint(self) -> Optional[str]:
        return self.checkpoint.resume_from_checkpoint

    @resume_from_checkpoint.setter
    def resume_from_checkpoint(self, value: Optional[str]) -> None:
        self.checkpoint.resume_from_checkpoint = value

    @property
    def ema_enabled(self) -> bool:
        return self.ema.enabled

    @ema_enabled.setter
    def ema_enabled(self, value: bool) -> None:
        self.ema.enabled = value

    @property
    def ema_decay(self) -> float:
        return self.ema.decay

    @ema_decay.setter
    def ema_decay(self, value: float) -> None:
        self.ema.decay = value

    @property
    def optimizer_type(self) -> str:
        meta = getattr(self, "metadata", {})
        return meta.get("optimizer_type", "adamw")

    @optimizer_type.setter
    def optimizer_type(self, value: str) -> None:
        if not hasattr(self, "metadata") or self.metadata is None:
            self.metadata = {}
        self.metadata["optimizer_type"] = value


__all__ = [
    "ModelConfig",
    "TrainingConfig",
    "HardwareConfig",
    "CheckpointConfig",
    "EMAConfig",
    "TrainerConfig",
]

_mod = sys.modules.get(__name__)
if _mod:
    if __name__.startswith("optimization_core.trainers."):
        sys.modules["trainers." + __name__[len("optimization_core.trainers."):]] = _mod
    elif __name__.startswith("trainers."):
        sys.modules["optimization_core.trainers." + __name__[len("trainers."):]] = _mod
