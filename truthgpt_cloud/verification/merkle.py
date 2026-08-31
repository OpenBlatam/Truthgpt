"""
🌳 TruthGPT Cloud - Merkle Proof Tree & Cryptographic Audit Utility
Provides hierarchical hash trees and inclusion proof verification for formal certificates.
"""

import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple


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
                # Sibling was duplicate of current
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
