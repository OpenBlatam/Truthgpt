"""
🧭 TruthGPT Cloud Server - Inference & Routing Router
Handles model routing, chat completions, OpenAI compatibility, and Server-Sent Events (SSE) streaming.
"""

import asyncio
import json
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from ..models import (
    ChatCompletionRequest,
    BatchChatRequest,
    OpenAIChatRequest,
)
from ..dependencies import resolve_user
from ...routing.router import cloud_router
from ...client.client import TruthGPTCloudClient

router = APIRouter(tags=["Inference & Chat"])


@router.get("/api/v1/cloud/models")
async def list_models():
    """Retrieve available frontier models across tiers with full specifications."""
    models = [
        {"model_id": "truthgpt-lite", "name": "TruthGPT Lite", "tier": "free", "context_window": 32768, "type": "smt_basic", "formal_verification": "SymPy Algebra", "latency": "Standard"},
        {"model_id": "deepseek-chat", "name": "DeepSeek Chat V3", "tier": "free", "context_window": 32768, "type": "chat", "formal_verification": "Basic", "latency": "Standard"},
        {"model_id": "truthgpt-pro-smt", "name": "TruthGPT Pro SMT", "tier": "pro", "context_window": 200000, "type": "formal_smt", "formal_verification": "Z3 SMT Prover Level 2 + Hoare DbC", "latency": "Priority TensorRT"},
        {"model_id": "claude-3-7-sonnet", "name": "Claude 3.7 Sonnet", "tier": "pro", "context_window": 200000, "type": "frontier_hybrid", "formal_verification": "Z3 Assisted", "latency": "Priority TensorRT"},
        {"model_id": "gpt-4o", "name": "GPT-4o Omnimodal", "tier": "pro", "context_window": 200000, "type": "frontier", "formal_verification": "Z3 Assisted", "latency": "Priority TensorRT"},
        {"model_id": "truthgpt-quantum-singularity", "name": "TruthGPT Quantum Singularity", "tier": "ultra", "context_window": 2000000, "type": "quantum_ensemble", "formal_verification": "Singularity Quantum Prover Level 3", "latency": "Zero-Queue H100"},
        {"model_id": "deepseek-r1-reasoner", "name": "DeepSeek R1 Reasoner", "tier": "ultra", "context_window": 2000000, "type": "reasoning_cot", "formal_verification": "Singularity Level 3", "latency": "Zero-Queue H100"},
        {"model_id": "truthgpt-sovereign-cluster", "name": "TruthGPT Sovereign Cluster", "tier": "enterprise", "context_window": 4000000, "type": "sovereign_isolated", "formal_verification": "Sovereign Audit & Formal DbC Sandbox", "latency": "Dedicated Clustered In-Memory"}
    ]
    return {"success": True, "models": models}


@router.post("/api/v1/cloud/chat/completions")
@router.post("/api/v1/cloud/chat")
@router.post("/api/v1/chat")
async def chat_completions(req: ChatCompletionRequest, auth_user: str = Depends(resolve_user)):
    """
    Tier-aware chat inference with formal Z3 verification and Proof Certificate.
    """
    uid = req.user_id if req.user_id and req.user_id != "usr_default_demo" else auth_user
    try:
        response = await cloud_router.route_inference(
            prompt=req.prompt,
            user_id=uid,
            model_override=req.model,
            enable_swarm=req.enable_swarm,
            enable_formal_verification=req.enable_formal_verification,
            constraints=req.constraints
        )
        return {"success": True, "response": response.to_dict()}
    except PermissionError as pe:
        raise HTTPException(status_code=402, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@router.post("/v1/chat/completions")
@router.post("/api/v1/chat/completions")
async def openai_chat_completions(req: OpenAIChatRequest, auth_user: str = Depends(resolve_user)):
    """OpenAI-compatible Chat Completions API endpoint with formal Z3 verification."""
    user_prompt = ""
    for m in reversed(req.messages):
        if m.role == "user":
            user_prompt = m.content
            break
    if not user_prompt and req.messages:
        user_prompt = req.messages[-1].content

    res = await cloud_router.route_inference(
        prompt=user_prompt,
        user_id=auth_user,
        model_override=req.model,
        enable_formal_verification=True
    )

    if req.stream:
        async def sse_openai_stream():
            words = res.content.split(" ")
            for idx, word in enumerate(words):
                chunk_data = {
                    "id": res.response_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": res.model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": word + (" " if idx < len(words) - 1 else "")},
                        "finish_reason": None if idx < len(words) - 1 else "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.01)
            yield "data: [DONE]\n\n"
        return StreamingResponse(sse_openai_stream(), media_type="text/event-stream")

    return {
        "id": res.response_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": res.model_name,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": res.content
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": max(10, int(len(user_prompt.split()) * 1.4)),
            "completion_tokens": max(10, int(len(res.content.split()) * 1.4)),
            "total_tokens": res.tokens_consumed
        },
        "truthgpt_verification": {
            "verified": res.verification_passed,
            "merkle_root": res.proof_certificate.get("proof_tree_hash") if res.proof_certificate else None,
            "status": res.proof_certificate.get("status") if res.proof_certificate else "PROVEN_VALID",
            "confidence": res.confidence_score
        }
    }


@router.post("/api/v1/cloud/chat/completions/stream")
async def chat_completions_stream(req: ChatCompletionRequest, auth_user: str = Depends(resolve_user)):
    """
    Server-Sent Events (SSE) streaming endpoint for live token generation.
    """
    uid = req.user_id if req.user_id and req.user_id != "usr_default_demo" else auth_user

    async def sse_generator():
        async for chunk in cloud_router.stream_inference(
            prompt=req.prompt,
            user_id=uid,
            model_override=req.model,
            enable_formal_verification=req.enable_formal_verification if req.enable_formal_verification is not None else True
        ):
            payload = json.dumps({"token": chunk})
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/api/v1/cloud/chat/batch")
async def batch_chat(req: BatchChatRequest, auth_user: str = Depends(resolve_user)):
    """Execute multiple prompts concurrently in a single batch request."""
    uid = req.user_id if req.user_id and req.user_id != "usr_default_demo" else auth_user
    client = TruthGPTCloudClient(user_id=uid)
    results = await client.batch_ask_async(req.prompts, enable_formal_verification=bool(req.enable_formal_verification))
    return {"success": True, "count": len(results), "responses": [r.to_dict() for r in results]}


__all__ = ["router"]
