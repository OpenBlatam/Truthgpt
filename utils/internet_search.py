import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

def load_env_manually():
    """Manually parse .env files to read TAVILY_API_KEY if not in environment."""
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

async def search_tavily(query: str, api_key: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Query Tavily Search API using the official AsyncTavilyClient."""
    try:
        from tavily import AsyncTavilyClient
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(query=query, max_results=max_results)
        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("content", "")
            })
        return results
    except Exception as e:
        # Fallback to direct HTTP request if official client is missing or fails
        import logging
        logging.getLogger(__name__).warning(f"AsyncTavilyClient failed, falling back to direct HTTP: {e}")
        
        # Raw HTTP implementation as secondary fallback
        import httpx
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "max_results": max_results
        }
        headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("results", []):
                        results.append({
                            "title": item.get("title", ""),
                            "link": item.get("url", ""),
                            "snippet": item.get("content", "")
                        })
                    return results
        except Exception as ex:
            logging.getLogger(__name__).error(f"Direct Tavily HTTP request failed: {ex}")
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

async def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Query DuckDuckGo using the newly installed ddgs library, falling back to manual html scraping."""
    # Strategy 1: ddgs library
    try:
        from ddgs import DDGS
        def _run_ddgs():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        
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
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=15)
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
        import logging
        logging.getLogger(__name__).warning(f"DuckDuckGo manual scraper fallback failed: {e}")
    return []

async def search_internet(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search the internet using Tavily (via official AsyncTavilyClient), fallback to ddgs + wikipedia."""
    load_env_manually()
    api_key = os.getenv("TAVILY_API_KEY")
    
    if api_key:
        results = await search_tavily(query, api_key, max_results)
        if results:
            return results
            
    # Fallback / Keyless rich search chain (Wikipedia + ddgs)
    wiki_task = search_wikipedia(query, max_results=2)
    ddg_task = search_duckduckgo(query, max_results=max_results)
    
    # Run in parallel
    wiki_results, ddg_results = await asyncio.gather(wiki_task, ddg_task)
    
    # Merge results, prioritizing Wikipedia at the top
    combined = wiki_results + ddg_results
    return combined[:max_results]
