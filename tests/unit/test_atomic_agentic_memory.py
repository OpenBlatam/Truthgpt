"""Unit tests for AtomMem atomic-operation agentic memory (arXiv:2601.08323v2).

Covers the paper's core promise: route each incoming observation through an atomic
operation (ADD / UPDATE / DELETE / NOOP) so the store stays compact, fresh, and
non-redundant, with an operation log that makes the state replayable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from papers.atomic_agentic_memory import AtomicAgenticMemory  # noqa: E402
from latency_optimizations import apply_atomic_memory  # noqa: E402


def test_first_observation_is_added():
    """An empty store has nothing to match, so the first op is always ADD."""
    mem = AtomicAgenticMemory()
    decision = mem.ingest("the deployment finished successfully")
    assert decision["op"] == "ADD"
    assert decision["similarity"] == 0.0
    assert len(mem.snapshot()) == 1


def test_near_duplicate_is_noop():
    """An (almost) identical observation is dropped as redundant (NOOP)."""
    mem = AtomicAgenticMemory()
    mem.ingest("latency is nominal this cycle")
    decision = mem.ingest("latency is nominal this cycle")
    assert decision["op"] == "NOOP"
    assert len(mem.snapshot()) == 1  # nothing added


def test_same_topic_new_detail_updates_and_merges():
    """Same-topic-but-new-detail triggers UPDATE, merging into the existing item."""
    mem = AtomicAgenticMemory(dup_threshold=0.9, update_threshold=0.3)
    mem.ingest("memory usage rising")
    decision = mem.ingest("memory usage rising fast across all worker nodes now")
    assert decision["op"] == "UPDATE"
    snap = mem.snapshot()
    assert len(snap) == 1  # merged, not appended
    # UPDATE keeps the longer/more informative content and bumps the hit count.
    assert snap[0]["content"] == "memory usage rising fast across all worker nodes now"
    assert snap[0]["hits"] == 2


def test_novel_observation_is_added():
    """A semantically unrelated observation is ADDed as a new item."""
    mem = AtomicAgenticMemory()
    mem.ingest("latency is nominal")
    decision = mem.ingest("disk encryption keys rotated by the security service")
    assert decision["op"] == "ADD"
    assert len(mem.snapshot()) == 2


def test_thresholds_partition_similarity_band():
    """dup_threshold and update_threshold define the NOOP / UPDATE / ADD bands."""
    mem = AtomicAgenticMemory(dup_threshold=0.85, update_threshold=0.45)
    assert mem.dup_threshold > mem.update_threshold


def test_process_reports_op_profile_and_compression():
    """process() aggregates op counts and reports the resulting compression."""
    obs = [
        "latency nominal",
        "latency nominal",          # NOOP (duplicate)
        "memory usage rising",
        "disk io spike detected",
    ]
    result = apply_atomic_memory(obs)
    counts = result["op_counts"]
    assert counts["NOOP"] == 1
    assert result["redundancy_dropped"] == counts["NOOP"]
    assert result["observations_ingested"] == 4
    # 4 ingested, 1 redundant dropped -> 3 retained.
    assert result["memory_size"] == 3
    assert result["compression_ratio"] == pytest.approx(1 - 3 / 4)


def test_operation_log_records_every_decision():
    """Every ingest appends one entry to the replayable operation log."""
    mem = AtomicAgenticMemory()
    for obs in ["a one", "a one", "b two", "c three"]:
        mem.ingest(obs)
    assert len(mem._log) == 4
    assert {d["op"] for d in mem._log} <= {"ADD", "UPDATE", "DELETE", "NOOP"}


def test_empty_batch_is_safe():
    """An empty batch yields a zeroed, well-formed profile."""
    result = apply_atomic_memory([])
    assert result["memory_size"] == 0
    assert result["compression_ratio"] == 0.0
    assert result["op_counts"] == {"ADD": 0, "UPDATE": 0, "DELETE": 0, "NOOP": 0}
