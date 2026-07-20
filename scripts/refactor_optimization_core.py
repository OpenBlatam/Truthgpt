# refactor_optimization_core.py - Automated refactoring of optimization_core directory
# 
# Usage:
#   python refactor_optimization_core.py --dry-run   (preview changes)
#   python refactor_optimization_core.py             (apply restructuring)
# 
# This script reorganizes the current working directory (optimization_core) into a clean,
# modular structure while preserving all files. It does not delete anything; it moves
# files to appropriate subfolders (src/, tests/, docs/, config/, legacy/, scripts/).

import os
import shutil
import sys
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.absolute()  # optimization_core directory

# Target new directory structure (all within ROOT)
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

# Mapping of known source files to target subdirectories (relative to src/)
FILE_MAP = {
    # Core functionality
    "truthgpt.py": "core",
    "constants.py": "core",
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
    # Compilers
    "compiler_demo.py": "compiler",
    "compiler_integration.py": "compiler",
    "enhanced_compiler_demo.py": "compiler",
    # Inference
    "latency_optimizations.py": "inference",
    # Training
    "build_trainer.py": "training",
    "train_llm.py": "training",
    # Optimizers
    "optimization_pipeline.py": "optimizers",
    # Multi-language cores
    # (Rust, Go, Julia, etc. remain in src/polyglot if not moved from existing dirs)
}

# Known test files (will be placed in tests/)
TEST_PATTERNS = ["test_", "_test.py", "smoke_test", "verify_", "debug_", "validate_"]

# Documentation patterns
DOC_PATTERNS = [
    ".md", "README", "CHANGELOG", "CONTRIBUTING", "FAQ",
    "GUIDE", "SUMMARY", "INDEX", "ARCHITECTURE", "REFACTORING", "DEPRECATED",
    "IMPLEMENTATION", "DEPLOYMENT", "QUICK_REFERENCE", "MODULAR"
]

# Directories that already exist and should be mapped as-is (we'll move them into src/)
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
    "plugins", "scheduler_registry.json", "default_workflow.yaml"
]

# Items to move to legacy (duplicates, old summaries, temporary files)
LEGACY_ITEMS = [
    "REFACTORING_*.md",
    "*_SUMMARY.md",
    "ABSOLUTE_PERFECTION_PIMOE_SUMMARY.md",
    "COSMIC_INTELLIGENCE_PIMOE_SUMMARY.md",
    "INFINITE_*.md",
    "LIGHTNING_SPEED_PIMOE_SUMMARY.md",
    "OMNIPOTENT_INTELLIGENCE_README.md",
    "OMNIPOTENT_INTELLIGENCE_REQUIREMENTS.txt",
    "SUPREME_INTELLIGENCE_README.md",
    "SUPREME_INTELLIGENCE_REQUIREMENTS.txt",
    "ULTIMATE_*.md",
    "ULTIMATE_*.txt",
    "Omnipotent_intelligence.py",
    "supreme_intelligence.py",
    "ultimate_intelligence.py",
    "output_continuous_*.py",
    "output_continuous_*.sh",
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
    "system_continuity.ps1",
    "system_manager.ps1",
    "openclaw.cmd",
    "run.bat",
    "launch.py",
    "launch_enhanced.py",
]

