"""
🧪 TruthGPT Cloud - Next-Gen Industrial Libraries Test Suite
Validates deep integrations for:
- psutil: Node hardware & worker process telemetry, Prometheus gauges
- PyJWT: Sovereign JWT session tokens, scope enforcement, and expiration
- networkx: Multi-agent swarm topology graphs, DAG validation, and centrality
- z3-solver & sympy: Formal refutation SMT theorem proving and model extraction
"""

import pytest
from unittest.mock import patch

from truthgpt_cloud.telemetry.system_metrics import (
    get_system_metrics,
    _HAS_PSUTIL,
)
from truthgpt_cloud.telemetry import (
    CloudTelemetryCollector,
    render_system_metrics_panel,
)
from truthgpt_cloud.security.jwt_auth import (
    create_session_jwt,
    verify_session_jwt,
    decode_jwt_unverified,
    _HAS_PYJWT,
)
from truthgpt_cloud.security import (
    cloud_security,
)
from truthgpt_cloud.core.exceptions import AuthenticationError
from truthgpt_cloud.swarm.graph_topology import (
    build_swarm_topology_graph,
    get_topological_reasoning_order,
    detect_deadlocks_and_cycles,
    calculate_agent_influence,
    _HAS_NETWORKX,
)
from truthgpt_cloud.swarm import cloud_swarm
from truthgpt_cloud.verification.smt_engine import (
    Z3TheoremSolver,
    _HAS_Z3,
    _HAS_SYMPY,
)


# ===========================================================================
# 1. PSUTIL HARDWARE & PROCESS TELEMETRY TESTS
# ===========================================================================

class TestPsutilSystemTelemetry:
    """Validate host node and worker process telemetry via psutil."""

    def test_01_psutil_is_active(self):
        assert _HAS_PSUTIL is True, "psutil should be installed in the environment"

    def test_02_get_system_metrics_structure(self):
        metrics = get_system_metrics()
        assert metrics is not None
        assert metrics.get("has_psutil") is True
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "process" in metrics

        # CPU validations
        assert "percent" in metrics["cpu"]
        assert metrics["cpu"]["logical_cores"] >= 1

        # Memory validations
        assert metrics["memory"]["total_bytes"] > 0
        assert metrics["memory"]["used_bytes"] > 0
        assert 0.0 <= metrics["memory"]["percent"] <= 100.0

        # Process validations
        assert metrics["process"]["pid"] > 0
        assert metrics["process"]["threads_count"] >= 1
        assert metrics["process"]["memory_rss_bytes"] > 0

    def test_03_telemetry_collector_includes_system_metrics(self):
        collector = CloudTelemetryCollector()
        cluster_metrics = collector.get_cluster_metrics()
        assert "system_metrics" in cluster_metrics
        assert cluster_metrics["system_metrics"]["has_psutil"] is True

    def test_04_render_system_metrics_panel(self):
        metrics = get_system_metrics()
        panel = render_system_metrics_panel(metrics)
        assert panel is not None

    def test_05_psutil_fallback_when_unavailable(self):
        with patch("truthgpt_cloud.telemetry.system_metrics._HAS_PSUTIL", False):
            metrics = get_system_metrics()
            assert metrics["has_psutil"] is False
            assert "cpu" in metrics
            assert "memory" in metrics


# ===========================================================================
# 2. PYJWT SESSION & ACCESS TOKEN TESTS
# ===========================================================================

