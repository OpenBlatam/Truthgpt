import torch.nn as nn
from typing import Dict, Any

class FusedKernelOptimizer:
    """Advanced kernel fusion optimizer for common operation patterns."""
    @staticmethod
    def can_fuse_operations(op1: str, op2: str) -> bool:
        fusable_patterns = {('layernorm', 'linear'): True, ('linear', 'activation'): True, ('attention', 'mlp'): True, ('embedding', 'positional'): True, ('dropout', 'residual'): True}
        return fusable_patterns.get((op1, op2), False)

    @staticmethod
    def estimate_fusion_benefit(op1_cost: float, op2_cost: float, fusion_overhead: float = 0.1) -> float:
        separate_cost = op1_cost + op2_cost
        fused_cost = (op1_cost + op2_cost) * (1 - fusion_overhead)
        return (separate_cost - fused_cost) / separate_cost

    @staticmethod
    def get_fusion_recommendations(model: nn.Module) -> Dict[str, Any]:
        recommendations, total_modules, fusable_pairs = [], 0, 0
        modules = list(model.named_modules())
        for i, (name1, module1) in enumerate(modules[:-1]):
            name2, module2 = modules[i + 1]
            total_modules += 1
            if isinstance(module1, nn.LayerNorm) and isinstance(module2, nn.Linear):
                fusable_pairs += 1
                recommendations.append({'type': 'layernorm_linear', 'modules': [name1, name2], 'estimated_speedup': 1.15})
            elif isinstance(module1, nn.Linear) and hasattr(module2, 'forward'):
                if 'activation' in str(type(module2)).lower():
                    fusable_pairs += 1
                    recommendations.append({'type': 'linear_activation', 'modules': [name1, name2], 'estimated_speedup': 1.08})
        return {'total_modules': total_modules, 'fusable_pairs': fusable_pairs, 'fusion_ratio': fusable_pairs / total_modules if total_modules > 0 else 0, 'recommendations': recommendations}
