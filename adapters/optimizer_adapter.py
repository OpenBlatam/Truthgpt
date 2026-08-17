"""
Optimizer Adapters — Pydantic-First Architecture.

The ``process()`` method creates PyTorch optimizers using a model retrieved
from the global ObjectStore and returns typed Pydantic result structures containing
an ``optimizer_id`` for downstream tool consumption.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, Iterator, List, Optional, Type

import torch
from pydantic import BaseModel, Field

# Dual module registration for backward compatibility
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.optimizer_adapter"] = _mod
    sys.modules["optimization_core.adapters.optimizer_adapter"] = _mod

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

class OptimizerCreateResult(BaseModel):
    """Typed response model from an optimizer creation action."""
    status: str = Field(default="success", description="Status of creation operation")
    optimizer_id: str = Field(description="Unique object store ID for created optimizer")
    optimizer_type: str = Field(description="Type identifier of created optimizer (e.g. 'adamw')")
    model_id: str = Field(description="Target model identifier associated with optimizer")


class OptimizerStateResult(BaseModel):
    """Typed response model querying optimizer state."""
    status: str = Field(default="success", description="Status of query")
    optimizer_id: str = Field(description="Target optimizer identifier")
    type_name: str = Field(description="Class name of the PyTorch optimizer")
    param_groups: int = Field(description="Count of parameter groups managed by optimizer")
    lr: Optional[float] = Field(default=None, description="Learning rate of first parameter group")


class OptimizerListResult(BaseModel):
    """Typed response model listing available optimizers in store."""
    status: str = Field(default="success", description="Status of list operation")
    optimizers: List[str] = Field(default_factory=list, description="List of active optimizer IDs in store")


# ---------------------------------------------------------------------------
# Core Optimizer Adapter Classes
# ---------------------------------------------------------------------------

class OptimizerAdapter(BaseDynamicAdapter):
    """Base dynamic adapter for managing PyTorch optimizer instantiation and inspection."""

    name: str = "optimizer_adapter"
    description: str = (
        "Adapter to create and manage PyTorch optimizers. Input JSON: "
        "{'action': 'create'|'get_state'|'step'|'zero_grad'|'list', 'model_id': 'str', "
        "'optimizer_type': 'adamw', 'kwargs': {'lr': 1e-4}}"
    )

    OPTIMIZER_MAP: Dict[str, Type[torch.optim.Optimizer]] = {
        "adam": torch.optim.Adam,
        "adamw": torch.optim.AdamW,
        "sgd": torch.optim.SGD,
        "rmsprop": torch.optim.RMSprop,
        "adamax": torch.optim.Adamax,
        "adagrad": torch.optim.Adagrad,
        "adadelta": torch.optim.Adadelta,
        "nadam": getattr(torch.optim, "NAdam", getattr(torch.optim, "Nadam", torch.optim.Adam)),
        "lbfgs": torch.optim.LBFGS,
        "asgd": torch.optim.ASGD,
    }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically process optimizer actions based on input JSON structure.

        Args:
            input_data: Dictionary payload with action, model_id, optimizer_type, and kwargs.

        Returns:
            Dictionary response serialized from corresponding Pydantic result model.
        """
        action = input_data.get("action")
        kwargs: Dict[str, Any] = dict(input_data.get("kwargs", {}))

        try:
            if action == "create":
                model_id = input_data.get("model_id", "")
                if not model_id:
                    raise ValueError("model_id is required for action='create'")

                optimizer_type = str(input_data.get("optimizer_type", "adamw")).lower()

                if not self.store:
                    raise RuntimeError("Adapter ObjectStore is not initialized.")

                model = self.store.get(model_id)
                if model is None:
                    raise ValueError(f"Model '{model_id}' not found in ObjectStore")

                if not hasattr(model, "parameters"):
                    raise ValueError(f"Object '{model_id}' is not a valid model (missing .parameters())")

                # Try creating optimizer with optional fused flag if on CUDA and supported
                try:
                    optimizer = self.create_optimizer(
                        model.parameters(),
                        optimizer_type=optimizer_type,
                        **kwargs,
                    )
                except TypeError as exc:
                    # If fused=True failed due to parameter mismatch, retry without fused
                    if "fused" in kwargs:
                        kwargs_no_fused = {k: v for k, v in kwargs.items() if k != "fused"}
                        optimizer = self.create_optimizer(
                            model.parameters(),
                            optimizer_type=optimizer_type,
                            **kwargs_no_fused,
                        )
                    else:
                        raise exc

                optimizer_id = self.store.put(
                    optimizer,
                    kind="optimizer",
                    meta={"model_id": model_id, "type": optimizer_type, **kwargs},
                )
                return OptimizerCreateResult(
                    optimizer_id=optimizer_id,
                    optimizer_type=optimizer_type,
                    model_id=model_id,
                ).model_dump()

            elif action == "get_state":
                optimizer_id = input_data.get("optimizer_id", "")
                if not optimizer_id:
                    raise ValueError("optimizer_id is required for action='get_state'")

                if not self.store:
                    raise RuntimeError("Adapter ObjectStore is not initialized.")

                optimizer = self.store.get(optimizer_id)
                if optimizer is None:
                    raise ValueError(f"Optimizer '{optimizer_id}' not found in ObjectStore")

                state = self.get_optimizer_state(optimizer, optimizer_id)
                return state.model_dump()

            elif action == "step":
                optimizer_id = input_data.get("optimizer_id", "")
                if not optimizer_id:
                    raise ValueError("optimizer_id is required for action='step'")
                optimizer = self.store.get(optimizer_id)
                if hasattr(optimizer, "step"):
                    optimizer.step()
                    return {"status": "success", "optimizer_id": optimizer_id, "message": "Optimizer step completed."}
                raise ValueError(f"Object '{optimizer_id}' is not a valid optimizer (missing .step())")

            elif action == "zero_grad":
                optimizer_id = input_data.get("optimizer_id", "")
                if not optimizer_id:
                    raise ValueError("optimizer_id is required for action='zero_grad'")
                optimizer = self.store.get(optimizer_id)
                if hasattr(optimizer, "zero_grad"):
                    optimizer.zero_grad()
                    return {"status": "success", "optimizer_id": optimizer_id, "message": "Gradients zeroed."}
                raise ValueError(f"Object '{optimizer_id}' is not a valid optimizer (missing .zero_grad())")

            elif action == "list":
                if not self.store:
                    raise RuntimeError("Adapter ObjectStore is not initialized.")
                ids = self.store.list_ids(kind="optimizer")
                return OptimizerListResult(optimizers=ids).model_dump()

            else:
                raise ValueError(
                    f"Unknown optimizer action: '{action}'. Supported actions: 'create', 'get_state', 'step', 'zero_grad', 'list'."
                )
        except Exception as e:
            logger.error("Optimizer adapter error: %s", e)
            return {"status": "error", "message": str(e)}

    def create_optimizer(
        self,
        parameters: Iterator[torch.nn.Parameter],
        optimizer_type: str = "adamw",
        **kwargs: Any,
    ) -> torch.optim.Optimizer:
        """
        Create a PyTorch optimizer instance from registry.

        Args:
            parameters: Parameter iterator from target model.
            optimizer_type: Optimizer variant string.
            **kwargs: Extra parameters passed to optimizer constructor (e.g. lr, weight_decay).

        Returns:
            Instantiated PyTorch Optimizer.

        Raises:
            ValueError: If optimizer_type is not registered.
        """
        opt_cls = self.OPTIMIZER_MAP.get(optimizer_type.lower())
        if opt_cls is None:
            available = ", ".join(self.OPTIMIZER_MAP.keys())
            raise ValueError(f"Unknown optimizer type: '{optimizer_type}'. Available: {available}")

        return opt_cls(parameters, **kwargs)

    def get_optimizer_state(
        self, optimizer: torch.optim.Optimizer, optimizer_id: str = ""
    ) -> OptimizerStateResult:
        """
        Extract summary state metadata from a PyTorch optimizer.

        Args:
            optimizer: PyTorch Optimizer instance.
            optimizer_id: Associated object store ID string.

        Returns:
            OptimizerStateResult model instance.
        """
        lr = optimizer.param_groups[0].get("lr") if optimizer.param_groups else None
        return OptimizerStateResult(
            optimizer_id=optimizer_id,
            type_name=type(optimizer).__name__,
            param_groups=len(optimizer.param_groups),
            lr=lr,
        )


class PyTorchOptimizerAdapter(OptimizerAdapter):
    """
    PyTorch-specific optimizer adapter subclass.

    Inherits logic from ``OptimizerAdapter``, registered for compatibility and future extensions.
    """

    name: str = "pytorch_optimizer_adapter"
    description: str = (
        "Create and manage PyTorch optimizers from a model_id. Input JSON: "
        "{'action': 'create', 'model_id': 'model_xxx', 'optimizer_type': 'adamw', "
        "'kwargs': {'lr': 1e-4, 'weight_decay': 0.01}}"
    )


__all__ = [
    "OptimizerCreateResult",
    "OptimizerStateResult",
    "OptimizerListResult",
    "OptimizerAdapter",
    "PyTorchOptimizerAdapter",
]
