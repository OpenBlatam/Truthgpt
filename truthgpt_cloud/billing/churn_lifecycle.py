"""
📊 TruthGPT Cloud - Churn Analytics, Retention & Lifecycle Management
Tracks DAU/WAU/MAU, MRR, ARR, churn rates, cancellation reasons, and reactivation workflows.
"""

import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import threading

from ..core.tiers import CloudTier, get_tier_config
from .models import UserSubscription, Invoice


def calculate_user_activity_metrics(
    user: UserSubscription, now: float
) -> Tuple[float, float, bool, bool, bool]:
    """
    Calculate seconds since active, days inactive, and DAU/WAU/MAU membership flags.

    Returns:
        (sec_since_active, days_inactive, is_dau, is_wau, is_mau)
    """
    last_act = getattr(user, "last_active_at", None) or getattr(
        user.usage, "last_reset_timestamp", 0.0
    )
    sec_since_active = max(0.0, now - last_act) if last_act else 999999999.0
    days_inactive = round(sec_since_active / 86400.0, 1)

    is_dau = sec_since_active <= 86400 or user.usage.tokens_consumed_today > 0
    is_wau = sec_since_active <= 7 * 86400
    is_mau = sec_since_active <= 30 * 86400

    return sec_since_active, days_inactive, is_dau, is_wau, is_mau


