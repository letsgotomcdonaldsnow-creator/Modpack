"""Akala Island's sites: Hano Grand Resort, the Battle Royal Dome, Brooklet Hill (Lana's trial), Kiawe's fire
stage on Wela Volcano, Mallow's jungle kitchen in the Lush Jungle and Paniola Ranch."""
from __future__ import annotations

import math
import random

from . import arch, furn, plants
from .buildings import merchant, npc, pokeball_disc
from .canvas import Canvas
from .sites import AIR, LUSH, glow_vines, ground_cover, hang_lantern, plant_on, stair, tall, wall_vines

pick = arch.pick
LOCAL_DIRS = {"south": (0, -1), "north": (0, 1), "east": (1, 0), "west": (-1, 0)}


def lounger(b, u, v, w, facing):
    """A two-part Beachparty sun lounger with its head toward `facing` (local compass)."""
    du, dw = LOCAL_DIRS[facing]
    b.set(u, v, w, f"beachparty:beach_sun_lounger[facing={facing},part=foot]")
    b.set(u + du, v, w + dw, f"beachparty:beach_sun_lounger[facing={facing},part=head]")


def parasol(b, u, v, w, colour):
    """A fabric parasol on a bamboo pole: wool crown with carpet skirts."""
    for dv in range(3):
        b.set(u, v + dv, w, "minecraft:bamboo_fence")
    for du in (-1, 0, 1):
        for dw in (-1, 0, 1):
            b.set(u + du, v + 3, w + dw, f"minecraft:{colour}_wool" if (du, dw) == (0, 0) else f"minecraft:{colour}_carpet")


def world_palm(b, u, w, rng, tall_=None):
    x, _, z = b.world(u, 0, w)
    if b.c.inside(x, z):
        plants.palm(b.c, x, b.c.surface(x, z), z, rng, tall=tall_ or rng.randint(7, 10))


# ======================================================================= Hano Grand Resort

RESORT = arch.replace(
    arch.STYLES["plantation"], name="resort",
    walls=[("minecraft:white_concrete", 5), ("minecraft:smooth_sandstone", 1)],
    frame="minecraft:smooth_quartz", beam="minecraft:cut_sandstone",
    plinth="minecraft:smooth_sandstone", plinth_stair="minecraft:smooth_sandstone_stairs",
    trim_slab="minecraft:smooth_sandstone_slab", trim_stair="minecraft:smooth_sandstone_stairs",
    roof="mcwroofs:orange_terracotta", roof_cap="minecraft:orange_terracotta",
    window="minecraft:light_blue_stained_glass_pane", shutter=None, door="mcwdoors:sliding_glass_door",
    floor="minecraft:smooth_quartz", inner_wall="minecraft:white_concrete", porch=0, planter=True, roof_kind="hip")


