"""
🏢 TruthGPT Cloud Server - Enterprise Suite Router
Exposes sovereign cluster orchestration, 99.999% SLA monitoring,
cryptographic audit generation, and multi-tenant organization management.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Query, Request

from ...enterprise.cluster_orchestrator import cluster_orchestrator, NodeRole
from ...enterprise.audit_engine import audit_engine, ComplianceStandard
from ...enterprise.tenant_manager import tenant_manager, TenantRole
from ...enterprise.sla_monitor import sla_monitor
from ..dependencies import require_tier
from ...core.tiers import CloudTier

router = APIRouter(prefix="/v1/enterprise", tags=["Enterprise & Sovereign Cloud"])


# ---------------------------------------------------------------------------
# 📦 Request & Response Schemas
# ---------------------------------------------------------------------------

class NodeHeartbeatRequest(BaseModel):
    node_id: str
    current_load: float = Field(..., ge=0.0, le=1.0)
    active_tasks: int = Field(..., ge=0)


class ComplianceReportRequest(BaseModel):
    tenant_id: str = "org_sovereign_enterprise"
    standard: str = "SOC2_Type_II"  # SOC2_Type_II, EU_AI_Act_High_Risk, HIPAA_Security_Rule


class MerkleProofVerificationRequest(BaseModel):
    proof_leaf_hash: str
    expected_merkle_root: str
    proof_path: List[Dict[str, str]]


class AddTenantMemberRequest(BaseModel):
    email: str
    role: str = "developer"  # org_owner, security_auditor, ml_platform_engineer, developer, read_only_viewer
    scopes: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# 🌐 Cluster Orchestration Endpoints
# ---------------------------------------------------------------------------

@router.get("/cluster/status")
async def get_cluster_status():
    """Returns the real-time health, load, and topology of the Sovereign GPU & SMT Cluster."""
    return cluster_orchestrator.get_cluster_status()


@router.post("/cluster/nodes/heartbeat")
async def node_heartbeat(payload: NodeHeartbeatRequest):
    """Processes worker node heartbeats for GPU and SMT compute instances."""
    ok = cluster_orchestrator.record_heartbeat(
        node_id=payload.node_id,
        current_load=payload.current_load,
        active_tasks=payload.active_tasks
    )
    if not ok:
        raise HTTPException(status_code=404, detail=f"Node {payload.node_id} not found")
    return {"success": True, "node_id": payload.node_id, "status": "acknowledged"}


# ---------------------------------------------------------------------------
# ⏱️ SLA & Error Budget Endpoints
# ---------------------------------------------------------------------------

@router.get("/sla/metrics")
async def get_sla_metrics():
    """Returns 99.999% SLA adherence metrics, latency percentiles (p50/p95/p99) and error budget burn."""
    return sla_monitor.get_uptime_metrics()


# ---------------------------------------------------------------------------
# 🛡️ Enterprise Audit & Compliance Endpoints
# ---------------------------------------------------------------------------

@router.post("/audit/compliance-report")
async def generate_compliance_report(payload: ComplianceReportRequest):
    """Synthesizes a certified compliance report (SOC 2, EU AI Act, HIPAA) with Merkle root seal."""
    try:
        std = ComplianceStandard(payload.standard)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid compliance standard: {payload.standard}")

    report = audit_engine.generate_compliance_report(
        tenant_id=payload.tenant_id,
        standard=std
    )
    return {
        "report_id": report.report_id,
        "tenant_id": report.tenant_id,
        "standard": report.standard.value,
        "generated_at": report.generated_at,
        "merkle_root_seal": report.merkle_root,
        "total_audited_events": report.total_audited_events,
        "chain_integrity_verified": report.integrity_verified,
        "evidence_sections": report.evidence_sections,
        "signature_hex": report.signature_hex,
    }


@router.post("/audit/verify-proof")
async def verify_merkle_proof(payload: MerkleProofVerificationRequest):
    """Independently verifies whether a given inference or certificate is in the immutable Merkle tree."""
    is_valid = audit_engine.verify_merkle_proof(
        proof_leaf_hash=payload.proof_leaf_hash,
        expected_root=payload.expected_merkle_root,
        proof_path=payload.proof_path
    )
    return {
        "is_valid": is_valid,
        "proof_leaf_hash": payload.proof_leaf_hash,
        "expected_merkle_root": payload.expected_merkle_root,
        "verification_result": "VALID_IN_TREE" if is_valid else "INVALID_PROOF"
    }


# ---------------------------------------------------------------------------
# 🏢 Multi-Tenant Management Endpoints
# ---------------------------------------------------------------------------

@router.get("/tenants/{org_id}")
async def get_tenant_details(org_id: str):
    """Returns organization settings, member count, and workspace namespaces."""
    summary = tenant_manager.get_tenant_summary(org_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Organization '{org_id}' not found")
    return summary


@router.post("/tenants/{org_id}/members")
async def add_tenant_member(org_id: str, payload: AddTenantMemberRequest):
    """Adds an enterprise user to an organization workspace with specific role and RBAC scopes."""
    try:
        role_enum = TenantRole(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tenant role: {payload.role}")

    try:
        member = tenant_manager.add_member(
            org_id=org_id,
            email=payload.email,
            role=role_enum,
            scopes=payload.scopes
        )
        return {
            "success": True,
            "user_id": member.user_id,
            "email": member.email,
            "role": member.role.value,
            "allowed_scopes": member.allowed_scopes,
            "joined_at": member.joined_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
