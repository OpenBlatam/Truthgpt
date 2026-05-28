# 🔌 Core Interfaces Specification - Optimization Core

## 📋 Executive Summary

This document specifies the core interfaces, abstract base classes, configuration objects, and standard exception hierarchies for `optimization_core`. These interfaces serve as the strictly typed architectural contracts that all components (Inference Engines, Data Processors, and Caching layers) must implement.

---

## 🎯 Interface Design Principles

1.  **Asynchronous-First Foundations**: All primary operations (weight loading, generating completions, streaming sequences, reading/writing files) are defined as coroutines to ensure non-blocking concurrent orchestration.
2.  **Zero-Copy Memory Contracts**: Interfaces handling intensive array/buffer payloads rely on Python's buffer protocol (`memoryview` or `bytes`) rather than high-overhead serialized forms:
    $$Overhead_{serialization} \approx 0$$
3.  **Strict Typing**: Every interface is annotated with type signatures compliant with `mypy --strict`.
4.  **Pydantic Input Validation**: User input and system configuration objects utilize Pydantic schemas to validate parameters at system boundaries.

---

## 📦 Core Subsystem Interfaces

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from pathlib import Path
from pydantic import BaseModel, Field

class IComponent(ABC):
    """Abstract base lifecycle interface for all system subsystems."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the registry name of the component.
        
        Returns:
            A string identifier (e.g., 'PolarsProcessor').
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Returns the semantic version of the component.
        
        Returns:
            A version string (e.g., '1.1.0').
        """
        pass
    
    @abstractmethod
    def initialize(self, **kwargs: Any) -> 'IComponent':
        """Executes synchronous resource allocation (e.g., config parsing).
        
        Args:
            **kwargs: System configuration options.
            
        Returns:
            The initialized component instance.
            
        Raises:
            ComponentLifecycleError: If initialization parameters are invalid.
        """
        pass
        
    @abstractmethod
    async def ainitialize(self, **kwargs: Any) -> 'IComponent':
        """Executes asynchronous resource allocation (e.g., socket connections).
        
        Args:
            **kwargs: System configuration options.
            
        Returns:
            The initialized component instance.
            
        Raises:
            ComponentLifecycleError: If asynchronous loading fails.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Synchronously releases allocated resources (handles, memory, sockets)."""
        pass
        
    @abstractmethod
    async def acleanup(self) -> None:
        """Asynchronously releases allocated resources."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Retrieves non-blocking diagnostic and observability metrics.
        
        Returns:
            A dictionary containing health indicators, active errors, and performance metrics.
            Example:
            {
                "name": "PolarsProcessor",
                "version": "1.1.0",
                "health": "healthy",
                "metrics": {"total_operations": 42},
                "last_error": None
            }
        """
        pass
