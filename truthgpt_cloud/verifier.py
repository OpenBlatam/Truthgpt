"""
🛡️ TruthGPT Cloud - Verifier Compatibility Bridge
Re-exports verifier and certificates from the canonical truthgpt_cloud.verification package.
"""

from .verification import (
    ProofStep,
    ContractVerificationResult,
    ProofCertificate,
    compute_merkle_root,
    verify_proof_certificate,
    CloudFormalVerifier,
    cloud_verifier,
)

__all__ = [
    "ProofStep",
    "ContractVerificationResult",
    "ProofCertificate",
    "compute_merkle_root",
    "verify_proof_certificate",
    "CloudFormalVerifier",
    "cloud_verifier",
]
