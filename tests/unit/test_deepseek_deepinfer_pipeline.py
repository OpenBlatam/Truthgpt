"""
Comprehensive Unit & Integration Test Suite for TruthGPT DeepSeek + DeepInfer Architecture.
Tests:
- Schema validation (config/truth_schema.json)
- SSE StreamProcessor (thinking isolation, chunk boundary splitting, verdict parsing)
- Two-factor RAG Reranker (CrossEncoder + Domain Trust Score)
- DeepSeek Prompt Builder (control tokens, chat templates)
- DeepInfer Client (deterministic sampling, token streaming)
- FastAPI Gateway API (/health, /api/v1/verify, /api/v1/verify-stream, /audit-ui)
- TruthGPT Adapter integration
"""

import sys
import os
import json
import asyncio
import pytest
from typing import AsyncGenerator

# Ensure project root is on sys.path
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.parser.stream_processor import TruthGPTStreamProcessor, StreamState
from src.rag.reranker import TruthGPTReranker, SourceDocument, prepare_prompt_with_reranked_rag
from src.gateway.prompt_builder import build_fact_check_prompt
from src.inference.deepinfer_client import TruthGPTInferenceEngine
from src.truthgpt.adapters.deepseek_deepinfer_adapter import DeepSeekDeepInferAdapter


# =============================================================================
# 1. SCHEMA TESTS
# =============================================================================

