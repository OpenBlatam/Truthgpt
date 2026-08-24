"""
Unified Factory Subsystem for Learning
======================================
Provides factory functions to dynamically create, configure, and initialize
learning modules, strategies, optimizers, and composite pipelines.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List, Optional, Type, Union

from .exceptions import (
    LearnerConfigurationError,
    LearnerInitializationError,
    LearnerNotFoundError,
)
from .registry import LearningRegistry, LEARNING_REGISTRY
from .types import LearningStrategyType

logger = logging.getLogger(__name__)


class LearningFactory:
    """Unified factory class for creating learning modules and strategies."""

    @staticmethod
    def create_module(
        module_type: Union[str, LearningStrategyType],
        config: Optional[Union[Dict[str, Any], Any]] = None,
        **kwargs: Any
    ) -> Any:
        return create_learning_module(module_type, config=config, **kwargs)

    @staticmethod
    def create_learner(
        learner_type: Union[str, LearningStrategyType],
        config: Optional[Union[Dict[str, Any], Any]] = None,
        **kwargs: Any
    ) -> Any:
        return create_learner(learner_type, config=config, **kwargs)

    @staticmethod
    def create_optimizer(
        optimizer_type: Union[str, LearningStrategyType],
        config: Optional[Union[Dict[str, Any], Any]] = None,
        **kwargs: Any
    ) -> Any:
        return create_learning_optimizer(optimizer_type, config=config, **kwargs)


def create_learning_module(
    module_type: Union[str, LearningStrategyType],
    config: Optional[Union[Dict[str, Any], Any]] = None,
    **kwargs: Any
) -> Any:
    """
    Unified factory function to instantiate any learning module.

    Args:
        module_type: The strategy or optimizer domain (e.g., 'active', 'evolutionary', 'bayesian')
        config: Optional configuration instance or dictionary of hyperparameters
        **kwargs: Additional parameters passed to the configuration or learner constructor

    Returns:
        An initialized instance of the requested learning module or optimizer.
    """
    key = module_type.value if isinstance(module_type, LearningStrategyType) else str(module_type).lower()
    try:
        target = LearningRegistry.get_learner(key)
    except Exception:
        try:
            target = LearningRegistry.get_optimizer(key)
        except Exception as e:
            raise LearnerNotFoundError(f"Learning module '{key}' not found in registry: {e}") from e

    try:
        if config is not None:
            try:
                return target(config=config, **kwargs)
            except TypeError:
                try:
                    return target(config, **kwargs)
                except TypeError:
                    return target(**kwargs)
        else:
            return target(**kwargs)
    except Exception as e:
        raise LearnerInitializationError(
            f"Failed to instantiate learning module '{key}': {e}",
            details={"module_type": key, "error": str(e)}
        ) from e


def create_learner(
    learner_type: Union[str, LearningStrategyType],
    config: Optional[Union[Dict[str, Any], Any]] = None,
    **kwargs: Any
) -> Any:
    """Convenience alias for create_learning_module."""
    return create_learning_module(learner_type, config=config, **kwargs)


def create_learning_optimizer(
    optimizer_type: Union[str, LearningStrategyType],
    config: Optional[Union[Dict[str, Any], Any]] = None,
    **kwargs: Any
) -> Any:
    """Convenience factory for optimization-oriented modules (e.g. bayesian, evolutionary, hpo)."""
    return create_learning_module(optimizer_type, config=config, **kwargs)


__all__ = [
    'LearningFactory',
    'create_learning_module',
    'create_learner',
    'create_learning_optimizer',
]

