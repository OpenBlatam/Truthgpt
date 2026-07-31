try:
    from optimization_core.utils.advanced_logging import is_main_process, log_info
except (ImportError, ModuleNotFoundError):
    from utils.advanced_logging import is_main_process, log_info

__all__ = ["is_main_process", "log_info"]







