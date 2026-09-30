"""Unique Alola landmarks."""
from __future__ import annotations

import math
import random

from . import furn
from .buildings import P, base, house, npc, pokeball_disc, pokeball_face, setup_cmd
from .canvas import SEA, Canvas
from .kit import B


# ------------------------------------------------------------------ tapu ruins
TAPU = {
    "koko": ("minecraft:yellow_concrete", "minecraft:black_concrete", "minecraft:orange_concrete"),
    "lele": ("minecraft:pink_concrete", "minecraft:white_concrete", "minecraft:magenta_concrete"),
    "bulu": ("minecraft:red_concrete", "minecraft:black_concrete", "minecraft:brown_concrete"),
    "fini": ("minecraft:light_blue_concrete", "minecraft:purple_concrete", "minecraft:blue_concrete"),
}


def tapu_ruins(c: Canvas, x, y, z, facing, rng, tapu="koko", name="Ruins of Conflict"):
    b = B(c, x, y, z, facing)
    main, dark, acc = TAPU[tapu]
    W, D = 19, 23
    base(b, W, D, floor="minecraft:mossy_stone_bricks", found="minecraft:stone_bricks", clear=20)
    # stepped approach
    for i in range(4):
        for u in range(5 - i, 14 + i):
            b.set(u, -i, -1 - i, "minecraft:stone_brick_stairs[facing=south]")
    # pillars and walls
    for w in range(0, D, 4):
        for u in (0, W - 1):
            for v in range(1, 8):
                b.set(u, v, w, "minecraft:chiseled_stone_bricks" if v in (1, 7) else "minecraft:stone_bricks")
    b.box(0, 1, D - 1, W - 1, 9, D - 1, "minecraft:stone_bricks")
    b.box(0, 8, 0, W - 1, 8, D - 1, "minecraft:stone_brick_slab[type=bottom]")
    for u in range(0, W):
        b.set(u, 9, 0, main if u % 2 else dark)
        b.set(u, 9, D - 1, main if u % 2 else dark)
    # inner shrine with the guardian's colors
    b.box(4, 1, 12, 14, 1, 20, "minecraft:polished_andesite")
    b.box(6, 2, 16, 12, 2, 20, "minecraft:polished_andesite")
    for u, v in ((9, 3), (9, 4), (9, 5), (8, 4), (10, 4), (7, 5), (11, 5), (8, 6), (10, 6), (9, 7), (7, 7), (11, 7)):
        b.set(u, v, 19, main)
    b.set(9, 6, 19, dark)
    b.set(8, 5, 19, acc), b.set(10, 5, 19, acc)
    for u in (6, 12):
        b.set(u, 3, 17, "minecraft:soul_lantern[hanging=false]")
    for w in range(2, 12, 3):
        for u in (4, 14):
            b.set(u, 1, w, "minecraft:mossy_cobblestone_wall")
            b.set(u, 2, w, "minecraft:torch")
    b.sign(9, 2, -1, [name, "", "Shrine of the", f"guardian Tapu {tapu.title()}"], wood="dark_oak")
    return W, D


