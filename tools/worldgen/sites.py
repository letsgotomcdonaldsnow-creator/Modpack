"""Alola's landmark sites, built with the building kit: the four Tapu ruins, the Battle Tree, Professor Kukui's
lab, the kahuna battle courts, Hokulani Observatory, the abandoned Thrifty Megamart and the Altar of the Sunne.

Every builder takes (c, x, y, z, facing, rng, ...) with (x, y, z) the front-left ground corner (v=0 is the ground
block) and returns the (W, D) it occupies, like the rest of the kit (see kit.py for the local u/v/w frame)."""
from __future__ import annotations

import math
import random

from . import arch, furn
from .buildings import merchant, npc, pokeball_disc, setup_cmd
from .canvas import Canvas

pick = arch.pick
AIR = "minecraft:air"


def stair(state, facing, half="bottom"):
    return f"{state}[facing={facing},half={half},shape=straight]"


def tall(b, u, v, w, name):
    furn.place_tall(b.c, *b.world(u, v, w), name)


def hang_lantern(b, u, v, w, drop=2, soul=False):
    """A lantern on a chain below (u, v, w), the block it hangs from."""
    for k in range(1, drop):
        b.set(u, v - k, w, "minecraft:chain[axis=y]")
    b.set(u, v - drop, w, f"minecraft:{'soul_' if soul else ''}lantern[hanging=true]")


def glow_vines(b, u, v, w, length, rng):
    """Glow-berry vines hanging below the block at (u, v, w)."""
    for k in range(1, length):
        if b.get(u, v - k, w) != AIR:
            return
        b.set(u, v - k, w, f"minecraft:cave_vines_plant[berries={'true' if rng.random() < 0.25 else 'false'}]")
    if b.get(u, v - length, w) == AIR:
        b.set(u, v - length, w, f"minecraft:cave_vines[age=25,berries={'true' if rng.random() < 0.4 else 'false'}]")


def wall_vines(b, u, v, w, face, length):
    """Vines hanging down the wall face that lies to the `face` side (local compass) of (u, v, w)."""
    for k in range(length):
        if b.get(u, v - k, w) != AIR:
            return
        b.set(u, v - k, w, f"minecraft:vine[{face}=true]")


def ground_cover(b, u1, w1, u2, w2, rng, mix):
    for u in range(u1, u2 + 1):
        for w in range(w1, w2 + 1):
            b.set(u, 0, w, pick(rng, mix))


def plant_on(b, u, v, w, rng, plants):
    """A small plant on top of the block at (u, v, w) when that block can hold it."""
    below = b.get(u, v, w).split("[")[0]
    if below in ("minecraft:grass_block", "minecraft:moss_block", "minecraft:podzol", "minecraft:rooted_dirt",
                 "minecraft:coarse_dirt", "minecraft:dirt") and b.get(u, v + 1, w) == AIR:
        b.set(u, v + 1, w, pick(rng, plants))


LUSH = [("minecraft:fern", 4), ("minecraft:short_grass", 5), ("minecraft:azalea", 1), ("minecraft:flowering_azalea", 1),
        ("minecraft:moss_carpet", 2)]


# ======================================================================= Tapu ruins

RUINS = {
    "koko": dict(
        stone=[("minecraft:stone_bricks", 6), ("minecraft:mossy_stone_bricks", 4), ("minecraft:cracked_stone_bricks", 2)],
        chisel="minecraft:chiseled_stone_bricks", stair="minecraft:stone_brick_stairs",
        mstair="minecraft:mossy_stone_brick_stairs", slab="minecraft:stone_brick_slab", wall="minecraft:mossy_stone_brick_wall",
        floor=[("minecraft:polished_andesite", 4), ("minecraft:andesite", 2), ("minecraft:mossy_cobblestone", 1),
               ("minecraft:moss_block", 1)],
        path="minecraft:smooth_stone", inlay="minecraft:chiseled_stone_bricks",
        band=("minecraft:yellow_terracotta", "minecraft:black_terracotta"),
        emblem=("minecraft:yellow_concrete", "minecraft:black_concrete", "minecraft:orange_concrete"),
        leaves=[("minecraft:jungle_leaves[persistent=true]", 3), ("minecraft:azalea_leaves[persistent=true]", 1)],
        flowers=[("minecraft:orange_tulip", 1), ("wilderwild:yellow_hibiscus", 1), ("minecraft:dandelion", 1)],
        soul=False),
    "lele": dict(
        stone=[("minecraft:polished_diorite", 4), ("minecraft:diorite", 2), ("minecraft:calcite", 2)],
        chisel="minecraft:chiseled_quartz_block", stair="minecraft:polished_diorite_stairs",
        mstair="minecraft:diorite_stairs", slab="minecraft:polished_diorite_slab", wall="minecraft:diorite_wall",
        floor=[("minecraft:polished_diorite", 3), ("minecraft:smooth_quartz", 1), ("minecraft:calcite", 1),
               ("minecraft:moss_block", 1)],
        path="minecraft:smooth_quartz", inlay="minecraft:pink_glazed_terracotta",
        band=("minecraft:pink_terracotta", "minecraft:white_terracotta"),
        emblem=("minecraft:pink_concrete", "minecraft:white_concrete", "minecraft:magenta_concrete"),
        leaves=[("minecraft:cherry_leaves[persistent=true]", 2), ("minecraft:flowering_azalea_leaves[persistent=true]", 1)],
        flowers=[("minecraft:pink_tulip", 1), ("wilderwild:pink_hibiscus", 1), ("minecraft:allium", 1)],
        soul=False),
    "bulu": dict(
        stone=[("minecraft:mud_bricks", 5), ("minecraft:packed_mud", 2), ("minecraft:granite", 1)],
        chisel="minecraft:polished_granite", stair="minecraft:mud_brick_stairs",
        mstair="minecraft:granite_stairs", slab="minecraft:mud_brick_slab", wall="minecraft:mud_brick_wall",
        floor=[("minecraft:polished_granite", 3), ("minecraft:packed_mud", 1), ("minecraft:coarse_dirt", 1),
               ("minecraft:moss_block", 1)],
        path="minecraft:smooth_red_sandstone", inlay="minecraft:red_glazed_terracotta",
        band=("minecraft:red_terracotta", "minecraft:black_terracotta"),
        emblem=("minecraft:red_concrete", "minecraft:black_concrete", "minecraft:brown_concrete"),
        leaves=[("minecraft:oak_leaves[persistent=true]", 2), ("minecraft:dark_oak_leaves[persistent=true]", 1)],
        flowers=[("minecraft:red_tulip", 1), ("wilderwild:red_hibiscus", 1), ("minecraft:poppy", 1)],
        soul=False),
    "fini": dict(
        stone=[("minecraft:deepslate_bricks", 5), ("minecraft:cracked_deepslate_bricks", 2), ("minecraft:deepslate_tiles", 2)],
        chisel="minecraft:chiseled_deepslate", stair="minecraft:deepslate_brick_stairs",
        mstair="minecraft:deepslate_tile_stairs", slab="minecraft:deepslate_brick_slab", wall="minecraft:deepslate_brick_wall",
        floor=[("minecraft:polished_deepslate", 3), ("minecraft:deepslate_tiles", 1), ("minecraft:moss_block", 1)],
        path="minecraft:dark_prismarine", inlay="minecraft:prismarine_bricks",
        band=("minecraft:light_blue_terracotta", "minecraft:purple_terracotta"),
        emblem=("minecraft:light_blue_concrete", "minecraft:purple_concrete", "minecraft:blue_concrete"),
        leaves=[("minecraft:azalea_leaves[persistent=true]", 2), ("minecraft:flowering_azalea_leaves[persistent=true]", 1)],
        flowers=[("minecraft:blue_orchid", 1), ("minecraft:cornflower", 1), ("wilderwild:purple_hibiscus", 1)],
        soul=True),
}

