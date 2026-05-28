# 🏗️ Modular Design Specification - Optimization Core

## 📋 Executive Summary

This document specifies the modular design principles and architectural patterns governing `optimization_core`. The goal is to enforce decoupling across layers, ensure high testability through interface mocking, and establish a runtime registry for dynamic component resolution.

---

## 🎯 Modular Design Objectives

1.  **Separation of Concerns (SoC)**: Separate orchestration logic, data pipelines, hardware-specific inference, and utility functions into dedicated modules.
2.  **Low Coupling**: Subsystems interact through stable, abstract interfaces rather than concrete implementations.
3.  **High Cohesion**: Keep related functions grouped in the same modules, minimizing dependency chains.
4.  **Extensibility**: Allow new backends or data engines to be registered at runtime without modifying existing core modules.
5.  **Test Isolation**: Facilitate mocking of hardware-level resources (GPUs, CUDA devices) during unit tests.

---

## 📐 SOLID Principles Applied

### 1. Single Responsibility Principle (SRP)
Every class or module has a single operational responsibility.

```python
# ✅ RECOMMENDED: Separated responsibilities
class VLLMEngine(BaseInferenceEngine):
    """Responsible solely for hosting vLLM models and generating completions."""
    pass

class PolarsProcessor(BaseDataProcessor):
    """Responsible solely for executing query graphs on Polars dataframes."""
    pass

# ❌ AVOID: Multiple responsibilities in a single class
class CoreEngineAndProcessor:
    """Combines inference execution and data processing, violating SRP."""
    pass
```

### 2. Open/Closed Principle (OCP)
Core classes are open for extension but closed for modification. New backends extend base classes without changing core registry loaders.

```python
# ✅ RECOMMENDED: Extended via inheritance
class BaseInferenceEngine(ABC):
    @abstractmethod
    def _generate_impl(self, prompts: List[str], **kwargs: Any) -> List[str]:
        pass

class TensorRTLLMEngine(BaseInferenceEngine):
    def _generate_impl(self, prompts: List[str], **kwargs: Any) -> List[str]:
        # Custom TensorRT-LLM implementation without modifying the base class
        pass

# ❌ AVOID: Modifying the base engine to add new backends
class StaticInferenceEngine:
    def generate(self, prompts: List[str], engine_type: str) -> List[str]:
        if engine_type == "vllm":
            return self._run_vllm(prompts)
        elif engine_type == "tensorrt":
            # Direct modifications required to add backends, violating OCP
            return self._run_trt(prompts)
```

### 3. Liskov Substitution & Dependency Inversion Principles (LSP & DIP)
High-level orchestrators depend on abstract interfaces, allowing any subclass to be substituted at runtime without changing caller code.

```python
# ✅ RECOMMENDED: Depends on abstraction
async def generate_response(engine: IInferenceEngine, prompt: str) -> str:
    return await engine.agenerate(prompt)

# ❌ AVOID: Depends on concrete implementation
async def generate_response(engine: VLLMEngine, prompt: str) -> str:
    return await engine.agenerate(prompt)
```

### 4. Interface Segregation Principle (ISP)
Interfaces are specific and single-purpose rather than monolithic.

```python
# ✅ RECOMMENDED: Specialized interfaces
class IInferenceEngine(IComponent):
    @abstractmethod
    async def agenerate(self, prompts: Union[str, List[str]], **kwargs: Any) -> Union[str, List[str]]:
        pass

class IDataProcessor(IComponent):
    @abstractmethod
    def process(self, data: Any, operations: List[Dict[str, Any]], **kwargs: Any) -> Any:
        pass

# ❌ AVOID: Monolithic interface forcing unused implementations
class IMonolithicComponent(IComponent):
    @abstractmethod
    def generate(self, prompts: List[str]) -> List[str]: pass
    @abstractmethod
    def process(self, data: Any) -> Any: pass
    @abstractmethod
    def train_model(self, weights: bytes) -> None: pass
```

---

## 📦 Directory Structure

