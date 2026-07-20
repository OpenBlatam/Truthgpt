"""
Configuration module for trainer.

Separates configuration from implementation for better modularity.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ModelConfig:
    """Configuration for model settings."""
    name_or_path: str = "gpt2"
    gradient_checkpointing: bool = True
    lora_enabled: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05


@dataclass
class TrainingConfig:
    """Configuration for training hyperparameters."""
    epochs: int = 3
    train_batch_size: int = 8
    eval_batch_size: int = 8
    grad_accum_steps: int = 2
    max_grad_norm: float = 1.0
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.06
    scheduler: str = "cosine"  # cosine|linear
    mixed_precision: str = "bf16"  # none|fp16|bf16
    early_stopping_patience: int = 2
    log_interval: int = 50
    eval_interval: int = 500
    select_best_by: str = "loss"  # loss|ppl


@dataclass
class HardwareConfig:
    """Configuration for hardware settings."""
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


@dataclass
class CheckpointConfig:
    """Configuration for checkpointing."""
    interval_steps: int = 1000
    keep_last: int = 3
    save_safetensors: bool = True
    resume_enabled: bool = False
    resume_checkpoint_dir: Optional[str] = None
    resume_from_checkpoint: Optional[str] = None


@dataclass
class EMAConfig:
    """Configuration for Exponential Moving Average."""
    enabled: bool = True
    decay: float = 0.999


@dataclass
class TrainerConfig:
    """
    Complete trainer configuration composed of specialized configs.
    
    This follows the composition pattern for better modularity.
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
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TrainerConfig":
        """
        Create TrainerConfig from dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            TrainerConfig instance
        """
        # Extract top-level config
        seed = config_dict.get("seed", 42)
        run_name = config_dict.get("run_name", "run")
        output_dir = config_dict.get("output_dir", "runs/run")
        metadata = config_dict.get("metadata", {})
        
        # Extract model config
        model_dict = config_dict.get("model", {})
        model = ModelConfig(
            name_or_path=model_dict.get("name_or_path", "gpt2"),
            gradient_checkpointing=model_dict.get("gradient_checkpointing", True),
            lora_enabled=model_dict.get("lora", {}).get("enabled", False),
            lora_r=model_dict.get("lora", {}).get("r", 16),
            lora_alpha=model_dict.get("lora", {}).get("alpha", 32),
            lora_dropout=model_dict.get("lora", {}).get("dropout", 0.05),
        )
        
        # Extract training config
        training_dict = config_dict.get("training", {})
        training = TrainingConfig(
            epochs=training_dict.get("epochs", 3),
            train_batch_size=training_dict.get("train_batch_size", 8),
            eval_batch_size=training_dict.get("eval_batch_size", 8),
            grad_accum_steps=training_dict.get("grad_accum_steps", 2),
            max_grad_norm=training_dict.get("max_grad_norm", 1.0),
            learning_rate=training_dict.get("learning_rate", 5e-5),
            weight_decay=training_dict.get("weight_decay", 0.01),
            warmup_ratio=training_dict.get("warmup_ratio", 0.06),
            scheduler=training_dict.get("scheduler", "cosine"),
            mixed_precision=training_dict.get("mixed_precision", "bf16"),
            early_stopping_patience=training_dict.get("early_stopping_patience", 2),
            log_interval=training_dict.get("log_interval", 50),
            eval_interval=training_dict.get("eval_interval", 500),
            select_best_by=config_dict.get("eval", {}).get("select_best_by", "loss"),
        )
        
        # Extract hardware config
        hardware_dict = config_dict.get("hardware", {})
        training_dict_hw = training_dict  # Also check training dict for hardware settings
        hardware = HardwareConfig(
            device=hardware_dict.get("device", "auto"),
            multi_gpu=training_dict_hw.get("multi_gpu", False),
            ddp=training_dict_hw.get("ddp", False),
            allow_tf32=training_dict_hw.get("allow_tf32", True),
            torch_compile=training_dict_hw.get("torch_compile", False),
            compile_mode=training_dict_hw.get("compile_mode", "default"),
            fused_adamw=training_dict_hw.get("fused_adamw", True),
            detect_anomaly=training_dict_hw.get("detect_anomaly", False),
            use_profiler=training_dict_hw.get("use_profiler", False),
            num_workers=config_dict.get("data", {}).get("num_workers", 4),
            prefetch_factor=config_dict.get("data", {}).get("prefetch_factor", 2),
            persistent_workers=config_dict.get("data", {}).get("persistent_workers", True),
        )
        
        # Extract checkpoint config
        checkpoint_dict = config_dict.get("checkpoint", {})
        resume_dict = config_dict.get("resume", {})
        checkpoint = CheckpointConfig(
            interval_steps=checkpoint_dict.get("interval_steps", 1000),
            keep_last=checkpoint_dict.get("keep_last", 3),
            save_safetensors=training_dict_hw.get("save_safetensors", True),
            resume_enabled=resume_dict.get("enabled", False),
            resume_checkpoint_dir=resume_dict.get("checkpoint_dir"),
            resume_from_checkpoint=None,
        )
        
        # Extract EMA config
        ema_dict = config_dict.get("ema", {})
        ema = EMAConfig(
            enabled=ema_dict.get("enabled", True),
            decay=ema_dict.get("decay", 0.999),
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
        """Convert config to dictionary."""
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
            },
            "checkpoint": {
                "interval_steps": self.checkpoint.interval_steps,
                "keep_last": self.checkpoint.keep_last,
                "save_safetensors": self.checkpoint.save_safetensors,
            },
            "ema": {
                "enabled": self.ema.enabled,
                "decay": self.ema.decay,
            },
            "metadata": self.metadata,
        }



