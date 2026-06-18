import os
import time
import asyncio
import logging
from pathlib import Path
from collections import OrderedDict
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

# Map de recencia legible -> (ddgs timelimit, Tavily days)
_RECENCY_MAP: Dict[str, Tuple[str, int]] = {
    "day": ("d", 1),
    "week": ("w", 7),
    "month": ("m", 30),
    "year": ("y", 365),
}

# Caché en memoria con TTL para evitar llamadas de red redundantes.
_CACHE_TTL_SECONDS = 300
_CACHE_MAX_ENTRIES = 256
_SEARCH_CACHE: "OrderedDict[str, Tuple[float, List[Dict[str, Any]]]]" = OrderedDict()


def _cache_get(key: str) -> Optional[List[Dict[str, Any]]]:
    """Devuelve resultados cacheados válidos, o None si no existen/expiraron."""
    entry = _SEARCH_CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if (time.time() - ts) >= _CACHE_TTL_SECONDS:
        _SEARCH_CACHE.pop(key, None)
        return None
    _SEARCH_CACHE.move_to_end(key)  # LRU: marca como reciente
    return value


def _cache_set(key: str, value: List[Dict[str, Any]]) -> None:
    """Guarda en caché purgando expirados y aplicando un tope LRU de tamaño."""
    now = time.time()
    # Purga oportunista de entradas expiradas.
    for k in [k for k, (ts, _) in _SEARCH_CACHE.items() if (now - ts) >= _CACHE_TTL_SECONDS]:
        _SEARCH_CACHE.pop(k, None)
    _SEARCH_CACHE[key] = (now, value)
    _SEARCH_CACHE.move_to_end(key)
    while len(_SEARCH_CACHE) > _CACHE_MAX_ENTRIES:
        _SEARCH_CACHE.popitem(last=False)  # descarta el más antiguo


