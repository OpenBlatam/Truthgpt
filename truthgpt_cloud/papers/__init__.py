"""
SOTA paper registry and compilation package for TruthGPT Cloud.
"""

from .registry import PaperItem, SOTA_PAPERS_CATALOG, get_all_papers, get_paper_by_id
from .compiler import CloudPaperCompiler, cloud_paper_compiler

__all__ = [
    "PaperItem",
    "SOTA_PAPERS_CATALOG",
    "get_all_papers",
    "get_paper_by_id",
    "CloudPaperCompiler",
    "cloud_paper_compiler",
]
