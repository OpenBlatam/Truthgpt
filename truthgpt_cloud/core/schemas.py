"""
🏛️ TruthGPT Cloud - Pydantic v2 Canonical Schemas & Data Contracts
Provides high-performance data validation, serialization, and schema definition
for formal verification certificates, cloud inference, tiers, audit logs, and SRE alerts.
"""

import time
import inspect
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ProofCertificateSchema(BaseModel):
    """Pydantic v2 schema for formal proof certificates."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    certificate_id: str = Field(..., description="Unique certificate UUID")
    theorem_or_claim: str = Field(..., description="Verified mathematical theorem or invariant claim")
    status: str = Field(..., description="Verification result status (e.g. PROVEN_VALID, SAT, UNSAT)")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Soundness confidence score [0.0, 1.0]")
    solver_engine: str = Field("z3_smt", description="Verification engine name and version")
    verification_time_ms: float = Field(0.0, ge=0.0, description="Execution time in milliseconds")
    proof_tree_hash: str = Field(..., description="SHA-256 Merkle root hash of proof steps")
    proof_steps: List[str] = Field(default_factory=list, description="Ordered proof steps")
    mathematical_invariants: List[str] = Field(default_factory=list, description="Preserved invariants")
    counterexample: Optional[Dict[str, Any]] = Field(None, description="Counterexample if claim was refuted")
    timestamp: float = Field(default_factory=time.time, description="Creation Unix timestamp")
    merkle_root: Optional[str] = Field(None, description="Merkle root hash")
    merkle_proof_path: Optional[List[Dict[str, str]]] = Field(None, description="Merkle inclusion path")
    merkle_proof: Optional[Dict[str, Any]] = Field(None, description="Merkle inclusion proof dictionary")
    signature_hmac: Optional[str] = Field(None, description="HMAC-SHA256 signature string")
    asymmetric_signature: Optional[str] = Field(None, description="Ed25519 signature in hex format")
    public_key_hex: Optional[str] = Field(None, description="Ed25519 public key in hex format")
    lean4_proof: Optional[str] = Field(None, description="Synthesized Lean 4 theorem script")
    coq_proof: Optional[str] = Field(None, description="Synthesized Coq proof script")
    isabelle_proof: Optional[str] = Field(None, description="Synthesized Isabelle/HOL script")

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return round(v, 4)

    def to_domain(self) -> Any:
        """Convert schema to ProofCertificate domain dataclass."""
        from ..verification.certificate import ProofCertificate
        valid_fields = set(inspect.signature(ProofCertificate.__init__).parameters.keys())
        d = self.model_dump()
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return ProofCertificate(**filtered)

    @classmethod
    def from_domain(cls, cert: Any) -> "ProofCertificateSchema":
        """Build schema from ProofCertificate domain object or dict."""
        if hasattr(cert, "to_dict"):
            data = cert.to_dict()
        elif isinstance(cert, dict):
            data = cert
        else:
            data = cert.__dict__
        return cls.model_validate(data)


class InferenceRequestSchema(BaseModel):
    """Pydantic v2 schema for cloud inference requests."""
    model_config = ConfigDict(extra="ignore")

    prompt: str = Field(..., min_length=1, description="Reasoning prompt or query")
    user_id: Optional[str] = Field(None, description="User or organization identifier")
    model: Optional[str] = Field(None, description="Target frontier model identifier")
    enable_swarm: Optional[bool] = Field(None, description="Whether to dispatch to multi-agent swarm")
    enable_formal_verification: Optional[bool] = Field(None, description="Enforce formal SMT verification")
    constraints: Optional[List[str]] = Field(default_factory=list, description="Mathematical constraints")


class InferenceResponseSchema(BaseModel):
    """Pydantic v2 schema for cloud inference responses."""
    model_config = ConfigDict(extra="ignore")

    response_id: str = Field(..., description="Unique response UUID")
    content: str = Field(..., description="Generated text or proof reasoning")
    tier_used: str = Field(..., description="Subscriber tier under which query was executed")
    model_name: str = Field(..., description="Frontier model used")
    execution_time_ms: float = Field(..., ge=0.0, description="End-to-end execution time in ms")
    tokens_consumed: int = Field(..., ge=0, description="Total tokens consumed in execution")
    tokens_remaining_today: int = Field(..., description="Quota balance remaining")
    time_to_first_token_ms: float = Field(0.0, ge=0.0, description="TTFT latency in ms")
    model_used: str = Field("", description="Effective model identifier")
    proof_certificate: Optional[Dict[str, Any]] = Field(None, description="Attached proof certificate")
    swarm_trace: Optional[Dict[str, Any]] = Field(None, description="Multi-agent swarm execution trace")
    verification_passed: bool = Field(True, description="Whether formal verification succeeded")
    confidence_score: float = Field(0.99, ge=0.0, le=1.0, description="Verification confidence score")
    priority_routing: bool = Field(False, description="Whether VIP low-latency routing was applied")


class TierConfigSchema(BaseModel):
    """Pydantic v2 schema for subscription tiers and feature flags."""
    model_config = ConfigDict(extra="ignore")

    tier: str = Field(..., description="Tier identifier")
    name: str = Field(..., description="Display name")
    daily_token_quota: int = Field(..., ge=0, description="Daily token quota")
    rpm_limit: int = Field(..., ge=1, description="Requests per minute limit")
    rpd_limit: int = Field(..., ge=1, description="Requests per day limit")
    max_concurrency: int = Field(..., ge=1, description="Maximum concurrent streams")
    smt_z3_verification_depth: int = Field(..., ge=1, description="SMT verification search depth")
    enable_swarm_orchestration: bool = Field(False, description="Access to multi-agent swarm")
    monthly_price_usd: float = Field(..., ge=0.0, description="Monthly subscription price")
    yearly_price_usd: float = Field(..., ge=0.0, description="Yearly subscription price")
    allowed_models: List[str] = Field(default_factory=list, description="Permitted frontier models")
    features: List[str] = Field(default_factory=list, description="Enabled platform features")

    @classmethod
    def from_domain(cls, config: Any) -> "TierConfigSchema":
        """Build schema from TierConfig domain object with field mapping."""
        if hasattr(config, "to_dict"):
            data = config.to_dict()
        elif isinstance(config, dict):
            data = dict(config)
        else:
            data = dict(config.__dict__)

        tier_val = data.get("tier") or data.get("tier_id")
        if hasattr(tier_val, "value"):
            tier_val = tier_val.value
        elif tier_val is not None:
            tier_val = str(tier_val)

        mapped = {
            "tier": tier_val or "free",
            "name": data.get("name", "Tier"),
            "daily_token_quota": data.get("daily_token_quota", data.get("daily_token_limit", 0)),
            "rpm_limit": data.get("rpm_limit", data.get("requests_per_minute", 60)),
            "rpd_limit": data.get("rpd_limit", data.get("rpd_limit", 1000)),
            "max_concurrency": data.get("max_concurrency", data.get("concurrent_requests", 1)),
            "smt_z3_verification_depth": data.get("smt_z3_verification_depth", 2),
            "enable_swarm_orchestration": data.get("enable_swarm_orchestration", data.get("swarm_multi_agent", False)),
            "monthly_price_usd": data.get("monthly_price_usd", data.get("price_monthly_usd", 0.0)),
            "yearly_price_usd": data.get("yearly_price_usd", data.get("price_yearly_usd", 0.0)),
            "allowed_models": data.get("allowed_models", data.get("available_models", [])),
            "features": data.get("features", data.get("features_list", [])),
        }
        return cls.model_validate(mapped)


class AuditLogSchema(BaseModel):
    """Pydantic v2 schema for security and operational audit entries."""
    model_config = ConfigDict(extra="ignore")

    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of event")
    event_type: str = Field(..., description="Category of event (e.g. signup, upgrade, verify)")
    user_id: str = Field(..., description="User ID associated with event")
    details: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class AlertRuleSchema(BaseModel):
    """Pydantic v2 schema for SRE metric alerting rules."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=1, description="Unique human-readable alert name")
    metric_key: str = Field(..., min_length=1, description="Target telemetry metric key")
    threshold: float = Field(..., description="Numeric threshold")
    comparison: str = Field("gte", description="Comparison operator: gte, lte, gt, lt, eq")
    is_active: bool = Field(True, description="Whether the rule is actively evaluated")
    cooldown_seconds: float = Field(60.0, ge=0.0, description="Cooldown interval between triggers")

    @field_validator("comparison")
    @classmethod
    def validate_comparison(cls, v: str) -> str:
        valid_ops = {"gte", "lte", "gt", "lt", "eq"}
        if v.lower() not in valid_ops:
            raise ValueError(f"comparison must be one of: {valid_ops}")
        return v.lower()


