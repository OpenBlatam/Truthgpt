"""
Common helper utilities for optimization_core.

Provides decorators, context managers, and utility functions
shared across all modules.
"""
import logging
import time
from typing import Callable, Optional, Dict, Any, TypeVar, List
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable)


def ensure_initialized(attr_name: str = '_initialized', error_message: Optional[str] = None):
    """Decorator to ensure object is initialized before calling method."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not getattr(self, attr_name, False):
                class_name = self.__class__.__name__
                message = error_message or f"{class_name} is not initialized. Call initialization first."
                raise RuntimeError(message)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def timing(operation_name: Optional[str] = None, log_level: int = logging.DEBUG):
    """Decorator to measure and log function execution time."""
    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__
        log = logging.getLogger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                log.log(log_level, f"{op_name} took {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                log.error(f"{op_name} failed after {elapsed:.3f}s: {e}")
                raise
        return wrapper
    return decorator


def handle_errors(
    error_type: type = Exception,
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = True
):
    """Decorator to handle errors with optional logging and default return."""
    def decorator(func: F) -> F:
        log = logging.getLogger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                if log_error:
                    log.error(f"{func.__name__} raised {type(e).__name__}: {e}", exc_info=True)
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator to retry function with exponential backoff."""
    def decorator(func: F) -> F:
        log = logging.getLogger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        log.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        log.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}",
                            exc_info=True
                        )

            raise last_exception
        return wrapper
    return decorator


@contextmanager
def timing_context(operation_name: str, logger_instance: Optional[logging.Logger] = None):
    """Context manager for timing operations."""
    log = logger_instance or logger
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        log.debug(f"{operation_name} took {elapsed:.3f}s")


@contextmanager
def error_context(operation: str, **context):
    """Context manager for error handling with context."""
    log = logging.getLogger(__name__)
    log.debug(f"Starting {operation}", extra=context)
    try:
        yield
        log.debug(f"Completed {operation}", extra=context)
    except Exception as e:
        log.error(
            f"Failed {operation}: {e}",
            extra={"operation": operation, **context},
            exc_info=True
        )
        raise


def batch_items(items: List[T], batch_size: int, truncate: bool = False) -> List[List[T]]:
    """Split items into batches of specified size."""
    if not isinstance(items, list):
        raise TypeError(f"items must be a list, got {type(items).__name__}")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")

    if not items:
        return []

    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

    if truncate and batches and len(batches[-1]) < batch_size:
        batches = batches[:-1]

    return batches


def format_duration(seconds: float, precision: int = 3) -> str:
    """Format duration in human-readable format with appropriate units."""
    if seconds < 0:
        raise ValueError(f"seconds must be non-negative, got {seconds}")
    if precision < 0:
        raise ValueError(f"precision must be non-negative, got {precision}")

    if seconds < 60:
        return f"{seconds:.{precision}f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.{precision}f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.{precision}f}s"


def format_size(size_bytes: int) -> str:
    """Format size in human-readable format with appropriate units."""
    if size_bytes < 0:
        raise ValueError(f"size_bytes must be non-negative, got {size_bytes}")

    if size_bytes == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.1f} {units[unit_index]}"


def safe_get(dictionary: Dict[str, Any], *keys, default: Any = None) -> Any:
    """Safely get nested dictionary values."""
    current = dictionary
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


__all__ = [
    "ensure_initialized",
    "timing",
    "handle_errors",
    "retry",
    "timing_context",
    "error_context",
    "batch_items",
    "format_duration",
    "format_size",
    "safe_get",
    "chunk_list",
]
