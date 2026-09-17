"""
📦 TruthGPT Cloud - Token Pack Catalog & Top-Up Operations
Provides catalog definitions and pack validation for on-demand token top-ups.
"""

from typing import Dict, List, Optional, Any
from ..core.exceptions import TruthGPTCloudError

TOKEN_PACK_CATALOG: List[Dict[str, Any]] = [
    {
        "pack_id": "pack_starter",
        "name": "Starter Boost Pack",
        "tokens": 500_000,
        "price_usd": 5.00,
        "description": "500,000 tokens adicionales para picos de inferencia y verificación SMT.",
    },
    {
        "pack_id": "pack_pro",
        "name": "Pro Research Pack",
        "tokens": 2_500_000,
        "price_usd": 19.00,
        "description": "2,500,000 tokens adicionales con prioridad de cómputo.",
    },
    {
        "pack_id": "pack_scale",
        "name": "Scale Enterprise Pack",
        "tokens": 10_000_000,
        "price_usd": 65.00,
        "description": "10,000,000 tokens para despliegues a gran escala y swarms paralelos.",
    },
    {
        "pack_id": "pack_enterprise",
        "name": "Frontier Ultra Pack",
        "tokens": 50_000_000,
        "price_usd": 250.00,
        "description": "50,000,000 tokens para cargas masivas con SLA dedicado.",
    },
]


def get_token_pack_catalog() -> List[Dict[str, Any]]:
    """Return the official catalog of top-up token packs as a list of dictionaries."""
    return [dict(p) for p in TOKEN_PACK_CATALOG]


def get_token_pack(pack_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve token pack definition by pack ID, or None if not found."""
    return next((p for p in TOKEN_PACK_CATALOG if p["pack_id"] == pack_id), None)


def validate_token_pack_id(pack_id: str) -> Dict[str, Any]:
    """
    Validate pack_id against TOKEN_PACK_CATALOG.
    Raises TruthGPTCloudError with code INVALID_PACK if unknown.
    """
    pack = get_token_pack(pack_id)
    if not pack:
        valid_ids = [p["pack_id"] for p in TOKEN_PACK_CATALOG]
        raise TruthGPTCloudError(
            f"Paquete de tokens '{pack_id}' no válido. Opciones: {', '.join(valid_ids)}",
            code="INVALID_PACK",
            status_code=400,
        )
    return pack


__all__ = [
    "TOKEN_PACK_CATALOG",
    "get_token_pack_catalog",
    "get_token_pack",
    "validate_token_pack_id",
]
