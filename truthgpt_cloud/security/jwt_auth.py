"""
🔑 TruthGPT Cloud - Enterprise JWT Session & Access Token Engine
Provides high-security JSON Web Token (JWT) minting, asymmetric EdDSA/Ed25519 signing,
symmetric HS256 verification, audience/issuer validation, and scope verification via PyJWT.
"""

import os
import time
import uuid
import logging
from typing import Dict, List, Optional, Any, Union

from ..core.exceptions import AuthenticationError

logger = logging.getLogger("TruthGPT.JWT")

_HAS_PYJWT = False
try:
    import jwt
    _HAS_PYJWT = True
except ImportError:
    _HAS_PYJWT = False

# Default secret key for symmetric JWT tokens (fallback if not in environment)
_DEFAULT_JWT_SECRET = os.environ.get("TRUTHGPT_JWT_SECRET", "tgpt_cloud_sovereign_jwt_secret_key_2026_x89")
_DEFAULT_ISSUER = "truthgpt:cloud:auth"
_DEFAULT_AUDIENCE = "truthgpt:cloud:api"


def create_session_jwt(
    user_id: str,
    tier: str = "pro",
    scopes: Optional[List[str]] = None,
    expires_in_seconds: int = 3600,
    secret_key: Optional[Union[str, bytes]] = None,
    algorithm: str = "HS256",
    custom_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate and cryptographically sign a stateless JWT session token.

    Args:
        user_id: Unique user identifier (e.g. 'usr_alan_turing').
        tier: Cloud tier assigned to token ('lite', 'pro', 'ultra', 'enterprise').
        scopes: List of permitted permission scopes.
        expires_in_seconds: Token validity lifespan (default 1 hour).
        secret_key: Symmetric key or asymmetric private key.
        algorithm: 'HS256' for HMAC-SHA256 or 'EdDSA' for Ed25519 asymmetric.
        custom_claims: Additional dictionary claims to bundle.

    Returns:
        Encoded JWT token string.
    """
    if not _HAS_PYJWT:
        raise RuntimeError("The 'PyJWT' library is required for JWT token generation.")

    now = int(time.time())
    payload = {
        "sub": user_id,
        "iss": _DEFAULT_ISSUER,
        "aud": _DEFAULT_AUDIENCE,
        "tier": str(tier).lower(),
        "scopes": scopes or ["inference:run", "proof:verify", "cache:read", "swarm:orchestrate"],
        "iat": now,
        "nbf": now,
        "exp": now + expires_in_seconds,
        "jti": f"jti_{uuid.uuid4().hex[:12]}",
    }

    if custom_claims:
        payload.update(custom_claims)

    key = secret_key or _DEFAULT_JWT_SECRET
    token = jwt.encode(payload, key, algorithm=algorithm)
    # PyJWT 2.x returns str
    return token if isinstance(token, str) else token.decode("utf-8")


def verify_session_jwt(
    token: str,
    secret_key: Optional[Union[str, bytes]] = None,
    algorithms: Optional[List[str]] = None,
    audience: Optional[str] = _DEFAULT_AUDIENCE,
    issuer: Optional[str] = _DEFAULT_ISSUER,
    verify_exp: bool = True,
) -> Dict[str, Any]:
    """
    Verify signature, expiration, issuer, and audience of a JWT token.

    Args:
        token: Raw JWT string.
        secret_key: Symmetric key or asymmetric public key.
        algorithms: List of allowed algorithms (defaults to ['HS256', 'EdDSA']).
        audience: Expected audience claim.
        issuer: Expected issuer claim.
        verify_exp: Whether to enforce token expiry.

    Returns:
        Decoded payload claims dictionary.

    Raises:
        AuthenticationError: If token is expired, invalid, or tampered with.
    """
    if not _HAS_PYJWT:
        raise RuntimeError("The 'PyJWT' library is required for JWT token verification.")

    key = secret_key or _DEFAULT_JWT_SECRET
    allowed_algs = algorithms or ["HS256", "EdDSA"]

    options = {
        "verify_signature": True,
        "verify_exp": verify_exp,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_aud": audience is not None,
        "verify_iss": issuer is not None,
    }

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=allowed_algs,
            audience=audience,
            issuer=issuer,
            options=options,
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise AuthenticationError(f"JWT session token has expired: {e}") from e
    except jwt.InvalidAudienceError as e:
        raise AuthenticationError(f"Invalid JWT audience: {e}") from e
    except jwt.InvalidIssuerError as e:
        raise AuthenticationError(f"Invalid JWT issuer: {e}") from e
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid or tampered JWT token: {e}") from e
    except Exception as e:
        raise AuthenticationError(f"Authentication token verification failed: {e}") from e


def decode_jwt_unverified(token: str) -> Dict[str, Any]:
    """Inspect claims of a token without verifying its signature (for diagnostics/logging)."""
    if not _HAS_PYJWT:
        raise RuntimeError("The 'PyJWT' library is required for JWT token decoding.")
    return jwt.decode(token, options={"verify_signature": False})


__all__ = [
    "create_session_jwt",
    "verify_session_jwt",
    "decode_jwt_unverified",
    "_HAS_PYJWT",
]
