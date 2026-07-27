"""
Utility functions for OpenClaw Agent Framework.
System 6.0 Gold Standard — High performance, robust parsing, and resilience.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import math
import random
import re
import time
import traceback
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Type, TypeVar, Union
from pydantic import ValidationError

try:
    from .models import AgentAction
except ImportError:
    try:
        from agents.framework.models import AgentAction
    except ImportError:
        from optimization_core.agents.framework.models import AgentAction

T = TypeVar("T")

# Precompiled regex patterns for maximum execution efficiency
JSON_CODE_BLOCK_PATTERN = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.DOTALL)
JSON_OBJECT_PATTERN = re.compile(r'(\{.*\})', re.DOTALL)
MARKDOWN_CODE_BLOCK_PATTERN = re.compile(r'^```(?:\w+)?\n?(.*?)\n?```$', re.DOTALL)
URL_REGEX_PATTERN = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')


def parse_agent_action(response: str) -> AgentAction:
    """
    Parses a JSON response from the LLM into an AgentAction object.
    If parsing fails, treats the response as a plain text final_answer.
    """
    if not response or not response.strip():
        return AgentAction(final_answer="[Empty response from model]")

    clean_resp = response.strip()
    
    # Attempt to extract JSON block using regex
    json_match = JSON_CODE_BLOCK_PATTERN.search(clean_resp)
    if json_match:
        candidate = json_match.group(1).strip()
    else:
        json_match = JSON_OBJECT_PATTERN.search(clean_resp)
        candidate = json_match.group(1).strip() if json_match else clean_resp
            
    try:
        action = AgentAction.model_validate_json(candidate)
        # If the LLM returned a valid JSON but forgot all expected keys, treat it as plain text final answer
        if not action.tool and not action.final_answer and not action.handoff:
            raw_dict = json.loads(candidate)
            possible_text = (
                raw_dict.get("response")
                or raw_dict.get("answer")
                or raw_dict.get("text")
                or raw_dict.get("message")
                or raw_dict.get("content")
                or raw_dict.get("result")
            )
            if possible_text:
                return AgentAction(final_answer=str(possible_text))
            return AgentAction(final_answer=clean_resp)
        return action
    except (ValidationError, json.JSONDecodeError, ValueError):
        # Fallback to AgentAction.parse_from_text or direct final_answer string
        return AgentAction.parse_from_text(clean_resp)


def safe_json_loads(data: str, default: Optional[Any] = None) -> Any:
    """Safely decode JSON string returning default on decode failure."""
    if not data or not isinstance(data, str):
        return default
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize an object to JSON string with fallback."""
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return default


def clean_markdown_code_blocks(text: str) -> str:
    """Strip top-level markdown code fence blocks if wrapping the entire string."""
    if not text:
        return ""
    text = text.strip()
    match = MARKDOWN_CODE_BLOCK_PATTERN.match(text)
    if match:
        return match.group(1).strip()
    return text


def format_exception_trace(exc: Exception) -> str:
    """Format an exception and traceback into a clean string for logging/telemetry."""
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def truncate_text_safely(text: str, max_length: int = 2000, suffix: str = "... [truncated]") -> str:
    """Truncate long text content without cutting in the middle of UTF-8 boundaries."""
    if not text or len(text) <= max_length:
        return text
    return text[: max(0, max_length - len(suffix))] + suffix


def sanitize_tool_input(input_val: Any) -> Any:
    """Ensure tool input value is safe for execution and string/dict formatting."""
    if isinstance(input_val, str):
        return input_val.strip()
    if isinstance(input_val, dict):
        return {k: sanitize_tool_input(v) for k, v in input_val.items()}
    if isinstance(input_val, list):
        return [sanitize_tool_input(item) for item in input_val]
    return input_val


def extract_urls(text: str) -> List[str]:
    """Extract all HTTP/HTTPS URLs from a given text string."""
    if not text:
        return []
    return URL_REGEX_PATTERN.findall(text)


def chunk_iterable(items: List[T], chunk_size: int) -> List[List[T]]:
    """Divide a list into smaller chunks of size chunk_size."""
    if chunk_size <= 0:
        return [items]
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def estimate_token_count(text: str) -> int:
    """Rough estimation of token count for prompt budget calculations (approx 4 chars per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def deep_merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries, giving precedence to override values."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


@contextlib.asynccontextmanager
async def execution_timer() -> AsyncGenerator[Dict[str, float], None]:
    """
    Async context manager for measuring block execution duration in milliseconds.
    Yields a dictionary `{"duration_ms": 0.0}` that is populated upon exit.
    """
    stats: Dict[str, float] = {"duration_ms": 0.0}
    start_time = time.perf_counter()
    try:
        yield stats
    finally:
        stats["duration_ms"] = (time.perf_counter() - start_time) * 1000.0


async def async_retry_with_backoff(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple[Type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """
    Executes an async or sync function with exponential backoff and randomized jitter.
    """
    delay = initial_delay
    last_exception: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            else:
                return fn(*args, **kwargs)
        except retry_exceptions as e:
            last_exception = e
            if attempt == max_retries:
                break
            sleep_duration = delay * (random.uniform(0.8, 1.2) if jitter else 1.0)
            await asyncio.sleep(sleep_duration)
            delay *= backoff_factor
    if last_exception:
        raise last_exception


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """
    Execute an async function with exponential backoff retries.
    """
    return await async_retry_with_backoff(
        func,
        *args,
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor,
        retry_exceptions=exceptions,
        **kwargs,
    )



