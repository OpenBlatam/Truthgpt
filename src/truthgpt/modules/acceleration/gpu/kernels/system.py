import torch
import torch.nn as nn
from typing import Optional, Tuple, Dict, Any
import warnings

from .base import AdvancedCUDAConfig
from .fusion import FusedKernelOptimizer
from .memory import MemoryCoalescingOptimizer
from .quantization import QuantizationKernelOptimizer

class EnhancedCUDAOptimizations:
    """Enhanced CUDA optimizations with advanced algorithms."""
    def __init__(self, config: Optional[AdvancedCUDAConfig] = None):
        self.config = config or AdvancedCUDAConfig()
        self.fusion_optimizer = FusedKernelOptimizer()
        self.memory_optimizer = MemoryCoalescingOptimizer()
        self.quantization_optimizer = QuantizationKernelOptimizer()

    def optimize_model_advanced(self, model: nn.Module) -> Tuple[nn.Module, Dict[str, Any]]:
        optimization_report = {'original_modules': sum(1 for _ in model.modules()), 'optimizations_applied': [], 'performance_estimates': {}}
        fusion_analysis = self.fusion_optimizer.get_fusion_recommendations(model)
        optimization_report['fusion_analysis'] = fusion_analysis
        if self.config.kernel_fusion and fusion_analysis['fusable_pairs'] > 0:
            model = self._apply_kernel_fusion(model)
            optimization_report['optimizations_applied'].append('kernel_fusion')
        if self.config.memory_coalescing:
            model = self._optimize_memory_access(model)
            optimization_report['optimizations_applied'].append('memory_coalescing')
        optimization_report['final_modules'] = sum(1 for _ in model.modules())
        optimization_report['optimization_ratio'] = len(optimization_report['optimizations_applied']) / 5
        return model, optimization_report

    def _apply_kernel_fusion(self, model: nn.Module) -> nn.Module:
        try:
            from .advanced_kernel_fusion import KernelFusionOptimizer
            return KernelFusionOptimizer().apply_kernel_fusion(model, {'fuse_layernorm_linear': True, 'fuse_attention_mlp': True})
        except ImportError:
            warnings.warn("Advanced kernel fusion not available")
            return model

    def _optimize_memory_access(self, model: nn.Module) -> nn.Module:
        for module in model.modules():
            if hasattr(module, 'weight') and isinstance(module.weight, torch.Tensor):
                if not module.weight.is_contiguous(): module.weight.data = module.weight.data.contiguous()
        return model

    def get_performance_analysis(self, model: nn.Module) -> Dict[str, Any]:
        total_params = sum(p.numel() for p in model.parameters())
        total_memory = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 ** 2)
        fusion_analysis = self.fusion_optimizer.get_fusion_recommendations(model)
        return {'model_stats': {'total_parameters': total_params, 'memory_usage_mb': total_memory, 'total_modules': sum(1 for _ in model.modules())}, 'optimization_opportunities': fusion_analysis, 'estimated_speedup': 1.0 + fusion_analysis['fusion_ratio'] * 0.2, 'memory_efficiency': 0.85 + fusion_analysis['fusion_ratio'] * 0.1}

def create_enhanced_cuda_optimizer(config: Optional[Dict[str, Any]] = None) -> EnhancedCUDAOptimizations:
    if config is None: config = {}
    cuda_config = AdvancedCUDAConfig()
    cuda_config.adaptive_block_sizing = config.get('adaptive_block_sizing', True)
    cuda_config.occupancy_optimization = config.get('occupancy_optimization', True)
    cuda_config.kernel_fusion = config.get('kernel_fusion', True)
    cuda_config.memory_coalescing = config.get('memory_coalescing', True)
    return EnhancedCUDAOptimizations(cuda_config)
