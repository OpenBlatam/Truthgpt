"""
🛡️ TruthGPT Cloud - Client Verification Mixin
Provides formal verification, SMT/Z3 solving, theorem exporting, and domain invariant methods for TruthGPTCloudClient.
"""

from typing import Dict, List, Optional, Any
from ..verification.certificate import ProofCertificate, ContractVerificationResult
from ..verification.merkle import MerkleTree


class ClientVerificationMixin:
    """Mixin encapsulating formal verification and theorem proving client SDK methods."""

    def verify_claim(
        self,
        claim: str,
        constraints: Optional[List[str]] = None,
        depth_level: Optional[int] = None
    ) -> ProofCertificate:
        """Directly verify a mathematical, algorithmic or logical invariant with Z3 SMT in the cloud."""
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
        """Verify multiple mathematical propositions in batch with Merkle proof trees."""
        tier_cfg = self.tier_config
        depth = depth_level if depth_level is not None else tier_cfg.smt_z3_verification_depth
        return self.verifier.verify_batch(claims=claims, tier_depth=depth)

    def verify_certificate(self, certificate: ProofCertificate) -> bool:
        """Cryptographically verify that a ProofCertificate is authentic, uncorrupted, and valid."""
        return certificate.verify_integrity()

    def verify_contract(
        self,
        preconditions: List[str],
        postconditions: List[str],
        invariants: Optional[List[str]] = None,
        function_name: str = "routine_spec",
        code_snippet: Optional[str] = None
    ) -> ContractVerificationResult:
        """Execute Design-by-Contract (DbC) Hoare Triple verification."""
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
        """Formally verify numerical stability invariants (vanishing/exploding gradients, underflow/overflow)."""
        return self.verifier.verify_numerical_stability(
            formula_or_loss=formula_or_loss,
            gradient_clipping_bound=gradient_clipping_bound,
            epsilon=epsilon
        )

    def verify_tensor_shapes(
        self,
        shape_a: List[int],
        shape_b: List[int],
        operation: str = "matmul"
    ) -> Dict[str, Any]:
        """Formally verify tensor dimension contracts and compatibility (e.g. matmul, conv, add)."""
        return self.verifier.verify_tensor_shapes(
            shape_a=shape_a,
            shape_b=shape_b,
            operation=operation
        )

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

    def verify_matrix(self, matrix: List[List[float]], matrix_name: str = "A") -> Dict[str, Any]:
        """Verify linear algebra matrix properties and bounds."""
        return self.verifier.verify_matrix_invariants(matrix, matrix_name=matrix_name)

    def verify_loop(self, loop_condition: str, invariant_claim: str, loop_body_effect: str = "x = x + 1") -> Dict[str, Any]:
        """Verify Hoare Logic loop invariant triple."""
        return self.verifier.verify_loop_invariant(loop_condition, invariant_claim, loop_body_effect)

    def verify_ode(self, system_matrix: List[List[float]], system_name: str = "ode_system") -> Dict[str, Any]:
        """Verify continuous/discrete dynamical system stability (Hurwitz / Lyapunov / contraction)."""
        return self.verifier.verify_ode_stability(system_matrix=system_matrix, system_name=system_name)

    def verify_smt2_script(self, smt2_text: str, timeout_ms: int = 5000) -> Dict[str, Any]:
        """Execute and verify raw SMT-LIB2 script using cloud SMT engine."""
        return self.verifier.verify_smt2_script(smt2_text=smt2_text, timeout_ms=timeout_ms)

    def verify_lora_rank_safety(
        self,
        base_dim: int = 4096,
        rank: int = 16,
        alpha: float = 32.0,
        target_modules: Optional[List[str]] = None,
        max_rank_ratio: float = 0.5,
        min_scaling: float = 0.05,
        max_scaling: float = 16.0,
        d_model: Optional[int] = None,
        num_heads: Optional[int] = None,
        target_norm_bound: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Formally verify Low-Rank Adaptation (LoRA) configuration invariants."""
        # Support alternate signature with d_model / num_heads / target_norm_bound
        effective_dim = d_model if d_model is not None else base_dim
        kwargs: Dict[str, Any] = {
            "base_dim": effective_dim,
            "rank": rank,
            "alpha": alpha,
            "target_modules": target_modules,
            "max_rank_ratio": max_rank_ratio,
            "min_scaling": min_scaling,
            "max_scaling": max_scaling,
        }
        if d_model is not None:
            kwargs["d_model"] = d_model
        if num_heads is not None:
            kwargs["num_heads"] = num_heads
        if target_norm_bound is not None:
            kwargs["target_norm_bound"] = target_norm_bound
        return self.verifier.verify_lora_rank_safety(**kwargs)

    def verify_lora_rank(
        self,
        d_model: int = 4096,
        rank: int = 16,
        alpha: float = 32.0,
        num_heads: int = 32,
        target_norm_bound: float = 2.0,
    ) -> Dict[str, Any]:
        """Formally verify LoRA rank safety and spectral norm delta bounds."""
        return self.verifier.verify_lora_rank_safety(
            d_model=d_model,
            rank=rank,
            alpha=alpha,
            num_heads=num_heads,
            target_norm_bound=target_norm_bound,
        )

    def verify_kv_cache_memory_bound(
        self,
        batch_size: int = 1,
        seq_len: int = 4096,
        num_layers: int = 32,
        num_heads: Optional[int] = None,
        head_dim: int = 128,
        precision_bits: int = 16,
        vram_budget_gb: float = 24.0,
        num_kv_heads: Optional[int] = None,
        precision_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Formally verify Transformer KV-Cache memory footprint bounds against GPU VRAM budget."""
        effective_heads = num_heads if num_heads is not None else (num_kv_heads or 8)
        kwargs: Dict[str, Any] = {
            "batch_size": batch_size,
            "seq_len": seq_len,
            "num_layers": num_layers,
            "num_heads": effective_heads,
            "head_dim": head_dim,
            "precision_bits": precision_bits,
            "vram_budget_gb": vram_budget_gb,
        }
        if num_kv_heads is not None:
            kwargs["num_kv_heads"] = num_kv_heads
        if precision_bytes is not None:
            kwargs["precision_bytes"] = precision_bytes
        return self.verifier.verify_kv_cache_memory_bound(**kwargs)

    def verify_kv_cache_memory(
        self,
        batch_size: int = 1,
        seq_len: int = 4096,
        num_layers: int = 32,
        num_kv_heads: int = 8,
        head_dim: int = 128,
        precision_bytes: int = 2,
        vram_budget_gb: float = 8.0,
    ) -> Dict[str, Any]:
        """Formally verify KV cache VRAM footprint does not exceed budget."""
        return self.verifier.verify_kv_cache_memory_bound(
            batch_size=batch_size,
            seq_len=seq_len,
            num_layers=num_layers,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            precision_bytes=precision_bytes,
            vram_budget_gb=vram_budget_gb,
        )

    def verify_moe_routing(
        self,
        num_experts: int,
        top_k: int,
        tokens_per_batch: int,
        capacity_factor: float = 1.25,
        gating_weights: Optional[List[float]] = None,
        aux_loss_coeff: float = 0.01,
        drop_tokens: bool = False
    ) -> Dict[str, Any]:
        """Formally verify Mixture of Experts (MoE) routing invariants."""
        return self.verifier.verify_moe_routing(
            num_experts=num_experts,
            top_k=top_k,
            tokens_per_batch=tokens_per_batch,
            capacity_factor=capacity_factor,
            gating_weights=gating_weights,
            aux_loss_coeff=aux_loss_coeff,
            drop_tokens=drop_tokens
        )

    def verify_rope_frequencies(
        self,
        head_dim: int,
        max_position_embeddings: int = 8192,
        base_theta: float = 10000.0,
        scaling_factor: float = 1.0,
        scaling_type: str = "linear",
        low_freq_factor: float = 1.0,
        high_freq_factor: float = 4.0
    ) -> Dict[str, Any]:
        """Formally verify Rotary Position Embeddings (RoPE) frequency invariants."""
        return self.verifier.verify_rope_frequencies(
            head_dim=head_dim,
            max_position_embeddings=max_position_embeddings,
            base_theta=base_theta,
            scaling_factor=scaling_factor,
            scaling_type=scaling_type,
            low_freq_factor=low_freq_factor,
            high_freq_factor=high_freq_factor
        )

    def verify_flash_attention_tiling(
        self,
        block_m: int = 128,
        block_n: int = 64,
        head_dim: int = 128,
        is_causal: bool = True,
        precision_bytes: int = 2,
        sram_budget_bytes: int = 227328
    ) -> Dict[str, Any]:
        """Formally verify FlashAttention-2/3 SRAM block tiling invariants."""
        return self.verifier.verify_flash_attention_tiling(
            block_m=block_m,
            block_n=block_n,
            head_dim=head_dim,
            is_causal=is_causal,
            precision_bytes=precision_bytes,
            sram_budget_bytes=sram_budget_bytes
        )

    def verify_microscaling_fp8(
        self,
        format: str = "e4m3",
        block_size: int = 32,
        scale_bias: int = 127,
        values: Optional[List[float]] = None,
        max_dynamic_range_db: float = 96.0
    ) -> Dict[str, Any]:
        """Formally verify Microscaling (MXFP8 / NVFP4) block quantization invariants."""
        return self.verifier.verify_microscaling_fp8(
            format=format,
            block_size=block_size,
            scale_bias=scale_bias,
            values=values,
            max_dynamic_range_db=max_dynamic_range_db
        )

    def verify_spectral_norm(self, matrix: List[List[float]], max_norm: float = 1.0) -> Dict[str, Any]:
        """Formally verify bounded spectral norm sigma_max(W) <= max_norm."""
        return self.verifier.verify_spectral_norm(matrix=matrix, max_norm=max_norm)

    def verify_lipschitz(
        self,
        layer_type: str = "dense",
        weight_spectral_norm: float = 1.0,
        activation: str = "relu",
        target_lipschitz: float = 1.0
    ) -> Dict[str, Any]:
        """Formally verify composite Lipschitz constant of neural network layer."""
        return self.verifier.verify_lipschitz_constant(
            layer_type=layer_type,
            weight_spectral_norm=weight_spectral_norm,
            activation=activation,
            target_lipschitz=target_lipschitz
        )

    def verify_claims_concurrently(self, claims: List[str], max_workers: int = 4) -> List[ProofCertificate]:
        """Verify multiple mathematical claims concurrently using thread pool."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            return list(pool.map(self.verify_claim, claims))

    def export_smt2(self, certificate: ProofCertificate) -> str:
        """Export formal proof certificate into SMT-LIB2 format."""
        return self.verifier.export_to_smt2(certificate)

    def export_jsonld(self, certificate: ProofCertificate) -> Dict[str, Any]:
        """Export verifiable credential in JSON-LD format."""
        return certificate.to_jsonld()

    def export_proof_to_lean4(self, certificate: ProofCertificate, theorem_name: Optional[str] = None) -> str:
        """Export theorem proof in Lean 4 formal language."""
        return self.verifier.export_to_lean4(certificate, theorem_name=theorem_name)

    def export_proof_to_coq(self, certificate: ProofCertificate, theorem_name: Optional[str] = None) -> str:
        """Export theorem proof in Coq Rocq formal language."""
        return self.verifier.export_to_coq(certificate, theorem_name=theorem_name)

    def export_proof_to_isabelle(self, certificate: ProofCertificate, theorem_name: Optional[str] = None) -> str:
        """Export theorem proof in Isabelle/HOL formal language."""
        return self.verifier.export_to_isabelle(certificate, theorem_name=theorem_name)

    def verify_gradient_clipping(
        self,
        grad_norm: float,
        max_norm: float = 1.0
    ) -> Dict[str, Any]:
        """Formally verify gradient clipping bounds and collinear angle preservation."""
        return self.verifier.verify_gradient_clipping_bounds(grad_norm=grad_norm, max_norm=max_norm)

    def verify_loss_monotonicity(
        self,
        loss_sequence: List[float],
        tolerance: float = 0.05,
        strict: bool = False
    ) -> Dict[str, Any]:
        """Formally verify non-increasing loss convergence invariants."""
        return self.verifier.verify_loss_monotonicity(loss_sequence=loss_sequence, tolerance=tolerance, strict=strict)

    def batch_verify_claims(
        self,
        claims: List[str],
        tier_depth: int = 2
    ) -> List[ProofCertificate]:
        """Formally verify multiple mathematical claims synchronously."""
        return self.verifier.verify_batch(claims, tier_depth=tier_depth)

    # Aliases
    verify = verify_claim
    verify_code = verify_python_code
    verify_lyapunov = verify_ode
    verify_attention = verify_attention_invariants
    export_isabelle = export_proof_to_isabelle
    verify_moe = verify_moe_routing
    verify_rope = verify_rope_frequencies
    verify_flash_attention = verify_flash_attention_tiling
    verify_fp8 = verify_microscaling_fp8


__all__ = ["ClientVerificationMixin"]
