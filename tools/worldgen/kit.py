"""Building kit: local-coordinate builders with rotation, shapes and furniture.

Local frame (as seen standing outside, facing the building's front):
  u -> to the right, v -> up, w -> into the building (w=0 is the front wall).
`facing` is the compass direction the front faces (the way you walk out).
Block states are written for a south-facing building and rotated.
"""
from __future__ import annotations

import math
import re

from .canvas import Canvas, parse_state

DIRS = ["north", "east", "south", "west"]
TURNS = {"south": 0, "west": 1, "north": 2, "east": 3}
FRAME = {  # right vector, back vector (world dx, dz)
    "south": ((1, 0), (0, -1)),
    "west": ((0, 1), (1, 0)),
    "north": ((-1, 0), (0, 1)),
    "east": ((0, -1), (-1, 0)),
}
CONNECTS = re.compile(r"(_fence$|_pane$|^minecraft:glass_pane$|_wall$|iron_bars$)")


def rotate_state(state: str, k: int) -> str:
    if k % 4 == 0:
        return state
    name, props = parse_state(state)
    new = dict(props)
    for key in ("facing",):
        if key in props and props[key] in DIRS:
            new[key] = DIRS[(DIRS.index(props[key]) + k) % 4]
    if "axis" in props and k % 2:
        new["axis"] = {"x": "z", "z": "x"}.get(props["axis"], props["axis"])
    if "rotation" in props:
        new["rotation"] = str((int(props["rotation"]) + 4 * k) % 16)
    if any(d in props for d in DIRS):
        for d in DIRS:
            new.pop(d, None)
        for d in DIRS:
            src = DIRS[(DIRS.index(d) - k) % 4]
            if src in props:
                new[d] = props[src]
    body = ",".join(f"{a}={b}" for a, b in new.items())
    return f"{name}[{body}]" if body else name


