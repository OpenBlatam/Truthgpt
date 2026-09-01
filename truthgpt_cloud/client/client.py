"""
🚀 TruthGPT Cloud - Official Python SDK Client
Enables seamless developer interaction with TruthGPT Cloud services,
tier management, Z3 formal verification, and multi-agent swarm orchestration.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

from ..core.tiers import CloudTier, TierConfig, get_tier_config, get_all_tiers
from ..billing.subscription import subscription_manager, UserSubscription
from ..billing.webhooks import webhook_manager, WebhookSubscription, WebhookEventPayload
from ..routing.router import cloud_router, CloudInferenceResponse
from ..verification.verifier import cloud_verifier, compute_merkle_root, verify_proof_certificate
from ..verification.certificate import ProofCertificate, ContractVerificationResult
from ..verification.merkle import MerkleTree
from ..swarm.orchestrator import cloud_swarm, SwarmExecutionTrace
from ..papers.compiler import cloud_paper_compiler
from ..papers.registry import get_all_papers, get_paper_by_id
from ..telemetry import cloud_telemetry
from ..cache import proof_cache


class TruthGPTCloudClient:
    """
    Developer Client SDK for TruthGPT Cloud.
    Supports both asynchronous and synchronous paradigms across all platform capabilities.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        tier: Optional[Union[str, CloudTier]] = None
    ):
        self.sub_manager = subscription_manager
        self.router = cloud_router
        self.verifier = cloud_verifier
        self.swarm = cloud_swarm
        self.paper_compiler = cloud_paper_compiler
        self.webhooks = webhook_manager
        self.telemetry = cloud_telemetry
        self.cache = proof_cache
        
        # Resolve user
        self.user: Optional[UserSubscription] = None
        if api_key:
            self.user = self.sub_manager.get_user_by_api_key(api_key)
        elif user_id:
            self.user = self.sub_manager.get_user(user_id)
            
        if not self.user:
            # Fallback to default demo user or create with specified tier
            tier_enum = CloudTier(tier.lower()) if (isinstance(tier, str) and tier) else (tier if isinstance(tier, CloudTier) else CloudTier.FREE)
            self.user = self.sub_manager.get_user("usr_default_demo")
            if not self.user:
                self.user = self.sub_manager.register_user(
                    email="developer@truthgpt.ai",
                    name="TruthGPT Developer",
                    tier=tier_enum
                )

        self.api_key = self.user.api_keys[0] if self.user.api_keys else "tgpt_cloud_live_demo"
        self.user_id = self.user.user_id

    def verify_attention(
        self,
        query_shape: List[int],
        key_shape: List[int],
        value_shape: List[int],
        num_heads_q: int = 32,
        num_heads_kv: Optional[int] = None,
        head_dim: int = 128,
        is_causal: bool = True,
        architecture_type: str = "FlashAttention-3"
    ) -> Dict[str, Any]:
        """Formally verify Multi-Head / Grouped-Query Attention invariants."""
        return self.verifier.verify_attention_invariants(
            query_shape=query_shape,
            key_shape=key_shape,
            value_shape=value_shape,
            num_heads_q=num_heads_q,
            num_heads_kv=num_heads_kv,
            head_dim=head_dim,
            is_causal=is_causal,
            architecture_type=architecture_type
        )

    def verify_differential_privacy(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        clipping_bound: float = 1.0,
        noise_multiplier: float = 1.1
    ) -> Dict[str, Any]:
        """Formally verify (epsilon, delta)-Differential Privacy bounds."""
        return self.verifier.verify_differential_privacy(
            epsilon=epsilon,
            delta=delta,
            clipping_bound=clipping_bound,
            noise_multiplier=noise_multiplier
        )

    def export_smt2(self, certificate: ProofCertificate) -> str:
        """Export formal proof certificate into SMT-LIB2 format."""
        return self.verifier.export_to_smt2(certificate)

    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get detailed token consumption and cost analytics for current user."""
        return self.sub_manager.get_usage_analytics(self.user_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    @property
    def tier(self) -> CloudTier:
        user = self.sub_manager.get_user(self.user_id)
        return user.tier if user else CloudTier.FREE

    @property
    def tier_config(self) -> TierConfig:
        return get_tier_config(self.tier)

    # ---------------------------------------------------------------------------
    # 💬 Async & Sync Cloud Inference
    # ---------------------------------------------------------------------------

    async def ask_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        enable_swarm: Optional[bool] = None,
        enable_formal_verification: Optional[bool] = None,
        constraints: Optional[List[str]] = None
    ) -> CloudInferenceResponse:
        """
        Execute an asynchronous reasoning query on TruthGPT Cloud with formal verification.
        """
        return await self.router.route_inference(
            prompt=prompt,
            user_id=self.user_id,
            model_override=model,
            enable_swarm=enable_swarm,
            enable_formal_verification=enable_formal_verification,
            constraints=constraints
        )

    def ask(
        self,
        prompt: str,
        model: Optional[str] = None,
        enable_swarm: Optional[bool] = None,
        enable_formal_verification: Optional[bool] = None,
        constraints: Optional[List[str]] = None
    ) -> CloudInferenceResponse:
        """
        Synchronous wrapper for ask_async.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.ask_async(
                            prompt=prompt,
                            model=model,
                            enable_swarm=enable_swarm,
                            enable_formal_verification=enable_formal_verification,
                            constraints=constraints
                        )
                    ).result()
            return loop.run_until_complete(
                self.ask_async(
                    prompt=prompt,
                    model=model,
                    enable_swarm=enable_swarm,
                    enable_formal_verification=enable_formal_verification,
                    constraints=constraints
                )
            )
        except RuntimeError:
            return asyncio.run(
                self.ask_async(
                    prompt=prompt,
                    model=model,
                    enable_swarm=enable_swarm,
                    enable_formal_verification=enable_formal_verification,
                    constraints=constraints
                )
            )

    async def batch_ask_async(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        enable_formal_verification: bool = True
    ) -> List[CloudInferenceResponse]:
        """
        Execute multiple prompts in parallel on TruthGPT Cloud.
        """
        tasks = [
            self.ask_async(
                prompt=p,
                model=model,
                enable_formal_verification=enable_formal_verification
            )
            for p in prompts
        ]
        return await asyncio.gather(*tasks)

    def batch_ask(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        enable_formal_verification: bool = True
    ) -> List[CloudInferenceResponse]:
        """Synchronous wrapper for batch_ask_async."""
        return asyncio.run(self.batch_ask_async(prompts, model, enable_formal_verification))

    # ---------------------------------------------------------------------------
    # 🌊 Streaming APIs
    # ---------------------------------------------------------------------------

    async def stream_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        enable_formal_verification: Optional[bool] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream reasoning chunks and formal verification metadata asynchronously.
        """
        async for chunk in self.router.stream_inference(
            prompt=prompt,
            user_id=self.user_id,
            model_override=model,
            enable_formal_verification=enable_formal_verification
        ):
            yield chunk

    async def stream_chat(
        self,
        prompt: str,
        model: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Alias for stream_async."""
        async for chunk in self.stream_async(prompt, model):
            yield chunk

    async def ask_stream_async(
        self,
        prompt: str,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Yields text deltas directly as strings for seamless CLI and terminal streaming.
        """
        async for chunk in self.stream_async(prompt, model):
            if chunk.get("type") == "token_chunk":
                yield chunk.get("delta", "")

    def stream(
        self,
        prompt: str,
        model: Optional[str] = None
    ):
        """
        Stream reasoning tokens and formal verification metadata synchronously as an iterator.
        """
        async def _collect():
            chunks = []
            async for c in self.stream_async(prompt, model):
                chunks.append(c)
            return chunks

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return iter(pool.submit(asyncio.run, _collect()).result())
            return iter(loop.run_until_complete(_collect()))
        except RuntimeError:
            return iter(asyncio.run(_collect()))

    # ---------------------------------------------------------------------------
    # 🛡️ Formal Verification API
    # ---------------------------------------------------------------------------

    def verify_claim(
        self,
        claim: str,
        constraints: Optional[List[str]] = None,
        depth_level: Optional[int] = None
    ) -> ProofCertificate:
        """
        Directly verify a mathematical, algorithmic or logical invariant with Z3 SMT in the cloud.
        """
        tier_cfg = self.tier_config
        depth = depth_level if depth_level is not None else tier_cfg.smt_z3_verification_depth
        return self.verifier.verify_expression(
            claim_text=claim,
            constraints=constraints,
            tier_depth=depth
        )

    def verify_expression(
        self,
        claim_text: str,
        constraints: Optional[List[str]] = None,
        tier_depth: Optional[int] = None
    ) -> ProofCertificate:
        """Alias for verify_claim."""
        return self.verify_claim(claim=claim_text, constraints=constraints, depth_level=tier_depth)

    def verify_batch(
        self,
        claims: List[str],
        depth_level: Optional[int] = None
    ) -> List[ProofCertificate]:
        """
        Verify multiple mathematical propositions in batch with Merkle proof trees.
        """
        tier_cfg = self.tier_config
        depth = depth_level if depth_level is not None else tier_cfg.smt_z3_verification_depth
        return self.verifier.verify_batch(claims=claims, tier_depth=depth)

    def verify_certificate(self, certificate: ProofCertificate) -> bool:
        """
        Cryptographically verify that a ProofCertificate is authentic, uncorrupted, and valid.
        """
        return certificate.verify_integrity()

    def verify_contract(
        self,
        preconditions: List[str],
        postconditions: List[str],
        invariants: Optional[List[str]] = None,
        function_name: str = "routine_spec",
        code_snippet: Optional[str] = None
    ) -> ContractVerificationResult:
        """
        Execute Design-by-Contract (DbC) Hoare Triple verification.
        """
        return self.verifier.verify_contract(
            preconditions=preconditions,
            postconditions=postconditions,
            invariants=invariants,
            function_name=function_name,
            code_snippet=code_snippet,
            tier_depth=self.tier_config.smt_z3_verification_depth
        )

    def verify_python_code(
        self,
        code_str: str,
        function_name: Optional[str] = None
    ) -> ContractVerificationResult:
        """Parse Python AST and verify pre/post contracts formally."""
        return self.verifier.verify_python_code(code_str, function_name=function_name, tier_depth=self.tier_config.smt_z3_verification_depth)

    def export_proof_to_lean4(self, certificate: ProofCertificate, theorem_name: Optional[str] = None) -> str:
        """Export theorem proof in Lean 4 formal language."""
        return self.verifier.export_to_lean4(certificate, theorem_name=theorem_name)

    def export_proof_to_coq(self, certificate: ProofCertificate, theorem_name: Optional[str] = None) -> str:
        """Export theorem proof in Coq Rocq formal language."""
        return self.verifier.export_to_coq(certificate, theorem_name=theorem_name)

    def export_proof_to_isabelle(self, certificate: ProofCertificate, theorem_name: Optional[str] = None) -> str:
        """Export theorem proof in Isabelle/HOL formal language."""
        return self.verifier.export_to_isabelle(certificate, theorem_name=theorem_name)

    def export_smt2(self, certificate: ProofCertificate) -> str:
        """Export formal proof in SMT-LIB2 format for independent third-party solvers."""
        return certificate.to_smt2_script()

    def export_jsonld(self, certificate: ProofCertificate) -> Dict[str, Any]:
        """Export verifiable credential in JSON-LD format."""
        return certificate.to_jsonld()

    def verify_merkle_branch(
        self,
        leaf_data: str,
        proof_path: List[Dict[str, str]],
        expected_root: str
    ) -> bool:
        """Cryptographically verify leaf data against Merkle proof branch."""
        return MerkleTree.verify_proof(leaf_data, proof_path, expected_root)

    def verify_merkle_exclusion(
        self,
        tree_leaves: List[str],
        target_claim: str
    ) -> Dict[str, Any]:
        """Formally verify a cryptographic non-membership (exclusion) proof in a Merkle tree."""
        return self.verifier.verify_merkle_exclusion(tree_leaves=tree_leaves, target_claim=target_claim)

    def verify_tensor_shapes(
        self,
        shape_a: List[int],
        shape_b: List[int],
        operation: str = "matmul"
    ) -> Dict[str, Any]:
        """
        Formally verify tensor dimension contracts and compatibility (e.g. matmul, conv, add).
        """
        return self.verifier.verify_tensor_shapes(
            shape_a=shape_a,
            shape_b=shape_b,
            operation=operation
        )

    def verify_attention_invariants(
        self,
        query_shape: List[int],
        key_shape: List[int],
        value_shape: List[int],
        num_heads_q: int = 32,
        num_heads_kv: Optional[int] = None,
        head_dim: int = 128,
        is_causal: bool = True,
        architecture_type: str = "FlashAttention-3"
    ) -> Dict[str, Any]:
        """Formally verify Transformer Attention invariants."""
        return self.verifier.verify_attention_invariants(
            query_shape=query_shape,
            key_shape=key_shape,
            value_shape=value_shape,
            num_heads_q=num_heads_q,
            num_heads_kv=num_heads_kv,
            head_dim=head_dim,
            is_causal=is_causal,
            architecture_type=architecture_type
        )

    def verify_quantization_safety(
        self,
        min_val: float,
        max_val: float,
        quant_format: str = "INT8",
        symmetric: bool = True
    ) -> Dict[str, Any]:
        """Formally verify quantization scale, clipping bounds, and zero-point safety."""
        return self.verifier.verify_quantization_safety(
            min_val=min_val,
            max_val=max_val,
            quant_format=quant_format,
            symmetric=symmetric
        )

    def verify_optimizer_convergence(
        self,
        optimizer_name: str = "AdamW",
        learning_rate: float = 1e-3,
        beta1: float = 0.9,
        beta2: float = 0.999,
        weight_decay: float = 0.01,
        eps: float = 1e-8
    ) -> Dict[str, Any]:
        """Formally verify optimizer convergence and stability bounds."""
        return self.verifier.verify_optimizer_convergence(
            optimizer_name=optimizer_name,
            learning_rate=learning_rate,
            beta1=beta1,
            beta2=beta2,
            weight_decay=weight_decay,
            eps=eps
        )

    def verify_numerical_stability(
        self,
        formula_or_loss: str,
        gradient_clipping_bound: float = 1.0,
        epsilon: float = 1e-8
    ) -> Dict[str, Any]:
        """
        Formally verify numerical stability invariants (vanishing/exploding gradients, underflow/overflow).
        """
        return self.verifier.verify_numerical_stability(
            formula_or_loss=formula_or_loss,
            gradient_clipping_bound=gradient_clipping_bound,
            epsilon=epsilon
        )

    # ---------------------------------------------------------------------------
    # 🐝 Multi-Agent Swarm Execution
    # ---------------------------------------------------------------------------

    async def run_swarm_async(
        self,
        prompt: str,
        max_agents: Optional[int] = None,
        topology: Optional[str] = None
    ) -> SwarmExecutionTrace:
        """
        Execute an autonomous multi-agent swarm research cycle asynchronously.
        """
        tier_cfg = self.tier_config
        num_agents = max_agents if max_agents is not None else tier_cfg.max_swarm_agents
        top = topology or "hierarchical"
        return await self.swarm.execute_swarm_session(
            prompt=prompt,
            user_id=self.user_id,
            max_agents=num_agents,
            depth_level=tier_cfg.smt_z3_verification_depth,
            topology=top
        )

    def run_swarm(
        self,
        prompt: str,
        max_agents: Optional[int] = None,
        topology: Optional[str] = None
    ) -> SwarmExecutionTrace:
        """
        Execute an autonomous multi-agent swarm research cycle synchronously.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, self.run_swarm_async(prompt, max_agents, topology=topology)).result()
            return loop.run_until_complete(self.run_swarm_async(prompt, max_agents, topology=topology))
        except RuntimeError:
            return asyncio.run(self.run_swarm_async(prompt, max_agents, topology=topology))

    # ---------------------------------------------------------------------------
    # 🔬 SOTA Paper Compiler
    # ---------------------------------------------------------------------------

    def compile_paper(self, paper_id: str) -> Dict[str, Any]:
        """Compile SOTA research paper architecture and inject into cloud pipeline."""
        return self.paper_compiler.compile_paper_technique(paper_id, user_tier=self.tier.value)

    def list_papers(self) -> List[Dict[str, Any]]:
        """List curated research papers available in the TruthGPT Cloud Hub."""
        papers_raw = get_all_papers()
        return [p if isinstance(p, dict) else (p.to_dict() if hasattr(p, "to_dict") else asdict(p)) for p in papers_raw]

    # ---------------------------------------------------------------------------
    # 💳 Subscription & Account Management
    # ---------------------------------------------------------------------------

    def get_subscription_status(self) -> Dict[str, Any]:
        """Get live token quota, tier status, and billing metrics."""
        return self.sub_manager.get_user_status_summary(self.user_id)

    def upgrade_tier(
        self,
        target_tier: Union[str, CloudTier],
        billing_cycle: str = "monthly",
        payment_method: str = "stripe_card"
    ) -> Dict[str, Any]:
        """Upgrade subscription tier with checkout simulation."""
        tier_enum = CloudTier(target_tier.lower()) if isinstance(target_tier, str) else target_tier
        return self.sub_manager.upgrade_subscription(
            user_id=self.user_id,
            target_tier=tier_enum,
            billing_cycle=billing_cycle,
            payment_method=payment_method
        )

    def generate_api_key(self, label: str = "Default Key", scopes: Optional[List[str]] = None) -> str:
        """Generate a new dedicated API key."""
        return self.sub_manager.generate_new_api_key(self.user_id, label=label, scopes=scopes)

    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an active API key."""
        return self.sub_manager.revoke_api_key(self.user_id, api_key)

    @staticmethod
    def list_available_tiers() -> List[Dict[str, Any]]:
        """List all subscription tier offerings and pricing matrices."""
        return get_all_tiers()

    # ---------------------------------------------------------------------------
    # 🔔 Webhooks API
    # ---------------------------------------------------------------------------

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List registered webhooks for current user."""
        from dataclasses import asdict
        return [asdict(w) for w in self.webhooks.list_user_webhooks(self.user_id)]

    def register_webhook(
        self,
        target_url: str,
        subscribed_events: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Register a new developer webhook URL."""
        from dataclasses import asdict
        sub = self.webhooks.register_webhook(self.user_id, target_url, subscribed_events)
        return asdict(sub)

    def delete_webhook(self, webhook_id: str) -> bool:
        """Remove a registered webhook."""
        return self.webhooks.delete_webhook(webhook_id)

    def trigger_webhook_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Emit a synthetic webhook event for testing."""
        from dataclasses import asdict
        evt = self.webhooks.emit_event(event_type, self.user_id, data)
        return asdict(evt)

    # ---------------------------------------------------------------------------
    # 🔒 Cryptographic Audit Ledger & Security APIs
    # ---------------------------------------------------------------------------

    def execute_adversarial_debate(
        self,
        topic: str,
        proponent_claim: str,
        adversary_focus: str = "Búsqueda de singularidades y contraejemplos",
        rounds: int = 2
    ) -> Dict[str, Any]:
        """Execute a formal Red Team vs Blue Team adversarial debate session."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.swarm.execute_adversarial_debate(
                            topic=topic,
                            proponent_claim=proponent_claim,
                            adversary_focus=adversary_focus,
                            rounds=rounds,
                            user_id=self.user_id
                        )
                    ).result()
            return loop.run_until_complete(
                self.swarm.execute_adversarial_debate(
                    topic=topic,
                    proponent_claim=proponent_claim,
                    adversary_focus=adversary_focus,
                    rounds=rounds,
                    user_id=self.user_id
                )
            )
        except RuntimeError:
            return asyncio.run(
                self.swarm.execute_adversarial_debate(
                    topic=topic,
                    proponent_claim=proponent_claim,
                    adversary_focus=adversary_focus,
                    rounds=rounds,
                    user_id=self.user_id
                )
            )

    def get_audit_ledger(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent immutable SHA-256 hash-chained audit ledger blocks."""
        from ..security import cloud_security
        return cloud_security.get_audit_ledger(limit=limit)

    def verify_ledger_integrity(self) -> Dict[str, Any]:
        """Verify unbroken cryptographic SHA-256 chain of the audit ledger."""
        from ..security import cloud_security
        return cloud_security.verify_ledger_integrity()

    # ---------------------------------------------------------------------------
    # 📊 Telemetry & Proof Cache APIs
    # ---------------------------------------------------------------------------

    def get_telemetry_metrics(self) -> Dict[str, Any]:
        """Get live cluster telemetry, percentiles and verification soundness rates."""
        return self.telemetry.get_cluster_metrics()

    def get_telemetry_stats(self) -> Dict[str, Any]:
        """Alias for get_telemetry_metrics."""
        return self.get_telemetry_metrics()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get semantic proof cache statistics and compute savings."""
        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """Clear the proof cache."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics combining user quota, telemetry, and proof cache."""
        user = self.sub_manager.get_user(self.user_id)
        quota_data = user.to_dict() if user else {}
        return {
            "tier": self.tier.value,
            "user_id": self.user_id,
            "quota_usage": quota_data.get("usage", {}),
            "cache": self.get_cache_stats(),
            "telemetry": self.get_telemetry_metrics()
        }

    def verify_smt2_script(self, smt2_text: str, timeout_ms: int = 5000) -> Dict[str, Any]:
        """Execute and verify raw SMT-LIB2 script using cloud SMT engine."""
        return self.verifier.verify_smt2_script(smt2_text=smt2_text, timeout_ms=timeout_ms)

    def get_sla_metrics(self) -> Dict[str, Any]:
        """Get real-time SLA metrics and error budget status."""
        return self.telemetry.get_sla_status()

    def export_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate ready-to-import Grafana dashboard JSON."""
        return self.telemetry.generate_grafana_dashboard_json()

    def verify_matrix(self, matrix: List[List[float]], matrix_name: str = "A") -> Dict[str, Any]:
        """Verify linear algebra matrix properties and bounds."""
        return self.verifier.verify_matrix_invariants(matrix, matrix_name=matrix_name)

    def verify_loop(self, loop_condition: str, invariant_claim: str, loop_body_effect: str = "x = x + 1") -> Dict[str, Any]:
        """Verify Hoare Logic loop invariant triple."""
        return self.verifier.verify_loop_invariant(loop_condition, invariant_claim, loop_body_effect)

    async def stream_async(self, prompt: str, model: Optional[str] = None):
        """Stream reasoning chunks and formal certificates asynchronously."""
        async for chunk in self.router.stream_inference(prompt=prompt, user_id=self.user_id, model_override=model):
            yield chunk

    def verify_ode(self, system_matrix: List[List[float]], system_name: str = "ode_system") -> Dict[str, Any]:
        """Verify continuous/discrete dynamical system stability (Hurwitz / Lyapunov / contraction)."""
        return self.verifier.verify_ode_stability(system_matrix=system_matrix, system_name=system_name)

    def export_isabelle(self, certificate: ProofCertificate, theorem_name: Optional[str] = None) -> str:
        """Export theorem proof in Isabelle/HOL formal theory language."""
        return self.verifier.export_to_isabelle(certificate, theorem_name=theorem_name)

    def search_papers(
        self,
        query: str = "",
        category: Optional[str] = None,
        tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search papers in the TruthGPT Cloud Hub."""
        from ..papers.registry import search_papers as _search_papers
        from dataclasses import asdict
        results = _search_papers(query=query, category=category, tier=tier)
        return [asdict(p) for p in results]

    def export_paper_citation(self, paper_id: str, format_type: str = "bibtex") -> str:
        """Export paper citation in BibTeX, APA, or IEEE format."""
        from ..papers.registry import export_bibtex, export_apa, export_ieee
        fmt = format_type.lower()
        if fmt == "apa":
            return export_apa(paper_id)
        elif fmt == "ieee":
            return export_ieee(paper_id)
        return export_bibtex(paper_id)

    def get_health_status(self) -> Dict[str, Any]:
        """Check operational readiness and health of all cloud components."""
        return self.telemetry.get_health_status()

    # Ergonomic aliases
    verify = verify_claim
    verify_code = verify_python_code
    verify_lyapunov = verify_ode
    verify_attention = verify_attention_invariants

    def verify_differential_privacy(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        clipping_bound: float = 1.0,
        noise_multiplier: float = 1.1
    ) -> Dict[str, Any]:
        """Formally verify (epsilon, delta)-Differential Privacy guarantees."""
        return self.verifier.verify_differential_privacy(
            epsilon=epsilon,
            delta=delta,
            clipping_bound=clipping_bound,
            noise_multiplier=noise_multiplier
        )

    def get_usage_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed usage analytics and token economics breakdown."""
        uid = user_id or self.user_id
        return self.sub_manager.get_usage_analytics(uid)

    def get_subscription_status(self) -> Dict[str, Any]:
        """Get current user subscription profile, tier limits and active status."""
        user = self.sub_manager.get_user(self.user_id)
        if user:
            return user.to_dict()
        return {"user_id": self.user_id, "tier": self.tier.value, "status": "active"}

    def compile_paper(self, paper_id: str) -> Dict[str, Any]:
        """Compile SOTA research paper architecture and synthesize kernel."""
        return self.paper_compiler.compile_paper_technique(paper_id=paper_id, user_tier=self.tier.value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


__all__ = ["TruthGPTCloudClient"]


