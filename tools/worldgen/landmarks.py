"""Place every town, trial site and landmark of Alola on the map."""
from __future__ import annotations

import math
import random

import numpy as np

from . import alola_map, buildings as bl, furn, plants, special as sp, terrain as T
from .canvas import SEA, Canvas
from .kit import B, connect_all

TOWN_Y = {name: y for name, (x, z, y) in alola_map.TOWNS.items()}


def reserve(t: T.Terrain, x1, z1, x2, z2):
    c = t.c
    i1, i2 = sorted((z1 - c.z0, z2 - c.z0))
    j1, j2 = sorted((x1 - c.x0, x2 - c.x0))
    t.no_trees[max(0, i1 - 2):i2 + 3, max(0, j1 - 2):j2 + 3] = True


def ground(c: Canvas, x1, z1, x2, z2, state, y=None):
    """Repaint the terrain surface of a rectangle (roads, plazas)."""
    sid = c.sid(state)
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            if not c.inside(x, z):
                continue
            i, j = z - c.z0, x - c.x0
            if y is not None:
                c.height[i, j] = y
            c.top[i, j] = sid
            if c.water[i, j] > c.height[i, j]:
                c.water[i, j] = -64


def place(t, fn, x, y, z, facing, rng, **kw):
    W, D = fn(t.c, x, y, z, facing, rng, **kw)
    b = B(t.c, x, y, z, facing)
    xs, zs = zip(*[b.world(u, 0, w)[::2] for u, w in ((-2, -3), (W + 1, -3), (-2, D + 1), (W + 1, D + 1))])
    reserve(t, min(xs), min(zs), max(xs), max(zs))
    return W, D


def street_row(t, rng, y, x_start, z_front, side, items, gap=4):
    """Place buildings along an east-west street. side='north' faces south, 'south' faces north."""
    x = x_start
    for fn, W, kw in items:
        if side == "north":
            place(t, fn, x, y, z_front, "south", rng, **kw)
        else:
            place(t, fn, x + W - 1, y, z_front, "north", rng, **kw)
        x += W + gap
    return x


def lamps_along(c, x1, z1, x2, z2, y, every=12):
    n = int(max(abs(x2 - x1), abs(z2 - z1)) / every)
    for i in range(n + 1):
        x = int(x1 + (x2 - x1) * i / max(1, n))
        z = int(z1 + (z2 - z1) * i / max(1, n))
        furn.place_tall(c, x, y + 1, z, "street_lamp")


def planter_palm(c, x, y, z, rng):
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            c.set(x + dx, y, z + dz, "minecraft:grass_block" if (dx, dz) == (0, 0) else "minecraft:stone_brick_slab[type=top]")
    plants.palm(c, x, y, z, rng, furn.piece("palm_log"), furn.piece("palm_leaves"))


def beach_set(c, x, y, z, rng, facing="south"):
    c.set(x, y + 1, z, furn.piece("sun_lounger", facing))
    c.set(x + 2, y + 1, z, furn.piece("beach_towel", facing))
    for v in range(1, 4):
        c.set(x + 1, y + v, z - 1, "minecraft:bamboo_fence" if v < 3 else "minecraft:bamboo_fence")
    col = rng.choice(["red", "yellow", "light_blue", "white", "orange"])
    for dx in (-1, 0, 1):
        for dz in (-2, -1, 0):
            c.set(x + 1 + dx, y + 4, z + dz, f"minecraft:{col}_wool" if (dx, dz) == (0, -1) else f"minecraft:{col}_carpet")


# ======================================================================= Melemele