def hano_resort(c: Canvas, x, y, z, facing, rng: random.Random):
    """Hano Grand Resort: a six-storey hotel under an orange hip roof with sea-view balconies, a marble lobby,
    a porte-cochère and fountain at the front, and a pool terrace with a bar stepping down to the beach."""
    b = arch.Bld(c, x, y, z, facing)
    W, D, F = 45, 17, 6
    H = RESORT.story_h
    cu = W // 2
    TER = 24                                     # terrace depth behind the hotel
    b.clear_above(-8, -18, W + 7, D + TER + 2, 12)
    b.foundation(-8, -18, W + 7, D + TER + 2, "minecraft:smooth_sandstone")
    arch.build_house(c, x, y, z, facing, rng, style=RESORT, W=W, D=D, floors=F, label=None, yard=False,
                     interior="empty")
    # ---- the lobby
    for u in range(1, W - 1):
        for w in range(1, D - 1):
            b.set(u, 0, w, "minecraft:smooth_quartz" if (u + w) % 2 else "minecraft:polished_diorite")
    for u in range(cu - 4, cu + 5):
        for v in range(1, 4):
            if u != cu:
                b.set(u, v, 0, "minecraft:glass_pane")
    for w in range(1, 11):                         # red carpet runner to the desk
        for du in (-1, 0, 1):
            b.set(cu + du, 0, w, "minecraft:red_concrete")
    for du in range(-4, 5):                        # reception
        b.piece(cu + du, 1, D - 4, "counter", "south")
    b.set(cu + 1, 2, D - 4, "another_furniture:service_bell")
    merchant(b, cu, 1, D - 3, name="Hano Concierge", look="front")
    b.sign(cu, 3, D - 2, ["Hano Grand", "Resort", "", "Welcome!"], wood="birch", glow=True)
    for u0 in (6, W - 12):                         # two lounges
        for du in range(3):
            b.piece(u0 + du, 1, 3, "sofa_white", "south")
            b.piece(u0 + du, 1, 7, "sofa_white", "north")
        b.piece(u0 + 1, 1, 5, "table")
        for du in range(-1, 4):
            for dw in (4, 5, 6):
                if b.get(u0 + du, 1, dw) == AIR:
                    b.set(u0 + du, 1, dw, "minecraft:light_blue_carpet")
        b.piece(u0 - 2, 1, 1, "plant_big"), b.piece(u0 + 4, 1, 1, "plant_big")
    for u in (8, cu, W - 9):
        b.set(u, 3, 7, "mcwlights:golden_chandelier")
    # back doors onto the terrace
    for du in (-1, 0, 1):
        for v in (1, 2):
            b.set(cu + du, v, D - 1, AIR)
    # ---- rooms upstairs: a corridor down the middle, rooms front and back
    for f in range(1, F):
        v0 = f * H
        for u in range(1, 36):
            for w in (6, 10):
                for dv in range(1, H):
                    b.set(u, v0 + dv, w, RESORT.inner_wall)
        for u in range(5, 36, 6):
            for w in list(range(1, 6)) + list(range(11, D - 1)):
                for dv in range(1, H):
                    b.set(u, v0 + dv, w, RESORT.inner_wall)
        for u in range(1, W - 1):
            for w in range(7, 10):
                b.set(u, v0, w, "minecraft:red_wool" if w == 8 else "minecraft:smooth_quartz")
        for u0 in range(1, 32, 6):
            for (dw, bw, face) in ((6, 2, "north"), (10, D - 3, "south")):
                arch.door(b, u0 + 2, v0 + 1, dw, "minecraft:birch_door", facing=face)
                b.bed(u0 + 1, v0 + 1, bw, "white", facing="south" if face == "north" else "north")
                b.piece(u0 + 3, v0 + 1, bw, "drawer", "east")
            b.piece(u0 + 2, v0 + H - 1, 8, "ceiling_lamp")
    # sea-view balconies on the back, reached through glass doors
    for f in range(1, F):
        v0 = f * H
        for u in range(3, 34, 6):
            for du in range(-2, 3):
                for dw in (D, D + 1):
                    b.set(u + du, v0, dw, "minecraft:smooth_quartz_slab[type=top]")
                b.set(u + du, v0 + 1, D + 1, "minecraft:white_stained_glass_pane")
                for dv in (1, 2, 3):
                    here = b.get(u + du, v0 + dv, D)
                    if "trapdoor" in here or "flower_box" in here or "slab" in here:
                        b.set(u + du, v0 + dv, D, AIR)
            b.set(u - 2, v0 + 1, D, "minecraft:white_stained_glass_pane")
            b.set(u + 2, v0 + 1, D, "minecraft:white_stained_glass_pane")
            arch.door(b, u, v0 + 1, D - 1, "mcwdoors:sliding_glass_door", facing="north")
            b.piece(u + 1, v0 + 1, D, "chair", "north")
    # ---- porte-cochère, driveway and fountain
    for u in range(cu - 5, cu + 6):
        for w in range(-7, 0):
            b.set(u, 5, w, "minecraft:smooth_quartz_slab[type=bottom]" if u in (cu - 5, cu + 5) or w == -7
                  else "minecraft:smooth_quartz")
    for u in (cu - 5, cu + 5):
        for w in (-7, -1):
            for v in range(1, 5):
                b.set(u, v, w, "minecraft:quartz_pillar[axis=y]")
    for u in range(cu - 4, cu + 5):
        b.set(u, 5, -8, stair("minecraft:smooth_quartz_stairs", "south", "top"))
    hang_lantern(b, cu - 2, 5, -4, 2), hang_lantern(b, cu + 2, 5, -4, 2)
    for u in range(-6, W + 6):
        for w in range(-17, 0):
            d = math.hypot(u - cu, w + 11)
            b.set(u, 0, w, "minecraft:smooth_sandstone" if (6 <= d <= 11 and w > -17) or -8 <= w <= -1 and
                  abs(u - cu) <= 6 else "minecraft:grass_block")
    for du in range(-4, 5):                        # fountain in the turning circle
        for dw in range(-4, 5):
            d = math.hypot(du, dw)
            if d <= 4.4:
                b.set(cu + du, 0, -11 + dw, "minecraft:prismarine_bricks")
                if d > 3.4:
                    b.set(cu + du, 1, -11 + dw, "minecraft:smooth_quartz_slab[type=bottom]")
                else:
                    b.set(cu + du, 1, -11 + dw, "minecraft:water")
    for v in range(1, 4):
        b.set(cu, v, -11, "minecraft:smooth_quartz" if v < 3 else "minecraft:sea_lantern")
    for u, w in ((cu - 8, -3), (cu + 8, -3), (-4, -4), (W + 3, -4), (cu - 9, -15), (cu + 9, -15)):
        world_palm(b, u, w, rng)
    for u in range(-3, W + 3, 8):
        tall(b, u, 1, -2, "street_lamp")
    b.sign(cu - 7, 1, -9, ["Hano Grand", "Resort", "", "Akala Island"], wood="birch", wall=False)
    # the drive out to the Hano road, which arrives along the west side
    for (ua, wa, ub, wb) in ((-18, -11, -18, 22), (-18, -11, cu - 11, -11)):
        for u in range(min(ua, ub) - 1, max(ua, ub) + 2):
            for w in range(min(wa, wb) - 1, max(wa, wb) + 2):
                xx, _, zz = b.world(u, 0, w)
                if c.inside(xx, zz) and not c.is_water(xx, zz) and not (-6 <= u <= W + 5 and -17 <= w <= D + TER):
                    c.set(xx, c.surface(xx, zz), zz, "minecraft:smooth_sandstone")
    # ---- the pool terrace
    t0 = D + 2
    for u in range(-6, W + 6):
        for w in range(D, D + TER + 1):
            b.set(u, 0, w, "mcwpaths:sandstone_flagstone" if (u + w) % 5 else "minecraft:cut_sandstone")

    def in_pool(u, w):
        return (8 <= u <= 30 and t0 + 4 <= w <= t0 + 12) or math.hypot(u - 33, w - (t0 + 13)) <= 5.5

    for u in range(4, 40):
        for w in range(t0 + 2, t0 + 21):
            if in_pool(u, w):
                deep = 3 if math.hypot(u - 33, w - (t0 + 13)) <= 4 else 2
                for v in range(-deep, 1):
                    b.set(u, v, w, "minecraft:water")
                b.set(u, -deep - 1, w, furn.piece("pool_tile"))
            elif any(in_pool(u + du, w + dw) for du in (-1, 0, 1) for dw in (-1, 0, 1)):
                b.set(u, 0, w, "minecraft:smooth_quartz")
                for v in range(-4, 0):
                    b.set(u, v, w, furn.piece("pool_tile"))
    for u in range(9, 30, 3):                       # loungers and parasols along the long side
        lounger(b, u, 1, t0 + 2, "south")
        if u % 6 == 0:
            parasol(b, u + 1, 1, t0 + 1, rng.choice(["orange", "white", "yellow", "light_blue"]))
    for u in range(10, 28, 4):
        lounger(b, u, 1, t0 + 14, "north")
    # the pool bar under a thatched roof
    bu, bw = 1, t0 + 8
    for du in range(0, 5):
        b.set(bu + du, 1, bw, "beachparty:palm_bar[facing=north]")
        b.set(bu + du, 1, bw - 1, "beachparty:palm_bar_stool")
    for dw in range(1, 4):
        b.set(bu + 4, 1, bw + dw, "beachparty:palm_bar[facing=west]")
    for du, dw in ((-1, -2), (5, -2), (-1, 5), (5, 5)):
        for v in range(1, 4):
            b.set(bu + du, v, bw + dw, "minecraft:stripped_jungle_log[axis=y]")
    b.hip_roof(bu - 1, bu + 5, bw - 2, bw + 5, 4, "beachparty:thatch_stairs", "beachparty:thatch")
    b.piece(bu + 1, 2, bw, "cocktail"), b.piece(bu + 3, 2, bw, "cocktail")
    b.piece(bu + 2, 1, bw + 3, "mini_fridge", "south")
    for u, w in ((2, D + 3), (41, D + 3), (41, t0 + 20), (2, t0 + 20), (20, t0 + 20), (36, D + 3)):
        world_palm(b, u, w, rng)
    for u in range(-6, W + 6, 9):
        tall(b, u, 1, D + TER, "tiki_torch")
    # steps down to the beach and a line of parasols on the sand
    for u in range(cu - 2, cu + 3):
        for k in range(1, 12):
            xx, _, zz = b.world(u, 0, D + TER + k)
            if not c.inside(xx, zz) or c.is_water(xx, zz):
                break
            c.set(xx, c.surface(xx, zz), zz, "mcwpaths:sandstone_flagstone_path")
    for k in range(8):
        u = -4 + k * 7
        xx, _, zz = b.world(u, 0, D + TER + 14)
        if c.inside(xx, zz) and not c.is_water(xx, zz):
            gy = c.surface(xx, zz)
            bb = arch.Bld(c, xx, gy, zz, facing)
            parasol(bb, 0, 1, 0, rng.choice(["red", "orange", "white", "yellow", "light_blue", "pink"]))
            lounger(bb, 1, 1, -1, "north")
            bb.piece(-1, 1, -1, "beach_towel", "north")
    return W, D + TER


