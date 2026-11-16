"""
TruthGPT Extended Specifications Test Suite.

Validates reference implementations of Altair, Bellatrix, Capella, Deneb,
Electra, Gloas KV Cache, Merkle Proofs, and SimpleSerialize (SSZ).
"""

import pytest
import torch
import numpy as np
from dataclasses import dataclass

from truthgpt_specs.altair import AltairConfig, AltairOptimizer
from truthgpt_specs.bellatrix import BellatrixConfig, BellatrixOptimizer
from truthgpt_specs.capella import CapellaConfig, CapellaOptimizer
from truthgpt_specs.deneb import DenebQuantumConfig, DenebQuantumRouter
from truthgpt_specs.electra import ElectraProductionConfig, ElectraHealthMonitor
from truthgpt_specs.gloas import GloasKVCacheConfig, GloasKVCache
from truthgpt_specs.merkle import MerkleTree, MerkleConfig
from truthgpt_specs.ssz import ssz_encode, deserialize_uint32, deserialize_float32


class TestAltairSpec:
    """Test suite for Altair Hyper-Speed specifications."""

    def test_altair_optimizer(self):
        config = AltairConfig(enable_lightning_mode=True, enable_zero_copy=True)
        optimizer = AltairOptimizer(config)
        linear = torch.nn.Linear(32, 32)
        optimized = optimizer.optimize_latency(linear)
        assert optimized is not None
        
        sample = torch.randn(2, 32)
        dispatched = optimizer.dispatch_fast_path(sample)
        assert dispatched.shape == sample.shape


class TestBellatrixSpec:
    """Test suite for Bellatrix Ultra-Optimization specifications."""

    def test_bellatrix_optimizer(self):
        config = BellatrixConfig(enable_fusion=True, enable_zero_copy=True)
        optimizer = BellatrixOptimizer(config)
        linear = torch.nn.Linear(16, 16)
        compiled = optimizer.compile_model(linear)
        assert compiled is not None


class TestCapellaSpec:
    """Test suite for Capella Enhanced AI specifications."""

    def test_capella_action_selection(self):
        config = CapellaConfig(state_size=64, action_size=4)
        optimizer = CapellaOptimizer(config)
        state = np.array([0.1, 0.9, 0.4, 0.2])
        action = optimizer.select_action(state)
        assert action == 1


class TestDenebSpec:
    """Test suite for Deneb Quantum-AI specifications."""

    def test_quantum_router(self):
        config = DenebQuantumConfig(num_qubits=4)
        router = DenebQuantumRouter(config)
        experts = router.route_experts(num_experts=3)
        assert len(experts) == 3


class TestElectraSpec:
    """Test suite for Electra Production-Ready specifications."""

    def test_health_monitor(self):
        config = ElectraProductionConfig()
        monitor = ElectraHealthMonitor(config)
        health = monitor.check_health()
        assert health["status"] == "healthy"
        assert health["production_mode"] == "production"


class TestGloasKVCacheSpec:
    """Test suite for Gloas Ultra-Efficient K/V Cache specifications."""

    def test_kv_cache_operations(self):
        config = GloasKVCacheConfig(max_cache_size=2)
        cache = GloasKVCache(config)
        
        k1, v1 = torch.randn(2, 64), torch.randn(2, 64)
        k2, v2 = torch.randn(2, 64), torch.randn(2, 64)
        k3, v3 = torch.randn(2, 64), torch.randn(2, 64)
        
        cache.put("seq_1", k1, v1)
        cache.put("seq_2", k2, v2)
        assert cache.size() == 2
        
        # Test eviction boundary
        cache.put("seq_3", k3, v3)
        assert cache.size() == 2
        assert cache.get("seq_1") is None
        assert cache.get("seq_3") is not None


class TestMerkleProofsSpec:
    """Test suite for Merkle Proof specifications."""

    def test_merkle_tree_and_proof_verification(self):
        leaves = [b"model_weights_l1", b"model_weights_l2", b"optimizer_state", b"eval_metrics"]
        tree = MerkleTree(leaves)
        root = tree.root
        assert root is not None
        assert len(root) == 32  # SHA-256 length

        # Test proof for leaf 2
        proof = tree.generate_proof(2)
        assert proof.leaf_hash == leaves[2]
        assert proof.root_hash == root
        assert MerkleTree.verify_proof(proof) is True

        # Test tampering detection
        tampered_proof = proof
        tampered_proof.leaf_hash = b"tampered_weights"
        assert MerkleTree.verify_proof(tampered_proof) is False


class TestSSZSpec:
    """Test suite for SimpleSerialize (SSZ) specifications."""

    def test_ssz_primitive_and_dataclass_encoding(self):
        @dataclass
        class MockModelSpec:
            d_model: int
            learning_rate: float
            is_active: bool
            name: str

        spec = MockModelSpec(d_model=512, learning_rate=0.001, is_active=True, name="TruthGPT-v1")
        encoded = ssz_encode(spec)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

        # Verify deterministic round-trip for primitive uint32
        val = 4096
        encoded_val = ssz_encode(val)
        decoded_val = deserialize_uint32(encoded_val)
        assert decoded_val == val
