"""Tree and plant templates. Every function places blocks relative to (x, y, z) = ground block."""
from __future__ import annotations

import math
import random

from .canvas import Canvas


def leaves(kind: str) -> str:
    return f"minecraft:{kind}_leaves[persistent=true]"


def log(kind: str, axis: str = "y") -> str:
    return f"minecraft:{kind}_log[axis={axis}]"


def _blob(c: Canvas, x, y, z, r, state, rng, density=0.85):
    ri = int(math.ceil(r))
    for dx in range(-ri, ri + 1):
        for dy in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.sqrt(dx * dx + dy * dy * 1.6 + dz * dz)
                if d <= r and (d < r - 0.8 or rng.random() < density):
                    if c.get(x + dx, y + dy, z + dz) in ("minecraft:air",):
                        c.set(x + dx, y + dy, z + dz, state)


def palm(c: Canvas, x, y, z, rng: random.Random, log_state=None, leaf_state=None):
    """Curved palm with drooping fronds and coconuts (cocoa pods)."""
    h = rng.randint(7, 11)
    lean = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    log_state = log_state or log("jungle")
    leaf_state = leaf_state or leaves("jungle")
    px, pz = x, z
    for i in range(1, h + 1):
        if i in (h // 2, h - 2) and rng.random() < 0.8:
            px += lean[0]
            pz += lean[1]
        c.set(px, y + i, pz, log_state)
    top = y + h
    c.set(px, top + 1, pz, leaf_state)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        length = rng.randint(3, 5) if dx and dz else rng.randint(4, 6)
        for s in range(1, length + 1):
            drop = 0 if s < 3 else (1 if s < 5 else 2)
            c.set(px + dx * s, top + 1 - drop, pz + dz * s, leaf_state)
            if s == 2 and not (dx and dz):
                c.set(px + dx * s, top + 2, pz + dz * s, leaf_state)
    for dx, dz, facing in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
        if rng.random() < 0.6:
            c.set(px + dx, top - 1, pz + dz, f"minecraft:cocoa[age=2,facing={facing}]")


def jungle_tree(c: Canvas, x, y, z, rng: random.Random, big=False):
    kind = "jungle"
    h = rng.randint(14, 22) if big else rng.randint(6, 10)
    w = 2 if big else 1
    for i in range(1, h + 1):
        for ox in range(w):
            for oz in range(w):
                c.set(x + ox, y + i, z + oz, log(kind))
    if big:
        for ox, oz, a in ((-1, 0, "x"), (2, 1, "x"), (0, -1, "z"), (1, 2, "z")):
            c.set(x + ox, y + 1, z + oz, log(kind, a))
    _blob(c, x, y + h, z, 4.5 if big else 3, leaves(kind), rng)
    if big:
        for _ in range(3):
            bx, bz = x + rng.randint(-5, 5), z + rng.randint(-5, 5)
            by = y + rng.randint(h // 2, h - 3)
            _blob(c, bx, by, bz, 2.5, leaves(kind), rng)
    for i in range(2, h - 1, 2):
        if rng.random() < 0.3:
            c.set(x - 1, y + i, z, "minecraft:vine[east=true]")
        if rng.random() < 0.3:
            c.set(x + w, y + i, z, "minecraft:vine[west=true]")


def round_tree(c: Canvas, x, y, z, rng: random.Random, kind="oak"):
    h = rng.randint(4, 7)
    for i in range(1, h + 1):
        c.set(x, y + i, z, log(kind))
    _blob(c, x, y + h, z, rng.uniform(2.3, 3.2), leaves(kind), rng)


def acacia(c: Canvas, x, y, z, rng: random.Random):
    h = rng.randint(5, 7)
    dx, dz = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
    px, pz = x, z
    for i in range(1, h + 1):
        if i > h - 3:
            px += dx
            pz += dz
        c.set(px, y + i, pz, log("acacia"))
    for ox in range(-3, 4):
        for oz in range(-3, 4):
            if abs(ox) + abs(oz) <= 4:
                c.set(px + ox, y + h + 1, pz + oz, leaves("acacia"))
    for ox in range(-1, 2):
        for oz in range(-1, 2):
            c.set(px + ox, y + h + 2, pz + oz, leaves("acacia"))


def spruce(c: Canvas, x, y, z, rng: random.Random, snowy=False):
    h = rng.randint(8, 13)
    for i in range(1, h + 1):
        c.set(x, y + i, z, log("spruce"))
    r = 3
    for i in range(3, h + 2):
        rr = max(0, int(r * (1 - (i - 3) / (h - 1)) + (1 if i % 2 else 0)))
        for ox in range(-rr, rr + 1):
            for oz in range(-rr, rr + 1):
                if abs(ox) + abs(oz) <= rr + (1 if rr > 1 else 0) and (ox or oz or i > h):
                    c.set(x + ox, y + i, z + oz, leaves("spruce"))
                    if snowy and c.get(x + ox, y + i + 1, z + oz) == "minecraft:air" and rng.random() < 0.5:
                        c.set(x + ox, y + i + 1, z + oz, "minecraft:snow[layers=1]")
    c.set(x, y + h + 1, z, leaves("spruce"))


def cherry(c: Canvas, x, y, z, rng: random.Random):
    h = rng.randint(5, 7)
    for i in range(1, h + 1):
        c.set(x, y + i, z, log("cherry"))
    for dx, dz in ((2, 0), (-2, 1), (0, -2)):
        c.set(x + dx // 2, y + h - 1, z + dz // 2, log("cherry", "x" if dx else "z"))
        _blob(c, x + dx, y + h, z + dz, 2.6, leaves("cherry"), rng)
    _blob(c, x, y + h + 1, z, 2.8, leaves("cherry"), rng)


def dark_oak(c: Canvas, x, y, z, rng: random.Random):
    h = rng.randint(6, 9)
    for i in range(1, h + 1):
        for ox in range(2):
            for oz in range(2):
                c.set(x + ox, y + i, z + oz, log("dark_oak"))
    _blob(c, x, y + h, z, 4.2, leaves("dark_oak"), rng)


def bush(c: Canvas, x, y, z, rng: random.Random, kind="oak"):
    c.set(x, y + 1, z, log(kind))
    _blob(c, x, y + 1, z, rng.uniform(1.2, 2.0), leaves(kind), rng, density=0.7)


def cactus(c: Canvas, x, y, z, rng: random.Random):
    for i in range(1, rng.randint(2, 4) + 1):
        c.set(x, y + i, z, "minecraft:cactus")


def boulder(c: Canvas, x, y, z, rng: random.Random, state="minecraft:cobblestone"):
    _blob(c, x, y + 1, z, rng.uniform(1.2, 2.2), state, rng, density=0.9)
    for s in ("minecraft:mossy_cobblestone", "minecraft:andesite"):
        if rng.random() < 0.5:
            c.set(x + rng.randint(-1, 1), y + 2, z + rng.randint(-1, 1), s)
