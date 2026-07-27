"""
Performance Monitoring and Hotspot Detection Subsystem for Runtime Compiler
"""

import time
import logging
import threading
import psutil
import gc
from collections import deque
from typing import Dict, List, Any, Optional, Callable

from ..config import OptimizationTrigger

logger = logging.getLogger(__name__)

class RuntimePerformanceMonitor:
    """Monitor encapsulating system metrics, profiling loops, and hotspot detection"""

    def __init__(self, config, execution_profiles: Dict[int, Dict[str, Any]], compilation_cache: Dict[str, Any]):
        self.config = config
        self.execution_profiles = execution_profiles
        self.compilation_cache = compilation_cache
        self.profiling_data = deque(maxlen=config.performance_window_size)
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False

    def start_monitoring(self):
        """Start background performance monitoring thread"""
        try:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Performance monitoring started")
        except Exception as e:
            logger.warning(f"Failed to start monitoring: {e}")

    def stop_monitoring(self, timeout: float = 5.0):
        """Stop background performance monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=timeout)

    def _monitoring_loop(self):
        while self.monitoring_active:
            try:
                cpu_percent = psutil.cpu_percent()
                memory_info = psutil.virtual_memory()

                compilation_metrics = {
                    "timestamp": time.time(),
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory_info.percent,
                    "memory_available": memory_info.available,
                    "active_compilations": len(self.execution_profiles),
                    "cache_size": len(self.compilation_cache)
                }

                self.profiling_data.append(compilation_metrics)
                self._check_optimization_triggers(compilation_metrics)
                time.sleep(self.config.monitoring_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(1.0)

    def _check_optimization_triggers(self, metrics: Dict[str, Any]):
        triggers = []
        if metrics["memory_usage"] > 80:
            triggers.append(OptimizationTrigger.MEMORY_PRESSURE.value)
        if metrics["cpu_usage"] > self.config.cpu_limit_percent:
            triggers.append(OptimizationTrigger.PERFORMANCE_THRESHOLD.value)
        if len(self.execution_profiles) > 10:
            triggers.append(OptimizationTrigger.HOTSPOT_DETECTION.value)

        if triggers:
            self._handle_triggers(triggers, metrics)

    def _handle_triggers(self, triggers: List[str], metrics: Dict[str, Any]):
        logger.info(f"Optimization triggers detected: {triggers}")
        for trigger in triggers:
            if trigger == OptimizationTrigger.MEMORY_PRESSURE.value:
                self.optimize_memory_usage()
            elif trigger == OptimizationTrigger.PERFORMANCE_THRESHOLD.value:
                self.optimize_performance()
            elif trigger == OptimizationTrigger.HOTSPOT_DETECTION.value:
                self.optimize_hotspots()

    def optimize_memory_usage(self):
        """Clean cache and invoke GC under memory pressure"""
        try:
            if len(self.compilation_cache) > self.config.cache_size // 2:
                self.cleanup_cache()
            gc.collect()
            logger.info("Memory optimization applied")
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")

    def optimize_performance(self):
        """Adaptively adjust compilation threshold under CPU load"""
        try:
            if self.config.compilation_threshold > 50:
                self.config.compilation_threshold = max(50, self.config.compilation_threshold // 2)
            logger.info("Performance optimization applied")
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")

    def optimize_hotspots(self):
        """Identify execution hotspots and elevate their optimization level"""
        try:
            hotspots = self.identify_hotspots()
            for hotspot in hotspots:
                model_id = hotspot["model_id"]
                if model_id in self.execution_profiles:
                    profile = self.execution_profiles[model_id]
                    profile["optimization_level"] = min(profile["optimization_level"] + 1, 7)
                    logger.info(f"Applied hotspot optimization to model {model_id}")
            logger.info(f"Hotspot optimization applied to {len(hotspots)} hotspots")
        except Exception as e:
            logger.error(f"Hotspot optimization failed: {e}")

    def identify_hotspots(self) -> List[Dict[str, Any]]:
        hotspots = []
        for model_id, profile in self.execution_profiles.items():
            if profile["execution_count"] > self.config.optimization_threshold:
                hotspots.append({
                    "model_id": model_id,
                    "execution_count": profile["execution_count"],
                    "total_time": profile["total_time"],
                    "optimization_level": profile["optimization_level"]
                })
        return hotspots

    def cleanup_cache(self):
        try:
            cache_items = list(self.compilation_cache.items())
            cache_items.sort(key=lambda x: x[1].get('timestamp', 0) if isinstance(x[1], dict) else 0)
            remove_count = len(cache_items) // 4
            for key, _ in cache_items[:remove_count]:
                del self.compilation_cache[key]
            logger.info(f"Cleaned up {remove_count} cache entries")
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    def calculate_memory_efficiency(self, model: Any, model_size_estimator: Callable) -> float:
        try:
            memory_usage = psutil.virtual_memory().percent
            return max(0.0, 1.0 - (memory_usage / 100.0))
        except Exception as e:
            logger.warning(f"Memory efficiency calculation failed: {e}")
            return 1.0

    def calculate_energy_efficiency(self, model: Any, model_size_estimator: Callable) -> float:
        try:
            cpu_usage = psutil.cpu_percent()
            return max(0.0, 1.0 - (cpu_usage / 100.0))
        except Exception as e:
            logger.warning(f"Energy efficiency calculation failed: {e}")
            return 1.0