def compute_churn_and_usage_dashboard(
    users: Dict[str, UserSubscription],
    lock: threading.RLock,
    gateway_status: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Comprehensive executive analytics for who is using the platform and who stopped using it.
    Computes MRR, ARR, DAU, WAU, MAU, Churn Rate, At-Risk users, and recent transaction log.
    """
    now = time.time()
    active_users_list: List[Dict[str, Any]] = []
    churned_users_list: List[Dict[str, Any]] = []
    at_risk_users_list: List[Dict[str, Any]] = []
    all_invoices: List[Dict[str, Any]] = []

    total_revenue_usd = 0.0
    mrr_usd = 0.0

    dau_count = 0
    wau_count = 0
    mau_count = 0

    with lock:
        for uid, u in users.items():
            tier_cfg = get_tier_config(u.tier)
            u_invoices = [asdict(inv) for inv in u.invoices]
            all_invoices.extend(u_invoices)

            # Total billed
            paid_invoices_sum = sum(
                inv.amount_usd for inv in u.invoices if inv.status == "paid"
            )
            user_billed = round(
                max(float(getattr(u, "total_billed_usd", 0.0)), paid_invoices_sum),
                2,
            )
            total_revenue_usd += user_billed

            # Activity calculation
            sec_since_act, days_inact, is_dau, is_wau, is_mau = (
                calculate_user_activity_metrics(u, now)
            )

            if is_dau:
                dau_count += 1
            if is_wau:
                wau_count += 1
            if is_mau:
                mau_count += 1

            # Churn vs Active status
            is_canceled = u.status in ["canceled", "cancelled"] or getattr(
                u, "churn_status", ""
            ) == "churned"
            is_at_risk = (
                (not is_canceled)
                and (sec_since_act > 7 * 86400)
                and (u.tier != CloudTier.FREE)
            )

            last_act = getattr(u, "last_active_at", None) or getattr(
                u.usage, "last_reset_timestamp", 0.0
            )

            user_summary = {
                "user_id": u.user_id,
                "email": u.email,
                "name": u.name,
                "tier": u.tier.value,
                "tier_name": tier_cfg.name,
                "tier_badge": tier_cfg.badge,
                "status": u.status,
                "churn_status": (
                    "churned"
                    if is_canceled
                    else ("at_risk" if is_at_risk else "active")
                ),
                "billing_cycle": u.billing_cycle,
                "last_active_at": last_act,
                "seconds_since_active": round(sec_since_act, 1),
                "days_inactive": days_inact,
                "tokens_consumed_today": u.usage.tokens_consumed_today,
                "daily_token_limit": tier_cfg.daily_token_limit,
                "percent_quota_used": min(
                    100.0,
                    round(
                        (
                            u.usage.tokens_consumed_today
                            / max(1, tier_cfg.daily_token_limit)
                        )
                        * 100,
                        1,
                    ),
                ),
                "total_tokens_all_time": u.usage.total_tokens_consumed,
                "total_requests": (
                    getattr(u, "total_requests", 0)
                    or u.usage.daily_request_count
                ),
                "requests_today": u.usage.daily_request_count,
                "total_billed_usd": round(user_billed, 2),
                "balance_usd": float(getattr(u, "balance_usd", 0.0)),
                "api_keys_count": len(u.api_keys),
                "created_at": getattr(
                    u, "created_at", u.subscription_start_date
                ),
                "churn_date": getattr(u, "churn_date", None),
                "churn_reason": getattr(u, "churn_reason", None),
                "churn_feedback": getattr(u, "churn_feedback", None),
            }

            if is_canceled:
                churned_users_list.append(user_summary)
            else:
                active_users_list.append(user_summary)
                if is_at_risk:
                    at_risk_users_list.append(user_summary)

                # MRR calculation
                if u.tier != CloudTier.FREE:
                    if u.billing_cycle == "yearly":
                        mrr_usd += tier_cfg.price_yearly_usd / 12.0
                    else:
                        mrr_usd += tier_cfg.price_monthly_usd

    # Sort lists
    active_users_list.sort(key=lambda x: x["last_active_at"], reverse=True)
    churned_users_list.sort(key=lambda x: x.get("churn_date") or "", reverse=True)
    at_risk_users_list.sort(key=lambda x: x["days_inactive"], reverse=True)
    all_invoices.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    total_users = len(users)
    churn_count = len(churned_users_list)
    churn_rate_pct = round((churn_count / max(1, total_users)) * 100.0, 1)
    retention_rate_pct = round(100.0 - churn_rate_pct, 1)

    # Recent event logs
    events_feed: List[Dict[str, Any]] = []
    for inv in all_invoices[:10]:
        events_feed.append(
            {
                "type": "invoice_paid",
                "title": f"Cobro exitoso: ${inv.get('amount_usd', 0):.2f} USD",
                "user_id": inv.get("user_id"),
                "timestamp": inv.get("created_at"),
                "details": f"Plan {inv.get('tier_id', '').upper()} ({inv.get('billing_cycle')})",
            }
        )
    for chu in churned_users_list[:5]:
        events_feed.append(
            {
                "type": "churn",
                "title": f"Baja de usuario: {chu['name']}",
                "user_id": chu["user_id"],
                "timestamp": chu.get("churn_date") or "",
                "details": f"Motivo: {chu.get('churn_reason') or 'No especificado'}",
            }
        )
    for act in active_users_list[:5]:
        if act["requests_today"] > 0:
            events_feed.append(
                {
                    "type": "activity",
                    "title": f"Actividad en vivo: {act['name']}",
                    "user_id": act["user_id"],
                    "timestamp": (
                        datetime.fromtimestamp(
                            act["last_active_at"], timezone.utc
                        ).isoformat()
                        if act["last_active_at"]
                        else ""
                    ),
                    "details": f"{act['requests_today']} peticiones hoy ({act['tokens_consumed_today']:,} tokens)",
                }
            )

    events_feed.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    if gateway_status is None:
        from .gateways import PaymentGatewayService

        gateway_status = PaymentGatewayService.get_gateway_status()

    return {
        "success": True,
        "timestamp": now,
        "kpis": {
            "total_users": total_users,
            "active_users_count": len(active_users_list),
            "churned_users_count": churn_count,
            "at_risk_users_count": len(at_risk_users_list),
            "dau": dau_count,
            "wau": wau_count,
            "mau": mau_count,
            "mrr_usd": round(mrr_usd, 2),
            "arr_usd": round(mrr_usd * 12.0, 2),
            "total_revenue_usd": round(total_revenue_usd, 2),
            "churn_rate_pct": churn_rate_pct,
            "retention_rate_pct": retention_rate_pct,
            "total_invoices_count": len(all_invoices),
        },
        "active_users": active_users_list,
        "churned_users": churned_users_list,
        "at_risk_users": at_risk_users_list,
        "recent_invoices": all_invoices[:20],
        "recent_events": events_feed[:25],
        "gateway_status": gateway_status,
    }


__all__ = [
    "calculate_user_activity_metrics",
    "compute_churn_and_usage_dashboard",
]
