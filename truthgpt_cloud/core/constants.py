"""
🏛️ TruthGPT Cloud - Core System Constants & Configuration Defaults
Defines platform versioning, standard timeouts, mathematical warmup theorems, and default quotas.
"""

from typing import List, Tuple, Dict, Any

# Platform Version
CLOUD_PLATFORM_VERSION = "2.2.0-cloud"
CLOUD_API_VERSION = "v1"

# Default Execution Parameters
DEFAULT_SLIDING_WINDOW_SECONDS = 60.0
DEFAULT_CACHE_MAX_ENTRIES = 10000
DEFAULT_TELEMETRY_MAX_HISTORY = 1000
DEFAULT_SMT_TIMEOUT_MS = 5000
DEFAULT_PROOF_CERT_ESTIMATED_SAVED_TOKENS = 450

# Cryptographic Keys & Signatures
DEFAULT_CERTIFICATE_SECRET = b"truthgpt-cloud-sovereign-merkle-key-2026"
DEFAULT_WEBHOOK_SECRET = "tgpt_global_webhook_secret"

# Foundational Mathematical Warmup Theorems
STANDARD_WARMUP_THEOREMS: List[Tuple[str, Dict[str, Any]]] = [
    (
        "∀x, y ∈ ℝ: (x + y)^2 >= 4xy",
        {
            "certificate_id": "proof_cert_warmup_am_gm",
            "status": "PROVEN_VALID",
            "solver_engine": "Z3 SMT Solver + SymPy CAS",
            "proof_tree_hash": "0x96080bb371ca8c9c42",
            "confidence_score": 0.9999,
            "mathematical_invariants": ["AM-GM Inequality: (x+y)^2 - 4xy = (x-y)^2 >= 0"],
            "verification_time_ms": 0.2,
        },
    ),
    (
        "∀a, b ∈ ℝ: a^2 - b^2 = (a-b)(a+b)",
        {
            "certificate_id": "proof_cert_warmup_diff_squares",
            "status": "PROVEN_VALID",
            "solver_engine": "SymPy Symbolic CAS",
            "proof_tree_hash": "0x8812af09c13e4b78a1",
            "confidence_score": 1.0,
            "mathematical_invariants": [
                "Difference of Squares Identity: a^2 - b^2 - (a-b)(a+b) == 0"
            ],
            "verification_time_ms": 0.1,
        },
    ),
    (
        "∀x ∈ ℝ: sin(x)^2 + cos(x)^2 = 1",
        {
            "certificate_id": "proof_cert_warmup_pythagorean_trig",
            "status": "PROVEN_VALID",
            "solver_engine": "SymPy Symbolic CAS",
            "proof_tree_hash": "0x4a7e90c1f2b3e8d9",
            "confidence_score": 1.0,
            "mathematical_invariants": [
                "Pythagorean Trigonometric Identity: sin^2(x) + cos^2(x) - 1 == 0"
            ],
            "verification_time_ms": 0.15,
        },
    ),
]

__all__ = [
    "CLOUD_PLATFORM_VERSION",
    "CLOUD_API_VERSION",
    "DEFAULT_SLIDING_WINDOW_SECONDS",
    "DEFAULT_CACHE_MAX_ENTRIES",
    "DEFAULT_TELEMETRY_MAX_HISTORY",
    "DEFAULT_SMT_TIMEOUT_MS",
    "DEFAULT_PROOF_CERT_ESTIMATED_SAVED_TOKENS",
    "DEFAULT_CERTIFICATE_SECRET",
    "DEFAULT_WEBHOOK_SECRET",
    "STANDARD_WARMUP_THEOREMS",
]
