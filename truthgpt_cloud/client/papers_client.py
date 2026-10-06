"""
🔬 TruthGPT Cloud - Client Papers Mixin
Provides SOTA research paper browsing, compilation, search, and citation export client methods.
"""

from typing import Dict, List, Optional, Any
from ..papers.registry import get_all_papers


class ClientPapersMixin:
    """Mixin encapsulating SOTA paper hub and kernel compilation client SDK methods."""

    def compile_paper(self, paper_id: str) -> Dict[str, Any]:
        """Compile SOTA research paper architecture and synthesize kernel."""
        if getattr(self, "_is_remote", False):
            return self.http_post(f"/api/v1/cloud/papers/{paper_id}/compile")
        return self.paper_compiler.compile_paper_technique(paper_id=paper_id, user_tier=self.tier.value)

    def list_papers(self) -> List[Dict[str, Any]]:
        """List curated research papers available in the TruthGPT Cloud Hub."""
        from dataclasses import asdict
        papers_raw = get_all_papers()
        return [p if isinstance(p, dict) else (p.to_dict() if hasattr(p, "to_dict") else asdict(p)) for p in papers_raw]

    def search_papers(
        self,
        query: str = "",
        category: Optional[str] = None,
        tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search papers in the TruthGPT Cloud Hub."""
        from ..papers.registry import search_papers as _search_papers
        from dataclasses import asdict
        results = _search_papers(query=query, category=category, tier=tier)
        return [asdict(p) for p in results]

    def export_paper_citation(self, paper_id: str, format_type: str = "bibtex") -> str:
        """Export paper citation in BibTeX, APA, or IEEE format."""
        from ..papers.registry import export_bibtex, export_apa, export_ieee
        fmt = format_type.lower()
        if fmt == "apa":
            return export_apa(paper_id)
        elif fmt == "ieee":
            return export_ieee(paper_id)
        return export_bibtex(paper_id)


__all__ = ["ClientPapersMixin"]
