import os
import shutil
import re
from pathlib import Path

# Base directory
BASE_DIR = Path(r"C:\blatam-academy\agents\backend\onyx\server\features\Frontier-Model-run-polyglot\scripts\TruthGPT-main\optimization_core\polyglot_core")

# File to category mapping
MAPPING = {
    "backend.py": "core",
    "cache.py": "core",
    "attention.py": "core",
    "compression.py": "core",
    "inference.py": "core",
    "tokenization.py": "core",
    "quantization.py": "core",
    "factory.py": "core",
    "builder.py": "core",
    "registry.py": "core",
    
    "batch.py": "processing",
    "streaming.py": "processing",
    "serialization.py": "processing",
    
    "profiling.py": "monitoring",
    "metrics.py": "monitoring",
    "health.py": "monitoring",
    "observability.py": "monitoring",
    "telemetry.py": "monitoring",
    "alerts.py": "monitoring",
    
    "rate_limiting.py": "infrastructure",
    "circuit_breaker.py": "infrastructure",
    "distributed.py": "infrastructure",
    "async_core.py": "infrastructure",
    "api.py": "infrastructure",
    "service_discovery.py": "infrastructure",
    "load_balancer.py": "infrastructure",
    
    "logging.py": "utils",
    "validation.py": "utils",
    "errors.py": "utils",
    "context.py": "utils",
    "decorators.py": "utils",
    "events.py": "utils",
    "utils.py": "utils",
    
    "config.py": "management",
    "migration.py": "management",
    "version.py": "management",
    "plugins.py": "management",
    "cli.py": "management",
    "docs.py": "management",
    
    "security.py": "enterprise",
    "compliance.py": "enterprise",
    "cost_optimization.py": "enterprise",
    "resource_management.py": "enterprise",
    "analytics.py": "enterprise",
    "backup.py": "enterprise",
    "performance_tuning.py": "enterprise",
    
    "scheduler.py": "orchestration",
    "workflow.py": "orchestration",
    "feature_flags.py": "orchestration",
    
    "testing.py": "testing",
    "integration.py": "integration",
    
    "benchmarking.py": "benchmarking",
    "reporting.py": "benchmarking",
    
    "optimization.py": "optimization",
}

# 1. Clean up _v2 legacy directories
for d in ["benchmarking_v2", "config_v2", "integration_v2", "optimization_v2", "testing_v2", "utils_v2"]:
    dir_path = BASE_DIR / d
    if dir_path.exists() and dir_path.is_dir():
        print(f"Removing legacy directory: {d}")
        shutil.rmtree(dir_path)

# 2. Create target directories and __init__.py files
for category in set(MAPPING.values()):
    cat_dir = BASE_DIR / category
    cat_dir.mkdir(exist_ok=True)
    init_file = cat_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()

# 3. Move files
for file_name, category in MAPPING.items():
    source_path = BASE_DIR / file_name
    dest_path = BASE_DIR / category / file_name
    if source_path.exists():
        print(f"Moving {file_name} to {category}/")
        shutil.move(str(source_path), str(dest_path))

# Helper to find category of a module
def get_category_for_module(module_name):
    # e.g., module_name = "backend" -> file = "backend.py" -> category = "core"
    file_name = f"{module_name}.py"
    return MAPPING.get(file_name)

# 4. Update internal imports in all moved files
for file_name, category in MAPPING.items():
    dest_path = BASE_DIR / category / file_name
    if not dest_path.exists():
        continue
        
    with open(dest_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace `from .module import` with `from ..category.module import`
    # or if the module is in the same category, `from .module import`
    def replacer(match):
        mod = match.group(1)
        mod_cat = get_category_for_module(mod)
        if mod_cat:
            if mod_cat == category:
                # Same directory, keep it as `from .module import`
                return f"from .{mod} import"
            else:
                # Different directory, go up one level then down to category
                return f"from ..{mod_cat}.{mod} import"
        return match.group(0)

    # regex to match `from .<module_name> import`
    new_content = re.sub(r"from \.([a-zA-Z_0-9]+) import", replacer, content)
    
    if new_content != content:
        print(f"Updated internal imports in {category}/{file_name}")
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(new_content)

# 5. Update top-level __init__.py
init_path = BASE_DIR / "__init__.py"
if init_path.exists():
    with open(init_path, "r", encoding="utf-8") as f:
        init_content = f.read()
        
    def init_replacer(match):
        mod = match.group(1)
        mod_cat = get_category_for_module(mod)
        if mod_cat:
            return f"from .{mod_cat}.{mod} import"
        return match.group(0)

    new_init_content = re.sub(r"from \.([a-zA-Z_0-9]+) import", init_replacer, init_content)
    
    if new_init_content != init_content:
        print("Updated top-level __init__.py")
        with open(init_path, "w", encoding="utf-8") as f:
            f.write(new_init_content)

print("Refactor completed successfully!")
