"""Multiplayer extras baked into the world: named Waystones in every town.

Waystones keeps its registry in data/waystones.dat; each waystone block entity points
at an entry by UUID. We write both, so every town stone already has its game name
("Hau'oli City", "Konikoni City"...) and players unlock them by visiting, as in the game.
"""
from __future__ import annotations

import gzip
import json
import struct
import uuid
from pathlib import Path

from . import nbt
from .canvas import DATA_VERSION, Canvas

NAMESPACE = uuid.UUID("5a1a0a7e-0000-4a1a-8000-000000000007")
WAYSTONES: list[dict] = []


def _ints(u: uuid.UUID) -> nbt.IntArray:
    return nbt.IntArray(list(struct.unpack(">4i", u.bytes)))


def waystone(c: Canvas, x, y, z, name: str, kind="waystones:waystone", facing="south", pad=True) -> None:
    """A two-block waystone standing on the block at y - 1 (on a small paved pad outdoors)."""
    if any(w["name"] == name for w in WAYSTONES):
        name = f"{name} ({sum(1 for w in WAYSTONES if w['name'].startswith(name)) + 1})"
    uid = uuid.uuid5(NAMESPACE, name)
    if pad:
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c.set(x + dx, y - 1, z + dz, "minecraft:polished_andesite" if (dx or dz) else "minecraft:chiseled_stone_bricks")
    c.set(x, y, z, f"{kind}[facing={facing},half=lower]", {"id": "waystones:waystone", "UUID": _ints(uid)})
    c.set(x, y + 1, z, f"{kind}[facing={facing},half=upper]", {"id": "waystones:waystone"})
    WAYSTONES.append({"name": name, "uid": uid, "pos": (x, y, z)})


def write_waystones(world: Path) -> None:
    entries = [{
        "WaystoneUid": _ints(w["uid"]),
        "Type": "waystones:waystone",
        "NameV2": json.dumps({"text": w["name"]}, ensure_ascii=False),
        "World": "minecraft:overworld",
        "Transient": nbt.Byte(0),
        "BlockPos": nbt.IntArray(list(w["pos"])),
        "Origin": "VILLAGE",
        "Visibility": "ACTIVATION",
    } for w in WAYSTONES]
    out = world / "data" / "waystones.dat"
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wb") as f:
        f.write(nbt.encode({"DataVersion": DATA_VERSION, "data": {"Waystones": entries}}))
    print(f"  waystones: {len(entries)} named town stones")


def free_spot(c: Canvas, x, z, radius=24):
    """Nearest dry, flat 3x3 spot around (x, z) with nothing built on it; returns (x, y, z) or None."""
    for r in range(0, radius):
        for dx in range(-r, r + 1):
            for dz in (-r, r) if abs(dx) != r else range(-r, r + 1):
                px, pz = x + dx, z + dz
                if not c.inside(px, pz) or c.is_water(px, pz):
                    continue
                y = c.surface(px, pz)
                ok = True
                for ox in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        qx, qz = px + ox, pz + oz
                        if c.surface(qx, qz) != y or c.is_water(qx, qz) or any(
                                c.get(qx, y + k, qz) != "minecraft:air" for k in (1, 2, 3)):
                            ok = False
                if ok:
                    return px, y + 1, pz
    return None
