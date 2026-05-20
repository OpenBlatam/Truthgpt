# refactor_optimization_core_complete.py
# Complete automated refactoring script for optimization_core directory.
# Place this file in the root of the directory to reorganize.
# Usage:
#   python refactor_optimization_core_complete.py --dry-run   (preview moves)
#   python refactor_optimization_core_complete.py             (apply restructuring)

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.absolute()

# New directory structure (relative to ROOT)
NEW_DIRS = {
    "src/core": [],
    "src/agents": [],
    "src/adapters": [],
    "src/compiler": [],
    "src/inference": [],
    "src/training": [],
    "src/polyglot": [],
    "src/optimizers": [],
    "src/factories": [],
    "src/managers": [],
    "src/registries": [],
    "src/utils": [],
    "src/bridges": [],
    "src/api": [],
    "tests": [],
    "docs": [],
    "config": [],
    "legacy": [],
    "scripts": [],
    "data": []
}

# Mapping of known source files to subdirectories under src/
FILE_MAP = {
    # Core functionality
    "truthgpt.py": "core",
    "constants.py": "core",
    "_lazy_imports.py": "core",
    "__init__.py": "core",
    "main.py": "core",
    "cli.py": "core",
    "openclaw.py": "core",
    "system_core_api.py": "core",
    "dynamic_terminal_agent.py": "core",
    "dynamic_truthgpt_terminal.py": "core",
    "dynamic_workflow.py": "core",
    "enhanced_cli.py": "core",
    "terminal_view.py": "core",
    "continuous_agent.py": "core",
    "continuous_agent_tui.py": "core",
    "multi_user_react_agent.py": "core",
    "enhanced_multi_user_react_agent.py": "core",
    "ultimate_dynamic_terminal.py": "core",
    "refactored_dynamic_terminal.py": "core",
    "enhanced_dynamic_terminal.py": "core",
    "improved_dynamic_terminal.py": "core",
    "dynamic_continuous_terminal.py": "core",
    "compiler_demo.py": "compiler",
    "compiler_integration.py": "compiler",
    "enhanced_compiler_demo.py": "compiler",
    "latency_optimizations.py": "inference",
    "build_trainer.py": "training",
    "train_llm.py": "training",
    "optimization_pipeline.py": "optimizers",
    "demo_gradio_llm.py": "core",
    "enhanced_terminal.py": "core",
    "init_project.py": "core",
    "install_enhanced_ui.py": "core",
    "install_extras.py": "core",
    "install_truth.ps1": "scripts",
    "migration_helper.py": "core",
    "validate_config.py": "core",
    "verify_enterprise_refactor.py": "core",
    "verify_structure.py": "core",
    "build.py": "core",
    "smoke_test_phase6.py": "tests",
    "test_compiler_integration.py": "tests",
    "test_kv_cache.py": "tests",
    "debug_imports.py": "tests",
    "debug_web3.py": "tests",
    "omnipotent_intelligence.py": "legacy",
    "supreme_intelligence.py": "legacy",
    "ultimate_intelligence.py": "legacy",
}

# Test file patterns (any file containing these will go to tests/)
TEST_PATTERNS = ["test_", "_test.py", "smoke_test", "verify_", "debug_", "validate_"]

# Documentation patterns (case-insensitive)
DOC_PATTERNS = [
    ".md", "README", "CHANGELOG", "CONTRIBUTING", "FAQ",
    "GUIDE", "SUMMARY", "INDEX", "ARCHITECTURE", "REFACTORING", "DEPRECATED",
    "IMPLEMENTATION", "DEPLOYMENT", "QUICK_REFERENCE", "MODULAR"
]

# Existing directories that should be moved directly into src/
EXISTING_DIRS_TO_MOVE = [
    "agents", "adapters", "compiler", "core", "inference", "training",
    "optimizers", "factories", "managers", "registries", "utils",
    "bridges", "polyglot", "polyglot_core", "rust_core", "go_core",
    "julia_core", "elixir_core", "scala_core", "cpp_core",
    "modules", "models", "config", "configs", "configurations",
    "constants", "research", "benchmarks", "benchmark_reports",
    "performance_reports", "reports", "tests", "test_framework",
    "test_reports", "specs", "tools", "scripts", "docs", "documentation",
    "production", "deployment", "infrastructure", "learning",
    "plugins"
]

