"""City streets built from Saro's Road Blocks (asphalt, lane markings, sidewalks) and
Saro's Road Signs (stop signs, crossings, traffic lights), with street lamps, palm
planters in the median and benches along the sidewalk.

A street is described by its centre line (an axis-aligned segment), a height and a
cross-section; `paint` lays it on the canvas so buildings can then line up with it.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from . import furn, plants
from .canvas import Canvas

RB = "saros_road_blocks_mod:"
RS = "saros_road_signs_mod:"

# texture_variant names of the plain asphalt block, as seen in the lab showroom
PLAIN = "default"
CENTRE = "road_block_linie_yellow"     # solid yellow centre line
LANE = "straight"                      # white lane divider
CROSSING = "cross"                     # zebra crossing stripe
ARROW = "arrow"


def asphalt(tv=PLAIN, facing="north") -> str:
    return f"{RB}asphalt[facing={facing},texture_variant={tv},variant=default]"


SIDEWALK = f"{RB}sidewalk[variant=default]"
CURB = "minecraft:smooth_stone_slab[type=bottom]"


@dataclass
class Street:
    x1: int
    z1: int
    x2: int
    z2: int
    y: int
    lanes: int = 2            # per direction
    sidewalk: int = 2
    median: int = 0           # planted median width (0 = painted centre line)
    crossings: int = 48       # zebra crossing every n blocks
    paving: tuple = ()        # road surface for pedestrian / dirt streets (no markings); () = asphalt
    walk: str = ""            # sidewalk block; "" = Saro's sidewalk
    lamps: str = "street_lamp"

    @property
    def along_x(self) -> bool:
        return self.z1 == self.z2

    @property
    def half(self) -> int:
        return self.lanes * 3 + (self.median + 1) // 2

    @property
    def width(self) -> int:
        return 2 * (self.half + self.sidewalk) + 1


def _cell(s: Street, t: int, o: int):
    """World (x, z) for a point `t` along the street and offset `o` across it."""
    return (s.x1 + t, s.z1 + o) if s.along_x else (s.x1 + o, s.z1 + t)


def paint(c: Canvas, s: Street, rng: random.Random):
    length = (s.x2 - s.x1) if s.along_x else (s.z2 - s.z1)
    dir_a, dir_b = ("east", "west") if s.along_x else ("south", "north")
    mh = (s.median + 1) // 2
    for t in range(0, length + 1):
        for o in range(-s.half - s.sidewalk, s.half + s.sidewalk + 1):
            x, z = _cell(s, t, o)
            if not c.inside(x, z):
                continue
            a = abs(o)
            i, j = z - c.z0, x - c.x0
            c.height[i, j] = s.y
            if c.water[i, j] > s.y:
                c.water[i, j] = -64
            if a > s.half:                                          # sidewalk
                state = s.walk or SIDEWALK
            elif s.paving:                                          # pedestrian or dirt street
                state = s.paving[(t * 7 + o * 13 + rng.randrange(3)) % len(s.paving)]
            elif s.median and a < mh:                               # planted median
                state = "minecraft:grass_block" if a < mh - 1 or s.median < 3 else "minecraft:smooth_stone"
            elif not s.median and o == 0:
                state = asphalt(CENTRE, dir_a)
            else:
                lane_edge = (a - mh) % 3 == 0 and a != mh and a < s.half
                crossing = s.crossings and t % s.crossings in (0, 1, 2, 3)
                if crossing:
                    state = asphalt(CROSSING, dir_a)
                elif lane_edge and t % 4 < 2:
                    state = asphalt(LANE, dir_a)
                else:
                    state = asphalt(PLAIN, dir_a if o > 0 else dir_b)
            c.top[i, j] = c.sid(state)
    # median palms, lamps and benches
    for t in range(6, length - 3, 12):
        if s.median >= 3:
            x, z = _cell(s, t, 0)
            plants.palm(c, x, s.y, z, rng, furn.piece("palm_log"), furn.piece("palm_leaves"))
        for side in (-1, 1):
            x, z = _cell(s, t, side * (s.half + 1))
            furn.place_tall(c, x, s.y + 1, z, s.lamps)
        if t % 24 == 6:
            for side in (-1, 1):
                x, z = _cell(s, t + 4, side * (s.half + s.sidewalk))
                c.set(x, s.y + 1, z, furn.piece("bench", _face_in(s, side)))
    # street trees in pits along wide sidewalks: palms and flowering plumerias, between the lamps
    if s.sidewalk >= 3:
        for t in range(12, length - 5, 12):
            for side in (-1, 1):
                x, z = _cell(s, t, side * (s.half + 2))
                if not c.inside(x, z) or c.get(x, s.y + 1, z) != "minecraft:air":
                    continue
                i, j = z - c.z0, x - c.x0
                c.top[i, j] = c.sid("minecraft:grass_block")
                if (t // 12 + (side > 0)) % 2:
                    plants.palm(c, x, s.y, z, rng, tall=rng.randint(6, 8))
                else:
                    plumeria(c, x, s.y, z, rng)
                for d in (-1, 1):
                    xx, zz = _cell(s, t + d, side * (s.half + 2))
                    if c.inside(xx, zz) and c.get(xx, s.y + 1, zz) == "minecraft:air":
                        c.set(xx, s.y + 1, zz, rng.choice(["minecraft:flowering_azalea_leaves[persistent=true]",
                                                            "minecraft:azalea_leaves[persistent=true]"]))


def plumeria(c: Canvas, x, y, z, rng: random.Random):
    """A small frangipani: a short forked grey trunk under a flat crown of flowering leaves."""
    h = rng.randint(3, 4)
    for k in range(1, h + 1):
        c.set(x, y + k, z, "minecraft:birch_log[axis=y]" if k < h else "minecraft:birch_wood[axis=y]")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in (0, 1):
                d = abs(dx) + abs(dz) + dy
                if d <= 3 - dy and not (abs(dx) == 2 and abs(dz) == 2) and c.get(x + dx, y + h + dy, z + dz) == "minecraft:air":
                    c.set(x + dx, y + h + dy, z + dz, "minecraft:flowering_azalea_leaves[persistent=true]"
                          if rng.random() < 0.6 else "minecraft:azalea_leaves[persistent=true]")


def junctions(c: Canvas, streets: list, rng: random.Random):
    """Traffic lights where two main streets cross, stop signs where a side street meets one."""
    for a in streets:
        if not a.along_x or a.paving:
            continue
        for b in streets:
            if b.along_x or b.paving:
                continue
            if not (min(a.x1, a.x2) < b.x1 < max(a.x1, a.x2) and min(b.z1, b.z2) <= a.z1 <= max(b.z1, b.z2)):
                continue
            x, z = b.x1, a.z1
            lights = a.lanes >= 2 or b.lanes >= 2
            for sx, sz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                cx, cz = x + sx * (b.half + 1), z + sz * (a.half + 1)
                if not c.inside(cx, cz) or c.get(cx, a.y + 1, cz) != "minecraft:air":
                    continue
                face = "north" if sz < 0 else "south"      # toward traffic coming along the side street
                c.set(cx, a.y + 1, cz, RS + "pfosten")
                if lights:
                    c.set(cx, a.y + 2, cz, RS + "pfosten")
                    c.set(cx, a.y + 3, cz, f"{RS}trafficlight[facing={face},light_state={rng.choice(['green', 'red'])}]")
                else:
                    c.set(cx, a.y + 2, cz, f"{RS}stopp_schild[facing={face}]")


def _face_in(s: Street, side: int) -> str:
    if s.along_x:
        return "south" if side < 0 else "north"
    return "east" if side < 0 else "west"


def front(s: Street, side: int) -> int:
    """Offset of the first building row on one side (just past the sidewalk)."""
    return side * (s.half + s.sidewalk + 1)
