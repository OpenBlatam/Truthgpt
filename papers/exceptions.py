"""
Domain exceptions for TruthGPT research papers optimization core.
"""

from __future__ import annotations


class PaperError(Exception):
    """Base exception for all research paper optimization errors."""
    pass


class PaperConfigError(PaperError):
    """Raised when an invalid configuration is supplied to a paper algorithm."""
    pass


class PaperValidationError(PaperError):
    """Raised when input validation fails for an algorithm method."""
    pass


class PaperExecutionError(PaperError):
    """Raised when an error occurs during algorithm execution or optimization."""
    pass


class PaperNotFoundError(PaperError):
    """Raised when a requested research paper or algorithm is not found in the registry."""
    pass


__all__ = [
    "PaperError",
    "PaperConfigError",
    "PaperValidationError",
    "PaperExecutionError",
    "PaperNotFoundError",
]
