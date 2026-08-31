"""
Constants & Centralized Configuration Settings for TruthGPT Interface.
======================================================================
Provides terminal styling constants, engine registries, default timeouts,
banner texts, code block extension mappings, and environment variable bindings.
"""
from __future__ import annotations

from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Theme & Visual Constants
# ---------------------------------------------------------------------------

DEFAULT_THEME: str = "claude"
DEFAULT_USER_NAME: str = "Explorer"
DEFAULT_ENGINE: str = "deepseek"
DEFAULT_ENSEMBLE_MODE: str = "race"
DEFAULT_MCP_SERVERS: List[str] = ["http://localhost:8000"]
DEFAULT_VERSION: str = "TruthGPT v2.4.1"
SYSTEM_VERSION_BANNER: str = "v5.9.0-GOLD"

THEME_COLORS: Dict[str, str] = {
    "claude": "cyan",
    "anthropic": "cyan",
    "minimalist": "white",
    "industrial": "magenta",
}

THEME_FOCUSED_COLORS: Dict[str, str] = {
    "claude": "#00ffff",
    "anthropic": "#00ffff",
    "minimalist": "#00ffff",
    "industrial": "#ffbbff",
}


# ---------------------------------------------------------------------------
# API Key & Engine Mappings
# ---------------------------------------------------------------------------

API_KEY_ENV_MAP: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "telegram": "TELEGRAM_BOT_TOKEN",
    "discord": "DISCORD_BOT_TOKEN",
    "slack": "SLACK_BOT_TOKEN",
    "whatsapp": "WHATSAPP_API_KEY",
}

DEFAULT_API_CREDITS: Dict[str, float] = {
    "claude": 10.00,
    "openai": 10.00,
    "google": 10.00,
}

AVAILABLE_ENGINES: List[str] = [
    "deepseek",
    "google",
    "openrouter",
    "chatgpt",
    "claude",
]

# (Brand, Default Model, Pref Key, Env Key)
ENGINE_METADATA: Dict[str, Tuple[str, str, str, str]] = {
    "deepseek": ("DeepSeek", "deepseek-reasoner", "deepseek", "DEEPSEEK_API_KEY"),
    "google": ("Google Gemini", "gemini-2.0-flash-exp", "google", "GOOGLE_API_KEY"),
    "openrouter": ("OpenRouter Unified", "anthropic/claude-3.7-sonnet", "openrouter", "OPENROUTER_API_KEY"),
    "chatgpt": ("OpenAI (ChatGPT)", "gpt-4o", "openai", "OPENAI_API_KEY"),
    "claude": ("Anthropic Claude", "claude-3-7-sonnet-latest", "anthropic", "ANTHROPIC_API_KEY"),
}

OPENROUTER_MODELS: List[str] = [
    "anthropic/claude-3.7-sonnet",
    "google/gemini-3.5-flash",
    "google/gemini-3.5-pro",
    "deepseek/deepseek-r1",
    "openai/gpt-4.5-preview",
    "deepseek/deepseek-chat",
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
]

OPENROUTER_MODEL_NAMES: Dict[str, str] = {
    "anthropic/claude-3.7-sonnet": "Claude 3.7 Sonnet (Recommended)",
    "google/gemini-3.5-flash": "Gemini 3.5 Flash",
    "google/gemini-3.5-pro": "Gemini 3.5 Pro",
    "deepseek/deepseek-r1": "DeepSeek R1 (Reasoning)",
    "openai/gpt-4.5-preview": "GPT-4.5 (Research Preview)",
    "deepseek/deepseek-chat": "DeepSeek V3 (Chat)",
    "anthropic/claude-3.5-sonnet": "Claude 3.5 Sonnet",
    "openai/gpt-4o": "GPT-4o (Omni)",
    "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B Instruct",
    "qwen/qwen-2.5-72b-instruct": "Qwen 2.5 72B Instruct",
}


# ---------------------------------------------------------------------------
# Code Block Language Extension Map
# ---------------------------------------------------------------------------

CODE_EXTENSION_MAP: Dict[str, str] = {
    "python": ".py",
    "py": ".py",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "html": ".html",
    "htm": ".html",
    "css": ".css",
    "json": ".json",
    "rust": ".rs",
    "rs": ".rs",
    "go": ".go",
    "bash": ".sh",
    "sh": ".sh",
    "shell": ".sh",
    "powershell": ".ps1",
    "ps1": ".ps1",
    "c": ".c",
    "cpp": ".cpp",
    "c++": ".cpp",
    "java": ".java",
    "sql": ".sql",
    "yaml": ".yaml",
    "yml": ".yml",
}


# ---------------------------------------------------------------------------
# Timeouts & Defaults
# ---------------------------------------------------------------------------

DEFAULT_IDLE_TIMEOUT_SECONDS: int = 15
DEFAULT_BALANCE_CACHE_TTL_SECONDS: float = 60.0
DEFAULT_TELEMETRY_CACHE_TTL_SECONDS: float = 1.0
DEFAULT_INPUT_TIMEOUT_SECONDS: float = 30.0


# ---------------------------------------------------------------------------
# Default Banners & Header Strings
# ---------------------------------------------------------------------------

INDUSTRIAL_BANNER_ASCII: str = r"""
   _____                      _      _____  _____  _______
  |_   _| __ _   _  | |_  | |_   / ____||  __ \|__   __|
    | |  |  __| | | | | __| | __| | |  __ | |__) |  | |
    | |  | |  | |_| | | |_  | |_  | |__  ||  ___/   | |
    |_|  |_|   \__,_|  \__|  \__|  \_____||_|       |_|
"""

CLAUDE_BANNER_TOP: str = "\n    ▀█▀ █▀▄ █ █ ▀█▀ █ █ █▀▀ █▀█ ▀█▀\n"
CLAUDE_BANNER_BOT: str = "     █  █▀▄ █▄█  █  █▀█ █▄█ █▀  █ \n\n"

DEFAULT_HEADER_UPDATES: List[str] = [
    "SOTA Hybrid Architecture v5.9",
    "Zero Latency Neural Boot",
    "API Budget & Cost Live-Sync",
    "Sandbox Security Hardened",
]
