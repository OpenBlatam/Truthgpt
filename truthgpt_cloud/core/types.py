"""
🏛️ TruthGPT Cloud - Core Typing, Enums & Protocol Types
Provides centralized type definitions, structured enumerations, and type contracts
for the TruthGPT Cloud platform.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, TypedDict, Union, Protocol, runtime_checkable


class CloudFeature(str, Enum):
    """Supported feature flags across the TruthGPT Cloud ecosystem."""
    FORMAL_VERIFICATION = "formal_verification"
    SWARM_ORCHESTRATION = "swarm_orchestration"
    CIRCUIT_BREAKER = "circuit_breaker"
    SEMANTIC_CACHE = "semantic_cache"
    SRE_ALERTING = "sre_alerting"
    CRYPTOGRAPHIC_AUDIT_LEDGER = "cryptographic_audit_ledger"
    SMT2_SOLVER = "smt2_solver"
    PAPER_COMPILER = "paper_compiler"
    STORAGE_PERSISTENCE = "storage_persistence"
    RATE_LIMITING = "rate_limiting"


class VerificationEngineType(str, Enum):
    """Engines and provers available for formal verification."""
    Z3_SMT = "z3_smt"
    SYMPY_CAS = "sympy_cas"
    LEAN4 = "lean4"
    COQ = "coq"
    ISABELLE = "isabelle"
    NATIVE_HEURISTIC = "native_heuristic"


class ProofStatus(str, Enum):
    """Possible outcomes of formal verification."""
    PROVEN_VALID = "PROVEN_VALID"
    VERIFIED_SYMBOLIC = "VERIFIED_SYMBOLIC"
    SAT = "SAT"
    UNSAT = "UNSAT"
    COUNTEREXAMPLE_FOUND = "COUNTEREXAMPLE_FOUND"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"
    REJECTED = "REJECTED"


class SwarmTopologyType(str, Enum):
    """Network topologies for multi-agent swarm orchestration."""
    HIERARCHICAL = "hierarchical"
    STAR = "star"
    RING = "ring"
    MESH = "mesh"
    ADVERSARIAL_DEBATE = "adversarial_debate"


class PaymentMethodType(str, Enum):
    """Supported payment gateways and transaction rails."""
    STRIPE_CARD = "stripe_card"
    CRYPTO_USDC = "crypto_usdc"
    CRYPTO_ETH = "crypto_eth"
    WIRE_TRANSFER = "wire_transfer"


class AlertComparisonOp(str, Enum):
    """Comparison operators for SRE metric alerting rules."""
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"


class CloudModuleInfo(TypedDict):
    """Metadata describing a canonical TruthGPT Cloud subpackage."""
    name: str
    import_path: str
    category: str
    description: str
    version: str
    exports: List[str]


class CloudPlatformStatus(TypedDict):
    """Operational status summary of the TruthGPT Cloud cluster."""
    platform: str
    version: str
    api_version: str
    status: str
    active_tiers: List[str]
    features: Dict[str, bool]
    registered_modules_count: int


__all__ = [
    "CloudFeature",
    "VerificationEngineType",
    "ProofStatus",
    "SwarmTopologyType",
    "PaymentMethodType",
    "AlertComparisonOp",
    "CloudModuleInfo",
    "CloudPlatformStatus",
]
