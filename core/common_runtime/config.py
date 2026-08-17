"""
Configuration management - Refactored configuration system
"""

import json
import yaml
import os
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import threading
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class ConfigSource(Enum):
    """Configuration sources."""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    API = "api"
    DEFAULT = "default"

@dataclass
class OptimizationConfig:
    """Optimization configuration."""
    level: str = "standard"
    enable_quantization: bool = True
    enable_pruning: bool = True
    enable_mixed_precision: bool = True
    enable_kernel_fusion: bool = True
    max_memory_gb: float = 16.0
    max_cpu_cores: int = 8
    enable_gpu_acceleration: bool = True
    gpu_memory_fraction: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'level': self.level,
            'enable_quantization': self.enable_quantization,
            'enable_pruning': self.enable_pruning,
            'enable_mixed_precision': self.enable_mixed_precision,
            'enable_kernel_fusion': self.enable_kernel_fusion,
            'max_memory_gb': self.max_memory_gb,
            'max_cpu_cores': self.max_cpu_cores,
            'enable_gpu_acceleration': self.enable_gpu_acceleration,
            'gpu_memory_fraction': self.gpu_memory_fraction
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enable_profiling: bool = True
    profiling_interval: int = 100
    log_level: str = "INFO"
    enable_metrics_collection: bool = True
    metrics_retention_days: int = 30
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    gpu_memory_threshold: float = 90.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enable_profiling': self.enable_profiling,
            'profiling_interval': self.profiling_interval,
            'log_level': self.log_level,
            'enable_metrics_collection': self.enable_metrics_collection,
            'metrics_retention_days': self.metrics_retention_days,
            'cpu_threshold': self.cpu_threshold,
            'memory_threshold': self.memory_threshold,
            'gpu_memory_threshold': self.gpu_memory_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoringConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class PerformanceConfig:
    """Performance configuration."""
    batch_size: int = 32
    max_workers: int = 4
    enable_async_processing: bool = True
    enable_parallel_optimization: bool = True
    optimization_timeout: float = 300.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'batch_size': self.batch_size,
            'max_workers': self.max_workers,
            'enable_async_processing': self.enable_async_processing,
            'enable_parallel_optimization': self.enable_parallel_optimization,
            'optimization_timeout': self.optimization_timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config_data: Dict[str, Any] = {}
        self.config_lock = threading.RLock()
        self.update_callbacks: List[callable] = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize with defaults
        self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration."""
        self.config_data = {
            'optimization': OptimizationConfig().to_dict(),
            'monitoring': MonitoringConfig().to_dict(),
            'performance': PerformanceConfig().to_dict()
        }
    
    def load_from_file(self, filepath: str) -> bool:
        """Load configuration from file."""
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                self.logger.warning(f"Config file {filepath} not found")
                return False
            
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    self.logger.error(f"Unsupported config file format: {file_path.suffix}")
                    return False
            
            with self.config_lock:
                self._merge_config(config)
            
            self.logger.info(f"Configuration loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load config from {filepath}: {e}")
            return False
    
    def load_from_environment(self, prefix: str = "OPTIMIZATION_") -> bool:
        """Load configuration from environment variables."""
        try:
            env_config = {}
            
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    config_key = key[len(prefix):].lower()
                    
                    # Handle nested keys
                    if '_' in config_key:
                        parts = config_key.split('_')
                        current = env_config
                        for part in parts[:-1]:
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                        current[parts[-1]] = self._parse_env_value(value)
                    else:
                        env_config[config_key] = self._parse_env_value(value)
            
            if env_config:
                with self.config_lock:
                    self._merge_config(env_config)
                
                self.logger.info("Configuration loaded from environment variables")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to load config from environment: {e}")
            return False
    
    def _parse_env_value(self, value: str) -> Union[str, int, float, bool, List]:
        """Parse environment variable value to appropriate type."""
        # Boolean values
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # List values (comma-separated)
        if ',' in value:
            return [self._parse_env_value(item.strip()) for item in value.split(',')]
        
        # String value
        return value
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration with existing."""
        def deep_merge(base: Dict[str, Any], update: Dict[str, Any]):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(self.config_data, new_config)
        self._notify_update_callbacks()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key path."""
        with self.config_lock:
            keys = key_path.split('.')
            value = self.config_data
            
            try:
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                return default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value by dot-separated key path."""
        with self.config_lock:
            keys = key_path.split('.')
            config = self.config_data
            
            # Navigate to parent of target key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            self._notify_update_callbacks()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})
    
    def update_section(self, section: str, updates: Dict[str, Any]):
        """Update entire configuration section."""
        with self.config_lock:
            if section not in self.config_data:
                self.config_data[section] = {}
            
            self._merge_config({section: updates})
    
    def get_optimization_config(self) -> OptimizationConfig:
        """Get optimization configuration."""
        data = self.get_section('optimization')
        return OptimizationConfig.from_dict(data)
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        data = self.get_section('monitoring')
        return MonitoringConfig.from_dict(data)
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration."""
        data = self.get_section('performance')
        return PerformanceConfig.from_dict(data)
    
    def add_update_callback(self, callback: callable):
        """Add callback for configuration updates."""
        self.update_callbacks.append(callback)
    
    def _notify_update_callbacks(self):
        """Notify all update callbacks."""
        for callback in self.update_callbacks:
            try:
                callback(self.config_data)
            except Exception as e:
                self.logger.error(f"Error in update callback: {e}")
    
    def export_config(self, filepath: str, format: str = 'json') -> bool:
        """Export current configuration to file."""
        try:
            with open(filepath, 'w') as f:
                if format.lower() == 'json':
                    json.dump(self.config_data, f, indent=2)
                elif format.lower() in ['yaml', 'yml']:
                    yaml.dump(self.config_data, f, default_flow_style=False)
                else:
                    self.logger.error(f"Unsupported export format: {format}")
                    return False
            
            self.logger.info(f"Configuration exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """Validate current configuration."""
        errors = []
        
        # Validate optimization config
        opt_config = self.get_optimization_config()
        if opt_config.max_memory_gb <= 0:
            errors.append("max_memory_gb must be positive")
        if opt_config.max_cpu_cores <= 0:
            errors.append("max_cpu_cores must be positive")
        if not 0 < opt_config.gpu_memory_fraction <= 1:
            errors.append("gpu_memory_fraction must be between 0 and 1")
        
        # Validate monitoring config
        mon_config = self.get_monitoring_config()
        if mon_config.profiling_interval <= 0:
            errors.append("profiling_interval must be positive")
        if mon_config.cpu_threshold <= 0 or mon_config.cpu_threshold > 100:
            errors.append("cpu_threshold must be between 0 and 100")
        
        # Validate performance config
        perf_config = self.get_performance_config()
        if perf_config.batch_size <= 0:
            errors.append("batch_size must be positive")
        if perf_config.max_workers <= 0:
            errors.append("max_workers must be positive")
        
        return errors

# Factory functions
def create_config_manager(environment: Environment = Environment.DEVELOPMENT) -> ConfigManager:
    """Create a configuration manager."""
    return ConfigManager(environment)

@contextmanager
def config_context(environment: Environment = Environment.DEVELOPMENT):
    """Context manager for configuration."""
    manager = create_config_manager(environment)
    try:
        yield manager
    finally:
        # Cleanup if needed
        pass


# --- Merged from core/config.py ---

"""
Configuration management module with validation and loading.
"""
import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from .exceptions import ConfigValidationError

logger = logging.getLogger(__name__)



@dataclass
class ModelConfig:
    """Model configuration."""
    name_or_path: str = "gpt2"
    gradient_checkpointing: bool = True
    lora_enabled: bool = False
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    attention_backend: str = "sdpa"
    kv_cache_type: str = "none"
    kv_cache_block_size: int = 128
    memory_policy: str = "adaptive"


@dataclass
class OptimizerConfig:
    """Optimizer configuration alias."""
    optimizer_type: str = "adamw"
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.06
    scheduler: str = "cosine"
    fused_adamw: bool = True

@dataclass
class TrainingConfig:
    """Training configuration."""
    epochs: int = 3
    train_batch_size: int = 8
    eval_batch_size: int = 8
    grad_accum_steps: int = 2
    max_grad_norm: float = 1.0
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.06
    scheduler: str = "cosine"
    mixed_precision: str = "bf16"  # none|fp16|bf16
    early_stopping_patience: int = 2
    log_interval: int = 50
    eval_interval: int = 500
    optimizer_type: str = "adamw"
    fused_adamw: bool = True
    allow_tf32: bool = True
    torch_compile: bool = False
    compile_mode: str = "default"
    detect_anomaly: bool = False
    use_profiler: bool = False
    save_safetensors: bool = True
    select_best_by: str = "loss"  # loss|ppl
    callbacks: list[str] = field(default_factory=lambda: ["print"])


@dataclass
class DataConfig:
    """Data loading configuration."""
    source: str = "hf"  # hf|jsonl|webdataset
    dataset: str = "wikitext"
    subset: Optional[str] = "wikitext-2-raw-v1"
    text_field: str = "text"
    streaming: bool = False
    collate: str = "lm"
    max_seq_len: int = 512
    bucket_by_length: bool = False
    bucket_bins: list[int] = field(default_factory=lambda: [64, 128, 256, 512])
    num_workers: int = 4
    prefetch_factor: int = 2
    persistent_workers: bool = True


@dataclass
class HardwareConfig:
    """Hardware configuration."""
    device: str = "auto"  # auto|cuda|cpu|mps
    multi_gpu: bool = False
    ddp: bool = False


@dataclass
class CheckpointConfig:
    """Checkpoint configuration."""
    interval_steps: int = 1000
    keep_last: int = 3
    enabled: bool = True


@dataclass
class EMAConfig:
    """EMA (Exponential Moving Average) configuration."""
    enabled: bool = True
    decay: float = 0.999


@dataclass
class ResumeConfig:
    """Resume training configuration."""
    enabled: bool = False
    checkpoint_dir: Optional[str] = None


@dataclass
class TrainerConfig:
    """
    Complete trainer configuration.
    Combines all sub-configurations.
    """
    seed: int = 42
    run_name: str = "run"
    output_dir: str = "runs/run"
    
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    data: DataConfig = field(default_factory=DataConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    ema: EMAConfig = field(default_factory=EMAConfig)
    resume: ResumeConfig = field(default_factory=ResumeConfig)
    
    logging: Dict[str, Any] = field(default_factory=dict)
    eval: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "TrainerConfig":
        """Create TrainerConfig from dictionary."""
        # Extract sub-configs
        model_dict = config_dict.get("model", {})
        training_dict = config_dict.get("training", {})
        data_dict = config_dict.get("data", {})
        hardware_dict = config_dict.get("hardware", {})
        ckpt_dict = config_dict.get("checkpoint", {})
        ema_dict = config_dict.get("ema", {})
        resume_dict = config_dict.get("resume", {})
        
        # Build sub-configs
        model_cfg = ModelConfig(
            name_or_path=model_dict.get("name_or_path", "gpt2"),
            gradient_checkpointing=model_dict.get("gradient_checkpointing", True),
            lora_enabled=model_dict.get("lora", {}).get("enabled", False),
            lora_r=model_dict.get("lora", {}).get("r", 16),
            lora_alpha=model_dict.get("lora", {}).get("alpha", 32),
            lora_dropout=model_dict.get("lora", {}).get("dropout", 0.05),
            attention_backend=model_dict.get("attention", {}).get("backend", "sdpa"),
            kv_cache_type=model_dict.get("kv_cache", {}).get("type", "none"),
            kv_cache_block_size=model_dict.get("kv_cache", {}).get("block_size", 128),
            memory_policy=model_dict.get("memory", {}).get("policy", "adaptive"),
        )
        
        training_cfg = TrainingConfig(
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
            optimizer_type=training_dict.get("optimizer", {}).get("type", "adamw"),
            fused_adamw=training_dict.get("fused_adamw", True),
            allow_tf32=training_dict.get("allow_tf32", True),
            torch_compile=training_dict.get("torch_compile", False),
            compile_mode=training_dict.get("compile_mode", "default"),
            detect_anomaly=training_dict.get("detect_anomaly", False),
            use_profiler=training_dict.get("use_profiler", False),
            save_safetensors=training_dict.get("save_safetensors", True),
            select_best_by=config_dict.get("eval", {}).get("select_best_by", "loss"),
            callbacks=training_dict.get("callbacks", ["print"]),
        )
        
        data_cfg = DataConfig(
            source=data_dict.get("source", "hf"),
            dataset=data_dict.get("dataset", "wikitext"),
            subset=data_dict.get("subset", "wikitext-2-raw-v1"),
            text_field=data_dict.get("text_field", "text"),
            streaming=data_dict.get("streaming", False),
            collate=data_dict.get("collate", "lm"),
            max_seq_len=data_dict.get("max_seq_len", 512),
            bucket_by_length=data_dict.get("bucket_by_length", False),
            bucket_bins=data_dict.get("bucket_bins", [64, 128, 256, 512]),
            num_workers=data_dict.get("num_workers", 4),
            prefetch_factor=data_dict.get("prefetch_factor", 2),
            persistent_workers=data_dict.get("persistent_workers", True),
        )
        
        hardware_cfg = HardwareConfig(
            device=hardware_dict.get("device", "auto"),
            multi_gpu=hardware_dict.get("multi_gpu", False),
            ddp=hardware_dict.get("ddp", False),
        )
        
        ckpt_cfg = CheckpointConfig(
            interval_steps=ckpt_dict.get("interval_steps", 1000),
            keep_last=ckpt_dict.get("keep_last", 3),
            enabled=True,
        )
        
        ema_cfg = EMAConfig(
            enabled=ema_dict.get("enabled", True),
            decay=ema_dict.get("decay", 0.999),
        )
        
        resume_cfg = ResumeConfig(
            enabled=resume_dict.get("enabled", False),
            checkpoint_dir=resume_dict.get("checkpoint_dir"),
        )
        
        return cls(
            seed=config_dict.get("seed", 42),
            run_name=config_dict.get("run_name", "run"),
            output_dir=config_dict.get("output_dir", "runs/run"),
            model=model_cfg,
            training=training_cfg,
            data=data_cfg,
            hardware=hardware_cfg,
            checkpoint=ckpt_cfg,
            ema=ema_cfg,
            resume=resume_cfg,
            logging=config_dict.get("logging", {}),
            eval=config_dict.get("eval", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TrainerConfig to dictionary."""
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
                "attention": {"backend": self.model.attention_backend},
                "kv_cache": {
                    "type": self.model.kv_cache_type,
                    "block_size": self.model.kv_cache_block_size,
                },
                "memory": {"policy": self.model.memory_policy},
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
                "optimizer": {"type": self.training.optimizer_type},
                "fused_adamw": self.training.fused_adamw,
                "allow_tf32": self.training.allow_tf32,
                "torch_compile": self.training.torch_compile,
                "compile_mode": self.training.compile_mode,
                "detect_anomaly": self.training.detect_anomaly,
                "use_profiler": self.training.use_profiler,
                "save_safetensors": self.training.save_safetensors,
                "callbacks": self.training.callbacks,
            },
            "data": {
                "source": self.data.source,
                "dataset": self.data.dataset,
                "subset": self.data.subset,
                "text_field": self.data.text_field,
                "streaming": self.data.streaming,
                "collate": self.data.collate,
                "max_seq_len": self.data.max_seq_len,
                "bucket_by_length": self.data.bucket_by_length,
                "bucket_bins": self.data.bucket_bins,
                "num_workers": self.data.num_workers,
                "prefetch_factor": self.data.prefetch_factor,
                "persistent_workers": self.data.persistent_workers,
            },
            "hardware": {
                "device": self.hardware.device,
                "multi_gpu": self.hardware.multi_gpu,
                "ddp": self.hardware.ddp,
            },
            "checkpoint": {
                "interval_steps": self.checkpoint.interval_steps,
                "keep_last": self.checkpoint.keep_last,
            },
            "ema": {
                "enabled": self.ema.enabled,
                "decay": self.ema.decay,
            },
            "resume": {
                "enabled": self.resume.enabled,
                "checkpoint_dir": self.resume.checkpoint_dir,
            },
            "logging": self.logging,
            "eval": self.eval,
        }