class UsageRecordSchema(BaseModel):
    """Pydantic v2 schema for subscriber quota and token consumption metrics."""
    model_config = ConfigDict(extra="ignore")

    total_tokens_consumed: int = Field(0, ge=0)
    tokens_consumed_today: int = Field(0, ge=0)
    verifications_run: int = Field(0, ge=0)
    swarm_sessions_count: int = Field(0, ge=0)
    last_reset_timestamp: float = Field(default_factory=time.time)
    daily_request_count: int = Field(0, ge=0)
    purchased_tokens_balance: int = Field(0, ge=0)
    total_purchased_tokens: int = Field(0, ge=0)


class InvoiceSchema(BaseModel):
    """Pydantic v2 schema for customer subscription invoices and billing records."""
    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    user_id: str
    tier_id: str
    amount_usd: float = Field(..., ge=0.0)
    billing_cycle: str = Field("monthly")
    payment_method: str = Field("stripe_card")
    status: str = Field("paid")
    discount_applied_usd: float = Field(0.0, ge=0.0)
    promo_code: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApiKeyInfoSchema(BaseModel):
    """Pydantic v2 schema for user API key registry entries."""
    model_config = ConfigDict(extra="ignore")

    key: str = ""
    key_id: str = ""
    key_prefix: str = ""
    label: str = "Default API Key"
    name: str = "Default API Key"
    created_at: float = Field(default_factory=time.time)
    last_used_at: Optional[float] = None
    is_active: bool = True
    scopes: List[str] = Field(default_factory=lambda: ["all"])


