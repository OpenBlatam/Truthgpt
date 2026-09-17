"""
🎟️ TruthGPT Cloud - Promotional Codes & Discount Calculator
Encapsulates promotional rules, discount percentages, and coupon validation.
"""

from typing import Optional, Tuple, Dict, Any

VALID_PROMO_CODES: Dict[str, Dict[str, Any]] = {
    "TRUTH2026": {
        "code": "TRUTH2026",
        "discount_ratio": 0.20,
        "description": "20% de descuento de lanzamiento en planes y paquetes de tokens.",
    },
    "DEV50": {
        "code": "DEV50",
        "discount_ratio": 0.50,
        "description": "50% de descuento para desarrolladores independientes.",
    },
    "SINGULARITY100": {
        "code": "SINGULARITY100",
        "discount_ratio": 1.00,
        "description": "100% de descuento para investigadores académicos y proyectos clave.",
    },
    "FREE100": {
        "code": "FREE100",
        "discount_ratio": 1.00,
        "description": "100% de descuento promocional de prueba gratuita.",
    },
}


def calculate_promo_discount(
    base_amount: float, promo_code: Optional[str]
) -> Tuple[float, float, Optional[str]]:
    """
    Calculate discount amount in USD given a base price and optional promotional coupon code.

    Returns:
        (final_amount_usd, discount_usd, applied_promo_code)
    """
    if not promo_code:
        return max(0.0, round(base_amount, 2)), 0.0, None

    code_clean = promo_code.strip().upper()
    promo = VALID_PROMO_CODES.get(code_clean)

    if promo:
        discount_ratio = promo["discount_ratio"]
        if discount_ratio >= 1.0:
            discount_usd = round(base_amount, 2)
        else:
            discount_usd = round(base_amount * discount_ratio, 2)
        final_amount = max(0.0, round(base_amount - discount_usd, 2))
        return final_amount, discount_usd, code_clean

    # Unknown promo code: 0 discount, promo not applied
    return max(0.0, round(base_amount, 2)), 0.0, None


__all__ = [
    "VALID_PROMO_CODES",
    "calculate_promo_discount",
]
