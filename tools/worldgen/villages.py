"""Villages that are not street grids: Iki Town's festival ring of stilt huts."""
from __future__ import annotations

import math
import random

from . import arch, furn, plants
from .buildings import npc
from .canvas import Canvas
from .kit import B

KOKO = ("minecraft:yellow_concrete", "minecraft:black_concrete", "minecraft:orange_concrete")
BUNTING = ["red", "yellow", "orange", "white"]


def festival_stage(c: Canvas, x, y, z, rng) -> tuple[int, int]:
    """Iki Town's raised wooden stage, centred on (x, z): steps on four sides, rope rail,
    lantern posts with bunting, drums, and Tapu Koko's totem at the north end. Hala stands on it."""
    b = arch.Bld(c, x - 9, y, z + 9, "south")      # front (south) edge at z + 9
    W = D = 19
    b.clear_above(-2, -2, W + 1, D + 1, 20)
    b.foundation(0, 0, W - 1, D - 1, "minecraft:stripped_spruce_log[axis=y]")
    for u in range(W):
        for w in range(D):
            b.set(u, 0, w, "minecraft:spruce_planks")
            edge = u in (0, W - 1) or w in (0, D - 1)
            b.set(u, 1, w, "minecraft:stripped_spruce_wood[axis=y]" if edge else
                  ("minecraft:jungle_planks" if (u // 3 + w // 3) % 2 else "minecraft:stripped_jungle_wood[axis=y]"))
    # steps in the middle of every side
    for k in range(-2, 3):
        c_u = W // 2 + k
        b.set(c_u, 1, -1, "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight]")
        b.set(c_u, 1, D, "minecraft:spruce_stairs[facing=south,half=bottom,shape=straight]")
        b.set(-1, 1, D // 2 + k, "minecraft:spruce_stairs[facing=east,half=bottom,shape=straight]")
        b.set(W, 1, D // 2 + k, "minecraft:spruce_stairs[facing=west,half=bottom,shape=straight]")
    # posts: corners and mid-sides, with lanterns and bunting strung between them
    posts = [(0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1), (W // 2 - 4, 0), (W // 2 + 4, 0),
             (0, D // 2 - 4), (W - 1, D // 2 - 4), (0, D // 2 + 4), (W - 1, D // 2 + 4)]
    for u, w in posts:
        for v in range(2, 8):
            b.set(u, v, w, "minecraft:stripped_dark_oak_log[axis=y]")
        b.set(u, 8, w, "minecraft:campfire[lit=true]")
    for u in range(1, W - 1):
        for w in (0, D - 1):
            if (u, w) in posts:
                continue
            if abs(u - W // 2) > 2:
                b.set(u, 2, w, "minecraft:spruce_fence")
            b.set(u, 7, w, f"supplementaries:bunting_{BUNTING[u % 4]}[axis=x]")
    for w in range(1, D - 1):
        for u in (0, W - 1):
            if (u, w) in posts:
                continue
            if abs(w - D // 2) > 2:
                b.set(u, 2, w, "minecraft:spruce_fence")
            b.set(u, 7, w, f"supplementaries:bunting_{BUNTING[w % 4]}[axis=z]")
    # Tapu Koko totem at the back: a carved column with the guardian's crest and wings
    main, dark, acc = KOKO
    tu, tw = W // 2, D - 3
    for v in range(2, 12):
        b.set(tu, v, tw, dark if v in (2, 3) else "minecraft:stripped_dark_oak_log[axis=y]" if v < 6 else main)
    for du, v in ((-1, 8), (1, 8), (-2, 9), (2, 9), (-3, 10), (3, 10), (-1, 11), (1, 11), (0, 12),
                  (-2, 7), (2, 7), (-3, 8), (3, 8)):
        b.set(tu + du, v, tw, main if v > 8 else acc)
    b.set(tu, 10, tw - 1, dark), b.set(tu, 9, tw - 1, acc)
    for du in (-1, 1):
        b.set(tu + du, 2, tw, "minecraft:note_block"), b.set(tu + du, 3, tw, "minecraft:red_carpet")
    for du in (-4, 4):
        furn.place_tall(c, *b.world(tu + du, 2, tw), "tiki_torch")
    b.sign(W // 2, 2, -2, ["Iki Town", "Festival Stage", "", "Tapu Koko watches"], wood="dark_oak", wall=False)
    npc(b, W // 2, 2, D // 2 + 2, "alola:hala")
    return W, D


def iki_town(t, rng: random.Random):
    from . import alola_map
    from .landmarks import place, reserve
    c = t.c
    x, z, y = alola_map.TOWNS["Iki Town"]
    b = B(c, x, y, z, "south")
    # the plaza: packed earth ring, stone path ring, grass beyond
    for du in range(-44, 45):
        for dw in range(-44, 45):
            d = math.hypot(du, dw)
            xx, zz = x + du, z + dw
            if not c.inside(xx, zz) or d > 44:
                continue
            i, j = zz - c.z0, xx - c.x0
            if d <= 17:
                c.top[i, j] = c.sid("minecraft:packed_mud" if (du + dw) % 5 else "minecraft:mud_bricks")
            elif d <= 19.5:
                c.top[i, j] = c.sid("mcwpaths:andesite_flagstone_path" if (du * 3 + dw) % 4 else "minecraft:dirt_path")
    festival_stage(c, x, y, z, rng)
    reserve(t, x - 12, z - 12, x + 12, z + 12)
    # spectator benches in a ring round the stage, tiki torches between them
    for a in range(0, 360, 20):
        r = 15
        u, w = round(r * math.cos(math.radians(a))), round(r * math.sin(math.radians(a)))
        if abs(u) <= 3 or abs(w) <= 3:
            continue   # keep the four approaches clear
        face = ("west" if u > 0 else "east") if abs(u) > abs(w) else ("north" if w > 0 else "south")
        c.set(x + u, y + 1, z + w, furn.piece("bench", face))
    for a in range(10, 360, 40):
        u, w = round(18.5 * math.cos(math.radians(a))), round(18.5 * math.sin(math.radians(a)))
        furn.place_tall(c, x + u, y + 1, z + w, "tiki_torch")
    # stilt huts in a ring facing the stage, each with a path in
    names = ["Kahuna Hala's House", None, None, "Iki Town Shop", None, None, None, None]
    ring = 32
    for k, a in enumerate(range(0, 360, 45)):
        if a in (225, 270):                 # leave the Mahalo Trail side (north, -z) open
            continue
        rad = math.radians(a + 22.5)
        hx, hz = x + round(ring * math.cos(rad)), z + round(ring * math.sin(rad))
        dx, dz = x - hx, z - hz
        facing = ("east" if dx > 0 else "west") if abs(dx) > abs(dz) else ("south" if dz > 0 else "north")
        W, D = (13, 9) if k == 0 else (9, 7)
        bb = B(c, hx, y, hz, facing)
        ox, _, oz = bb.world(-(W // 2), 0, -3)
        place(t, arch.house, ox, y, oz, facing, rng, W=W, D=D, style="iki", yard=True, label=names[k % len(names)])
        # path from the hut to the ring
        for s in range(0, 14):
            px, pz = hx + round(dx * s / ring), hz + round(dz * s / ring)
            if c.inside(px, pz) and math.hypot(px - x, pz - z) > 19.5:
                c.top[pz - c.z0, px - c.x0] = c.sid("minecraft:dirt_path")
    # gardens: palms and hibiscus between the huts
    for a in range(0, 360, 45):
        rad = math.radians(a)
        px, pz = x + round(26 * math.cos(rad)), z + round(26 * math.sin(rad))
        if c.inside(px, pz):
            plants.palm(c, px, c.surface(px, pz), pz, rng, furn.piece("palm_log"), furn.piece("palm_leaves"))
            for k in range(6):
                fx, fz = px + rng.randint(-3, 3), pz + rng.randint(-3, 3)
                if c.get(fx, c.surface(fx, fz) + 1, fz) == "minecraft:air":
                    c.set(fx, c.surface(fx, fz) + 1, fz, rng.choice(["wilderwild:red_hibiscus", "wilderwild:yellow_hibiscus",
                                                                     "wilderwild:pink_hibiscus", "minecraft:azure_bluet"]))
    c.sign(x, y + 1, z + 22, ["Iki Town", "", "Home of the", "Kahuna"], wood="dark_oak", rotation=0)
    reserve(t, x - 44, z - 44, x + 44, z + 44)
