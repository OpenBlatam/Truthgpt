"""
🧪 Comprehensive Test Suite for TruthGPT Package Refactor
=========================================================
Validates modular subpackage access, lazy-loading resolution, formal contracts,
unified factories, and dual-mode import parity (`truthgpt` and `src.truthgpt`).
"""

import sys
import unittest
import asyncio
from pathlib import Path

# Setup paths
_test_dir = Path(__file__).resolve().parent
_tests_dir = _test_dir.parent
_workspace_root = _tests_dir.parent
_src_dir = _workspace_root / "src"
_workspace_parent = _workspace_root.parent

for p in [str(_workspace_parent), str(_workspace_root), str(_src_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)


class TestTruthGPTPackageStructure(unittest.TestCase):
    """Test package metadata, versioning, and dual-mode import parity."""

    def test_import_src_truthgpt(self):
        """Verify that src.truthgpt imports cleanly with correct metadata."""
        import src.truthgpt as tg
        self.assertEqual(tg.__version__, "2.0.0")
        self.assertIn("TruthGPT", tg.__author__)
        self.assertEqual(tg.__license__, "MIT")

    def test_import_truthgpt_alias(self):
        """Verify that top-level truthgpt imports cleanly and matches src.truthgpt."""
        import truthgpt
        self.assertEqual(truthgpt.__version__, "2.0.0")
        self.assertIsNotNone(truthgpt.api)

    def test_subpackages_resolution(self):
        """Verify that all modular subpackages resolve cleanly via lazy-loading."""
        import src.truthgpt as tg

        subpackages = [
            "adapters", "agents", "bridges", "compiler", "config", "constants",
            "core", "factories", "formal", "inference", "interface", "learning",
            "managers", "models", "modules", "optimization", "optimizers",
            "persistence", "plugins", "polyglot", "registries", "security",
            "terminal", "tools", "trainers", "training", "utils"
        ]

        for sub in subpackages:
            mod = getattr(tg, sub)
            self.assertIsNotNone(mod, f"Failed to resolve subpackage: truthgpt.{sub}")


class TestFormalVerificationEngine(unittest.TestCase):
    """Test Hoare logic Design-by-Contract (DbC), preconditions, postconditions, and types."""

    def test_formal_contract_precondition(self):
        """Test precondition violations throw FormalContractError."""
        from src.truthgpt.formal import formal_contract, FormalContractError

        @formal_contract(pre=lambda x: x > 0)
        def positive_only(x: int) -> int:
            return x * 2

        self.assertEqual(positive_only(5), 10)
        with self.assertRaises(FormalContractError):
            positive_only(-3)

    def test_formal_contract_type_verification(self):
        """Test type constraints raise TypeError when violated."""
        from src.truthgpt.formal import formal_contract

        @formal_contract()
        def typed_fn(name: str, count: int) -> str:
            return f"{name}: {count}"

        self.assertEqual(typed_fn("test", 3), "test: 3")
        with self.assertRaises(TypeError):
            typed_fn(123, 3)  # name must be str

    def test_formal_contract_postcondition(self):
        """Test postcondition violations throw FormalContractError."""
        from src.truthgpt.formal import formal_contract, FormalContractError

        @formal_contract(post=lambda result: len(result) > 0)
        def non_empty_str(flag: bool) -> str:
            return "hello" if flag else ""

        self.assertEqual(non_empty_str(True), "hello")
        with self.assertRaises(FormalContractError):
            non_empty_str(False)

    def test_system_integrity_verification(self):
        """Test formal system integrity analysis report."""
        import src.truthgpt as tg
        report = tg.verify_system_integrity()
        self.assertIsInstance(report, dict)
        self.assertIn("healthy", report)
        self.assertIn("verification_engine", report)


class TestUnifiedFactories(unittest.TestCase):
    """Test unified factory interfaces for adapters and optimizers."""

    def test_adapter_factory_and_registry(self):
        """Test create_adapter factory and ADAPTER_REGISTRY."""
        import src.truthgpt as tg
        self.assertTrue(callable(tg.create_adapter))
        self.assertIsInstance(tg.ADAPTER_REGISTRY, dict)
        self.assertIn("optimizer", tg.ADAPTER_REGISTRY)
        self.assertIn("data", tg.ADAPTER_REGISTRY)

    def test_create_optimization_core_factory(self):
        """Test create_optimization_core factory callable."""
        import src.truthgpt as tg
        self.assertTrue(callable(tg.create_optimization_core))

    def test_create_truthgpt_optimizer(self):
        """Test create_truthgpt_optimizer factory callable."""
        import src.truthgpt as tg
        self.assertTrue(callable(tg.create_truthgpt_optimizer))


class TestAutocompleteAndIntrospection(unittest.TestCase):
    """Test __dir__ and __all__ exposure for developer experience and IDEs."""

    def test_dir_contains_subpackages_and_symbols(self):
        """Verify __dir__() returns comprehensive symbols."""
        import src.truthgpt as tg
        symbols = dir(tg)
        self.assertIn("adapters", symbols)
        self.assertIn("optimizers", symbols)
        self.assertIn("formal_contract", symbols)
        self.assertIn("create_adapter", symbols)
        self.assertIn("create_optimization_core", symbols)
        self.assertIn("TruthGPT_API", symbols)


if __name__ == "__main__":
    unittest.main(verbosity=2)
