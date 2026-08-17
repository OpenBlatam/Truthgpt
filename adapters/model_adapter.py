"""
Model Adapters — Pydantic-First Architecture.

The ``process()`` method performs model operations, storing and retrieving
``torch.nn.Module`` instances via the global ObjectStore, returning typed
Pydantic results with lightweight ``model_id`` handles.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, List, Optional

import torch
from pydantic import BaseModel, Field, computed_field

# Dual module registration for backward compatibility
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.model_adapter"] = _mod
    sys.modules["optimization_core.adapters.model_adapter"] = _mod

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

logger: logging.Logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------------------

class ModelInfoResult(BaseModel):
    """Typed model parameter statistics."""
    num_parameters: int = Field(default=0, description="Total parameter count in model")
    trainable_parameters: int = Field(default=0, description="Trainable parameter count")
    model_type: Optional[str] = Field(default=None, description="Architecture or model type name")
    vocab_size: Optional[int] = Field(default=None, description="Vocabulary size if applicable")

    @computed_field  # type: ignore[misc]
    @property
    def trainable_pct(self) -> float:
        """Percentage of total parameters that are trainable."""
        if self.num_parameters == 0:
            return 0.0
        return round(self.trainable_parameters / self.num_parameters * 100, 2)


class ModelLoadResult(BaseModel):
    """Typed response model from a model load operation."""
    status: str = Field(default="success", description="Status of load operation")
    model_id: str = Field(description="Unique object store ID for the model")
    info: ModelInfoResult = Field(description="Model statistics and info")


class ModelSaveResult(BaseModel):
    """Typed response model from a model save operation."""
    status: str = Field(default="success", description="Status of save operation")
    message: str = Field(description="Informational status message")


class ModelListResult(BaseModel):
    """Typed response model listing available models in store."""
    status: str = Field(default="success", description="Status of list operation")
    models: List[str] = Field(default_factory=list, description="List of active model IDs in store")


# ---------------------------------------------------------------------------
# Core Model Adapter Classes
# ---------------------------------------------------------------------------

class ModelAdapter(BaseDynamicAdapter):
    """Base dynamic adapter for loading, saving, and inspecting PyTorch models."""

    name: str = "model_adapter"
    description: str = (
        "Adapter to load, save, and inspect PyTorch models. Input JSON: "
        "{'action': 'load'|'save'|'info'|'eval'|'train'|'count_parameters'|'list', 'path': 'str', 'model_id': 'str'}"
    )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically process model lifecycle operations.

        Args:
            input_data: Dictionary payload specifying action and parameters.

        Returns:
            Dictionary response serialized from corresponding Pydantic result model.

        Raises:
            ValueError: If an invalid action or missing required parameters are supplied.
        """
        action = input_data.get("action")
        kwargs: Dict[str, Any] = input_data.get("kwargs", {})

        if action == "load":
            path = input_data.get("path", "")
            model = self.load_model(path, **kwargs)
            num_params = (
                sum(p.numel() for p in model.parameters()) if hasattr(model, "parameters") else 0
            )
            model_id = self.store.put(
                model,
                kind="model",
                meta={"path": path, "num_params": num_params},
            )
            info = self.get_model_info(model)
            return ModelLoadResult(model_id=model_id, info=info).model_dump()

        elif action == "save":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='save'")
            path = input_data.get("path", "")
            if not path:
                raise ValueError("path is required for action='save'")
            model = self.store.get(model_id)
            self.save_model(model, path, **kwargs)
            return ModelSaveResult(message=f"Model successfully saved to {path}").model_dump()

        elif action == "info":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='info'")
            model = self.store.get(model_id)
            info = self.get_model_info(model)
            return {"status": "success", "model_id": model_id, **info.model_dump()}

        elif action == "eval":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='eval'")
            model = self.store.get(model_id)
            if hasattr(model, "eval"):
                model.eval()
                return {"status": "success", "model_id": model_id, "mode": "eval"}
            raise ValueError(f"Object '{model_id}' does not support eval mode.")

        elif action == "train":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='train'")
            model = self.store.get(model_id)
            if hasattr(model, "train"):
                model.train()
                return {"status": "success", "model_id": model_id, "mode": "train"}
            raise ValueError(f"Object '{model_id}' does not support train mode.")

        elif action == "count_parameters":
            model_id = input_data.get("model_id", "")
            if not model_id:
                raise ValueError("model_id is required for action='count_parameters'")
            model = self.store.get(model_id)
            info = self.get_model_info(model)
            return {"status": "success", "model_id": model_id, **info.model_dump()}

        elif action == "list":
            ids = self.store.list_ids(kind="model")
            return ModelListResult(models=ids).model_dump()

        else:
            raise ValueError(
                f"Unknown model action: '{action}'. Supported actions: 'load', 'save', 'info', 'eval', 'train', 'count_parameters', 'list'."
            )

    def load_model(self, model_path: str, **kwargs: Any) -> torch.nn.Module:
        """
        Load a model from specified path or hub identifier. Must be overridden in subclasses.

        Args:
            model_path: File path or hub name.
            **kwargs: Extra keyword options.

        Returns:
            torch.nn.Module instance.

        Raises:
            NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclasses must implement load_model().")

    def save_model(self, model: torch.nn.Module, path: str, **kwargs: Any) -> None:
        """
        Save model to specified path. Must be overridden in subclasses.

        Args:
            model: torch.nn.Module instance.
            path: Target file path or directory.
            **kwargs: Extra save parameters.

        Raises:
            NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclasses must implement save_model().")

    def get_model_info(self, model: torch.nn.Module) -> ModelInfoResult:
        """
        Extract model parameter statistics.

        Args:
            model: PyTorch module instance.

        Returns:
            ModelInfoResult instance.
        """
        if not hasattr(model, "parameters"):
            return ModelInfoResult(num_parameters=0, trainable_parameters=0)

        num_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if getattr(p, "requires_grad", False))
        return ModelInfoResult(
            num_parameters=num_params,
            trainable_parameters=trainable_params,
        )


