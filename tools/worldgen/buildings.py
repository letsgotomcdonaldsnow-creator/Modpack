"""Building templates for the Alola region.

Every function takes (c, x, y, z, facing, rng) where (x, y, z) is the front-left
floor corner seen from outside and y is the floor level, and returns the
footprint as (u_max, w_max) so callers can reserve the ground.
"""
from __future__ import annotations

import math
import random

from . import furn
from .canvas import Canvas
from .kit import B

SETUP: list[tuple[int, int, int, str]] = []   # (x, y, z, command) run once when the world first loads


def setup_cmd(b: B, u, v, w, template: str):
    x, y, z = b.world(u, v, w)
    SETUP.append((x, y, z, template.format(x=x, y=y, z=z, xc=x + 0.5, zc=z + 0.5, facing=b.dir("front"),
                                            back=b.dir("back"))))


def npc(b: B, u, v, w, cls: str):
    setup_cmd(b, u, v, w, "spawnnpcat {xc} {y} {zc} " + cls)


def P(name, facing="south"):
    return furn.piece(name, facing)


def base(b: B, W, D, floor="minecraft:smooth_stone", found="minecraft:stone_bricks", clear=24):
    b.clear_above(-1, -1, W, D, clear)
    b.foundation(-1, -1, W, D, found)
    b.box(-1, 0, -1, W, 0, D, floor)


def pokeball_disc(b: B, cu, cw, v, r=3):
    for du in range(-r, r + 1):
        for dw in range(-r, r + 1):
            d = math.hypot(du, dw)
            if d > r + 0.3:
                continue
            if d > r - 0.7 or abs(dw) == 0:
                s = "minecraft:black_concrete"
            elif dw > 0:
                s = "minecraft:red_concrete"
            else:
                s = "minecraft:white_concrete"
            if d <= 1.1:
                s = "minecraft:white_concrete" if d < 0.6 else "minecraft:black_concrete"
            b.set(cu + du, v, cw + dw, s)


def pokeball_face(b: B, cu, cv, w, r=3):
    """Poké Ball emblem on a wall plane (u/v)."""
    for du in range(-r, r + 1):
        for dv in range(-r, r + 1):
            d = math.hypot(du, dv)
            if d > r + 0.3:
                continue
            if d > r - 0.7 or dv == 0:
                s = "minecraft:black_concrete"
            elif dv > 0:
                s = "minecraft:red_concrete"
            else:
                s = "minecraft:white_concrete"
            if d <= 1.1:
                s = "minecraft:white_concrete" if d < 0.6 else "minecraft:black_concrete"
            b.set(cu + du, cv + dv, w, s)


# --------------------------------------------------------------- Pokémon Center

