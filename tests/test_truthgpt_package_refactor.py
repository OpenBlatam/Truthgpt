"""
TruthGPT Package Refactoring Verification Test Suite
====================================================
Validates all subpackages, lazy loading, AST syntax, and public APIs of `truthgpt`.
"""

import sys
import os
import unittest
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

for p in [str(SRC_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)


class TestTruthGPTPackageStructure(unittest.TestCase):
    """Test full structure and AST validity of truthgpt package."""

    def test_syntax_validity_all_files(self):
        """Verify that 100% of Python files in src/truthgpt compile without syntax errors."""
        truthgpt_dir = SRC_DIR / "truthgpt"
        errors = []
        file_count = 0
        for root, dirs, files in os.walk(truthgpt_dir):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    file_count += 1
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as src_f:
                            compile(src_f.read(), fp, "exec")
                    except SyntaxError as e:
                        errors.append((fp, e.lineno, e.msg))

        self.assertEqual(len(errors), 0, f"Found {len(errors)} syntax errors in {file_count} files: {errors}")
        print(f"\n[OK] 100% Syntax check passed ({file_count} Python files compiled successfully)")

    def test_package_import(self):
        """Verify that truthgpt package can be imported directly and has version metadata."""
        import truthgpt
        self.assertTrue(hasattr(truthgpt, "__version__"))
        self.assertEqual(truthgpt.__version__, "2.0.0")
        print(f"[OK] truthgpt version: {truthgpt.__version__}")

    def test_all_subpackages_resolution(self):
        """Verify lazy/direct resolution of all 26 core subpackages."""
        import truthgpt

        subpackages = [
            "adapters", "agents", "bridges", "compiler", "config", "constants",
            "core", "factories", "inference", "interface", "learning", "managers",
            "models", "modules", "optimization", "optimizers", "persistence",
            "plugins", "polyglot", "registries", "security", "terminal", "tools",
            "trainers", "training", "utils"
        ]

        for sub in subpackages:
            try:
                mod = getattr(truthgpt, sub)
                self.assertIsNotNone(mod, f"Failed to access truthgpt.{sub}")
                print(f"[OK] truthgpt.{sub} successfully resolved")
            except Exception as e:
                self.fail(f"Failed to access truthgpt.{sub}: {e}")

    def test_top_level_exports(self):
        """Verify top-level exported functions and classes."""
        import truthgpt

        symbols = [
            "create_truthgpt_optimizer",
            "create_generic_optimizer",
            "create_optimization_core",
            "create_adapter",
            "formal_contract",
            "FormalContractError",
        ]

        for sym in symbols:
            self.assertTrue(hasattr(truthgpt, sym), f"truthgpt missing top-level symbol: {sym}")
            val = getattr(truthgpt, sym)
            self.assertIsNotNone(val)
            print(f"[OK] truthgpt.{sym} verified")

    def test_backward_compatibility_shims(self):
        """Verify backward-compatible shim access."""
        import truthgpt
        # Test utils_mod alias
        utils_mod = getattr(truthgpt, "utils_mod", None)
        self.assertIsNotNone(utils_mod)
        print("[OK] truthgpt.utils_mod backward-compatibility alias verified")


if __name__ == "__main__":
    unittest.main(verbosity=2)