class WebhookSubscriptionSchema(BaseModel):
    """Pydantic v2 schema for webhook notification configurations."""
    model_config = ConfigDict(extra="ignore")

    webhook_id: str
    user_id: str
    endpoint_url: str = ""
    target_url: str = ""
    events: List[str] = Field(default_factory=lambda: ["invoice.paid", "quota.warning"])
    subscribed_events: List[str] = Field(default_factory=lambda: ["invoice.paid", "quota.warning"])
    is_active: bool = True
    secret_key: str = ""
    created_at: float = Field(default_factory=time.time)


class UserSubscriptionSchema(BaseModel):
    """Pydantic v2 schema for user accounts stored in cloud_subscriptions_db.json."""
    model_config = ConfigDict(extra="ignore")

    user_id: str
    email: str
    name: str = "TruthGPT User"
    tier: str = "free"
    billing_cycle: str = "monthly"
    status: str = "active"
    api_keys: List[str] = Field(default_factory=list)
    subscription_start_date: str = ""
    next_billing_date: str = ""
    usage: UsageRecordSchema = Field(default_factory=UsageRecordSchema)
    invoices: List[InvoiceSchema] = Field(default_factory=list)
    api_key_details: List[ApiKeyInfoSchema] = Field(default_factory=list)
    webhooks: List[WebhookSubscriptionSchema] = Field(default_factory=list)
    custom_limits: Optional[Dict[str, Any]] = None

    def to_domain(self) -> Any:
        from ..billing.models import UserSubscription, UsageRecord, Invoice, ApiKeyInfo, WebhookSubscription
        from ..core.tiers import CloudTier
        tier_enum = CloudTier.FREE
        for t in CloudTier:
            if t.value == self.tier:
                tier_enum = t
                break
        return UserSubscription(
            user_id=self.user_id,
            email=self.email,
            name=self.name,
            tier=tier_enum,
            billing_cycle=self.billing_cycle,
            status=self.status,
            api_keys=self.api_keys,
            subscription_start_date=self.subscription_start_date,
            next_billing_date=self.next_billing_date,
            usage=UsageRecord(**self.usage.model_dump()),
            invoices=[Invoice(**inv.model_dump()) for inv in self.invoices],
            api_key_details=[ApiKeyInfo(**k.model_dump()) for k in self.api_key_details],
            webhooks=[WebhookSubscription(**w.model_dump()) for w in self.webhooks],
            custom_limits=self.custom_limits,
        )

    @classmethod
    def from_domain(cls, user: Any) -> "UserSubscriptionSchema":
        """Build schema from domain UserSubscription object."""
        if hasattr(user, "to_dict"):
            data = user.to_dict()
        elif isinstance(user, dict):
            data = user
        else:
            data = user.__dict__
        return cls.model_validate(data)


def validate_subscription_db(raw_db: Any) -> Dict[str, UserSubscriptionSchema]:
    """Validate and normalize an entire cloud_subscriptions_db dictionary using Pydantic v2.

    Accepts a dictionary, a file path (str or Path), or a raw JSON string.
    """
    import os
    import json

    if isinstance(raw_db, (str, os.PathLike)):
        str_path = str(raw_db)
        if os.path.exists(str_path):
            with open(str_path, encoding="utf-8") as f:
                raw_db = json.load(f)
        else:
            raw_db = json.loads(str_path)

    validated: Dict[str, UserSubscriptionSchema] = {}
    if isinstance(raw_db, dict):
        for uid, udata in raw_db.items():
            if isinstance(udata, dict):
                validated[uid] = UserSubscriptionSchema.model_validate(udata)
    return validated


__all__ = [
    "ProofCertificateSchema",
    "InferenceRequestSchema",
    "InferenceResponseSchema",
    "TierConfigSchema",
    "AuditLogSchema",
    "AlertRuleSchema",
    "UsageRecordSchema",
    "InvoiceSchema",
    "ApiKeyInfoSchema",
    "WebhookSubscriptionSchema",
    "UserSubscriptionSchema",
    "validate_subscription_db",
]