The codebase is organized into layered directories:

```
optimization_core/
├── core/                   # Abstraction Layer
│   ├── interfaces.py       # Async abstract base classes
│   ├── base_classes.py     # Base initializers
│   └── factories.py        # Shared factory registries
│
├── inference/              # Inference Layer
│   ├── base_engine.py      # Base engine setup
│   ├── vllm_engine.py      # vLLM implementation
│   └── trt_engine.py       # TensorRT implementation
│
├── data/                   # Data Processing Layer
│   ├── polars_processor.py # Polars implementation
│   └── factory.py          # Data factory resolver
│
├── polyglot_core/          # Polyglot Routing Layer
│   ├── backend.py          # Discovery logic
│   ├── cache.py            # Unified cache facade
│   └── compression.py      # FFI compression bridge
│
└── utils/                  # Utility Layer
    ├── validation/         # Input validators
    ├── error_handling/     # Exception guards
    └── metrics/            # Observability counters
```

---

## 🔌 Decoupling Patterns

### 1. Component Registry Pattern
We implement a runtime registry to register and resolve components dynamically using decorators.

```python
# core/factories.py
from typing import Dict, Type, Any

class ComponentRegistry:
    """Thread-safe registry for dynamically discovering and loading components."""
    
    _registry: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a class to the registry."""
        def decorator(subclass: Type[Any]):
            cls._registry[name] = subclass
            return subclass
        return decorator

    @classmethod
    def resolve(cls, name: str, **kwargs: Any) -> Any:
        """Instantiates a registered component by name.

        Args:
            name: Registry identifier of the class.
            **kwargs: Arguments passed to the target class constructor.

        Returns:
            An instance of the registered class.

        Raises:
            KeyError: If the class name is not registered.
        """
        if name not in cls._registry:
            raise KeyError(f"Component '{name}' is not registered.")
        return cls._registry[name](**kwargs)
```

### 2. Factory Registration Example

```python
# inference/vllm_engine.py
from optimization_core.core.factories import ComponentRegistry
from optimization_core.inference.base_engine import BaseInferenceEngine

@ComponentRegistry.register("vllm")
class VLLMEngine(BaseInferenceEngine):
    """vLLM implementation registered dynamically."""
    
    def initialize(self, **kwargs: Any) -> 'VLLMEngine':
        # Resource allocation logic
        return self
```

---

## 🧪 Modular Unit Testing

By depending on abstract interfaces, we can verify caller logic using standard mocks without triggering native CUDA loads or spawning Rust threads.

```python
import pytest
from unittest.mock import AsyncMock
from optimization_core.core.interfaces import IInferenceEngine

@pytest.mark.asyncio
async def test_orchestration_loop_with_engine_mock():
    """Verify orchestrator logic using a mocked inference interface."""
    # Instantiate an AsyncMock conforming to the IInferenceEngine interface
    mock_engine = AsyncMock(spec=IInferenceEngine)
    mock_engine.agenerate.return_value = "Mocked Response Output"
    
    # Run caller code using the mock
    response = await mock_engine.agenerate("Test Prompt")
    
    assert response == "Mocked Response Output"
    mock_engine.agenerate.assert_called_once_with("Test Prompt")
```

---

## ⚠️ Architectural Anti-Patterns to Avoid

1.  **God Objects**: Avoid consolidating orchestration, FFI loading, and metrics tracking into a single class. Divide these responsibilities into dedicated modules.
2.  **Circular Import Chains**: Ensure imports flow down the layered architecture (`inference/` depends on `core/`, but `core/` must never import from `inference/`). Use dependency injection where necessary.
3.  **Direct Concrete Instantiations**: Do not instantiate concrete engines directly in caller logic (e.g. avoiding `engine = VLLMEngine()`). Instead, resolve instances using the factory:
    `engine = ComponentRegistry.resolve("vllm")`

---

**Specification Version**: 1.1.0  
**Last Updated**: March 2026  
**Architectural Scope**: Decoupling and Design Standards
