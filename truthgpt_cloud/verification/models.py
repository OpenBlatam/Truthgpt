"""
🛡️ TruthGPT Cloud - Verification Data Models
Re-exports canonical proof certificate, steps, and contract verification structures.
"""

from .certificate import (
    ProofStep,
    ProofCertificate,
    ContractVerificationResult,
)

__all__ = [
    "ProofStep",
    "ProofCertificate",
    "ContractVerificationResult",
]
