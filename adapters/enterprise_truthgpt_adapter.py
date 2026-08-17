"""
Enterprise TruthGPT Adapter — Pydantic-First Architecture.

Dynamic adapter for enterprise-grade TruthGPT model lifecycle operations, optimization, and analytics.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Dual module registration for backward compatibility
_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["adapters.enterprise_truthgpt_adapter"] = _mod
    sys.modules["optimization_core.adapters.enterprise_truthgpt_adapter"] = _mod

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
    from ..modules.enterprise import (
        AdapterConfig,
        EnterpriseModelInfo,
        EnterpriseTruthGPTModel,
    )
except (ImportError, ValueError):
    try:
        from optimization_core.modules.enterprise import (
            AdapterConfig,
            EnterpriseModelInfo,
            EnterpriseTruthGPTModel,
        )
    except (ImportError, ValueError):
        AdapterConfig, EnterpriseTruthGPTModel, EnterpriseModelInfo = None, None, None

logger: logging.Logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------------------

class EnterpriseAdapterCreateResult(BaseModel):
    """Typed response model from enterprise model creation."""
    status: str = Field(default="success", description="Status of creation operation")
    model_id: str = Field(description="Unique object store ID of created enterprise model")
    info: Any = Field(description="Enterprise model metadata information")


class EnterpriseAdapterForwardResult(BaseModel):
    """Typed response model from enterprise forward pass."""
    status: str = Field(default="success", description="Status of forward operation")
    output_shape: List[int] = Field(description="Tensor output shape list")


# ---------------------------------------------------------------------------
# Core Dynamic Enterprise Adapter Class
# ---------------------------------------------------------------------------

class EnterpriseTruthGPTAdapter(BaseDynamicAdapter):
    """Enterprise TruthGPT dynamic adapter for agent tools and workflow engines."""

    name: str = "enterprise_truthgpt_adapter"
    description: str = (
        "Enterprise TruthGPT operations. Input JSON: "
        "{'action': 'create'|'info'|'optimize'|'analyze', 'kwargs': {}}"
    )

    def __init__(self, adapter_config: Optional[Any] = None, **kwargs: Any) -> None:
        super().__init__()
        if adapter_config is not None:
            self.adapter_config: Any = adapter_config
        elif AdapterConfig is not None:
            self.adapter_config = AdapterConfig()
        else:
            self.adapter_config = None

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically process enterprise model operations.

        Args:
            input_data: Input JSON dictionary payload.

        Returns:
            Dictionary response payload.

        Raises:
            RuntimeError: If ObjectStore is not initialized.
        """
        if not self.store:
            raise RuntimeError("Enterprise Adapter ObjectStore is not initialized.")

        action = input_data.get("action")
        kwargs: Dict[str, Any] = input_data.get("kwargs", {})

        try:
            if action == "create":
                if EnterpriseTruthGPTModel is None:
                    raise ImportError("EnterpriseTruthGPTModel package is unavailable.")

                config = self.adapter_config
                if "config" in kwargs and AdapterConfig is not None:
                    config = AdapterConfig.model_validate(kwargs["config"])
                elif config is None and AdapterConfig is not None:
                    config = AdapterConfig()

                model = EnterpriseTruthGPTModel(config)
                vocab_size = getattr(config, "vocab_size", 32000)

                model_id = self.store.put(
                    model,
                    kind="enterprise_model",
                    meta={"type": "TruthGPT", "vocab_size": vocab_size},
                )

                info = model.get_model_info() if hasattr(model, "get_model_info") else {}

                return EnterpriseAdapterCreateResult(
                    model_id=model_id,
                    info=info,
                ).model_dump()

            elif action == "info":
                model_id = input_data.get("model_id", "")
                if not model_id:
                    raise ValueError("model_id is required for action='info'")
                model = self.store.get(model_id)
                if not model:
                    raise ValueError(f"Model '{model_id}' not found.")
                info = model.get_model_info() if hasattr(model, "get_model_info") else {}
                info_dict = info.model_dump() if hasattr(info, "model_dump") else info
                return {"status": "success", "model_id": model_id, **info_dict}

            elif action == "optimize":
                model_id = input_data.get("model_id", "")
                if not model_id:
                    raise ValueError("model_id is required for action='optimize'")
                model = self.store.get(model_id)
                if not model:
                    raise ValueError(f"Model '{model_id}' not found.")

                if hasattr(model, "optimize_for_inference"):
                    model.optimize_for_inference()
                    return {"status": "success", "message": f"Model {model_id} optimized for inference."}
                else:
                    return {"status": "success", "message": f"Model {model_id} does not require explicit optimization."}

            elif action == "analyze":
                model_id = input_data.get("model_id", "")
                if not model_id:
                    raise ValueError("model_id is required for action='analyze'")
                model = self.store.get(model_id)
                if not model:
                    raise ValueError(f"Model '{model_id}' not found.")

                stats: Dict[str, Any] = {}
                if hasattr(model, "get_holographic_quantum_computing_stats"):
                    stats = model.get_holographic_quantum_computing_stats()
                elif hasattr(model, "get_stats"):
                    stats = model.get_stats()

                return {"status": "success", "model_id": model_id, "analysis": stats}

            else:
                raise ValueError(
                    f"Unknown truthgpt enterprise action: '{action}'. Use 'create', 'info', 'optimize', or 'analyze'."
                )
        except Exception as e:
            logger.error("Enterprise adapter error: %s", e)
            return {"status": "error", "message": str(e)}


__all__ = [
    "EnterpriseAdapterCreateResult",
    "EnterpriseAdapterForwardResult",
    "EnterpriseTruthGPTAdapter",
]