def hauoli(t, rng):
    c = t.c
    y = TOWN_Y["Hau'oli City"]
    x1, x2 = -960, -620
    road_z = -440
    ground(c, x1, road_z - 4, x2, road_z + 4, "minecraft:gray_concrete", y)
    ground(c, x1, road_z - 6, x2, road_z - 5, "minecraft:smooth_stone", y)
    ground(c, x1, road_z + 5, x2, road_z + 6, "minecraft:smooth_stone", y)
    for x in range(x1, x2, 6):
        for dx in range(3):
            c.set(x + dx, y, road_z, "minecraft:white_concrete")
    lamps_along(c, x1, road_z - 6, x2, road_z - 6, y)
    lamps_along(c, x1 + 6, road_z + 6, x2, road_z + 6, y)
    H = bl.house
    north = [
        (bl.pokemon_center, 17, {"name": "Hau'oli City"}),
        (bl.malasada_shop, 11, {}),
        (bl.shop, 13, {"label": "Apparel Shop", "color": "minecraft:pink_concrete"}),
        (bl.shop, 13, {"label": "Salon", "color": "minecraft:magenta_concrete"}),
        (bl.hotel, 23, {"label": "Hau'oli City Hall", "floors": 3, "wall": "minecraft:smooth_quartz",
                         "trim": "minecraft:yellow_concrete"}),
        (bl.shop, 13, {"label": "Tourist Bureau", "color": "minecraft:cyan_concrete"}),
        (bl.shop, 13, {"label": "Police Station", "color": "minecraft:blue_concrete"}),
        (H, 10, {"W": 10}), (H, 9, {"W": 9}), (H, 11, {"W": 11}),
        (bl.hotel, 29, {"label": "Trainers' School", "floors": 2, "W": 29, "D": 17, "wall": "minecraft:white_terracotta",
                         "trim": "minecraft:green_concrete"}),
        (H, 10, {"W": 10}), (H, 9, {"W": 9}),
    ]
    street_row(t, rng, y, x1 + 38, road_z - 8, "north", north)
    south = [
        (bl.hotel, 31, {"label": "Hau'oli Shopping Mall", "floors": 2, "W": 31, "D": 17, "trim": "minecraft:orange_concrete"}),
        (bl.shop, 13, {"label": "Poké Mart", "color": "minecraft:blue_concrete"}),
        (H, 10, {"W": 10}), (H, 11, {"W": 11}), (H, 9, {"W": 9}),
        (bl.shop, 13, {"label": "Ice Cream Shop", "color": "minecraft:light_blue_concrete"}),
        (H, 10, {"W": 10}), (H, 10, {"W": 10}), (H, 11, {"W": 11}), (H, 9, {"W": 9}),
    ]
    street_row(t, rng, y, x1 + 42, road_z + 8, "south", south)
    # palms in planters along the boulevard
    for x in range(x1 + 10, x2, 24):
        planter_palm(c, x, y, road_z - 6, rng)
    # central fountain plaza
    fx, fz = -790, road_z
    b = B(c, fx, y, fz, "south")
    b.disc(0, 0, 0, 9, "minecraft:smooth_stone")
    b.disc(0, 0, 0, 5, "minecraft:water")
    b.cylinder(0, 0, 1, 1, 5, "minecraft:quartz_block")
    for v in range(1, 5):
        b.set(0, v, 0, "minecraft:quartz_pillar[axis=y]")
    b.set(0, 5, 0, "minecraft:water")
    c.sign(fx, y + 1, fz + 8, ["Hau'oli City", "", "Melemele Island", ""], wood="birch", rotation=0)
    # beachfront south of the city
    for x in range(x1 + 20, x2 - 40, 14):
        z = road_z + 42
        if c.inside(x, z) and not c.is_water(x, z):
            beach_set(c, x, c.surface(x, z), z, rng)
    # marina: pier and ferry
    mx, mz = -955, -452
    place(t, bl.ferry_terminal, mx - 7, TOWN_Y["Hau'oli Marina"], mz + 10, "south", rng, label="Hau'oli Marina",
          dest="Heahea City")
    bl.pier(c, mx - 2, SEA + 1, mz + 14, "north", length=40, width=5)
    bl.ferry_ship(c, mx + 6, SEA + 1, mz + 18, "north", rng, "S.S. Heahea")
    reserve(t, mx - 20, mz - 10, mx + 20, mz + 60)


def player_home(t, rng):
    c = t.c
    x, z = alola_map.TOWNS["Player's House"][:2]
    y = TOWN_Y["Player's House"]
    place(t, bl.house, x - 6, y, z + 6, "south", rng, W=13, D=11, wall="minecraft:white_terracotta",
          roof=("minecraft:dark_oak_stairs", "minecraft:dark_oak_planks"), label="Your House", beds=1)
    lx, lz = alola_map.TOWNS["Kukui's Lab"][:2]
    place(t, sp.lab, lx - 6, TOWN_Y["Kukui's Lab"], lz + 5, "south", rng)


