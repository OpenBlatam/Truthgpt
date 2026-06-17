import asyncio
import logging
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote
import httpx
from typing import Optional, List, Dict, Any
from .tool_base import BaseTool

logger = logging.getLogger(__name__)


def _import_search_internet():
    """Importa el motor de búsqueda compartido, tolerando ambos layouts de paquete."""
    try:
        from utils.internet_search import search_internet
    except ImportError:
        from optimization_core.utils.internet_search import search_internet
    return search_internet

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
        "latest", "today", "recent", "current", "now", "breaking", "news",
        "hoy", "ahora", "reciente", "última", "ultima", "últimas", "actual",
        "noticias",
    )
    # Límites de palabra para evitar falsos positivos (p.ej. "now" en "knowledge").
    _RECENCY_RE = re.compile(r"\b(?:" + "|".join(_RECENCY_HINTS) + r")\b", re.IGNORECASE)
    _YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

    @classmethod
    def _detect_recency(cls, query: str) -> Optional[str]:
        if cls._RECENCY_RE.search(query):
            return "week"
        # Mención de un año actual o futuro → también indica recencia.
        current_year = datetime.now().year
        if any(int(y) >= current_year for y in cls._YEAR_RE.findall(query)):
            return "week"
        return None

    async def _try_unified(self, query: str) -> Optional[str]:
        """Delegate to the shared multi-source search engine."""
        try:
            search_internet = _import_search_internet()
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

    # User-Agent de navegador: DuckDuckGo devuelve páginas vacías a UAs no realistas.
    _HTTP_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es,en;q=0.9",
    }

    @staticmethod
    def _decode_ddg_url(href: str) -> str:
        """Resuelve los links de redirección de DuckDuckGo (//duckduckgo.com/l/?uddg=...)."""
        if href.startswith("//"):
            href = "https:" + href
        parsed = urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            uddg = parse_qs(parsed.query).get("uddg")
            if uddg:
                return unquote(uddg[0])
        return href

    def _parse_ddg_lite(self, html: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Extrae (title, link, snippet) del HTML de DuckDuckGo Lite.

        Empareja título y snippet por orden en el documento (más robusto que por
        índice) y descarta anuncios / enlaces internos de DuckDuckGo.
        """
        import bs4
        soup = bs4.BeautifulSoup(html, "html.parser")
        results: List[Dict[str, str]] = []
        pending: Optional[Dict[str, str]] = None

        def _flush() -> None:
            nonlocal pending
            if pending is None:
                return
            host = urlparse(pending["link"]).netloc.lower()
            # Las URLs que siguen en duckduckgo.com son ads (y.js) o links de ayuda.
            if pending["title"] and pending["link"] and not host.endswith("duckduckgo.com"):
                results.append(pending)
            pending = None

        # Recorre links y snippets en orden de aparición.
        for el in soup.select("a.result-link, td.result-snippet"):
            classes = el.get("class") or []
            if el.name == "a":          # nuevo resultado: cierra el anterior
                _flush()
                pending = {
                    "title": el.get_text(strip=True),
                    "link": self._decode_ddg_url(el.get("href", "")),
                    "snippet": "",
                }
            elif "result-snippet" in classes and pending is not None:
                pending["snippet"] = el.get_text(" ", strip=True)
                _flush()
            if len(results) >= max_results:
                return results
        _flush()
        return results[:max_results]

    async def _try_http(self, query: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True,
                                         headers=self._HTTP_HEADERS) as client:
                # DuckDuckGo Lite sirve los resultados vía POST del formulario.
                resp = await client.post(
                    "https://lite.duckduckgo.com/lite/",
                    data={"q": query},
                )
            if resp.status_code != 200:
                logger.warning("HTTP fallback: status %s", resp.status_code)
                return None

            try:
                hits = self._parse_ddg_lite(resp.text)
            except ImportError:
                logger.info("bs4 no instalado; no se puede parsear el HTML de DuckDuckGo.")
                return None

            if hits:
                self._failures = 0
                lines = [
                    f"{i}. **{h['title']}**\n"
                    f"   {h['snippet']}\n"
                    f"   Link: {h['link']}"
                    for i, h in enumerate(hits, 1)
                ]
                return f"Resultados para '{query}':\n\n" + "\n\n".join(lines)
            logger.info("HTTP fallback: sin resultados parseables para '%s'.", query)
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


class DeepResearchTool(BaseTool):
    """
    Investigación profunda en internet en una sola llamada: busca el tema,
    abre en paralelo las páginas de los mejores resultados, extrae su contenido
    y devuelve un dossier consolidado con fuentes citadas (título, URL y extracto).
    Úsala cuando necesites información detallada y verificada, no solo titulares.
    Entrada: el tema a investigar (opcionalmente 'tema:::N' para fijar N fuentes a leer, máx 5).
    """
    name = "deep_research"

    _DEFAULT_PAGES = 3
    _MAX_PAGES = 5
    _PER_PAGE_CHARS = 1800

    def _parse_input(self, tool_input: str) -> tuple[str, int]:
        """Acepta 'tema' o 'tema:::N' para controlar cuántas fuentes leer."""
        raw = (tool_input or "").strip()
        n = self._DEFAULT_PAGES
        if ":::" in raw:
            query, _, n_str = raw.rpartition(":::")
            query = query.strip() or raw
            try:
                n = max(1, min(self._MAX_PAGES, int(n_str.strip())))
            except ValueError:
                query = raw
        else:
            query = raw
        return query, n

    async def run(self, tool_input: str) -> str:
        query, num_pages = self._parse_input(tool_input)
        if not query:
            return "Error: indica un tema a investigar."

        logger.info("deep_research: %r (leyendo %d fuentes)", query, num_pages)

        # 1) Buscar (multi-fuente, con caché/dedup/recencia heredados)
        try:
            search_internet = _import_search_internet()
            hits: List[Dict[str, Any]] = await search_internet(query, max_results=max(num_pages + 2, 5))
        except Exception as e:
            return f"Error en la fase de búsqueda para '{query}': {e}"

        if not hits:
            return f"No se encontraron fuentes en internet para: '{query}'."

        # 2) Seleccionar las primeras URLs http(s) válidas y leerlas en paralelo
        readable = [h for h in hits if str(h.get("link", "")).startswith("http")][:num_pages]
        reader = WebReaderTool()

        async def _read(hit: Dict[str, Any]) -> Dict[str, Any]:
            content = await reader.run(hit["link"])
            return {**hit, "content": content[:self._PER_PAGE_CHARS]}

        read_results = await asyncio.gather(
            *(_read(h) for h in readable), return_exceptions=True
        )

        # 3) Construir el dossier consolidado
        lines = [f"# Investigación profunda: {query}\n",
                 f"Fuentes consultadas: {len(readable)} (de {len(hits)} encontradas)\n"]
        for i, res in enumerate(read_results, 1):
            if isinstance(res, Exception):
                lines.append(f"## {i}. [Error leyendo fuente]: {res}\n")
                continue
            title = res.get("title", "—") or "—"
            link = res.get("link", "N/A")
            snippet = (res.get("snippet", "") or "").strip()
            content = (res.get("content", "") or "").strip()
            body = content if len(content) > len(snippet) else snippet
            lines.append(
                f"## {i}. {title}\n"
                f"Fuente: {link}\n\n"
                f"{body or '[Sin contenido extraíble]'}\n"
            )

        # Adjuntar resultados extra solo-snippet (no leídos) como referencias rápidas
        extra = [h for h in hits if h not in readable and str(h.get('title', '')).strip()]
        if extra:
            lines.append("## Referencias adicionales (no leídas en detalle)")
            for h in extra[:5]:
                lines.append(f"- {h.get('title', '—')} — {h.get('link', 'N/A')}")

        return "\n".join(lines)
