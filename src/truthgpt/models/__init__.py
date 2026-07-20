"""
Unified Models System — Lazy Loading Edition
=============================================
Prevents heavy ML libraries from loading during CLI boot.
"""

from typing import Any, Dict, List, Optional

# Organized registry of modules for lazy loading
_MODULE_MAP = {
    "ModelManager": ".model_manager",
    "ModelBuilder": ".model_manager",
    "AttentionUtils": ".attention_utils",
    "DiffusionManager": ".diffusion_manager",
    "HFTransformersModel": ".hf_transformers",
    "create_hf_transformers_model": ".hf_transformers",
    "HFDiffusersModel": ".hf_diffusers",
    "create_hf_diffusers_model": ".hf_diffusers",
}

_import_cache = {}

def __getattr__(name: str) -> Any:
    """Lazy loader for model components."""
    if name in _MODULE_MAP:
        module_path = _MODULE_MAP[name]
        try:
            # Use relative import based on current package
            import importlib
            module = importlib.import_module(module_path, __package__)
            val = getattr(module, name)
            _import_cache[name] = val
            return val
        except (ImportError, AttributeError) as e:
            if name in ["ModelBuilder", "AttentionUtils", "DiffusionManager", "HFTransformersModel", "HFDiffusersModel"]:
                return None
            raise AttributeError(f"Could not lazy-import {name} from {module_path}: {e}")
    
    if name == "build_model":
        return create_model
    
    if name == "MODEL_REGISTRY":
        return {
            "manager": {"module": "models.model_manager", "description": "Model manager"},
            "hf_transformers": {"module": "models.hf_transformers", "description": "HuggingFace Transformers model"},
        }

    raise AttributeError(f"module {__name__} has no attribute {name}")

def create_model(model_type: str = "manager", config: dict = None):
    """Factory function that triggers the actual imports when called."""
    if config is None: config = {}
    model_type = model_type.lower()
    
    if model_type == "manager":
        from .model_manager import ModelManager
        return ModelManager(**config)
    elif model_type == "hf_transformers":
        from .hf_transformers import create_hf_transformers_model
        return create_hf_transformers_model(config)
    
    raise ValueError(f"Unknown model type: {model_type}")

def list_available_models() -> List[str]:
    return ["manager", "hf_transformers"]

__all__ = list(_MODULE_MAP.keys()) + ["create_model", "build_model", "list_available_models"]
