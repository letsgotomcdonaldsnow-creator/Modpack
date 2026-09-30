"""Minimal NBT writer (big-endian, as used by Minecraft Java Edition).

Values are written from plain Python objects with a few typed wrappers:
dict -> Compound, str -> String, bool -> Byte, int -> Int, float -> Double,
list -> List (element type inferred), plus Byte/Short/Long/Float/ByteArray/
IntArray/LongArray for explicit types.
"""
from __future__ import annotations

import struct

import numpy as np


class Byte(int):
    pass


class Short(int):
    pass


class Long(int):
    pass


class Float(float):
    pass


class ByteArray(bytes):
    pass


class IntArray(list):
    pass


class LongArray:
    """Wraps an int64 numpy array (or list of ints)."""

    def __init__(self, values):
        self.values = np.asarray(values, dtype=">i8")


TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE = 0, 1, 2, 3, 4, 5, 6
TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 7, 8, 9, 10, 11, 12


def _tag_type(value) -> int:
    if isinstance(value, bool) or isinstance(value, Byte):
        return TAG_BYTE
    if isinstance(value, Short):
        return TAG_SHORT
    if isinstance(value, Long):
        return TAG_LONG
    if isinstance(value, int):
        return TAG_INT
    if isinstance(value, Float):
        return TAG_FLOAT
    if isinstance(value, float):
        return TAG_DOUBLE
    if isinstance(value, ByteArray):
        return TAG_BYTE_ARRAY
    if isinstance(value, str):
        return TAG_STRING
    if isinstance(value, LongArray):
        return TAG_LONG_ARRAY
    if isinstance(value, IntArray):
        return TAG_INT_ARRAY
    if isinstance(value, list):
        return TAG_LIST
    if isinstance(value, dict):
        return TAG_COMPOUND
    raise TypeError(f"cannot encode {type(value)} as NBT")


def _string(s: str) -> bytes:
    raw = s.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def _payload(value, out: list) -> None:
    t = _tag_type(value)
    if t == TAG_BYTE:
        out.append(struct.pack(">b", int(value)))
    elif t == TAG_SHORT:
        out.append(struct.pack(">h", int(value)))
    elif t == TAG_INT:
        out.append(struct.pack(">i", int(value)))
    elif t == TAG_LONG:
        out.append(struct.pack(">q", int(value)))
    elif t == TAG_FLOAT:
        out.append(struct.pack(">f", float(value)))
    elif t == TAG_DOUBLE:
        out.append(struct.pack(">d", float(value)))
    elif t == TAG_BYTE_ARRAY:
        out.append(struct.pack(">i", len(value)) + bytes(value))
    elif t == TAG_STRING:
        out.append(_string(value))
    elif t == TAG_LONG_ARRAY:
        out.append(struct.pack(">i", len(value.values)) + value.values.tobytes())
    elif t == TAG_INT_ARRAY:
        out.append(struct.pack(">i", len(value)) + np.asarray(value, dtype=">i4").tobytes())
    elif t == TAG_LIST:
        et = _tag_type(value[0]) if value else TAG_END
        out.append(struct.pack(">bi", et, len(value)))
        for v in value:
            _payload(v, out)
    elif t == TAG_COMPOUND:
        for k, v in value.items():
            if v is None:
                continue
            out.append(struct.pack(">b", _tag_type(v)) + _string(k))
            _payload(v, out)
        out.append(b"\x00")


def encode(root: dict, name: str = "") -> bytes:
    out = [struct.pack(">b", TAG_COMPOUND) + _string(name)]
    _payload(root, out)
    return b"".join(out)
