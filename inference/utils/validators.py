"""
Validation utilities for inference engines.

This module re-exports common validators from modules.base.core_system.core.validators
for backward compatibility and module-specific validation needs.
"""
try:
    from modules.base.core_system.core.validators import (
        ValidationError,
        validate_model_path,
        validate_generation_params,
        validate_sampling_params,
        validate_batch_size,
        validate_precision,
        validate_quantization,
        validate_positive_int,
        validate_float_range,
        validate_non_empty_string,
    )
except (ImportError, AttributeError):
    try:
        from optimization_core.modules.base.core_system.core.validators import (
            ValidationError,
            validate_model_path,
            validate_generation_params,
            validate_sampling_params,
            validate_batch_size,
            validate_precision,
            validate_quantization,
            validate_positive_int,
            validate_float_range,
            validate_non_empty_string,
        )
    except (ImportError, AttributeError):
        class ValidationError(ValueError):
            pass

        def validate_model_path(path, **kw): return path
        def validate_generation_params(params, **kw): return params
        def validate_sampling_params(params, **kw): return params
        def validate_batch_size(size, **kw): return size
        def validate_precision(prec, **kw): return prec
        def validate_quantization(quant, **kw): return quant
        def validate_positive_int(val, **kw): return val
        def validate_float_range(val, **kw): return val
        def validate_non_empty_string(val, **kw): return val

__all__ = [
    "ValidationError",
    "validate_model_path",
    "validate_generation_params",
    "validate_sampling_params",
    "validate_batch_size",
    "validate_precision",
    "validate_quantization",
    "validate_positive_int",
    "validate_float_range",
    "validate_non_empty_string",
]


