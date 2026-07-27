"""
LLM Engine Registry and Providers Package.
"""

from __future__ import annotations

import sys
from . import engine_registry
from . import engine_config
from . import engine_providers
from . import engine_benchmark

from .engine_registry import EngineRegistry, engine_registry as engine_registry_instance
from .engine_config import _get_user_prefs, _load_api_keys_from_prefs, _normalize_engine_key, _resolve_api_key
from .engine_providers import (
    BaseProvider,
    DeepSeekProvider,
    GoogleGeminiProvider,
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
    AsyncLLMEngine,
    DummyAsyncLLM,
)

__all__ = [
    "engine_registry",
    "engine_config",
    "engine_providers",
    "engine_benchmark",
    "EngineRegistry",
    "engine_registry_instance",
    "_get_user_prefs",
    "_load_api_keys_from_prefs",
    "_normalize_engine_key",
    "_resolve_api_key",
    "BaseProvider",
    "DeepSeekProvider",
    "GoogleGeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OpenRouterProvider",
    "AsyncLLMEngine",
    "DummyAsyncLLM",
]
