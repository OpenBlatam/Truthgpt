"""
🔒 TruthGPT Cloud - API Key Scopes and Permissions
"""

from enum import Enum


class ApiKeyScope(str, Enum):
    ALL = "all"
    INFERENCE = "inference"
    VERIFY = "verify"
    SWARM = "swarm"
    ADMIN = "admin"
    BILLING = "billing"
    VERIFY_ATTENTION = "verify:attention"
    VERIFY_QUANTIZATION = "verify:quantization"
    VERIFY_OPTIMIZER = "verify:optimizer"
    AUDIT_LEDGER = "audit:ledger"
    SWARM_DEBATE = "swarm:debate"


__all__ = ["ApiKeyScope"]