class TestPyJWTAuthentication:
    """Validate JWT token generation, cryptographic verification, and RBAC claims."""

    def test_01_pyjwt_is_active(self):
        assert _HAS_PYJWT is True, "PyJWT should be installed in the environment"

    def test_02_create_and_verify_session_jwt(self):
        token = create_session_jwt(
            user_id="usr_ada_lovelace",
            tier="ultra",
            scopes=["inference:run", "proof:verify"],
            expires_in_seconds=1800,
        )
        assert isinstance(token, str)
        assert token.startswith("eyJ")

        # Decode and verify
        payload = verify_session_jwt(token)
        assert payload["sub"] == "usr_ada_lovelace"
        assert payload["tier"] == "ultra"
        assert "proof:verify" in payload["scopes"]
        assert payload["aud"] == "truthgpt:cloud:api"

    def test_03_cloud_security_manager_jwt_integration(self):
        token = cloud_security.create_session_jwt(
            user_id="usr_von_neumann",
            tier="enterprise",
            expires_in_seconds=7200,
        )
        assert isinstance(token, str)

        claims = cloud_security.verify_session_jwt(token)
        assert claims["sub"] == "usr_von_neumann"
        assert claims["tier"] == "enterprise"

        # Check ledger recorded audit block
        ledger = cloud_security.get_audit_ledger(limit=5)
        event_types = [b["event_type"] for b in ledger]
        assert "JWT_TOKEN_ISSUED" in event_types

    def test_04_expired_jwt_raises_authentication_error(self):
        token = create_session_jwt(
            user_id="usr_expired_test",
            tier="pro",
            expires_in_seconds=-10,  # Already expired in the past
        )
        with pytest.raises(AuthenticationError) as exc_info:
            verify_session_jwt(token, verify_exp=True)
        assert "expired" in str(exc_info.value).lower()

    def test_05_tampered_jwt_fails_verification(self):
        token = create_session_jwt(user_id="usr_secure", tier="lite")
        # Corrupt the payload signature segment
        tampered = token[:-6] + "xxxxxx"
        with pytest.raises(AuthenticationError):
            verify_session_jwt(tampered)

    def test_06_unverified_decode(self):
        token = create_session_jwt(user_id="usr_diagnostic", tier="pro")
        claims = decode_jwt_unverified(token)
        assert claims["sub"] == "usr_diagnostic"


# ===========================================================================
# 3. NETWORKX MULTI-AGENT SWARM GRAPH TOPOLOGY TESTS
# ===========================================================================

class TestNetworkXSwarmTopology:
    """Validate Swarm multi-agent coordination as a NetworkX directed graph."""

    def test_01_networkx_is_active(self):
        assert _HAS_NETWORKX is True, "NetworkX should be installed in the environment"

    def test_02_build_hierarchical_dag(self):
        from truthgpt_cloud.swarm.agents import get_default_swarm_nodes
        agents = get_default_swarm_nodes(max_agents=5)
        graph = build_swarm_topology_graph(agents, topology_type="hierarchical")

        assert graph.number_of_nodes() == 5
        assert graph.number_of_edges() > 0

        # Check DAG property
        deadlock = detect_deadlocks_and_cycles(graph)
        assert deadlock["is_acyclic"] is True
        assert deadlock["has_deadlock_risk"] is False

        # Check topological sort
        order = get_topological_reasoning_order(graph)
        assert len(order) == 5
        # Master coordinator should be first in topological ordering
        assert order[0] == agents[0].agent_id

    def test_03_peer_to_peer_mesh_topology(self):
        from truthgpt_cloud.swarm.agents import get_default_swarm_nodes
        agents = get_default_swarm_nodes(max_agents=4)
        graph = build_swarm_topology_graph(agents, topology_type="peer_to_peer")

        # 4 nodes in full directed mesh: 4 * 3 = 12 directed edges
        assert graph.number_of_nodes() == 4
        assert graph.number_of_edges() == 12

        # In a bidirectional mesh, cycles are intentional for continuous debate
        deadlock = detect_deadlocks_and_cycles(graph)
        assert deadlock["is_acyclic"] is False
        assert deadlock["simple_cycles_count"] > 0

    def test_04_agent_influence_centrality(self):
        from truthgpt_cloud.swarm.agents import get_default_swarm_nodes
        agents = get_default_swarm_nodes(max_agents=4)
        graph = build_swarm_topology_graph(agents, topology_type="star")

        influence = calculate_agent_influence(graph)
        assert len(influence) == 4
        # Central hub (index 0) has highest degree centrality
        hub_id = agents[0].agent_id
        assert influence[hub_id] >= max(influence.values())

    def test_05_orchestrator_get_topology_metrics(self):
        metrics = cloud_swarm.get_topology_metrics(topology="hierarchical", max_agents=4)
        assert metrics["has_networkx"] is True
        assert metrics["node_count"] == 4
        assert metrics["is_dag"] is True
        assert "execution_order" in metrics
        assert "agent_influence" in metrics


