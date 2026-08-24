"""
🚀 TruthGPT - Enterprise ML & Optimization Framework
=====================================================
Unified, high-performance, modular system for large language models,
high-throughput inference, polyglot compiler acceleration, and multi-agent systems.

Features:
- ⚡ Fast Startup: Thread-safe lazy import system (<0.1s load time)
- 🧩 Modular Clean Architecture: SOLID principles with decoupled domain subsystems
- 🛡️ Design-by-Contract (DbC): Formal verification & integrity checking
- 🏭 Unified Factories: Standardized creation for models, optimizers, agents, compilers
- 🔍 Discovery Registries: Programmatic introspection across all components
"""

from __future__ import annotations

import sys
import threading
import importlib
from typing import Dict, Any, List, Optional
from pathlib import Path

# Setup search path
_curr_dir = str(Path(__file__).parent.resolve())
_src_dir = str(Path(__file__).parent.parent.resolve())
_root_dir = str(Path(__file__).parent.parent.parent.resolve())
_parent_root = str(Path(__file__).parent.parent.parent.parent.resolve())

for p in (_curr_dir, _src_dir, _root_dir, _parent_root):
    if p not in sys.path:
        sys.path.insert(0, p)

__version__ = "2.0.0"
__author__ = "Frontier-Model-Run / TruthGPT Team"
__license__ = "MIT"
__path__ = [_curr_dir]


# ---------------------------------------------------------------------------
# 🔍 Meta-Path Finder for Seamless Dual Import Resolution
# ---------------------------------------------------------------------------

class TruthGPTMetaFinder:
    """
    Meta path finder ensuring imports of 'truthgpt.xyz' and 'src.truthgpt.xyz'
    map cleanly to the same underlying module instances.
    """
    _resolving: set = set()

    def find_spec(self, fullname, path, target=None):
        if not (fullname.startswith("truthgpt.") or fullname.startswith("src.truthgpt.")):
            return None

        if fullname in self._resolving:
            return None

        target_name = None
        if fullname.startswith("truthgpt."):
            target_name = "src." + fullname
        elif fullname.startswith("src.truthgpt."):
            target_name = fullname[4:]

        if target_name and target_name in sys.modules and sys.modules[target_name] is not None:
            mod = sys.modules[target_name]
            sys.modules[fullname] = mod
            if hasattr(mod, '__spec__') and mod.__spec__ is not None:
                import copy
                spec = copy.copy(mod.__spec__)
                spec.name = fullname
                return spec
            import importlib.util
            return importlib.util.spec_from_loader(fullname, loader=None)

        return None


