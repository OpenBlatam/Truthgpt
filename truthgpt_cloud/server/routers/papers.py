"""
🔬 TruthGPT Cloud Server - Research Papers Router
Provides SOTA research paper catalog browsing, search, citation exports, and JIT compilation.
"""

from dataclasses import asdict
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from ..models import ApplyPaperRequest
from ...papers.registry import (
    get_all_papers,
    search_papers,
    export_bibtex,
    export_apa,
    export_ieee,
)
from ...papers.compiler import cloud_paper_compiler

router = APIRouter(tags=["Research Papers"])


@router.get("/api/v1/cloud/papers/hub")
async def get_papers_hub():
    """Retrieve curated SOTA AI Research papers available in the TruthGPT Cloud Hub."""
    papers_raw = get_all_papers()
    papers = [p if isinstance(p, dict) else (p.to_dict() if hasattr(p, "to_dict") else asdict(p)) for p in papers_raw]
    return {"success": True, "total_papers": len(papers), "papers": papers}


@router.post("/api/v1/cloud/papers/apply")
async def apply_paper(req: ApplyPaperRequest):
    """Compile and activate a SOTA paper technique directly into cloud runtime."""
    res = cloud_paper_compiler.compile_paper_technique(req.paper_id)
    return res


@router.get("/api/v1/cloud/papers/search")
async def search_papers_endpoint(
    query: str = Query("", description="Search term"),
    category: Optional[str] = Query(None, description="Category filter"),
    tier: Optional[str] = Query(None, description="Tier filter")
):
    """Search catalogued research papers with filters."""
    results = search_papers(query=query, category=category, tier=tier)
    return {"success": True, "count": len(results), "papers": [asdict(p) for p in results]}


@router.get("/api/v1/cloud/papers/{paper_id}/citation")
async def get_paper_citation_endpoint(
    paper_id: str,
    format: str = Query("bibtex", description="Citation format: bibtex, apa, ieee")
):
    """Export research paper citation."""
    fmt = format.lower()
    if fmt == "apa":
        cite = export_apa(paper_id)
    elif fmt == "ieee":
        cite = export_ieee(paper_id)
    else:
        cite = export_bibtex(paper_id)
    return PlainTextResponse(cite, media_type="text/plain")


__all__ = ["router"]
