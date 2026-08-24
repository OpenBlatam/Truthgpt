"""
Cross-Platform Test Helpers, File Utilities, and Decorators for TruthGPT Optimization Core.
"""

from __future__ import annotations

import json
import time
import shutil
import tempfile
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_temp_directory(prefix: str = "truthgpt_test_") -> Path:
    """Create a temporary directory and return its Path."""
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    return Path(temp_dir)


def cleanup_temp_directory(temp_dir: Union[str, Path]) -> None:
    """Recursively clean up a temporary directory."""
    path = Path(temp_dir)
    if path.exists():
        try:
            shutil.rmtree(path)
        except Exception as e:
            logger.warning("Failed to remove temp dir '%s': %s", path, e)


def create_test_config(**kwargs: Any) -> Dict[str, Any]:
    """Create a default test configuration dictionary."""
    cfg = {
        "batch_size": 2,
        "seq_len": 128,
        "d_model": 512,
        "n_heads": 8,
        "n_layers": 6,
        "dropout": 0.1,
        "learning_rate": 0.001,
        "device": "cpu",
    }
    cfg.update(kwargs)
    return cfg


def create_mock_processor(**kwargs: Any) -> Any:
    """Create a mock data processor instance."""
    from ..fixtures.mock_components import MockDataset
    return MockDataset(**kwargs)


def create_mock_engine(**kwargs: Any) -> Any:
    """Create a mock inference engine instance."""
    from ..fixtures.mock_components import MockModel
    return MockModel(**kwargs)


def create_test_data_file(
    file_path: Union[str, Path],
    num_samples: int = 100,
    format: str = "jsonl",
) -> Path:
    """Create a temporary synthetic dataset file (jsonl or json)."""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with open(p, 'w', encoding='utf-8') as f:
        if format == "jsonl":
            for i in range(num_samples):
                row = {
                    "id": i,
                    "text": f"Sample synthetic text line {i} for optimization tests.",
                    "label": i % 2,
                }
                f.write(json.dumps(row) + "\n")
        elif format == "json":
            rows = [
                {
                    "id": i,
                    "text": f"Sample synthetic text line {i} for optimization tests.",
                    "label": i % 2,
                }
                for i in range(num_samples)
            ]
            json.dump(rows, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    return p


def load_test_data(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load test dataset from file."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    if p.suffix == ".jsonl":
        data = []
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    data.append(json.loads(line_str))
        return data
    elif p.suffix == ".json":
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported file extension: {p.suffix}")


def assert_dict_contains(actual: Dict[str, Any], expected: Dict[str, Any], path: str = "") -> None:
    """Assert that dictionary `actual` recursively contains all expected keys and values."""
    for k, v in expected.items():
        curr_path = f"{path}.{k}" if path else k
        assert k in actual, f"Missing key in actual dict: '{curr_path}'"
        if isinstance(v, dict):
            assert isinstance(actual[k], dict), f"Expected dict at '{curr_path}', got {type(actual[k])}"
            assert_dict_contains(actual[k], v, curr_path)
        else:
            assert actual[k] == v, f"Mismatch at '{curr_path}': expected {v}, got {actual[k]}"


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 0.5,
    exceptions: tuple = (Exception,),
) -> Callable[..., Any]:
    """Decorator to retry a test or callable on failure."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_err = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_err
        return wrapper
    return decorator


def skip_if_backend_unavailable(backend: str) -> Callable[..., Any]:
    """Decorator to skip test if backend is unavailable."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import pytest
            backend_lower = backend.lower()
            available = False
            if backend_lower == "rust":
                try:
                    import truthgpt_rust  # type: ignore
                    available = True
                except (ImportError, ModuleNotFoundError):
                    pass
            elif backend_lower == "cpp":
                try:
                    import _cpp_core  # type: ignore
                    available = True
                except (ImportError, ModuleNotFoundError):
                    pass
            elif backend_lower == "julia":
                try:
                    from julia import TruthGPTCore  # type: ignore
                    available = True
                except (ImportError, ModuleNotFoundError):
                    pass
            elif backend_lower in ("cuda", "gpu"):
                import torch
                available = torch.cuda.is_available()
            elif backend_lower == "python":
                available = True

            if not available:
                pytest.skip(f"Native backend '{backend}' not available.")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to measure and log function execution time."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        res = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return res, elapsed_ms
    return wrapper


__all__ = [
    "create_temp_directory",
    "cleanup_temp_directory",
    "create_test_config",
    "create_mock_processor",
    "create_mock_engine",
    "create_test_data_file",
    "load_test_data",
    "assert_dict_contains",
    "retry_on_failure",
    "skip_if_backend_unavailable",
    "measure_time",
]