if not any(isinstance(finder, TruthGPTMetaFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, TruthGPTMetaFinder())


# ---------------------------------------------------------------------------
# 🛡️ Design-by-Contract & Formal Verification APIs
# ---------------------------------------------------------------------------

from .formal import (
    FormalContractError,
    formal_contract,
    TruthGPT_API,
    api,
    ask,
    list_papers,
    get_paper_info,
    apply_paper,
    verify_system_integrity,
)


# ---------------------------------------------------------------------------
# ⚡ Thread-Safe Lazy Import System
# ---------------------------------------------------------------------------

_ALL_LAZY_IMPORTS: Dict[str, tuple[str, str]] = {
    # Factories
    "create_optimization_core": (".optimizers.optimization_cores", "create_optimization_core"),
    "create_truthgpt_optimizer": (".optimizers", "create_truthgpt_optimizer"),
    "create_generic_optimizer": (".optimizers", "create_generic_optimizer"),
    "create_adapter": (".adapters", "create_adapter"),
    "create_core_optimizer": (".core.optimizers", "create_core_optimizer"),
    "create_specialized_optimizer": (".optimizers.specialized", "create_specialized_optimizer"),
    "create_truthgpt_optimizer_by_type": (".optimizers.truthgpt", "create_truthgpt_optimizer_by_type"),
    "UnifiedOptimizerFactory": (".optimizers.unified_optimizer_factory", "UnifiedOptimizerFactory"),
    
    # Core classes
    "UnifiedTruthGPTOptimizer": (".optimizers.core.base_truthgpt_optimizer", "UnifiedTruthGPTOptimizer"),
    "BaseTruthGPTOptimizer": (".optimizers.core.base_truthgpt_optimizer", "BaseTruthGPTOptimizer"),
    "ModernTruthGPTOptimizer": (".core.modern_truthgpt_optimizer", "ModernTruthGPTOptimizer"),
    "TruthGPTOptimizer": (".optimizers.core.base_truthgpt_optimizer", "UnifiedTruthGPTOptimizer"),
    "ProductionOptimizer": (".optimizers.production.production_optimizer", "ProductionOptimizer"),
    "DynamicFactory": (".core.dynamic_factory", "DynamicFactory"),
    "ConfigManager": (".core.config", "ConfigManager"),
    "ServiceRegistry": (".core.service_registry", "ServiceRegistry"),
    "BaseTrainer": (".core.interfaces", "BaseTrainer"),
    "BaseEvaluator": (".core.interfaces", "BaseEvaluator"),
    "BaseModelManager": (".core.interfaces", "BaseModelManager"),
    "ADAPTER_REGISTRY": (".adapters", "ADAPTER_REGISTRY"),
    "BaseDynamicAdapter": (".adapters.base", "BaseDynamicAdapter"),
    "AgentClient": (".agents.client", "AgentClient"),
    "InferenceEngine": (".inference.inference_engine", "InferenceEngine"),
    "CompilerCore": (".compiler.core.compiler_core", "CompilerCore"),
}

_SUBMODULE_NAMES = [
    "adapters", "agents", "bridges", "compiler", "config", "constants",
    "core", "factories", "formal", "formal_api", "inference", "interface", "learning",
    "managers", "models", "modules", "optimization", "optimizers",
    "persistence", "plugins", "polyglot", "registries", "security",
    "terminal", "tools", "trainers", "training", "utils", "utils_mod"
]

_import_cache: Dict[str, Any] = {}
_cache_lock = threading.RLock()


def __getattr__(name: str) -> Any:
    """Lazy import system - imports modules and symbols only when accessed."""
    if name == "__version__":
        return __version__
    if name == "__author__":
        return __author__
    if name == "__license__":
        return __license__
    if name.startswith('_'):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    with _cache_lock:
        if name in _import_cache:
            return _import_cache[name]

        # 1. Check in lazy exports dictionary
        if name in _ALL_LAZY_IMPORTS:
            module_path, symbol_name = _ALL_LAZY_IMPORTS[name]
            try:
                mod = importlib.import_module(module_path, package=__name__)
                obj = getattr(mod, symbol_name) if hasattr(mod, symbol_name) else mod
                _import_cache[name] = obj
                globals()[name] = obj
                return obj
            except Exception as e:
                try:
                    full_path = module_path.lstrip(".")
                    mod = importlib.import_module(f"truthgpt.{full_path}")
                    obj = getattr(mod, symbol_name) if hasattr(mod, symbol_name) else mod
                    _import_cache[name] = obj
                    globals()[name] = obj
                    return obj
                except Exception:
                    raise AttributeError(
                        f"Failed to lazy import '{name}' from '{module_path}.{symbol_name}': {e}"
                    ) from e

        # 2. Check if name matches a subpackage directly
        if name in _SUBMODULE_NAMES:
            try:
                mod = importlib.import_module(f".{name}", package=__name__)
                _import_cache[name] = mod
                globals()[name] = mod
                return mod
            except Exception as e:
                try:
                    mod = importlib.import_module(f"truthgpt.{name}")
                    _import_cache[name] = mod
                    globals()[name] = mod
                    return mod
                except Exception:
                    raise AttributeError(f"Failed to import submodule '{name}': {e}") from e

        available = sorted(list(_ALL_LAZY_IMPORTS.keys()) + _SUBMODULE_NAMES)[:10]
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'. "
            f"Available attributes include: {', '.join(available)}..."
        )


