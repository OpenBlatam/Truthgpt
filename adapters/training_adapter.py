"""
Training Adapter — Pydantic-First Architecture.

Orchestrates the GenericTrainer via the ObjectStore.
"""
import logging
import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from .base import BaseDynamicAdapter


try:
    from ..trainers.trainer import GenericTrainer
    from ..trainers.config import TrainerConfig
except (ImportError, ValueError):
    try:
        from optimization_core.trainers.trainer import GenericTrainer
        from optimization_core.trainers.config import TrainerConfig
    except (ImportError, ValueError):
        GenericTrainer, TrainerConfig = None, None



logger = logging.getLogger(__name__)

class TrainingCreateResult(BaseModel):
    """Result of creating a trainer."""
    status: str = "success"
    trainer_id: str
    model_id: str
    data_id: Optional[str] = None

class TrainingRunResult(BaseModel):
    """Result of a training run."""
    status: str = "success"
    trainer_id: str
    message: str
    elapsed_ms: float

class TrainingAdapter(BaseDynamicAdapter):
    """
    Adapter to manage training lifecycles.
    
    Actions:
    - create: Initialize a GenericTrainer with model_id and data_id.
    - train: Start the training loop for a given trainer_id.
    """
    name: str = "training_adapter"
    description: str = (
        "Adapter to manage model training. Input JSON: "
        "{'action': 'create'|'train', 'config': {}, 'model_id': 'str', 'data_id': 'str'}"
    )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "create")
        
        if action == "create":
            raw_cfg = input_data.get("config", {})
            model_id = input_data.get("model_id")
            data_id = input_data.get("data_id")
            
            if not model_id:
                raise ValueError("model_id is required for action='create'")
            
            try:
                cfg = TrainerConfig.from_dict(raw_cfg)
            except Exception as e:
                logger.error("Invalid trainer config: %s", e)
                raise ValueError(f"Invalid trainer config: {e}")
            
            trainer = GenericTrainer(
                cfg=cfg,
                model_id=model_id,
                data_id=data_id
            )
            
            if not self.store:
                raise RuntimeError("Adapter ObjectStore is not initialized.")
                
            trainer_id = self.store.put(trainer, kind="trainer")
            
            return TrainingCreateResult(
                trainer_id=trainer_id,
                model_id=trainer.model_id or model_id,
                data_id=data_id
            ).model_dump()

        elif action == "train":
            trainer_id = input_data.get("trainer_id")
            if not trainer_id:
                raise ValueError("trainer_id is required for action='train'")
                
            if not self.store:
                raise RuntimeError("Adapter ObjectStore is not initialized for trainer lookup.")
                
            trainer: Optional[GenericTrainer] = self.store.get(trainer_id)
            if not trainer:
                raise ValueError(f"Trainer '{trainer_id}' not found in ObjectStore")
            
            start_time = time.monotonic()
            try:
                trainer.train()
            except Exception as exc:
                logger.error(f"Training failed for trainer '{trainer_id}': {exc}")
                raise RuntimeError(f"Training execution error in trainer '{trainer_id}': {exc}") from exc
                
            elapsed = (time.monotonic() - start_time) * 1000.0
            
            return TrainingRunResult(
                trainer_id=trainer_id,
                message="Training completed successfully",
                elapsed_ms=round(elapsed, 2)
            ).model_dump()

        else:
            supported_actions = ("create", "train")
            raise ValueError(f"Unknown training action '{action}'. Supported actions: {supported_actions}")


