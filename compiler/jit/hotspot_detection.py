"""
Hotspot Detection module for TruthGPT JIT Compiler
Performance profiling and hotspot identification
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class HotspotDetector:
    """Detects execution hotspots in computation graphs and subroutines."""

    def __init__(self, threshold_executions: int = 100):
        self.threshold = threshold_executions
        self.call_counts: Dict[str, int] = {}
        self.execution_times: Dict[str, float] = {}

    def record_execution(self, name: str, execution_time: float):
        """Record a single execution of a component."""
        self.call_counts[name] = self.call_counts.get(name, 0) + 1
        self.execution_times[name] = self.execution_times.get(name, 0.0) + execution_time

    def is_hotspot(self, name: str) -> bool:
        """Check if a named component exceeds hotspot threshold."""
        return self.call_counts.get(name, 0) >= self.threshold

    def get_hotspots(self) -> List[str]:
        """Return list of identified hotspot identifiers."""
        return [name for name, count in self.call_counts.items() if count >= self.threshold]


class HotspotAnalyzer:
    """Analyzes profile metrics for compiler optimization triggers."""

    def __init__(self, detector: Optional[HotspotDetector] = None):
        self.detector = detector or HotspotDetector()

    def analyze_hotspots(self) -> Dict[str, Any]:
        """Generate analysis report of hotspots."""
        hotspots = self.detector.get_hotspots()
        report = {
            "total_monitored": len(self.detector.call_counts),
            "hotspot_count": len(hotspots),
            "hotspots": hotspots
        }
        return report


class PerformanceProfiler:
    """Profiler for model execution latency and call metrics."""

    def __init__(self):
        self.records: Dict[str, List[float]] = {}

    def start_profiling(self, name: str):
        """Mark start of execution profiling."""
        if name not in self.records:
            self.records[name] = []

    def stop_profiling(self, name: str, duration: float):
        """Record execution duration."""
        if name in self.records:
            self.records[name].append(duration)

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics of profiled operations."""
        summary = {}
        for name, times in self.records.items():
            if times:
                summary[name] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times)
                }
        return summary


def create_hotspot_detector(threshold: int = 100) -> HotspotDetector:
    """Factory function for HotspotDetector."""
    return HotspotDetector(threshold_executions=threshold)


@contextmanager
def hotspot_analysis_context(threshold: int = 100):
    """Context manager for hotspot analysis."""
    detector = create_hotspot_detector(threshold)
    try:
        yield detector
    finally:
        pass