# ======================================================================= Battle Royal Dome

def royal_dome(c: Canvas, x, y, z, facing, rng: random.Random):
    """The Battle Royal Dome: a striped drum under a shallow ribbed dome with an oculus, tiered stands round
    a raised four-corner ring, and an entrance canopy onto Royal Avenue."""
    b = arch.Bld(c, x, y, z, facing)
    R = 20
    W = D = 2 * R + 1
    cu = cw = R
    b.clear_above(-5, -12, W + 4, D + 4, 40)
    b.foundation(-5, -12, W + 4, D + 4, "minecraft:polished_andesite")
    for u in range(-5, W + 5):
        for w in range(-12, D + 5):
            d = math.hypot(u - cu, w - cw)
            b.set(u, 0, w, "minecraft:polished_andesite" if d <= R + 1 else
                  "mcwpaths:andesite_flagstone" if (u + w) % 7 else "minecraft:smooth_stone")

    def facing_out(du, dw):
        if abs(du) >= abs(dw):
            return "east" if du > 0 else "west"
        return "north" if dw > 0 else "south"

    front_gap = lambda du, dw: dw < 0 and abs(du) <= 3
    for du in range(-R - 1, R + 2):
        for dw in range(-R - 1, R + 2):
            d = math.hypot(du, dw)
            a = math.degrees(math.atan2(dw, du)) % 360
            if R - 0.8 < d <= R + 0.3:               # the drum
                for v in range(1, 12):
                    if front_gap(du, dw) and v <= 5:
                        continue
                    stripe = int(a) % 30 < 4
                    b.set(cu + du, v, cw + dw,
                          "minecraft:polished_andesite" if v == 1 else
                          "minecraft:light_blue_stained_glass" if v in (6, 7) and not stripe else
                          "minecraft:red_concrete" if stripe else
                          "minecraft:smooth_quartz" if v in (10, 11) else "minecraft:white_concrete")
            if d <= R:                               # shallow ribbed dome
                vt = 12 + int(round(9 * (1 - (d / R) ** 2)))
                rib = int(a) % 30 < 4
                s = ("minecraft:light_blue_stained_glass" if d < 3.2 else
                     "minecraft:red_concrete" if d > R - 1.5 else
                     "minecraft:light_gray_concrete" if rib else "minecraft:white_concrete")
                b.set(cu + du, vt, cw + dw, s)
                d2 = math.hypot(abs(du) + 1, dw)
                if d2 <= R:
                    vt2 = 12 + int(round(9 * (1 - (d2 / R) ** 2)))
                    for v in range(vt2 + 1, vt):
                        b.set(cu + du, v, cw + dw, s)
                d3 = math.hypot(du, abs(dw) + 1)
                if d3 <= R:
                    vt3 = 12 + int(round(9 * (1 - (d3 / R) ** 2)))
                    for v in range(vt3 + 1, vt):
                        b.set(cu + du, v, cw + dw, s)
            # tiered stands inside, aisles at the four compass points
            if 9.5 <= d < R - 1 and not (abs(du) <= 1 or abs(dw) <= 1):
                k = int((d - 9.5) / 1.5)
                for v in range(1, k + 1):
                    b.set(cu + du, v, cw + dw, "minecraft:polished_andesite")
                b.set(cu + du, k + 1, cw + dw, stair("minecraft:red_nether_brick_stairs" if k % 2 else
                                                     "minecraft:polished_andesite_stairs", facing_out(du, dw)))
            elif d < 9.5:
                b.set(cu + du, 0, cw + dw, "minecraft:gray_concrete")
    # the ring: raised floor, coloured corner posts, chain ropes
    for du in range(-5, 6):
        for dw in range(-5, 6):
            edge = abs(du) == 5 or abs(dw) == 5
            b.set(cu + du, 1, cw + dw, "minecraft:white_concrete" if edge else "minecraft:blue_concrete")
    pokeball_disc(b, cu, cw, 1, 2)
    for (du, dw), col in (((-5, -5), "red"), ((5, -5), "blue"), ((-5, 5), "yellow"), ((5, 5), "lime")):
        for v in range(2, 5):
            b.set(cu + du, v, cw + dw, f"minecraft:{col}_concrete")
    for k in range(-4, 5):
        for v in (3, 4):
            b.set(cu + k, v, cw - 5, "minecraft:chain[axis=x]"), b.set(cu + k, v, cw + 5, "minecraft:chain[axis=x]")
            b.set(cu - 5, v, cw + k, "minecraft:chain[axis=z]"), b.set(cu + 5, v, cw + k, "minecraft:chain[axis=z]")
    for du, dw in ((-8, 0), (8, 0), (0, 8)):
        hang_lantern(b, cu + du, 12 + int(round(9 * (1 - (math.hypot(du, dw) / R) ** 2))), cw + dw, 3)
    npc(b, cu, 2, cw + 3, "alola:champion_kukui")
    # entrance canopy and signs
    for u in range(cu - 5, cu + 6):
        for w in range(-4, 1):
            b.set(u, 6, w, "minecraft:red_concrete" if w == -4 or u in (cu - 5, cu + 5) else "minecraft:white_concrete")
    for u in (cu - 5, cu + 5):
        for v in range(1, 6):
            b.set(u, v, -4, "minecraft:quartz_pillar[axis=y]")
    b.sign(cu - 2, 1, -6, ["Battle Royal Dome", "", "Royal Avenue", "Four trainers, one ring!"], wood="birch",
           wall=False)
    for u, w in ((-3, -3), (W + 2, -3), (-3, D + 2), (W + 2, D + 2)):
        world_palm(b, u, w, rng)
    for u in range(-4, W + 4, 9):
        tall(b, u, 1, -11, "street_lamp")
    return W, D


