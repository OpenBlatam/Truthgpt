"""
📝 TruthGPT Cloud Server - Pydantic Request & Response Data Contracts
Provides strongly typed schema definitions for all HTTP REST API endpoints.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 👤 Authentication & User Models
# ---------------------------------------------------------------------------

class UserAuthRequest(BaseModel):
    email: str
    name: str = "TruthGPT Developer"
    initial_tier: str = "free"


class UpgradeRequest(BaseModel):
    user_id: str
    target_tier: str
    billing_cycle: str = "monthly"  # "monthly" or "yearly"
    payment_method: str = "stripe_card"  # "stripe_card", "crypto_usdc"


class IssueTokenRequest(BaseModel):
    user_id: str
    tier: Optional[str] = "pro"
    expires_in_seconds: Optional[int] = 3600
    scopes: Optional[List[str]] = None


class ApplyPromoRequest(BaseModel):
    user_id: str
    promo_code: str
    target_tier: str
    billing_cycle: Optional[str] = "monthly"


# ---------------------------------------------------------------------------
# 🧭 Inference Models
# ---------------------------------------------------------------------------

class ChatCompletionRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = "usr_default_demo"
    model: Optional[str] = None
    enable_swarm: Optional[bool] = None
    enable_formal_verification: Optional[bool] = None
    constraints: Optional[List[str]] = None


class BatchChatRequest(BaseModel):
    prompts: List[str]
    user_id: Optional[str] = "usr_default_demo"
    enable_formal_verification: Optional[bool] = True


class OpenAIChatMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    messages: List[OpenAIChatMessage]
    model: Optional[str] = "truthgpt-pro-smt"
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048


# ---------------------------------------------------------------------------
# 📐 Verification Models
# ---------------------------------------------------------------------------

class FormalVerifyRequest(BaseModel):
    claim: str
    constraints: Optional[List[str]] = None
    tier_depth: Optional[int] = 2


class BatchFormalVerifyRequest(BaseModel):
    claims: List[str]
    tier_depth: Optional[int] = 2


class ExportProofRequest(BaseModel):
    claim: str
    constraints: Optional[List[str]] = None
    tier_depth: Optional[int] = 2


class VerifyContractRequest(BaseModel):
    function_name: str
    preconditions: List[str]
    postconditions: List[str]
    invariants: Optional[List[str]] = None
    code_snippet: Optional[str] = None


class VerifyCertificateRequest(BaseModel):
    certificate_id: str
    proof_tree_hash: str
    theorem_or_claim: str


class ExportSmt2Request(BaseModel):
    claim: str
    constraints: Optional[List[str]] = None
    tier_depth: Optional[int] = 2


class RawSmt2Request(BaseModel):
    smt2_text: str
    timeout_ms: Optional[int] = 5000


class CodePurityVerifyRequest(BaseModel):
    code: str


class SynthesizeTheoremRequest(BaseModel):
    claim: str
    target_language: str = "lean4"  # lean4, coq, isabelle


class TensorShapesVerifyRequest(BaseModel):
    shape_a: List[int]
    shape_b: List[int]
    operation: Optional[str] = "matmul"


class NumericalStabilityVerifyRequest(BaseModel):
    formula_or_loss: str
    gradient_clipping_bound: Optional[float] = 1.0
    epsilon: Optional[float] = 1e-8


class AttentionInvariantsVerifyRequest(BaseModel):
    query_shape: List[int]
    key_shape: List[int]
    value_shape: List[int]
    num_heads_q: Optional[int] = 32
    num_heads_kv: Optional[int] = None
    head_dim: Optional[int] = 128
    is_causal: Optional[bool] = True
    architecture_type: Optional[str] = "FlashAttention-3"


class QuantizationSafetyVerifyRequest(BaseModel):
    min_val: float
    max_val: float
    quant_format: Optional[str] = "INT8"
    symmetric: Optional[bool] = True


class OptimizerConvergenceVerifyRequest(BaseModel):
    optimizer_name: Optional[str] = "AdamW"
    learning_rate: Optional[float] = 1e-3
    beta1: Optional[float] = 0.9
    beta2: Optional[float] = 0.999
    weight_decay: Optional[float] = 0.01
    eps: Optional[float] = 1e-8


class MerkleExclusionRequest(BaseModel):
    tree_leaves: List[str]
    target_claim: str


class DifferentialPrivacyVerifyRequest(BaseModel):
    epsilon: Optional[float] = 1.0
    delta: Optional[float] = 1e-5
    clipping_bound: Optional[float] = 1.0
    noise_multiplier: Optional[float] = 1.1


class MatrixVerifyRequest(BaseModel):
    matrix: List[List[float]]
    matrix_name: Optional[str] = "A"


class ODEVerifyRequest(BaseModel):
    system_matrix: List[List[float]]
    system_name: Optional[str] = "ode_system"


class LoopVerifyRequest(BaseModel):
    loop_condition: str
    invariant_claim: str
    loop_body_effect: Optional[str] = "x = x + 1"


class SpectralNormVerifyRequest(BaseModel):
    matrix: List[List[float]]
    max_norm: float = 1.0


class LipschitzVerifyRequest(BaseModel):
    layer_type: str = "dense"
    weight_spectral_norm: float = 1.0
    activation: str = "relu"
    target_lipschitz: float = 1.0


class MOEVerifyRequest(BaseModel):
    num_experts: int
    top_k: int
    tokens_per_batch: int
    capacity_factor: Optional[float] = 1.25
    gating_weights: Optional[List[float]] = None
    aux_loss_coeff: Optional[float] = 0.01
    drop_tokens: Optional[bool] = False


class ROPEVerifyRequest(BaseModel):
    head_dim: int
    max_position_embeddings: Optional[int] = 8192
    base_theta: Optional[float] = 10000.0
    scaling_factor: Optional[float] = 1.0
    scaling_type: Optional[str] = "linear"
    low_freq_factor: Optional[float] = 1.0
    high_freq_factor: Optional[float] = 4.0


class FlashAttentionVerifyRequest(BaseModel):
    block_m: Optional[int] = 128
    block_n: Optional[int] = 64
    head_dim: Optional[int] = 128
    is_causal: Optional[bool] = True
    precision_bytes: Optional[int] = 2
    sram_budget_bytes: Optional[int] = 227328


class MicroscalingFP8VerifyRequest(BaseModel):
    format: Optional[str] = "e4m3"
    block_size: Optional[int] = 32
    scale_bias: Optional[int] = 127
    values: Optional[List[float]] = None
    max_dynamic_range_db: Optional[float] = 96.0


# ---------------------------------------------------------------------------
# 🐝 Swarm Models
# ---------------------------------------------------------------------------

class SwarmExecuteRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = "usr_default_demo"
    max_agents: Optional[int] = 5


class SwarmDebateRequest(BaseModel):
    topic: str
    proponent_claim: str
    adversary_focus: Optional[str] = "Búsqueda de singularidades y contraejemplos"
    rounds: Optional[int] = 2
    user_id: Optional[str] = "usr_default_demo"


# ---------------------------------------------------------------------------
# 🔔 Webhook Models
# ---------------------------------------------------------------------------

class WebhookRegisterRequest(BaseModel):
    user_id: str
    target_url: str
    subscribed_events: Optional[List[str]] = None


class WebhookTestTriggerRequest(BaseModel):
    user_id: str
    event_type: str = "verification.completed"
    data: Optional[Dict[str, Any]] = None


class WebhookVerifyRequest(BaseModel):
    payload: Dict[str, Any]
    signature: str
    secret: Optional[str] = "tgpt_global_webhook_secret"


# ---------------------------------------------------------------------------
# 🔬 Papers Models
# ---------------------------------------------------------------------------

class ApplyPaperRequest(BaseModel):
    paper_id: str
    user_id: Optional[str] = "usr_default_demo"


# ---------------------------------------------------------------------------
# 📊 Telemetry & Alerts Models
# ---------------------------------------------------------------------------

class RegisterAlertRuleRequest(BaseModel):
    name: str
    metric_key: str
    threshold: float
    comparison: Optional[str] = "gte"
    cooldown_seconds: Optional[float] = 60.0


# ---------------------------------------------------------------------------
# 💳 Checkout, Direct Charge & Churn Management Models
# ---------------------------------------------------------------------------

class CheckoutSessionRequest(BaseModel):
    user_id: str = "usr_default_demo"
    tier_id: str = "pro"
    amount_usd: Optional[float] = None
    billing_cycle: str = "monthly"  # "monthly", "yearly", "one_time"
    customer_email: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PaymentLinkRequest(BaseModel):
    amount_usd: float = 19.99
    description: str = "TruthGPT Cloud Service / Plan Pro"
    user_id: Optional[str] = None


class PortalSessionRequest(BaseModel):
    user_id: str = "usr_default_demo"
    return_url: Optional[str] = None


class DirectChargeRequest(BaseModel):
    user_id: str
    amount_usd: float
    description: Optional[str] = "Cobro puntual TruthGPT Cloud"
    payment_method: Optional[str] = "stripe_card"


class CancelSubscriptionRequest(BaseModel):
    user_id: str
    reason: Optional[str] = "Usuario canceló suscripción"
    feedback: Optional[str] = None


class ReactivateSubscriptionRequest(BaseModel):
    user_id: str
    target_tier: Optional[str] = None


class BillingConfigUpdateRequest(BaseModel):
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    test_after_save: Optional[bool] = True


class CheckoutCompleteRequest(BaseModel):
    user_id: str
    tier_id: Optional[str] = "pro"
    amount_usd: float
    billing_cycle: Optional[str] = "monthly"
    payment_method: Optional[str] = "stripe_card"
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    description: Optional[str] = None


__all__ = [
    "UserAuthRequest",
    "UpgradeRequest",
    "IssueTokenRequest",
    "ApplyPromoRequest",
    "ChatCompletionRequest",
    "BatchChatRequest",
    "OpenAIChatMessage",
    "OpenAIChatRequest",
    "FormalVerifyRequest",
    "BatchFormalVerifyRequest",
    "ExportProofRequest",
    "VerifyContractRequest",
    "VerifyCertificateRequest",
    "ExportSmt2Request",
    "RawSmt2Request",
    "CodePurityVerifyRequest",
    "SynthesizeTheoremRequest",
    "TensorShapesVerifyRequest",
    "NumericalStabilityVerifyRequest",
    "AttentionInvariantsVerifyRequest",
    "QuantizationSafetyVerifyRequest",
    "OptimizerConvergenceVerifyRequest",
    "MerkleExclusionRequest",
    "DifferentialPrivacyVerifyRequest",
    "MatrixVerifyRequest",
    "ODEVerifyRequest",
    "LoopVerifyRequest",
    "SpectralNormVerifyRequest",
    "LipschitzVerifyRequest",
    "MOEVerifyRequest",
    "ROPEVerifyRequest",
    "FlashAttentionVerifyRequest",
    "MicroscalingFP8VerifyRequest",
    "SwarmExecuteRequest",
    "SwarmDebateRequest",
    "WebhookRegisterRequest",
    "WebhookTestTriggerRequest",
    "WebhookVerifyRequest",
    "ApplyPaperRequest",
    "RegisterAlertRuleRequest",
    "CheckoutSessionRequest",
    "PaymentLinkRequest",
    "PortalSessionRequest",
    "DirectChargeRequest",
    "CancelSubscriptionRequest",
    "ReactivateSubscriptionRequest",
    "BillingConfigUpdateRequest",
    "CheckoutCompleteRequest",
]