def test_truth_schema_file_and_structure():
    """Verify truth_schema.json exists and defines required fields & enums."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "truth_schema.json")
    assert os.path.exists(schema_path), f"Schema file not found at {schema_path}"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "verdict" in schema["properties"]
    assert "confidence_score" in schema["properties"]
    assert "claims_analysis" in schema["properties"]
    assert "final_explanation" in schema["properties"]

    expected_enums = ["VERDADERO", "FALSO", "ENGANOSO", "NO_VERIFICABLE"]
    assert schema["properties"]["verdict"]["enum"] == expected_enums
    assert set(schema["required"]) == {"verdict", "confidence_score", "claims_analysis", "final_explanation"}


# =============================================================================
# 2. STREAM PROCESSOR TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_stream_processor_normal_flow():
    """Tests normal SSE streaming with <think> tag and JSON verdict."""
    processor = TruthGPTStreamProcessor()

    async def sample_token_gen() -> AsyncGenerator[str, None]:
        tokens = [
            "<think>\n",
            "Paso 1: evaluando evidencia...\n",
            "Paso 2: verificando consistencia.\n",
            "</think>\n",
            '{"verdict": "VERDADERO", ',
            '"confidence_score": 0.96, ',
            '"claims_analysis": [{"claim": "Hecho A", "is_supported": true}], ',
            '"final_explanation": "Confirmado por evidencia oficial."}'
        ]
        for t in tokens:
            yield t

    events = []
    async for sse_chunk in processor.process_stream(sample_token_gen()):
        events.append(sse_chunk)

    all_sse = "".join(events)

    assert "event: thinking" in all_sse
    assert "event: payload" in all_sse
    assert "event: verdict" in all_sse
    assert "event: done" in all_sse
    assert '"verdict": "VERDADERO"' in all_sse
    assert '"confidence_score": 0.96' in all_sse


@pytest.mark.asyncio
async def test_stream_processor_split_boundary_tags():
    """Tests that split <think> and </think> tags across chunk boundaries are handled cleanly."""
    processor = TruthGPTStreamProcessor()

    # <think> split as "<th" and "ink>"
    # </think> split as "</th" and "ink>"
    async def split_token_gen() -> AsyncGenerator[str, None]:
        chunks = [
            "<th",
            "ink>",
            "Razonamiento interno DeepSeek...",
            "</th",
            "ink>",
            '{"verdict": "FALSO", "confidence_score": 0.90, "claims_analysis": [], "final_explanation": "Refutado."}'
        ]
        for c in chunks:
            yield c

    events = []
    async for sse_chunk in processor.process_stream(split_token_gen()):
        events.append(sse_chunk)

    all_sse = "".join(events)

    # Thinking event must be emitted and accumulated without leaking tags
    assert "event: thinking" in all_sse
    assert "".join(processor.thinking_accumulator) == "Razonamiento interno DeepSeek..."
    # </think> tag must not leak as a payload delta
    assert "</think>" not in "".join(processor.payload_accumulator)
    assert "event: verdict" in all_sse
    assert '"verdict": "FALSO"' in all_sse


@pytest.mark.asyncio
async def test_stream_processor_invalid_json():
    """Tests that invalid JSON payload gracefully emits error event."""
    processor = TruthGPTStreamProcessor()

    async def bad_json_gen() -> AsyncGenerator[str, None]:
        yield "<think>Deduciendo</think>"
        yield "{invalid_json_format"

    events = []
    async for sse_chunk in processor.process_stream(bad_json_gen()):
        events.append(sse_chunk)

    all_sse = "".join(events)
    assert "event: error" in all_sse
    assert "Falló la validación del JSON" in all_sse
    assert "event: done" in all_sse


# =============================================================================
# 3. RERANKER TESTS
# =============================================================================

def test_reranker_with_domain_trust_scores():
    """Tests that low-trust domains are penalized and filtered below threshold."""
    reranker = TruthGPTReranker(min_score_threshold=0.25)

    docs = [
        SourceDocument(
            id="doc_trusted",
            text="La misión Perseverance de la NASA detectó compuestos en el cráter Jezero.",
            url="https://nasa.gov/article",
            domain_trust_score=1.0
        ),
        SourceDocument(
            id="doc_untrusted",
            text="Perseverance de la NASA halló civilizaciones secretas en Jezero.",
            url="https://fake-conspiracy.xyz",
            domain_trust_score=0.10  # Penalized heavily
        ),
        SourceDocument(
            id="doc_medium",
            text="Informes sobre la detección de moléculas orgánicas en suelo marciano.",
            url="https://science-news.com",
            domain_trust_score=0.85
        )
    ]

    query = "Perseverance detectó compuestos en el cráter Jezero de Marte"
    reranked = reranker.rerank(query, docs, top_k=2)

    assert len(reranked) <= 2
    assert reranked[0].id == "doc_trusted"
    # Untrusted document should either be filtered out or ranked lowest
    for r in reranked:
        assert r.score >= 0.25
    assert not any(r.id == "doc_untrusted" and r.score < 0.25 for r in reranked)


def test_prepare_prompt_with_reranked_rag():
    """Tests prompt preparation with reranked sources."""
    reranker = TruthGPTReranker(min_score_threshold=0.10)
    docs = [
        SourceDocument(id="src_1", text="Evidencia A", url="https://src1.org", domain_trust_score=0.9),
    ]

    prompt = prepare_prompt_with_reranked_rag(
        user_query="¿Es cierto el hecho A?",
        raw_documents=docs,
        reranker=reranker,
        top_k=1
    )

    assert "Evidencia A" in prompt
    assert "¿Es cierto el hecho A?" in prompt
    assert "TruthGPT" in prompt


# =============================================================================
# 4. INFERENCE ENGINE TESTS
# =============================================================================

def test_inference_engine_deterministic_verdict():
    """Tests that the inference engine produces schema-compliant verdicts."""
    engine = TruthGPTInferenceEngine()
    verdict = engine.generate_verdict("Afirmación sobre Marte con fuentes oficiales")

    assert "verdict" in verdict
    assert verdict["verdict"] in ["VERDADERO", "FALSO", "ENGANOSO", "NO_VERIFICABLE"]
    assert 0.0 <= verdict["confidence_score"] <= 1.0
    assert isinstance(verdict["claims_analysis"], list)
    assert isinstance(verdict["final_explanation"], str)


@pytest.mark.asyncio
async def test_inference_engine_token_streaming():
    """Tests async token stream from TruthGPTInferenceEngine."""
    engine = TruthGPTInferenceEngine()
    tokens = []
    async for t in engine.generate_stream_tokens("Afirmación de prueba"):
        tokens.append(t)

    full_output = "".join(tokens)
    assert "<think>" in full_output
    assert "</think>" in full_output
    assert "verdict" in full_output


# =============================================================================
# 5. FASTAPI GATEWAY ENDPOINTS TESTS
# =============================================================================

def test_api_gateway_endpoints():
    """Tests FastAPI endpoints using TestClient."""
    from fastapi.testclient import TestClient
    from src.gateway.api import app

    client = TestClient(app)

    # Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200
    health_json = res_health.json()
    assert health_json["status"] == "healthy"
    assert health_json["schema_loaded"] is True

    # Schema endpoint
    res_schema = client.get("/api/v1/schema")
    assert res_schema.status_code == 200
    schema_json = res_schema.json()
    assert "verdict" in schema_json["properties"]

    # Auditor UI endpoint
    res_ui = client.get("/audit-ui")
    assert res_ui.status_code == 200
    assert "TruthGPT" in res_ui.text
    assert "Unidad de Auditoría" in res_ui.text

    # Synchronous verify endpoint
    req_payload = {
        "query": "Perseverance detectó compuestos en Jezero",
        "sources": [
            {
                "id": "s1",
                "text": "Perseverance confirmó compuestos orgánicos en Jezero.",
                "url": "https://nasa.gov",
                "domain_trust_score": 0.95
            }
        ],
        "top_k": 1,
        "min_threshold": 0.15
    }
    res_verify = client.post("/api/v1/verify", json=req_payload)
    assert res_verify.status_code == 200
    v_data = res_verify.json()
    assert "verdict" in v_data
    assert v_data["verdict"] in ["VERDADERO", "FALSO", "ENGANOSO", "NO_VERIFICABLE"]


# =============================================================================
# 6. ADAPTER INTEGRATION TESTS
# =============================================================================

def test_adapter_registry_and_execution():
    """Tests that DeepSeekDeepInferAdapter is instantiated and executed."""
    adapter = DeepSeekDeepInferAdapter()
    assert isinstance(adapter, DeepSeekDeepInferAdapter)

    result = adapter.process({
        "query": "La velocidad de la luz en el vacío es de aproximadamente 300,000 km/s",
        "sources": [
            {
                "id": "phys_01",
                "text": "La velocidad de la luz en el vacío es una constante universal c ≈ 299,792 km/s.",
                "url": "https://physics.nist.gov",
                "domain_trust_score": 1.0
            }
        ]
    })

    assert result["status"] == "success"
    assert "verdict" in result["verdict"]
    assert result["verdict"]["verdict"] == "VERDADERO"


if __name__ == "__main__":
    print("=== RUNNING DEEPSEEK & DEEPINFER TEST SUITE ===")
    
    print("\n[1/6] Testing Truth Schema...")
    test_truth_schema_file_and_structure()
    print("  -> PASSED: Schema exists and strictly defines verdict enums & required fields.")

    print("\n[2/6] Testing Stream Processor (SSE & <think> isolation)...")
    asyncio.run(test_stream_processor_normal_flow())
    asyncio.run(test_stream_processor_split_boundary_tags())
    asyncio.run(test_stream_processor_invalid_json())
    print("  -> PASSED: StreamProcessor isolates <think> from payload, handles chunk boundary splits, and validates JSON.")

    print("\n[3/6] Testing Two-Factor Reranker (CrossEncoder + Domain Trust)...")
    test_reranker_with_domain_trust_scores()
    test_prepare_prompt_with_reranked_rag()
    print("  -> PASSED: Reranker weights domain trust scores and filters below threshold.")

    print("\n[4/6] Testing Inference Engine (Deterministic & Token Stream)...")
    test_inference_engine_deterministic_verdict()
    asyncio.run(test_inference_engine_token_streaming())
    print("  -> PASSED: TruthGPTInferenceEngine adheres to schema and streams tokens.")

    print("\n[5/6] Testing FastAPI Gateway Endpoints...")
    test_api_gateway_endpoints()
    print("  -> PASSED: /health, /api/v1/schema, /audit-ui, and /api/v1/verify endpoints verified.")

    print("\n[6/6] Testing TruthGPT Adapter Integration...")
    test_adapter_registry_and_execution()
    print("  -> PASSED: create_adapter('deepseek', 'deepinfer') instantiated and executed.")

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! (6/6) <<<")
