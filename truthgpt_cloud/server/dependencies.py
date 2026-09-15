"""
🔑 TruthGPT Cloud Server - FastAPI Dependency Injection & Auth Guards
Handles JWT verification, API key extraction, tier authorization, and context binding.
"""

from typing import Optional
from fastapi import Header, HTTPException, Depends

from ..billing.subscription import subscription_manager
from ..security.manager import verify_session_jwt
from ..core.tiers import CloudTier, get_tier_config
from ..core.exceptions import TierUnauthorizedError


async def resolve_user(
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Resolve user from JWT Bearer token, API key, or user header.
    Falls back to 'usr_default_demo' for unauthenticated exploratory calls.
    """
    user_id = "usr_default_demo"
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token.startswith("eyJ"):
            try:
                payload = verify_session_jwt(token)
                user_id = payload.get("sub", "usr_default_demo")
            except Exception:
                pass
        elif token.startswith("tgpt_"):
            user = subscription_manager.get_user_by_api_key(token)
            if user:
                user_id = user.user_id

    elif x_api_key:
        user = subscription_manager.get_user_by_api_key(x_api_key)
        if user:
            user_id = user.user_id
    elif x_user_id:
        user = subscription_manager.get_user(x_user_id)
        if user:
            user_id = user.user_id

    # Record real-time user activity for active usage & churn analytics
    try:
        subscription_manager.record_activity(user_id)
    except Exception:
        pass

    return user_id


def require_tier(required_tier: CloudTier):
    """
    FastAPI dependency factory enforcing a minimum subscription tier.
    """
    async def dependency(user_id: str = Depends(resolve_user)):
        user = subscription_manager.get_user(user_id)
        current_tier = user.tier if user else CloudTier.FREE
        tier_hierarchy = {
            CloudTier.FREE: 0,
            CloudTier.PRO: 1,
            CloudTier.ULTRA: 2,
            CloudTier.ENTERPRISE: 3,
        }
        if tier_hierarchy.get(current_tier, 0) < tier_hierarchy.get(required_tier, 0):
            raise TierUnauthorizedError(
                required_tier=required_tier.value,
                current_tier=current_tier.value,
                feature="Tier Protected Endpoint",
            )
        return user_id
    return dependency


verify_api_key_or_token = resolve_user

__all__ = [
    "resolve_user",
    "require_tier",
    "verify_api_key_or_token",
]