# ------------------------------------------------------------------ iki town
def iki_stage(c: Canvas, x, y, z, facing, rng):
    """The festival stage where the Island Challenge begins."""
    b = B(c, x, y, z, facing)
    W, D = 17, 17
    base(b, W, D, floor="minecraft:stripped_oak_wood[axis=y]")
    for u in range(W):
        for w in range(D):
            b.set(u, 1, w, "minecraft:oak_planks" if (u + w) % 2 else "minecraft:stripped_oak_wood[axis=y]")
    for u, w in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
        for v in range(2, 8):
            b.set(u, v, w, "minecraft:stripped_dark_oak_log[axis=y]")
        b.set(u, 8, w, "minecraft:campfire[lit=true]")
    for u in range(W):
        b.set(u, 2, -1, "minecraft:oak_stairs[facing=north]") if 5 <= u <= 11 else b.set(u, 2, -1, "minecraft:oak_fence")
    for i, u in enumerate(range(2, W - 2)):
        b.set(u, 7, 0, "minecraft:red_wool" if i % 2 else "minecraft:yellow_wool")
        b.set(u, 7, D - 1, "minecraft:red_wool" if i % 2 else "minecraft:yellow_wool")
    # Tapu Koko statue at the back
    main, dark, acc = TAPU["koko"]
    for v in range(2, 10):
        b.set(8, v, D - 2, dark if v < 5 else main)
    for u, v in ((7, 7), (9, 7), (6, 8), (10, 8), (5, 9), (11, 9), (7, 9), (9, 9), (8, 10)):
        b.set(u, v, D - 2, main)
    b.set(8, 8, D - 3, acc)
    for u in (3, 13):
        b.set(u, 2, D - 3, "minecraft:note_block"), b.set(u, 3, D - 3, "minecraft:red_carpet")
    b.sign(8, 3, -2, ["Iki Town", "Festival Stage", "", "Tapu Koko watches"], wood="dark_oak", wall=False)
    npc(b, 8, 2, 8, "alola:hala")
    return W, D


