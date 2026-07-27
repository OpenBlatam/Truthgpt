"""
Unit test suite for new trainers subsystems: TrainingProfiler, MetricTracker, DistributedManager.
"""
import time
import unittest
import torch

from trainers.profiler import TrainingProfiler
from trainers.metrics_tracker import MetricTracker
from trainers.dist_manager import DistributedManager


class TestNewSubsystems(unittest.TestCase):

    def test_training_profiler(self):
        """Test TrainingProfiler step measurement and throughput metrics."""
        profiler = TrainingProfiler(enabled=True)
        profiler.start()

        step_start = profiler.step_start()
        time.sleep(0.01)
        metrics = profiler.step_end(step_start, num_tokens=100)

        self.assertIn("step_latency_sec", metrics)
        self.assertIn("tokens_per_sec", metrics)
        self.assertGreater(metrics["tokens_per_sec"], 0.0)

        summary = profiler.summary()
        self.assertEqual(summary["total_steps"], 1)
        self.assertEqual(summary["total_tokens"], 100)
        self.assertGreater(summary["avg_tokens_per_sec"], 0.0)

    def test_metric_tracker(self):
        """Test MetricTracker sliding window statistics and moving averages."""
        tracker = MetricTracker(window_size=5)
        for val in [1.0, 2.0, 3.0, 4.0, 5.0]:
            tracker.update("loss", val)

        self.assertEqual(tracker.get_latest("loss"), 5.0)
        self.assertEqual(tracker.get_avg("loss"), 3.0)
        self.assertEqual(tracker.get_min("loss"), 1.0)
        self.assertEqual(tracker.get_max("loss"), 5.0)

        summary = tracker.summary()
        self.assertIn("loss", summary)
        self.assertEqual(summary["loss"]["count"], 5.0)

    def test_distributed_manager(self):
        """Test DistributedManager environment queries and rank properties."""
        dist_mgr = DistributedManager()
        self.assertTrue(dist_mgr.is_main_process)
        self.assertEqual(dist_mgr.rank, 0)
        self.assertEqual(dist_mgr.world_size, 1)

        info = dist_mgr.info()
        self.assertIn("is_main_process", info)
        self.assertIn("rank", info)
        self.assertIn("world_size", info)


if __name__ == "__main__":
    unittest.main()