class B:
    def __init__(self, c: Canvas, x: int, y: int, z: int, facing: str = "south"):
        self.c, self.x, self.y, self.z, self.facing = c, x, y, z, facing
        self.k = TURNS[facing]
        self.R, self.Bk = FRAME[facing]

    def world(self, u, v, w):
        return (self.x + u * self.R[0] + w * self.Bk[0], self.y + v, self.z + u * self.R[1] + w * self.Bk[1])

    def dir(self, local: str) -> str:
        """Compass direction for a local direction: front/back/left/right."""
        base = {"front": "south", "back": "north", "left": "west", "right": "east"}[local]
        return DIRS[(DIRS.index(base) + self.k) % 4]

    def set(self, u, v, w, state: str, nbt=None):
        x, y, z = self.world(u, v, w)
        st = rotate_state(state, self.k)
        self.c.set(x, y, z, st, nbt)
        if CONNECTS.search(st.split("[")[0]):
            CONNECTABLE.append((x, y, z))

    def get(self, u, v, w) -> str:
        return self.c.get(*self.world(u, v, w))

    def box(self, u1, v1, w1, u2, v2, w2, state, hollow=False, walls_only=False):
        for u in range(min(u1, u2), max(u1, u2) + 1):
            for v in range(min(v1, v2), max(v1, v2) + 1):
                for w in range(min(w1, w2), max(w1, w2) + 1):
                    edge_u = u in (u1, u2)
                    edge_w = w in (w1, w2)
                    edge_v = v in (v1, v2)
                    if walls_only and not (edge_u or edge_w):
                        continue
                    if hollow and not (edge_u or edge_w or edge_v):
                        continue
                    self.set(u, v, w, state)

    def clear(self, u1, v1, w1, u2, v2, w2):
        self.box(u1, v1, w1, u2, v2, w2, "minecraft:air")

    def sign(self, u, v, w, lines, wood="oak", wall=True, glow=False):
        x, y, z = self.world(u, v, w)
        if wall:
            self.c.sign(x, y, z, lines, wood=wood, wall_facing=self.dir("front"), glow=glow)
        else:
            self.c.sign(x, y, z, lines, wood=wood, rotation=(8 + 4 * self.k) % 16, glow=glow)

    def door(self, u, v, w, kind="oak", hinge="left", facing="south"):
        self.set(u, v, w, f"minecraft:{kind}_door[facing={facing},half=lower,hinge={hinge},open=false]")
        self.set(u, v + 1, w, f"minecraft:{kind}_door[facing={facing},half=upper,hinge={hinge},open=false]")

    def bed(self, u, v, w, color="red", facing="north"):
        # foot at (u, w), head one block "back" in the given local facing
        du, dw = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}[facing]
        self.set(u, v, w, f"minecraft:{color}_bed[facing={facing},part=foot]")
        self.set(u + du, v, w + dw, f"minecraft:{color}_bed[facing={facing},part=head]")

    def foundation(self, u1, w1, u2, w2, state="minecraft:stone_bricks", depth=12):
        """Fill down from the floor to the terrain so nothing floats."""
        for u in range(min(u1, u2), max(u1, u2) + 1):
            for w in range(min(w1, w2), max(w1, w2) + 1):
                x, y, z = self.world(u, 0, w)
                ground = self.c.surface(x, z) if self.c.inside(x, z) else y
                for yy in range(y - 1, max(ground, y - depth) - 1, -1):
                    self.c.set(x, yy, z, state)
                for yy in range(y, y + 1):
                    pass

    def clear_above(self, u1, w1, u2, w2, height=30):
        for u in range(min(u1, u2), max(u1, u2) + 1):
            for w in range(min(w1, w2), max(w1, w2) + 1):
                x, y, z = self.world(u, 0, w)
                for yy in range(y + 1, y + height):
                    if self.c.get(x, yy, z) != "minecraft:air":
                        self.c.set(x, yy, z, "minecraft:air")

    # ------------------------------------------------------------- roofs
    def gable_roof(self, u1, u2, w1, w2, v, stair, slab=None, full=None, overhang=1):
        """Ridge along w; slopes to the left/right."""
        width = u2 - u1 + 1
        half = (width + 1) // 2
        for i in range(half + overhang):
            left, right = u1 - overhang + i, u2 + overhang - i
            if left > right:
                break
            for w in range(w1 - overhang, w2 + overhang + 1):
                if left == right:
                    self.set(left, v + i, w, slab or full or stair)
                else:
                    self.set(left, v + i, w, f"{stair}[facing=east,half=bottom]")
                    self.set(right, v + i, w, f"{stair}[facing=west,half=bottom]")
                    if full and i > 0:
                        for fu in range(left + 1, right):
                            pass
        return v + half

    def hip_roof(self, u1, u2, w1, w2, v, stair, cap):
        i = 0
        a, b, c_, d = u1 - 1, u2 + 1, w1 - 1, w2 + 1
        while a <= b and c_ <= d:
            if a == b or c_ == d:
                for u in range(a, b + 1):
                    for w in range(c_, d + 1):
                        self.set(u, v + i, w, cap)
                break
            for u in range(a, b + 1):
                self.set(u, v + i, c_, f"{stair}[facing=north,half=bottom]")
                self.set(u, v + i, d, f"{stair}[facing=south,half=bottom]")
            for w in range(c_ + 1, d):
                self.set(a, v + i, w, f"{stair}[facing=east,half=bottom]")
                self.set(b, v + i, w, f"{stair}[facing=west,half=bottom]")
            for u in range(a + 1, b):
                for w in range(c_ + 1, d):
                    if (u in (a + 1, b - 1)) or (w in (c_ + 1, d - 1)):
                        self.set(u, v + i, w, cap)
            a, b, c_, d = a + 1, b - 1, c_ + 1, d - 1
            i += 1
        return v + i

    def dome(self, cu, cw, v, r, state, inner=None, half=True):
        ri = int(math.ceil(r))
        for du in range(-ri, ri + 1):
            for dw in range(-ri, ri + 1):
                for dv in range(0, ri + 1):
                    d = math.sqrt(du * du + dv * dv + dw * dw)
                    if r - 1 < d <= r:
                        self.set(cu + du, v + dv, cw + dw, state)
                    elif inner and d <= r - 1:
                        self.set(cu + du, v + dv, cw + dw, inner)

    def cylinder(self, cu, cw, v1, v2, r, state, hollow=True):
        ri = int(math.ceil(r))
        for du in range(-ri, ri + 1):
            for dw in range(-ri, ri + 1):
                d = math.hypot(du, dw)
                if d <= r and (not hollow or d > r - 1.2):
                    for v in range(v1, v2 + 1):
                        self.set(cu + du, v, cw + dw, state)

    def disc(self, cu, cw, v, r, state):
        ri = int(math.ceil(r))
        for du in range(-ri, ri + 1):
            for dw in range(-ri, ri + 1):
                if math.hypot(du, dw) <= r:
                    self.set(cu + du, v, cw + dw, state)


CONNECTABLE: list[tuple[int, int, int]] = []


def connect_all(c: Canvas) -> None:
    """Give fences, panes, bars and walls their neighbour connections."""
    offsets = {"north": (0, -1), "east": (1, 0), "south": (0, 1), "west": (-1, 0)}
    for x, y, z in set(CONNECTABLE):
        state = c.get(x, y, z)
        name, props = parse_state(state)
        if not CONNECTS.search(name):
            continue
        is_wall = name.endswith("_wall")
        for d, (dx, dz) in offsets.items():
            other = c.get(x + dx, y, z + dz)
            oname = other.split("[")[0]
            solid = not any(s in oname for s in ("air", "water", "grass", "flower", "torch", "sign", "door",
                                                  "leaves", "slab", "stairs", "carpet", "button", "lantern",
                                                  "snow", "rail", "fern", "sapling", "tall_", "bush", "vine"))
            connected = bool(CONNECTS.search(oname)) or solid
            if is_wall:
                props[d] = "low" if connected else "none"
            else:
                props[d] = "true" if connected else "false"
        if is_wall:
            props["up"] = "true"
        body = ",".join(f"{k}={v}" for k, v in props.items())
        c.set(x, y, z, f"{name}[{body}]")
