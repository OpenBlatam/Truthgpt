# TruthGPT Optimization Core - Migration Guide

This guide details the architectural changes introduced in the recent massive refactoring (v2.0.0) of the `optimization_core` and provides instructions for migrating your legacy code to the new structure.

## Overview of Changes

To improve maintainability, discoverability, and startup times, the following major changes were implemented:
1. **Lazy Imports**: Module loading is now deferred until access.
2. **Constants Organization**: Monolithic `constants.py` was split into logical submodules.
3. **Utils Organization**: The flat `utils/` directory was grouped into logical subdirectories.
4. **Core Optimizer Consolidation**: Multiple core optimization files were consolidated into a unified `UnifiedTruthGPTOptimizer`.

---

## 1. Lazy Imports

The root `__init__.py` has been completely rewritten to use a lazy import system defined in `_lazy_imports.py`.

**Before:**
```python
from optimization_core.core.optimizers import ExtremeOptimizer, QuantumOptimizer
import optimization_core.utils.performance_utils
```

**After:**
All imports can still be accessed from the root, but they are dynamically loaded:
```python
import optimization_core
# The module will be loaded on first access:
optimizer = optimization_core.ExtremeOptimizer()
```

If you are adding new components to the core, you **must** register them in `_lazy_imports.py` rather than importing them directly in `__init__.py`.

---

## 2. Constants Migration

The monolithic `constants.py` file (previously 974 lines) has been reduced to a 75-line backward-compatibility shim. The constants have been organized into the `constants/` module.

**Old Imports (Still works but deprecated):**
```python
from optimization_core.constants import ENUM_VALUE, PERFORMANCE_METRIC
```

**New Imports (Recommended):**
```python
from optimization_core.constants.enums import ENUM_VALUE
from optimization_core.constants.performance import PERFORMANCE_METRIC
from optimization_core.constants.configurations import CONFIG_DICT
from optimization_core.constants.messages import MSG_DICT
from optimization_core.constants.version import VERSION_INFO
```

---

## 3. Utils Directory Organization

Over 100 standalone utility files in `src/truthgpt/utils/` were reorganized into logical subdirectories. All import references across the codebase have been updated. If you have custom plugins, update your imports:

| Legacy Import Path | New Import Path | Category |
| :--- | :--- | :--- |
| `utils.validation_utils` | `utils.validation.validation_utils` | Validation |
| `utils.logging_utils` | `utils.monitoring.logging_utils` | Monitoring |
| `utils.error_handling` | `utils.resilience.error_handling` | Resilience |
| `utils.deployment_utils` | `utils.deployment.deployment_utils` | Deployment |
| `utils.backup_utils` | `utils.storage.backup_utils` | Storage & Data |
| `utils.networking_utils` | `utils.networking.networking_utils` | Networking |
| `utils.performance_utils` | `utils.performance.performance_utils` | Performance |

**Example Migration:**
```python
# Old
from truthgpt.utils.logging_utils import TrainingLogger

# New
from truthgpt.utils.monitoring.logging_utils import TrainingLogger
```

---

## 4. Optimization Cores Consolidation

Thousands of lines of duplicated code across 7 core optimization files (e.g., `enhanced_optimization_core.py`, `hybrid_optimization_core.py`) were consolidated.

You should now instantiate optimizers via the unified factory:
```python
from optimization_core.optimizers.optimization_cores import create_optimization_core

# Instead of importing a specific core directly:
core = create_optimization_core("enhanced")
```

---

## Need Help?

If you encounter an `ImportError` or `ModuleNotFoundError` during migration, please check the tables above or inspect the `_lazy_imports.py` manifest to locate the new path of the required module.