def iki_town(t, rng):
    c = t.c
    x, z = alola_map.TOWNS["Iki Town"][:2]
    y = TOWN_Y["Iki Town"]
    b = B(c, x, y, z, "south")
    b.disc(0, 0, 0, 30, "minecraft:packed_mud")
    b.disc(0, 0, 0, 22, "minecraft:dirt_path")
    place(t, sp.iki_stage, x - 8, y, z + 8, "south", rng)
    homes = [(x - 38, z - 16, "east"), (x + 38, z - 10, "west"), (x - 36, z + 20, "east"), (x + 36, z + 24, "west"),
             (x - 8, z - 38, "south")]
    for i, (hx, hz, f) in enumerate(homes):
        place(t, bl.house, hx, y, hz, f, rng, W=9, D=8, wall=rng.choice(["minecraft:stripped_oak_wood[axis=y]",
              "minecraft:bamboo_block[axis=y]", "minecraft:birch_planks"]),
              roof=("minecraft:dark_oak_stairs", "minecraft:dark_oak_planks"),
              label="Kahuna Hala's House" if i == 0 else None)
    for a in range(0, 360, 40):
        tx, tz = x + int(26 * math.cos(math.radians(a))), z + int(26 * math.sin(math.radians(a)))
        furn.place_tall(c, tx, y + 1, tz, "tiki_torch")
    c.sign(x, y + 1, z + 30, ["Iki Town", "", "Home of the", "Kahuna"], wood="dark_oak", rotation=0)


def melemele_misc(t, rng):
    c = t.c
    # Route 2 Pokémon Center + motel + berry fields
    x, z = alola_map.TOWNS["Route 2 Pokemon Center"][:2]
    y = TOWN_Y["Route 2 Pokemon Center"]
    place(t, bl.pokemon_center, x + 8, y, z - 8, "west", rng, name="Route 2")
    place(t, bl.house, x - 20, y, z - 16, "east", rng, W=15, D=9, label="Route 2 Motel", beds=3)
    for row in range(5):
        for k in range(12):
            bx, bz = x - 20 + k * 3, z + 14 + row * 3
            if c.inside(bx, bz):
                c.set(bx, c.surface(bx, bz) + 1, bz, "minecraft:sweet_berry_bush[age=3]")
    # cemetery
    x, z = alola_map.TOWNS["Hau'oli Cemetery"][:2]
    place(t, sp.grave_field, x - 15, TOWN_Y["Hau'oli Cemetery"], z + 9, "south", rng)
    # Verdant Cavern (Ilima's trial)
    x, z = alola_map.TOWNS["Verdant Cavern"][:2]
    y = TOWN_Y["Verdant Cavern"]
    sp.cave_entrance(c, x, y, z + 12, "south", rng, depth=28, name="Captain Ilima", npc_cls="alola:ilima")
    reserve(t, x - 15, z - 30, x + 15, z + 16)
    # Ruins of Conflict (Tapu Koko)
    x, z = alola_map.TOWNS["Ruins of Conflict"][:2]
    place(t, sp.tapu_ruins, x - 9, TOWN_Y["Ruins of Conflict"], z + 10, "south", rng, tapu="koko", name="Ruins of Conflict")
    # Ten Carat Hill and Melemele Meadow signs, Big Wave Beach
    for name in ("Ten Carat Hill", "Melemele Meadow", "Kala'e Bay", "Big Wave Beach"):
        x, z = alola_map.TOWNS[name][:2]
        c.set(x, c.ground(x, z) + 1, z, "minecraft:spruce_fence")
        c.sign(x, c.ground(x, z) + 2, z, [name, "", "Melemele Island"], wood="spruce", rotation=0)
    x, z = alola_map.TOWNS["Big Wave Beach"][:2]
    for k in range(6):
        bx, bz = x - 15 + k * 6, z + 6
        if c.inside(bx, bz) and not c.is_water(bx, bz):
            beach_set(c, bx, c.surface(bx, bz), bz, rng)
    place(t, sp.arena, -560 - 8, TOWN_Y["Iki Town"], -770 - 40, "south", rng, npc_cls="alola:hau", label="Hau's spot",
          lines=("Iki Town", "Rival battle"))


# ======================================================================= Akala

