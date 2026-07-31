import sys
import logging
from typing import Dict, Any, Optional
import torch
import torch.nn as nn
import torch.jit

_mod = sys.modules.get(__name__)
if _mod:
    sys.modules["optimization_core.optimizers.pytorch.jit"] = _mod

from .interfaces import PyTorchSubOptimizer


class JITOptimizer(PyTorchSubOptimizer):
    """Enterprise PyTorch JIT and Dynamo compilation optimizer."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.compilation_cache: Dict[str, nn.Module] = {}
        self.logger = logging.getLogger(__name__)

    def optimize(self, model: nn.Module) -> nn.Module:
        """Apply JIT and compilation optimizations to a PyTorch model."""
        self.logger.info("⚡ Applying JIT compilation optimizations")
        model_id = str(id(model))
        if model_id in self.compilation_cache:
            return self.compilation_cache[model_id]
        
        # Script compilation pass
        model = self._apply_script_compilation(model)
        
        # TorchDynamo compilation if available
        model = self._apply_dynamo_compilation(model)
        
        # Optimization passes
        model = self._apply_optimization_passes(model)
        
        self.compilation_cache[model_id] = model
        return model
    
    def _apply_script_compilation(self, model: nn.Module) -> nn.Module:
        """Apply TorchScript compilation with exception fallback."""
        try:
            if not isinstance(model, torch.jit.ScriptModule):
                return torch.jit.script(model)
            return model
        except Exception as e:
            self.logger.warning(f"Script compilation failed: {e}")
            return model
    
    def _apply_dynamo_compilation(self, model: nn.Module) -> nn.Module:
        """Apply PyTorch 2.x torch.compile if supported by system runtime."""
        if hasattr(torch, "compile"):
            try:
                backend = self.config.get("backend", "inductor") if self.config else "inductor"
                mode = self.config.get("mode", "default") if self.config else "default"
                compiled_model = torch.compile(model, backend=backend, mode=mode)
                return compiled_model
            except Exception as e:
                self.logger.warning(f"Torch compile failed: {e}")
        return model

    def _apply_trace_compilation(self, model: nn.Module, example_input: Optional[torch.Tensor] = None) -> nn.Module:
        """Apply trace compilation with dummy fallback tensor."""
        try:
            dummy_input = example_input if example_input is not None else torch.randn(1, 3, 224, 224)
            traced_model = torch.jit.trace(model, dummy_input)
            return traced_model
        except Exception as e:
            self.logger.warning(f"Trace compilation failed: {e}")
            return model
    
    def _apply_optimization_passes(self, model: nn.Module) -> nn.Module:
        """Apply PyTorch JIT graph optimizations (freeze, inline, optimize_for_inference)."""
        try:
            if isinstance(model, torch.jit.ScriptModule):
                model = torch.jit.freeze(model)
        except Exception as e:
            self.logger.debug(f"JIT freeze pass omitted: {e}")
        return model


PyTorchJITOptimizer = JITOptimizer
__all__ = ["JITOptimizer", "PyTorchJITOptimizer"]

