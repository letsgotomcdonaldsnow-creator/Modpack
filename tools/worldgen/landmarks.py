"""Place every town, trial site and landmark of Alola on the map."""
from __future__ import annotations

import math
import random

import numpy as np

from . import alola_map, arch, buildings as bl, furn, plants, special as sp, terrain as T, tour
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
    tour.record(fn.__name__, kw.get("label") or kw.get("name"), x, y, z, facing, W, D)
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


def back_street(t, rng, y, x1, x2, z, style="plantation", ground_state="minecraft:polished_andesite"):
    """A residential street with houses on both sides."""
    c = t.c
    ground(c, x1, z - 2, x2, z + 2, ground_state, y)
    items = [(arch.house, rng.choice([9, 11]), {"style": style}) for _ in range(40)]
    for it in items:
        it[2]["W"] = it[1]
    xs = x1
    north = []
    width = 0
    for it in items:
        if width + it[1] + 4 > (x2 - x1):
            break
        north.append(it)
        width += it[1] + 4
    street_row(t, rng, y, x1, z - 4, "north", north)
    street_row(t, rng, y, x1 + 3, z + 4, "south", north[:-1])
    lamps_along(c, x1, z - 3, x2, z - 3, y, every=16)


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
    from . import city
    city.hauoli(t, rng)
    mx, mz, _ = alola_map.TOWNS["Hau'oli Marina"]
    reserve(t, mx - 20, mz - 10, mx + 20, mz + 60)
    # Trainers' School on the Outskirts, its schoolyard gate opening onto Route 1
    from . import grand
    place(t, grand.trainers_school, -606, TOWN_Y["Hau'oli Outskirts"], -493, "south", rng)


def player_home(t, rng):
    c = t.c
    x, z = alola_map.TOWNS["Player's House"][:2]
    y = TOWN_Y["Player's House"]
    place(t, arch.house, x - 6, y, z + 6, "south", rng, W=13, D=11, style="plantation", floors=2,
          roof_colour="red_terracotta", label="Your House", beds=1, yard=True)
    lx, lz = alola_map.TOWNS["Kukui's Lab"][:2]
    place(t, sp.lab, lx - 6, TOWN_Y["Kukui's Lab"], lz + 5, "south", rng)


def iki_town(t, rng):
    from . import villages
    villages.iki_town(t, rng)


def melemele_misc(t, rng):
    c = t.c
    # Route 2 Pokémon Center + motel + berry fields
    x, z = alola_map.TOWNS["Route 2 Pokemon Center"][:2]
    y = TOWN_Y["Route 2 Pokemon Center"]
    place(t, bl.pokemon_center, x + 8, y, z - 8, "west", rng, name="Route 2")
    place(t, arch.house, x - 20, y, z - 16, "east", rng, W=15, D=9, label="Route 2 Motel", beds=3)
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
    from . import city
    city.heahea(t, rng)
    city.paniola(t, rng)
    # Paniola Ranch
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
    place(t, arch.house, x + 6, y, z + 22, "north", rng, W=15, D=9, label="Route 8 Motel", beds=3)
    # Lush Jungle (Mallow)
    x, z = alola_map.TOWNS["Lush Jungle"][:2]
    y = TOWN_Y["Lush Jungle"]
    sp.trial_gate(c, x - 3, y, z - 16, "north", rng, "Captain Mallow")
    b = B(c, x, y, z, "south")
    b.disc(0, 0, 0, 7, "minecraft:moss_block")
    bl.npc(b, 0, 1, 0, "alola:mallow")
    # Konikoni City (Kahuna Olivia's arena north of the market street)
    city.konikoni(t, rng)
    x, z = alola_map.TOWNS["Konikoni City"][:2]
    y = TOWN_Y["Konikoni City"]
    place(t, sp.arena, x - 8, y, z - 40, "south", rng, npc_cls="alola:olivia", label="Kahuna Olivia",
          lines=("Grand Trial", "Akala Island"))
    # Memorial Hill + Ruins of Life
    x, z = alola_map.TOWNS["Memorial Hill"][:2]
    place(t, sp.grave_field, x - 12, TOWN_Y["Memorial Hill"], z + 8, "south", rng, rows=4, cols=8, name="Memorial Hill")
    x, z = alola_map.TOWNS["Ruins of Life"][:2]
    place(t, sp.tapu_ruins, x - 9, TOWN_Y["Ruins of Life"], z + 10, "south", rng, tapu="lele", name="Ruins of Life")


# ======================================================================= Ula'ula

