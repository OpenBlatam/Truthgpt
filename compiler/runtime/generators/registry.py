"""
Code Generator Registry for Runtime Compiler
Implementing Factory/Generator pattern for target-specific code generation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..config import RuntimeTarget

logger = logging.getLogger(__name__)

class BaseCodeGenerator(ABC):
    """Abstract Base Class for code generation targets"""

    @property
    @abstractmethod
    def target(self) -> RuntimeTarget:
        pass

    @abstractmethod
    def generate(self, model: Any, input_spec: Optional[Dict[str, Any]] = None) -> Any:
        pass

class NativeCodeGenerator(BaseCodeGenerator):
    target = RuntimeTarget.NATIVE

    def generate(self, model: Any, input_spec: Optional[Dict[str, Any]] = None) -> Any:
        logger.info("Generating native runtime code")
        return model

class CUDACodeGenerator(BaseCodeGenerator):
    target = RuntimeTarget.CUDA

    def generate(self, model: Any, input_spec: Optional[Dict[str, Any]] = None) -> Any:
        logger.info("Generating CUDA runtime code")
        return model

class BytecodeCodeGenerator(BaseCodeGenerator):
    target = RuntimeTarget.BYTECODE

    def generate(self, model: Any, input_spec: Optional[Dict[str, Any]] = None) -> Any:
        logger.info("Generating bytecode runtime code")
        return model

class InterpreterCodeGenerator(BaseCodeGenerator):
    target = RuntimeTarget.INTERPRETER

    def generate(self, model: Any, input_spec: Optional[Dict[str, Any]] = None) -> Any:
        logger.info("Generating interpreter runtime code")
        return model

class CodeGeneratorRegistry:
    """Registry maintaining code generator strategies for target platforms"""

    def __init__(self):
        self._generators: Dict[RuntimeTarget, BaseCodeGenerator] = {}
        self._register_defaults()

    def _register_defaults(self):
        generators = [
            NativeCodeGenerator(),
            CUDACodeGenerator(),
            BytecodeCodeGenerator(),
            InterpreterCodeGenerator()
        ]
        for g in generators:
            self._generators[g.target] = g

    def generate(self, target: RuntimeTarget, model: Any, input_spec: Optional[Dict[str, Any]] = None) -> Any:
        if target in self._generators:
            return self._generators[target].generate(model, input_spec)
        logger.info(f"Fallback: generating interpreter code for target {target}")
        return self._generators[RuntimeTarget.INTERPRETER].generate(model, input_spec)
