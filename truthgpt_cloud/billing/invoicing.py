"""
🧾 TruthGPT Cloud - Invoicing & Charging Engine
Handles direct charges, metered token usage charging, invoice history, and ASCII/text receipt generation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import asdict

from ..core.exceptions import AuthenticationError, TruthGPTCloudError
from .models import Invoice
from .gateways import PaymentGatewayService


def charge_user_handler(
    subscription_manager: Any,
    user_id: str,
    amount_usd: float,
    description: str = "TruthGPT Cloud Service Charge",
    payment_method: str = "stripe_card",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Directly charge a TruthGPT user for cloud service compute, inference, or custom features.
    Processes transaction through PaymentGatewayService and records an official invoice.
    """
    user = subscription_manager.get_user(user_id)
    if not user:
        user = subscription_manager.get_user_by_api_key(user_id)
    if not user:
        raise AuthenticationError(f"Usuario {user_id} no encontrado.")

    if amount_usd <= 0:
        raise TruthGPTCloudError(
            f"El monto a cobrar debe ser mayor que 0 (recibido: {amount_usd})",
            code="INVALID_AMOUNT",
            status_code=400
        )

    # Process payment gateway
    payment_res = PaymentGatewayService.process_payment(
        user_id=user.user_id,
        amount_usd=amount_usd,
        tier_id=f"service_charge_{user.tier.value}",
        billing_cycle="metered",
        payment_method=payment_method
    )

    # Create invoice record
    invoice = Invoice(
        invoice_id=payment_res["invoice_id"],
        user_id=user.user_id,
        tier_id=f"charge_{user.tier.value}",
        amount_usd=amount_usd,
        billing_cycle="metered",
        payment_method=payment_method,
        status="paid",
        discount_applied_usd=0.0,
        promo_code=None,
        created_at=datetime.now(timezone.utc).isoformat()
    )

    with subscription_manager._lock:
        user.invoices.insert(0, invoice)
        user.total_billed_usd = round(sum(inv.amount_usd for inv in user.invoices if inv.status == "paid"), 2)
        subscription_manager._save_storage()

    try:
        from ..telemetry import cloud_telemetry
        cloud_telemetry.record_audit_event(
            "user_charged",
            user.user_id,
            {
                "amount_usd": amount_usd,
                "description": description,
                "payment_method": payment_method,
                "invoice_id": invoice.invoice_id,
                "metadata": metadata or {}
            }
        )
        from .webhooks import webhook_manager
        webhook_manager.emit_event(
            "invoice.paid",
            user.user_id,
            {
                "invoice_id": invoice.invoice_id,
                "amount_usd": amount_usd,
                "description": description,
                "payment_method": payment_method,
                "tier": user.tier.value
            }
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": f"Cobro de ${amount_usd:.2f} USD procesado exitosamente para el usuario {user.name}.",
        "user_id": user.user_id,
        "amount_usd": amount_usd,
        "description": description,
        "payment_method": payment_method,
        "invoice_id": invoice.invoice_id,
        "invoice": asdict(invoice),
        "payment_details": payment_res
    }


def charge_usage_tokens_handler(
    subscription_manager: Any,
    user_id: str,
    tokens_consumed: int,
    unit_price_per_1k_tokens: float = 0.002,
    description: Optional[str] = None,
    payment_method: str = "stripe_card"
) -> Dict[str, Any]:
    """
    Calculate cost for consumed tokens and execute an immediate metered charge for the TruthGPT user.
    """
    amount_usd = max(0.01, round((tokens_consumed / 1000.0) * unit_price_per_1k_tokens, 4))
    desc = description or f"Cobro por consumo de {tokens_consumed:,} tokens en TruthGPT Cloud"
    return charge_user_handler(
        subscription_manager=subscription_manager,
        user_id=user_id,
        amount_usd=amount_usd,
        description=desc,
        payment_method=payment_method,
        metadata={"tokens_consumed": tokens_consumed, "unit_price_per_1k": unit_price_per_1k_tokens}
    )


def get_user_invoices_handler(
    subscription_manager: Any,
    user_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Retrieve paid invoices and billing receipts for a user."""
    user = subscription_manager.get_user(user_id) or subscription_manager.get_user_by_api_key(user_id)
    if not user:
        return []
    invoices = [asdict(inv) for inv in user.invoices]
    return invoices[:limit] if limit is not None else invoices


def get_invoice_receipt_handler(
    subscription_manager: Any,
    user_id: str,
    invoice_id: str
) -> Optional[str]:
    """Generate official ASCII receipt for specified invoice."""
    user = subscription_manager.get_user(user_id) or subscription_manager.get_user_by_api_key(user_id)
    if not user:
        return None
    for inv in user.invoices:
        if inv.invoice_id == invoice_id:
            return inv.to_text_receipt()
    return None