def akala(t, rng):
    c = t.c
    # Heahea City
    x, z = alola_map.TOWNS["Heahea City"][:2]
    y = TOWN_Y["Heahea City"]
    ground(c, x - 80, z - 3, x + 80, z + 3, "minecraft:gray_concrete", y)
    street_row(t, rng, y, x - 78, z - 5, "north", [
        (bl.pokemon_center, 17, {"name": "Heahea City"}),
        (bl.hotel, 25, {"label": "Tide Song Hotel", "floors": 5, "W": 25, "trim": "minecraft:light_blue_concrete"}),
        (bl.shop, 15, {"label": "Dimensional Research Lab", "color": "minecraft:purple_concrete", "W": 15}),
        (bl.house, 10, {"W": 10}), (bl.house, 10, {"W": 10}), (bl.house, 11, {"W": 11}),
    ])
    street_row(t, rng, y, x - 70, z + 5, "south", [
        (bl.shop, 13, {"label": "Surf Association", "color": "minecraft:cyan_concrete"}),
        (bl.house, 10, {"W": 10}), (bl.house, 9, {"W": 9}), (bl.malasada_shop, 11, {}),
        (bl.house, 10, {"W": 10}),
    ])
    lamps_along(c, x - 78, z - 4, x + 78, z - 4, y)
    place(t, bl.ferry_terminal, x - 60, y, z - 36, "north", rng, label="Heahea Ferry Terminal", dest="Hau'oli / Malie")
    bl.pier(c, x - 58, SEA + 1, z - 60, "north", length=26)
    bl.ferry_ship(c, x - 50, SEA + 1, z - 70, "west", rng, "S.S. Malie")
    # Paniola Town + Ranch
    x, z = alola_map.TOWNS["Paniola Town"][:2]
    y = TOWN_Y["Paniola Town"]
    ground(c, x - 40, z - 3, x + 40, z + 3, "minecraft:coarse_dirt", y)
    street_row(t, rng, y, x - 40, z - 5, "north", [
        (bl.pokemon_center, 17, {"name": "Paniola Town"}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:stripped_spruce_wood[axis=y]", "roof": ("minecraft:spruce_stairs", "minecraft:spruce_planks")}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:stripped_spruce_wood[axis=y]", "roof": ("minecraft:spruce_stairs", "minecraft:spruce_planks")}),
    ])
    street_row(t, rng, y, x - 36, z + 5, "south", [
        (bl.shop, 13, {"label": "Paniola Saloon", "color": "minecraft:brown_concrete"}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:stripped_spruce_wood[axis=y]", "roof": ("minecraft:spruce_stairs", "minecraft:spruce_planks")}),
        (bl.house, 10, {"W": 10}),
    ])
    x, z = alola_map.TOWNS["Paniola Ranch"][:2]
    y = TOWN_Y["Paniola Ranch"]
    place(t, sp.barn, x - 7, y, z - 8, "south", rng)
    for fx in range(x - 35, x + 36):
        for fz in (z + 2, z + 34):
            c.set(fx, y + 1, fz, "minecraft:oak_fence")
    for fz in range(z + 2, z + 35):
        for fx in (x - 35, x + 35):
            c.set(fx, y + 1, fz, "minecraft:oak_fence")
    for k in range(8):
        bl.SETUP.append((x - 25 + k * 7, y + 1, z + 18, f"spawnpokemonat {x - 25 + k * 7} {y + 1} {z + 18} "
                         + ["mudbray", "tauros", "miltank", "mudsdale"][k % 4] + " level=15"))
    # Brooklet Hill (Lana)
    x, z = alola_map.TOWNS["Brooklet Hill"][:2]
    y = TOWN_Y["Brooklet Hill"]
    sp.trial_gate(c, x - 3, y, z - 14, "north", rng, "Captain Lana")
    b = B(c, x - 15, y, z + 5, "south")
    for u in range(0, 30):
        for w in range(0, 4):
            b.set(u, 0, w, "minecraft:spruce_planks")
    bl.npc(b, 15, 1, 2, "alola:lana")
    # Royal Avenue
    x, z = alola_map.TOWNS["Royal Avenue"][:2]
    y = TOWN_Y["Royal Avenue"]
    place(t, sp.royal_dome, x - 18, y, z + 18, "south", rng)
    place(t, bl.pokemon_center, x - 44, y, z - 26, "south", rng, name="Royal Avenue")
    place(t, bl.shop, x + 24, y, z - 26, "south", rng, label="Thrifty Megamart", color="minecraft:orange_concrete", W=19, D=15)
    # Hano Grand Resort
    x, z = alola_map.TOWNS["Hano Grand Resort"][:2]
    y = TOWN_Y["Hano Grand Resort"]
    place(t, bl.hotel, x - 17, y, z - 8, "south", rng, label="Hano Grand Resort", floors=6, W=35, D=17,
          trim="minecraft:yellow_concrete")
    pool = B(c, x - 14, y, z + 4, "south")
    pool.box(0, 0, 0, 28, 0, 12, furn.piece("pool_tile"))
    pool.box(1, 0, 1, 27, 0, 11, "minecraft:water")
    pool.box(1, -1, 1, 27, -1, 11, furn.piece("pool_tile"))
    for k in range(0, 28, 5):
        c.set(x - 14 + k, y + 1, z + 3, furn.piece("sun_lounger", "south"))
    for k in range(10):
        bx, bz = x - 30 + k * 7, z + 30
        if c.inside(bx, bz) and not c.is_water(bx, bz):
            beach_set(c, bx, c.surface(bx, bz), bz, rng)
    # Wela Volcano Park (Kiawe)
    x, z = alola_map.TOWNS["Wela Volcano Park"][:2]
    y = TOWN_Y["Wela Volcano Park"]
    place(t, bl.shop, x - 30, y, z + 40, "south", rng, label="Wela Volcano Park", color="minecraft:red_concrete", W=11, D=7)
    b = B(c, x + 24, c.surface(x + 24, z) , z, "west")
    for u in range(-4, 5):
        for w in range(0, 9):
            b.set(u, 0, w, "minecraft:polished_blackstone_bricks")
    for u in (-4, 4):
        b.set(u, 1, 0, "minecraft:campfire[lit=true]"), b.set(u, 1, 8, "minecraft:campfire[lit=true]")
    bl.npc(b, 0, 1, 6, "alola:kiawe")
    sp.trial_gate(c, *b.world(-3, 0, -2), "west", rng, "Captain Kiawe")
    # Route 8: PC, motel, Aether Base, Fossil Restoration Center
    x, z = alola_map.TOWNS["Route 8"][:2]
    y = TOWN_Y["Route 8"]
    place(t, bl.pokemon_center, x - 26, y, z - 8, "south", rng, name="Route 8")
    place(t, bl.shop, x - 4, y, z - 8, "south", rng, label="Fossil Restoration Center", color="minecraft:brown_concrete")
    place(t, bl.shop, x + 14, y, z - 8, "south", rng, label="Aether Base", color="minecraft:yellow_concrete")
    place(t, bl.house, x + 6, y, z + 22, "north", rng, W=15, D=9, label="Route 8 Motel", beds=3)
    # Lush Jungle (Mallow)
    x, z = alola_map.TOWNS["Lush Jungle"][:2]
    y = TOWN_Y["Lush Jungle"]
    sp.trial_gate(c, x - 3, y, z - 16, "north", rng, "Captain Mallow")
    b = B(c, x, y, z, "south")
    b.disc(0, 0, 0, 7, "minecraft:moss_block")
    bl.npc(b, 0, 1, 0, "alola:mallow")
    # Konikoni City
    x, z = alola_map.TOWNS["Konikoni City"][:2]
    y = TOWN_Y["Konikoni City"]
    ground(c, x - 70, z - 3, x + 70, z + 3, "minecraft:red_terracotta", y)
    pagoda = ("minecraft:red_nether_brick_stairs", "minecraft:red_nether_bricks")
    street_row(t, rng, y, x - 68, z - 5, "north", [
        (bl.pokemon_center, 17, {"name": "Konikoni City"}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:white_terracotta", "roof": pagoda, "label": "Olivia's Jewelry"}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:yellow_terracotta", "roof": pagoda, "label": "Herb Shop"}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:white_terracotta", "roof": pagoda, "label": "Incense Shop"}),
        (bl.house, 10, {"W": 10, "roof": pagoda}),
    ])
    street_row(t, rng, y, x - 60, z + 5, "south", [
        (bl.house, 10, {"W": 10, "roof": pagoda}), (bl.house, 11, {"W": 11, "roof": pagoda}),
        (bl.shop, 13, {"label": "Konikoni Market", "color": "minecraft:red_concrete"}),
        (bl.house, 10, {"W": 10, "roof": pagoda}),
    ])
    for k in range(-60, 70, 10):
        c.set(x + k, y + 1, z - 4, furn.piece("paper_lamp"))
    place(t, sp.lighthouse, x + 58, y, z + 30, "north", rng)
    place(t, sp.arena, x - 8, y, z - 40, "south", rng, npc_cls="alola:olivia", label="Kahuna Olivia",
          lines=("Grand Trial", "Akala Island"))
    # Memorial Hill + Ruins of Life
    x, z = alola_map.TOWNS["Memorial Hill"][:2]
    place(t, sp.grave_field, x - 12, TOWN_Y["Memorial Hill"], z + 8, "south", rng, rows=4, cols=8, name="Memorial Hill")
    x, z = alola_map.TOWNS["Ruins of Life"][:2]
    place(t, sp.tapu_ruins, x - 9, TOWN_Y["Ruins of Life"], z + 10, "south", rng, tapu="lele", name="Ruins of Life")


# ======================================================================= Ula'ula

def ulaula(t, rng):
    c = t.c
    x, z = alola_map.TOWNS["Malie City"][:2]
    y = TOWN_Y["Malie City"]
    ground(c, x - 90, z - 3, x + 90, z + 3, "minecraft:polished_andesite", y)
    japanese = ("minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles")
    street_row(t, rng, y, x - 88, z - 5, "north", [
        (bl.pokemon_center, 17, {"name": "Malie City"}),
        (bl.hotel, 27, {"label": "Malie Library", "floors": 2, "W": 27, "D": 19, "wall": "minecraft:stripped_dark_oak_wood[axis=y]",
                         "trim": "minecraft:red_concrete"}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:white_concrete", "roof": japanese}),
        (bl.shop, 13, {"label": "Apparel Shop", "color": "minecraft:pink_concrete"}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:white_concrete", "roof": japanese}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:white_concrete", "roof": japanese}),
    ])
    street_row(t, rng, y, x - 80, z + 5, "south", [
        (bl.shop, 17, {"label": "Malie Community Center", "color": "minecraft:red_concrete", "W": 17}),
        (bl.malasada_shop, 11, {}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:white_concrete", "roof": japanese}),
        (bl.house, 11, {"W": 11, "wall": "minecraft:white_concrete", "roof": japanese}),
        (bl.shop, 13, {"label": "Poké Mart", "color": "minecraft:blue_concrete"}),
    ])
    for k in range(-85, 90, 10):
        c.set(x + k, y + 1, z - 4, furn.piece("paper_lamp"))
    place(t, bl.ferry_terminal, x - 80, y, z + 50, "south", rng, label="Malie Ferry Terminal", dest="Heahea / Seafolk")
    bl.pier(c, x - 110, SEA + 1, z + 20, "east", length=26)
    bl.ferry_ship(c, x - 120, SEA + 1, z + 40, "east", rng, "S.S. Seafolk")
    # Malie Garden: pond, bridge, tea house
    gx, gz = alola_map.TOWNS["Malie Garden"][:2]
    gy = TOWN_Y["Malie Garden"]
    b = B(c, gx, gy, gz, "south")
    b.disc(0, 0, 0, 14, "minecraft:water")
    b.disc(0, -1, 0, 14, "minecraft:clay")
    for u in range(-15, 16):
        b.set(u, 1, 0, "minecraft:red_nether_brick_slab[type=bottom]")
        b.set(u, 0, 0, "minecraft:dark_oak_planks")
    for u in (-15, 15):
        b.set(u, 1, -1, "minecraft:red_nether_brick_fence"), b.set(u, 1, 1, "minecraft:red_nether_brick_fence")
    for a in range(0, 360, 45):
        tx, tz = gx + int(18 * math.cos(math.radians(a))), gz + int(18 * math.sin(math.radians(a)))
        plants.cherry(c, tx, c.surface(tx, tz), tz, rng)
        c.set(tx + 2, c.surface(tx + 2, tz) + 1, tz, furn.piece("paper_lamp"))
    place(t, bl.house, gx + 20, gy, gz - 26, "south", rng, W=11, D=9, wall="minecraft:stripped_bamboo_block[axis=y]",
          roof=japanese, label="Malie Garden Tea House", beds=0)
    reserve(t, gx - 22, gz - 22, gx + 22, gz + 22)
    # Mount Hokulani observatory
    x, z = alola_map.TOWNS["Mount Hokulani"][:2]
    place(t, sp.observatory, x - 10, TOWN_Y["Mount Hokulani"], z + 10, "south", rng)
    # Blush Mountain power plant
    x, z = alola_map.TOWNS["Blush Mountain"][:2]
    place(t, sp.power_plant, x - 12, TOWN_Y["Blush Mountain"], z + 8, "south", rng)
    # Tapu Village
    x, z = alola_map.TOWNS["Tapu Village"][:2]
    y = TOWN_Y["Tapu Village"]
    place(t, bl.pokemon_center, x - 8, y, z - 12, "south", rng, name="Tapu Village")
    for k, (hx, hz, f) in enumerate(((x - 30, z + 10, "north"), (x + 20, z + 12, "north"), (x + 26, z - 20, "west"))):
        place(t, bl.house, hx, y, hz, f, rng, W=9, D=8, wall="minecraft:cracked_stone_bricks",
              roof=("minecraft:cobblestone_stairs", "minecraft:mossy_cobblestone"))
    place(t, sp.arena, x - 8, y, z + 36, "north", rng, npc_cls="alola:nanu", label="Kahuna Nanu",
          lines=("Grand Trial", "Ula'ula Island"))
    # Haina Desert: Ruins of Abundance
    x, z = alola_map.TOWNS["Ruins of Abundance"][:2]
    place(t, sp.tapu_ruins, x - 9, TOWN_Y["Ruins of Abundance"], z + 10, "south", rng, tapu="bulu", name="Ruins of Abundance")
    # Thrifty Megamart (abandoned), Aether House
    x, z = alola_map.TOWNS["Thrifty Megamart"][:2]
    place(t, sp.megamart, x - 20, TOWN_Y["Thrifty Megamart"], z - 16, "south", rng)
    x, z = alola_map.TOWNS["Aether House"][:2]
    place(t, bl.house, x - 6, TOWN_Y["Aether House"], z - 6, "south", rng, W=13, D=10, wall="minecraft:white_concrete",
          roof=("minecraft:quartz_stairs", "minecraft:quartz_block"), label="Aether House", beds=2)
    # Po Town
    x, z = alola_map.TOWNS["Po Town"][:2]
    y = TOWN_Y["Po Town"]
    sp.po_town_walls(c, x - 46, z - 36, x + 46, z + 36, y)
    place(t, sp.shady_house, x - 13, y, z - 12, "south", rng)
    place(t, bl.pokemon_center, x - 40, y, z + 30, "north", rng, name="Po Town")
    for k, hx in enumerate((x + 20, x + 32)):
        place(t, bl.house, hx, y, z + 30, "north", rng, W=9, D=8, wall="minecraft:gray_concrete",
              roof=("minecraft:blackstone_stairs", "minecraft:blackstone"))
    for gx2 in (x - 5, x + 5):
        bl.SETUP.append((gx2, y + 1, z + 38, f"spawnnpcat {gx2 + 0.5} {y + 1} {z + 38.5} alola:skull_grunt"))
    reserve(t, x - 48, z - 38, x + 48, z + 38)
    # Pokémon League on Mount Lanakila
    x, z = alola_map.TOWNS["Pokemon League"][:2]
    place(t, sp.pokemon_league, x - 22, TOWN_Y["Pokemon League"], z + 22, "south", rng)


# ======================================================================= Poni

def poni(t, rng):
    c = t.c
    # Seafolk Village: houseboats and the Wailord restaurant around the harbour
    x, z = alola_map.TOWNS["Seafolk Village"][:2]
    for k, (bx, bz, f) in enumerate(((x - 30, z - 20, "east"), (x - 30, z + 5, "east"), (x + 10, z - 25, "south"),
                                     (x + 20, z + 10, "west"))):
        sp.houseboat(c, bx, SEA + 1, bz, f, rng)
    sp.wailord_restaurant(c, x - 10, SEA + 1, z + 30, "north", rng)
    bl.pier(c, x - 12, SEA + 1, z - 30, "south", length=60, width=4)
    place(t, bl.pokemon_center, x + 40, TOWN_Y["Poni Wilds"], z - 40, "west", rng, name="Seafolk Village")
    # Hapu's House + grand trial
    x, z = alola_map.TOWNS["Hapu's House"][:2]
    y = TOWN_Y["Hapu's House"]
    place(t, bl.house, x - 6, y, z - 4, "south", rng, W=13, D=10, wall="minecraft:stripped_spruce_wood[axis=y]",
          roof=("minecraft:spruce_stairs", "minecraft:spruce_planks"), label="Hapu's House", beds=1)
    place(t, sp.arena, x + 14, y, z + 6, "east", rng, npc_cls="alola:hapu", label="Kahuna Hapu",
          lines=("Grand Trial", "Poni Island"))
    # Ruins of Hope
    x, z = alola_map.TOWNS["Ruins of Hope"][:2]
    place(t, sp.tapu_ruins, x - 9, TOWN_Y["Ruins of Hope"], z + 10, "south", rng, tapu="fini", name="Ruins of Hope")
    # Exeggutor Island: giant palms
    x, z = alola_map.TOWNS["Exeggutor Island"][:2]
    for k in range(10):
        px, pz = x + rng.randint(-20, 20), z + rng.randint(-15, 15)
        if c.inside(px, pz) and not c.is_water(px, pz):
            plants.palm(c, px, c.surface(px, pz), pz, rng, furn.piece("palm_log"), furn.piece("palm_leaves"))
    # Vast Poni Canyon: Totem Kommo-o, Altar of the Sunne
    x, z = alola_map.TOWNS["Vast Poni Canyon"][:2]
    y = c.surface(x, z)
    sp.trial_gate(c, x - 3, y, z + 6, "south", rng, "Vast Poni Canyon")
    bl.SETUP.append((x, y + 1, z - 10, f"spawnnpcat {x + 0.5} {y + 1} {z - 9.5} alola:totem_kommoo"))
    x, z = alola_map.TOWNS["Altar of the Sunne"][:2]
    place(t, sp.altar, x - 12, TOWN_Y["Altar of the Sunne"], z + 12, "south", rng)
    # Battle Tree
    x, z = alola_map.TOWNS["Battle Tree"][:2]
    place(t, sp.battle_tree, x - 20, TOWN_Y["Battle Tree"], z + 20, "south", rng)
    place(t, bl.pokemon_center, x - 44, TOWN_Y["Battle Tree"], z + 30, "south", rng, name="Battle Tree")
    # Poni Meadow (Mina)
    x, z = alola_map.TOWNS["Poni Meadow"][:2]
    y = TOWN_Y["Poni Meadow"]
    b = B(c, x - 8, y, z + 8, "south")
    for i in range(6):
        u, w = 2 + i * 3, 4 + (i % 2) * 3
        b.set(u, 1, w, "minecraft:oak_fence"), b.set(u, 2, w, "minecraft:white_wool")
        b.set(u, 3, w, rng.choice(["minecraft:pink_wool", "minecraft:light_blue_wool", "minecraft:yellow_wool"]))
    bl.npc(b, 9, 1, 12, "alola:mina")
    sp.trial_gate(c, x - 8, y, z + 6, "south", rng, "Captain Mina")
    # Resolution Cave, Poni Plains, Poni Grove signs
    for name in ("Resolution Cave", "Poni Plains", "Poni Grove", "Poni Wilds", "Haina Desert", "Ula'ula Meadow",
                 "Exeggutor Island", "Lush Jungle", "Brooklet Hill", "Wela Volcano Park"):
        x, z = alola_map.TOWNS[name][:2]
        sx, sz = x + 3, z + 3
        if c.inside(sx, sz) and not c.is_water(sx, sz):
            gy = c.surface(sx, sz)
            c.set(sx, gy + 1, sz, "minecraft:spruce_fence")
            c.sign(sx, gy + 2, sz, [name, "", "Alola Region"], wood="spruce", rotation=0)
    x, z = alola_map.TOWNS["Resolution Cave"][:2]
    sp.cave_entrance(c, x, TOWN_Y["Resolution Cave"], z + 8, "south", rng, depth=20, name="Resolution Cave")


def build_all(c: Canvas, t: T.Terrain, rng: random.Random):
    bl.SETUP.clear()
    hauoli(t, rng)
    player_home(t, rng)
    iki_town(t, rng)
    melemele_misc(t, rng)
    x, z, y = alola_map.TOWNS["Aether Paradise"]
    sp.aether_paradise(c, x, y, z, rng)
    reserve(t, x - 75, z - 75, x + 75, z + 95)
    akala(t, rng)
    ulaula(t, rng)
    poni(t, rng)
    connect_all(c)