# ======================================================================= Brooklet Hill

def brooklet_hill(c: Canvas, x, y, z, rng: random.Random, lake=(-850, 745, 34, 20, 76)):
    """Lana's trial: a boardwalk on posts out over the big pond to a gazebo, a rock bluff with a double
    waterfall on the far shore, lily pads and cattails. World coordinates; (x, z) is the site centre."""
    lx, lz, rx, rz, level = lake
    deck = level + 1
    b = arch.Bld(c, 0, 0, 0, "south")               # world-aligned: u = x, v = y, w = -z

    def put(xx, yy, zz, state):
        b.set(xx, yy, -zz, state)

    def get(xx, yy, zz):
        return b.get(xx, yy, -zz)

    # boardwalk: from the site north along x, then west to the gazebo
    path = [(x, zz) for zz in range(z - 4, lz - 1, -1)] + [(xx, lz) for xx in range(x, lx + 5, -1)]
    for i, (px, pz) in enumerate(path):
        along_x = pz == lz
        for o in (-1, 0, 1):
            qx, qz = (px, pz + o) if along_x else (px + o, pz)
            if c.inside(qx, qz) and not c.is_water(qx, qz) and c.surface(qx, qz) >= deck:
                put(qx, c.surface(qx, qz), qz, "minecraft:dirt_path")      # still on land
                continue
            put(qx, deck, qz, "minecraft:spruce_planks" if o == 0 or i % 2 else "minecraft:stripped_spruce_wood[axis=y]")
            for yy in range(deck + 1, deck + 4):
                if get(qx, yy, qz) != AIR:
                    put(qx, yy, qz, AIR)
            if o and i % 4 == 0:
                for yy in range(deck - 6, deck):
                    if c.inside(qx, qz) and yy > c.surface(qx, qz) - 1 or c.is_water(qx, qz):
                        put(qx, yy, qz, "minecraft:stripped_spruce_log[axis=y]")
            if o:
                put(qx, deck + 1, qz, "minecraft:spruce_fence")
                if i % 8 == 0:
                    put(qx, deck + 2, qz, "minecraft:lantern[hanging=false]")
    # the gazebo platform
    gx = lx
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            d = math.hypot(dx, dz)
            if d <= 6.5:
                put(gx + dx, deck, lz + dz, "minecraft:stripped_spruce_wood[axis=y]" if d > 5.5 else "minecraft:spruce_planks")
                for yy in range(deck + 1, deck + 7):
                    put(gx + dx, yy, lz + dz, AIR)
                if 5.5 < d and not (dx > 0 and abs(dz) <= 1):
                    put(gx + dx, deck + 1, lz + dz, "minecraft:spruce_fence")
            if 5.5 < d <= 6.5 and (dx + dz) % 3 == 0:
                for yy in range(deck - 6, deck):
                    put(gx + dx, yy, lz + dz, "minecraft:stripped_spruce_log[axis=y]")
    for dx, dz in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
        for yy in range(deck + 1, deck + 5):
            put(gx + dx, yy, lz + dz, "minecraft:stripped_spruce_log[axis=y]")
    gb = arch.Bld(c, gx - 3, deck, lz + 3, "south")
    gb.hip_roof(0, 6, 0, 6, 5, "mcwroofs:spruce_roof", "minecraft:spruce_planks")
    hang_lantern(b, gx, deck + 8, -lz, 3)
    npc(arch.Bld(c, gx, deck, lz, "east"), 0, 1, 0, "alola:lana")
    for dz in (-4, 4):
        arch.Bld(c, gx - 4, deck, lz + dz, "south").piece(0, 1, 0, "bench", "east")
    # the bluff and waterfall on the north shore
    bz = lz - rz - 1
    for dx in range(-10, 11):
        for dz in range(-8, 2):
            xx, zz = lx + dx, bz + dz
            if not c.inside(xx, zz):
                continue
            h = int(10 - abs(dx) * 0.35 - max(0, dz) * 3 + rng.random() * 2)
            if h <= 0:
                continue
            base = c.surface(xx, zz)
            for yy in range(min(base, level - 3), level + h):
                put(xx, yy, zz, pick(rng, [("minecraft:stone", 4), ("minecraft:andesite", 2), ("minecraft:mossy_cobblestone", 2),
                                           ("minecraft:cobblestone", 1)]))
            put(xx, level + h, zz, pick(rng, [("minecraft:moss_block", 3), ("minecraft:grass_block", 2)]))
            if rng.random() < 0.4:
                put(xx, level + h + 1, zz, pick(rng, LUSH))
    top = level + 8
    for dx in (-1, 0, 1):                             # the pool on top and the falls
        for dz in range(-5, 1):
            put(lx + dx, top, bz + dz, "minecraft:water")
            put(lx + dx, top - 1, bz + dz, "minecraft:stone")
            for yy in range(top + 1, top + 4):
                put(lx + dx, yy, bz + dz, AIR)
        for yy in range(level + 1, top + 1):
            put(lx + dx, yy, bz + 1, "minecraft:water[level=8]" if yy < top else "minecraft:water")
        put(lx + dx, top, bz + 1, "minecraft:water")
    for dx in (-2, 2):
        for dz in range(-5, 2):
            if get(lx + dx, top, bz + dz) == AIR:
                put(lx + dx, top, bz + dz, "minecraft:mossy_cobblestone")
    # lily pads, flowering lilies on the water
    for dx in range(-rx, rx + 1):
        for dz in range(-rz, rz + 1):
            xx, zz = lx + dx, lz + dz
            if c.inside(xx, zz) and c.is_water(xx, zz) and get(xx, level + 1, zz) == AIR and rng.random() < 0.035:
                put(xx, level + 1, zz, "wilderwild:flowering_lily_pad" if rng.random() < 0.4 else "minecraft:lily_pad")
    from .special import trial_gate
    trial_gate(c, x - 3, c.surface(x, z - 2), z - 2, "south", rng, "Captain Lana")