# The guardian's shell, carved into the sanctum's back wall: # dark, a main colour, A accent, . bare wall.
EMBLEMS = {
    "koko": ["....#.#....",
             "...##.##...",
             "..#aaaaa#..",
             ".#aaAAAaa#.",
             "#aaA.#.Aaa#",
             "#aaA...Aaa#",
             ".#aaAAAaa#.",
             "..#aaaaa#..",
             "....#a#...."],
    "lele": ["...#####...",
             "..#aaaaa#..",
             ".#aAAAAAa#.",
             "#aA.....Aa#",
             "#aA..#..Aa#",
             "#aaA...Aaa#",
             ".#aaAAAaa#.",
             "#a#aaaaa#a#",
             "##.#####.##"],
    "bulu": ["#.........#",
             "##.......##",
             ".##aaaaa##.",
             "..aaAAAaa..",
             ".aaA.#.Aaa.",
             ".aaA...Aaa.",
             ".aaaAAAaaa.",
             "..#aaaaa#..",
             "...#####..."],
    "fini": ["....###....",
             "...#aaa#...",
             "..#aAAAa#..",
             "##aA...Aa##",
             "#aaA.#.Aaa#",
             "##aA...Aa##",
             "..#aAAAa#..",
             "...#aaa#...",
             "....###...."],
}


