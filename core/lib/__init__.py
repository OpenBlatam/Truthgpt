"""
Core Best Libraries Submodule.

Provides integration and management of high-performance libraries:
- BestLibraries: Manager for best-in-class deep learning and numerical libraries
- LibraryCategory, LibraryInfo: Library metadata structures
- create_best_libraries, best_libraries_context: Factory and context manager helpers
"""

from .best_libraries import (
    LibraryCategory,
    LibraryInfo,
    BestLibraries,
    create_best_libraries,
    best_libraries_context,
)

__all__ = [
    "LibraryCategory",
    "LibraryInfo",
    "BestLibraries",
    "create_best_libraries",
    "best_libraries_context",
]
