"""
TruthGPT Refactor Verification Suite
====================================
Validates that the entire truthgpt package is structurally sound, 100% free of
syntax/compilation errors, cleanly initialized, and properly exposes its public APIs.
"""

import sys
import unittest
import py_compile
from pathlib import Path
import types

# Ensure src/ is on sys.path for direct truthgpt imports
ROOT = Path(__file__).parent.parent.resolve()
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestTruthGPTRefactor(unittest.TestCase):
    """Test suite verifying the refactored truthgpt package."""

    def test_truthgpt_root_import(self):
        """Verify that root truthgpt package imports and has correct version metadata."""
        import truthgpt
        self.assertEqual(truthgpt.__version__, "2.0.0")
        self.assertIn("UnifiedTruthGPTOptimizer", dir(truthgpt))
        self.assertIn("core", dir(truthgpt))

    def test_no_compilation_errors(self):
        """Verify all Python files compile cleanly with zero errors."""
        tg_dir = SRC_DIR / "truthgpt"
        errors = []
        total = 0
        for p in tg_dir.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            total += 1
            try:
                py_compile.compile(str(p), doraise=True)
            except py_compile.PyCompileError as e:
                errors.append((str(p), str(e)))

        self.assertEqual(
            len(errors), 0,
            f"Found {len(errors)} compilation errors out of {total} files: {errors[:5]}"
        )
        print(f"\n[PASS] Verified {total} Python files compiled with 0 errors.")

    def test_all_subpackages_have_init(self):
        """Verify all directories containing python files have an __init__.py."""
        tg_dir = SRC_DIR / "truthgpt"
        missing_inits = []
        for d in tg_dir.rglob("*"):
            if d.is_dir() and "__pycache__" not in d.parts:
                py_files = [f for f in d.iterdir() if f.is_file() and f.suffix == ".py" and "__pycache__" not in f.parts]
                if py_files and not (d / "__init__.py").exists():
                    missing_inits.append(str(d))

        self.assertEqual(
            len(missing_inits), 0,
            f"Directories missing __init__.py: {missing_inits}"
        )
        print("\n[PASS] All subdirectories containing .py files possess valid __init__.py.")

    def test_no_py_in_pycache(self):
        """Verify no .py source files remain misplaced inside __pycache__ folders."""
        tg_dir = SRC_DIR / "truthgpt"
        misplaced = list(tg_dir.rglob("__pycache__/*.py"))
        self.assertEqual(
            len(misplaced), 0,
            f"Found misplaced .py files in __pycache__: {misplaced}"
        )
        print("\n[PASS] Zero misplaced source files in __pycache__.")

    def test_no_nested_backend_corrupted_directory(self):
        """Verify accidental nested backend copy has been removed."""
        backend_dir = SRC_DIR / "truthgpt" / "agents" / "backend"
        self.assertFalse(
            backend_dir.exists(),
            "Accidental nested backend directory still exists!"
        )
        print("\n[PASS] No corrupt nested backend paths.")

    def test_subpackage_lazy_resolution(self):
        """Verify key subpackages can be accessed through truthgpt namespace."""
        import truthgpt

        subpackages = [
            "adapters", "agents", "bridges", "compiler", "config",
            "constants", "core", "factories", "inference", "interface",
            "learning", "managers", "models", "modules", "optimization",
            "optimizers", "persistence", "plugins", "polyglot",
            "registries", "security", "terminal", "tools", "trainers",
            "training", "utils"
        ]

        for pkg in subpackages:
            mod = getattr(truthgpt, pkg)
            self.assertIsNotNone(mod, f"Subpackage '{pkg}' resolved to None")
        print(f"\n[PASS] Successfully lazy-resolved all {len(subpackages)} subpackages.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