def pokemon_center(c: Canvas, x, y, z, facing, rng, name="Pokémon Center"):
    b = B(c, x, y, z, facing)
    W, D, H = 17, 15, 7
    base(b, W, D, floor="minecraft:white_concrete")
    # floor pattern: red entrance runner and Poké Ball mosaic
    for w in range(0, 9):
        for u in range(7, 10):
            b.set(u, 0, w, "minecraft:red_concrete")
    pokeball_disc(b, 8, 6, 0, 3)
    # walls
    b.box(0, 1, 0, W - 1, H - 1, D - 1, "minecraft:white_concrete", walls_only=True)
    for u in range(W):
        for w in (0, D - 1):
            b.set(u, 5, w, "minecraft:red_concrete")
    for w in range(D):
        for u in (0, W - 1):
            b.set(u, 5, w, "minecraft:red_concrete")
    for u in list(range(1, 6)) + list(range(11, 16)):
        for v in range(1, 5):
            b.set(u, v, 0, "minecraft:light_blue_stained_glass_pane")
    for w in (4, 5, 9, 10):
        for v in (2, 3):
            b.set(0, v, w, "minecraft:glass_pane")
            b.set(W - 1, v, w, "minecraft:glass_pane")
    b.clear(7, 1, 0, 9, 3, 0)                        # entrance
    for u in (6, 10):
        for v in range(1, 5):
            b.set(u, v, 0, "minecraft:quartz_pillar[axis=y]")
    # roof and facade
    b.box(-1, H, -1, W, H, D, "minecraft:red_concrete")
    b.box(0, H + 1, 0, W - 1, H + 1, D - 1, "minecraft:white_concrete_powder")
    for u in range(-1, W + 1):
        b.set(u, H, -1, "minecraft:white_concrete")
        b.set(u, H + 1, -1, "minecraft:quartz_slab[type=bottom]")
    b.box(4, H, 0, 12, H + 7, 0, "minecraft:white_concrete")
    pokeball_face(b, 8, H + 4, -1, 3)
    for u in range(5, 12):
        b.set(u, H + 8, 0, "minecraft:red_concrete")
    # awning over the door
    for u in range(5, 12):
        for w in (-1, -2):
            b.set(u, 4, w, "minecraft:red_concrete_powder" if w == -1 else "minecraft:red_concrete")
    b.set(5, 1, -2, "minecraft:white_concrete"), b.set(11, 1, -2, "minecraft:white_concrete")
    for v in (1, 2, 3):
        b.set(5, v, -2, "minecraft:quartz_pillar[axis=y]")
        b.set(11, v, -2, "minecraft:quartz_pillar[axis=y]")
    b.sign(4, 3, -1, ["§4POKéMON", "§4CENTER", "", name if name != "Pokémon Center" else ""], wood="birch")
    # lights
    for u in (3, 8, 13):
        for w in (3, 7, 11):
            b.set(u, H, w, "minecraft:sea_lantern")
    # healing counter at the back
    for u in range(4, 13):
        b.set(u, 1, 10, "minecraft:red_concrete")
        b.set(u, 2, 10, "minecraft:smooth_quartz_slab[type=bottom]")
    b.box(4, 1, 11, 12, 1, 12, "minecraft:white_concrete")
    b.set(8, 1, 13, "minecraft:red_concrete")
    setup_cmd(b, 8, 1, 11, "setblock {x} {y} {z} cobblemon:healing_machine[facing={facing}]")
    npc(b, 9, 1, 12, "alola:nurse")
    b.set(6, 1, 11, P("plant")), b.set(11, 1, 11, P("plant"))
    for u in range(4, 13):
        b.set(u, 4, 13, "minecraft:red_concrete")
    b.sign(8, 4, 12, ["", "Welcome to the", "Pokémon Center", ""], wood="birch")
    # PCs on the left wall
    for w in (8, 11):
        setup_cmd(b, 1, 1, w, "setblock {x} {y} {z} cobblemon:pc[facing=east,part=bottom]")
        setup_cmd(b, 1, 2, w, "setblock {x} {y} {z} cobblemon:pc[facing=east,part=top]")
    # café corner (front left)
    for u in range(1, 6):
        b.set(u, 1, 6, P("counter", "south"))
    for u in (2, 4):
        b.set(u, 1, 5, P("stool", "north"))
    b.set(1, 1, 7, P("kitchen_drawer", "south")), b.set(2, 1, 7, P("stove", "south"))
    b.set(3, 1, 7, P("kitchen_sink", "south"))
    for (tu, tw) in ((2, 2), (4, 3)):
        b.set(tu, 1, tw, P("table"))
        b.set(tu - 1, 1, tw, P("chair_modern", "east")), b.set(tu + 1, 1, tw, P("chair_modern", "west"))
    b.sign(3, 4, 7, ["Café", "", "Tapioca Latte", "Pinap Juice"], wood="birch", wall=True)
    # Poké Mart counter (right side)
    for w in range(3, 10):
        b.set(13, 1, w, "minecraft:light_blue_concrete")
        b.set(13, 2, w, "minecraft:smooth_quartz_slab[type=bottom]")
    for w in range(2, 11):
        b.set(15, 1, w, P("crate", "west"))
        b.set(15, 2, w, "minecraft:bookshelf" if w % 3 else P("jar"))
    b.sign(14, 4, 9, ["§1POKé MART", "", "Poké Balls", "Potions"], wood="birch")
    npc(b, 14, 1, 6, "alola:nurse")  # clerk (heals too)
    # waiting sofas and plants
    for u in (6, 10):
        b.set(u, 1, 8, P("pc_sofa", "south"))
    for (u, w) in ((1, 1), (15, 1), (1, 13), (15, 13)):
        b.set(u, 1, w, P("plant_big"))
    return W, D


# --------------------------------------------------------------------- houses

