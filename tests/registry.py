"""
TruthGPT Optimization Core - Thread-Safe Test Registry
======================================================
Centralized dynamic registration and factory engine for test suites, benchmarks,
synthetic fixtures, mock components, custom assertions, and multi-format reporters.
"""

from __future__ import annotations

import sys
import threading
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .types import BackendType, TestCategory
from .exceptions import RegistryError, TestFrameworkError


# ---------------------------------------------------------------------------
# Module Aliasing across namespaces
# ---------------------------------------------------------------------------
_mod = sys.modules.get(__name__)
if _mod is not None:
    if __name__ == "optimization_core.tests.registry":
        sys.modules["tests.registry"] = _mod
    elif __name__ == "tests.registry":
        sys.modules["optimization_core.tests.registry"] = _mod


class TestRegistry:
    """
    Thread-safe registry for test suites, fixtures, mocks, assertions, and reporters.
    Enforces concurrency isolation using recursive re-entrant locks.
    """
    __test__ = False

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._components: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def register(
        self,
        category: str,
        name: str,
        component: Any,
        metadata: Optional[Dict[str, Any]] = None,
        override: bool = True,
    ) -> None:
        """Register a component under a specified category."""
        with self._lock:
            if category not in self._components:
                self._components[category] = {}

            if name in self._components[category] and not override:
                raise RegistryError(
                    f"Component '{name}' already registered in category '{category}'.",
                    details={"category": category, "name": name},
                )

            self._components[category][name] = {
                "component": component,
                "metadata": metadata or {},
            }

    def get(self, category: str, name: str) -> Any:
        """Retrieve a registered component."""
        with self._lock:
            if category not in self._components or name not in self._components[category]:
                if category == "reporters":
                    from .reporters import create_reporter as rep_factory
                    return lambda *args, **kwargs: rep_factory(name, *args, **kwargs)
                raise RegistryError(
                    f"Component '{name}' not found in category '{category}'.",
                    details={"category": category, "name": name},
                )
            return self._components[category][name]["component"]

    def get_metadata(self, category: str, name: str) -> Dict[str, Any]:
        """Retrieve metadata for a registered component."""
        with self._lock:
            if category not in self._components or name not in self._components[category]:
                raise RegistryError(
                    f"Component '{name}' not found in category '{category}'.",
                    details={"category": category, "name": name},
                )
            return dict(self._components[category][name]["metadata"])

    def create(self, category: str, name: str, *args: Any, **kwargs: Any) -> Any:
        """Instantiate or call a registered component factory."""
        if category == "reporters" and not self.is_registered("reporters", name):
            from .reporters import create_reporter as rep_factory
            return rep_factory(name, *args, **kwargs)
        comp = self.get(category, name)
        if callable(comp):
            return comp(*args, **kwargs)
        return comp

    def get_assertion(self, name: str) -> Callable[..., Any]:
        """Retrieve a registered custom assertion function."""
        return self.get("assertions", name)

    def is_registered(self, category: str, name: str) -> bool:
        """Check if a component exists in the registry."""
        with self._lock:
            return category in self._components and name in self._components[category]

    def list_components(self, category: Optional[str] = None) -> Union[List[str], Dict[str, List[str]]]:
        """List registered component names for a category or across all categories."""
        with self._lock:
            if category is not None:
                return sorted(list(self._components.get(category, {}).keys()))
            return {cat: sorted(list(comps.keys())) for cat, comps in self._components.items()}

    def list_benchmarks(self) -> List[str]:
        """List all registered benchmark names."""
        return sorted(list(self._components.get("benchmarks", {}).keys()))

    def list_fixtures(self) -> List[str]:
        """List all registered fixture names."""
        return sorted(list(self._components.get("fixtures", {}).keys()))

    def clear(self, category: Optional[str] = None) -> None:
        """Clear components in a specific category or across the entire registry."""
        with self._lock:
            if category is not None:
                self._components.pop(category, None)
            else:
                self._components.clear()

    def get_info(self) -> Dict[str, Any]:
        """Return diagnostic metrics and summary of registered components."""
        with self._lock:
            breakdown = {cat: len(comps) for cat, comps in self._components.items()}
            total_suites = len(self._components.get("suites", {}))
            total_fixtures = len(self._components.get("fixtures", {}))
            total_benchmarks = len(self._components.get("benchmarks", {}))
            total_mocks = len(self._components.get("mocks", {}))
            total_reporters = len(self._components.get("reporters", {}))
            total_assertions = len(self._components.get("assertions", {}))

            return {
                "categories": sorted(list(self._components.keys())),
                "total_components": sum(breakdown.values()),
                "breakdown": breakdown,
                "total_suites": total_suites,
                "total_fixtures": total_fixtures,
                "total_benchmarks": total_benchmarks,
                "total_mocks": total_mocks,
                "total_reporters": total_reporters,
                "total_assertions": total_assertions,
                "fixtures": total_fixtures,
                "suites": total_suites,
                "benchmarks": total_benchmarks,
                "mocks": total_mocks,
                "reporters": total_reporters,
                "assertions": total_assertions,
            }

    # -----------------------------------------------------------------------
    # Backward compatibility API
    # -----------------------------------------------------------------------
    def register_suite(
        self,
        name: str,
        suite_cls_or_factory: Union[Type[Any], Callable[..., Any]],
        category: TestCategory = TestCategory.UNIT,
        required_backends: Optional[List[BackendType]] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        override: bool = True,
    ) -> None:
        meta = {
            "name": name,
            "category": category,
            "required_backends": required_backends or [],
            "description": description,
            "tags": tags or [],
        }
        self.register("suites", name, suite_cls_or_factory, metadata=meta, override=override)

    def register_benchmark(
        self,
        name: str,
        benchmark_fn: Callable[..., Any],
        baseline_fn: Optional[Callable[..., Any]] = None,
        category: TestCategory = TestCategory.BENCHMARK,
        target_backends: Optional[List[BackendType]] = None,
        description: str = "",
        override: bool = True,
    ) -> None:
        meta = {
            "name": name,
            "baseline_fn": baseline_fn,
            "category": category,
            "target_backends": target_backends or [BackendType.PYTHON],
            "description": description,
        }
        self.register("benchmarks", name, benchmark_fn, metadata=meta, override=override)

    def register_fixture(
        self,
        name: str,
        fixture_fn: Callable[..., Any],
        metadata: Optional[Dict[str, Any]] = None,
        override: bool = True,
    ) -> None:
        self.register("fixtures", name, fixture_fn, metadata=metadata, override=override)

    def get_suite(self, name: str) -> Dict[str, Any]:
        with self._lock:
            comp = self.get("suites", name)
            meta = self.get_metadata("suites", name)
            return {"factory": comp, **meta}

    def get_benchmark(self, name: str) -> Dict[str, Any]:
        with self._lock:
            comp = self.get("benchmarks", name)
            meta = self.get_metadata("benchmarks", name)
            return {"fn": comp, **meta}

    def get_fixture(self, name: str) -> Callable[..., Any]:
        return self.get("fixtures", name)

    def list_suites(
        self,
        category: Optional[Union[TestCategory, str]] = None,
        backend: Optional[BackendType] = None,
        tag: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[str]:
        with self._lock:
            res: List[str] = []
            suites = self._components.get("suites", {})
            for s_name, s_data in suites.items():
                meta = s_data.get("metadata", {})
                if category is not None:
                    cat_val = category.value if hasattr(category, "value") else str(category)
                    s_cat = meta.get("category")
                    s_cat_val = s_cat.value if hasattr(s_cat, "value") else str(s_cat)
                    if cat_val.upper() != s_cat_val.upper():
                        continue
                if backend and backend not in meta.get("required_backends", []):
                    continue
                if tag and tag not in meta.get("tags", []):
                    continue
                if tags and not all(t in meta.get("tags", []) for t in tags):
                    continue
                res.append(s_name)
            return sorted(res)


# ---------------------------------------------------------------------------
# Global Singleton and Decorator Helpers
# ---------------------------------------------------------------------------
TEST_REGISTRY = TestRegistry()


def get_test_registry() -> TestRegistry:
    """Return global singleton TestRegistry instance."""
    return TEST_REGISTRY


def _create_register_decorator(category: str):
    def decorator_factory(
        name_or_func: Optional[Union[str, Callable[..., Any]]] = None,
        name: Optional[str] = None,
        category_kw: Optional[Any] = None,
        override: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        **extra_meta: Any,
    ):
        combined_meta = dict(metadata or {})
        combined_meta.update(extra_meta)
        if category_kw is not None:
            combined_meta["category"] = category_kw
        if "category" in extra_meta:
            combined_meta["category"] = extra_meta["category"]
        if tags is not None:
            combined_meta["tags"] = tags

        actual_name = name or (name_or_func if isinstance(name_or_func, str) else None)

        if callable(name_or_func):
            func = name_or_func
            comp_name = actual_name or getattr(func, "__name__", str(func))
            combined_meta["name"] = comp_name
            TEST_REGISTRY.register(category, comp_name, func, metadata=combined_meta, override=override)
            return func

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            comp_name = actual_name or getattr(fn, "__name__", str(fn))
            combined_meta["name"] = comp_name
            TEST_REGISTRY.register(category, comp_name, fn, metadata=combined_meta, override=override)
            return fn

        return decorator

    return decorator_factory


register_test_suite = _create_register_decorator("suites")
register_benchmark = _create_register_decorator("benchmarks")
register_fixture = _create_register_decorator("fixtures")
register_mock = _create_register_decorator("mocks")
register_reporter = _create_register_decorator("reporters")
register_assertion = _create_register_decorator("assertions")


def create_fixture(name: str, *args: Any, **kwargs: Any) -> Any:
    """Create or retrieve a registered fixture."""
    return TEST_REGISTRY.create("fixtures", name, *args, **kwargs)


def create_mock(name: str, *args: Any, **kwargs: Any) -> Any:
    """Create or retrieve a registered mock component."""
    return TEST_REGISTRY.create("mocks", name, *args, **kwargs)


def create_reporter(name: str, *args: Any, **kwargs: Any) -> Any:
    """Create or retrieve a registered reporter."""
    if TEST_REGISTRY.is_registered("reporters", name):
        return TEST_REGISTRY.create("reporters", name, *args, **kwargs)
    from .reporters import create_reporter as create_rep_factory
    return create_rep_factory(name, *args, **kwargs)


def list_available_fixtures() -> List[str]:
    """List all registered fixtures."""
    return list(TEST_REGISTRY.list_components("fixtures"))


def list_available_test_suites(
    category: Optional[Union[TestCategory, str]] = None,
    tag: Optional[str] = None,
) -> List[str]:
    """List all registered test suites."""
    return TEST_REGISTRY.list_suites(category=category, tag=tag)


def list_available_benchmarks() -> List[str]:
    """List all registered benchmark names."""
    return TEST_REGISTRY.list_benchmarks()


def list_available_reporters() -> List[str]:
    """List all registered test reporters."""
    return list(TEST_REGISTRY.list_components("reporters"))


def list_available_mocks() -> List[str]:
    """List all registered mock components."""
    return list(TEST_REGISTRY.list_components("mocks"))


def list_available_assertions() -> List[str]:
    """List all registered assertion helpers."""
    return list(TEST_REGISTRY.list_components("assertions"))


def get_test_registry_info() -> Dict[str, Any]:
    """Return diagnostic summary of global test registry."""
    return TEST_REGISTRY.get_info()


def is_test_component_registered(category: str, name: str) -> bool:
    """Check if component is registered in global test registry."""
    return TEST_REGISTRY.is_registered(category, name)


__all__ = [
    "TestRegistry",
    "TEST_REGISTRY",
    "get_test_registry",
    "register_test_suite",
    "register_benchmark",
    "register_fixture",
    "register_mock",
    "register_reporter",
    "register_assertion",
    "create_fixture",
    "create_mock",
    "create_reporter",
    "list_available_fixtures",
    "list_available_test_suites",
    "list_available_benchmarks",
    "list_available_reporters",
    "list_available_mocks",
    "list_available_assertions",
    "get_test_registry_info",
    "is_test_component_registered",
]
