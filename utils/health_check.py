"""
Health check script to verify environment and configuration.
"""

import sys
import importlib
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False


def check_package(package_name: str, import_name: str = None) -> bool:
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} (not installed)")
        return False


def check_cuda():
    """Check CUDA availability."""
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            print(f"✅ CUDA available ({device_count} device(s): {device_name})")
            return True
        else:
            print("⚠️  CUDA not available (will use CPU)")
            return False
    except ImportError:
        print("⚠️  PyTorch not installed, cannot check CUDA")
        return False


def check_config_files():
    """Check if essential config files exist."""
    configs_dir = Path("configs")
    
    essential = [
        "llm_default.yaml",
    ]
    
    all_ok = True
    for config_file in essential:
        config_path = configs_dir / config_file
        if config_path.exists():
            print(f"✅ Config: {config_file}")
        else:
            print(f"⚠️  Config missing: {config_file}")
            all_ok = False
    
    # Check presets
    presets_dir = configs_dir / "presets"
    if presets_dir.exists():
        presets = list(presets_dir.glob("*.yaml"))
        print(f"✅ Presets: {len(presets)} preset(s) found")
    
    return all_ok


def check_core_modules():
    """Check if core modules can be imported."""
    modules = [
        ("trainers.trainer", "GenericTrainer"),
        ("build_trainer", "build_trainer"),
        ("factories.registry", "Registry"),
    ]
    
    all_ok = True
    for module_name, attr_name in modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, attr_name):
                print(f"✅ Module: {module_name}.{attr_name}")
            else:
                print(f"⚠️  Module: {module_name} (missing {attr_name})")
                all_ok = False
        except ImportError as e:
            print(f"❌ Module: {module_name} (import error: {e})")
            all_ok = False
    
    return all_ok


def main():
    print("🏥 TruthGPT Optimization Core - Health Check\n")
    print("=" * 60)
    
    checks = []
    
    # Python version
    print("\n📋 Python Environment:")
    checks.append(check_python_version())
    
    # Core packages
    print("\n📦 Core Packages:")
    checks.append(check_package("torch", "torch"))
    checks.append(check_package("transformers", "transformers"))
    checks.append(check_package("datasets", "datasets"))
    
    # Optional packages
    print("\n📦 Optional Packages:")
    check_package("wandb", "wandb")
    check_package("tensorboard", "tensorboard")
    check_package("accelerate", "accelerate")
    check_package("peft", "peft")
    
    # CUDA
    print("\n🎮 Hardware:")
    checks.append(check_cuda())
    
    # Config files
    print("\n📄 Configuration Files:")
    checks.append(check_config_files())
    
    # Core modules
    print("\n🔧 Core Modules:")
    checks.append(check_core_modules())
    
    # Summary
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All essential checks passed!")
        print("\n💡 Ready to train. Run: python train_llm.py --config configs/llm_default.yaml")
        sys.exit(0)
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        print("\n💡 Run: ./setup_dev.sh or pip install -r requirements_advanced.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()


