import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from loguru import logger

_ENGINE_ALIASES = {
    "anthropic": "claude",
    "openai": "chatgpt",
}

def _normalize_engine_key(name: str) -> str:
    if not name:
        return ""
    return _ENGINE_ALIASES.get(name.strip().lower(), name.strip().lower())

_PREFS_CACHE: Optional[Dict] = None

def _find_user_prefs_file() -> Optional[Path]:
    candidates = [
        Path.cwd() / "user_preferences.json",
        Path(__file__).resolve().parent.parent.parent.parent / "user_preferences.json",
        Path(__file__).resolve().parent.parent.parent / "user_preferences.json",
        Path(__file__).resolve().parent.parent / "user_preferences.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def _load_api_keys_from_prefs() -> Dict[str, str]:
    """Load API keys from user_preferences.json as a fallback when env vars are not set."""
    global _PREFS_CACHE
    if _PREFS_CACHE is not None:
        return _PREFS_CACHE
    _PREFS_CACHE = {}
    try:
        prefs_path = _find_user_prefs_file()
        if prefs_path and prefs_path.exists():
            data = json.loads(prefs_path.read_text())
            raw_keys = data.get("api_keys", {})
            mapping = {
                "openai": "OPENAI_API_KEY",
                "deepseek": "DEEPSEEK_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY",
                "openrouter": "OPENROUTER_API_KEY",
            }
            for pref_key, env_key in mapping.items():
                val = raw_keys.get(pref_key, "")
                if val:
                    _PREFS_CACHE[env_key] = val
                    if not os.environ.get(env_key):
                        os.environ[env_key] = val
    except Exception as e:
        logger.debug(f"Could not load API keys from preferences: {e}")
    return _PREFS_CACHE

def _resolve_api_key(env_var: str, explicit_key: Optional[str] = None) -> Optional[str]:
    """Resolve an API key from: explicit arg > env var > user_preferences.json."""
    if explicit_key:
        return explicit_key
    env_val = os.getenv(env_var)
    if env_val:
        return env_val
    prefs_keys = _load_api_keys_from_prefs()
    return prefs_keys.get(env_var)

def _get_user_prefs() -> Dict[str, Any]:
    try:
        prefs_path = _find_user_prefs_file()
        if prefs_path and prefs_path.exists():
            return json.loads(prefs_path.read_text())
    except Exception:
        pass
    return {}