def ulaula(t, rng):
    from . import city
    c = t.c
    city.malie(t, rng)
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
        b.set(u, 1, -1, "minecraft:nether_brick_fence"), b.set(u, 1, 1, "minecraft:nether_brick_fence")
    for a in range(0, 360, 45):
        tx, tz = gx + int(18 * math.cos(math.radians(a))), gz + int(18 * math.sin(math.radians(a)))
        plants.cherry(c, tx, c.surface(tx, tz), tz, rng)
        c.set(tx + 2, c.surface(tx + 2, tz) + 1, tz, furn.piece("paper_lamp"))
    place(t, arch.house, gx + 20, gy, gz - 26, "south", rng, W=11, D=9, style="malie",
          label="Malie Garden Tea House", beds=0)
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
        place(t, arch.house, hx, y, hz, f, rng, W=9, D=8, style="tapu", yard=True)
    place(t, sp.arena, x - 8, y, z + 36, "north", rng, npc_cls="alola:nanu", label="Kahuna Nanu",
          lines=("Grand Trial", "Ula'ula Island"))
    # Haina Desert: Ruins of Abundance
    x, z = alola_map.TOWNS["Ruins of Abundance"][:2]
    place(t, sp.tapu_ruins, x - 9, TOWN_Y["Ruins of Abundance"], z + 10, "south", rng, tapu="bulu", name="Ruins of Abundance")
    # Thrifty Megamart (abandoned), Aether House
    x, z = alola_map.TOWNS["Thrifty Megamart"][:2]
    place(t, sp.megamart, x - 20, TOWN_Y["Thrifty Megamart"], z - 16, "south", rng)
    x, z = alola_map.TOWNS["Aether House"][:2]
    place(t, arch.house, x - 6, TOWN_Y["Aether House"], z - 6, "south", rng, W=13, D=11, style="modern", floors=2,
          label="Aether House", beds=2)
    # Po Town
    x, z = alola_map.TOWNS["Po Town"][:2]
    y = TOWN_Y["Po Town"]
    sp.po_town_walls(c, x - 46, z - 36, x + 46, z + 36, y)
    place(t, sp.shady_house, x - 13, y, z - 12, "south", rng)
    place(t, bl.pokemon_center, x - 40, y, z + 30, "north", rng, name="Po Town")
    for k, hx in enumerate((x + 20, x + 32)):
        place(t, arch.house, hx, y, z + 30, "north", rng, W=9, D=8, style="po")
    for gx2 in (x - 5, x + 5):
        bl.SETUP.append((gx2, y + 1, z + 38, f"spawnnpcat {gx2 + 0.5} {y + 1} {z + 38.5} alola:skull_grunt"))
    reserve(t, x - 48, z - 38, x + 48, z + 38)
    # Pokémon League on Mount Lanakila
    x, z = alola_map.TOWNS["Pokemon League"][:2]
    from . import grand
    place(t, grand.pokemon_league, x - 22, TOWN_Y["Pokemon League"], z + 31, "south", rng)


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
    place(t, arch.house, x - 6, y, z - 4, "south", rng, W=13, D=9, style="paniola", label="Hapu's House", beds=1,
          yard=True)
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


EXTRA_WAYSTONES = ["Iki Town", "Ten Carat Hill", "Wela Volcano Park", "Lush Jungle",
                   "Hano Grand Resort", "Malie Garden", "Vast Poni Canyon", "Altar of the Sunne", "Pokemon League",
                   "Exeggutor Island", "Mount Hokulani", "Haina Desert"]


def waystones(c: Canvas):
    from . import multiplayer
    for name in EXTRA_WAYSTONES:
        x, z, _ = alola_map.TOWNS[name]
        spot = multiplayer.free_spot(c, x + 8, z + 8)
        if spot:
            multiplayer.waystone(c, *spot, name.replace("Pokemon", "Pokémon"))


def build_all(c: Canvas, t: T.Terrain, rng: random.Random):
    from . import multiplayer
    bl.SETUP.clear()
    tour.PLACED.clear()
    multiplayer.WAYSTONES.clear()
    hauoli(t, rng)
    player_home(t, rng)
    iki_town(t, rng)
    melemele_misc(t, rng)
    x, z, y = alola_map.TOWNS["Aether Paradise"]
    from . import grand
    grand.aether_paradise(c, x, y, z, rng)
    reserve(t, x - 75, z - 75, x + 75, z + 95)
    akala(t, rng)
    ulaula(t, rng)
    poni(t, rng)
    waystones(c)
    connect_all(c)
    arch.fix_shapes(c)