# ======================================================================= Wela Volcano Park: Kiawe's stage

def kiawe_stage(c: Canvas, x, y, z, facing, rng: random.Random):
    """Kiawe's fire-dance stage on the crater rim: a round basalt stage ringed with magma and fire braziers,
    stepped seating and a railing looking into the crater."""
    b = arch.Bld(c, x, y, z, facing)
    R = 8
    W = D = 2 * R + 7
    cu = cw = W // 2
    b.clear_above(-2, -4, W + 1, D + 1, 20)
    b.foundation(-2, -4, W + 1, D + 1, "minecraft:blackstone")
    for u in range(-2, W + 2):
        for w in range(-4, D + 2):
            b.set(u, 0, w, pick(rng, [("minecraft:smooth_basalt", 3), ("minecraft:blackstone", 2), ("minecraft:tuff", 1)]))
    for du in range(-R - 1, R + 2):
        for dw in range(-R - 1, R + 2):
            d = math.hypot(du, dw)
            if d <= R:
                b.set(cu + du, 1, cw + dw, "minecraft:magma_block" if R - 1 < d else
                      "minecraft:polished_blackstone_bricks" if d > 3 else "minecraft:gilded_blackstone" if d > 2
                      else "minecraft:polished_blackstone")
    for k in range(6):
        a = math.radians(k * 60 + 30)
        pu, pw = cu + int(round(math.cos(a) * (R + 1))), cw + int(round(math.sin(a) * (R + 1)))
        for v in range(1, 5):
            b.set(pu, v, pw, "minecraft:polished_basalt[axis=y]")
        b.set(pu, 5, pw, "minecraft:campfire[lit=true]")
    for k in range(3):                                 # stepped seats on the approach side
        for du in range(-6, 7):
            w = -1 - k
            for v in range(1, k + 1):
                b.set(cu + du, v, w, "minecraft:polished_blackstone")
    for du in range(-6, 7):
        b.set(cu + du, 1, -1, stair("minecraft:polished_blackstone_stairs", "south"))
    for du in range(-3, 4):
        b.set(cu + du, 1, cw - R - 1, stair("minecraft:polished_blackstone_brick_stairs", "south"))
    npc(b, cu, 2, cw + 2, "alola:kiawe")
    b.sign(cu - 4, 1, -3, ["Wela Volcano Park", "", "Captain Kiawe's", "Trial"], wood="crimson", wall=False)
    return W, D


