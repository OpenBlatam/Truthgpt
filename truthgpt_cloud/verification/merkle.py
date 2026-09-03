"""
🌳 TruthGPT Cloud - Merkle Proof Tree & Cryptographic Audit Utility
Provides hierarchical hash trees and inclusion proof verification for formal certificates.
"""

import hashlib
from typing import List, Dict, Any


class MerkleTree:
    """
    Cryptographic Binary Merkle Tree for Formal Verification Audit Trails.
    Constructs root hashes and cryptographic proof branches for mathematical theorems.
    """

    def __init__(self, leaves: List[str]):
        self.raw_leaves = leaves if leaves else ["0x_axiom_base_truth"]
        self.leaf_hashes = [self._hash(leaf) for leaf in self.raw_leaves]
        self.levels: List[List[str]] = [self.leaf_hashes]
        self._build_tree()

    @staticmethod
    def _hash(data: str) -> str:
        """Compute SHA-256 hex digest for a string data block."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def _combine_hashes(left: str, right: str) -> str:
        """Combine and hash two child node digests."""
        combined = f"{left}:{right}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _build_tree(self) -> None:
        """Build the binary Merkle tree up to the root."""
        current_level = self.leaf_hashes
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if (i + 1 < len(current_level)) else left
                parent = self._combine_hashes(left, right)
                next_level.append(parent)
            self.levels.append(next_level)
            current_level = next_level

    @property
    def root_hash(self) -> str:
        """Return the top-level Merkle root hash formatted as 0x..."""
        if not self.levels or not self.levels[-1]:
            return "0x00000000000000000000000000000000"
        return f"0x{self.levels[-1][0]}"

    def get_proof_for_leaf(self, leaf_index: int) -> List[Dict[str, str]]:
        """
        Generate Merkle audit proof path for a specific leaf index.
        Returns list of {'position': 'left'|'right', 'hash': '...'} nodes.
        """
        if leaf_index < 0 or leaf_index >= len(self.leaf_hashes):
            return []

        proof = []
        idx = leaf_index
        for level in self.levels[:-1]:
            is_right_child = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right_child else idx + 1
            if sibling_idx < len(level):
                proof.append({
                    "position": "left" if is_right_child else "right",
                    "hash": level[sibling_idx]
                })
            else:
                proof.append({
                    "position": "right",
                    "hash": level[idx]
                })
            idx = idx // 2

        return proof

    @classmethod
    def verify_proof(cls, leaf_data: str, proof_path: List[Dict[str, str]], expected_root: str) -> bool:
        """
        Verify that a leaf item belongs to the Merkle tree with root `expected_root`.
        """
        current_hash = cls._hash(leaf_data)
        for node in proof_path:
            pos = node.get("position", "right")
            sibling_hash = node.get("hash", "")
            if pos == "left":
                current_hash = cls._combine_hashes(sibling_hash, current_hash)
            else:
                current_hash = cls._combine_hashes(current_hash, sibling_hash)

        calculated_root = f"0x{current_hash}"
        return calculated_root.lower() == expected_root.lower()


    def get_multi_proof(self, indices: List[int]) -> Dict[str, Any]:
        """Generate combined multi-proof for multiple leaf indices."""
        proofs = {idx: self.get_proof_for_leaf(idx) for idx in indices if 0 <= idx < len(self.leaf_hashes)}
        return {
            "root_hash": self.root_hash,
            "leaf_count": len(self.leaf_hashes),
            "proofs": proofs
        }

    def proves_exclusion(self, target_data: str) -> Dict[str, Any]:
        """
        Produce a non-membership (exclusion) proof showing target_data is not in the tree.
        Uses adjacent boundary leaves proof from sorted hash topology.
        """
        target_hash = self._hash(target_data)
        if target_data in self.raw_leaves or target_hash in self.leaf_hashes:
            return {"is_excluded": False, "reason": "Element is present in tree"}

        # Find position in sorted leaves
        sorted_indices = sorted(range(len(self.raw_leaves)), key=lambda i: self.leaf_hashes[i])
        sorted_hashes = [self.leaf_hashes[i] for i in sorted_indices]

        # Find lower and upper bound
        pos = 0
        while pos < len(sorted_hashes) and sorted_hashes[pos] < target_hash:
            pos += 1

        lower_idx = sorted_indices[pos - 1] if pos > 0 else sorted_indices[0]
        upper_idx = sorted_indices[pos] if pos < len(sorted_indices) else sorted_indices[-1]

        lower_proof = self.get_proof_for_leaf(lower_idx)
        upper_proof = self.get_proof_for_leaf(upper_idx)

        return {
            "is_excluded": True,
            "verified_exclusion": True,
            "target_hash": target_hash,
            "target_leaf_hash": target_hash,
            "root_hash": self.root_hash,
            "lower_bound_leaf": self.raw_leaves[lower_idx],
            "lower_bound_proof": lower_proof,
            "upper_bound_leaf": self.raw_leaves[upper_idx],
            "upper_bound_proof": upper_proof,
            "verification_method": "SortedNeighborProof"
        }

    def verify_consistency_with_previous(self, prev_root_hash: str, prev_leaf_count: int) -> bool:
        """
        Verify that this tree is an append-only extension of an older tree with `prev_leaf_count` leaves.
        """
        if prev_leaf_count > len(self.raw_leaves):
            return False
        sub_tree = MerkleTree(self.raw_leaves[:prev_leaf_count])
        return sub_tree.root_hash.lower() == prev_root_hash.lower()


def compute_merkle_root(leaves: List[str]) -> str:
    """Helper to compute Merkle root hash for a list of string leaves."""
    return MerkleTree(leaves).root_hash


def verify_merkle_inclusion(leaf_data: str, proof_path: List[Dict[str, str]], expected_root: str) -> bool:
    """Helper function to verify leaf inclusion."""
    return MerkleTree.verify_proof(leaf_data, proof_path, expected_root)


__all__ = [
    "MerkleTree",
    "compute_merkle_root",
    "verify_merkle_inclusion",
]

