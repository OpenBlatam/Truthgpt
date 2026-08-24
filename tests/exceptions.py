"""
TruthGPT Optimization Core - Typed Exception Hierarchy
======================================================
Granular, structured domain exceptions for the test subsystem.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict, Optional


class TestFrameworkError(Exception):
    """Base exception for all test framework related errors."""
    __test__ = False

    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_FRAMEWORK",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        self.suggested_action = suggested_action or ""
        self.timestamp = time.time()

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.suggested_action:
            parts.append(f"Action: {self.suggested_action}")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to structured dictionary."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize exception to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class TestDiscoveryError(TestFrameworkError):
    """Raised when test discovery fails or locates an invalid test module."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_DISCOVERY",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class TestExecutionError(TestFrameworkError):
    """Raised when an unhandled exception or crash occurs during test execution."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_EXECUTION",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class TestAssertionError(TestFrameworkError, AssertionError):
    """Raised when an advanced assertion or validation fails with rich diagnostic context."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_ASSERTION",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


AssertionErrorWrapper = TestAssertionError


class TestFixtureError(TestFrameworkError):
    """Raised when fixture creation, mock component setup, or teardown fails."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_FIXTURE",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


FixtureError = TestFixtureError


class MockComponentError(TestFrameworkError):
    """Raised when mock component initialization or simulation fails."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_MOCK_COMPONENT",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class FlakyTestError(TestFrameworkError):
    """Raised when a flaky test exceeds configured retry attempts."""
    def __init__(
        self,
        test_name_or_message: str = "",
        attempts: int = 1,
        last_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_FLAKY_TEST",
        suggested_action: Optional[str] = None,
    ) -> None:
        dt = dict(details or {})
        dt["attempts"] = attempts
        if last_error:
            dt["last_error"] = str(last_error)
        msg = f"Flaky test '{test_name_or_message}' failed after {attempts} attempts."
        if last_error:
            msg += f" Last error: {last_error}"
        super().__init__(msg, dt, error_code, suggested_action)
        self.attempts = attempts
        self.last_error = last_error


class TestTimeoutError(TestFrameworkError):
    """Raised when a test case exceeds its allocated execution timeout limit."""
    def __init__(
        self,
        test_name_or_message: str = "",
        timeout_seconds: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_TIMEOUT",
        suggested_action: Optional[str] = None,
    ) -> None:
        dt = dict(details or {})
        if timeout_seconds is not None:
            msg = f"Test '{test_name_or_message}' timed out after exceeding {timeout_seconds:.1f}s limit."
            dt["test_name"] = test_name_or_message
            dt["timeout_seconds"] = timeout_seconds
        else:
            msg = test_name_or_message
        super().__init__(msg, dt, error_code, suggested_action)
        self.test_name = test_name_or_message
        self.timeout_seconds = timeout_seconds


class TestConfigurationError(TestFrameworkError):
    """Raised when test runner, pipeline, or suite configuration is invalid."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_CONFIG",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class TestReportError(TestFrameworkError):
    """Raised when report generation or export fails."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_TEST_REPORT",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class BackendUnavailableError(TestFrameworkError):
    """Raised when an operation requires a native backend that is not available."""
    def __init__(
        self,
        backend_name_or_message: str = "",
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_BACKEND_UNAVAILABLE",
        suggested_action: Optional[str] = None,
    ) -> None:
        dt = dict(details or {})
        if reason:
            msg = f"Native backend '{backend_name_or_message}' is not available. Reason: {reason}"
            dt["backend"] = backend_name_or_message
            dt["reason"] = reason
        elif "available" in backend_name_or_message or "backend" in backend_name_or_message:
            msg = backend_name_or_message
            dt["backend"] = backend_name_or_message
        else:
            msg = f"Native backend '{backend_name_or_message}' is not available."
            dt["backend"] = backend_name_or_message

        super().__init__(msg, dt, error_code, suggested_action)
        self.backend_name = backend_name_or_message
        self.reason = reason


class EnvironmentSetupError(TestFrameworkError):
    """Raised when test environment initialization or dependency verification fails."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_ENV_SETUP",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class RegistryError(TestFrameworkError):
    """Raised when registration or retrieval within the test registry fails."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_REGISTRY",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class BenchmarkFailureError(TestFrameworkError):
    """Raised when a benchmark routine fails to converge, produces invalid measurements, or fails regressions."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_BENCHMARK_FAILURE",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class ProfilerError(TestFrameworkError):
    """Raised when the performance profiler encounters an error."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_PROFILER",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


class MemoryTrackingError(TestFrameworkError):
    """Raised when memory tracker fails to sample memory or detects an unacceptable memory leak."""
    def __init__(
        self,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "ERR_MEMORY_TRACKING",
        suggested_action: Optional[str] = None,
    ) -> None:
        super().__init__(message, details, error_code, suggested_action)


# Dual namespace aliasing for submodule
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.exceptions":
        sys.modules["tests.exceptions"] = _mod
    elif __name__ == "tests.exceptions":
        sys.modules["optimization_core.tests.exceptions"] = _mod


__all__ = [
    "TestFrameworkError",
    "TestDiscoveryError",
    "TestExecutionError",
    "TestAssertionError",
    "AssertionErrorWrapper",
    "TestFixtureError",
    "FixtureError",
    "MockComponentError",
    "FlakyTestError",
    "TestTimeoutError",
    "TestConfigurationError",
    "TestReportError",
    "BackendUnavailableError",
    "EnvironmentSetupError",
    "RegistryError",
    "BenchmarkFailureError",
    "ProfilerError",
    "MemoryTrackingError",
]