# ======================================================================= Lush Jungle: Mallow's kitchen

def mallow_kitchen(c: Canvas, x, y, z, facing, rng: random.Random):
    """A clearing in the Lush Jungle: Mallow's open-air kitchen under a thatched roof (stove, cauldron,
    barrels of ingredients, a long table), ringed by three great jungle trees with cocoa and vines."""
    b = arch.Bld(c, x, y, z, facing)
    W = D = 29
    cu = cw = W // 2
    b.clear_above(-4, -4, W + 3, D + 3, 40)
    b.foundation(-4, -4, W + 3, D + 3, "minecraft:dirt")
    ground_cover(b, -4, -4, W + 3, D + 3, rng, [("minecraft:grass_block", 4), ("minecraft:moss_block", 3),
                                                ("minecraft:podzol", 2), ("minecraft:rooted_dirt", 1)])
    for w in range(-4, cw):                         # trail in
        for du in (-1, 0, 1):
            b.set(cu + du, 0, w, "minecraft:dirt_path" if rng.random() < 0.8 else "minecraft:coarse_dirt")
    # the kitchen
    k1, k2, kw1, kw2 = cu - 5, cu + 5, cw, cw + 7
    for u in range(k1, k2 + 1):
        for w in range(kw1, kw2 + 1):
            b.set(u, 0, w, "minecraft:stripped_jungle_wood[axis=y]" if u in (k1, k2) or w in (kw1, kw2) else "minecraft:jungle_planks")
    for u, w in ((k1, kw1), (k2, kw1), (k1, kw2), (k2, kw2)):
        for v in range(1, 5):
            b.set(u, v, w, "minecraft:stripped_jungle_log[axis=y]")
    b.hip_roof(k1, k2, kw1, kw2, 5, "beachparty:thatch_stairs", "beachparty:thatch")
    for u in range(k1 + 1, k2):
        b.piece(u, 1, kw2 - 1, "counter", "south")
    b.set(cu - 2, 1, kw2 - 1, "minecraft:smoker[facing=south]")
    b.set(cu, 1, kw2 - 1, "minecraft:water_cauldron[level=3]")
    b.set(cu + 1, 1, kw2 - 2, "minecraft:campfire[lit=true]")
    b.set(cu + 2, 1, kw2 - 1, "minecraft:barrel[facing=up]")
    for w in range(kw1 + 2, kw2 - 2):
        b.set(k1 + 1, 1, w, "minecraft:barrel[facing=east]")
        b.set(k1 + 1, 2, w, pick(rng, [("minecraft:melon", 1), ("minecraft:pumpkin", 1), ("minecraft:hay_block[axis=y]", 1)]))
    for u in range(cu - 2, cu + 3):
        b.piece(u, 1, kw1 + 2, "table")
        b.piece(u, 1, kw1 + 1, "chair", "north")
    b.set(cu - 1, 2, kw1 + 2, "minecraft:cake")
    hang_lantern(b, cu, 5, kw1 + 3, 2)
    npc(b, cu, 1, kw1 + 4, "alola:mallow")
    b.sign(cu + 2, 1, -2, ["Lush Jungle", "", "Captain Mallow's", "Trial"], wood="jungle", wall=False)
    from .special import trial_gate
    trial_gate(c, *b.world(cu - 3, 0, -4), facing, rng, "Captain Mallow")
    # three great jungle trees round the clearing
    for (tu, tw) in ((3, 6), (W - 4, 8), (cu - 9, D - 3)):
        h = rng.randint(20, 26)
        for v in range(1, h):
            for du in (0, 1):
                for dw in (0, 1):
                    b.set(tu + du, v, tw + dw, "minecraft:jungle_log[axis=y]")
        for du, dw, face in ((-1, 0, "east"), (2, 1, "west"), (0, -1, "north"), (1, 2, "south")):
            for v in range(3, h - 4, 3):
                if rng.random() < 0.35:
                    b.set(tu + du, v, tw + dw, f"minecraft:cocoa[age=2,facing={face}]")
                elif rng.random() < 0.4:
                    wall_vines(b, tu + du, v + 2, tw + dw, face, 3)
        for k in range(4):                           # buttress roots
            du, dw = ((-1, 0), (2, 1), (1, -1), (0, 2))[k]
            b.set(tu + du, 1, tw + dw, "minecraft:jungle_wood[axis=y]")
        for (lu, lv, lw, r) in ((tu, h, tw, 5.5), (tu + 3, h - 4, tw + 2, 3.5), (tu - 3, h - 6, tw - 1, 3.5)):
            ri = int(r) + 1
            for du in range(-ri, ri + 1):
                for dv in range(-2, 3):
                    for dw in range(-ri, ri + 1):
                        d = math.sqrt(du * du + (dv * 1.8) ** 2 + dw * dw)
                        if d <= r and (d < r - 1 or rng.random() < 0.6) and b.get(lu + du, lv + dv, lw + dw) == AIR:
                            b.set(lu + du, lv + dv, lw + dw, "minecraft:jungle_leaves[persistent=true]")
            for _ in range(int(r * 2)):
                du, dw = rng.randint(-int(r) + 1, int(r) - 1), rng.randint(-int(r) + 1, int(r) - 1)
                if "leaves" in b.get(lu + du, lv - 2, lw + dw) and b.get(lu + du, lv - 3, lw + dw) == AIR:
                    glow_vines(b, lu + du, lv - 2, lw + dw, rng.randint(2, 6), rng)
    # undergrowth: ferns, dripleaf, bamboo clumps
    for u in range(-4, W + 4):
        for w in range(-4, D + 4):
            if k1 - 1 <= u <= k2 + 1 and kw1 - 1 <= w <= kw2 + 1 or abs(u - cu) <= 1 and w < cw:
                continue
            r = rng.random()
            if r < 0.3:
                plant_on(b, u, 0, w, rng, LUSH + [("minecraft:big_dripleaf[facing=south]", 1)])
            elif r < 0.33 and b.get(u, 1, w) == AIR:
                for v in range(1, rng.randint(4, 9)):
                    b.set(u, v, w, "minecraft:bamboo[age=1,leaves=large,stage=0]")
    return W, D


