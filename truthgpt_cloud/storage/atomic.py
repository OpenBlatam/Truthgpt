"""
💾 TruthGPT Cloud - Atomic Persistent Storage
Provides crash-safe JSON serialization with atomic tempfile replacement and automatic recovery.
"""

import json
import os
import shutil
import tempfile
import threading
import time
import logging
from typing import Dict, Any

logger = logging.getLogger("TruthGPT.CloudStorage")


class AtomicJsonStorage:
    """Thread-safe and process-safe atomic JSON file persistence."""

    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self._lock = threading.RLock()
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        parent = os.path.dirname(os.path.abspath(self.file_path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load JSON data from file or return empty dict on missing/corrupted file."""
        with self._lock:
            if not os.path.exists(self.file_path):
                return {}
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error(f"Failed to read storage file '{self.file_path}': {e}. Creating backup.")
                backup_path = f"{self.file_path}.corrupted_{os.getpid()}"
                try:
                    shutil.copyfile(self.file_path, backup_path)
                except Exception:
                    pass
                return {}

    def save(self, data: Dict[str, Any]) -> bool:
        """Write JSON data atomically using a temporary file with Windows file lock tolerance."""
        with self._lock:
            self._ensure_parent_dir()
            parent_dir = os.path.dirname(os.path.abspath(self.file_path))
            temp_fd, temp_path = tempfile.mkstemp(
                prefix="tgpt_sub_",
                suffix=".tmp",
                dir=parent_dir
            )
            try:
                with open(temp_fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Atomic replace with retries for Windows file lock tolerance
                replaced = False
                for attempt in range(5):
                    try:
                        os.replace(temp_path, self.file_path)
                        replaced = True
                        break
                    except (PermissionError, OSError):
                        time.sleep(0.02 * (attempt + 1))

                if not replaced:
                    shutil.move(temp_path, self.file_path)
                return True
            except Exception as e:
                logger.error(f"Failed to atomically write storage to '{self.file_path}': {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                return False


__all__ = ["AtomicJsonStorage"]
