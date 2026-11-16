"""
TruthGPT SimpleSerialize (SSZ) Specification Reference Implementation.

Implements deterministic binary serialization and deserialization for model configs,
tensors, and performance metrics defined in specs/ssz/simple_serialize.md.
"""

from dataclasses import dataclass, fields, is_dataclass
import struct
from typing import Any, Dict, Type


def serialize_uint32(val: int) -> bytes:
    """Serializes 32-bit unsigned integer in little-endian format."""
    return struct.pack("<I", val)


def deserialize_uint32(data: bytes) -> int:
    """Deserializes 32-bit unsigned integer from little-endian format."""
    return struct.unpack("<I", data[:4])[0]


def serialize_float32(val: float) -> bytes:
    """Serializes 32-bit float in little-endian format."""
    return struct.pack("<f", val)


def deserialize_float32(data: bytes) -> float:
    """Deserializes 32-bit float from little-endian format."""
    return struct.unpack("<f", data[:4])[0]


def serialize_bool(val: bool) -> bytes:
    """Serializes boolean as 1-byte integer."""
    return b"\x01" if val else b"\x00"


def deserialize_bool(data: bytes) -> bool:
    """Deserializes boolean from 1-byte integer."""
    return data[0] != 0


def ssz_encode(obj: Any) -> bytes:
    """Encodes a dataclass or basic value into SSZ binary format."""
    if isinstance(obj, bool):
        return serialize_bool(obj)
    if isinstance(obj, int):
        return serialize_uint32(obj)
    if isinstance(obj, float):
        return serialize_float32(obj)
    if isinstance(obj, str):
        encoded = obj.encode("utf-8")
        return serialize_uint32(len(encoded)) + encoded
    if isinstance(obj, bytes):
        return serialize_uint32(len(obj)) + obj
    if is_dataclass(obj):
        buffer = bytearray()
        for f in fields(obj):
            val = getattr(obj, f.name)
            buffer.extend(ssz_encode(val))
        return bytes(buffer)
    raise TypeError(f"Unsupported type for SSZ serialization: {type(obj)}")