# Items to move to legacy (wildcards not allowed, we'll match explicitly later)
LEGACY_ITEMS = [
    "ABSOLUTE_PERFECTION_PIMOE_SUMMARY.md",
    "COSMIC_INTELLIGENCE_PIMOE_SUMMARY.md",
    "INFINITE_DIVINE_PIMOE_SUMMARY.md",
    "INFINITE_REALITY_PIMOE_SUMMARY.md",
    "INFINITE_TRANSCENDENCE_PIMOE_SUMMARY.md",
    "INFINITE_UNDERSTANDING_PIMOE_SUMMARY.md",
    "INFINITE_WISDOM_PIMOE_SUMMARY.md",
    "LIGHTNING_SPEED_PIMOE_SUMMARY.md",
    "OMNIPOTENT_INTELLIGENCE_README.md",
    "OMNIPOTENT_INTELLIGENCE_REQUIREMENTS.txt",
    "SUPREME_INTELLIGENCE_README.md",
    "SUPREME_INTELLIGENCE_REQUIREMENTS.txt",
    "ULTIMATE_AWARENESS_PIMOE_SUMMARY.md",
    "ULTIMATE_CONSCIOUSNESS_PIMOE_SUMMARY.md",
    "ULTIMATE_CREATIVITY_PIMOE_SUMMARY.md",
    "ULTIMATE_EXCELLENCE_PIMOE_SUMMARY.md",
    "ULTIMATE_INTELLIGENCE_PIMOE_SUMMARY.md",
    "ULTIMATE_INTELLIGENCE_README.md",
    "ULTIMATE_INTELLIGENCE_REQUIREMENTS.txt",
    "ULTIMATE_OPTIMIZATION_PIMOE_SUMMARY.md",
    "ULTIMATE_PIMOE_ENHANCEMENT_SUMMARY.md",
    "ULTIMATE_TRANSCENDENCE_PIMOE_SUMMARY.md",
    "ULTIMATE_WISDOM_PIMOE_SUMMARY.md",
    "ULTRA_RAPID_SPEED_PIMOE_SUMMARY.md",
    "TRANSCENDENT_PERFECTION_PIMOE_SUMMARY.md",
    "IMPROVEMENTS_COMPLETE_SUMMARY.md",
    "PHASE1_IMPLEMENTATION_STATUS.md",
    "PHASE2_DIRECTORY_REORGANIZATION.md",
    "PHASE2_IMPLEMENTATION_STATUS.md",
    "REFACTORING_COMPLETE_SUMMARY.md",
    "REFACTORING_COMPREHENSIVE.md",
    "REFACTORING_CONSTANTS.md",
    "REFACTORING_CORE_OPTIMIZERS.md",
    "REFACTORING_CORE_ORGANIZATION.md",
    "REFACTORING_EXAMPLES_BENCHMARKS.md",
    "REFACTORING_FACTORIES_MANAGERS.md",
    "REFACTORING_FEED_FORWARD.md",
    "REFACTORING_FINAL_SESSION.md",
    "REFACTORING_FINAL_SUMMARY.md",
    "REFACTORING_INFERENCE_ORGANIZATION.md",
    "REFACTORING_INIT_PY.md",
    "REFACTORING_MASS_REFACTOR.md",
    "REFACTORING_MODULES_DATA_OPTIMIZATION.md",
    "REFACTORING_OPPORTUNITIES.md",
    "REFACTORING_OPTIMIZATION_CORES.md",
    "REFACTORING_OPTIMIZERS.md",
    "REFACTORING_OPTIMIZERS_ORGANIZATION.md",
    "REFACTORING_PRODUCTION_CONFIGS.md",
    "REFACTORING_PROGRESS.md",
    "REFACTORING_REGISTRIES.md",
    "REFACTORING_ROOT_ORGANIZATION.md",
    "REFACTORING_SESSION_SUMMARY.md",
    "REFACTORING_STATUS.md",
    "REFACTORING_SUMMARY.md",
    "REFACTORING_TRAINING_CONFIG.md",
    "REFACTORING_UTILS_ORGANIZATION.md",
    "REFACTORING_COMPILERS_MODELS_ADAPTERS.md",
    "DIRECTORY_STRUCTURE_GUIDE.md",  # legacy if we want
    "DEPLOYMENT_GUIDE.md",
    "COMPILER_INTEGRATION_GUIDE.md",
    "IMPLEMENTATION_GUIDE_PHASE1.md",
    "KV_CACHE_OPTIMIZATION_GUIDE.md",
    "DEPLOYMENT_REQUIREMENTS.txt",
    "DEPRECATED_OPTIMIZERS.md",
    "ARCHITECTURE_IMPROVEMENTS.md",
    "ARCHITECTURE_IMPROVEMENTS_SUMMARY.md",
    "TRUTHPGT_SYSTEM_SUMMARY.md",
    # Output logs, cache, temp files
    "output_continuous_1_1779222847.py",
    "output_continuous_1_1779227309.sh",
    "output_continuous_1_1779229341.sh",
    "output_continuous_1_1779232702.sh",
    "search_results.csv",
    "import_test_report.json",
    "import_time.log",
    "persistence.log",
    "synthesis_error.log",
    "truthgpt_api.log",
    "verify_out.txt",
    "verify_out_utf8.txt",
    "test_out.txt",
    "test_output.txt",
    "traces_history.json",
    "user_preferences.json",
    "scheduler_registry.json",
    "terminal_config.json",
    "system_continuity.ps1",
    "system_manager.ps1",
    "openclaw.cmd",
    "run.bat",
    "launch.py",
    "launch_enhanced.py",
    "setup_dev.ps1",
    "setup_dev.sh",
    "quick_install.sh",
    "agent_core_memory.db",
    "agent_persistence.db",
    "openclaw_memory.db",
    "test_agent_memory.db",
]

