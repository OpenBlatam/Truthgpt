"""
🔒 TruthGPT Cloud - Enterprise Secrets & Vault Provider
Decouples cryptographic keys, database credentials, and webhook secrets from code,
supporting multi-tier resolution (Environment -> File/K8s Secrets -> In-Memory Vault)
with zero-leakage masking for audit logs and SRE debugging.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class CloudSecretsProvider:
    """
    Resolves secrets securely across environment variables, file mounts (Docker/K8s),
    and runtime in-memory stores with secure masking.
    """

    def __init__(self, secrets_dir: Optional[str] = None):
        self._secrets_dir = Path(secrets_dir) if secrets_dir else Path("/run/secrets")
        self._in_memory_vault: Dict[str, str] = {}

    def set_secret(self, key: str, value: str) -> None:
        """Store a secret in the in-memory vault for current process."""
        self._in_memory_vault[key.upper()] = value

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Resolve a secret value using hierarchical lookup:
        1. In-memory vault
        2. Environment variable: TG_CLOUD_<KEY>
        3. Environment variable: <KEY>
        4. File: /run/secrets/<key_lower> or /run/secrets/<KEY>
        5. Default fallback
        """
        normalized_key = key.upper()

        # 1. In-memory vault
        if normalized_key in self._in_memory_vault:
            return self._in_memory_vault[normalized_key]

        # 2. TG_CLOUD_<KEY>
        env_tg = f"TG_CLOUD_{normalized_key}"
        if env_tg in os.environ:
            return os.environ[env_tg]

        # 3. Standard env var
        if normalized_key in os.environ:
            return os.environ[normalized_key]

        # 4. File-based secret
        try:
            for file_candidate in (key.lower(), normalized_key):
                file_path = self._secrets_dir / file_candidate
                if file_path.is_file():
                    content = file_path.read_text(encoding="utf-8").strip()
                    if content:
                        return content
        except Exception:
            pass

        return default

    @staticmethod
    def mask_secret(value: Optional[str], visible_prefix: int = 7, visible_suffix: int = 4) -> str:
        """
        Mask a secret value for safe logging, displaying only prefix and suffix.
        Example: 'tg_sec_9941a8e74bc29f' -> 'tg_sec_***c29f'
        """
        if not value:
            return "<unset>"
        if len(value) <= (visible_prefix + visible_suffix + 2):
            return "***"
        return f"{value[:visible_prefix]}***{value[-visible_suffix:]}"

    def audit_status(self, keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Produce a security audit report showing configured secrets and their sources
        without exposing cleartext values.
        """
        default_keys = [
            "API_SECRET_KEY",
            "WEBHOOK_SECRET",
            "STORAGE_ENCRYPTION_KEY",
            "REDIS_URL",
            "DATABASE_URL",
            "STRIPE_API_KEY",
        ]
        target_keys = keys or default_keys
        report = {}

        for k in target_keys:
            val = self.get_secret(k)
            source = "unset"
            if k.upper() in self._in_memory_vault:
                source = "vault"
            elif f"TG_CLOUD_{k.upper()}" in os.environ:
                source = "env_prefixed"
            elif k.upper() in os.environ:
                source = "env"
            elif (self._secrets_dir / k.lower()).is_file() or (self._secrets_dir / k.upper()).is_file():
                source = "file"

            report[k] = {
                "is_set": val is not None,
                "source": source,
                "masked": self.mask_secret(val) if val else "<unset>",
            }
        return report

    def audit_secrets_presence(self, required_keys: Optional[List[str]] = None) -> Dict[str, bool]:
        """Audit presence of essential secrets without disclosing their plaintext values."""
        status = self.audit_status(keys=required_keys)
        return {k: v["is_set"] for k, v in status.items()}


# Standalone helper
mask_secret = CloudSecretsProvider.mask_secret

# Global singleton instance & aliases
cloud_secrets_provider = CloudSecretsProvider()
cloud_secrets = cloud_secrets_provider
secrets_provider = cloud_secrets_provider

__all__ = [
    "mask_secret",
    "CloudSecretsProvider",
    "cloud_secrets_provider",
    "cloud_secrets",
    "secrets_provider",
]