def tapu_ruins(c: Canvas, x, y, z, facing, rng: random.Random, tapu="koko", name="Ruins of Conflict"):
    """A guardian's shrine: a stone plinth reached by a stair, a gate, a half-fallen colonnade and a roofed
    sanctum whose back wall carries the Tapu's shell above a stepped dais. Overgrown and weathered."""
    p = RUINS[tapu]
    b = arch.Bld(c, x, y, z, facing)
    W, D, P = 27, 46, 5
    cu = W // 2
    G = P + 1                                    # standing level on the plinth
    base_stone = p["stone"][0][0]

    def S():
        return pick(rng, p["stone"])

    def rubble(u0, w0, n, keep_clear=(9, 17)):
        for _ in range(n):
            u, w = u0 + rng.randint(-3, 3), w0 + rng.randint(-3, 3)
            if keep_clear[0] <= u <= keep_clear[1] or b.get(u, G, w) != AIR or b.get(u, P, w) == AIR:
                continue
            r = rng.random()
            b.set(u, G, w, S() if r < 0.3 else
                  stair(p["mstair"], rng.choice(["north", "south", "east", "west"])) if r < 0.6 else
                  f"{p['slab']}[type=bottom]" if r < 0.8 else "minecraft:moss_carpet")

    b.clear_above(-3, -10, W + 2, D + 2, 40)
    b.foundation(-3, -10, W + 2, D + 2, "minecraft:dirt")
    ground_cover(b, -3, -10, W + 2, D + 2, rng, [("minecraft:grass_block", 6), ("minecraft:moss_block", 2),
                                                  ("minecraft:coarse_dirt", 1), ("minecraft:rooted_dirt", 1)])
    # ---- the plinth: pilasters every four blocks, a projecting lip at floor level
    for u in range(-1, W + 1):
        for w in range(-1, D + 1):
            edge = u in (-1, W) or w in (-1, D)
            for v in range(0, P):
                if edge:
                    pil = (u % 4 == 1 and w in (-1, D)) or (w % 4 == 1 and u in (-1, W))
                    b.set(u, v, w, p["chisel"] if pil and v in (0, P - 1) else S())
                else:
                    b.set(u, v, w, base_stone)
            b.set(u, P, w, pick(rng, p["floor"]))
    for u in range(-2, W + 2):
        if not 7 <= u <= W - 8:
            b.set(u, P, -2, stair(p["stair"], "north", "top"))
        b.set(u, P, D + 1, stair(p["stair"], "south", "top"))
    for w in range(-1, D + 1):
        b.set(-2, P, w, stair(p["stair"], "east", "top"))
        b.set(W + 1, P, w, stair(p["stair"], "west", "top"))
    # ---- the approach stair with stepped cheek walls and lantern posts at the foot
    for k in range(1, P + 1):
        w = k - P - 2
        for u in range(8, W - 8):
            for v in range(0, k):
                b.set(u, v, w, base_stone)
            b.set(u, k, w, stair(p["stair"] if (u + k) % 3 else p["mstair"], "north"))
        for u in (7, W - 8):
            for v in range(0, k + 1):
                b.set(u, v, w, S())
            b.set(u, k + 1, w, f"{p['slab']}[type=bottom]")
    for u in (7, W - 8):
        b.set(u, 1, -P - 2, S()), b.set(u, 2, -P - 2, p["chisel"])
        b.set(u, 3, -P - 2, f"minecraft:{'soul_' if p['soul'] else ''}lantern[hanging=false]")
    for u in (5, W - 6):                        # braziers at the top of the stair
        b.set(u, G, 0, p["wall"])
        b.set(u, G + 1, 0, f"minecraft:{'soul_' if p['soul'] else ''}campfire[lit=true,facing=south]")
    b.sign(5, 1, -P - 3, [name, "", "Shrine of the guardian", f"Tapu {tapu.title()}"], wood="dark_oak", wall=False)
    # ---- the gate: two 3x3 pillars, a coloured tie beam and an upswept lintel
    for u0 in (5, W - 8):
        for du in range(3):
            for dw in range(3):
                for v in range(G, G + 9):
                    corner = du in (0, 2) and dw in (0, 2)
                    b.set(u0 + du, v, 1 + dw, p["chisel"] if v in (G, G + 8) and corner else S())
    for u in range(8, W - 8):
        b.set(u, G + 6, 2, p["band"][u % 2])
    for u in range(3, W - 3):
        for dw in range(3):
            b.set(u, G + 9, 1 + dw, S())
        if 4 <= u <= W - 5:
            b.set(u, G + 10, 2, f"{p['slab']}[type=bottom]")
    b.set(3, G + 10, 2, stair(p["stair"], "west")), b.set(W - 4, G + 10, 2, stair(p["stair"], "east"))
    main, dark, acc = p["emblem"]
    for du, s in ((-1, main), (0, acc), (1, main)):
        b.set(cu + du, G + 9, 0, s)
    b.set(cu, G + 10, 0, main)
    if rng.random() < 0.6:                      # one end of the lintel has fallen
        end = W - 5 if rng.random() < 0.5 else 3
        for u in range(end, end + 2):
            for dw in range(3):
                b.set(u, G + 9, 1 + dw, AIR)
            b.set(u, G + 10, 2, AIR)
        rubble(end, 5, 7)
    # ---- the colonnade: path, pillars (some broken), beams and hanging lanterns
    for w in range(4, 31):
        for u in range(10, W - 10):
            b.set(u, P, w, p["inlay"] if u in (10, W - 11) and w % 4 == 0 else p["path"])
    cols = [6, 12, 18, 24]
    for u0 in (4, W - 6):
        intact = []
        for w0 in cols:
            h = 9 if rng.random() > 0.3 else rng.randint(3, 6)
            intact.append(h == 9)
            for du in range(2):
                for dw in range(2):
                    for v in range(G, G + h):
                        b.set(u0 + du, v, w0 + dw, p["chisel"] if v == G or v == G + 8 else S())
                    if h < 9 and rng.random() < 0.5:
                        b.set(u0 + du, G + h, w0 + dw, stair(p["stair"], rng.choice(["north", "south", "east", "west"])))
            if h < 9:
                rubble(u0 + 1, w0 + 1, 8)
            for dw in range(2):
                if rng.random() < 0.5:
                    wall_vines(b, u0 - 1 if u0 < cu else u0 + 2, G + h - 1, w0 + dw,
                               "east" if u0 < cu else "west", rng.randint(2, h))
        for i in range(len(cols) - 1):
            wa, wb = cols[i], cols[i + 1]
            if intact[i] and intact[i + 1]:
                for w in range(wa, wb + 2):
                    for du in range(2):
                        b.set(u0 + du, G + 9, w, S())
            elif intact[i]:
                for w in range(wa + 2, wa + 4):
                    b.set(u0, G + 9, w, S())
    for w0 in cols:                             # cross beams where both sides still stand
        if b.get(4, G + 8, w0) != AIR and b.get(W - 6, G + 8, w0) != AIR:
            for u in range(4, W - 4):
                b.set(u, G + 9, w0, S())
                b.set(u, G + 9, w0 + 1, S())
            hang_lantern(b, cu, G + 9, w0, 3, p["soul"])
    # low outer walls with window gaps and missing sections
    for u in (0, W - 1):
        w = 4
        while w <= 30:
            if rng.random() < 0.15:
                b.set(u, G, w, S())
                w += rng.randint(2, 3)
                continue
            for v in range(G, G + 3):
                b.set(u, v, w, AIR if (w % 5 == 0 and v == G + 1) else S())
            b.set(u, G + 3, w, f"{p['slab']}[type=bottom]")
            w += 1
    # ---- the sanctum
    s1, s2, u1, u2, H = 31, D - 1, 3, W - 4, 12
    for u in range(u1, u2 + 1):
        for w in range(s1, s2 + 1):
            wall = u in (u1, u2) or w in (s1, s2)
            for v in range(G, G + H):
                b.set(u, v, w, S() if wall else AIR)
            b.set(u, G + H, w, S())
            if not wall:
                b.set(u, P, w, p["path"] if (u + w) % 2 else pick(rng, p["floor"][:2]))
    for u in range(u1, u2 + 1, 4):              # projecting pilasters on the front
        if abs(u - cu) <= 3:
            continue
        for v in range(G, G + H):
            b.set(u, v, s1 - 1, p["chisel"] if v in (G, G + H - 1) else S())
    for w in range(s1 + 2, s2, 4):              # and on the sides
        for v in range(G, G + H):
            b.set(u1 - 1, v, w, p["chisel"] if v in (G, G + H - 1) else S())
            b.set(u2 + 1, v, w, p["chisel"] if v in (G, G + H - 1) else S())
    for u in range(u1 - 1, u2 + 2):             # cornice and a crenellated parapet
        b.set(u, G + H, s1 - 1, stair(p["stair"], "north", "top"))
        b.set(u, G + H, s2 + 1, stair(p["stair"], "south", "top"))
        b.set(u, G + H + 1, s1, S() if u % 2 else f"{p['slab']}[type=bottom]")
        b.set(u, G + H + 1, s2, S() if u % 2 else f"{p['slab']}[type=bottom]")
    for w in range(s1, s2 + 1):
        b.set(u1 - 1, G + H, w, stair(p["stair"], "east", "top"))
        b.set(u2 + 1, G + H, w, stair(p["stair"], "west", "top"))
        b.set(u1, G + H + 1, w, S() if w % 2 else f"{p['slab']}[type=bottom]")
        b.set(u2, G + H + 1, w, S() if w % 2 else f"{p['slab']}[type=bottom]")
    # arched doorway with a keystone
    for u in range(cu - 2, cu + 3):
        for v in range(G, G + 6):
            b.set(u, v, s1, AIR)
    for u in range(cu - 1, cu + 2):
        b.set(u, G + 6, s1, AIR)
    b.set(cu - 2, G + 6, s1, stair(p["stair"], "west", "top"))
    b.set(cu + 2, G + 6, s1, stair(p["stair"], "east", "top"))
    b.set(cu, G + 7, s1, p["chisel"])
    for u in (cu - 4, cu + 4):
        b.set(u, G, s1 - 2, "minecraft:decorated_pot[facing=south]")
    # oculus over the dais, and a collapsed back corner
    oc = s2 - 7
    for du in range(-3, 4):
        for dw in range(-3, 4):
            if math.hypot(du, dw) <= 2.2:
                b.set(cu + du, G + H, oc + dw, AIR)
    kc = rng.choice([u1 + 3, u2 - 3])
    for du in range(-4, 5):
        for dw in range(-4, 5):
            d = math.hypot(du, dw)
            if d <= 3.6:
                for v in range(G + H - (2 if d < 2.5 else 1), G + H + 2):
                    if u1 <= kc + du <= u2 and s1 < s2 - 3 + dw <= s2:
                        b.set(kc + du, v, s2 - 3 + dw, AIR)
    for _ in range(14):
        u, w = kc + rng.randint(-3, 3), s2 - 3 + rng.randint(-3, 2)
        if u1 < u < u2 and s1 < w < s2 and b.get(u, G, w) == AIR:
            b.set(u, G, w, S() if rng.random() < 0.5 else stair(p["mstair"], rng.choice(["north", "east", "west"])))
    # inner columns
    for u in (u1 + 4, u2 - 4):
        for w in (s1 + 3, s1 + 7):
            for v in range(G, G + H):
                b.set(u, v, w, p["chisel"] if v in (G, G + H - 1) else S())
    # the stepped dais
    for w in range(s2 - 6, s2):
        for u in range(u1 + 3, u2 - 2):
            lvl = 1 + (w >= s2 - 4 and u1 + 5 <= u <= u2 - 5) + (w >= s2 - 2 and u1 + 7 <= u <= u2 - 7)
            front = {1: s2 - 6, 2: s2 - 4, 3: s2 - 2}[lvl] == w
            for v in range(G, G + lvl):
                top = v == G + lvl - 1
                if top and front:
                    b.set(u, v, w, stair(p["stair"], "north"))
                else:
                    b.set(u, v, w, p["path"] if top else S())
    b.set(cu, G + 3, s2 - 1, p["chisel"])
    b.set(cu, G + 4, s2 - 1, "minecraft:decorated_pot[facing=south]")
    for du in (-2, 2):
        b.set(cu + du, G + 3, s2 - 1, "minecraft:candle[candles=3,lit=true]")
    for u in (u1 + 3, u2 - 3):
        b.set(u, G + 1, s2 - 5, f"minecraft:{'soul_' if p['soul'] else ''}campfire[lit=true,facing=north]")
    # the guardian's shell on the back wall
    colour = {"#": dark, "a": main, "A": acc}
    rows = EMBLEMS[tapu]
    for r, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in colour:
                b.set(cu - 5 + i, G + 11 - r, s2, colour[ch])
    hang_lantern(b, cu, G + H - 1, s1 + 3, 3, p["soul"])
    hang_lantern(b, cu, G + H - 1, s1 + 7, 3, p["soul"])
    # ---- overgrowth: moss on the floors, leaves spilling over the walls, vines, a planted apron
    for u in range(0, W):
        for w in range(0, D):
            if b.get(u, G, w) == AIR and b.get(u, P, w) != AIR and rng.random() < 0.1 and not 10 <= u <= W - 11:
                b.set(u, G, w, "minecraft:moss_carpet")
    for _ in range(26):
        side = rng.randrange(3)
        if side == 0:
            u, w = rng.choice([u1, u2]), rng.randint(s1, s2)
        elif side == 1:
            u, w = rng.randint(u1, u2), s2
        else:
            u, w = rng.randint(u1, u2), s1
        if b.get(u, G + H + 1, w) == AIR and b.get(u, G + H, w) == AIR:
            continue
        for du in (-1, 0, 1):
            for dw in (-1, 0, 1):
                if rng.random() < 0.6 and b.get(u + du, G + H + 1, w + dw) == AIR:
                    b.set(u + du, G + H + 1, w + dw, pick(rng, p["leaves"]))
        if u == u1:
            wall_vines(b, u1 - 1, G + H - 1, w, "east", rng.randint(3, 9))
        elif u == u2:
            wall_vines(b, u2 + 1, G + H - 1, w, "west", rng.randint(3, 9))
        elif w == s2:
            wall_vines(b, u, G + H - 1, s2 + 1, "south", rng.randint(3, 9))
    for u in range(-3, W + 3):
        for w in range(-10, D + 3):
            if -1 <= u <= W and -1 <= w <= D or (7 <= u <= W - 8 and w >= -P - 3):
                continue
            if rng.random() < 0.35:
                plant_on(b, u, 0, w, rng, LUSH + [(f, 1) for f, _ in p["flowers"]])
    for u, w in ((-3, -3), (W + 2, -3), (-3, D + 2), (W + 2, D + 2)):
        for du in (-1, 0, 1):
            for dw in (-1, 0, 1):
                for dv in (1, 2):
                    if rng.random() < 0.7 - 0.3 * dv:
                        b.set(u + du, dv, w + dw, pick(rng, p["leaves"]))
    return W, D


