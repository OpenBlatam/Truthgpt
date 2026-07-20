"""
Model service for managing model lifecycle.
"""
import logging
from typing import Dict, Any, Optional

import torch

from .base_service import BaseService
from ..event_system import EventType
from ...models.model_manager import ModelManager

logger = logging.getLogger(__name__)


class ModelService(BaseService):
    """
    Service for model management operations.
    """
    
    def __init__(self, **kwargs):
        """Initialize model service."""
        super().__init__(name="ModelService", **kwargs)
        self.model_manager: Optional[ModelManager] = None
    
    def _do_initialize(self) -> None:
        """Initialize model manager."""
        self.model_manager = ModelManager()
    
    def load_model(
        self,
        model_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> torch.nn.Module:
        """
        Load a model.
        
        Args:
            model_name: Model name or path
            config: Optional model configuration
        
        Returns:
            Loaded model
        """
        config = config or {}
        
        try:
            model = self.model_manager.load_model(
                model_name=model_name,
                torch_dtype=config.get("torch_dtype"),
                device_map=config.get("device_map"),
                gradient_checkpointing=config.get("gradient_checkpointing", True),
                lora_config=config.get("lora"),
            )
            
            self.emit(EventType.MODEL_LOADED, {
                "model_name": model_name,
                "config": config,
            })
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}", exc_info=True)
            self.emit(EventType.ERROR_OCCURRED, {
                "error": str(e),
                "operation": "load_model",
            })
            raise
    
    def save_model(
        self,
        model: torch.nn.Module,
        path: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save a model.
        
        Args:
            model: Model to save
            path: Save path
            config: Optional save configuration
        """
        config = config or {}
        
        try:
            self.model_manager.save_model(
                model=model,
                path=path,
                tokenizer=config.get("tokenizer"),
                safe_serialization=config.get("safe_serialization", True),
            )
            
            self.emit(EventType.MODEL_SAVED, {
                "path": path,
                "config": config,
            })
            
        except Exception as e:
            logger.error(f"Failed to save model to {path}: {e}", exc_info=True)
            self.emit(EventType.ERROR_OCCURRED, {
                "error": str(e),
                "operation": "save_model",
            })
            raise
    
    def optimize_model(
        self,
        model: torch.nn.Module,
        optimizations: list[str]
    ) -> torch.nn.Module:
        """
        Optimize a model.
        
        Args:
            model: Model to optimize
            optimizations: List of optimization names
        
        Returns:
            Optimized model
        """
        from ...optimization.performance_optimizer import PerformanceOptimizer
        
        optimizer = PerformanceOptimizer()
        optimized = optimizer.optimize_model(model, optimizations)
        
        return optimized


