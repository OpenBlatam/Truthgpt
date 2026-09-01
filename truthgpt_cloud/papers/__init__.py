"""
SOTA paper registry and compilation package for TruthGPT Cloud.
"""

from .registry import (
    PaperItem,
    SOTA_PAPERS_CATALOG,
    get_all_papers,
    get_paper_by_id,
    search_papers,
    export_bibtex,
    export_apa,
    export_ieee,
)
from .compiler import CloudPaperCompiler, cloud_paper_compiler

__all__ = [
    "PaperItem",
    "SOTA_PAPERS_CATALOG",
    "get_all_papers",
    "get_paper_by_id",
    "search_papers",
    "export_bibtex",
    "export_apa",
    "export_ieee",
    "CloudPaperCompiler",
    "cloud_paper_compiler",
]

