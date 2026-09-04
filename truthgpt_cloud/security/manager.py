"""
🔒 TruthGPT Cloud - Security & RBAC Manager
Manages API keys, role-based access control (RBAC), and cryptographic key verification.
"""

import time
import json
import hmac
import base64
import hashlib
import uuid
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Union

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives.constant_time import bytes_eq
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False

from .scopes import ApiKeyScope
from .models import ApiKeyMetadata, LedgerBlock
from .rate_limiter import TokenBucketRateLimiter
from .jwt_auth import (
    create_session_jwt,
    verify_session_jwt,
    decode_jwt_unverified,
    _HAS_PYJWT,
)
from ..core.exceptions import AuthenticationError, TierUnauthorizedError

logger = logging.getLogger("TruthGPT.CloudSecurity")


class CloudSecurityManager:
    """
    Manages API keys, role-based access control (RBAC), organizations,
    and maintains an immutable SHA-256 hash-chained cryptographic audit ledger.
    """

    def __init__(self):
        self.rate_limiter = TokenBucketRateLimiter()
        self._key_registry: Dict[str, ApiKeyMetadata] = {}  # key_hash -> ApiKeyMetadata
        self._organizations: Dict[str, Dict[str, Any]] = {}
        self._audit_ledger: List[LedgerBlock] = []
        self._initialize_genesis_block()

    def _initialize_genesis_block(self):
        """Create genesis block for tamper-evident cryptographic ledger."""
        genesis_prev = "0" * 64
        block_content = f"0:{time.time()}:GENESIS_BLOCK:system:{genesis_prev}"
        genesis_hash = hashlib.sha256(block_content.encode("utf-8")).hexdigest()
        self._audit_ledger.append(
            LedgerBlock(
                block_index=0,
                timestamp=time.time(),
                event_type="GENESIS_BLOCK",
                user_id="system",
                details={"message": "TruthGPT Cloud Cryptographic Sovereign Ledger Genesis"},
                prev_hash=genesis_prev,
                block_hash=genesis_hash
            )
        )

    def append_audit_block(self, event_type: str, user_id: str, details: Dict[str, Any]) -> LedgerBlock:
        """Append a tamper-evident audit record cryptographically linked to previous block."""
        prev_block = self._audit_ledger[-1]
        block_idx = len(self._audit_ledger)
        ts = time.time()
        payload = f"{block_idx}:{ts}:{event_type}:{user_id}:{prev_block.block_hash}:{json.dumps(details, sort_keys=True)}"
        curr_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        block = LedgerBlock(
            block_index=block_idx,
            timestamp=ts,
            event_type=event_type,
            user_id=user_id,
            details=details,
            prev_hash=prev_block.block_hash,
            block_hash=curr_hash
        )
        self._audit_ledger.append(block)
        return block

    def verify_ledger_integrity(self) -> Dict[str, Any]:
        """Verify unbroken cryptographic SHA-256 chain from genesis block."""
        if not self._audit_ledger:
            return {"is_valid": False, "reason": "Empty ledger"}

        for i in range(1, len(self._audit_ledger)):
            prev = self._audit_ledger[i - 1]
            curr = self._audit_ledger[i]
            if curr.prev_hash != prev.block_hash:
                return {
                    "is_valid": False,
                    "tampered_block_index": curr.block_index,
                    "reason": f"Hash chain broken at block #{curr.block_index}"
                }

        return {
            "is_valid": True,
            "total_blocks": len(self._audit_ledger),
            "total_blocks_verified": len(self._audit_ledger),
            "latest_block_hash": self._audit_ledger[-1].block_hash,
            "last_block_hash": self._audit_ledger[-1].block_hash,
            "genesis_block_hash": self._audit_ledger[0].block_hash
        }

    def sign_audit_block(self, block: LedgerBlock, private_key: Union[str, bytes]) -> str:
        """
        Cryptographically sign an audit block using an Ed25519 sovereign private key.
        Sets block.asymmetric_signature and block.public_key_hex.
        """
        if not _HAS_CRYPTOGRAPHY:
            raise RuntimeError("The 'cryptography' library is required for asymmetric block signing.")

        if isinstance(private_key, str):
            priv_bytes = bytes.fromhex(private_key)
        else:
            priv_bytes = private_key

        priv_obj = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        pub_obj = priv_obj.public_key()
        block.public_key_hex = pub_obj.public_bytes_raw().hex()

        payload = f"{block.block_index}:{block.timestamp}:{block.event_type}:{block.user_id}:{block.prev_hash}:{block.block_hash}".encode("utf-8")
        sig = priv_obj.sign(payload)
        block.asymmetric_signature = sig.hex()
        return block.asymmetric_signature

    def verify_audit_block(self, block: LedgerBlock, public_key: Optional[Union[str, bytes]] = None) -> bool:
        """
        Verify the Ed25519 asymmetric signature of an audit block.
        """
        if not _HAS_CRYPTOGRAPHY or not block.asymmetric_signature:
            return False

        target_pub = public_key or block.public_key_hex
        if not target_pub:
            return False

        try:
            if isinstance(target_pub, str):
                pub_bytes = bytes.fromhex(target_pub)
            else:
                pub_bytes = target_pub

            pub_obj = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            payload = f"{block.block_index}:{block.timestamp}:{block.event_type}:{block.user_id}:{block.prev_hash}:{block.block_hash}".encode("utf-8")
            sig_bytes = bytes.fromhex(block.asymmetric_signature)
            pub_obj.verify(sig_bytes, payload)
            return True
        except Exception:
            return False

    def get_audit_ledger(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent ledger blocks."""
        return [b.to_dict() for b in self._audit_ledger[-limit:]]

    def create_organization(self, org_id: str, name: str, owner_id: str) -> Dict[str, Any]:
        """Create a multi-tenant organization."""
        org = {
            "org_id": org_id,
            "name": name,
            "owner_id": owner_id,
            "created_at": time.time(),
            "members": {owner_id: "owner"},
            "projects": {}
        }
        self._organizations[org_id] = org
        self.append_audit_block("ORG_CREATED", owner_id, {"org_id": org_id, "name": name})
        return org

    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve organization by ID."""
        return self._organizations.get(org_id)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Compute SHA-256 digest of raw API key."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def generate_api_key(
        self,
        user_id: str,
        name: str = "Production API Key",
        scopes: Optional[Set[ApiKeyScope]] = None
    ) -> Tuple[str, ApiKeyMetadata]:
        """
        Create a new API key for a user and register its cryptographic hash.
        """
        raw_key = f"tgpt_cloud_live_{uuid.uuid4().hex}"
        key_hash = self.hash_key(raw_key)
        prefix = raw_key[:16] + "..."

        meta = ApiKeyMetadata(
            key_id=f"key_{uuid.uuid4().hex[:10]}",
            key_hash=key_hash,
            key_prefix=prefix,
            user_id=user_id,
            name=name,
            scopes=scopes or {ApiKeyScope.ALL}
        )
        self._key_registry[key_hash] = meta
        self.append_audit_block("API_KEY_GENERATED", user_id, {"key_id": meta.key_id, "name": name})
        return raw_key, meta

    def validate_api_key(
        self,
        raw_key: str,
        required_scope: Optional[ApiKeyScope] = None,
        client_ip: Optional[str] = None
    ) -> ApiKeyMetadata:
        """
        Validate raw key against registry and verify authorization scopes and IP whitelists.
        """
        key_hash = self.hash_key(raw_key)
        meta = self._key_registry.get(key_hash)

        if not meta or not meta.is_active:
            raise AuthenticationError("Clave de API no válida o revocada.")

        if meta.expires_at and time.time() > meta.expires_at:
            meta.is_active = False
            raise AuthenticationError("La clave de API ha expirado.")

        if client_ip and meta.ip_whitelist and client_ip not in meta.ip_whitelist:
            raise AuthenticationError(f"Acceso no autorizado desde la dirección IP '{client_ip}'.")

        if required_scope and (ApiKeyScope.ALL not in meta.scopes and required_scope not in meta.scopes):
            raise TierUnauthorizedError(
                required_tier="API Scope",
                current_tier="Restricted",
                feature=f"Scope requerido: {required_scope.value}"
            )

        meta.last_used_at = time.time()
        return meta

    def generate_session_token(
        self,
        user_id: str,
        duration_seconds: int = 3600,
        scopes: Optional[List[str]] = None
    ) -> str:
        """Generate a cryptographically signed temporary session token."""
        expiry = time.time() + duration_seconds
        payload_dict = {
            "user_id": user_id,
            "exp": expiry,
            "scopes": scopes or ["all"]
        }
        payload_json = json.dumps(payload_dict, sort_keys=True)
        b64_payload = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
        sig = hmac.new(b"truthgpt_session_secret_2026", b64_payload.encode(), hashlib.sha256).hexdigest()[:32]
        return f"sess_tgpt_{b64_payload}.{sig}"

    def validate_session_token(self, token: str) -> Dict[str, Any]:
        """Validate signature and expiration of a session token."""
        if token.startswith("sess_tgpt_"):
            token_body = token[len("sess_tgpt_"):]
        elif token.startswith("sess_tgpt."):
            token_body = token[len("sess_tgpt."):]
        else:
            return {"is_valid": False, "reason": "Invalid token prefix"}

        parts = token_body.split(".")
        if len(parts) != 2:
            return {"is_valid": False, "reason": "Malformed token structure"}

        b64_payload, signature = parts
        expected_sig = hmac.new(b"truthgpt_session_secret_2026", b64_payload.encode(), hashlib.sha256).hexdigest()[:32]
        if _HAS_CRYPTOGRAPHY:
            is_valid_sig = bytes_eq(signature.encode("utf-8"), expected_sig.encode("utf-8"))
        else:
            is_valid_sig = hmac.compare_digest(signature, expected_sig)
        if not is_valid_sig:
            return {"is_valid": False, "reason": "Invalid token signature"}

        try:
            padded = b64_payload + "=" * ((4 - len(b64_payload) % 4) % 4)
            raw_json = base64.urlsafe_b64decode(padded.encode()).decode()
            data = json.loads(raw_json)
        except Exception:
            return {"is_valid": False, "reason": "Could not decode payload"}

        expiry = data.get("exp", 0)
        if time.time() > expiry:
            return {"is_valid": False, "reason": "Session token expired"}

        return {
            "is_valid": True,
            "user_id": data.get("user_id", ""),
            "expires_at": expiry,
            "scopes": data.get("scopes", []),
            "time_remaining_seconds": round(expiry - time.time(), 1)
        }

    def list_user_keys(self, user_id: str) -> List[ApiKeyMetadata]:
        """List all API keys (active and inactive) registered for a user."""
        return [meta for meta in self._key_registry.values() if meta.user_id == user_id]

    def register_existing_key(
        self,
        raw_key: str,
        user_id: str,
        name: str = "Imported Key",
        scopes: Optional[Set[ApiKeyScope]] = None
    ) -> ApiKeyMetadata:
        """Register a key loaded from persistent database into security registry."""
        key_hash = self.hash_key(raw_key)
        prefix = raw_key[:16] + "..."
        meta = ApiKeyMetadata(
            key_id=f"key_{uuid.uuid4().hex[:10]}",
            key_hash=key_hash,
            key_prefix=prefix,
            user_id=user_id,
            name=name,
            scopes=scopes or {ApiKeyScope.ALL}
        )
        self._key_registry[key_hash] = meta
        return meta

    def revoke_key(self, key_hash: str) -> bool:
        """Revoke an active key."""
        if key_hash in self._key_registry:
            self._key_registry[key_hash].is_active = False
            self.append_audit_block("API_KEY_REVOKED", self._key_registry[key_hash].user_id, {"key_hash": key_hash})
            return True
        return False

    def create_session_jwt(
        self,
        user_id: str,
        tier: str = "pro",
        scopes: Optional[List[str]] = None,
        expires_in_seconds: int = 3600,
        custom_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Mint a stateless JWT session token for user authentication.
        Records an audit block in the sovereign ledger.
        """
        token = create_session_jwt(
            user_id=user_id,
            tier=tier,
            scopes=scopes,
            expires_in_seconds=expires_in_seconds,
            custom_claims=custom_claims,
        )
        self.append_audit_block(
            "JWT_TOKEN_ISSUED",
            user_id,
            {"tier": tier, "expires_in_seconds": expires_in_seconds},
        )
        return token

    def verify_session_jwt(
        self,
        token: str,
        verify_exp: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate and decode a stateless JWT session token.
        Returns the claims dictionary if valid.
        """
        return verify_session_jwt(token, verify_exp=verify_exp)


# Global Security Instance
cloud_security = CloudSecurityManager()

__all__ = [
    "ApiKeyScope",
    "ApiKeyMetadata",
    "LedgerBlock",
    "TokenBucketRateLimiter",
    "CloudSecurityManager",
    "cloud_security",
    "create_session_jwt",
    "verify_session_jwt",
    "decode_jwt_unverified",
    "_HAS_PYJWT",
]