DRY_RUN = "--dry-run" in sys.argv

def log(msg):
    print(msg)

def create_dirs():
    for dir_rel in NEW_DIRS:
        full_path = ROOT / dir_rel
        if not full_path.exists():
            if not DRY_RUN:
                full_path.mkdir(parents=True, exist_ok=True)
            log(f"[CREATE] {full_path.relative_to(ROOT)}")
        else:
            log(f"[EXISTS] {full_path.relative_to(ROOT)}")

def move_file(src, dst):
    if src == dst:
        return
    # avoid moving files already inside target subdirectories (e.g., src/ or legacy/)
    if not DRY_RUN:
        shutil.move(str(src), str(dst))
    log(f"[MOVE] {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

def get_target_subdir(filename: str) -> str:
    """Determine target subdirectory for a given file name."""
    # Check FILE_MAP first
    if filename in FILE_MAP:
        return FILE_MAP[filename]
    # Check test patterns
    name_lower = filename.lower()
    for pattern in TEST_PATTERNS:
        if pattern.lower() in name_lower:
            return "tests"
    # Check documentation patterns
    if any(p.lower() in name_lower for p in DOC_PATTERNS):
        return "docs"
    # Python files not mapped -> core
    if filename.endswith('.py'):
        return "core"
    # shell scripts -> scripts
    if filename.endswith('.sh') or filename.endswith('.ps1') or filename.endswith('.cmd') or filename.endswith('.bat'):
        return "scripts"
    # YAML/TOML -> config
    if filename.endswith('.yaml') or filename.endswith('.yml') or filename.endswith('.toml'):
        return "config"
    # requirements or lock -> config
    if filename in ['requirements.txt', 'requirements_advanced.txt', 'requirements_lock.txt', 'pyproject.toml', 'Makefile', 'BUILD.bazel', 'WORKSPACE.bazel', '.bazelrc']:
        return "config"
    # Databases -> legacy
    if filename.endswith('.db') or filename.endswith('.log'):
        return "legacy"
    # Unknown - keep in ROOT unless it's a file we'll later sweep to legacy
    return None

def is_legacy(item_name: str) -> bool:
    """Check if the item (file or directory) should go to legacy."""
    return item_name in LEGACY_ITEMS

def reorganize():
    create_dirs()

    # Process existing directories first
    for dir_name in EXISTING_DIRS_TO_MOVE:
        dir_path = ROOT / dir_name
        if dir_path.exists() and dir_path.is_dir():
            # skip directories that will be moved to src/ or other target folders
            if dir_name in ["src", "tests", "docs", "config", "legacy", "scripts", "data"]:
                continue
            # Move entire directory into src/
            target = ROOT / "src" / dir_name
            if not target.exists():
                move_file(dir_path, target)

    # Process files at the top level
    for item in list(ROOT.iterdir()):
        if item.name == __file__:
            continue
        if item.is_dir():
            # Handle existing dirs that weren't in EXISTING_DIRS_TO_MOVE
            if item.name in ["src", "tests", "docs", "config", "legacy", "scripts", "data"]:
                continue
            # For other dirs, move to legacy if legacy item, else keep as is
            if is_legacy(item.name):
                move_file(item, ROOT / "legacy" / item.name)
            # else skip unknown dirs (like .api_cost_cache, .pytest_cache, __pycache__, etc.)
        else:
            # File
            if is_legacy(item.name):
                move_file(item, ROOT / "legacy" / item.name)
                continue

            # Determine target subdirectory
            target_sub = get_target_subdir(item.name)
            if target_sub is None:
                # if unknown, keep in place (or maybe move to legacy)
                log(f"[SKIP] {item.relative_to(ROOT)} (unmapped)")
                continue

            # If target is under src/, prepend src/
            if target_sub in ["core", "agents", "adapters", "compiler", "inference", "training",
                               "polyglot", "optimizers", "factories", "managers", "registries", "utils",
                               "bridges", "api"]:
                final_dir = ROOT / "src" / target_sub
            else:
                final_dir = ROOT / target_sub

            move_file(item, final_dir / item.name)

if __name__ == "__main__":
    print(f"Starting refactoring of {ROOT}")
    if DRY_RUN:
        print("### DRY RUN MODE - No files will be moved. ###")
    reorganize()
    print("Refactoring complete.")
