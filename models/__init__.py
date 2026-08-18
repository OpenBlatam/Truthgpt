"""
Unified Models System — Enterprise Lazy-Loading Edition
======================================================
Provides centralized access to model managers, builders, attention kernels,
diffusion pipelines, HuggingFace wrappers, native TruthGPT architectures,
exception types, interfaces, types, and the central MODEL_REGISTRY.
"""

from __future__ import annotations

import importlib
import sys
import threading
from typing import Any, Dict, List, Optional

__version__ = "2.5.0"

# Organized registry of modules for lazy loading
_MODULE_MAP: Dict[str, str] = {
    # Metadata
    "__version__": ".models",

    # Managers & Builders
    "ModelManager": ".model_manager",
    "create_model_manager": ".model_manager",
    "ModelBuilder": ".model_builder",
    "create_model_builder": ".model_builder",

    # Attention & Positional Encoding
    "PositionalEncoding": ".attention_utils",
    "RotaryPositionalEmbedding": ".attention_utils",
    "ALiBiPositionalEmbedding": ".attention_utils",
    "EfficientAttention": ".attention_utils",
    "AttentionOptimizer": ".attention_utils",
    "AttentionUtils": ".attention_utils",
    "create_attention_module": ".attention_utils",
    "create_attention": ".attention_utils",

    # Diffusion
    "DiffusionModelManager": ".diffusion_manager",
    "DiffusionManager": ".diffusion_manager",
    "DiffusionTrainer": ".diffusion_manager",
    "create_diffusion_manager": ".diffusion_manager",

    # HuggingFace Wrappers
    "HFTransformersModel": ".hf_transformers",
    "HFLLM": ".hf_transformers",
    "create_hf_transformers_model": ".hf_transformers",
    "HFDiffusersModel": ".hf_diffusers",
    "HFDiffusion": ".hf_diffusers",
    "create_hf_diffusers_model": ".hf_diffusers",

    # Native TruthGPT Architectures
    "TruthGPTModelConfig": ".models",
    "TruthGPTConfig": ".models",
    "TruthGPTPositionalEncoding": ".models",
    "TruthGPTSelfAttention": ".models",
    "TruthGPTFeedForward": ".models",
    "TruthGPTMLP": ".models",
    "TruthGPTTransformerLayer": ".models",
    "TruthGPTBlock": ".models",
    "TruthGPTOutput": ".models",
    "TruthGPTModel": ".models",
    "TruthGPTForCausalLM": ".models",
    "create_truthgpt_model": ".models",
    "load_truthgpt_model": ".models",
    "save_truthgpt_model": ".models",

    # Exceptions
    "ModelError": ".exceptions",
    "ModelNotFoundError": ".exceptions",
    "ModelInitializationError": ".exceptions",
    "ModelLoadError": ".exceptions",
    "ModelSaveError": ".exceptions",
    "ModelInferenceError": ".exceptions",
    "ModelConfigurationError": ".exceptions",
    "ModelOptimizationError": ".exceptions",
    "DeviceAllocationError": ".exceptions",
    "DevicePlacementError": ".exceptions",
    "UnsupportedArchitectureError": ".exceptions",
    "DependencyMissingError": ".exceptions",
    "QuantizationError": ".exceptions",
    "AttentionError": ".exceptions",
    "DiffusionError": ".exceptions",

    # Interfaces & Schemas
    "BaseModel": ".interfaces",
    "BaseModelManager": ".interfaces",
    "BaseModelBuilder": ".interfaces",
    "BaseDiffusionManager": ".interfaces",
    "BaseAttentionModule": ".interfaces",
    "BaseAttentionOptimizer": ".interfaces",
    "BaseModelProtocol": ".interfaces",
    "BaseModelManagerProtocol": ".interfaces",
    "IModel": ".interfaces",
    "IModelManager": ".interfaces",
    "IModelBuilder": ".interfaces",
    "IDiffusionManager": ".interfaces",
    "IAttentionModule": ".interfaces",
    "IAttentionOptimizer": ".interfaces",
    "ModelInfoResult": ".interfaces",
    "ModelLoadResult": ".interfaces",
    "ModelSaveResult": ".interfaces",
    "ModelInferenceResult": ".interfaces",
    "DiffusionInferenceResult": ".interfaces",
    "AttentionOptimizationResult": ".interfaces",

    # Types & Enums
    "ModelArchitectureType": ".types",
    "PrecisionType": ".types",
    "DeviceMapType": ".types",
    "AttentionBackend": ".types",
    "SchedulerType": ".types",
    "QuantizationType": ".types",
    "GenerationConfig": ".types",
    "DiffusionConfig": ".types",
    "ModelConfig": ".types",
    "ModelOutput": ".types",
    "DiffusionOutput": ".types",
    "ModelInfo": ".types",

    # Registry & Factories
    "ModelRegistry": ".registry",
    "MODEL_REGISTRY": ".registry",
    "register_model": ".registry",
    "register_model_class": ".registry",
    "get_model_class": ".registry",
    "get_registered_class": ".registry",
    "list_available_models": ".registry",
    "get_model_info": ".registry",
    "create_model": ".registry",
    "build_model": ".registry",
}

_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()


def __getattr__(name: str) -> Any:
    """
    Thread-safe lazy loader for model components.
    Loads submodules only when requested to prevent heavy ML libraries from slowing down startup.
    """
    if name == "__version__":
        return __version__

    if name in _MODULE_MAP:
        module_path = _MODULE_MAP[name]
        with _cache_lock:
            if name in _import_cache:
                return _import_cache[name]
            try:
                module = importlib.import_module(module_path, __package__)
                val = getattr(module, name)
                _import_cache[name] = val
                return val
            except (ImportError, AttributeError) as e:
                raise AttributeError(f"Could not lazy-import '{name}' from '{module_path}': {e}") from e

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> List[str]:
    """Provide directory listing for IDE autocomplete and introspection."""
    return sorted(list(_MODULE_MAP.keys()))


# Eagerly expose __all__
__all__ = list(_MODULE_MAP.keys())

# Ensure smooth resolution in sys.modules under both 'models' and 'optimization_core.models'
_mod = sys.modules.get(__name__)
if _mod:
    if __name__ == "optimization_core.models":
        sys.modules["models"] = _mod
    elif __name__ == "models":
        sys.modules["optimization_core.models"] = _mod
