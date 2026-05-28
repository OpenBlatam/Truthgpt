import logging
import httpx
from typing import Optional
from .tool_base import BaseTool

logger = logging.getLogger(__name__)

class WebSearchTool(BaseTool):
    """
    Web search via DuckDuckGo with automatic degradation.

    Strategies (in order):
    1. ``duckduckgo_search`` library
    2. HTTP fallback to DuckDuckGo Lite
    3. Graceful degradation advisory after *_DEGRADED_THRESHOLD* consecutive failures
    """

    name = "web_search"
    _DEGRADED_THRESHOLD = 3

    def __init__(self) -> None:
        self._failures: int = 0

    async def run(self, query: str) -> str:
        logger.info("web_search: %s", query)

        if self._failures >= self._DEGRADED_THRESHOLD:
            return (
                f"[TOOL DEGRADED] web_search ha fallado {self._failures} "
                f"veces consecutivas. Usa tu conocimiento interno. "
                f"Query: '{query}'"
            )

        # Strategy 1: duckduckgo_search library
        result = await self._try_ddgs(query)
        if result is not None:
            return result

        # Strategy 2: HTTP fallback
        result = await self._try_http(query)
        if result is not None:
            return result

        # All failed
        self._failures += 1
        return (
            f"Sin resultados para '{query}'. "
            f"[Fallos: {self._failures}/{self._DEGRADED_THRESHOLD}]. "
            f"Usa tu conocimiento interno."
        )

    async def _try_ddgs(self, query: str) -> Optional[str]:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=5))
                if hits:
                    self._failures = 0
                    lines = [
                        f"{i}. **{h.get('title', '—')}**\n"
                        f"   {h.get('body', '')}\n"
                        f"   Link: {h.get('href', 'N/A')}"
                        for i, h in enumerate(hits, 1)
                    ]
                    return f"Resultados para '{query}':\n\n" + "\n\n".join(lines)
        except ImportError:
            logger.info("duckduckgo_search not installed, trying HTTP.")
        except Exception as exc:
            logger.warning("DDGS failed: %s", exc)
        return None

    async def _try_http(self, query: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                    headers={"User-Agent": "TruthGPT/5.9"},
                )
                if resp.status_code == 200 and len(resp.text) > 500:
                    self._failures = 0
                    return f"Resultados (raw) para '{query}':\n{resp.text[:2000]}"
        except Exception as exc:
            logger.warning("HTTP fallback failed: %s", exc)
        return None

class WebReaderTool(BaseTool):
    """
    Lee el contenido textual de una URL específica usando Crawl4AI. 
    Extrae texto limpio y estructurado en Markdown perfecto para el LLM.
    """
    name = "web_reader"

    async def run(self, url: str) -> str:
        if not url.startswith("http"):
            return "Error: URL inválida."
            
        try:
            from crawl4ai import AsyncWebCrawler
            
            logger.info(f"Crawling URL con Crawl4AI: {url}")
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url=url)
                
                if result.success:
                    # Return perfectly formatted markdown
                    markdown = result.markdown
                    return markdown[:5000] + "\n...[Truncated]" if len(markdown) > 5000 else markdown
                else:
                    return f"Error al crawlear: {result.error_message}"
                    
        except ImportError:
            # Fallback to bs4 if crawl4ai is not installed
            logger.warning("crawl4ai no instalado. Usando fallback bs4.")
            try:
                import bs4
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    soup = bs4.BeautifulSoup(response.text, "html.parser")
                    text = soup.get_text(separator="\n", strip=True)
                    return text[:5000]
            except Exception as e:
                return f"Error en fallback bs4: {str(e)}"
        except Exception as e:
            return f"Error inesperado en WebReaderTool: {str(e)}"