class HuggingFaceModelAdapter(ModelAdapter):
    """Adapter for HuggingFace Transformers models."""

    name: str = "hf_model_adapter"
    description: str = (
        "Load/save HuggingFace Transformers models. Input JSON: "
        "{'action': 'load', 'path': 'meta-llama/Llama-2-7b', 'kwargs': {'device_map': 'auto'}}"
    )

    def load_model(self, model_path: str, **kwargs: Any) -> torch.nn.Module:
        """
        Load HuggingFace model using AutoModelForCausalLM.

        Args:
            model_path: Model ID or path.
            **kwargs: Extra pretrained options.

        Returns:
            Pretrained HuggingFace model.

        Raises:
            ImportError: If 'transformers' package is not installed.
            ValueError: If model_path is empty.
        """
        try:
            from transformers import AutoModelForCausalLM
        except ImportError as err:
            raise ImportError(
                "HuggingFace 'transformers' package is required for HuggingFaceModelAdapter. "
                "Install it via `pip install transformers`."
            ) from err

        if not model_path:
            raise ValueError("model_path must be specified for HuggingFaceModelAdapter load.")

        return AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=kwargs.get("torch_dtype"),
            device_map=kwargs.get("device_map"),
            trust_remote_code=kwargs.get("trust_remote_code", False),
        )

    def save_model(self, model: torch.nn.Module, path: str, **kwargs: Any) -> None:
        """
        Save HuggingFace model to directory using save_pretrained.

        Args:
            model: Model instance.
            path: Destination directory.
            **kwargs: Extra save parameters.
        """
        model_to_save = getattr(model, "module", model)
        if hasattr(model_to_save, "save_pretrained"):
            model_to_save.save_pretrained(
                path,
                safe_serialization=kwargs.get("safe_serialization", True),
            )
        else:
            torch.save(model_to_save.state_dict(), path)

    def get_model_info(self, model: torch.nn.Module) -> ModelInfoResult:
        """Get detailed HuggingFace model information including model type and vocab size."""
        base_model = getattr(model, "module", model)
        info = super().get_model_info(model)

        if hasattr(base_model, "config"):
            info.model_type = getattr(base_model.config, "model_type", "unknown")
            info.vocab_size = getattr(base_model.config, "vocab_size", 0)

        return info


__all__ = [
    "ModelInfoResult",
    "ModelLoadResult",
    "ModelSaveResult",
    "ModelListResult",
    "ModelAdapter",
    "HuggingFaceModelAdapter",
]
