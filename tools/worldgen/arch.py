"""Architecture kit: styled Alola buildings with real detailing.

A house is assembled from parts the way a builder would do it by hand:
plinth with a bevelled lip, framed walls (corner posts, beams at every floor), mixed
wall textures, window units (glass, sill, lintel, shutters, planter), a proper door with
lamp, a lanai porch with posts and railings, a Macaw's Roofs hip or gable roof with
overhang and ridge, furnished rooms inside, and a landscaped yard outside.

All coordinates are local (see kit.B): u to the right, v up, w into the building,
the front wall is w = 0 and the floor is v = 0.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace

from . import furn
from .canvas import Canvas, parse_state
from .kit import B, rotate_state

# ----------------------------------------------------------- stair shapes

SHAPED: list[tuple[int, int, int]] = []   # stairs / roofs placed this run; fix_shapes() gives them corner shapes
_TURN_CCW = {"north": "west", "west": "south", "south": "east", "east": "north"}
_OFF = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
_OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def _stairish(state: str):
    name, props = parse_state(state)
    if "facing" in props and "shape" in props and props.get("half") in ("bottom", "top"):
        return name, props
    return None


def fix_shapes(c: Canvas) -> None:
    """Vanilla StairBlock shape rules, applied to stairs and Macaw's roof pieces we placed."""
    for x, y, z in set(SHAPED):
        st = _stairish(c.get(x, y, z))
        if not st:
            continue
        name, props = st
        f, half = props["facing"], props["half"]

        def neighbour(d):
            dx, dz = _OFF[d]
            return _stairish(c.get(x + dx, y, z + dz))

        def can_take(d):
            n = neighbour(d)
            return not n or n[1]["facing"] != f or n[1]["half"] != half

        shape = "straight"
        front = neighbour(f)
        if front and front[1]["half"] == half:
            f1 = front[1]["facing"]
            if f1 not in (f, _OPP[f]) and can_take(_OPP[f1]):
                shape = "outer_left" if f1 == _TURN_CCW[f] else "outer_right"
        if shape == "straight":
            back = neighbour(_OPP[f])
            if back and back[1]["half"] == half:
                f2 = back[1]["facing"]
                if f2 not in (f, _OPP[f]) and can_take(f2):
                    shape = "inner_left" if f2 == _TURN_CCW[f] else "inner_right"
        if shape != props["shape"]:
            props["shape"] = shape
            c.set(x, y, z, name + "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]")


class Bld(B):
    """B that remembers stairs/roofs for fix_shapes and resolves furniture pieces."""

    def set(self, u, v, w, state, nbt=None):
        super().set(u, v, w, state, nbt)
        if "shape=" in state:
            SHAPED.append(self.world(u, v, w))

    def piece(self, u, v, w, name, facing="south"):
        self.set(u, v, w, furn.piece(name, facing))


# ----------------------------------------------------------------- styles

@dataclass
class Style:
    name: str
    walls: list                      # [(state, weight)] wall infill mix
    frame: str                       # corner posts (y-axis log or pillar)
    beam: str                        # horizontal beams: a log/wood id without axis, or a plain block
    plinth: str
    plinth_stair: str
    trim_slab: str
    trim_stair: str
    roof: str                        # Macaw's Roofs prefix ("mcwroofs:red_terracotta") or a stairs id
    roof_cap: str                    # block used on flat tops / ridge fallback
    window: str = "minecraft:glass_pane"
    shutter: str | None = "minecraft:oak_trapdoor"
    door: str = "minecraft:oak_door"
    floor: str = "minecraft:oak_planks"
    inner_wall: str = "minecraft:white_terracotta"
    deck: str = "minecraft:spruce_planks"
    post: str = "minecraft:stripped_oak_log[axis=y]"
    rail: str = "minecraft:oak_fence"
    story_h: int = 4
    roof_kind: str = "hip"           # hip | gable | flat
    porch: int = 3                   # porch depth (0 = none)
    raised: int = 0                  # stilts height (Iki Town huts)
    planter: bool = True
    interior: str = "home"


def macaw(prefix: str) -> bool:
    return prefix.startswith("mcwroofs:")