```

### IInferenceEngine

```python
class IInferenceEngine(IComponent):
    """Asynchronous interface for Large Language Model (LLM) inference engines."""
    
    @abstractmethod
    async def agenerate(
        self,
        prompts: Union[str, List[str]],
        config: Optional['GenerationConfig'] = None,
        **kwargs: Any
    ) -> Union[str, List[str]]:
        """Asynchronously generates text completions.
        
        Args:
            prompts: A single string prompt or a list of prompts.
            config: Configuration defining temperature, top_p, etc.
            **kwargs: Dynamic generation flags.
            
        Returns:
            Generated text string or list of text strings.
            
        Raises:
            NotInitializedError: If the model has not been loaded.
            ValueError: If the generation parameters are invalid.
        """
        pass
        
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        config: Optional['GenerationConfig'] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """Asynchronously streams generated tokens.
        
        Args:
            prompt: Input text prompt.
            config: Generation configuration parameters.
            **kwargs: Dynamic generation parameters.
            
        Yields:
            Text tokens sequentially.
            
        Raises:
            NotInitializedError: If the model has not been loaded.
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Retrieves model metadata and hardware footprints.
        
        Returns:
            A dictionary containing model parameter counts, layers, and device allocations.
        """
        pass
    
    @abstractmethod
    def load_model(self, model: Union[str, Path], **kwargs: Any) -> bool:
        """Loads model weights into memory.
        
        Args:
            model: Filepath or model hub identifier.
            **kwargs: Backend configuration (device, dtype, precision).
            
        Returns:
            True if loading is successful, False otherwise.
            
        Raises:
            ModelLoadError: If loading the weights fails.
        """
        pass
    
    @property
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Indicates if the model has been loaded into memory.
        
        Returns:
            True if model weights are loaded, False otherwise.
        """
        pass
```

### IDataProcessor

```python
class IDataProcessor(IComponent):
    """Interface for Lazy data evaluation and Out-of-Core streaming transformations."""
    
    @abstractmethod
    def process(
        self,
        data: Any,
        operations: List[Dict[str, Any]],
        **kwargs: Any
    ) -> Any:
        """Applies a sequence of logical operations to a dataframe or dataset.
        
        Args:
            data: Dataframe (Polars/Pandas) or Lazy graph object.
            operations: List of operation descriptors (filters, joins, projections).
            **kwargs: Execution options.
            
        Returns:
            The transformed dataset or Lazy graph.
            
        Raises:
            SchemaValidationError: If operations fail schema verification.
        """
        pass
    
    @abstractmethod
    async def aread(
        self,
        path: Union[str, Path],
        format: Optional[str] = None,
        **kwargs: Any
    ) -> Any:
        """Asynchronously reads a dataset file.
        
        Args:
            path: Target file path.
            format: Data format (e.g., 'parquet', 'csv'). If None, inferred from extension.
            **kwargs: Reader-specific options.
            
        Returns:
            The loaded dataset or Lazy graph object.
            
        Raises:
            DataIOError: If reading the file fails.
        """
        pass
    
    @abstractmethod
    async def awrite(
        self,
        data: Any,
        path: Union[str, Path],
        format: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        """Asynchronously writes a dataset to disk.
        
        Args:
            data: The dataset (DataFrame or LazyFrame) to write.
            path: Target destination file path.
            format: Data format (e.g., 'parquet', 'csv').
            **kwargs: Writer-specific options.
            
        Returns:
            True if write completes successfully, False otherwise.
            
        Raises:
            DataIOError: If writing the file fails.
        """
        pass
```

---

## 📦 Pydantic Configuration Model

```python
class GenerationConfig(BaseModel):
    """Pydantic-based configuration model enforcing strict bounds at system boundaries."""
    
    max_tokens: int = Field(
        default=100, 
        ge=1, 
        description="Maximum number of tokens to generate."
    )
    temperature: float = Field(
        default=0.7, 
        ge=0.0, 
        le=2.0, 
        description="Sampling temperature."
    )
    top_p: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0, 
        description="Nucleus sampling probability."
    )
    top_k: int = Field(
        default=-1, 
        description="Top-k sampling. Set to -1 to disable."
    )
    repetition_penalty: float = Field(
        default=1.0, 
        ge=0.0, 
        description="Penalty factor for repeating tokens."
    )
    stop_sequences: Optional[List[str]] = Field(
        default=None, 
        description="List of sequences that halt token generation."
    )
    seed: Optional[int] = Field(
        default=None, 
        description="Random seed for deterministic generation."
    )

    class Config:
        frozen = True
        extra = "forbid"
```

---

## 🏭 Component Registry Interface

```python
class IComponentFactory(ABC):
    """Abstract interface for the dynamic Component Registry."""
    
    @classmethod
    @abstractmethod
    def register(cls, name: str) -> Any:
        """Decorator to register a concrete class to the factory.
        
        Args:
            name: Registry identifier for the class.
        """
        pass
    
    @classmethod
    @abstractmethod
    def create(cls, name: str, **kwargs: Any) -> IComponent:
        """Instantiates a registered component.
        
        Args:
            name: Registry identifier of the component.
            **kwargs: Initialization arguments.
            
        Returns:
            The instantiated component instance.
            
        Raises:
            KeyError: If the component name is not registered.
        """
        pass
```

---

## 🚨 System Exception Hierarchy

All exceptions raised by the core subsystems inherit from a unified base exception.

```python
class OptimizationCoreError(Exception):
    """Base exception for all Optimization Core runtime errors."""
    pass

class ComponentLifecycleError(OptimizationCoreError):
    """Raised during invalid transition phases in initialize() or cleanup()."""
    pass

class MemoryConstraintError(OptimizationCoreError):
    """Raised when an operation exceeds pre-allocated memory or FFI buffer bounds."""
    pass

class DataIOError(OptimizationCoreError):
    """Raised for input/output operational failures during file operations."""
    pass

class SchemaValidationError(OptimizationCoreError):
    """Raised when dataset schemas fail validation tests."""
    pass
```

---

## 🧪 Verification and Testing

During testing, asynchronous boundaries are validated using standard mocks.

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_inference_engine_contract():
    """Verify inference execution using a mock conforming to IInferenceEngine."""
    # Instantiate engine mock
    engine = AsyncMock(spec=IInferenceEngine)
    engine.agenerate.return_value = "Sequential Output"
    
    # Run test
    result = await engine.agenerate("Input Sequence")
    
    assert result == "Sequential Output"
    engine.agenerate.assert_called_once_with("Input Sequence")
```

---

**Specification Version**: 1.1.0  
**Last Updated**: March 2026  
**Architectural Scope**: Core Interface Definitions
