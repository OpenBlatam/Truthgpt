import logging
import httpx
from typing import Optional
from .tool_base import BaseTool

logger = logging.getLogger(__name__)

class WebSearchTool(BaseTool):
    """
    Búsqueda en internet con degradación automática.

    Estrategias (en orden):
    1. ``utils.internet_search.search_internet`` — motor unificado
       (Tavily si hay ``TAVILY_API_KEY``, con fallback a Wikipedia + DuckDuckGo).
    2. HTTP directo a DuckDuckGo Lite.
    3. Aviso de degradación tras *_DEGRADED_THRESHOLD* fallos consecutivos.
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

        # Strategy 1: unified internet search engine (Tavily + Wikipedia + ddgs)
        result = await self._try_unified(query)
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

    # Palabras que sugieren que el usuario quiere información reciente.
    _RECENCY_HINTS = (
        "latest", "today", "recent", "current", "now", "breaking", "2026",
        "hoy", "ahora", "reciente", "última", "ultima", "últimas", "actual",
        "noticias", "news",
    )

    @classmethod
    def _detect_recency(cls, query: str) -> Optional[str]:
        q = query.lower()
        return "week" if any(h in q for h in cls._RECENCY_HINTS) else None

    async def _try_unified(self, query: str) -> Optional[str]:
        """Delegate to the shared multi-source search engine."""
        try:
            try:
                from utils.internet_search import search_internet
            except ImportError:
                from optimization_core.utils.internet_search import search_internet

            hits = await search_internet(query, max_results=5, recency=self._detect_recency(query))
            if hits:
                self._failures = 0
                lines = [
                    f"{i}. **{h.get('title', '—')}**\n"
                    f"   {h.get('snippet', '')}\n"
                    f"   Link: {h.get('link', 'N/A')}"
                    for i, h in enumerate(hits, 1)
                ]
                return f"Resultados para '{query}':\n\n" + "\n\n".join(lines)
        except ImportError:
            logger.info("internet_search no disponible, probando HTTP directo.")
        except Exception as exc:
            logger.warning("search_internet falló: %s", exc)
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
    _MAX_CHARS = 5000

    # Cabeceras de navegador: muchos sitios devuelven 403 sin un User-Agent realista.
    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es,en;q=0.9",
    }

    def _truncate(self, text: str) -> str:
        text = text.strip()
        if len(text) > self._MAX_CHARS:
            return text[:self._MAX_CHARS] + "\n...[Truncado]"
        return text

    async def run(self, url: str) -> str:
        url = (url or "").strip()
        if not url.startswith("http"):
            return "Error: URL inválida (debe empezar por http/https)."

        try:
            from crawl4ai import AsyncWebCrawler

            logger.info(f"Crawling URL con Crawl4AI: {url}")
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)

                if result.success and result.markdown:
                    return self._truncate(result.markdown)
                logger.warning("Crawl4AI sin contenido (%s); usando fallback bs4.",
                               getattr(result, "error_message", "?"))
        except ImportError:
            logger.info("crawl4ai no instalado. Usando fallback bs4.")
        except Exception as e:
            logger.warning("Crawl4AI falló (%s); usando fallback bs4.", e)

        # Fallback robusto con httpx + BeautifulSoup
        return await self._fallback_bs4(url)

    async def _fallback_bs4(self, url: str) -> str:
        try:
            import bs4
            async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                         headers=self._HEADERS) as client:
                response = await client.get(url)
                response.raise_for_status()

                ctype = response.headers.get("content-type", "")
                if "html" not in ctype and "xml" not in ctype:
                    # Contenido no-HTML (PDF, JSON, texto plano...): devolver crudo acotado.
                    if ctype.startswith("text/") or "json" in ctype:
                        return self._truncate(response.text)
                    return f"Contenido no textual ({ctype or 'desconocido'}) en {url}."

                soup = bs4.BeautifulSoup(response.text, "html.parser")
                # Eliminar ruido estructural antes de extraer texto.
                for tag in soup(["script", "style", "noscript", "nav", "footer",
                                 "header", "aside", "form", "svg"]):
                    tag.decompose()
                main = soup.find("main") or soup.find("article") or soup.body or soup
                text = main.get_text(separator="\n", strip=True)
                if not text:
                    return f"No se extrajo texto legible de {url}."
                return self._truncate(text)
        except httpx.HTTPStatusError as e:
            return f"Error HTTP {e.response.status_code} al leer {url}."
        except Exception as e:
            return f"Error al leer {url}: {str(e)}"
