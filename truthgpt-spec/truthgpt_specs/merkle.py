"""
TruthGPT Merkle Proofs Specification Reference Implementation.

Implements cryptographic hashing, Merkle tree construction, proof generation,
and verification defined in specs/merkle/merkle_proofs.md.
"""

from dataclasses import dataclass
from typing import List, Optional
import hashlib


@dataclass
class MerkleConfig:
    """Configuration for TruthGPT Merkle trees."""
    hash_function: str = "sha256"
    tree_depth: int = 32
    leaf_size: int = 32


@dataclass
class MerkleProof:
    """Cryptographic proof validating leaf inclusion in Merkle root."""
    leaf_hash: bytes
    proof_path: List[bytes]
    proof_index: List[bool]  # True = leaf on right, False = leaf on left
    root_hash: bytes
    leaf_index: int


class MerkleTree:
    """Merkle tree calculation and verification engine."""

    def __init__(self, leaves: List[bytes], config: Optional[MerkleConfig] = None):
        self.config = config or MerkleConfig()
        self.leaves = leaves if leaves else [self._hash(b"empty")]
        self.levels = [self.leaves]
        self._build_tree()

    def _hash(self, data: bytes) -> bytes:
        return hashlib.sha256(data).digest()

    def _build_tree(self) -> None:
        current = self.leaves
        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                combined = self._hash(left + right)
                next_level.append(combined)
            self.levels.append(next_level)
            current = next_level

    @property
    def root(self) -> bytes:
        """Returns root hash of the Merkle tree."""
        return self.levels[-1][0]

    def generate_proof(self, leaf_index: int) -> MerkleProof:
        """Generates Merkle inclusion proof for a given leaf index."""
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError("Leaf index out of bounds")

        proof_path = []
        proof_index = []
        idx = leaf_index

        for level in self.levels[:-1]:
            is_right = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right else (idx + 1 if idx + 1 < len(level) else idx)
            proof_path.append(level[sibling_idx])
            proof_index.append(is_right)
            idx //= 2

        return MerkleProof(
            leaf_hash=self.leaves[leaf_index],
            proof_path=proof_path,
            proof_index=proof_index,
            root_hash=self.root,
            leaf_index=leaf_index
        )

    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """Verifies whether a Merkle proof reconstructs the canonical root hash."""
        current_hash = proof.leaf_hash
        for sibling, is_right in zip(proof.proof_path, proof.proof_index):
            if is_right:
                current_hash = hashlib.sha256(sibling + current_hash).digest()
            else:
                current_hash = hashlib.sha256(current_hash + sibling).digest()
        return current_hash == proof.root_hash
