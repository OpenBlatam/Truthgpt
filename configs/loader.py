"""Configuration loader utility for merging YAML files, environment variables, and CLI overrides."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

import yaml

from .schema import AppCfg


def _set_in(dct: Dict[str, Any], keys: List[str], value: Any) -> None:
    cur = dct
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def parse_overrides(kvs: Optional[List[str]]) -> Dict[str, Any]:
    """Parse dotted dot-notation overrides like 'training.learning_rate=0.001' into nested dicts."""
    result: Dict[str, Any] = {}
    if not kvs:
        return result
    for item in kvs:
        if "=" not in item:
            continue
        key, val = item.split("=", 1)
        _set_in(result, key.split("."), _parse_scalar(val))
    return result


def _parse_scalar(v: str) -> Any:
    if v.lower() in {"true", "false"}:
        return v.lower() == "true"
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dictionary b into dictionary a."""
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def parse_env_overrides(prefix: str = "OPTIM_CORE_") -> Dict[str, Any]:
    """Extract environment variable overrides matching a specified prefix."""
    result: Dict[str, Any] = {}
    for key, val in os.environ.items():
        if key.startswith(prefix):
            clean_key = key[len(prefix):].lower().replace("__", ".")
            _set_in(result, clean_key.split("."), _parse_scalar(val))
    return result


def load_config(path: str | Path, overrides: Optional[List[str]] = None, use_env: bool = True) -> AppCfg:
    """Load, merge, and validate AppCfg from a YAML file, environment variables, and CLI overrides."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        base: Dict[str, Any] = yaml.safe_load(f) or {}

    merged = base
    if use_env:
        merged = deep_merge(merged, parse_env_overrides())
    if overrides:
        merged = deep_merge(merged, parse_overrides(overrides))

    return AppCfg.from_dict(merged)


def save_config(config: AppCfg, path: str | Path, format: str = "yaml") -> None:
    """Save AppCfg object to a YAML or JSON file."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    dict_data = config.to_dict()

    if format.lower() == "yaml":
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(dict_data, f, default_flow_style=False, sort_keys=False)
    elif format.lower() == "json":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config.to_json(indent=2))
    else:
        raise ValueError(f"Unsupported format '{format}'. Use 'yaml' or 'json'.")


def get_preset_config(preset_name: str = "default") -> AppCfg:
    """Retrieve a pre-configured AppCfg preset instance."""
    presets_dir = Path(__file__).parent / "presets"
    preset_file = presets_dir / f"{preset_name}.yaml"
    if preset_file.exists():
        return load_config(preset_file, use_env=False)
    # Default fallback instance
    return AppCfg()


__all__ = [
    "load_config",
    "save_config",
    "get_preset_config",
    "deep_merge",
    "parse_overrides",
    "parse_env_overrides",
]