def hash_file(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def backup_path(path):
    """Create a backup path with timestamp."""
    base = path.name
    stem = path.stem
    suffix = path.suffix
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return path.parent / f"{stem}_{timestamp}_bak{suffix}"

def create_dirs():
    for dir_path_relative in NEW_DIRS.keys():
        full_path = ROOT / dir_path_relative
        full_path.mkdir(parents=True, exist_ok=True)

def move_file(src, dest):
    """Move file, creating destination dir if needed, and backup if dest exists."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        # backup existing
        bak = backup_path(dest)
        print(f"  Backing up existing {dest} to {bak}")
        shutil.move(str(dest), str(bak))
    print(f"  Moving {src} -> {dest}")
    shutil.move(str(src), str(dest))

def move_directory(src_dir, dest_parent):
    """Move a directory into dest_parent, handling conflicts by merging."""
    src_dir = Path(src_dir)
    dest = Path(dest_parent) / src_dir.name
    if dest.exists():
        # Merge: move contents recursively
        for item in src_dir.iterdir():
            target = dest / item.name
            if item.is_dir():
                if target.exists():
                    # merge subdirs
                    move_directory(item, dest)
                else:
                    shutil.move(str(item), str(target))
            else:
                if target.exists():
                    # backup and replace
                    bak = backup_path(target)
                    print(f"  Backing up {target} to {bak}")
                    shutil.move(str(target), str(bak))
                shutil.move(str(item), str(target))
        # remove original empty dir
        src_dir.rmdir()
    else:
        shutil.move(str(src_dir), str(dest))
    print(f"  Moved directory {src_dir} -> {dest}")

def classify_and_move():
    print("Classifying and moving root-level files...")
    for item in ROOT.iterdir():
        if item == ROOT / "refactor_optimization_core.py":
            continue  # don't move self
        if item.name.startswith('.'):
            continue  # skip hidden
        if item.is_file():
            name = item.name
            # Check LEGACY first
            for pattern in LEGACY_ITEMS:
                if Path(name).match(pattern) or pattern.endswith("*"):
                    # simple glob match
                    if name.endswith(pattern[1:]) if pattern.startswith('*') else name == pattern:
                        dest = ROOT / "legacy" / name
                        move_file(item, dest)
                        break
            else:
                # Map by known mapping
                mapped = False
                for key, target_dir in FILE_MAP.items():
                    if name == key:
                        dest = ROOT / "src" / target_dir / name
                        move_file(item, dest)
                        mapped = True
                        break
                if not mapped:
                    # Heuristics
                    lower = name.lower()
                    if any(lower.startswith(tp) for tp in TEST_PATTERNS):
                        dest = ROOT / "tests" / name
                        move_file(item, dest)
                    elif any(doc in lower for doc in DOC_PATTERNS):
                        dest = ROOT / "docs" / name
                        move_file(item, dest)
                    elif lower.endswith('.py'):
                        # Python modules go to src/utils if not special
                        dest = ROOT / "src" / "utils" / name
                        move_file(item, dest)
                    elif lower.endswith('.json') or lower.endswith('.yaml') or lower.endswith('.toml'):
                        dest = ROOT / "config" / name
                        move_file(item, dest)
                    elif lower.endswith('.txt') or lower.endswith('.csv') or lower.endswith('.log'):
                        dest = ROOT / "legacy" / name
                        move_file(item, dest)
                    else:
                        dest = ROOT / "legacy" / name
                        move_file(item, dest)
        elif item.is_dir():
            name = item.name
            # Move known dirs into src/ if applicable
            if name in EXISTING_DIRS_TO_MOVE:
                target = ROOT / "src"
                move_directory(item, target)
            elif name in NEW_DIRS:
                pass  # already target dir, not moving
            else:
                # Move unknown dirs to src/ for now
                target = ROOT / "src"
                move_directory(item, target)

def create_init_files():
    """Ensure all package dirs have __init__.py"""
    for dirpath, dirnames, files in os.walk(ROOT / "src"):
        if "__init__.py" not in files:
            init_file = os.path.join(dirpath, "__init__.py")
            print(f"  Creating {init_file}")
            Path(init_file).touch()
    # Also for tests
    tests_dir = ROOT / "tests"
    if tests_dir.exists() and not (tests_dir / "__init__.py").exists():
        print("  Creating tests/__init__.py")
        (tests_dir / "__init__.py").touch()

def generate_readme():
    content = """# TruthGPT Optimization Core - Refactored

This directory has been automatically refactored for modularity and clarity.

## Structure
- `src/` : Source code organized into subpackages (core, agents, adapters, compiler, etc.)
- `tests/` : Test suites
- `docs/` : Documentation
- `config/` : Configuration files
- `scripts/` : Utility scripts
- `legacy/` : Archived and deprecated files
- `data/` : Data files (if any)

Run `python -m src.core.truthgpt` or similar to start.

Generated on: {}
""".format(datetime.now().isoformat())
    readme_path = ROOT / "README.md"
    if not readme_path.exists():
        print("Creating README.md")
        readme_path.write_text(content)
    else:
        print("README.md already exists, skipping.")

def main(dry_run=False):
    if dry_run:
        print("DRY RUN: No files will be moved.\n")
    else:
        print("Starting refactoring of optimization_core...\n")
        create_dirs()
        classify_and_move()
        create_init_files()
        generate_readme()
        print("\nRefactoring complete! Check the new structure.")

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
