"""
🌐 TruthGPT Cloud - Client HTTP Layer & Networking Protocol
Provides connection pooling, sync and async httpx client lifecycle management,
and robust event loop handling for synchronous invocations.
"""

import asyncio
from typing import Dict, Any, Optional

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


def _run_sync(coro):
    """
    Execute an async coroutine synchronously, handling nested event loops gracefully.
    Centralizes the repeated pattern of event loop detection + ThreadPoolExecutor fallback.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class ClientHttpMixin:
    """Mixin managing synchronous and asynchronous HTTP/REST networking for TruthGPTCloudClient."""

    base_url: Optional[str] = None
    timeout: float = 30.0
    _http_client: Optional[Any] = None
    _async_http_client: Optional[Any] = None
    api_key: str = ""

    def get_http_client(self) -> Any:
        """Get or initialize sync httpx.Client with connection pooling."""
        if not _HAS_HTTPX:
            raise RuntimeError("The 'httpx' library is required for HTTP operations.")
        if self._http_client is None:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            self._http_client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                limits=limits,
            )
        return self._http_client

    async def get_async_http_client(self) -> Any:
        """Get or initialize async httpx.AsyncClient with connection pooling."""
        if not _HAS_HTTPX:
            raise RuntimeError("The 'httpx' library is required for HTTP operations.")
        if self._async_http_client is None:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
            self._async_http_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                limits=limits,
            )
        return self._async_http_client

    def http_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute HTTP GET request against remote TruthGPT Cloud server."""
        client = self.get_http_client()
        resp = client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def http_post(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute HTTP POST request against remote TruthGPT Cloud server."""
        client = self.get_http_client()
        resp = client.post(path, json=json_data)
        resp.raise_for_status()
        return resp.json()

    async def http_get_async(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute async HTTP GET request against remote TruthGPT Cloud server."""
        client = await self.get_async_http_client()
        resp = await client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def http_post_async(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute async HTTP POST request against remote TruthGPT Cloud server."""
        client = await self.get_async_http_client()
        resp = await client.post(path, json=json_data)
        resp.raise_for_status()
        return resp.json()

    def close(self):
        """Close synchronous HTTP connection pool."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    async def aclose(self):
        """Close asynchronous HTTP connection pool."""
        if self._async_http_client is not None:
            await self._async_http_client.aclose()
            self._async_http_client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
        return False
