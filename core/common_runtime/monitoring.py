"""
Performance and System Monitoring for Common Runtime.
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors latency, execution time, and throughput."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.start_time: Optional[float] = None
        self.elapsed: float = 0.0

    def start(self) -> None:
        """Start timer."""
        self.start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop timer and return elapsed seconds."""
        if self.start_time is not None:
            self.elapsed = time.perf_counter() - self.start_time
            self.start_time = None
        return self.elapsed

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            "name": self.name,
            "elapsed_seconds": self.elapsed,
            "elapsed_ms": self.elapsed * 1000.0,
        }