ROOF_COLOURS = ["red_terracotta", "blue_terracotta", "cyan_terracotta", "gray_terracotta", "green_terracotta",
                "light_blue_terracotta", "brown_terracotta", "orange_terracotta"]

PLANTATION = Style(
    name="plantation",
    walls=[("minecraft:white_terracotta", 6), ("minecraft:calcite", 1)],
    frame="minecraft:stripped_birch_log[axis=y]", beam="minecraft:stripped_birch_log",
    plinth="minecraft:stone_bricks", plinth_stair="minecraft:stone_brick_stairs",
    trim_slab="minecraft:smooth_quartz_slab", trim_stair="minecraft:smooth_quartz_stairs",
    roof="mcwroofs:red_terracotta", roof_cap="minecraft:red_terracotta",
    window="minecraft:glass_pane", shutter="minecraft:birch_trapdoor", door="mcwdoors:oak_tropical_door",
    floor="minecraft:birch_planks", inner_wall="minecraft:white_terracotta", deck="minecraft:stripped_birch_wood[axis=y]",
    post="minecraft:stripped_birch_log[axis=y]", rail="minecraft:birch_fence",
)
STYLES: dict[str, Style] = {
    "plantation": PLANTATION,
    "hauoli": replace(PLANTATION, name="hauoli", walls=[("minecraft:white_concrete", 5), ("minecraft:calcite", 1)],
                      roof="mcwroofs:light_blue_terracotta", porch=2),
    "iki": Style(
        name="iki", walls=[("minecraft:stripped_bamboo_block[axis=y]", 4), ("minecraft:bamboo_planks", 1)],
        frame="minecraft:stripped_jungle_log[axis=y]", beam="minecraft:stripped_jungle_log",
        plinth="minecraft:stripped_jungle_log[axis=y]", plinth_stair="minecraft:jungle_stairs",
        trim_slab="minecraft:bamboo_slab", trim_stair="minecraft:bamboo_stairs",
        roof="beachparty:thatch_stairs", roof_cap="beachparty:thatch",
        window="minecraft:bamboo_fence", shutter="minecraft:bamboo_trapdoor", door="mcwdoors:jungle_tropical_door",
        floor="minecraft:bamboo_planks", inner_wall="minecraft:bamboo_planks", deck="minecraft:bamboo_planks",
        post="minecraft:stripped_jungle_log[axis=y]", rail="minecraft:bamboo_fence", roof_kind="hip", porch=2,
        raised=1, planter=False),
    "malie": Style(
        name="malie", walls=[("minecraft:white_terracotta", 4), ("minecraft:calcite", 1)],
        frame="minecraft:stripped_dark_oak_log[axis=y]", beam="minecraft:stripped_dark_oak_log",
        plinth="minecraft:stone_bricks", plinth_stair="minecraft:stone_brick_stairs",
        trim_slab="minecraft:dark_oak_slab", trim_stair="minecraft:dark_oak_stairs",
        roof="mcwroofs:deepslate", roof_cap="minecraft:deepslate_tiles",
        window="minecraft:white_stained_glass_pane", shutter=None, door="mcwdoors:dark_oak_japanese_door",
        floor="minecraft:dark_oak_planks", inner_wall="minecraft:white_terracotta", deck="minecraft:dark_oak_planks",
        post="minecraft:stripped_dark_oak_log[axis=y]", rail="minecraft:dark_oak_fence", roof_kind="hip", porch=2,
        planter=False),
    "konikoni": Style(
        name="konikoni", walls=[("minecraft:white_terracotta", 3), ("minecraft:yellow_terracotta", 1)],
        frame="minecraft:red_concrete", beam="minecraft:red_terracotta",
        plinth="minecraft:polished_granite", plinth_stair="minecraft:polished_granite_stairs",
        trim_slab="minecraft:red_nether_brick_slab", trim_stair="minecraft:red_nether_brick_stairs",
        roof="mcwroofs:red_nether_bricks", roof_cap="minecraft:red_nether_bricks",
        window="minecraft:red_stained_glass_pane", shutter="minecraft:crimson_trapdoor", door="mcwdoors:cherry_japanese_door",
        floor="minecraft:cherry_planks", inner_wall="minecraft:white_terracotta", deck="minecraft:cherry_planks",
        post="minecraft:red_concrete", rail="minecraft:crimson_fence", roof_kind="gable", porch=2, planter=False),
    "paniola": Style(
        name="paniola", walls=[("minecraft:spruce_planks", 4), ("minecraft:stripped_spruce_wood[axis=y]", 1)],
        frame="minecraft:spruce_log[axis=y]", beam="minecraft:stripped_spruce_log",
        plinth="minecraft:cobblestone", plinth_stair="minecraft:cobblestone_stairs",
        trim_slab="minecraft:spruce_slab", trim_stair="minecraft:spruce_stairs",
        roof="mcwroofs:spruce", roof_cap="minecraft:spruce_planks",
        window="minecraft:glass_pane", shutter="minecraft:spruce_trapdoor", door="mcwdoors:spruce_western_door",
        floor="minecraft:spruce_planks", inner_wall="minecraft:stripped_spruce_wood[axis=y]",
        deck="minecraft:spruce_planks", post="minecraft:spruce_fence", rail="minecraft:spruce_fence",
        roof_kind="gable", porch=3),
    "modern": Style(
        name="modern", walls=[("minecraft:white_concrete", 6), ("minecraft:smooth_quartz", 1)],
        frame="minecraft:smooth_quartz", beam="minecraft:light_gray_concrete",
        plinth="minecraft:polished_andesite", plinth_stair="minecraft:polished_andesite_stairs",
        trim_slab="minecraft:smooth_quartz_slab", trim_stair="minecraft:smooth_quartz_stairs",
        roof="minecraft:smooth_quartz_stairs", roof_cap="minecraft:smooth_quartz",
        window="minecraft:light_blue_stained_glass_pane", shutter=None, door="mcwdoors:sliding_glass_door",
        floor="minecraft:polished_diorite", inner_wall="minecraft:white_concrete", deck="minecraft:smooth_stone",
        post="minecraft:quartz_pillar[axis=y]", rail="minecraft:glass_pane", roof_kind="flat", porch=0, planter=False),
    "po": Style(
        name="po", walls=[("minecraft:gray_concrete", 4), ("minecraft:cracked_stone_bricks", 1), ("minecraft:andesite", 1)],
        frame="minecraft:polished_blackstone", beam="minecraft:polished_blackstone_bricks",
        plinth="minecraft:cobbled_deepslate", plinth_stair="minecraft:cobbled_deepslate_stairs",
        trim_slab="minecraft:polished_blackstone_slab", trim_stair="minecraft:polished_blackstone_stairs",
        roof="mcwroofs:blackstone", roof_cap="minecraft:blackstone",
        window="minecraft:iron_bars", shutter=None, door="mcwdoors:metal_reinforced_door",
        floor="minecraft:spruce_planks", inner_wall="minecraft:gray_concrete", deck="minecraft:cobbled_deepslate",
        post="minecraft:polished_blackstone_wall", rail="minecraft:iron_bars", roof_kind="gable", porch=0,
        planter=False),
}


