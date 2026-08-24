"""
Environment Diagnostics and Test Harness Validator for TruthGPT Optimization Core.
"""

from __future__ import annotations

import sys
import importlib
from pathlib import Path
from typing import Any, Dict, List


class TestEnvironmentSetup:
    """Setup and diagnostic inspector for test harness dependencies and polyglot backends."""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.test_root = Path(__file__).parent
        self.required_packages = [
            'torch',
            'numpy',
            'psutil',
            'pytest',
            'unittest',
            'json',
            'time',
            'gc',
        ]
        self.optional_packages = [
            'polars',
            'transformers',
            'accelerate',
            'yaml',
            'pytest-cov',
            'pytest-xdist',
        ]

    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        print("🐍 Checking Python version...")
        if sys.version_info < (3, 8):
            print(f"❌ Python {sys.version} is not supported. Requires Python 3.8+")
            return False
        print(f"✅ Python {sys.version.split()[0]} is compatible")
        return True

    def check_required_packages(self) -> Dict[str, bool]:
        """Check availability of required foundational packages."""
        print("📦 Checking required packages...")
        status = {}
        for pkg in self.required_packages:
            try:
                importlib.import_module(pkg)
                status[pkg] = True
                print(f"  ✅ {pkg}")
            except ImportError:
                status[pkg] = False
                print(f"  ❌ {pkg} (missing)")
        return status

    def check_optional_packages(self) -> Dict[str, bool]:
        """Check availability of optional performance packages."""
        print("🔧 Checking optional packages...")
        status = {}
        for pkg in self.optional_packages:
            mod_name = pkg.replace('-', '_')
            try:
                importlib.import_module(mod_name)
                status[pkg] = True
                print(f"  ✅ {pkg}")
            except ImportError:
                status[pkg] = False
                print(f"  ⚠️  {pkg} (optional - not installed)")
        return status

    def check_torch_installation(self) -> Dict[str, Any]:
        """Check PyTorch capabilities (CUDA, MPS, CPU)."""
        print("🔥 Checking PyTorch installation...")
        try:
            import torch
            cuda_avail = torch.cuda.is_available()
            mps_avail = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
            info = {
                'installed': True,
                'version': torch.__version__,
                'cuda_available': cuda_avail,
                'device_count': torch.cuda.device_count() if cuda_avail else 0,
                'mps_available': mps_avail,
            }
            print(f"  ✅ PyTorch {info['version']}")
            if cuda_avail:
                print(f"  ✅ CUDA available with {info['device_count']} device(s)")
            else:
                print("  ℹ️  Running on CPU backend")
            return info
        except ImportError:
            print("  ❌ PyTorch is not installed")
            return {'installed': False}

    def check_polyglot_backends(self) -> Dict[str, bool]:
        """Check availability of native polyglot acceleration backends."""
        print("🌐 Checking polyglot native backends...")
        backends = {"python": True, "rust": False, "cpp": False, "julia": False}
        try:
            import truthgpt_rust  # type: ignore
            backends["rust"] = True
            print("  ✅ Rust backend (truthgpt_rust)")
        except (ImportError, ModuleNotFoundError):
            print("  ⚠️  Rust backend not compiled / available")

        try:
            import _cpp_core  # type: ignore
            backends["cpp"] = True
            print("  ✅ C++ backend (_cpp_core)")
        except (ImportError, ModuleNotFoundError):
            print("  ⚠️  C++ backend not compiled / available")

        try:
            from julia import TruthGPTCore  # type: ignore
            backends["julia"] = True
            print("  ✅ Julia backend (TruthGPTCore)")
        except (ImportError, ModuleNotFoundError):
            print("  ⚠️  Julia backend not installed / available")

        return backends

    def ensure_test_directories(self) -> None:
        """Ensure all required test directory structures exist."""
        print("📁 Verifying test directory structure...")
        dirs = [
            self.test_root / "unit",
            self.test_root / "integration",
            self.test_root / "performance",
            self.test_root / "fixtures",
            self.test_root / "utils",
            self.test_root / "reports",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {d.relative_to(self.project_root)}")

    def run_all_checks(self) -> bool:
        """Run complete environment diagnostic suite."""
        print("=" * 60)
        print("🚀 TruthGPT Test Environment Diagnostic Suite")
        print("=" * 60)
        py_ok = self.check_python_version()
        req_ok = all(self.check_required_packages().values())
        self.check_optional_packages()
        self.check_torch_installation()
        self.check_polyglot_backends()
        self.ensure_test_directories()
        print("=" * 60)
        all_ok = py_ok and req_ok
        print(f"Overall Environment Status: {'✅ READY' if all_ok else '❌ ISSUES DETECTED'}")
        print("=" * 60)
        return all_ok


def main() -> None:
    setup = TestEnvironmentSetup()
    success = setup.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
