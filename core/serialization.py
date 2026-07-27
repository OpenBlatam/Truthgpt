"""
Serialization utilities for optimization_core.

Provides common serialization/deserialization patterns with support for:
- JSON (with gzip compression)
- YAML
- Pickle (with compression)
- Dictionary conversion
"""
import json
import pickle
import gzip
from typing import Any, Dict, Optional, Union
from pathlib import Path
import logging

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


def ensure_output_directory(file_path: Union[str, Path]) -> Path:
    """Ensure output directory exists, creating it if necessary."""
    path_obj = Path(file_path)
    output_dir = path_obj.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def validate_path(file_path: Union[str, Path], must_exist: bool = True, must_be_file: bool = False) -> Path:
    """Validate file path existence and type."""
    path_obj = Path(file_path)
    if must_exist and not path_obj.exists():
        raise FileNotFoundError(f"Path does not exist: {file_path}")
    if must_be_file and path_obj.exists() and not path_obj.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    return path_obj


def to_dict(obj: Any, exclude_none: bool = False, exclude_defaults: bool = False) -> Dict[str, Any]:
    """Convert object to dictionary."""
    if hasattr(obj, 'to_dict'):
        result = obj.to_dict(exclude_none=exclude_none, exclude_defaults=exclude_defaults)
    elif hasattr(obj, '__dict__'):
        result = obj.__dict__
    else:
        return obj

    if exclude_none and isinstance(result, dict):
        result = {k: v for k, v in result.items() if v is not None}

    return result


def from_dict(cls: type, data: Dict[str, Any], strict: bool = True) -> Any:
    """Create object from dictionary."""
    if hasattr(cls, 'from_dict'):
        return cls.from_dict(data, strict=strict)
    else:
        return cls(**data)


def to_json(
    obj: Any,
    file_path: Optional[Union[str, Path]] = None,
    indent: int = 2,
    exclude_none: bool = False,
    compress: bool = False
) -> Union[str, None]:
    """Serialize object to JSON."""
    data = to_dict(obj, exclude_none=exclude_none)
    json_str = json.dumps(data, indent=indent, ensure_ascii=False, default=str)

    if file_path:
        path = Path(file_path)
        ensure_output_directory(path)

        if compress:
            path = path.with_suffix(path.suffix + '.gz')
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                f.write(json_str)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        logger.debug(f"Saved JSON to {path}")
        return None
    else:
        return json_str


def save_json(
    data: Any,
    file_path: Union[str, Path],
    indent: int = 2,
    compress: bool = False
) -> None:
    """Save data to JSON file."""
    to_json(data, file_path=file_path, indent=indent, compress=compress)


def from_json(
    json_str: Optional[str] = None,
    file_path: Optional[Union[str, Path]] = None,
    cls: Optional[type] = None,
    compressed: Optional[bool] = None
) -> Union[Dict[str, Any], Any]:
    """Deserialize JSON to object."""
    if file_path:
        path = Path(file_path)

        if compressed is None:
            compressed = path.suffix == '.gz'

        if compressed:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            path = validate_path(path, must_exist=True, must_be_file=True)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    elif json_str:
        data = json.loads(json_str)
    else:
        raise ValueError("Either json_str or file_path must be provided")

    if cls:
        return from_dict(cls, data)
    return data


def load_json(
    file_path: Union[str, Path],
    compressed: Optional[bool] = None
) -> Any:
    """Load data from JSON file."""
    return from_json(file_path=file_path, compressed=compressed)


def to_pickle(
    obj: Any,
    file_path: Union[str, Path],
    protocol: int = pickle.HIGHEST_PROTOCOL
) -> None:
    """Serialize object to pickle file."""
    path = Path(file_path)
    ensure_output_directory(path)

    with open(path, 'wb') as f:
        pickle.dump(obj, f, protocol=protocol)

    logger.debug(f"Saved pickle to {file_path}")


def from_pickle(file_path: Union[str, Path]) -> Any:
    """Deserialize object from pickle file."""
    path = validate_path(file_path, must_exist=True, must_be_file=True)

    with open(path, 'rb') as f:
        return pickle.load(f)


def safe_serialize(obj: Any, default: Any = None) -> Any:
    """Safely serialize object, handling non-serializable types."""
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        try:
            return to_dict(obj)
        except Exception:
            return default if default is not None else str(obj)


__all__ = [
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
    "save_json",
    "load_json",
    "to_pickle",
    "from_pickle",
    "safe_serialize",
]