# ======================================================================= Battle Tree

TREE_LEAVES = [("minecraft:jungle_leaves[persistent=true]", 6), ("minecraft:azalea_leaves[persistent=true]", 2),
               ("minecraft:flowering_azalea_leaves[persistent=true]", 1)]
BARK = "minecraft:jungle_wood[axis=y]"


def battle_tree(c: Canvas, x, y, z, facing, rng: random.Random):
    """The Battle Tree: a giant jungle tree with buttress roots and a crown of leaf clouds hung with glow
    berries. A timber deck wraps the trunk; on it a battle court, stands, and a hall carved into the trunk
    with a Pokémon Center counter and the Battle Point exchange. Red and Blue wait by the court."""
    b = arch.Bld(c, x, y, z, facing)
    W, D = 61, 64
    cu, cw, TR = 30, 44, 7.5
    DV = 8                                        # deck floor level
    TOP = 50
    b.clear_above(-3, -14, W + 2, D + 2, 100)
    b.foundation(-3, -14, W + 2, D + 2, "minecraft:dirt")
    ground_cover(b, -3, -14, W + 2, D + 2, rng, [("minecraft:grass_block", 6), ("minecraft:moss_block", 2),
                                                  ("minecraft:podzol", 1), ("minecraft:rooted_dirt", 1)])

    def trunk_r(v):
        return TR * (1 - max(v, 0) / 95)

    # trunk with twisting bark ridges
    for v in range(-3, TOP):
        r = trunk_r(v)
        ri = int(r) + 2
        for du in range(-ri, ri + 1):
            for dw in range(-ri, ri + 1):
                a = math.atan2(dw, du)
                if math.hypot(du, dw) <= r + 0.7 * math.sin(5 * a + v * 0.15):
                    b.set(cu + du, v, cw + dw, BARK)
    # buttress roots
    for i in range(9):
        a = math.radians(i * 40 + rng.uniform(-12, 12))
        L = rng.randint(11, 17)
        for s in range(L):
            d = TR - 1 + s
            h = int(round(9 * (1 - s / L) ** 1.6))
            pu, pw = cu + d * math.cos(a), cw + d * math.sin(a)
            wid = 1 if s < L * 0.6 else 0
            for o in range(-wid, wid + 1):
                ou, ow = int(round(pu - o * math.sin(a))), int(round(pw + o * math.cos(a)))
                for v in range(-1, h + 1 - abs(o)):
                    b.set(ou, v, ow, BARK)
                if rng.random() < 0.3 and b.get(ou, h + 1 - abs(o), ow) == AIR:
                    b.set(ou, h + 1 - abs(o), ow, "minecraft:moss_carpet")

    def limb(u0, v0, w0, a, elev, L, t):
        pu = pv = pw = 0.0
        for s in range(L):
            pu, pv, pw = u0 + s * math.cos(a), v0 + s * elev, w0 + s * math.sin(a)
            tt = t if s < L * 0.55 else max(0, t - 1)
            for du in range(-tt, tt + 1):
                for dv in range(-tt, tt + 1):
                    for dw in range(-tt, tt + 1):
                        if du * du + dv * dv + dw * dw <= tt * tt + 0.5:
                            b.set(int(round(pu)) + du, int(round(pv)) + dv, int(round(pw)) + dw, BARK)
        return int(round(pu)), int(round(pv)), int(round(pw))

    blobs = []

    def leaf_cloud(u0, v0, w0, r, squash=0.6):
        ri = int(r) + 1
        for du in range(-ri, ri + 1):
            for dv in range(-ri, ri + 1):
                for dw in range(-ri, ri + 1):
                    d = math.sqrt(du * du + (dv / squash) ** 2 + dw * dw)
                    if d <= r and (d < r - 1 or rng.random() < 0.55) and b.get(u0 + du, v0 + dv, w0 + dw) == AIR:
                        b.set(u0 + du, v0 + dv, w0 + dw, pick(rng, TREE_LEAVES))
        blobs.append((u0, v0, w0, r, squash))

    for i in range(7):
        a = math.radians(i * 360 / 7 + rng.uniform(-15, 15))
        v0 = rng.randint(26, 36)
        L = rng.randint(15, 21)
        eu, ev, ew = limb(cu, v0, cw, a, rng.uniform(0.35, 0.6), L, 1)
        leaf_cloud(eu, ev + 2, ew, rng.uniform(6.5, 8.5))
        mu, mv, mw = cu + 0.55 * L * math.cos(a), v0 + 0.55 * L * 0.45, cw + 0.55 * L * math.sin(a)
        su, sv, sw = limb(int(mu), int(mv), int(mw), a + rng.choice([-1, 1]) * math.radians(55), 0.3,
                          rng.randint(7, 10), 0)
        leaf_cloud(su, sv + 2, sw, rng.uniform(4.5, 5.5))
    leaf_cloud(cu, TOP + 2, cw, 11, 0.55)
    # glow berries hanging from the underside of every leaf cloud
    for (u0, v0, w0, r, sq) in blobs:
        for _ in range(int(r * 2.5)):
            du, dw = rng.randint(-int(r * 0.8), int(r * 0.8)), rng.randint(-int(r * 0.8), int(r * 0.8))
            for dv in range(-int(r * sq) - 1, 1):
                if "leaves" in b.get(u0 + du, v0 + dv, w0 + dw):
                    if b.get(u0 + du, v0 + dv - 1, w0 + dw) == AIR:
                        glow_vines(b, u0 + du, v0 + dv, w0 + dw, rng.randint(2, 7), rng)
                    break
    # ---- the deck: a terrace in front joined to a ring round the trunk
    TU1, TU2 = 12, W - 13

    def on_deck(u, w):
        return (TU1 <= u <= TU2 and 2 <= w <= cw) or math.hypot(u - cu, w - cw) <= TR + 6.5

    cells = [(u, w) for u in range(0, W) for w in range(0, D) if on_deck(u, w)]
    cellset = set(cells)
    for u, w in cells:
        edge = any((u + du, w + dw) not in cellset for du, dw in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if b.get(u, DV, w) == AIR:
            b.set(u, DV, w, "minecraft:stripped_jungle_log[axis=x]" if w % 6 == 0 else "minecraft:jungle_planks")
        if edge:
            if b.get(u, DV - 1, w) == AIR:
                b.set(u, DV - 1, w, "minecraft:stripped_jungle_wood[axis=y]")
            if (u + w) % 4 == 0:
                for v in range(1, DV - 1):
                    if b.get(u, v, w) == AIR:
                        b.set(u, v, w, "minecraft:stripped_jungle_log[axis=y]")
            stair_gap = w <= 3 and cu - 4 <= u <= cu + 4
            if not stair_gap and b.get(u, DV + 1, w) == AIR:
                b.set(u, DV + 1, w, "minecraft:jungle_fence")
                if (u + w) % 8 == 0:
                    b.set(u, DV + 1, w, "minecraft:stripped_jungle_log[axis=y]")
                    b.set(u, DV + 2, w, "minecraft:lantern[hanging=false]")
    # grand stair from the plaza
    for j in range(1, DV + 1):
        w = 1 - (DV - j)
        for u in range(cu - 4, cu + 5):
            for v in range(1, j):
                b.set(u, v, w, "minecraft:jungle_planks")
            b.set(u, j, w, stair("minecraft:jungle_stairs", "north"))
        for u in (cu - 5, cu + 5):
            for v in range(1, j + 1):
                b.set(u, v, w, "minecraft:stripped_jungle_wood[axis=y]")
            b.set(u, j + 1, w, "minecraft:jungle_fence")
    for u in (cu - 5, cu + 5):
        tall(b, u, 1, -DV, "tiki_torch")
    # the plaza and the path up to it
    for u in range(cu - 7, cu + 8):
        for w in range(-14, 2 - DV):
            b.set(u, 0, w, pick(rng, [("minecraft:packed_mud", 3), ("minecraft:coarse_dirt", 2), ("minecraft:dirt_path", 2),
                                      ("minecraft:mud_bricks", 1)]))
    for w in range(-13, 1 - DV, 4):
        tall(b, cu - 8, 1, w, "tiki_torch")
        tall(b, cu + 8, 1, w, "tiki_torch")
    b.sign(cu - 3, 1, -13, ["Battle Tree", "", "Poni Island", "Test your strength!"], wood="jungle", wall=False)
    # battle court on the terrace
    cu1, cu2, cw1, cw2 = cu - 9, cu + 9, 6, 28
    for u in range(cu1, cu2 + 1):
        for w in range(cw1, cw2 + 1):
            line = u in (cu1, cu2) or w in (cw1, cw2, (cw1 + cw2) // 2)
            box = (cu - 2 <= u <= cu + 2 and w in (cw1 + 2, cw1 + 4, cw2 - 4, cw2 - 2)) or \
                  (u in (cu - 2, cu + 2) and (cw1 + 2 <= w <= cw1 + 4 or cw2 - 4 <= w <= cw2 - 2))
            b.set(u, DV, w, "minecraft:white_concrete" if line or box else
                  "minecraft:dark_oak_planks" if (u // 3 + w // 3) % 2 else "minecraft:spruce_planks")
    pokeball_disc(b, cu, (cw1 + cw2) // 2, DV, 3)
    for w in range(cw1 + 2, cw2 - 1, 3):
        b.piece(cu1 - 3, DV + 1, w, "bench", "east")
        b.piece(cu2 + 3, DV + 1, w, "bench", "west")
    for (u, w) in ((cu1 - 1, cw1 - 1), (cu2 + 1, cw1 - 1), (cu1 - 1, cw2 + 1), (cu2 + 1, cw2 + 1)):
        tall(b, u, DV + 1, w, "street_lamp")
    # the hall inside the trunk
    hr = trunk_r(DV + 3) - 1.8
    for du in range(-7, 8):
        for dw in range(-7, 8):
            d = math.hypot(du, dw)
            if d <= hr:
                b.set(cu + du, DV, cw + dw, "minecraft:stripped_jungle_wood[axis=y]" if d > hr - 1 else "minecraft:jungle_planks")
                for v in range(DV + 1, DV + 7):
                    b.set(cu + du, v, cw + dw, AIR)
    pokeball_disc(b, cu, cw - 2, DV, 2)
    for w in range(cw - int(TR) - 3, cw - 2):     # an arched tunnel through the bark
        for u in range(cu - 1, cu + 2):
            for v in range(DV + 1, DV + 5):
                b.set(u, v, w, AIR)
            b.set(u, DV, w, "minecraft:jungle_planks")
        b.set(cu - 1, DV + 4, w, stair("minecraft:jungle_stairs", "west", "top"))
        b.set(cu + 1, DV + 4, w, stair("minecraft:jungle_stairs", "east", "top"))
    b.sign(cu + 3, DV + 1, cw2 + 3, ["Battle Tree", "Reception", "", "Pokémon Center"], wood="jungle", wall=False)
    hang_lantern(b, cu, DV + 7, cw, 2)
    for u in (cu - 3, cu + 3):
        hang_lantern(b, u, DV + 7, cw + 1, 2)
    for du in (-3, -2, -1):                       # Pokémon Center counter on the left
        b.piece(cu + du, DV + 1, cw + 1, "counter", "south")
    npc(b, cu - 2, DV + 1, cw + 2, "alola:nurse")
    setup_cmd(b, cu - 3, DV + 1, cw + 2, "setblock {x} {y} {z} cobblemon:healing_machine[facing={facing}]")
    for du in (1, 2, 3):                          # the Battle Point exchange on the right
        b.piece(cu + du, DV + 1, cw + 1, "counter", "south")
    merchant(b, cu + 2, DV + 1, cw + 2, name="Battle Point Exchange", look="front")
    for u in (cu - 1, cu + 1):
        b.set(u, DV + 1, cw + 4, "cobblemon:display_case[facing=south]")
    npc(b, cu - 5, DV + 1, cw2 + 3, "alola:red")
    npc(b, cu + 5, DV + 1, cw2 + 3, "alola:blue")
    # the forest floor round the tree
    for u in range(-3, W + 3):
        for w in range(-14, D + 3):
            if rng.random() < 0.3 and b.get(u, 1, w) == AIR and not on_deck(u, w):
                plant_on(b, u, 0, w, rng, LUSH + [("wilderwild:red_hibiscus", 1), ("wilderwild:pink_hibiscus", 1)])
    return W, D


# ======================================================================= Kukui's lab

KUKUI = arch.replace(
    arch.STYLES["plantation"], name="kukui",
    walls=[("minecraft:stripped_oak_wood[axis=y]", 5), ("minecraft:oak_planks", 1)],
    frame="minecraft:stripped_dark_oak_log[axis=y]", beam="minecraft:stripped_dark_oak_log",
    roof="mcwroofs:cyan_terracotta", roof_cap="minecraft:cyan_terracotta", roof_kind="gable",
    shutter="minecraft:dark_oak_trapdoor", floor="minecraft:oak_planks", inner_wall="minecraft:stripped_oak_wood[axis=y]",
    deck="minecraft:stripped_oak_wood[axis=y]", post="minecraft:stripped_dark_oak_log[axis=y]",
    rail="minecraft:dark_oak_fence", porch=3, planter=True)


def kukui_lab(c: Canvas, x, y, z, facing, rng: random.Random):
    """Professor Kukui's beach house: the lab (fossil machine, PC, research desks, blackboard) on the left,
    his living corner on the right, a lanai and a practice court on the sand."""
    b = arch.Bld(c, x, y, z, facing)
    W, D = 17, 13
    arch.build_house(c, x, y, z, facing, rng, style=KUKUI, W=W, D=D, floors=1, label="Kukui's Lab", yard=False,
                     interior="empty")
    v = 1
    # partition with a bookcase wall and a doorway
    for w in range(5, D - 1):
        for dv in range(3):
            b.set(8, v + dv, w, "minecraft:bookshelf" if dv < 2 and w % 3 else "minecraft:stripped_oak_wood[axis=y]")
    for dv in range(2):
        b.set(8, v + dv, 6, AIR)
    # the lab: fossil machine, PC, desks with monitors, a blackboard, a healing machine
    for w in range(1, D - 1):
        b.set(1, 0, w, "minecraft:white_concrete")
    setup_cmd(b, 1, v, 6, "setblock {x} {y} {z} cobblemon:fossil_analyzer[facing=east]")
    setup_cmd(b, 1, v + 1, 6, "setblock {x} {y} {z} cobblemon:monitor[facing=east]")
    setup_cmd(b, 1, v, 7, "setblock {x} {y} {z} cobblemon:restoration_tank[facing=east,part=bottom]")
    setup_cmd(b, 1, v + 1, 7, "setblock {x} {y} {z} cobblemon:restoration_tank[facing=east,part=top]")
    setup_cmd(b, 4, v, D - 2, "setblock {x} {y} {z} cobblemon:pc[facing=south,part=bottom]")
    setup_cmd(b, 4, v + 1, D - 2, "setblock {x} {y} {z} cobblemon:pc[facing=south,part=top]")
    setup_cmd(b, 6, v, D - 2, "setblock {x} {y} {z} cobblemon:healing_machine[facing=south]")
    for u in (2, 3):
        b.piece(u, v, D - 2, "desk", "south")
    b.set(2, v + 1, D - 2, "cobblemon:monitor[facing=south,screen=blue_progress_5]")
    b.piece(3, v, D - 3, "chair", "north")
    for w in (3, 4):
        b.set(1, v + 1, w, "supplementaries:blackboard[facing=east]")
    b.piece(4, v, 3, "table")
    b.piece(5, v, 3, "chair", "west")
    b.piece(7, v, 1, "plant_big")
    b.piece(4, v, 4, "rug")
    b.piece(4, 3, 6, "ceiling_lamp")
    # Kukui's corner: bed, hammock-style sofa, TV, a Rowlet doll
    b.bed(W - 2, v, D - 3, "orange", facing="north")
    b.piece(W - 3, v, D - 2, "drawer", "north")
    b.piece(10, v, D - 2, "wardrobe", "north")
    b.piece(W - 2, v, 1, "tv", "west")
    b.piece(10, v, 1, "sofa", "east")
    b.piece(10, v, 2, "sofa", "east")
    b.piece(12, v, 2, "table")
    b.piece(12, v, 3, "rug")
    b.piece(W - 2, v, 4, "doll_rowlet", "west")
    b.piece(12, 3, 7, "ceiling_lamp")
    # a path from the lanai to the practice court on the sand, a beach corner and palms
    from . import plants
    for w in range(-6, -3):
        for u in range(W // 2 - 1, W // 2 + 2):
            b.set(u, 0, w, furn.piece("path_tile"))
    for u in range(-1, W + 1):
        for w in range(-P_YARD, -6):
            line = u in (1, W - 2) or w in (-P_YARD + 1, -7, -12)
            b.set(u, 0, w, "minecraft:white_concrete" if line and 1 <= u <= W - 2 and -P_YARD + 1 <= w <= -7
                  else "minecraft:sand")
    pokeball_disc(b, W // 2, -12, 0, 2)
    b.set(W + 1, 1, -9, "minecraft:target")
    b.piece(-2, 1, -8, "beach_chair", "east")
    b.piece(-2, 1, -10, "umbrella", "east")
    for u, w in ((-3, -4), (W + 2, -13), (-3, -15)):
        xx, _, zz = b.world(u, 0, w)
        if c.inside(xx, zz):
            plants.palm(c, xx, c.surface(xx, zz), zz, rng, tall=rng.randint(7, 9))
    return W, D


P_YARD = 17


# ======================================================================= kahuna courts

COURTS = {
    "alola:hau": ("minecraft:smooth_sandstone", "minecraft:cut_sandstone", "minecraft:birch_stairs", "yellow"),
    "alola:hala": ("minecraft:smooth_sandstone", "minecraft:cut_sandstone", "minecraft:jungle_stairs", "orange"),
    "alola:olivia": ("minecraft:polished_granite", "minecraft:red_sandstone", "minecraft:cherry_stairs", "pink"),
    "alola:nanu": ("minecraft:polished_andesite", "minecraft:polished_blackstone_bricks", "minecraft:dark_oak_stairs", "gray"),
    "alola:hapu": ("minecraft:packed_mud", "minecraft:mud_bricks", "minecraft:spruce_stairs", "brown"),
}


def court(c: Canvas, x, y, z, facing, rng: random.Random, npc_cls, label, lines=("Grand Trial",)):
    """A proper battle court: a lined field with trainer boxes and a Poké Ball centre, stepped stands on both
    sides, lamp towers with the kahuna's banners, and the challenger's sign at the gate."""
    floor, rim, seat, colour = COURTS.get(npc_cls, COURTS["alola:hau"])
    b = arch.Bld(c, x, y, z, facing)
    W, D = 27, 35
    b.clear_above(-2, -3, W + 1, D + 1, 20)
    b.foundation(-2, -3, W + 1, D + 1, rim)
    ground_cover(b, -2, -3, W + 1, D + 1, rng, [(rim, 1)])
    f1, f2, g1, g2 = 5, W - 6, 3, D - 4          # the field
    for u in range(f1, f2 + 1):
        for w in range(g1, g2 + 1):
            line = u in (f1, f2) or w in (g1, g2, (g1 + g2) // 2)
            box = (W // 2 - 3 <= u <= W // 2 + 3 and w in (g1 + 2, g1 + 5, g2 - 5, g2 - 2)) or \
                  (u in (W // 2 - 3, W // 2 + 3) and (g1 + 2 <= w <= g1 + 5 or g2 - 5 <= w <= g2 - 2))
            b.set(u, 0, w, "minecraft:white_concrete" if line or box else floor)
    pokeball_disc(b, W // 2, (g1 + g2) // 2, 0, 3)
    # stands: three stepped rows each side
    for k in range(3):
        for w in range(g1 + 2, g2 - 1):
            for u, fc in ((f1 - 2 - k, "west"), (f2 + 2 + k, "east")):
                for v in range(1, k + 1):
                    b.set(u, v, w, rim)
                b.set(u, k + 1, w, stair(seat, fc))
    for w in range(g1 + 2, g2 - 1):
        b.set(f1 - 5, 1, w, rim), b.set(f1 - 5, 2, w, rim), b.set(f1 - 5, 3, w, rim)
        b.set(f2 + 5, 1, w, rim), b.set(f2 + 5, 2, w, rim), b.set(f2 + 5, 3, w, rim)
        b.set(f1 - 5, 4, w, "minecraft:spruce_fence"), b.set(f2 + 5, 4, w, "minecraft:spruce_fence")
    # lamp towers with banners at the corners
    for u, w in ((f1 - 2, g1 - 2), (f2 + 2, g1 - 2), (f1 - 2, g2 + 2), (f2 + 2, g2 + 2)):
        for v in range(1, 9):
            b.set(u, v, w, rim if v < 8 else "minecraft:chiseled_stone_bricks")
        b.set(u, 9, w, "minecraft:lantern[hanging=false]")
        b.set(u, 6, w - 1 if w < D // 2 else w + 1, f"minecraft:{colour}_wall_banner[facing={'south' if w < D // 2 else 'north'}]")
    # gate: posts, sign, the kahuna at the far end
    for u in (W // 2 - 3, W // 2 + 3):
        b.set(u, 1, 0, rim), b.set(u, 2, 0, rim), b.set(u, 3, 0, "minecraft:lantern[hanging=false]")
    npc(b, W // 2, 1, g2 - 3, npc_cls)
    b.sign(W // 2 - 2, 1, -1, [label, *lines], wood="spruce", wall=False)
    return W, D


# ======================================================================= Hokulani Observatory

def observatory(c: Canvas, x, y, z, facing, rng: random.Random):
    """A white domed observatory with an open slit and a big telescope, joined to a modern research annex
    where Sophocles runs his trial; a viewing terrace with coin telescopes."""
    b = arch.Bld(c, x, y, z, facing)
    W, D = 37, 35
    cu, cw, R = 18, 22, 10
    b.clear_above(-2, -8, W + 1, D + 1, 34)
    b.foundation(-2, -8, W + 1, D + 1, "minecraft:polished_andesite")
    ground_cover(b, -2, -8, W + 1, D + 1, rng, [("mcwpaths:andesite_flagstone", 3), ("minecraft:polished_andesite", 1)])
    # the annex in front (built first: it clears its own plot)
    AW, AD = 21, 10
    ax = cu - AW // 2
    arch.build_house(c, *b.world(ax, 0, 0), facing, rng, style="modern", W=AW, D=AD, floors=1,
                     label="Hokulani Observatory", yard=False, interior="empty")
    # the drum
    for du in range(-R - 1, R + 2):
        for dw in range(-R - 1, R + 2):
            d = math.hypot(du, dw)
            if d <= R + 0.5:
                b.set(cu + du, 0, cw + dw, "minecraft:black_concrete" if rng.random() > 0.04 else "minecraft:sea_lantern")
            if R - 0.7 < d <= R + 0.5:
                for v in range(1, 10):
                    a = math.degrees(math.atan2(dw, du)) % 360
                    win = v in (4, 5) and int(a) % 45 < 12
                    b.set(cu + du, v, cw + dw, "minecraft:light_blue_stained_glass" if win else
                          "minecraft:smooth_quartz" if v in (1, 9) else "minecraft:white_concrete")
    # the dome with its observation slit facing the front
    for du in range(-R, R + 1):
        for dw in range(-R, R + 1):
            for dv in range(0, R + 1):
                d = math.sqrt(du * du + dv * dv + dw * dw)
                if R - 1.1 < d <= R:
                    slit = abs(du) <= 1 and dw < 2
                    b.set(cu + du, 10 + dv, cw + dw, AIR if slit else
                          "minecraft:light_gray_concrete" if (dv % 4 == 0) else "minecraft:white_concrete")
    # the telescope, pivoting on a pier and pointing out of the slit
    for v in range(1, 5):
        b.set(cu, v, cw + 2, "minecraft:iron_block" if v < 4 else "minecraft:polished_andesite")
    for s in range(0, 13):
        tv, tw = 5 + int(s * 0.75), cw + 2 - s
        for du, dv in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            b.set(cu + du, tv + dv, tw, "minecraft:tinted_glass" if s == 12 else
                  "minecraft:black_concrete" if s == 0 else "minecraft:light_gray_concrete" if s % 4 else "minecraft:iron_block")
    # a glazed corridor from the annex into the drum
    for w in range(AD, cw - R + 2):
        for u in range(cu - 2, cu + 3):
            b.set(u, 0, w, "minecraft:polished_diorite")
            b.set(u, 4, w, "minecraft:smooth_quartz_slab[type=bottom]")
            for v in range(1, 4):
                side = u in (cu - 2, cu + 2)
                if side and w < cw - R:
                    b.set(u, v, w, "minecraft:white_concrete" if v != 2 else "minecraft:light_blue_stained_glass")
                elif not side:
                    b.set(u, v, w, AIR)
    for v in range(1, 3):
        b.set(cu, v, AD - 1, AIR)
    for u in range(ax + 2, ax + AW - 2, 3):
        b.piece(u, 1, AD - 2, "desk", "south")
        b.set(u, 2, AD - 2, "cobblemon:monitor[facing=south,screen=green_progress_9]")
        b.piece(u, 1, AD - 3, "chair_modern", "north")
    b.piece(ax + 1, 1, 1, "plant_big")
    b.piece(ax + AW - 2, 1, 1, "plant_big")
    npc(b, cu + 3, 1, 4, "alola:sophocles")
    # viewing terrace with coin telescopes and benches
    for u in range(-1, W + 1, 5):
        b.set(u, 1, -7, "minecraft:andesite_wall")
        b.set(u, 2, -7, "minecraft:lightning_rod[facing=south]")
    for u in (4, W - 5):
        b.piece(u, 1, -4, "bench", "south")
    b.sign(cu - 2, 1, -6, ["Hokulani", "Observatory", "", "Trial Site"], wood="birch", wall=False)
    return W, D


# ======================================================================= Thrifty Megamart (abandoned)

def megamart(c: Canvas, x, y, z, facing, rng: random.Random, abandoned=True):
    """The abandoned Thrifty Megamart where Acerola's trial waits: cracked car park, broken storefront,
    toppled aisles in the dark, candles and Mimikyu dolls."""
    b = arch.Bld(c, x, y, z, facing)
    W, D, H = 41, 31, 9
    PK = 14                                        # car park depth
    b.clear_above(-2, -PK - 1, W + 1, D + 1, 20)
    b.foundation(-2, -PK - 1, W + 1, D + 1, "minecraft:stone")
    for u in range(-2, W + 2):
        for w in range(-PK - 1, 0):
            cracked = rng.random() < 0.12
            b.set(u, 0, w, "minecraft:moss_block" if cracked else
                  "minecraft:light_gray_concrete" if (u % 5 == 0 and -PK + 2 <= w <= -3) else "minecraft:black_concrete_powder"
                  if rng.random() < 0.2 else "minecraft:gray_concrete_powder")
            if cracked and rng.random() < 0.6:
                b.set(u, 1, w, pick(rng, [("minecraft:short_grass", 3), ("minecraft:fern", 1), ("minecraft:dead_bush", 1)]))
    for u in range(-1, W + 1, 12):
        tall(b, u, 1, -PK, "street_lamp")
    # shell: white walls, orange-and-yellow fascia, flat roof with a parapet
    for u in range(W):
        for w in range(D):
            b.set(u, 0, w, "minecraft:white_concrete" if (u + w) % 2 else "minecraft:light_gray_concrete")
            wall = u in (0, W - 1) or w in (0, D - 1)
            for v in range(1, H + 1):
                b.set(u, v, w, ("minecraft:white_concrete" if v < H - 2 else "minecraft:orange_concrete" if v == H - 1
                                else "minecraft:yellow_concrete" if v == H - 2 else "minecraft:white_concrete")
                      if wall else AIR)
            b.set(u, H + 1, w, "minecraft:light_gray_concrete")
    for u in range(W):
        b.set(u, H + 2, 0, "minecraft:smooth_stone_slab[type=bottom]")
        b.set(u, H + 2, D - 1, "minecraft:smooth_stone_slab[type=bottom]")
    for w in range(D):
        b.set(0, H + 2, w, "minecraft:smooth_stone_slab[type=bottom]")
        b.set(W - 1, H + 2, w, "minecraft:smooth_stone_slab[type=bottom]")
    # storefront: glass with broken panes, jammed sliding doors, a big glowing name board
    for u in range(2, W - 2):
        for v in range(1, 6):
            if W // 2 - 2 <= u <= W // 2 + 2 and v < 4:
                continue
            r = rng.random()
            b.set(u, v, 0, AIR if abandoned and r < 0.12 else "minecraft:cobweb" if abandoned and r < 0.18 else
                  "minecraft:glass_pane")
    for u in range(W // 2 - 2, W // 2 + 3):
        for v in range(1, 4):
            b.set(u, v, 0, AIR)
    b.door(W // 2 - 1, 1, 0, "iron", hinge="left")
    for u in range(W // 2 - 6, W // 2 + 7):
        b.set(u, 7, -1, "minecraft:red_concrete")
    b.sign(W // 2, 7, -2, ["THRIFTY", "MEGAMART", "", "CLOSED" if abandoned else "Open!"], wood="birch", glow=True)
    # aisles: shelves (some toppled), crates, dusty checkouts
    for aisle in range(5, W - 5, 5):
        for w in range(8, D - 4):
            fallen = abandoned and rng.random() < 0.12
            if fallen:
                b.set(aisle + rng.choice([-1, 1]), 1, w, stair("minecraft:spruce_stairs", rng.choice(["east", "west"]), "top"))
                continue
            b.set(aisle, 1, w, "minecraft:barrel[facing=up]" if w % 3 else "minecraft:chiseled_bookshelf[facing=south]")
            b.set(aisle, 2, w, "minecraft:chiseled_bookshelf[facing=north]" if w % 2 else furn.piece("crate"))
            if rng.random() < 0.4:
                b.set(aisle, 3, w, furn.piece("crate"))
    for u in range(4, 17, 4):
        b.piece(u, 1, 4, "counter", "south")
        b.piece(u + 1, 1, 4, "counter", "south")
    for u in range(4, W - 4, 6):
        for w in range(6, D - 3, 7):
            b.set(u, H, w, "minecraft:redstone_lamp[lit=false]" if abandoned else "minecraft:redstone_lamp[lit=true]")
    if abandoned:
        for _ in range(70):
            u, v, w = rng.randint(1, W - 2), rng.randint(1, H - 1), rng.randint(1, D - 2)
            if b.get(u, v, w) == AIR:
                b.set(u, v, w, "minecraft:cobweb")
        for _ in range(9):
            u, w = rng.randint(2, W - 3), rng.randint(6, D - 3)
            if b.get(u, 1, w) == AIR:
                b.set(u, 1, w, "pokeblocks:pokedoll_mimikyu")
        for _ in range(14):
            u, w = rng.randint(2, W - 3), rng.randint(5, D - 3)
            if b.get(u, 1, w) == AIR:
                b.set(u, 1, w, f"minecraft:candle[candles={rng.randint(1, 4)},lit=true]")
        npc(b, W // 2, 1, D - 4, "alola:acerola")
    return W, D + PK


# ======================================================================= Altar of the Sunne

def altar(c: Canvas, x, y, z, facing, rng: random.Random):
    """The Altar of the Sunne and Moone: a stepped round dais with a sun mosaic, a ring of lantern pillars and
    a great half-ring frame, gold on the sun side and purple on the moon side."""
    b = arch.Bld(c, x, y, z, facing)
    W = D = 31
    cu, cw, R = 15, 16, 13
    b.clear_above(-2, -6, W + 1, D + 1, 34)
    b.foundation(-2, -6, W + 1, D + 1, "minecraft:polished_blackstone")
    for du in range(-R - 3, R + 4):
        for dw in range(-R - 3, R + 4):
            d = math.hypot(du, dw)
            lvl = 3 if d <= R else 2 if d <= R + 1 else 1 if d <= R + 2 else 0
            for v in range(0, lvl + 1):
                b.set(cu + du, v, cw + dw, "minecraft:polished_blackstone_bricks")
            if lvl == 3 and R - 1 < d:
                b.set(cu + du, 3, cw + dw, "minecraft:gilded_blackstone")
            if d <= R - 1:
                a = math.degrees(math.atan2(dw, du)) % 360
                ray = int(a / 15) % 2 == 0
                b.set(cu + du, 3, cw + dw, "minecraft:gold_block" if d <= 2.5 else
                      "minecraft:orange_glazed_terracotta" if d <= 4.5 else
                      ("minecraft:yellow_glazed_terracotta" if ray else "minecraft:smooth_quartz") if d <= 9 else
                      "minecraft:polished_blackstone")
    for k in range(3):                           # front stair
        for u in range(cu - 3, cu + 4):
            b.set(u, k + 1, cw - R - 3 + k, stair("minecraft:polished_blackstone_brick_stairs", "north"))
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        pu, pw = cu + int(round(math.cos(a) * (R - 1))), cw + int(round(math.sin(a) * (R - 1)))
        for v in range(4, 11):
            b.set(pu, v, pw, "minecraft:quartz_pillar[axis=y]")
        b.set(pu, 11, pw, "minecraft:chiseled_quartz_block")
        b.set(pu, 12, pw, "minecraft:lantern[hanging=false]")
    # the great half ring at the back
    for du in range(-R, R + 1):
        for dv in range(0, R + 1):
            d = math.hypot(du, dv)
            if R - 1.6 < d <= R:
                sun = du < 0
                b.set(cu + du, 4 + dv, cw + R - 2, "minecraft:gold_block" if sun and d > R - 0.8 else
                      "minecraft:orange_concrete" if sun else
                      "minecraft:purple_concrete" if d > R - 0.8 else "minecraft:amethyst_block")
    b.sign(cu - 5, 1, cw - R - 5, ["Altar of", "the Sunne", "", "Vast Poni Canyon"], wood="dark_oak", wall=False)
    return W, D