WALLS = ["minecraft:white_terracotta", "minecraft:light_blue_terracotta", "minecraft:yellow_terracotta",
         "minecraft:pink_terracotta", "minecraft:lime_terracotta", "minecraft:cyan_terracotta",
         "minecraft:orange_terracotta", "minecraft:white_concrete", "minecraft:smooth_sandstone",
         "minecraft:birch_planks", "minecraft:light_gray_concrete"]
ROOFS = [("minecraft:dark_oak_stairs", "minecraft:dark_oak_planks"), ("minecraft:spruce_stairs", "minecraft:spruce_planks"),
         ("minecraft:acacia_stairs", "minecraft:acacia_planks"), ("minecraft:red_nether_brick_stairs", "minecraft:red_nether_bricks"),
         ("minecraft:mud_brick_stairs", "minecraft:mud_bricks"), ("minecraft:prismarine_brick_stairs", "minecraft:prismarine_bricks"),
         ("minecraft:cut_copper_stairs", "minecraft:cut_copper"), ("minecraft:blackstone_stairs", "minecraft:blackstone")]


def house(c: Canvas, x, y, z, facing, rng, W=None, D=None, wall=None, roof=None, label=None, beds=1):
    b = B(c, x, y, z, facing)
    W = W or rng.choice([9, 10, 11])
    D = D or rng.choice([8, 9, 10])
    wall = wall or rng.choice(WALLS)
    stair, full = roof or rng.choice(ROOFS)
    H = 4
    base(b, W, D, floor="minecraft:oak_planks")
    b.box(0, 1, 0, W - 1, H, D - 1, wall, walls_only=True)
    for u, w in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1)):
        for v in range(1, H + 1):
            b.set(u, v, w, "minecraft:stripped_oak_log[axis=y]")
    for u in range(W):
        for w in (0, D - 1):
            b.set(u, H, w, "minecraft:stripped_oak_log[axis=x]")
    for w in range(D):
        for u in (0, W - 1):
            b.set(u, H, w, "minecraft:stripped_oak_log[axis=z]")
    door_u = W // 2
    b.door(door_u, 1, 0, "oak", facing="north")
    b.set(door_u, 0, -1, "minecraft:oak_slab[type=top]")
    # windows with shutters and flower boxes
    for u in (2, W - 3):
        if u == door_u:
            continue
        b.set(u, 2, 0, "minecraft:glass_pane"), b.set(u, 3, 0, "minecraft:glass_pane")
        b.set(u, 1, -1, P("flower_box"))
        b.set(u - 1, 2, -1, P("shutter", "north")) if u - 1 > 0 else None
    for w in (2, D - 3):
        for u in (0, W - 1):
            b.set(u, 2, w, "minecraft:glass_pane"), b.set(u, 3, w, "minecraft:glass_pane")
    # roof
    b.gable_roof(0, W - 1, 0, D - 1, H + 1, stair, full=full)
    for w in range(-1, D + 1):
        pass
    # gable ends
    half = (W + 1) // 2
    for i in range(half):
        for u in range(i + 1, W - 1 - i):
            b.set(u, H + 1 + i, 0, wall)
            b.set(u, H + 1 + i, D - 1, wall)
    # interior
    b.set(1, H, 1, "minecraft:air")
    b.set(W // 2, H, D // 2, P("ceiling_lamp"))
    b.set(1, 1, D - 2, P("bookshelf", "south"))
    b.set(W - 2, 1, D - 2, P("wardrobe", "south"))
    for i in range(beds):
        b.bed(W - 3 - 2 * i, 1, D - 3, rng.choice(["red", "light_blue", "yellow", "pink", "white"]), facing="north")
    b.set(W - 2, 1, D - 4, P("drawer", "west"))
    b.set(W - 2, 2, D - 4, P("pot_flower"))
    tu, tw = 3, 3
    b.set(tu, 1, tw, P("table"))
    b.set(tu, 2, tw, P("table_top")) if P("table").endswith("fence") else None
    b.set(tu - 1, 1, tw, P("chair", "east")), b.set(tu + 1, 1, tw, P("chair", "west"))
    b.set(1, 1, 1, P("kitchen_drawer", "east")), b.set(1, 1, 2, P("stove", "east"))
    b.set(1, 1, 3, P("kitchen_sink", "east"))
    b.set(W - 2, 1, 1, P("tv"))
    b.set(W - 3, 1, 2, P("sofa", "north"))
    b.set(W // 2, 1, D // 2, P("rug"))
    b.set(1, 1, D - 3, P("plant"))
    if label:
        b.sign(door_u + 1, 2, -1, [label], wood="oak")
    return W, D


def malasada_shop(c: Canvas, x, y, z, facing, rng):
    b = B(c, x, y, z, facing)
    W, D = house(c, x, y, z, facing, rng, W=11, D=9, wall="minecraft:pink_terracotta",
                 roof=("minecraft:red_nether_brick_stairs", "minecraft:red_nether_bricks"), beds=0)
    for u in range(2, 9):
        b.set(u, 1, 5, P("counter", "south"))
    b.sign(6, 3, -1, ["§dMalasada Shop", "Sweet! Spicy!", "Sour! Bitter!", "Dry!"], wood="cherry")
    for (tu, tw) in ((-3, -3), (W + 1, -3)):
        b.set(tu, 1, tw, P("table"))
        b.set(tu, 2, tw, P("umbrella"))
        b.set(tu - 1, 1, tw, P("chair", "east")), b.set(tu + 1, 1, tw, P("chair", "west"))
    return W, D


def shop(c: Canvas, x, y, z, facing, rng, label, color="minecraft:light_blue_concrete", W=13, D=11):
    b = B(c, x, y, z, facing)
    base(b, W, D, floor="minecraft:polished_diorite")
    H = 5
    b.box(0, 1, 0, W - 1, H, D - 1, "minecraft:white_concrete", walls_only=True)
    for u in range(W):
        b.set(u, H, 0, color)
    for u in range(1, W - 1):
        for v in range(1, 4):
            b.set(u, v, 0, "minecraft:glass_pane")
    b.clear(W // 2, 1, 0, W // 2 + 1, 2, 0)
    b.box(-1, H + 1, -1, W, H + 1, D, "minecraft:smooth_stone_slab[type=bottom]")
    for u in range(1, W - 1):
        b.set(u, 4, -1, color.replace("concrete", "stained_glass") if "concrete" in color else color)
    b.sign(W // 2 - 1, 4, -1, [label], wood="birch")
    for w in range(2, D - 1, 2):
        for u in range(2, W - 2, 3):
            b.set(u, 1, w, P("crate", "south"))
            b.set(u, 2, w, P("jar"))
    for u in range(3, W - 3):
        b.set(u, 1, D - 3, P("counter", "south"))
    b.set(W // 2, H, D // 2, "minecraft:sea_lantern")
    return W, D


def hotel(c: Canvas, x, y, z, facing, rng, label, floors=4, W=23, D=15, wall="minecraft:white_concrete",
          trim="minecraft:light_blue_concrete"):
    b = B(c, x, y, z, facing)
    base(b, W, D, floor="minecraft:polished_andesite", clear=floors * 5 + 12)
    Hf = 4
    top = floors * Hf
    b.box(0, 1, 0, W - 1, top, D - 1, wall, walls_only=True)
    for f in range(floors):
        v0 = f * Hf
        if f:
            b.box(1, v0, 1, W - 2, v0, D - 2, "minecraft:smooth_quartz")
            for u in range(W):
                b.set(u, v0, 0, trim)
        for u in range(2, W - 2, 3):
            for v in (v0 + 2, v0 + 3):
                b.set(u, v, 0, "minecraft:glass_pane"), b.set(u + 1, v, 0, "minecraft:glass_pane")
                b.set(u, v, D - 1, "minecraft:glass_pane")
        if f:
            for u in range(2, W - 2, 3):  # balconies
                b.set(u, v0 + 1, -1, "minecraft:quartz_slab[type=bottom]")
                b.set(u, v0 + 2, -1, "minecraft:glass_pane")
        for u in range(3, W - 3, 6):
            b.set(u, v0 + Hf - 1 if f else Hf - 1, D // 2, P("ceiling_lamp"))
        for u in range(2, W - 2, 5):
            if f:
                b.bed(u, v0 + 1, D - 3, "white", facing="north")
                b.set(u + 1, v0 + 1, D - 2, P("drawer", "south"))
    b.box(-1, top + 1, -1, W, top + 1, D, "minecraft:smooth_quartz_slab[type=bottom]")
    b.clear(W // 2 - 1, 1, 0, W // 2 + 1, 3, 0)
    for u in range(W // 2 - 3, W // 2 + 4):
        for w in (-1, -2, -3):
            b.set(u, 4, w, trim)
    b.sign(W // 2 - 2, 3, -1, [label], wood="birch")
    for u in range(4, W - 4):
        b.set(u, 1, 5, P("counter", "south"))
    b.set(3, 1, 2, P("sofa_white", "east")), b.set(W - 4, 1, 2, P("sofa_white", "west"))
    b.set(2, 1, 1, P("plant_big")), b.set(W - 3, 1, 1, P("plant_big"))
    # stairs to upper floors (ladder column)
    for v in range(1, top):
        b.set(W - 2, v, D - 2, "minecraft:ladder[facing=west]")
        b.set(W - 2, v, D - 2, "minecraft:ladder[facing=west]")
    for f in range(1, floors):
        b.set(W - 2, f * Hf, D - 2, "minecraft:ladder[facing=west]")
    return W, D


def ferry_terminal(c: Canvas, x, y, z, facing, rng, label, dest):
    """Terminal building on the quay plus a pier with a moored ferry."""
    b = B(c, x, y, z, facing)
    W, D = shop(c, x, y, z, facing, rng, label, color="minecraft:blue_concrete", W=15, D=9)
    b.sign(3, 2, -1, ["Ferry to", dest, "", ""], wood="birch")
    return W, D


def ferry_ship(c: Canvas, x, y, z, facing, rng, name="Alola Ferry"):
    """A white passenger ferry floating at sea level (y = water surface)."""
    b = B(c, x, y, z, facing)
    L, Wd = 34, 9
    for w in range(L):
        taper = 0 if 3 < w < L - 6 else (min(w, L - 1 - w) if w <= 3 else (L - 1 - w) // 2)
        half = max(1, 4 - (3 - min(taper, 3)) if w <= 3 or w >= L - 6 else 4)
        for u in range(-half, half + 1):
            b.set(u + 4, -1, w, "minecraft:blue_concrete")
            b.set(u + 4, 0, w, "minecraft:white_concrete" if abs(u) == half else "minecraft:spruce_planks")
            if abs(u) == half:
                b.set(u + 4, 1, w, "minecraft:white_concrete")
                b.set(u + 4, 2, w, "minecraft:white_stained_glass_pane" if 6 < w < L - 8 else "minecraft:air")
    b.box(1, 1, 8, 7, 5, 22, "minecraft:white_concrete", walls_only=True)
    for w in range(9, 22, 2):
        b.set(1, 3, w, "minecraft:light_blue_stained_glass_pane"), b.set(7, 3, w, "minecraft:light_blue_stained_glass_pane")
    b.box(1, 6, 8, 7, 6, 22, "minecraft:white_concrete")
    b.box(2, 7, 18, 6, 9, 22, "minecraft:white_concrete", walls_only=True)
    for u in range(2, 7):
        b.set(u, 8, 18, "minecraft:light_blue_stained_glass_pane")
    b.box(3, 10, 20, 5, 12, 21, "minecraft:red_concrete")
    b.box(3, 13, 20, 5, 13, 21, "minecraft:black_concrete")
    b.clear(4, 1, 8, 4, 2, 8)
    for w in range(10, 21, 3):
        b.set(3, 1, w, P("bench", "east")), b.set(5, 1, w, P("bench", "west"))
    b.sign(4, 4, 7, [name], wood="birch")
    return Wd, L


def pier(c: Canvas, x, y, z, facing, length=24, width=5):
    b = B(c, x, y, z, facing)
    for w in range(length):
        for u in range(width):
            b.set(u, 0, w, "minecraft:spruce_planks")
        for u in (0, width - 1):
            if w % 4 == 0:
                for v in range(-8, 0):
                    b.set(u, v, w, "minecraft:stripped_spruce_log[axis=y]")
                b.set(u, 1, w, "minecraft:spruce_fence")
                b.set(u, 2, w, "minecraft:lantern[hanging=false]") if w % 8 == 0 else None
    return width, length
