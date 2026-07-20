import os
import shutil
import glob
import re
import ast

base_dir = r"C:\blatam-academy\agents\backend\onyx\server\features\Frontier-Model-run-polyglot\scripts\TruthGPT-main\optimization_core\polyglot_core"
os.chdir(base_dir)

# --- PHASE 1: CLEANUP ---
redundant_docs = [
    "ABSOLUTE_FINAL_SUMMARY.md", "COMPLETE_FEATURE_LIST.md", "COMPLETE_FEATURE_LIST_FINAL.md",
    "COMPLETE_REFACTORING_SUMMARY.md", "ENTERPRISE_COMPLETE.md", "INDEX.md",
    "MODULAR_COMPLETE.md", "MODULAR_REFACTORING_COMPLETE.md", "MODULAR_STRUCTURE.md",
    "PRODUCTION_READY.md", "REFACTORING_COMPLETE.md", "REFACTORING_PATTERNS.md", "SUMMARY.md"
]
for doc in redundant_docs:
    if os.path.exists(doc):
        os.remove(doc)
        print(f"Removed {doc}")

v2_dirs = [
    "benchmarking_v2", "config_v2", "integration_v2", 
    "optimization_v2", "testing_v2", "utils_v2"
]
for d in v2_dirs:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"Removed {d}")

# --- PHASE 2: DOMAIN RESTRUCTURING ---
moves = {
    "backend.py": "core/backend.py",
    "builder.py": "core/builder.py",
    "factory.py": "core/factory.py",
    "registry.py": "core/registry.py",
    "quantization.py": "core/quantization.py",
    "attention.py": "core/attention.py",
    "cache.py": "core/cache.py",
    "inference.py": "core/inference.py",
    "compression.py": "core/compression.py",
    "tokenization.py": "core/tokenization.py",
    "api.py": "infrastructure/api.py",
    "distributed.py": "infrastructure/distributed.py",
    "load_balancer.py": "infrastructure/load_balancer.py",
    "service_discovery.py": "infrastructure/service_discovery.py",
    "circuit_breaker.py": "infrastructure/circuit_breaker.py",
    "rate_limiting.py": "infrastructure/rate_limiting.py",
    "async_core.py": "infrastructure/async_core.py",
    "alerts.py": "monitoring/alerts.py",
    "health.py": "monitoring/health.py",
    "metrics.py": "monitoring/metrics.py",
    "observability.py": "monitoring/observability.py",
    "profiling.py": "monitoring/profiling.py",
    "telemetry.py": "monitoring/telemetry.py",
    "cli.py": "management/cli.py",
    "config.py": "management/config.py",
    "docs.py": "management/docs.py",
    "migration.py": "management/migration.py",
    "plugins.py": "management/plugins.py",
    "version.py": "management/version.py",
    "analytics.py": "enterprise/analytics.py",
    "backup.py": "enterprise/backup.py",
    "compliance.py": "enterprise/compliance.py",
    "cost_optimization.py": "enterprise/cost_optimization.py",
    "performance_tuning.py": "enterprise/performance_tuning.py",
    "resource_management.py": "enterprise/resource_management.py",
    "security.py": "enterprise/security.py",
    "feature_flags.py": "orchestration/feature_flags.py",
    "scheduler.py": "orchestration/scheduler.py",
    "workflow.py": "orchestration/workflow.py",
    "batch.py": "processing/batch.py",
    "serialization.py": "processing/serialization.py",
    "streaming.py": "processing/streaming.py",
    "context.py": "utils/context.py",
    "decorators.py": "utils/decorators.py",
    "errors.py": "utils/errors.py",
    "events.py": "utils/events.py",
    "logging.py": "utils/logging.py",
    "utils.py": "utils/utils.py",
    "validation.py": "utils/validation.py",
    "integration.py": "integration/integration.py",
    "benchmarking.py": "benchmarking/benchmarking.py",
    "reporting.py": "benchmarking/reporting.py",
    "optimization.py": "optimization/optimization.py",
    "testing.py": "testing/testing.py"
}

for src, dst in moves.items():
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        print(f"Moved {src} to {dst}")

# Remove existing __init__.py in all subdirs to start fresh
for root, dirs, files in os.walk("."):
    if "__init__.py" in files and root != ".":
        os.remove(os.path.join(root, "__init__.py"))

# --- PHASE 3: MONOLITH SPLITTING ---
def split_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath}, not found.")
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
        
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}. Skipping split.")
        return
    
    pkg_dir = filepath.replace(".py", "")
    os.makedirs(pkg_dir, exist_ok=True)
    
    imports_lines = []
    configs_lines = []
    engine_lines = []
    constants_lines = []
    
    exports = []
    
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports_lines.extend(lines[node.lineno - 1 : node.end_lineno])
            continue
            
        start_idx = node.lineno - 1
        while start_idx > 0 and (lines[start_idx - 1].strip().startswith("#") or lines[start_idx - 1].strip() == ""):
            start_idx -= 1
            
        block = "".join(lines[start_idx : node.end_lineno]) + "\n"
        
        if isinstance(node, ast.ClassDef):
            exports.append(node.name)
            name_lower = node.name.lower()
            if "config" in name_lower or "result" in name_lower or "stats" in name_lower or "pattern" in name_lower or "encoding" in name_lower:
                configs_lines.append(block)
            else:
                engine_lines.append(block)
        elif isinstance(node, ast.FunctionDef):
            exports.append(node.name)
            engine_lines.append(block)
        elif isinstance(node, ast.Assign):
            constants_lines.append(block)
            
    with open(os.path.join(pkg_dir, "constants.py"), "w", encoding="utf-8") as f:
        f.write("".join(imports_lines) + "\n\n" + "".join(constants_lines))
        
    with open(os.path.join(pkg_dir, "config.py"), "w", encoding="utf-8") as f:
        f.write("".join(imports_lines) + "\nfrom .constants import *\n\n" + "".join(configs_lines))
        
    with open(os.path.join(pkg_dir, "engine.py"), "w", encoding="utf-8") as f:
        f.write("".join(imports_lines) + "\nfrom .constants import *\nfrom .config import *\n\n" + "".join(engine_lines))
        
    with open(os.path.join(pkg_dir, "__init__.py"), "w", encoding="utf-8") as f:
        f.write(f'from .constants import *\n')
        f.write(f'from .config import *\n')
        f.write(f'from .engine import *\n\n')
        f.write(f'__all__ = [\n')
        for exp in exports:
            f.write(f'    "{exp}",\n')
        f.write(f']\n')
        
    os.remove(filepath)
    print(f"Split {filepath} into {pkg_dir}/")

