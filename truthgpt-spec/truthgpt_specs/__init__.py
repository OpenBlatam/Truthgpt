"""
TruthGPT Specification Reference Implementation Package.

This package provides executable reference models, state transition logic,
Merkle proof verifiers, SSZ encoders, and optimization kernels adhering
strictly to the TruthGPT Optimization Core formal specifications.
"""

__version__ = "1.0.0"

from . import phase0
from . import altair
from . import bellatrix
from . import capella
from . import deneb
from . import electra
from . import gloas
from . import merkle
from . import ssz

__all__ = [
    "phase0",
    "altair",
    "bellatrix",
    "capella",
    "deneb",
    "electra",
    "gloas",
    "merkle",
    "ssz",
]