# ------------------------------------------------------------------ parts

def pick(rng: random.Random, weighted):
    tot = sum(wt for _, wt in weighted)
    r = rng.random() * tot
    for st, wt in weighted:
        r -= wt
        if r <= 0:
            return st
    return weighted[-1][0]


def axis_log(state: str, axis: str) -> str:
    name, props = parse_state(state)
    if name.endswith(("_log", "_wood", "_stem", "_block", "pillar")) and ("axis" in props or name.endswith(("_log", "_wood", "_stem"))):
        props["axis"] = axis
        return name + "[" + ",".join(f"{k}={v}" for k, v in props.items()) + "]"
    return state


def roof_piece(prefix: str, facing: str, half="bottom") -> str:
    if macaw(prefix):
        return f"{prefix}_roof[facing={facing},half={half},shape=straight]"
    return f"{prefix}[facing={facing},half={half},shape=straight]"


def ridge_piece(st: Style, along: str) -> str:
    if macaw(st.roof):
        return f"{st.roof}_top_roof[part={'switched_0' if along == 'u' else 'switched_90'}]"
    return st.roof_cap


def door(b: Bld, u, v, w, kind, facing="south", hinge="left"):
    b.set(u, v, w, f"{kind}[facing={facing},half=lower,hinge={hinge},open=false]")
    b.set(u, v + 1, w, f"{kind}[facing={facing},half=upper,hinge={hinge},open=false]")