def __dir__() -> List[str]:
    """Return all available attributes including subpackages, lazy imports, and formal methods."""
    return sorted(list(set(globals().keys()) | set(_ALL_LAZY_IMPORTS.keys()) | set(_SUBMODULE_NAMES) | set(__all__)))


# ---------------------------------------------------------------------------
# 🏭 Unified Enterprise Factory Functions
# ---------------------------------------------------------------------------

def create_model(model_type: str = "transformer", config: Optional[dict] = None, **kwargs) -> Any:
    """Unified factory function to create model architectures."""
    model_type = model_type.lower()
    if model_type in ("transformer", "standard"):
        from .models.transformer_model import TruthGPTTransformerModel
        return TruthGPTTransformerModel(config=config, **kwargs)
    elif model_type in ("pimoe", "expert"):
        from .models.pimoe_transformer import PiMoETransformer
        return PiMoETransformer(config=config, **kwargs)
    elif model_type in ("moe", "mixture_of_experts"):
        from .models.moe_architecture import MoEArchitecture
        return MoEArchitecture(config=config, **kwargs)
    else:
        raise ValueError(f"Unknown model type: '{model_type}'. Available: ['transformer', 'pimoe', 'moe']")


def create_optimizer(optimizer_type: str = "dynamo", config: Optional[dict] = None, **kwargs) -> Any:
    """Unified factory function to create TruthGPT optimizers."""
    optimizer_type = optimizer_type.lower()
    from .optimizers.truthgpt import create_truthgpt_optimizer_by_type
    try:
        return create_truthgpt_optimizer_by_type(optimizer_type, config=config, **kwargs)
    except ValueError:
        if optimizer_type == "mcts":
            from .optimizers.mcts_optimizer import MCTSOptimizer
            return MCTSOptimizer(config=config, **kwargs)
        raise ValueError(
            f"Unknown optimizer type: '{optimizer_type}'. "
            f"Available: ['dynamo', 'inductor', 'quantization', 'supreme', 'transformer', 'mcts']"
        )


def create_compiler(compiler_type: str = "aot", config: Optional[dict] = None, **kwargs) -> Any:
    """Unified factory function to create hardware & kernel compilers."""
    from .compiler import create_compiler as _create_compiler
    return _create_compiler(compiler_type, config=config, **kwargs)


def create_inference_engine(engine_type: str = "standard", config: Optional[dict] = None, **kwargs) -> Any:
    """Unified factory function to create inference engines."""
    engine_type = engine_type.lower()
    if engine_type in ("standard", "truthgpt"):
        from .inference import TruthGPTInferenceEngine
        return TruthGPTInferenceEngine(config=config, **kwargs)
    elif engine_type in ("vllm", "high_throughput"):
        from .inference import VLLMInferenceEngine
        return VLLMInferenceEngine(config=config, **kwargs)
    else:
        raise ValueError(f"Unknown inference engine type: '{engine_type}'. Available: ['standard', 'vllm']")


def create_agent(agent_type: str = "client", config: Optional[dict] = None, **kwargs) -> Any:
    """Unified factory function to create agent instances."""
    agent_type = agent_type.lower()
    if agent_type in ("client", "orchestrator"):
        from .agents import AgentClient
        return AgentClient(config=config, **kwargs)
    elif agent_type in ("composer", "multi_user"):
        from .agents.composer.agent_composer import AgentComposer
        return AgentComposer(config=config, **kwargs)
    else:
        raise ValueError(f"Unknown agent type: '{agent_type}'. Available: ['client', 'composer']")


__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__license__",
    # Subpackages
    *_SUBMODULE_NAMES,
    # Formal Verification & Contracts
    "FormalContractError",
    "formal_contract",
    "TruthGPT_API",
    "api",
    "ask",
    "list_papers",
    "get_paper_info",
    "apply_paper",
    "verify_system_integrity",
    # Core Factories
    "create_model",
    "create_optimizer",
    "create_compiler",
    "create_inference_engine",
    "create_agent",
    # Lazy exports
    *list(_ALL_LAZY_IMPORTS.keys()),
]
