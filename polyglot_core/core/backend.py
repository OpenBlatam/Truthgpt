"""
Backend Detection, Selection, and Negotiation Sub-System
=========================================================

This module provides the authoritative runtime backend registry for the TruthGPT
polyglot_core engine.  It is responsible for:

  1. **Auto-detection** – Probing available native extensions (Rust/PyO3,
     C++/PyBind11) and remote services (Go gRPC / HTTP) at startup.
  2. **Capability negotiation** – Each backend advertises a fine-grained set of
     capability flags (``kv_cache``, ``flash_attention``, ``cuda``, …).  The
     selection algorithm ranks candidates by capability coverage and performance
     multiplier rather than by coarse backend type.
  3. **Health-aware selection** – Failed or slow backends are demoted in the
     preference order at runtime without requiring a process restart.
  4. **Observability** – Every detection probe result and selection decision is
     emitted to the structured-logging subsystem and can optionally be exported
     to OpenTelemetry via a pluggable telemetry sink.
  5. **Thread-safety** – The entire registry is protected by a ``RLock`` so that
     concurrent ``get_best_backend`` calls from multiple inference threads never
     race.

Architecture
------------
::

    ┌──────────────────────────────────────┐
    │           BackendRegistry            │  thread-safe singleton
    │  ┌─────────────────────────────────┐ │
    │  │       detection layer           │ │  probes: Rust / C++ / Go / Python
    │  └────────────────┬────────────────┘ │
    │                   │                  │
    │  ┌────────────────▼────────────────┐ │
    │  │        BackendInfo cache        │ │  version, features, perf_multiplier
    │  └────────────────┬────────────────┘ │
    │                   │                  │
    │  ┌────────────────▼────────────────┐ │
    │  │  capability-based selector      │ │  get_best_backend(feature)
    │  └─────────────────────────────────┘ │
    └──────────────────────────────────────┘

Usage
-----
::

    from polyglot_core.core.backend import Backend, get_best_backend, is_backend_available

    backend = get_best_backend("kv_cache")
    print(backend)                    # Backend.RUST  (if available)

    if is_backend_available(Backend.CPP):
        print("CUDA acceleration ready")

    from polyglot_core.core.backend import print_backend_status
    print_backend_status()            # rich ASCII table to stdout
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto, unique
from typing import (
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    runtime_checkable,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CAPABILITY CONSTANTS
# These strings are the single source of truth for capability names across
# the entire polyglot_core package.
# ─────────────────────────────────────────────────────────────────────────────

CAP_KV_CACHE: str = "kv_cache"
CAP_COMPRESSION: str = "compression"
CAP_TOKENIZATION: str = "tokenization"
CAP_DATA_LOADING: str = "data_loading"
CAP_ATTENTION: str = "attention"
CAP_FLASH_ATTENTION: str = "flash_attention"
CAP_SPARSE_ATTENTION: str = "sparse_attention"
CAP_CUDA: str = "cuda"
CAP_CUTLASS: str = "cutlass"
CAP_EIGEN: str = "eigen"
CAP_TBB: str = "tbb"
CAP_INFERENCE: str = "inference"
CAP_DISTRIBUTED: str = "distributed"
CAP_HTTP: str = "http"
CAP_GRPC: str = "grpc"
CAP_QUANTIZATION: str = "quantization"
CAP_FALLBACK: str = "fallback"

#: All known capability strings (used for validation)
ALL_KNOWN_CAPABILITIES: FrozenSet[str] = frozenset({
    CAP_KV_CACHE,
    CAP_COMPRESSION,
    CAP_TOKENIZATION,
    CAP_DATA_LOADING,
    CAP_ATTENTION,
    CAP_FLASH_ATTENTION,
    CAP_SPARSE_ATTENTION,
    CAP_CUDA,
    CAP_CUTLASS,
    CAP_EIGEN,
    CAP_TBB,
    CAP_INFERENCE,
    CAP_DISTRIBUTED,
    CAP_HTTP,
    CAP_GRPC,
    CAP_QUANTIZATION,
    CAP_FALLBACK,
})


# ─────────────────────────────────────────────────────────────────────────────
# BACKEND ENUM
# ─────────────────────────────────────────────────────────────────────────────

@unique
class Backend(Enum):
    """
    Enumeration of all supported backend implementations.

    Ordering reflects the *general* preference when multiple backends share
    the same feature set.  Specialised per-feature overrides are defined in
    :data:`FEATURE_PREFERENCE_MAP`.
    """

    PYTHON = auto()  # Pure Python – always available, zero-dependency fallback
    RUST = auto()    # Rust via PyO3 – 20-50× faster than Python for CPU ops
    CPP = auto()     # C++ via PyBind11 – CUDA/Eigen, 10-100× with GPU
    GO = auto()      # Go services via gRPC / HTTP – horizontal scalability


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BackendHealth:
    """
    Runtime health snapshot for a backend.

    Updated by :class:`BackendRegistry` as operations succeed or fail.
    Used to demote unreliable backends in the preference ordering.
    """

    error_count: int = 0
    """Number of consecutive errors since last successful call."""

    last_error_ts: float = 0.0
    """UNIX timestamp of the most recent error (0 = no error)."""

    last_success_ts: float = 0.0
    """UNIX timestamp of the most recent successful call (0 = never used)."""

    total_calls: int = 0
    """Cumulative calls routed to this backend in the current process."""

    total_errors: int = 0
    """Cumulative error count in the current process."""

    @property
    def is_healthy(self) -> bool:
        """True when fewer than 5 consecutive errors have occurred."""
        return self.error_count < 5

    @property
    def error_rate(self) -> float:
        """Fraction of calls that resulted in an error; 0.0 if never called."""
        if self.total_calls == 0:
            return 0.0
        return self.total_errors / self.total_calls

    def record_success(self) -> None:
        """Reset error streak and update last-success timestamp."""
        self.error_count = 0
        self.last_success_ts = time.monotonic()
        self.total_calls += 1

    def record_error(self) -> None:
        """Increment error counters and update last-error timestamp."""
        self.error_count += 1
        self.last_error_ts = time.monotonic()
        self.total_calls += 1
        self.total_errors += 1


@dataclass
class BackendInfo:
    """
    Comprehensive descriptor for a single backend implementation.

    Attributes
    ----------
    name:
        Human-readable backend identifier (e.g. ``"rust_core"``).
    backend:
        The :class:`Backend` enum member this descriptor belongs to.
    available:
        ``True`` when the backend was successfully probed at startup.
    version:
        Version string reported by the native extension (empty if not
        available).
    features:
        Sorted list of capability strings provided by this backend.
    performance_multiplier:
        Estimated throughput advantage relative to the Python fallback
        (which has multiplier 1.0).  Used as a tie-breaker when multiple
        backends share a required capability.
    error:
        Error message from the detection probe (``None`` when available).
    health:
        Runtime health counters updated throughout the process lifetime.
    probe_duration_ms:
        Wall-clock time (ms) taken by the detection probe.
    """

    name: str
    backend: Backend
    available: bool
    version: str = ""
    features: List[str] = field(default_factory=list)
    performance_multiplier: float = 1.0
    error: Optional[str] = None
    health: BackendHealth = field(default_factory=BackendHealth)
    probe_duration_ms: float = 0.0

    def has_capability(self, capability: str) -> bool:
        """Return ``True`` if *capability* is in this backend's feature set."""
        return capability in self.features

    def has_all_capabilities(self, capabilities: Set[str]) -> bool:
        """Return ``True`` if *all* of *capabilities* are supported."""
        feature_set = set(self.features)
        return capabilities.issubset(feature_set)

    def effective_performance(self) -> float:
        """
        Adjust the performance multiplier downward when the backend is
        experiencing errors, so that a degraded backend is naturally
        deprioritised in the selection algorithm.
        """
        if not self.health.is_healthy:
            penalty = min(self.health.error_count * 0.2, 0.9)
            return self.performance_multiplier * (1.0 - penalty)
        return self.performance_multiplier

    def __str__(self) -> str:
        status = "✓" if self.available else "✗"
        perf = f"{self.performance_multiplier:.0f}×"
        return f"{status} {self.name} v{self.version or '?'} ({perf})"

    def __repr__(self) -> str:
        return (
            f"BackendInfo(name={self.name!r}, backend={self.backend.name}, "
            f"available={self.available}, version={self.version!r}, "
            f"features={self.features!r}, "
            f"perf_multiplier={self.performance_multiplier})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE → PREFERENCE MAP
# ─────────────────────────────────────────────────────────────────────────────

#: Maps a capability string to the ordered list of backends that best support
#: it.  The first available backend wins.
FEATURE_PREFERENCE_MAP: Dict[str, List[Backend]] = {
    CAP_ATTENTION:       [Backend.CPP, Backend.RUST, Backend.PYTHON],
    CAP_FLASH_ATTENTION: [Backend.CPP, Backend.RUST, Backend.PYTHON],
    CAP_SPARSE_ATTENTION:[Backend.CPP, Backend.PYTHON],
    CAP_CUDA:            [Backend.CPP],
    CAP_KV_CACHE:        [Backend.RUST, Backend.CPP, Backend.GO, Backend.PYTHON],
    CAP_COMPRESSION:     [Backend.RUST, Backend.CPP, Backend.PYTHON],
    CAP_TOKENIZATION:    [Backend.RUST, Backend.PYTHON],
    CAP_DATA_LOADING:    [Backend.RUST, Backend.PYTHON],
    CAP_INFERENCE:       [Backend.CPP, Backend.RUST, Backend.GO, Backend.PYTHON],
    CAP_QUANTIZATION:    [Backend.CPP, Backend.RUST, Backend.PYTHON],
    CAP_DISTRIBUTED:     [Backend.GO, Backend.PYTHON],
    CAP_HTTP:            [Backend.GO, Backend.PYTHON],
    CAP_GRPC:            [Backend.GO, Backend.CPP],
}


# ─────────────────────────────────────────────────────────────────────────────
# PROTOCOLS
# ─────────────────────────────────────────────────────────────────────────────

@runtime_checkable
class TelemetrySink(Protocol):
    """
    Optional telemetry sink injected into :class:`BackendRegistry`.

    Implement this protocol to forward backend events to OpenTelemetry,
    Prometheus, DataDog, or any custom monitoring system.
    """

    def emit_backend_selected(
        self,
        feature: str,
        backend: Backend,
        alternatives: List[Backend],
    ) -> None:
        """Called whenever a backend is selected for a feature."""
        ...

    def emit_probe_result(
        self,
        backend: Backend,
        available: bool,
        duration_ms: float,
    ) -> None:
        """Called after each detection probe completes."""
        ...

    def emit_health_update(
        self,
        backend: Backend,
        health: BackendHealth,
    ) -> None:
        """Called whenever a backend's health counters change."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# DETECTION PROBES
# ─────────────────────────────────────────────────────────────────────────────

def _probe_rust_backend() -> BackendInfo:
    """
    Probe the Rust backend (``optimization_core.rust_core.truthgpt_rust``).

    Detection strategy:
      1. Import ``optimization_core.rust_core``.
      2. Traverse the ``truthgpt_rust`` sub-module to discover advertised
         capabilities via ``hasattr`` checks.
      3. Record the ``__version__`` attribute when present.

    Returns
    -------
    BackendInfo
        Populated descriptor; ``available=False`` on any :class:`ImportError`.
    """
    t0 = time.perf_counter()
    try:
        from optimization_core import rust_core  # type: ignore[import]
        tr = rust_core.truthgpt_rust

        features: List[str] = []
        capability_map: Dict[str, str] = {
            "PyKVCache":         CAP_KV_CACHE,
            "PyCompressor":      CAP_COMPRESSION,
            "PyTokenizer":       CAP_TOKENIZATION,
            "PyBatchDataLoader": CAP_DATA_LOADING,
            "PyAttention":       CAP_ATTENTION,
            "PyQuantizer":       CAP_QUANTIZATION,
        }
        for attr, cap in capability_map.items():
            if hasattr(tr, attr):
                features.append(cap)

        version: str = getattr(tr, "__version__", "1.0.0")
        duration_ms = (time.perf_counter() - t0) * 1_000.0

        logger.debug(
            "[backend] Rust probe SUCCESS version=%s features=%s (%.1f ms)",
            version,
            features,
            duration_ms,
        )
        return BackendInfo(
            name="rust_core",
            backend=Backend.RUST,
            available=True,
            version=version,
            features=features,
            performance_multiplier=50.0,
            probe_duration_ms=duration_ms,
        )

    except ImportError as exc:
        duration_ms = (time.perf_counter() - t0) * 1_000.0
        logger.debug("[backend] Rust probe FAILED: %s (%.1f ms)", exc, duration_ms)
        return BackendInfo(
            name="rust_core",
            backend=Backend.RUST,
            available=False,
            error=str(exc),
            probe_duration_ms=duration_ms,
        )


def _probe_cpp_backend() -> BackendInfo:
    """
    Probe the C++ backend (``optimization_core._cpp_core``).

    Capability discovery works by interrogating the module's sub-namespaces:
    ``attention``, ``memory``, and a ``get_system_info()`` call to detect
    hardware-level features (CUDA, cuTLASS, Eigen, TBB, LZ4).

    Performance multiplier is set to 100× when CUDA is present, 10× otherwise.

    Returns
    -------
    BackendInfo
        Populated descriptor; ``available=False`` on any :class:`ImportError`.
    """
    t0 = time.perf_counter()
    try:
        from optimization_core import _cpp_core  # type: ignore[import]

        features: List[str] = []

        # Namespace-level capability detection
        if hasattr(_cpp_core, "attention"):
            features += [CAP_ATTENTION, CAP_FLASH_ATTENTION]
        if hasattr(_cpp_core, "memory"):
            features.append(CAP_KV_CACHE)

        # Hardware / library detection via system info
        sys_info: Dict = {}
        if hasattr(_cpp_core, "get_system_info"):
            try:
                sys_info = _cpp_core.get_system_info()
            except Exception:
                pass

        hw_flag_map: Dict[str, str] = {
            "cuda":    CAP_CUDA,
            "cutlass": CAP_CUTLASS,
            "eigen":   CAP_EIGEN,
            "tbb":     CAP_TBB,
            "lz4":     CAP_COMPRESSION,
        }
        for hw_flag, capability in hw_flag_map.items():
            if hw_flag in sys_info.get("backends", []):
                features.append(capability)

        # Add quantization if CUDA or eigen is available
        if CAP_CUDA in features or CAP_EIGEN in features:
            features.append(CAP_QUANTIZATION)

        version: str = getattr(_cpp_core, "__version__", "1.1.0")
        perf = 100.0 if CAP_CUDA in features else 10.0
        duration_ms = (time.perf_counter() - t0) * 1_000.0

        logger.debug(
            "[backend] C++ probe SUCCESS version=%s features=%s perf=%.0f× (%.1f ms)",
            version,
            features,
            perf,
            duration_ms,
        )
        return BackendInfo(
            name="cpp_core",
            backend=Backend.CPP,
            available=True,
            version=version,
            features=features,
            performance_multiplier=perf,
            probe_duration_ms=duration_ms,
        )

    except ImportError as exc:
        duration_ms = (time.perf_counter() - t0) * 1_000.0
        logger.debug("[backend] C++ probe FAILED: %s (%.1f ms)", exc, duration_ms)
        return BackendInfo(
            name="cpp_core",
            backend=Backend.CPP,
            available=False,
            error=str(exc),
            probe_duration_ms=duration_ms,
        )


def _probe_go_backend() -> BackendInfo:
    """
    Probe Go service backends reachable via HTTP health endpoints.

    The probe verifies that both ``grpc`` and ``requests`` are importable and
    then performs lightweight HTTP GET requests against the inference and cache
    service health endpoints.  The ``POLYGLOT_INFERENCE_URL`` and
    ``POLYGLOT_CACHE_URL`` environment variables customise endpoint discovery.

    The backend is considered **available** when at least one Go service
    responds with HTTP 200 within a 1-second timeout.

    Returns
    -------
    BackendInfo
        Populated descriptor; ``available=False`` when no service is reachable.
    """
    t0 = time.perf_counter()
    try:
        import grpc          # type: ignore[import]
        import requests      # type: ignore[import]

        features: List[str] = [CAP_GRPC, CAP_HTTP, CAP_DISTRIBUTED]
        active_services: List[str] = []

        # Probe inference service
        inference_url = os.environ.get("POLYGLOT_INFERENCE_URL", "http://localhost:8080")
        try:
            resp = requests.get(f"{inference_url}/health", timeout=1.0)
            if resp.status_code == 200:
                features.append(CAP_INFERENCE)
                active_services.append("inference")
        except Exception:
            pass

        # Probe cache service
        cache_url = os.environ.get("POLYGLOT_CACHE_URL", "http://localhost:8081")
        try:
            resp = requests.get(f"{cache_url}/health", timeout=1.0)
            if resp.status_code == 200:
                features.append(CAP_KV_CACHE)
                active_services.append("cache")
        except Exception:
            pass

        # The Go backend is only useful when at least one service is reachable
        is_available = len(active_services) > 0
        duration_ms = (time.perf_counter() - t0) * 1_000.0

        logger.debug(
            "[backend] Go probe %s services=%s (%.1f ms)",
            "SUCCESS" if is_available else "NO_SERVICES",
            active_services,
            duration_ms,
        )
        return BackendInfo(
            name="go_core",
            backend=Backend.GO,
            available=is_available,
            version="1.0.0",
            features=features if is_available else [],
            performance_multiplier=20.0,
            error=None if is_available else "No Go services reachable",
            probe_duration_ms=duration_ms,
        )

    except ImportError as exc:
        duration_ms = (time.perf_counter() - t0) * 1_000.0
        logger.debug("[backend] Go probe FAILED: %s (%.1f ms)", exc, duration_ms)
        return BackendInfo(
            name="go_core",
            backend=Backend.GO,
            available=False,
            error=str(exc),
            probe_duration_ms=duration_ms,
        )


def _build_python_backend_info() -> BackendInfo:
    """
    Build the always-available Python fallback :class:`BackendInfo`.

    The Python backend supports every capability (including ``fallback``),
    but with a performance multiplier of exactly 1.0.
    """
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return BackendInfo(
        name="python",
        backend=Backend.PYTHON,
        available=True,
        version=version,
        features=sorted(ALL_KNOWN_CAPABILITIES),
        performance_multiplier=1.0,
        probe_duration_ms=0.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# BACKEND REGISTRY – thread-safe singleton
# ─────────────────────────────────────────────────────────────────────────────

class BackendRegistry:
    """
    Thread-safe singleton that owns the backend detection cache and the
    capability-based backend selection algorithm.

    The registry lazily initialises on first access.  All public methods
    acquire ``_lock`` (an :class:`threading.RLock`) so they are safe to call
    from multiple inference threads simultaneously.

    Lifecycle
    ---------
    1. :meth:`probe_all` is called (automatically on first access or
       explicitly via :meth:`refresh`) to run all detection probes.
    2. Results are stored in ``_infos`` keyed by :class:`Backend`.
    3. :meth:`get_best_backend` uses :data:`FEATURE_PREFERENCE_MAP` to rank
       candidates and returns the highest-ranked available backend.
    4. Callers can report success/failure via :meth:`record_success` /
       :meth:`record_error` which update :class:`BackendHealth` and influence
       future rankings.

    Attributes
    ----------
    _instance : ClassVar[Optional[BackendRegistry]]
        Singleton instance (``None`` before first call to :meth:`instance`).
    _lock : ClassVar[threading.RLock]
        Class-level re-entrant lock guarding instance creation.
    """

    _instance: ClassVar[Optional["BackendRegistry"]] = None
    _class_lock: ClassVar[threading.RLock] = threading.RLock()

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._infos: Dict[Backend, BackendInfo] = {}
        self._probed: bool = False
        self._telemetry: Optional[TelemetrySink] = None
        self._selection_log: List[Tuple[str, Backend, float]] = []
        # Maximum selection-log entries kept in memory
        self._max_selection_log: int = 1_000

    # ── Singleton access ──────────────────────────────────────────────────────

    @classmethod
    def instance(cls) -> "BackendRegistry":
        """Return the process-global :class:`BackendRegistry` singleton."""
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    # ── Telemetry ─────────────────────────────────────────────────────────────

    def set_telemetry_sink(self, sink: Optional[TelemetrySink]) -> None:
        """
        Attach (or detach when *sink* is ``None``) an optional
        :class:`TelemetrySink` that receives backend lifecycle events.
        """
        with self._lock:
            self._telemetry = sink

    # ── Detection / refresh ──────────────────────────────────────────────────

    def probe_all(self, *, force: bool = False) -> None:
        """
        Run all backend detection probes and populate the internal cache.

        Parameters
        ----------
        force:
            When ``True``, re-run every probe even when results are already
            cached.  Useful after a native library is installed at runtime.

        Notes
        -----
        Probes are executed **synchronously** in order:
        Python → Rust → C++ → Go.  The Python backend never fails.
        """
        with self._lock:
            if self._probed and not force:
                return

            logger.info("[backend] Running backend detection probes …")
            t_start = time.perf_counter()

            probes: List[Callable[[], BackendInfo]] = [
                _build_python_backend_info,
                _probe_rust_backend,
                _probe_cpp_backend,
                _probe_go_backend,
            ]

            new_infos: Dict[Backend, BackendInfo] = {}
            for probe_fn in probes:
                info = probe_fn()
                new_infos[info.backend] = info

                if self._telemetry:
                    try:
                        self._telemetry.emit_probe_result(
                            backend=info.backend,
                            available=info.available,
                            duration_ms=info.probe_duration_ms,
                        )
                    except Exception:
                        pass

            # Preserve health history when refreshing
            for backend, old_info in self._infos.items():
                if backend in new_infos:
                    new_infos[backend].health = old_info.health

            self._infos = new_infos
            self._probed = True

            elapsed_ms = (time.perf_counter() - t_start) * 1_000.0
            available_names = [
                info.name for info in self._infos.values() if info.available
            ]
            logger.info(
                "[backend] Probe complete in %.1f ms – available: %s",
                elapsed_ms,
                available_names,
            )

    def refresh(self) -> None:
        """Force a fresh detection run, re-probing all backends."""
        self.probe_all(force=True)

    # ── Query API ────────────────────────────────────────────────────────────

    def get_all(self, *, force_refresh: bool = False) -> List[BackendInfo]:
        """
        Return a snapshot list of all :class:`BackendInfo` objects.

        Parameters
        ----------
        force_refresh:
            When ``True`` (alias for :meth:`refresh`) re-probe before
            returning.
        """
        if force_refresh:
            self.refresh()
        else:
            self.probe_all()

        with self._lock:
            return list(self._infos.values())

    def get_info(self, backend: Backend) -> Optional[BackendInfo]:
        """Return the :class:`BackendInfo` for *backend*, or ``None``."""
        self.probe_all()
        with self._lock:
            return self._infos.get(backend)

    def is_available(self, backend: Backend) -> bool:
        """Return ``True`` when *backend* was successfully detected."""
        info = self.get_info(backend)
        return info is not None and info.available

    def get_best_backend(self, feature: str) -> Backend:
        """
        Select the best available backend for *feature*.

        The algorithm proceeds as follows:

        1. Look up the preference order from :data:`FEATURE_PREFERENCE_MAP`.
        2. For each candidate in preference order: skip unavailable backends
           and backends that do not declare the required capability.
        3. Among the remaining candidates, pick the one with the highest
           :meth:`BackendInfo.effective_performance` score (accounts for
           health degradation).
        4. If no suitable candidate is found, fall back to
           :attr:`Backend.PYTHON`.

        Parameters
        ----------
        feature:
            A capability string (see ``CAP_*`` module-level constants).

        Returns
        -------
        Backend
            The selected backend enum member.
        """
        self.probe_all()

        with self._lock:
            preferences = FEATURE_PREFERENCE_MAP.get(feature, [Backend.PYTHON])

            candidates: List[Tuple[float, Backend]] = []
            for backend in preferences:
                info = self._infos.get(backend)
                if info is None or not info.available:
                    continue
                if not info.has_capability(feature):
                    continue
                candidates.append((info.effective_performance(), backend))

            if candidates:
                # Sort descending by effective performance; stable sort
                # preserves the original preference order for equal scores.
                candidates.sort(key=lambda t: -t[0])
                selected = candidates[0][1]
            else:
                selected = Backend.PYTHON

            # Record in selection log
            self._selection_log.append((feature, selected, time.monotonic()))
            if len(self._selection_log) > self._max_selection_log:
                self._selection_log.pop(0)

            if self._telemetry:
                try:
                    self._telemetry.emit_backend_selected(
                        feature=feature,
                        backend=selected,
                        alternatives=[b for _, b in candidates[1:]],
                    )
                except Exception:
                    pass

            logger.debug("[backend] %s → %s", feature, selected.name)
            return selected

    def get_best_backend_for_capabilities(
        self, capabilities: Set[str]
    ) -> Backend:
        """
        Select the best backend that supports **all** of *capabilities*.

        Useful when a component requires multiple features simultaneously
        (e.g. ``{kv_cache, compression}``).

        Parameters
        ----------
        capabilities:
            Set of capability strings that must all be present.

        Returns
        -------
        Backend
            The selected backend; :attr:`Backend.PYTHON` as fallback.
        """
        self.probe_all()

        with self._lock:
            # Build the union of preference lists
            all_backends: List[Backend] = [
                Backend.CPP,
                Backend.RUST,
                Backend.GO,
                Backend.PYTHON,
            ]

            scored: List[Tuple[float, Backend]] = []
            for backend in all_backends:
                info = self._infos.get(backend)
                if info is None or not info.available:
                    continue
                if not info.has_all_capabilities(capabilities):
                    continue
                scored.append((info.effective_performance(), backend))

            if scored:
                scored.sort(key=lambda t: -t[0])
                return scored[0][1]
            return Backend.PYTHON

    # ── Health feedback ──────────────────────────────────────────────────────

    def record_success(self, backend: Backend) -> None:
        """
        Notify the registry that a call to *backend* succeeded.

        Updates the backend's :class:`BackendHealth` and optionally notifies
        the telemetry sink.
        """
        with self._lock:
            info = self._infos.get(backend)
            if info is None:
                return
            info.health.record_success()
            if self._telemetry:
                try:
                    self._telemetry.emit_health_update(backend, info.health)
                except Exception:
                    pass

    def record_error(self, backend: Backend) -> None:
        """
        Notify the registry that a call to *backend* failed.

        Updates the backend's :class:`BackendHealth`.  After 5 consecutive
        errors the backend is considered *degraded* and will be deprioritised
        by :meth:`get_best_backend`.
        """
        with self._lock:
            info = self._infos.get(backend)
            if info is None:
                return
            info.health.record_error()
            if not info.health.is_healthy:
                logger.warning(
                    "[backend] %s is DEGRADED (consecutive_errors=%d)",
                    info.name,
                    info.health.error_count,
                )
            if self._telemetry:
                try:
                    self._telemetry.emit_health_update(backend, info.health)
                except Exception:
                    pass

    # ── Diagnostics ──────────────────────────────────────────────────────────

    def print_status(self) -> None:
        """
        Print a rich ASCII table of all backend statuses to :data:`sys.stdout`.
        """
        infos = self.get_all()
        width = 66

        print(f"\n╔{'═' * width}╗")
        print(f"║{'  TruthGPT / PolyglotCore — Backend Status':^{width}}║")
        print(f"╠{'═' * width}╣")

        for info in infos:
            status_icon = "✓" if info.available else "✗"
            perf = f"{info.performance_multiplier:.0f}×" if info.available else "N/A"
            health_icon = "🟢" if info.health.is_healthy else "🔴"
            line = (
                f"  {health_icon} {status_icon} {info.name:<12} "
                f"v{(info.version or '?'):<8}  Perf: {perf:<6}"
            )
            print(f"║{line:<{width}}║")

            if info.features:
                feature_str = ", ".join(sorted(info.features)[:5])
                if len(info.features) > 5:
                    feature_str += f" +{len(info.features) - 5}"
                print(f"║{'     Features: ' + feature_str:<{width}}║")

            if info.error:
                truncated = info.error[:width - 12]
                print(f"║{'     Error: ' + truncated:<{width}}║")

            print(f"║{'     Health: calls=' + str(info.health.total_calls) + ' errors=' + str(info.health.total_errors):<{width}}║")

        print(f"╚{'═' * width}╝\n")

    def get_selection_history(self) -> List[Tuple[str, Backend, float]]:
        """
        Return the in-memory selection log as a list of
        ``(feature, backend, monotonic_timestamp)`` tuples.
        """
        with self._lock:
            return list(self._selection_log)

    def get_capability_matrix(self) -> Dict[str, Dict[Backend, bool]]:
        """
        Return a capability × backend availability matrix.

        Returns
        -------
        Dict[str, Dict[Backend, bool]]
            Outer key: capability string.  Inner key: :class:`Backend`.
            Value: ``True`` when that backend supports that capability.
        """
        self.probe_all()
        matrix: Dict[str, Dict[Backend, bool]] = {}
        with self._lock:
            for cap in sorted(ALL_KNOWN_CAPABILITIES):
                matrix[cap] = {
                    backend: info.available and cap in info.features
                    for backend, info in self._infos.items()
                }
        return matrix


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _registry() -> BackendRegistry:
    """Return the process-global :class:`BackendRegistry` singleton."""
    return BackendRegistry.instance()


def get_available_backends(force_refresh: bool = False) -> List[BackendInfo]:
    """
    Return a list of all :class:`BackendInfo` objects.

    Parameters
    ----------
    force_refresh:
        When ``True``, re-run the detection probes before returning.
    """
    return _registry().get_all(force_refresh=force_refresh)


def is_backend_available(backend: Backend) -> bool:
    """Return ``True`` when *backend* was successfully detected."""
    return _registry().is_available(backend)


def get_best_backend(feature: str) -> Backend:
    """
    Select the best available backend for a given *feature*.

    See :meth:`BackendRegistry.get_best_backend` for the full selection
    algorithm description.

    Parameters
    ----------
    feature:
        A capability string.  See the ``CAP_*`` constants in this module.

    Returns
    -------
    Backend
        The selected :class:`Backend` enum member.
    """
    return _registry().get_best_backend(feature)


def get_best_backend_for_capabilities(capabilities: Set[str]) -> Backend:
    """
    Select the best backend that supports **all** of the given *capabilities*.

    Parameters
    ----------
    capabilities:
        Set of capability strings.

    Returns
    -------
    Backend
    """
    return _registry().get_best_backend_for_capabilities(capabilities)


def get_backend_info(backend: Backend) -> Optional[BackendInfo]:
    """Return the :class:`BackendInfo` for *backend*, or ``None``."""
    return _registry().get_info(backend)


def record_backend_success(backend: Backend) -> None:
    """
    Notify the global registry that a call to *backend* succeeded.

    Should be called by component engines after a successful native operation
    so that the health-aware selection algorithm can reward reliable backends.
    """
    _registry().record_success(backend)


def record_backend_error(backend: Backend) -> None:
    """
    Notify the global registry that a call to *backend* failed.

    Should be called by component engines in their ``except`` blocks so that
    the health-aware selection algorithm can demote unreliable backends.
    """
    _registry().record_error(backend)


def refresh_backends() -> None:
    """Force a fresh detection run, re-probing all backends."""
    _registry().refresh()


def print_backend_status() -> None:
    """Print a rich ASCII status table for all detected backends."""
    _registry().print_status()


def set_telemetry_sink(sink: Optional[TelemetrySink]) -> None:
    """
    Attach an optional :class:`TelemetrySink` to the global registry.

    Pass ``None`` to detach.
    """
    _registry().set_telemetry_sink(sink)