def window_unit(b: Bld, st: Style, u, v, w, rng, outward="south", tall=2, width=1):
    """Glass in the wall plane w, sill below, lintel above, shutters and a planter outside (w - 1 side)."""
    out = -1 if outward == "south" else 1
    for du in range(width):
        for dv in range(tall):
            b.set(u + du, v + dv, w, st.window)
    back = "north" if outward == "south" else "south"
    for du in range(width):
        if st.planter:                                   # flower box doubles as the sill
            b.set(u + du, v - 1, w + out, furn.piece("flower_box", outward))
        else:
            b.set(u + du, v - 1, w + out, f"{st.trim_stair}[facing={back},half=top,shape=straight]")
        b.set(u + du, v + tall, w + out, f"{st.trim_slab}[type=top]")   # lintel hood
    if st.shutter:
        for su in (u - 1, u + width):
            for dv in range(tall):
                b.set(su, v + dv, w + out, f"{st.shutter}[facing={outward},half=bottom,open=true]")


def lamp_pair(b: Bld, u1, u2, v, w, facing="south"):
    for u in (u1, u2):
        b.piece(u, v, w, "wall_lamp", facing)


# --------------------------------------------------------------- the house

@dataclass
class House:
    W: int
    D: int
    floors: int = 1
    label: str | None = None
    roof_colour: str | None = None
    beds: int = 1
    yard: bool = True