# ======================================================================= Paniola Ranch

def gambrel_barn(b: arch.Bld, u0, w0, W, D, rng):
    """A red barn with white trim, big doors front and back, a gambrel roof and a hay loft."""
    H = 6
    for u in range(u0, u0 + W):
        for w in range(w0, w0 + D):
            b.set(u, 0, w, "minecraft:coarse_dirt" if 0 < u - u0 < W - 1 and 0 < w - w0 < D - 1 else "minecraft:cobblestone")
            wall = u in (u0, u0 + W - 1) or w in (w0, w0 + D - 1)
            for v in range(1, H + 1):
                if wall:
                    corner = u in (u0, u0 + W - 1) and w in (w0, w0 + D - 1)
                    b.set(u, v, w, "minecraft:stripped_birch_log[axis=y]" if corner or (w - w0) % 4 == 0 and u in (u0, u0 + W - 1)
                          else "minecraft:red_terracotta")
                else:
                    b.set(u, v, w, AIR)
    for w in (w0, w0 + D - 1):                        # doors with a white X brace
        mu = u0 + W // 2
        for u in range(mu - 2, mu + 3):
            for v in range(1, 5):
                b.set(u, v, w, "minecraft:white_terracotta" if abs(u - mu) == abs(v - 2.5) - 0.5 or u in (mu - 2, mu + 2)
                      or v == 4 else "minecraft:red_terracotta")
        for v in (1, 2, 3):
            b.set(mu, v, w, AIR), b.set(mu - 1, v, w, AIR), b.set(mu + 1, v, w, AIR)
    # gambrel roof: steep lower slope then a shallow upper one, gable ends in red
    half = W // 2 + 1
    gable = (w0, w0 + D - 1)
    for w in range(w0 - 1, w0 + D + 1):
        for i in range(half + 1):
            lu, ru = u0 - 1 + i, u0 + W - i
            if lu > ru:
                break
            if i < 3:                                  # steep lower slope: stairs
                pv = H + 1 + i
                ls, rs = stair("minecraft:dark_oak_stairs", "east"), stair("minecraft:dark_oak_stairs", "west")
            else:                                      # shallow upper slope: alternating slabs
                pv = H + 4 + (i - 3) // 2
                top = (i - 3) % 2 == 1
                ls = rs = ("minecraft:dark_oak_planks" if w in gable else "minecraft:dark_oak_slab[type=top]") if top \
                    else "minecraft:dark_oak_slab[type=bottom]"
            if lu == ru:
                b.set(lu, pv, w, "minecraft:dark_oak_planks")
            else:
                b.set(lu, pv, w, ls)
                b.set(ru, pv, w, rs)
            if w in gable:                             # red gable ends under the roof
                for vv in range(H + 1, pv):
                    for uu in range(lu + 1, ru):
                        if b.get(uu, vv, w) == AIR:
                            b.set(uu, vv, w, "minecraft:red_terracotta")
    # the loft: planks at v=H with hay, a hay door at the front gable
    for u in range(u0 + 1, u0 + W - 1):
        for w in range(w0 + 1, w0 + D // 2):
            b.set(u, H, w, "minecraft:spruce_planks")
            if rng.random() < 0.5:
                b.set(u, H + 1, w, "minecraft:hay_block[axis=x]")
    mu = u0 + W // 2
    b.set(mu, H + 2, w0, AIR), b.set(mu, H + 3, w0, AIR)
    # stalls down one side with hay
    for w in range(w0 + 2, w0 + D - 2, 3):
        for du in range(1, 4):
            b.set(u0 + du, 1, w, "minecraft:spruce_fence")
        b.set(u0 + 1, 1, w + 1, "minecraft:hay_block[axis=y]")
        b.set(u0 + 2, 1, w + 1, "minecraft:water_cauldron[level=3]") if rng.random() < 0.5 else None
    hang_lantern(b, mu, H, w0 + D // 2 + 2, 2)


def paniola_ranch(c: Canvas, x, y, z, facing, rng: random.Random):
    """Paniola Ranch: a red gambrel barn, a ranch house with a porch, a silo, a water tower, stables and
    paddocks with troughs and hay bales where Mudbray and Tauros graze."""
    b = arch.Bld(c, x, y, z, facing)
    W, D = 71, 48
    b.clear_above(-2, -2, W + 1, D + 1, 30)
    gambrel_barn(b, 4, 4, 15, 21, rng)
    # silo beside the barn
    for v in range(1, 16):
        b.cylinder(22, 10, v, v, 3.2, "minecraft:light_gray_terracotta" if v % 4 else "minecraft:white_terracotta")
    b.dome(22, 10, 16, 3.2, "minecraft:red_terracotta")
    # ranch house
    arch.build_house(c, *b.world(30, 0, 6), facing, rng, style="paniola", W=13, D=9, floors=2, label="Paniola Ranch",
                     beds=2, yard=False)
    # water tower on stilts
    for du, dw in ((0, 0), (4, 0), (0, 4), (4, 4)):
        for v in range(1, 9):
            b.set(50 + du, v, 6 + dw, "minecraft:spruce_log[axis=y]")
    for du in range(-1, 6):
        for dw in range(-1, 6):
            if math.hypot(du - 2, dw - 2) <= 3.3:
                b.set(50 + du, 9, 6 + dw, "minecraft:spruce_planks")
                if math.hypot(du - 2, dw - 2) > 2.3:
                    for v in range(10, 14):
                        b.set(50 + du, v, 6 + dw, "minecraft:spruce_planks" if v % 2 else "minecraft:stripped_spruce_wood[axis=y]")
                else:
                    b.set(50 + du, 13, 6 + dw, "minecraft:water")
    b.hip_roof(47, 55, 3, 11, 14, "minecraft:spruce_stairs", "minecraft:spruce_planks")
    # stables: a row of open stalls under a lean-to
    for k in range(6):
        u = 44 + k * 4
        for v in range(1, 5):
            b.set(u, v, 18, "minecraft:stripped_spruce_log[axis=y]")
        for w in range(19, 23):
            b.set(u, 1, w, "minecraft:spruce_fence")
        b.set(u + 2, 1, 22, "minecraft:hay_block[axis=y]")
    for u in range(43, 69):
        for w in range(18, 24):
            b.set(u, 5 if w < 21 else 4, w, "minecraft:spruce_slab[type=bottom]")
        b.set(u, 1, 23, "minecraft:spruce_planks"), b.set(u, 2, 23, "minecraft:spruce_planks"), b.set(u, 3, 23, "minecraft:spruce_planks")
    # paddocks with gates, troughs and hay bales
    for (p1, q1, p2, q2) in ((2, 28, 32, 46), (36, 28, 68, 46)):
        for u in range(p1, p2 + 1):
            for w in (q1, q2):
                b.set(u, 1, w, "minecraft:spruce_fence_gate[facing=north]" if u == (p1 + p2) // 2 and w == q1 else "minecraft:spruce_fence")
        for w in range(q1, q2 + 1):
            b.set(p1, 1, w, "minecraft:spruce_fence"), b.set(p2, 1, w, "minecraft:spruce_fence")
        for k in range(3):
            tu = p1 + 4 + k * 3
            b.set(tu, 1, q2 - 2, "minecraft:water_cauldron[level=3]")
        for _ in range(6):
            b.set(rng.randint(p1 + 2, p2 - 2), 1, rng.randint(q1 + 2, q2 - 4), "minecraft:hay_block[axis=" + rng.choice("xz") + "]")
    b.sign(20, 1, -1, ["Paniola Ranch", "", "Mudbray, Tauros", "& Miltank"], wood="spruce", wall=False)
    for u in range(-1, W + 1, 12):
        b.set(u, 1, 26, "minecraft:spruce_fence"), b.set(u, 2, 26, "minecraft:lantern[hanging=false]")
    from .buildings import setup_cmd
    for k in range(8):                                  # the ranch's Pokémon
        setup_cmd(b, 6 + k * 8, 1, 37, "spawnpokemonat {xc} {y} {zc} "
                  + ["mudbray", "tauros", "miltank", "mudsdale"][k % 4] + " level=15")
    return W, D