class ConfigManager:
    """
    Configuration manager for loading and validating YAML configs.
    """

    @staticmethod
    def load_yaml(path: str) -> Dict[str, Any]:
        """Load YAML configuration file with validation."""
        if not os.path.exists(path):
            raise ConfigValidationError(f"Config file not found: {path}", config_key="path")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            import re
            def env_replacer(match):
                var_name = match.group(1)
                default_val = match.group(3) if match.group(3) is not None else ""
                return os.environ.get(var_name, default_val)

            content = re.sub(r"\$\{([A-Za-z0-9_]+)(:([^}]+))?\}", env_replacer, content)
            config = yaml.safe_load(content)

            if config is None:
                raise ConfigValidationError(f"Empty or invalid YAML file: {path}", config_key="file")

            logger.info(f"Successfully loaded config from {path}")
            return config

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {path}: {e}", exc_info=True)
            raise ConfigValidationError(f"YAML syntax error: {e}") from e
        except Exception as e:
            if isinstance(e, ConfigValidationError):
                raise
            logger.error(f"Error reading config file {path}: {e}", exc_info=True)
            raise ConfigValidationError(f"Error reading config file {path}: {e}") from e

    @staticmethod
    def validate_config(config_dict: Dict[str, Any]) -> bool:
        """Validate configuration dictionary."""
        required_keys = ["model", "training", "data"]

        for key in required_keys:
            if key not in config_dict:
                raise ConfigValidationError(f"Missing required configuration section: {key}", config_key=key)

        model = config_dict.get("model", {})
        if "name_or_path" not in model:
            raise ConfigValidationError("model.name_or_path is required", config_key="model.name_or_path")

        training = config_dict.get("training", {})
        if "epochs" in training and training["epochs"] < 1:
            raise ConfigValidationError("training.epochs must be >= 1", config_key="training.epochs")
        if "learning_rate" in training and training["learning_rate"] <= 0:
            raise ConfigValidationError("training.learning_rate must be > 0", config_key="training.learning_rate")

        data = config_dict.get("data", {})
        if "dataset" not in data:
            raise ConfigValidationError("data.dataset is required", config_key="data.dataset")

        logger.debug("Configuration validation passed")
        return True

    @classmethod
    def load_config(cls, path: str) -> TrainerConfig:
        """Load and validate configuration from YAML file."""
        config_dict = cls.load_yaml(path)
        cls.validate_config(config_dict)
        return TrainerConfig.from_dict(config_dict)


# Backward compatibility aliases
OptimizerConfig = TrainingConfig
OptimizationConfig = TrainingConfig
TruthGPTConfigManager = ConfigManager