split_file("core/attention.py")
split_file("core/cache.py")
split_file("core/inference.py")
split_file("core/compression.py")
split_file("core/tokenization.py")

# --- PHASE 4: IMPORT RESOLUTION ---
module_map = {
    "backend": "core.backend",
    "builder": "core.builder",
    "factory": "core.factory",
    "registry": "core.registry",
    "quantization": "core.quantization",
    "attention": "core.attention",
    "cache": "core.cache",
    "inference": "core.inference",
    "compression": "core.compression",
    "tokenization": "core.tokenization",
    "api": "infrastructure.api",
    "distributed": "infrastructure.distributed",
    "load_balancer": "infrastructure.load_balancer",
    "service_discovery": "infrastructure.service_discovery",
    "circuit_breaker": "infrastructure.circuit_breaker",
    "rate_limiting": "infrastructure.rate_limiting",
    "async_core": "infrastructure.async_core",
    "alerts": "monitoring.alerts",
    "health": "monitoring.health",
    "metrics": "monitoring.metrics",
    "observability": "monitoring.observability",
    "profiling": "monitoring.profiling",
    "telemetry": "monitoring.telemetry",
    "cli": "management.cli",
    "config": "management.config",
    "docs": "management.docs",
    "migration": "management.migration",
    "plugins": "management.plugins",
    "version": "management.version",
    "analytics": "enterprise.analytics",
    "backup": "enterprise.backup",
    "compliance": "enterprise.compliance",
    "cost_optimization": "enterprise.cost_optimization",
    "performance_tuning": "enterprise.performance_tuning",
    "resource_management": "enterprise.resource_management",
    "security": "enterprise.security",
    "feature_flags": "orchestration.feature_flags",
    "scheduler": "orchestration.scheduler",
    "workflow": "orchestration.workflow",
    "batch": "processing.batch",
    "serialization": "processing.serialization",
    "streaming": "processing.streaming",
    "context": "utils.context",
    "decorators": "utils.decorators",
    "errors": "utils.errors",
    "events": "utils.events",
    "logging": "utils.logging",
    "validation": "utils.validation",
    "integration": "integration.integration",
    "benchmarking": "benchmarking.benchmarking",
    "reporting": "benchmarking.reporting",
    "optimization": "optimization.optimization",
    "testing": "testing.testing"
}

# Create __init__.py files
for root, dirs, files in os.walk("."):
    for dir_name in dirs:
        if "__pycache__" in root or "__pycache__" in dir_name or dir_name.startswith("."): continue
        init_path = os.path.join(root, dir_name, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w", encoding="utf-8") as f:
                f.write("# Auto-generated\n")
                
packages = [
    ("core", ["backend", "builder", "factory", "registry", "quantization", "attention", "cache", "inference", "compression", "tokenization"]),
    ("infrastructure", ["api", "distributed", "load_balancer", "service_discovery", "circuit_breaker", "rate_limiting", "async_core"]),
    ("monitoring", ["alerts", "health", "metrics", "observability", "profiling", "telemetry"]),
    ("management", ["cli", "config", "docs", "migration", "plugins", "version"]),
    ("enterprise", ["analytics", "backup", "compliance", "cost_optimization", "performance_tuning", "resource_management", "security"]),
    ("orchestration", ["feature_flags", "scheduler", "workflow"]),
    ("processing", ["batch", "serialization", "streaming"]),
    ("utils", ["context", "decorators", "errors", "events", "logging", "utils", "validation"]),
    ("integration", ["integration"]),
    ("benchmarking", ["benchmarking", "reporting"]),
    ("optimization", ["optimization"]),
    ("testing", ["testing"])
]

for pkg, modules in packages:
    if not os.path.exists(pkg): continue
    with open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8") as f:
        for mod in modules:
            f.write(f"from .{mod} import *\n")

print("Updating imports...")
for f in glob.glob("**/*.py", recursive=True):
    if not os.path.isfile(f): continue
    if os.path.basename(f) == "do_refactor.py": continue
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
        
    original_content = content
    
    for old, new in module_map.items():
        if old == "utils" and new == "utils.utils": continue
        if old == "testing" and new == "testing.testing": continue
        
        content = re.sub(rf'from polyglot_core\.{old}\b', f'from polyglot_core.{new}', content)
        content = re.sub(rf'import polyglot_core\.{old}\b', f'import polyglot_core.{new}', content)
        
    if content != original_content:
        with open(f, "w", encoding="utf-8") as file:
            file.write(content)

with open("__init__.py", "w", encoding="utf-8") as f:
    f.write('"""Polyglot Core"""\n')
    for pkg in ["core", "infrastructure", "monitoring", "management", "enterprise", "orchestration", "processing", "utils"]:
        f.write(f"from .{pkg} import *\n")

print("Massive refactoring completed.")
