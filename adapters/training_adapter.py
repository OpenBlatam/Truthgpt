"""
Training Adapter — Pydantic-First Architecture.

Orchestrates trainer instances (e.g. GenericTrainer) stored in the global ObjectStore.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

# Dual module registration for backward compatibility
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.training_adapter"] = _mod
    sys.modules["optimization_core.adapters.training_adapter"] = _mod

try:
    from optimization_core.adapters.base import (
        AdapterConfigurationError,
        AdapterExecutionError,
        BaseDynamicAdapter,
        ObjectNotFoundError,
    )
except ImportError:
    from .base import (
        AdapterConfigurationError,
        AdapterExecutionError,
        BaseDynamicAdapter,
        ObjectNotFoundError,
    )

try:
    from ..trainers.config import TrainerConfig
    from ..trainers.trainer import GenericTrainer
except (ImportError, ValueError):
    try:
        from optimization_core.trainers.config import TrainerConfig
        from optimization_core.trainers.trainer import GenericTrainer
    except (ImportError, ValueError):
        GenericTrainer, TrainerConfig = None, None

logger: logging.Logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------------------

class TrainingCreateResult(BaseModel):
    """Typed result from creating a trainer instance."""
    status: str = Field(default="success", description="Status of create operation")
    trainer_id: str = Field(description="Unique object store handle for created trainer")
    model_id: str = Field(description="Associated model identifier")
    data_id: Optional[str] = Field(default=None, description="Associated dataset identifier if provided")


class TrainingRunResult(BaseModel):
    """Typed result from executing a training run."""
    status: str = Field(default="success", description="Status of training run")
    trainer_id: str = Field(description="Trainer identifier executed")
    message: str = Field(default="Training completed successfully", description="Execution summary message")
    elapsed_ms: float = Field(default=0.0, description="Total elapsed training time in milliseconds")


# ---------------------------------------------------------------------------
# Core Training Adapter Class
# ---------------------------------------------------------------------------

class TrainingAdapter(BaseDynamicAdapter):
    """
    Adapter to manage trainer lifecycles across optimization_core.

    Actions:
    - create: Initialize a GenericTrainer with model_id and data_id.
    - train: Execute the training loop for a given trainer_id.
    - info: Query metadata for a given trainer_id.
    - list: List all registered trainer IDs in store.
    """

    name: str = "training_adapter"
    description: str = (
        "Adapter to manage model training. Input JSON: "
        "{'action': 'create'|'train'|'info'|'list', 'config': {}, 'model_id': 'str', 'data_id': 'str'}"
    )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically process training lifecycle operations.

        Args:
            input_data: Dictionary payload specifying action and parameters.

        Returns:
            Dictionary response serialized from corresponding Pydantic result model.

        Raises:
            ImportError: If GenericTrainer/TrainerConfig unavailable on system.
            ValueError: If missing required model_id or trainer config parameters.
            RuntimeError: If execution fails during training.
        """
        action = input_data.get("action", "create")

        if action == "create":
            if GenericTrainer is None or TrainerConfig is None:
                raise ImportError("GenericTrainer and TrainerConfig must be available to use TrainingAdapter.")

            raw_cfg = input_data.get("config", {})
            model_id = input_data.get("model_id")
            data_id = input_data.get("data_id")

            if not model_id:
                raise ValueError("model_id is required for action='create'")

            try:
                cfg = TrainerConfig.from_dict(raw_cfg)
            except Exception as e:
                logger.error("Invalid trainer config provided: %s", e)
                raise ValueError(f"Invalid trainer config: {e}") from e

            trainer = GenericTrainer(
                cfg=cfg,
                model_id=model_id,
                data_id=data_id,
            )

            if not self.store:
                raise RuntimeError("Adapter ObjectStore is not initialized.")

            trainer_id = self.store.put(trainer, kind="trainer")

            return TrainingCreateResult(
                trainer_id=trainer_id,
                model_id=getattr(trainer, "model_id", None) or model_id,
                data_id=data_id,
            ).model_dump()

        elif action == "train":
            trainer_id = input_data.get("trainer_id")
            if not trainer_id:
                raise ValueError("trainer_id is required for action='train'")

            if not self.store:
                raise RuntimeError("Adapter ObjectStore is not initialized for trainer lookup.")

            trainer: Optional[Any] = self.store.get(trainer_id)
            if not trainer:
                raise ValueError(f"Trainer '{trainer_id}' not found in ObjectStore")

            start_time = time.monotonic()
            try:
                if hasattr(trainer, "train"):
                    trainer.train()
                else:
                    raise RuntimeError(f"Object '{trainer_id}' does not implement a train() method.")
            except Exception as exc:
                logger.error("Training failed for trainer '%s': %s", trainer_id, exc)
                raise RuntimeError(f"Training execution error in trainer '{trainer_id}': {exc}") from exc

            elapsed_ms = (time.monotonic() - start_time) * 1000.0

            return TrainingRunResult(
                trainer_id=trainer_id,
                message="Training completed successfully",
                elapsed_ms=round(elapsed_ms, 2),
            ).model_dump()

        elif action == "info":
            trainer_id = input_data.get("trainer_id")
            if not trainer_id:
                raise ValueError("trainer_id is required for action='info'")
            if not self.store:
                raise RuntimeError("Adapter ObjectStore is not initialized.")
            meta = self.store.get_meta(trainer_id)
            return {"status": "success", "trainer_id": trainer_id, "meta": meta}

        elif action == "list":
            if not self.store:
                raise RuntimeError("Adapter ObjectStore is not initialized.")
            ids = self.store.list_ids(kind="trainer")
            return {"status": "success", "trainers": ids}

        else:
            supported_actions = ("create", "train", "info", "list")
            raise ValueError(f"Unknown training action '{action}'. Supported actions: {supported_actions}")


__all__ = [
    "TrainingCreateResult",
    "TrainingRunResult",
    "TrainingAdapter",
]
