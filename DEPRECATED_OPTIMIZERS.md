# Deprecated Optimizer Files

## ⚠️ Deprecation Notice

The following optimizer files have been **deprecated** and will be removed in a future version:

- `advanced_truthgpt_optimizer.py`
- `expert_truthgpt_optimizer.py`
- `ultimate_truthgpt_optimizer.py`
- `supreme_truthgpt_optimizer.py`
- `enterprise_truthgpt_optimizer.py`
- `ultra_fast_truthgpt_optimizer.py`
- `ultra_speed_truthgpt_optimizer.py`
- `hyper_speed_truthgpt_optimizer.py`
- `lightning_speed_truthgpt_optimizer.py`
- `infinite_truthgpt_optimizer.py`
- `transcendent_truthgpt_optimizer.py`

## Migration

Please migrate to the unified optimizer system:

```python
# Old (deprecated)
from advanced_truthgpt_optimizer import AdvancedTruthGPTOptimizer
optimizer = AdvancedTruthGPTOptimizer(config)

# New (recommended)
from optimizers import create_truthgpt_optimizer
optimizer = create_truthgpt_optimizer('advanced', config)
```

Or use compatibility shims (temporary):

```python
from optimizers.compatibility import AdvancedTruthGPTOptimizer
optimizer = AdvancedTruthGPTOptimizer(config)  # Shows deprecation warning
```

See `REFACTORING_OPTIMIZERS.md` for complete migration guide.