def build_house(c: Canvas, x, y, z, facing, rng: random.Random, style="plantation", W=11, D=9, floors=1,
                label=None, roof_colour=None, beds=1, yard=True, interior=None):
    """Build a detailed house; (x, y, z) is the front-left floor corner. Returns the reserved (u_max, w_max)."""
    st = STYLES[style] if isinstance(style, str) else style
    if roof_colour and macaw(st.roof):
        st = replace(st, roof=f"mcwroofs:{roof_colour}")
    b = Bld(c, x, y, z, facing)
    P = st.porch
    H = st.story_h
    top = H * floors
    R = st.raised
    # ground: clear the plot and pour footing down to the terrain
    b.clear_above(-3, -P - 3, W + 2, D + 2, top + R + 16)
    for u in range(-1, W + 1):
        for w in range(-1 - P, D + 1):
            xx, yy, zz = b.world(u, 0, w)
            ground = c.surface(xx, zz) if c.inside(xx, zz) else y
            for yy2 in range(y - 1, min(ground, y - 1) - 1, -1):
                c.set(xx, yy2, zz, st.plinth if 0 <= u < W and 0 <= w < D else "minecraft:dirt")
    if R:   # stilts
        for (u, w) in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1), (W // 2, 0), (W // 2, D - 1)):
            for v in range(0, R):
                b.set(u, v, w, st.frame)
    b0 = R   # floor level
    # floor and plinth lip
    for u in range(W):
        for w in range(D):
            b.set(u, b0, w, st.floor if 0 < u < W - 1 and 0 < w < D - 1 else st.plinth if not R else st.frame)
    if not R:
        for u in range(-1, W + 1):
            b.set(u, 0, -1, f"{st.plinth_stair}[facing=north,half=bottom,shape=straight]") if P == 0 else None
            b.set(u, 0, D, f"{st.plinth_stair}[facing=south,half=bottom,shape=straight]")
        for w in range(-1 if P == 0 else 0, D + 1):
            b.set(-1, 0, w, f"{st.plinth_stair}[facing=east,half=bottom,shape=straight]")
            b.set(W, 0, w, f"{st.plinth_stair}[facing=west,half=bottom,shape=straight]")
    # walls, posts and beams
    for f in range(floors):
        v0 = b0 + f * H
        for v in range(v0 + 1, v0 + H):
            for u in range(W):
                for w in (0, D - 1):
                    b.set(u, v, w, pick(rng, st.walls))
            for w in range(1, D - 1):
                for u in (0, W - 1):
                    b.set(u, v, w, pick(rng, st.walls))
        # beam ring at the top of the storey
        for u in range(W):
            for w in (0, D - 1):
                b.set(u, v0 + H, w, axis_log(st.beam, "x"))
        for w in range(D):
            for u in (0, W - 1):
                b.set(u, v0 + H, w, axis_log(st.beam, "z"))
        if f:   # upper floor
            for u in range(1, W - 1):
                for w in range(1, D - 1):
                    b.set(u, v0, w, st.floor)
    for (u, w) in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
        for v in range(b0 + 1, b0 + top + 1):
            b.set(u, v, w, st.frame)
    # intermediate posts on long walls
    posts_u = [u for u in range(4, W - 3, 4)] if W >= 11 else []
    for u in posts_u:
        if u == W // 2:
            continue
        for v in range(b0 + 1, b0 + top):
            b.set(u, v, 0, st.frame)
            b.set(u, v, D - 1, st.frame)
    # door, windows
    du = W // 2
    door(b, du, b0 + 1, 0, st.door, facing="south")
    b.set(du, b0 + 3, -1, f"{st.trim_slab}[type=top]")
    lamp_pair(b, du - 1, du + 1, b0 + 3, -1)
    for f in range(floors):
        v0 = b0 + f * H
        for u in range(2, W - 2, 3):
            if abs(u - du) <= 1 and f == 0 or u in posts_u:
                continue
            window_unit(b, st, u, v0 + 2, 0, rng, "south")
            window_unit(b, st, u, v0 + 2, D - 1, rng, "north")
        for w in range(2, D - 2, 3):
            _side_window(b, st, 0, v0 + 2, w, "west")
            _side_window(b, st, W - 1, v0 + 2, w, "east")
    # porch / lanai
    if P:
        porch(b, st, W, P, b0, rng)
    # roof
    rtop = b0 + top
    if st.roof_kind == "flat":
        flat_roof(b, st, W, D, rtop)
    elif st.roof_kind == "gable":
        gable_roof(b, st, W, D, rtop, rng)
    else:
        hip_roof(b, st, W, D, rtop)
    # inside
    furnish(b, st, W, D, floors, b0, rng, beds=beds, kind=interior or st.interior)
    if label:
        b.sign(du + 1, b0 + 2, -1, [label], wood="birch")
    if yard:
        landscape(b, st, W, D, rng)
    return W, D


def _side_window(b: Bld, st: Style, u, v, w, outward):
    """Windows on the side walls (u plane)."""
    out = -1 if outward == "west" else 1
    for dv in (0, 1):
        b.set(u, v + dv, w, st.window)
    inward = "east" if outward == "west" else "west"
    b.set(u + out, v - 1, w, f"{st.trim_stair}[facing={inward},half=top,shape=straight]")
    b.set(u + out, v + 2, w, f"{st.trim_slab}[type=top]")
    if st.shutter:
        for sw in (w - 1, w + 1):
            for dv in (0, 1):
                b.set(u + out, v + dv, sw, f"{st.shutter}[facing={outward},half=bottom,open=true]")


def porch(b: Bld, st: Style, W, P, b0, rng):
    """Covered lanai across the front: deck, posts, railings, steps, a lean-to roof and seating."""
    for u in range(-1, W + 1):
        for w in range(-P, 0):
            b.set(u, b0, w, st.deck)
    step_u = W // 2
    for u in (-1, W):
        for v in range(b0 + 1, b0 + st.story_h):
            b.set(u, v, -P, st.post)
    for u in range(-1, W + 1, 4):
        for v in range(b0 + 1, b0 + st.story_h):
            b.set(u, v, -P, st.post)
    for u in range(0, W):
        if abs(u - step_u) > 1 and b.get(u, b0 + 1, -P) == "minecraft:air":
            b.set(u, b0 + 1, -P, st.rail)
    for w in range(-P + 1, 0):
        b.set(-1, b0 + 1, w, st.rail)
        b.set(W, b0 + 1, w, st.rail)
    if b0:  # raised floor: steps down
        for k in range(b0):
            for u in (step_u - 1, step_u, step_u + 1):
                b.set(u, b0 - 1 - k, -P - 1 - k, f"{st.trim_stair}[facing=north,half=bottom,shape=straight]")
    # lean-to roof over the deck
    v = b0 + st.story_h
    for u in range(-2, W + 2):
        b.set(u, v, -P - 1, roof_piece(st.roof, "north"))
        for w in range(-P, 0):
            b.set(u, v, w, f"{st.trim_slab}[type=top]")
    # seating
    b.piece(1, b0 + 1, -P + 1, "chair", "south")
    b.piece(W - 2, b0 + 1, -P + 1, "chair", "south")
    b.piece(2, b0 + 1, -P + 1, "plant")


def hip_roof(b: Bld, st: Style, W, D, v):
    a, bb, c1, d = -1, W, -1, D
    k = 0
    while a <= bb and c1 <= d:
        vv = v + k
        if a == bb or c1 == d:
            along = "u" if bb - a > d - c1 else "w"
            for u in range(a, bb + 1):
                for w in range(c1, d + 1):
                    b.set(u, vv, w, ridge_piece(st, along))
            break
        for u in range(a, bb + 1):
            b.set(u, vv, c1, roof_piece(st.roof, "north"))
            b.set(u, vv, d, roof_piece(st.roof, "south"))
        for w in range(c1 + 1, d):
            b.set(a, vv, w, roof_piece(st.roof, "east"))
            b.set(bb, vv, w, roof_piece(st.roof, "west"))
        # fill under the slope so the roof reads solid from inside
        for u in range(a + 1, bb):
            for w in range(c1 + 1, d):
                if u in (a + 1, bb - 1) or w in (c1 + 1, d - 1):
                    if b.get(u, vv, w) == "minecraft:air":
                        b.set(u, vv, w, st.roof_cap)
        a, bb, c1, d = a + 1, bb - 1, c1 + 1, d - 1
        k += 1


def gable_roof(b: Bld, st: Style, W, D, v, rng):
    """Ridge parallel to the front; gable walls on the left and right with a small window."""
    c1, d = -1, D
    k = 0
    while c1 <= d:
        vv = v + k
        if c1 == d:
            for u in range(-1, W + 1):
                b.set(u, vv, c1, ridge_piece(st, "u"))
            break
        for u in range(-1, W + 1):
            b.set(u, vv, c1, roof_piece(st.roof, "north"))
            b.set(u, vv, d, roof_piece(st.roof, "south"))
        # gable wall under this course
        for w in range(max(c1 + 1, 0), min(d, D)):
            for u in (0, W - 1):
                if b.get(u, vv, w) == "minecraft:air":
                    b.set(u, vv, w, pick(rng, st.walls))
        c1, d = c1 + 1, d - 1
        k += 1
    mid = D // 2
    for u in (0, W - 1):
        b.set(u, v + 1, mid, st.window)


def flat_roof(b: Bld, st: Style, W, D, v):
    for u in range(-1, W + 1):
        for w in range(-1, D + 1):
            edge = u in (-1, W) or w in (-1, D)
            b.set(u, v, w, st.beam if edge else st.roof_cap)
            if edge:
                b.set(u, v + 1, w, f"{st.trim_slab}[type=bottom]")


# ---------------------------------------------------------------- interior

def furnish(b: Bld, st: Style, W, D, floors, b0, rng, beds=1, kind="home"):
    """Rooms: living room at the front, kitchen on the left, bedroom at the back right."""
    v = b0 + 1
    if kind == "empty":
        return
    split = max(3, D // 2)
    # interior wall between front and back rooms, with a doorway
    for u in range(1, W - 1):
        if b.get(u, v, split) == "minecraft:air":
            for dv in range(3):
                b.set(u, v + dv, split, st.inner_wall)
    b.clear(W // 2, v, split, W // 2, v + 1, split)
    # living room (front)
    b.piece(1, v, 1, "sofa", "east")
    b.piece(1, v, 2, "sofa", "east")
    b.piece(3, v, 1, "table")
    b.piece(W - 2, v, 1, "tv", "west")
    b.piece(W - 3, v, 1, "armchair", "west")
    b.set(3, v, 2, furn.piece("rug"))
    b.piece(1, v, split - 1, "plant_big")
    b.piece(W - 2, v, split - 1, "bookshelf", "west")
    b.piece(W // 2, b0 + st.story_h - 1, split // 2, "ceiling_lamp")
    # kitchen strip on the back-left
    for w in range(split + 1, D - 1):
        b.piece(1, v, w, "kitchen_drawer" if w % 2 else "counter", "east")
    b.piece(1, v, D - 2, "fridge", "east")
    b.piece(2, v, D - 2, "stove", "north")
    b.piece(3, v, D - 2, "kitchen_sink", "north")
    b.piece(3, v, split + 2, "table")
    b.piece(4, v, split + 2, "chair", "west")
    # bedroom back-right
    for i in range(beds):
        bu = W - 2 - 2 * i
        if bu < W // 2 + 1:
            break
        b.bed(bu, v, D - 3, rng.choice(["red", "light_blue", "yellow", "pink", "white", "lime"]), facing="north")
        b.piece(bu - 1, v, D - 2, "drawer", "north") if bu - 1 > W // 2 else None
    b.piece(W // 2 + 1, v, split + 1, "wardrobe", "south")
    b.piece(W - 2, v, split + 1, "doll_rowlet" if rng.random() < 0.5 else "doll_mimikyu", "west")
    b.piece(W // 2 + 2, b0 + st.story_h - 1, (split + D) // 2, "ceiling_lamp")


# ----------------------------------------------------------------- the yard

def landscape(b: Bld, st: Style, W, D, rng):
    """Front path, flower beds along the walls, a hedge line and a tree or palm in the yard."""
    c = b.c
    P = st.porch
    du = W // 2
    for w in range(-P - 6, -P):
        for u in (du - 1, du, du + 1):
            xx, yy, zz = b.world(u, 0, w)
            if c.inside(xx, zz):
                c.set(xx, c.surface(xx, zz), zz, furn.piece("path_tile"))
    for u in range(-2, W + 2):
        if abs(u - du) <= 1:
            continue
        xx, yy, zz = b.world(u, 0, -P - 2)
        if c.inside(xx, zz) and rng.random() < 0.85:
            gy = c.surface(xx, zz)
            c.set(xx, gy + 1, zz, rng.choice(["minecraft:azalea_leaves[persistent=true]",
                                              "minecraft:flowering_azalea_leaves[persistent=true]"]))
    for w in range(0, D, 2):
        for u in (-2, W + 1):
            xx, yy, zz = b.world(u, 0, w)
            if c.inside(xx, zz):
                gy = c.surface(xx, zz)
                if c.get(xx, gy + 1, zz) == "minecraft:air":
                    c.set(xx, gy + 1, zz, rng.choice(["wilderwild:pink_hibiscus", "wilderwild:red_hibiscus",
                                                     "wilderwild:yellow_hibiscus", "minecraft:poppy",
                                                     "minecraft:azure_bluet"]))


# ------------------------------------------------------------ lab samples

def _test_board(c: Canvas, x, y, z):
    """Macaw's pieces whose shapes need checking: ridge parts, windows, shutters, planters."""
    b = Bld(c, x, y, z, "south")
    col = 0
    labels = []

    def spot(lbl):
        nonlocal col
        u = col * 3
        col += 1
        labels.append((u, lbl))
        return u

    # small roofs: 3 wide, ridge variants
    for part in ("switched_0", "switched_90", "top_end_0", "pyramid", "four_way", "top_outer_0"):
        u = spot(f"top {part}")
        b.set(u, 1, 2, "minecraft:stone")
        b.set(u, 2, 2, f"mcwroofs:red_terracotta_top_roof[part={part}]")
    for kind in ("roof", "lower_roof", "steep_roof", "attic_roof", "upper_lower_roof", "upper_steep_roof"):
        u = spot(kind)
        b.set(u, 1, 2, "minecraft:stone")
        props = "facing=north,half=bottom,shape=straight" if kind != "attic_roof" else "facing=north,open=false"
        b.set(u, 2, 2, f"mcwroofs:red_terracotta_{kind}[{props}]")
    for win in ("birch_window[facing=north,part=base]", "birch_window2[facing=north,windowstate=closed]",
                "birch_four_window[facing=north,windowstate=closed]", "birch_pane_window[facing=north,part=base,windowstate=closed]",
                "birch_louvered_shutter[facing=south,hinge=left,open=false]", "birch_louvered_shutter[facing=south,hinge=left,open=true]",
                "birch_shutter[facing=south,hinge=left,open=true]", "birch_plank_parapet[facing=south,part=flower]",
                "white_curtain[facing=south,tied=left]"):
        u = spot(win.split("[")[0])
        b.set(u, 1, 3, "minecraft:white_terracotta")
        b.set(u, 2, 3, "minecraft:white_terracotta")
        b.set(u, 1, 2, f"mcwwindows:{win}")
    for tr in ("minecraft:birch_trapdoor[facing=south,half=bottom,open=true]",
               "minecraft:birch_trapdoor[facing=north,half=bottom,open=true]",
               "supplementaries:flower_box[facing=south]", "another_furniture:oak_flower_box[facing=south]",
               "supplementaries:awning_red[facing=south]", "mcwroofs:red_striped_awning[facing=south,shape=straight]"):
        u = spot(tr.split(":")[1].split("[")[0] + (" N" if "facing=north" in tr else ""))
        b.set(u, 1, 3, "minecraft:white_terracotta")
        b.set(u, 2, 3, "minecraft:white_terracotta")
        b.set(u, 2, 2, tr)
    for u, lbl in labels:
        b.sign(u, 1, 0, [lbl[:15], lbl[15:30]], wood="birch", wall=False)
    for u in range(-1, col * 3):
        for w in range(-1, 5):
            b.set(u, 0, w, "minecraft:smooth_stone")
    return col * 3, 5


def _sample(style, **kw):
    def fn(c, x, y, z):
        W = kw.get("W", 11)
        D = kw.get("D", 9)
        st = STYLES[style]
        build_house(c, x, y, z + st.porch + 1, "south", random.Random(3), style=style, **kw)
        return W, D + st.porch + 2
    return fn


def register_lab():
    from . import lab
    lab.SAMPLES.clear()
    lab.SAMPLES.append(("test_board", _test_board))
    for style, kw in (("plantation", dict(W=11, D=9)), ("hauoli", dict(W=11, D=9, floors=2, roof_colour="blue_terracotta")),
                      ("iki", dict(W=9, D=7)), ("malie", dict(W=11, D=9)), ("konikoni", dict(W=11, D=9)),
                      ("paniola", dict(W=11, D=9)), ("modern", dict(W=13, D=11, floors=2)), ("po", dict(W=9, D=9))):
        lab.SAMPLES.append((style, _sample(style, **kw)))


# ------------------------------------------------------------- town adapter

STYLES["tapu"] = replace(PLANTATION, name="tapu",
                         walls=[("minecraft:cracked_stone_bricks", 3), ("minecraft:mossy_stone_bricks", 2),
                                ("minecraft:stone_bricks", 2)],
                         frame="minecraft:stripped_spruce_log[axis=y]", beam="minecraft:stripped_spruce_log",
                         roof="mcwroofs:cobblestone", roof_cap="minecraft:mossy_cobblestone",
                         shutter="minecraft:spruce_trapdoor", door="mcwdoors:spruce_swamp_door", porch=2, planter=False)


def house(c: Canvas, x, y, z, facing, rng: random.Random, W=None, D=None, style="plantation", label=None, beds=1,
          floors=1, roof_colour=None, yard=False, **_):
    """Street-friendly wrapper: (x, y, z) is the front-left corner of the lot, porch included."""
    st = STYLES[style]
    W = W or rng.choice([9, 11])
    D = D or rng.choice([8, 9])
    if roof_colour is None and style in ("plantation", "hauoli"):
        roof_colour = rng.choice(ROOF_COLOURS)
    ox, oy, oz = B(c, x, y, z, facing).world(0, 0, st.porch)
    build_house(c, ox, oy, oz, facing, rng, style=style, W=W, D=D, floors=floors, label=label,
                roof_colour=roof_colour, beds=beds, yard=yard)
    return W, D + st.porch
