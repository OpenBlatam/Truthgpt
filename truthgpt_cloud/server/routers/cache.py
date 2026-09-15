"""
⚡ TruthGPT Cloud Server - Proof Cache Router
Provides semantic proof cache statistics, eviction, and distributed L1/L2 Redis status.
"""

from fastapi import APIRouter

from ...cache.proof_cache import proof_cache

router = APIRouter(tags=["Proof Cache"])


@router.get("/api/v1/cloud/cache/stats")
async def get_cache_stats():
    """Retrieve semantic proof cache statistics and savings."""
    return {"success": True, "cache": proof_cache.get_stats()}


@router.post("/api/v1/cloud/cache/purge")
async def purge_cache_endpoint():
    """Purge all expired entries from semantic proof cache."""
    purged_count = proof_cache.purge_expired()
    return {"success": True, "purged_entries": purged_count, "stats": proof_cache.get_stats()}


@router.get("/api/v1/cloud/cache/cluster-status")
async def get_cluster_cache_status_endpoint():
    """Retrieve L1 and L2 Redis distributed proof cache statistics."""
    return {
        "success": True,
        "cache": proof_cache.get_stats(),
    }


__all__ = ["router"]