# ===========================================================================
# 4. Z3 SMT & SYMPY FORMAL THEOREM PROVER TESTS
# ===========================================================================

class TestZ3AndSymPySMTVerification:
    """Validate Z3 SMT refutation solving, model synthesis, and SymPy CAS integration."""

    def test_01_z3_and_sympy_are_active(self):
        assert _HAS_Z3 is True, "z3-solver should be installed"
        assert _HAS_SYMPY is True, "sympy should be installed"

    def test_02_z3_prove_am_gm_inequality(self):
        solver = Z3TheoremSolver()
        res = solver.prove_inequality_real("am_gm_2")
        assert res["status"] == "PROVEN_VALID"
        assert res["is_valid"] is True
        assert res["confidence"] == 1.0
        assert res["counterexample"] is None
        assert "Z3" in res["solver_engine"]

    def test_03_z3_prove_cauchy_schwarz_inequality(self):
        solver = Z3TheoremSolver()
        res = solver.prove_inequality_real("cauchy_schwarz_2")
        assert res["status"] == "PROVEN_VALID"
        assert res["is_valid"] is True
        assert res["confidence"] == 1.0
        assert res["counterexample"] is None

    def test_04_z3_solve_satisfiability_with_model(self):
        import z3
        solver = Z3TheoremSolver()
        # Find satisfying assignment for x^2 + y^2 == 25 and x > 0 and y > 0
        x = z3.Real("x")
        y = z3.Real("y")
        constraints = [x**2 + y**2 == 25, x > 0, y > 0]
        res = solver.solve_satisfiability(constraints)

        assert res["status"] == "SAT"
        assert res["is_sat"] is True
        assert "x" in res["model"]
        assert "y" in res["model"]

    def test_05_sympy_symbolic_simplification_and_expansion(self):
        solver = Z3TheoremSolver()
        # Expand and simplify (a + b)^2 - (a^2 + 2*a*b + b^2) == 0
        res = solver.verify_with_sympy_symbolic("(a + b)**2 - (a**2 + 2*a*b + b**2)")
        assert res["has_sympy"] is True
        assert res["is_zero"] is True
        assert res["simplified"] == "0"
        assert "a" in res["free_symbols"]
        assert "b" in res["free_symbols"]


# ===========================================================================
# 5. FASTAPI NEXT-GEN ENDPOINTS INTEGRATION TESTS
# ===========================================================================

class TestFastAPINextGenEndpoints:
    """Validate FastAPI endpoints for token issuance, telemetry, and swarm graphs."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from truthgpt_cloud_server import app
        return TestClient(app)

    def test_01_issue_token_endpoint(self, client):
        resp = client.post("/api/v1/auth/token", json={
            "user_id": "usr_api_tester",
            "tier": "pro",
            "expires_in_seconds": 1800,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["token_type"] == "Bearer"
        assert "access_token" in data
        assert data["access_token"].startswith("eyJ")

    def test_02_swarm_graph_endpoint(self, client):
        resp = client.get("/api/v1/swarm/graph?topology=hierarchical&max_agents=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["topology"] == "hierarchical"
        assert data["metrics"]["node_count"] == 5
        assert data["metrics"]["is_dag"] is True

    def test_03_telemetry_system_endpoint(self, client):
        resp = client.get("/api/v1/telemetry/system")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "system_metrics" in data
        assert data["system_metrics"]["has_psutil"] is True

    def test_04_authenticated_chat_with_jwt_bearer(self, client):
        # 1. Issue JWT token
        tok_resp = client.post("/api/v1/auth/token", json={
            "user_id": "usr_bearer_tester",
            "tier": "pro",
        })
        token = tok_resp.json()["access_token"]

        # 2. Make authenticated inference chat with Bearer token
        chat_resp = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "prompt": "Verify Cauchy-Schwarz inequality",
                "enable_formal_verification": False,
            }
        )
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert chat_data["success"] is True
