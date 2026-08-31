"""
User Preferences & Configuration Management for TruthGPT Interface.
===================================================================
Handles persistent storage of user preferences, API keys, ensemble configuration,
and self-healing recovery against corrupted configuration files.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from interface.constants import (
    API_KEY_ENV_MAP,
    DEFAULT_API_CREDITS,
    DEFAULT_ENGINE,
    DEFAULT_THEME,
    DEFAULT_USER_NAME,
)
from interface.interfaces import BasePreferenceManager, IPreferenceManager
from interface.types import UserPreferencesDict

logger = logging.getLogger(__name__)

# Load .env variables from workspace root
try:
    from dotenv import load_dotenv

    _current = Path(__file__).resolve().parent
    _workspace_env: Optional[Path] = None
    for _ in range(20):
        if (_current / ".git").exists() or _current.name == "blatam-academy":
            if (_current / ".env").exists():
                _workspace_env = _current / ".env"
                break
        if _current.parent == _current:
            break
        _current = _current.parent

    if _workspace_env:
        load_dotenv(_workspace_env, override=True)
    else:
        _current = Path(__file__).resolve().parent
        for _ in range(10):
            _env_path = _current / ".env"
            if _env_path.exists():
                load_dotenv(_env_path, override=True)
                break
            if _current.parent == _current:
                break
            _current = _current.parent
except Exception:
    pass

# --- Path Initialization ---
current_dir: Path = Path(__file__).resolve().parent.parent
CONFIG_PATH: Path = current_dir / "user_preferences.json"

DEFAULT_USER_PREFS: Dict[str, Any] = {
    "user_name": DEFAULT_USER_NAME,
    "preferred_engine": "deepseek",
    "theme": DEFAULT_THEME,
    "continuous_mode": False,
    "mcp_servers": ["http://localhost:8000"],
    "api_keys": {
        "telegram": "",
        "discord": "",
        "slack": "",
        "whatsapp": "",
        "openai": "",
        "deepseek": "",
        "anthropic": "",
        "google": "",
        "openrouter": "",
    },
    "api_credits": dict(DEFAULT_API_CREDITS),
    "ensemble_mode": "race",
    "google_access_token": "",
    "google_service_account": "",
    "engine_models": {},
    "mcts_optimized": False,
    "speculative_decoding": False,
    "kv_quantization": False,
    "dpo_truth_bias": False,
    "rag_fusion_opt": False,
    "cove_hallucination_control": False,
    "math_formalizer": False,
    "sota_injection": False,
    "self_refinement": False,
    "flash_attention_v3": False,
    "dynamic_lora": False,
    "forensic_audit": False,
    "cross_model_moe": False,
    "cache_warming": False,
}


def load_user_prefs(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load user preferences from CONFIG_PATH with fallback to defaults and corruption recovery."""
    target_path = path or CONFIG_PATH
    defaults = dict(DEFAULT_USER_PREFS)
    defaults["api_keys"] = dict(DEFAULT_USER_PREFS["api_keys"])
    defaults["api_credits"] = dict(DEFAULT_USER_PREFS["api_credits"])
    defaults["engine_models"] = dict(DEFAULT_USER_PREFS.get("engine_models", {}))

    if target_path.exists():
        try:
            loaded = json.loads(target_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                if "api_keys" in loaded and isinstance(loaded["api_keys"], dict):
                    defaults["api_keys"].update(loaded["api_keys"])
                if "api_credits" in loaded and isinstance(loaded["api_credits"], dict):
                    defaults["api_credits"].update(loaded["api_credits"])
                if "engine_models" in loaded and isinstance(loaded["engine_models"], dict):
                    defaults["engine_models"].update(loaded["engine_models"])
                defaults.update(loaded)
        except Exception as e:
            logger.warning(f"Corrupted user preferences detected, resetting: {e}")
            try:
                corrupt_backup = target_path.with_suffix(".corrupt")
                if target_path.exists():
                    if corrupt_backup.exists():
                        corrupt_backup.unlink()
                    target_path.rename(corrupt_backup)
            except Exception:
                pass
    return defaults


def save_user_prefs(prefs: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Atomically save user preferences to disk and notify engine cache."""
    target_path = path or CONFIG_PATH
    try:
        temp_path = target_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(prefs, indent=4), encoding="utf-8")
        if temp_path.exists():
            if target_path.exists():
                target_path.unlink()
            temp_path.rename(target_path)
    except Exception:
        try:
            target_path.write_text(json.dumps(prefs, indent=4), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to write user preferences: {e}")

    # Synchronize updated API keys with os.environ
    if "api_keys" in prefs and isinstance(prefs["api_keys"], dict):
        for pref_key, env_key in API_KEY_ENV_MAP.items():
            val = prefs["api_keys"].get(pref_key)
            if val:
                os.environ[env_key] = val

    _invalidate_llm_client_cache()


def _invalidate_llm_client_cache() -> None:
    """Force swarm/client to rebuild LLM engine after prefs change."""
    try:
        import interface.swarm_menu as swarm_menu

        swarm_menu._client_cache = None
    except Exception:
        pass


class PreferenceManager(BasePreferenceManager, IPreferenceManager):
    """Concrete implementation of IPreferenceManager."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_PATH
        self._prefs = load_user_prefs(self.config_path)

    def load(self) -> Dict[str, Any]:
        self._prefs = load_user_prefs(self.config_path)
        return self._prefs

    def load_preferences(self) -> Dict[str, Any]:
        return self.load()

    def save(self, prefs: Dict[str, Any]) -> None:
        self._prefs = prefs
        save_user_prefs(prefs, self.config_path)

    def save_preferences(self, prefs: Dict[str, Any]) -> None:
        self.save(prefs)

    def get(self, key: str, default: Any = None) -> Any:
        return self._prefs.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._prefs[key] = value
        self.save(self._prefs)


USER_PREFS: Dict[str, Any] = load_user_prefs()

# Key mapping alias for backwards compatibility
KEY_MAPPING = API_KEY_ENV_MAP

# Populate environment variables from USER_PREFS api_keys
if "api_keys" in USER_PREFS and isinstance(USER_PREFS["api_keys"], dict):
    for pref_key, env_key in API_KEY_ENV_MAP.items():
        val = USER_PREFS["api_keys"].get(pref_key)
        if val and not os.environ.get(env_key):
            os.environ[env_key] = val
