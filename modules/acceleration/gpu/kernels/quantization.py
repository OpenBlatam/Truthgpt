import torch
import torch.nn.functional as F
import math
from typing import Dict, Any

class QuantizationKernelOptimizer:
    """Advanced quantization kernel optimizations."""
    @staticmethod
    def get_optimal_quantization_config(tensor_stats: Dict[str, float]) -> Dict[str, Any]:
        dynamic_range = tensor_stats.get('max', 1.0) - tensor_stats.get('min', -1.0)
        variance = tensor_stats.get('variance', 1.0)
        if dynamic_range < 2.0 and variance < 0.1: return {'bits': 4, 'symmetric': True, 'per_channel': False}
        elif dynamic_range < 10.0 and variance < 1.0: return {'bits': 8, 'symmetric': False, 'per_channel': True}
        else: return {'bits': 16, 'symmetric': False, 'per_channel': True}

    @staticmethod
    def estimate_quantization_error(original: torch.Tensor, quantized: torch.Tensor) -> Dict[str, float]:
        mse = F.mse_loss(original, quantized).item()
        mae = F.l1_loss(original, quantized).item()
        original_norm = torch.norm(original).item()
        error_norm = torch.norm(original - quantized).item()
        relative_error = error_norm / (original_norm + 1e-8)
        return {'mse': mse, 'mae': mae, 'relative_error': relative_error, 'snr_db': 10 * math.log10((original_norm ** 2) / (error_norm ** 2 + 1e-8))}