# ------------------------------------------------------------------ domes/observatory
def royal_dome(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    R = 18
    W = D = 2 * R + 1
    base(b, W, D, floor="minecraft:smooth_stone", clear=R + 6)
    b.cylinder(R, R, 1, 6, R, "minecraft:white_concrete")
    b.dome(R, R, 6, R, "minecraft:light_blue_stained_glass")
    b.disc(R, R, 1, 9, "minecraft:red_concrete")
    b.disc(R, R, 1, 8, "minecraft:white_concrete")
    for a in range(0, 360, 20):
        u = R + int(round(math.cos(math.radians(a)) * 13))
        w = R + int(round(math.sin(math.radians(a)) * 13))
        for v in (1, 2, 3):
            b.set(u, v, w, "minecraft:polished_andesite_stairs[facing=north]" if v == 1 else "minecraft:air")
    b.clear(R - 2, 1, 0, R + 2, 4, 1)
    b.sign(R - 3, 5, -1, ["Battle Royal", "Dome", "", "Royal Avenue"], wood="birch")
    for u in (R - 2, R + 2):
        for v in range(7, 12):
            b.set(u, v, R, "minecraft:red_concrete_powder")
    return W, D


def observatory(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    W, D = 21, 21
    base(b, W, D, floor="minecraft:polished_diorite", clear=22)
    b.cylinder(10, 10, 1, 7, 10, "minecraft:white_concrete")
    b.dome(10, 10, 8, 10, "minecraft:light_gray_concrete")
    for v in range(8, 19):
        b.set(10, v, 2 + (v - 8) // 2, "minecraft:black_stained_glass")
    for v in range(2, 8):
        b.set(10, v, 10, "minecraft:iron_block" if v < 7 else "minecraft:lightning_rod[facing=up]")
    for a in range(0, 360, 30):
        u = 10 + int(round(math.cos(math.radians(a)) * 7))
        w = 10 + int(round(math.sin(math.radians(a)) * 7))
        b.set(u, 1, w, P("desk", "south"))
        b.set(u, 2, w, "minecraft:redstone_lamp[lit=true]")
    b.clear(9, 1, 0, 11, 3, 0)
    b.sign(8, 4, -1, ["Hokulani", "Observatory", "", "Trial Site"], wood="birch")
    npc(b, 10, 1, 5, "alola:sophocles")
    return W, D


# ------------------------------------------------------------------ megamart
def megamart(c: Canvas, x, y, z, facing, rng, abandoned=True):
    b = B(c, x, y, z, facing)
    W, D = 41, 31
    base(b, W, D, floor="minecraft:light_gray_concrete", clear=16)
    b.box(0, 1, 0, W - 1, 9, D - 1, "minecraft:white_concrete", walls_only=True)
    for u in range(W):
        b.set(u, 9, 0, "minecraft:orange_concrete"), b.set(u, 8, 0, "minecraft:yellow_concrete")
    b.box(-1, 10, -1, W, 10, D, "minecraft:gray_concrete")
    for u in range(3, W - 3):
        for v in range(2, 6):
            b.set(u, v, 0, "minecraft:cracked_stone_bricks" if abandoned and rng.random() < 0.15 else "minecraft:glass_pane")
    b.clear(19, 1, 0, 21, 4, 0)
    for aisle in range(5, W - 5, 6):
        for w in range(6, D - 6):
            b.set(aisle, 1, w, "minecraft:barrel[facing=up]")
            b.set(aisle, 2, w, "minecraft:bookshelf" if rng.random() < 0.5 else "minecraft:barrel[facing=up]")
            if abandoned and rng.random() < 0.3:
                b.set(aisle + 1, 1, w, "minecraft:cobweb")
    for u in range(4, 16):
        b.set(u, 1, 3, P("counter", "south"))
    if abandoned:
        for _ in range(80):
            b.set(rng.randint(1, W - 2), rng.randint(1, 8), rng.randint(1, D - 2), "minecraft:cobweb")
    b.sign(18, 6, -1, ["Thrifty", "Megamart", "", "CLOSED" if abandoned else "Open!"], wood="birch")
    if abandoned:
        npc(b, 20, 1, 20, "alola:acerola")
    return W, D


# ------------------------------------------------------------------ battle tree
def battle_tree(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    W = D = 41
    base(b, W, D, floor="minecraft:moss_block", clear=60)
    cu, cw = 20, 26
    for v in range(1, 48):
        r = 5.5 - v * 0.05
        b.cylinder(cu, cw, v, v, r, "minecraft:jungle_wood[axis=y]", hollow=False)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        for s in range(6, 14):
            b.set(cu + dx * s, max(1, 4 - s // 3), cw + dz * s, "minecraft:jungle_wood[axis=y]")
    for layer, (v, r) in enumerate(((36, 16), (44, 14), (50, 10), (55, 6))):
        for du in range(-r, r + 1):
            for dw in range(-r, r + 1):
                d = math.hypot(du, dw)
                if d <= r and rng.random() < 0.85:
                    for dv in range(0, 3 if d < r - 3 else 2):
                        b.set(cu + du, v + dv - (1 if d > r - 3 else 0), cw + dw, "minecraft:jungle_leaves[persistent=true]")
    # arena in front
    b.disc(20, 11, 0, 9, "minecraft:polished_andesite")
    b.box(12, 0, 11, 28, 0, 11, "minecraft:white_concrete")
    pokeball_disc(b, 20, 11, 0, 3)
    b.sign(20, 2, 1, ["Battle Tree", "", "Poni Island", ""], wood="jungle", wall=False)
    npc(b, 17, 1, 17, "alola:red")
    npc(b, 23, 1, 17, "alola:blue")
    return W, D


# ------------------------------------------------------------------ small landmarks
def lighthouse(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    base(b, 9, 9, floor="minecraft:stone_bricks", clear=30)
    for v in range(1, 22):
        b.cylinder(4, 4, v, v, 3.6, "minecraft:red_concrete" if (v // 3) % 2 else "minecraft:white_concrete")
    b.cylinder(4, 4, 22, 24, 3.6, "minecraft:glass")
    b.set(4, 23, 4, "minecraft:sea_lantern"), b.set(4, 22, 4, "minecraft:glowstone")
    b.disc(4, 4, 25, 4, "minecraft:red_concrete")
    b.clear(4, 1, 0, 4, 2, 0)
    return 9, 9


def barn(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    W, D = 15, 19
    base(b, W, D, floor="minecraft:coarse_dirt")
    b.box(0, 1, 0, W - 1, 6, D - 1, "minecraft:red_terracotta", walls_only=True)
    for w in range(0, D, 4):
        for v in range(1, 7):
            b.set(0, v, w, "minecraft:stripped_spruce_log[axis=y]"), b.set(W - 1, v, w, "minecraft:stripped_spruce_log[axis=y]")
    b.clear(5, 1, 0, 9, 5, 0)
    b.gable_roof(0, W - 1, 0, D - 1, 7, "minecraft:spruce_stairs", full="minecraft:spruce_planks")
    for w in range(2, D - 2, 3):
        b.set(2, 1, w, "minecraft:hay_block[axis=y]"), b.set(2, 2, w, "minecraft:hay_block[axis=x]")
        b.set(W - 3, 1, w, "minecraft:hay_block[axis=y]")
    b.sign(7, 6, -1, ["Paniola Ranch"], wood="spruce")
    return W, D


def lab(c: Canvas, x, y, z, facing, rng):
    """Professor Kukui's beach-side lab house (with the lab downstairs)."""
    b = B(c, x, y, z, facing)
    W, D = house(c, x, y, z, facing, rng, W=13, D=11, wall="minecraft:smooth_sandstone",
                 roof=("minecraft:dark_prismarine_stairs", "minecraft:dark_prismarine"), label="Kukui's Lab", beds=1)
    b.clear(2, -6, 2, W - 3, -1, D - 3)
    b.box(1, -7, 1, W - 2, -7, D - 2, "minecraft:smooth_quartz")
    for u in range(2, W - 2, 2):
        b.set(u, -6, D - 3, P("desk", "south"))
        b.set(u, -5, D - 3, "minecraft:redstone_lamp[lit=true]")
    for v in range(-6, 0):
        b.set(2, v, 2, "minecraft:ladder[facing=east]")
    b.set(W - 3, -6, 3, "minecraft:enchanting_table")
    b.set(W - 3, -1, 3, "minecraft:sea_lantern")
    return W, D


def houseboat(c: Canvas, x, y, z, facing, rng):
    """Seafolk Village houseboat floating at sea level."""
    b = B(c, x, y, z, facing)
    L, Wd = 18, 9
    hull = rng.choice(["minecraft:spruce_planks", "minecraft:dark_oak_planks", "minecraft:mangrove_planks"])
    for w in range(L):
        half = 4 if 2 < w < L - 3 else 3
        for u in range(-half, half + 1):
            b.set(u + 4, -1, w, hull)
            b.set(u + 4, 0, w, "minecraft:spruce_planks")
            if abs(u) == half:
                b.set(u + 4, 1, w, "minecraft:spruce_fence")
    house(c, *b.world(1, 0, 4), facing, rng, W=7, D=8, wall=rng.choice(["minecraft:white_terracotta", "minecraft:cyan_terracotta"]),
          roof=("minecraft:spruce_stairs", "minecraft:spruce_planks"))
    return Wd, L


def wailord_restaurant(c: Canvas, x, y, z, facing, rng):
    """Seafolk Village's Wailord-shaped restaurant boat."""
    b = B(c, x, y, z, facing)
    L, R = 40, 9
    for w in range(L):
        r = R * math.sin(math.pi * min(1.0, (w + 4) / (L + 4)))
        for du in range(-R, R + 1):
            for dv in range(-4, R + 1):
                d = math.hypot(du, dv * 1.1)
                if r - 1.2 < d <= r:
                    state = "minecraft:blue_concrete" if dv > -1 else "minecraft:light_blue_concrete"
                    b.set(R + du, dv, w, state)
    for du in (-4, 4):
        b.set(R + du, 4, 5, "minecraft:white_concrete"), b.set(R + du, 4, 4, "minecraft:black_concrete")
    b.box(R - 5, 0, 2, R + 5, 0, L - 4, "minecraft:spruce_planks")
    for w in range(6, L - 6, 4):
        b.set(R - 3, 1, w, P("table")), b.set(R + 3, 1, w, P("table"))
    b.sign(R, 2, 1, ["Seafolk", "Restaurant"], wood="spruce", wall=False)
    return 2 * R + 1, L


def po_town_walls(c: Canvas, x1, z1, x2, z2, y):
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            for v in range(0, 9):
                c.set(x, y + v, z, "minecraft:gray_concrete" if v < 8 else "minecraft:black_concrete")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            for v in range(0, 9):
                c.set(x, y + v, z, "minecraft:gray_concrete" if v < 8 else "minecraft:black_concrete")
    # graffiti
    rng = random.Random(42)
    cols = ["minecraft:magenta_concrete", "minecraft:lime_concrete", "minecraft:cyan_concrete", "minecraft:white_concrete"]
    for _ in range(300):
        if rng.random() < 0.5:
            xx, zz = rng.randint(x1, x2), rng.choice([z1, z2])
        else:
            xx, zz = rng.choice([x1, x2]), rng.randint(z1, z2)
        c.set(xx, y + rng.randint(1, 6), zz, rng.choice(cols))
    gate = (x1 + x2) // 2
    for x in range(gate - 2, gate + 3):
        for v in range(1, 6):
            c.set(x, y + v, z2, "minecraft:air")
        c.set(x, y + 1, z2, "minecraft:iron_bars")


def shady_house(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    W, D = 27, 21
    base(b, W, D, floor="minecraft:dark_oak_planks", clear=24)
    b.box(0, 1, 0, W - 1, 12, D - 1, "minecraft:deepslate_bricks", walls_only=True)
    b.box(1, 6, 1, W - 2, 6, D - 2, "minecraft:dark_oak_planks")
    for u in range(2, W - 2, 3):
        for v in (3, 4, 8, 9):
            b.set(u, v, 0, "minecraft:gray_stained_glass_pane")
    b.clear(12, 1, 0, 14, 4, 0)
    b.hip_roof(0, W - 1, 0, D - 1, 13, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks")
    b.set(13, 3, -1, "minecraft:skeleton_skull[rotation=0]")
    b.sign(12, 5, -1, ["Shady House", "", "Team Skull", "HQ"], wood="dark_oak")
    for w in range(3, D - 3, 2):
        b.set(6, 1, w, "minecraft:red_carpet"), b.set(20, 1, w, "minecraft:red_carpet")
    b.set(13, 7, D - 3, P("sofa", "north"))
    npc(b, 13, 7, D - 5, "alola:guzma")
    for u in (5, 21):
        npc(b, u, 1, 8, "alola:skull_grunt")
    return W, D


def power_plant(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    W, D = 25, 17
    base(b, W, D, floor="minecraft:polished_andesite")
    b.box(0, 1, 0, W - 1, 8, D - 1, "minecraft:light_gray_concrete", walls_only=True)
    b.box(-1, 9, -1, W, 9, D, "minecraft:gray_concrete")
    for cu in (5, 12, 19):
        b.cylinder(cu, D + 5, 1, 16, 3, "minecraft:white_concrete")
        b.set(cu, 17, D + 5, "minecraft:campfire[lit=true,signal_fire=true]")
    for u in range(3, W - 3):
        b.set(u, 5, D, "minecraft:iron_bars")
    b.clear(11, 1, 0, 13, 3, 0)
    b.sign(10, 5, -1, ["Blush Mountain", "Geothermal", "Power Plant"], wood="birch")
    return W, D + 9


def trial_gate(c: Canvas, x, y, z, facing, rng, captain_line="Trial Site"):
    """The yellow-and-black barrier that marks an island trial site."""
    b = B(c, x, y, z, facing)
    for u in (0, 6):
        for v in range(1, 5):
            b.set(u, v, 0, "minecraft:yellow_concrete" if v % 2 else "minecraft:black_concrete")
    for u in range(0, 7):
        b.set(u, 5, 0, "minecraft:yellow_concrete" if u % 2 else "minecraft:black_concrete")
    b.sign(3, 3, -1, ["§6Trial Site", "", captain_line, ""], wood="birch", wall=False)
    return 7, 1


def cave_entrance(c: Canvas, x, y, z, facing, rng, depth=30, name="Verdant Cavern", npc_cls=None):
    """Tunnel into a hillside ending in a den."""
    b = B(c, x, y, z, facing)
    for w in range(0, depth):
        wobble = int(2 * math.sin(w / 5))
        for u in range(-2, 3):
            for v in range(1, 5):
                b.set(u + wobble, v, w, "minecraft:air")
            b.set(u + wobble, 0, w, "minecraft:gravel" if (u + w) % 3 else "minecraft:coarse_dirt")
        b.set(-3 + wobble, 3, w, "minecraft:stone"), b.set(3 + wobble, 3, w, "minecraft:stone")
        if w % 6 == 3:
            b.set(-2 + wobble, 3, w, "minecraft:torch")
    b.clear(-6, 1, depth, 6, 7, depth + 12)
    b.box(-6, 0, depth, 6, 0, depth + 12, "minecraft:mossy_cobblestone")
    b.set(0, 1, depth + 10, "minecraft:mossy_cobblestone_wall")
    for u in (-4, 4):
        b.set(u, 1, depth + 6, "minecraft:lantern[hanging=false]")
    if npc_cls:
        npc(b, 0, 1, depth + 8, npc_cls)
    trial_gate(c, *b.world(-3, 0, -2), facing, rng, name)
    return 13, depth + 13


def grave_field(c: Canvas, x, y, z, facing, rng, rows=6, cols=10, name="Hau'oli Cemetery"):
    b = B(c, x, y, z, facing)
    for r in range(rows):
        for k in range(cols):
            u, w = k * 3, r * 3 + 2
            b.set(u, 1, w, "minecraft:stone_brick_wall")
            b.set(u, 2, w, "minecraft:stone_brick_slab[type=bottom]")
            b.set(u, 1, w - 1, rng.choice(["minecraft:poppy", "minecraft:white_tulip", "minecraft:lily_of_the_valley", "minecraft:air"]))
    b.sign(-2, 1, 0, [name], wood="dark_oak", wall=False)
    return cols * 3, rows * 3 + 2


def arena(c: Canvas, x, y, z, facing, rng, npc_cls, label, lines=("Grand Trial",)):
    """A simple battle court (white lines on a pale field) with the trainer at the far end."""
    b = B(c, x, y, z, facing)
    W, D = 17, 27
    base(b, W, D, floor="minecraft:smooth_sandstone")
    for u in range(W):
        b.set(u, 0, 0, "minecraft:white_concrete"), b.set(u, 0, D - 1, "minecraft:white_concrete")
        b.set(u, 0, D // 2, "minecraft:white_concrete")
    for w in range(D):
        b.set(0, 0, w, "minecraft:white_concrete"), b.set(W - 1, 0, w, "minecraft:white_concrete")
    pokeball_disc(b, W // 2, D // 2, 0, 3)
    npc(b, W // 2, 1, D - 3, npc_cls)
    b.sign(W // 2, 1, -2, [label, *lines], wood="spruce", wall=False)
    for u, w in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
        b.set(u, 1, w, "minecraft:spruce_fence"), b.set(u, 2, w, "minecraft:lantern[hanging=false]")
    return W, D


def altar(c: Canvas, x, y, z, facing, rng):
    """Altar of the Sunne at the top of Vast Poni Canyon."""
    b = B(c, x, y, z, facing)
    W = D = 25
    base(b, W, D, floor="minecraft:polished_blackstone", clear=20)
    b.disc(12, 12, 1, 9, "minecraft:gold_block")
    b.disc(12, 12, 1, 7, "minecraft:yellow_glazed_terracotta")
    b.disc(12, 12, 1, 4, "minecraft:lapis_block")
    for a in range(0, 360, 45):
        u = 12 + int(round(math.cos(math.radians(a)) * 11))
        w = 12 + int(round(math.sin(math.radians(a)) * 11))
        for v in range(1, 8):
            b.set(u, v, w, "minecraft:quartz_pillar[axis=y]")
        b.set(u, 8, w, "minecraft:lantern[hanging=false]")
    b.sign(12, 1, 0, ["Altar of", "the Sunne", "", "and Moone"], wood="dark_oak", wall=False)
    return W, D


def mina_meadow(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    for i in range(6):
        u, w = 2 + i * 3, 4 + (i % 2) * 3
        b.set(u, 1, w, "minecraft:oak_fence"), b.set(u, 2, w, "minecraft:item_frame" if False else "minecraft:painting" if False else "minecraft:white_wool")
        b.set(u, 3, w, "minecraft:white_wool")
    npc(b, 9, 1, 12, "alola:mina")
    trial_gate(c, x, y, z, facing, rng, "Captain Mina")
    return 20, 16