def _normalize_url(url: str) -> str:
    """Normaliza una URL para deduplicar (sin esquema/trailing slash/fragment)."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        return urlunparse(("", netloc, path, "", parsed.query, "")).lstrip("/")
    except Exception:
        return url.strip().rstrip("/")


def _dedupe(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Elimina duplicados por URL normalizada (o título si no hay URL), preservando orden."""
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for r in results:
        key = _normalize_url(r.get("link", "")) or (r.get("title", "") or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped

_ENV_LOADED = False


def load_env_manually():
    """Manually parse .env files to read TAVILY_API_KEY if not in environment.

    Idempotent: the .env files are read from disk at most once per process.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    paths = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path("C:/blatam-academy/.env"),
        Path("C:/blatam-academy/TruthGPT-main/.env")
    ]
    for p in paths:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k and v and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass

def _tavily_days(recency: Optional[str]) -> Optional[int]:
    entry = _RECENCY_MAP.get(recency or "")
    return entry[1] if entry else None


async def search_tavily(query: str, api_key: str, max_results: int = 5,
                        recency: Optional[str] = None) -> List[Dict[str, Any]]:
    """Query Tavily Search API. Includes a synthesized answer as the first result when available."""
    days = _tavily_days(recency)
    try:
        from tavily import AsyncTavilyClient
        client = AsyncTavilyClient(api_key=api_key)
        kwargs: Dict[str, Any] = {"query": query, "max_results": max_results,
                                  "search_depth": "advanced", "include_answer": True}
        if days is not None:
            kwargs.update(topic="news", days=days)
        response = await client.search(**kwargs)
        results: List[Dict[str, Any]] = []
        answer = response.get("answer")
        if answer:
            results.append({"title": f"Respuesta directa (Tavily): {query}",
                            "link": "", "snippet": answer})
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("content", "")
            })
        return results
    except Exception as e:
        # Fallback to direct HTTP request if official client is missing or fails
        logger.warning(f"AsyncTavilyClient failed, falling back to direct HTTP: {e}")

        # Raw HTTP implementation as secondary fallback
        import httpx
        url = "https://api.tavily.com/search"
        payload: Dict[str, Any] = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": max_results
        }
        if days is not None:
            payload.update(topic="news", days=days)
        headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    if data.get("answer"):
                        results.append({"title": f"Respuesta directa (Tavily): {query}",
                                        "link": "", "snippet": data["answer"]})
                    for item in data.get("results", []):
                        results.append({
                            "title": item.get("title", ""),
                            "link": item.get("url", ""),
                            "snippet": item.get("content", "")
                        })
                    return results
        except Exception as ex:
            logger.error(f"Direct Tavily HTTP request failed: {ex}")
    return []

async def search_wikipedia(query: str, max_results: int = 2) -> List[Dict[str, Any]]:
    """Search Wikipedia for rich reference summaries."""
    def _wiki_sync():
        try:
            import wikipedia
            search_titles = wikipedia.search(query, results=max_results)
            results = []
            for title in search_titles:
                try:
                    summary = wikipedia.summary(title, sentences=3)
                    url_title = title.replace(" ", "_")
                    results.append({
                        "title": f"Wikipedia: {title}",
                        "link": f"https://en.wikipedia.org/wiki/{url_title}",
                        "snippet": summary
                    })
                except Exception:
                    pass
            return results
        except Exception:
            return []
            
    return await asyncio.to_thread(_wiki_sync)

async def search_duckduckgo(query: str, max_results: int = 5,
                            recency: Optional[str] = None) -> List[Dict[str, Any]]:
    """Query DuckDuckGo using the newly installed ddgs library, falling back to manual html scraping."""
    timelimit = (_RECENCY_MAP.get(recency or "") or (None,))[0]
    # Strategy 1: ddgs library
    try:
        from ddgs import DDGS
        def _run_ddgs():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results, timelimit=timelimit))

        hits = await asyncio.to_thread(_run_ddgs)
        if hits:
            results = []
            for h in hits:
                results.append({
                    "title": h.get("title", ""),
                    "link": h.get("href", h.get("link", "")),
                    "snippet": h.get("body", h.get("snippet", ""))
                })
            return results
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"ddgs library failed, falling back to scraper: {e}")

    # Strategy 2: Manual HTML parsing fallback using BeautifulSoup
    import httpx
    from bs4 import BeautifulSoup
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = "https://html.duckduckgo.com/html/"
    params: Dict[str, str] = {"q": query}
    if timelimit:
        params["df"] = timelimit  # filtro temporal (d/w/m/y)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                results = []
                items = soup.select(".result__results .result")
                if not items:
                    items = soup.select(".result")
                
                for a in items[:max_results]:
                    title_elem = a.select_one(".result__title a")
                    snippet_elem = a.select_one(".result__snippet")
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link = title_elem["href"]
                        if "uddg=" in link:
                            from urllib.parse import unquote, urlparse, parse_qs
                            parsed = urlparse(link)
                            qs = parse_qs(parsed.query)
                            if "uddg" in qs:
                                link = qs["uddg"][0]
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                        results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet
                        })
                return results
    except Exception as e:
        logger.warning(f"DuckDuckGo manual scraper fallback failed: {e}")
    return []

async def search_internet(query: str, max_results: int = 5,
                          recency: Optional[str] = None,
                          use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Busca en internet con varias fuentes, dedup y caché.

    Estrategia:
      1. Tavily (si hay ``TAVILY_API_KEY``) — incluye respuesta directa sintetizada.
      2. Fallback keyless: Wikipedia + DuckDuckGo en paralelo (tolerante a fallos).

    Args:
        query: Texto de búsqueda.
        max_results: Máximo de resultados a devolver.
        recency: Filtro temporal opcional: 'day' | 'week' | 'month' | 'year'.
        use_cache: Reutiliza resultados recientes (TTL %d s) para la misma consulta.
    """ % _CACHE_TTL_SECONDS
    query = (query or "").strip()
    if not query:
        return []

    cache_key = f"{query.lower()}|{max_results}|{recency or ''}"
    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.debug("search_internet: cache hit for %r", query)
            return cached

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        load_env_manually()
        api_key = os.getenv("TAVILY_API_KEY")

    results: List[Dict[str, Any]] = []
    if api_key:
        results = await search_tavily(query, api_key, max_results, recency=recency)

    # Fallback / Keyless rich search chain (Wikipedia + ddgs) si Tavily no aporta nada.
    if not results:
        wiki_task = search_wikipedia(query, max_results=2)
        ddg_task = search_duckduckgo(query, max_results=max_results, recency=recency)

        # Ejecutar en paralelo, tolerando que una fuente falle.
        gathered = await asyncio.gather(wiki_task, ddg_task, return_exceptions=True)
        wiki_results, ddg_results = [], []
        for res, label in zip(gathered, ("wikipedia", "duckduckgo")):
            if isinstance(res, Exception):
                logger.warning("Fuente %s falló: %s", label, res)
            else:
                if label == "wikipedia":
                    wiki_results = res
                else:
                    ddg_results = res

        # DuckDuckGo primero (más relevante a la query); Wikipedia como contexto enciclopédico.
        results = ddg_results + wiki_results

    deduped = _dedupe(results)[:max_results]
    if use_cache and deduped:
        _cache_set(cache_key, deduped)
    return deduped
