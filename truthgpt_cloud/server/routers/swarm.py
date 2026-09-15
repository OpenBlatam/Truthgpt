"""
🐝 TruthGPT Cloud Server - Multi-Agent Swarm Router
Handles swarm execution, live SSE debate streams, adversarial debates, and graph topology visualization.
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse, PlainTextResponse

from ..models import (
    SwarmExecuteRequest,
    SwarmDebateRequest,
)
from ..dependencies import resolve_user
from ...swarm.orchestrator import cloud_swarm
from ...billing.subscription import subscription_manager

router = APIRouter(tags=["Multi-Agent Swarm"])


@router.get("/api/v1/swarm/graph")
async def get_swarm_graph(
    topology: str = Query("hierarchical", description="Swarm topology type: hierarchical, peer_to_peer, star, adversarial"),
    max_agents: int = Query(5, ge=1, le=20, description="Number of agents in topology"),
):
    """Retrieve NetworkX topological graph metrics, DAG properties, and execution dependency ordering."""
    try:
        metrics = cloud_swarm.get_topology_metrics(topology=topology, max_agents=max_agents)
        return {"success": True, "topology": topology, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/api/v1/cloud/swarm/execute")
async def execute_swarm(req: SwarmExecuteRequest, auth_user: str = Depends(resolve_user)):
    """Execute an autonomous multi-agent swarm research round."""
    uid = req.user_id if req.user_id and req.user_id != "usr_default_demo" else auth_user
    try:
        subscription_manager.record_activity(uid, tokens=500, operation="swarm_execution")
    except Exception:
        pass

    try:
        trace = await cloud_swarm.execute_swarm_session(
            prompt=req.prompt,
            user_id=uid,
            max_agents=req.max_agents or 5
        )
        return {"success": True, "trace": trace.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/cloud/swarm/stream")
async def stream_swarm_endpoint(req: SwarmExecuteRequest, auth_user: str = Depends(resolve_user)):
    """Server-Sent Events (SSE) streaming endpoint for live multi-agent swarm reasoning and debate rounds."""
    uid = req.user_id if req.user_id and req.user_id != "usr_default_demo" else auth_user
    try:
        subscription_manager.record_activity(uid, tokens=500, operation="swarm_stream")
    except Exception:
        pass

    async def sse_generator():
        async for event in cloud_swarm.stream_swarm_session(
            prompt=req.prompt,
            user_id=uid,
            max_agents=req.max_agents or 5
        ):
            payload = json.dumps(event)
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.get("/api/v1/cloud/swarm/topologies")
async def list_swarm_topologies():
    """Retrieve available Swarm coordination topologies."""
    topologies = cloud_swarm.list_available_topologies() if hasattr(cloud_swarm, "list_available_topologies") else [
        {"topology_id": "adversarial_debate", "name": "Adversarial Debate & Refutation", "min_agents": 3, "recommended_tier": "pro"},
        {"topology_id": "quantum_consensus", "name": "Quantum Singularity Consensus", "min_agents": 5, "recommended_tier": "ultra"},
        {"topology_id": "hierarchical_audit", "name": "Hierarchical Sovereign Audit", "min_agents": 10, "recommended_tier": "enterprise"}
    ]
    return {"success": True, "topologies": topologies}


@router.post("/api/v1/cloud/swarm/debate")
async def execute_swarm_debate_endpoint(req: SwarmDebateRequest, auth_user: str = Depends(resolve_user)):
    """Execute a Red Team vs Blue Team formal adversarial debate session."""
    uid = req.user_id if req.user_id and req.user_id != "usr_default_demo" else auth_user
    res = await cloud_swarm.execute_adversarial_debate(
        topic=req.topic,
        proponent_claim=req.proponent_claim,
        adversary_focus=req.adversary_focus or "Búsqueda de singularidades y contraejemplos",
        rounds=req.rounds or 2,
        user_id=uid
    )
    return {"success": True, "debate": res}


@router.get("/api/v1/cloud/swarm/{session_id}/mermaid")
async def get_swarm_session_mermaid_endpoint(session_id: str):
    """Retrieve Mermaid diagram for a completed or active swarm execution trace."""
    trace = cloud_swarm.get_session_trace(session_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Swarm trace '{session_id}' not found.")
    return PlainTextResponse(trace.to_mermaid(), media_type="text/plain")


@router.get("/api/v1/cloud/swarm/topologies/{topology_id}/mermaid")
async def get_swarm_topology_mermaid_endpoint(topology_id: str):
    """Generate Mermaid diagram visualizing coordination network for a topology."""
    mermaid_def = cloud_swarm.render_topology_mermaid(topology=topology_id)
    return PlainTextResponse(mermaid_def, media_type="text/plain")


__all__ = ["router"]
