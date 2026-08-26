"""
Composable and Validated Configuration System for the Learning Subsystem.

Provides typed dataclasses for all 16 learning paradigms with strict
validation bounds, property helpers, and JSON/dict serialization.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .exceptions import LearningConfigError

# Import paradigm-specific configurations directly from their source definitions
from .active_learning import ActiveLearningConfig
from .adaptive_learning import AdaptiveLearningConfig
from .adversarial_learning import AdversarialConfig
from .bayesian_optimization import BayesianOptimizationConfig
from .causal_inference import CausalConfig
from .continual_learning import ContinualLearningConfig
from .ensemble_learning import EnsembleConfig
from .evolutionary_computing import EvolutionaryConfig
from .federated_learning import FederatedLearningConfig
from .hyperparameter_optimization import HpoConfig
from .meta_learning import MetaLearningConfig
from .multitask_learning import MultiTaskConfig
from .nas import NASConfig
from .reinforcement_learning import RLConfig
from .self_supervised_learning import SSLConfig
from .transfer_learning import TransferLearningConfig


@dataclass
class BaseLearningConfig:
    """Base configuration common to all learning paradigms."""
    device: str = "cpu"
    seed: int = 42
    output_dir: str = "./outputs/learning"
    log_interval: int = 10
    save_checkpoints: bool = False
    checkpoint_interval: int = 50
    enable_telemetry: bool = True
    extra_options: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate base configuration invariants."""
        if self.log_interval <= 0:
            raise LearningConfigError("log_interval must be positive")
        if self.checkpoint_interval <= 0:
            raise LearningConfigError("checkpoint_interval must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a nested dictionary."""
        d = asdict(self)
        def _convert(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_convert(v) for v in obj]
            elif hasattr(obj, "value"):
                return obj.value
            return obj
        return _convert(d)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Construct configuration from dictionary."""
        valid_fields = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def save_json(self, path: Union[str, Path]) -> None:
        """Save configuration to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: Union[str, Path]) -> Any:
        """Load configuration from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class LearningPipelineConfig(BaseLearningConfig):
    """Configuration for orchestrating multi-stage learning pipelines."""
    pipeline_name: str = "default_learning_pipeline"
    stages: List[Dict[str, Any]] = field(default_factory=list)
    stop_on_stage_failure: bool = True
    shared_state: Dict[str, Any] = field(default_factory=dict)


# Backward compatibility aliases
HPOConfig = HpoConfig
HyperparameterOptimizationConfig = HpoConfig
ContinualConfig = ContinualLearningConfig
FederatedConfig = FederatedLearningConfig
SelfSupervisedConfig = SSLConfig
BayesianConfig = BayesianOptimizationConfig
MetaConfig = MetaLearningConfig
MultitaskConfig = MultiTaskConfig
PipelineConfig = LearningPipelineConfig
LearningConfig = BaseLearningConfig

__all__ = [
    'BaseLearningConfig',
    'LearningPipelineConfig',
    'ActiveLearningConfig',
    'AdaptiveLearningConfig',
    'AdversarialConfig',
    'BayesianOptimizationConfig',
    'CausalConfig',
    'ContinualLearningConfig',
    'EnsembleConfig',
    'EvolutionaryConfig',
    'FederatedLearningConfig',
    'HpoConfig',
    'MetaLearningConfig',
    'MultiTaskConfig',
    'NASConfig',
    'RLConfig',
    'SSLConfig',
    'TransferLearningConfig',
    # Backward-compat aliases
    'HPOConfig',
    'HyperparameterOptimizationConfig',
    'ContinualConfig',
    'FederatedConfig',
    'SelfSupervisedConfig',
    'BayesianConfig',
    'MetaConfig',
    'MultitaskConfig',
    'PipelineConfig',
    'LearningConfig',
]
