"""Alias loader module pointing to configs.loader."""

try:
    from configs.loader import (
        load_config,
        parse_overrides,
        deep_merge,
        parse_env_overrides,
    )
except ImportError:
    from ..configs.loader import (
        load_config,
        parse_overrides,
        deep_merge,
        parse_env_overrides,
    )

__all__ = [
    "load_config",
    "parse_overrides",
    "deep_merge",
    "parse_env_overrides",
]
