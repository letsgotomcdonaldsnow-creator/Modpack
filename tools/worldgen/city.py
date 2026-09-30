"""City layout: a street grid with building frontages, plazas and a beach promenade.

Streets come from streets.py (Saro's asphalt, markings, sidewalks, lamps, median palms).
Buildings are lined up along each street side, facing it, lot by lot, skipping any lot
that would overlap something already built (tracked in an occupancy mask).
"""
from __future__ import annotations

import math
import random
from typing import Callable, Iterable

import numpy as np

from . import arch, furn, plants, streets
from .canvas import SEA, Canvas
from .kit import B


class City:
    def __init__(self, t, y: int, rng: random.Random):
        self.t, self.c, self.y, self.rng = t, t.c, y, rng
        self.occ = np.zeros(self.c.height.shape, dtype=bool)
        self.streets: list[streets.Street] = []

    # --------------------------------------------------------------- helpers
    def free(self, x1, z1, x2, z2) -> bool:
        c = self.c
        i1, i2 = sorted((z1 - c.z0, z2 - c.z0))
        j1, j2 = sorted((x1 - c.x0, x2 - c.x0))
        return not self.occ[i1:i2 + 1, j1:j2 + 1].any()

    def mark(self, x1, z1, x2, z2):
        c = self.c
        i1, i2 = sorted((z1 - c.z0, z2 - c.z0))
        j1, j2 = sorted((x1 - c.x0, x2 - c.x0))
        self.occ[i1:i2 + 1, j1:j2 + 1] = True
        self.t.no_trees[max(0, i1 - 1):i2 + 2, max(0, j1 - 1):j2 + 2] = True

    def street(self, s: streets.Street):
        streets.paint(self.c, s, self.rng)
        o = s.half + s.sidewalk
        if s.along_x:
            self.mark(s.x1, s.z1 - o, s.x2, s.z1 + o)
        else:
            self.mark(s.x1 - o, s.z1, s.x1 + o, s.z2)
        self.streets.append(s)

    def building(self, fn: Callable, x, z, facing, lot_w, lot_d, **kw) -> bool:
        """Place a building whose front-left corner is (x, z) on a lot_w x lot_d lot. False if the lot is taken."""
        b = B(self.c, x, self.y, z, facing)
        W, D = lot_w, lot_d
        xs, zs = zip(*[b.world(u, 0, w)[::2] for u, w in ((0, 0), (W - 1, 0), (0, D - 1), (W - 1, D - 1))])
        if not self.free(min(xs), min(zs), max(xs), max(zs)):
            return False
        from . import tour
        W2, D2 = fn(self.c, x, self.y, z, facing, self.rng, **kw)
        tour.record(fn.__name__, kw.get("label") or kw.get("name"), x, self.y, z, facing, W2, D2)
        xs, zs = zip(*[b.world(u, 0, w)[::2] for u, w in ((-1, -1), (W2, -1), (-1, D2), (W2, D2))])
        self.mark(min(xs), min(zs), max(xs), max(zs))
        return True

    def frontage(self, s: streets.Street, side: int, a: int, b: int, items: Iterable, depth: int, gap=2):
        """Line buildings up along street `s` between positions a..b (x for E-W streets, z for N-S),
        on side -1 (north/west) or +1 (south/east). `items` yields (fn, W, D, kw)."""
        off = streets.front(s, side)
        pos = a
        for fn, W, D, kw in items:
            if pos + W - 1 > b:
                break
            D = min(D, depth)
            if s.along_x:
                fz = s.z1 + off
                if side < 0:     # north side, faces south
                    ok = self.building(fn, pos, fz, "south", W, D, **kw)
                else:            # south side, faces north; front-left is the east end
                    ok = self.building(fn, pos + W - 1, fz, "north", W, D, **kw)
            else:
                fx = s.x1 + off
                if side < 0:     # west side, faces east; front-left is the south end
                    ok = self.building(fn, fx, pos + W - 1, "east", W, D, **kw)
                else:            # east side, faces west
                    ok = self.building(fn, fx, pos, "west", W, D, **kw)
            pos += (W + gap) if ok else 3

    # ---------------------------------------------------------------- plazas
    def plaza(self, x1, z1, x2, z2, name: str | None = None, pave="mcwpaths:sandstone_flagstone"):
        """Paved square with a tiered fountain, flower beds, palms, benches and lamps."""
        c, rng, y = self.c, self.rng, self.y
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                i, j = z - c.z0, x - c.x0
                c.height[i, j] = y
                ring = max(abs(x - cx), abs(z - cz))
                c.top[i, j] = c.sid(pave if ring % 6 else "mcwpaths:andesite_flagstone")
        self.mark(x1, z1, x2, z2)
        b = B(c, cx, y, cz, "south")
        # fountain: basin, rim, centre column with a bowl
        b.disc(0, 0, 0, 6.5, "minecraft:smooth_quartz")
        b.disc(0, 0, 0, 5.5, "minecraft:water")
        b.disc(0, -1, 0, 5.5, "minecraft:prismarine_bricks")
        for a in range(0, 360, 12):
            u, w = round(6 * math.cos(math.radians(a))), round(6 * math.sin(math.radians(a)))
            b.set(u, 1, w, "minecraft:smooth_quartz_slab[type=bottom]")
        for v in range(1, 4):
            b.set(0, v, 0, "minecraft:quartz_pillar[axis=y]")
        b.disc(0, 4, 0, 1.5, "minecraft:smooth_quartz_slab[type=bottom]")
        b.set(0, 4, 0, "minecraft:water")
        # flower beds with hibiscus at the corners, palms behind them
        for sx, sz in ((x1 + 4, z1 + 4), (x2 - 4, z1 + 4), (x1 + 4, z2 - 4), (x2 - 4, z2 - 4)):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    c.set(sx + dx, y, sz + dz, "minecraft:grass_block")
                    if (dx, dz) != (0, 0):
                        c.set(sx + dx, y + 1, sz + dz, rng.choice(arch_flowers()))
            plants.palm(c, sx, y, sz, rng, furn.piece("palm_log"), furn.piece("palm_leaves"))
        # benches facing the fountain and lamps around it
        for a in range(0, 360, 45):
            u, w = round(9 * math.cos(math.radians(a))), round(9 * math.sin(math.radians(a)))
            face = ("west" if u > 0 else "east") if abs(u) >= abs(w) else ("north" if w > 0 else "south")
            c.set(cx + u, y + 1, cz + w, furn.piece("bench", face))
        for u, w in ((-8, -8), (8, -8), (-8, 8), (8, 8)):
            furn.place_tall(c, cx + u, y + 1, cz + w, "street_lamp")
        if name:
            c.sign(cx, y + 1, cz + 8, [name, "", "Alola Region", ""], wood="birch", rotation=0)

    def promenade(self, x1, x2, z, beach_side=1):
        """Beach promenade south of a street: palms, lamps, benches; umbrellas and loungers on the sand."""
        c, rng, y = self.c, self.rng, self.y
        for x in range(x1, x2 + 1, 10):
            zz = z + beach_side * 2
            if c.inside(x, zz) and not c.is_water(x, zz):
                plants.palm(c, x, c.surface(x, zz), zz, rng, furn.piece("palm_log"), furn.piece("palm_leaves"))
            if x % 20 == 0:
                c.set(x + 5, y + 1, z + beach_side, furn.piece("bench", "south" if beach_side > 0 else "north"))
        for x in range(x1 + 6, x2, 12):
            for k in (8, 16):
                bz = z + beach_side * k
                if c.inside(x, bz) and not c.is_water(x, bz):
                    gy = c.surface(x, bz)
                    if c.get(x, gy + 1, bz) == "minecraft:air":
                        umbrella(c, x, gy, bz, rng)


def arch_flowers():
    return ["wilderwild:pink_hibiscus", "wilderwild:red_hibiscus", "wilderwild:yellow_hibiscus",
            "wilderwild:white_hibiscus", "minecraft:allium", "minecraft:azure_bluet"]


def umbrella(c: Canvas, x, y, z, rng):
    c.set(x, y + 1, z, furn.piece("sun_lounger", "south"))
    c.set(x + 2, y + 1, z, furn.piece("beach_towel", "south"))
    for v in range(1, 4):
        c.set(x + 1, y + v, z - 1, "minecraft:bamboo_fence")
    col = rng.choice(["red", "yellow", "light_blue", "white", "orange", "pink"])
    for dx in (-1, 0, 1):
        for dz in (-2, -1, 0):
            c.set(x + 1 + dx, y + 4, z + dz, f"minecraft:{col}_wool" if (dx, dz) == (0, -1) else f"minecraft:{col}_carpet")


# ================================================================ Hau'oli City

def _houses(rng, style_pool, depth, n=40, label_first=None):
    for k in range(n):
        st = rng.choice(style_pool)
        P = arch.STYLES[st].porch
        W = rng.choice([9, 11, 11, 13])
        D = max(6, min(9, depth - P))
        kw = {"style": st, "W": W, "D": D}
        if k == 0 and label_first:
            kw["label"] = label_first
        yield arch.house, W, D + P, kw


def _shop_items(rng, shops, depth, floors=(2, 3)):
    for kind, label in shops:
        W = rng.choice([11, 13])
        yield arch.shop, W, depth, {"kind": kind, "label": label, "W": W, "D": depth, "floors": rng.choice(floors)}


def hauoli(t, rng):
    from . import alola_map, buildings as bl
    y = alola_map.TOWNS["Hau'oli City"][2]
    city = City(t, y, rng)
    X1, X2 = -927, -618
    S = streets.Street
    north = S(X1, -497, X2, -497, y, lanes=1, sidewalk=2)
    boulevard = S(X1, -460, X2, -460, y, lanes=2, sidewalk=3, median=3)
    beach = S(-899, -418, X2, -418, y, lanes=1, sidewalk=2, crossings=0)
    crosses = [S(x, -497, x, -418, y, lanes=1, sidewalk=2, crossings=0) for x in (-905, -845, -735, -675)]
    for s in (boulevard, north, beach, *crosses):
        city.street(s)
    # central plaza on the south side of the boulevard; City Hall and the Pokémon Center face it
    city.plaza(-812, -446, -768, -424, name="Hau'oli City")
    fz = boulevard.z1 + streets.front(boulevard, -1)
    city.building(bl.pokemon_center, -838, fz, "south", 17, 15, name="Hau'oli City")
    city.building(arch.shop, -812, fz, "south", 23, 12, kind="office", label="Hau'oli City Hall", W=23, D=12, floors=3)
    shops = [("malasada", "Malasada Shop"), ("apparel", "Apparel Shop"), ("salon", "Salon"),
             ("mart", "Poké Mart"), ("cafe", "Café"), ("bureau", "Tourist Bureau"), ("ice_cream", "Ice Cream Shop"),
             ("police", "Police Station"), ("surf", "Surf Shop"), ("cafe", "Hau'oli Diner"), ("market", "Market"),
             ("apparel", "Boutique"), ("office", "Pokémon Fan Club"), ("cafe", "Tapioca Bar")]
    rng.shuffle(shops)
    it = iter(list(_shop_items(rng, shops, 11)))
    blocks = [(X1 + 2, -911), (-899, -851), (-839, -741), (-729, -681), (-669, X2)]
    for a, b in blocks:
        city.frontage(boulevard, -1, a, b, it, depth=11)
        city.frontage(boulevard, +1, a, b, it, depth=10)
    homes = _houses(rng, ["plantation", "hauoli", "plantation"], 9, n=120)
    for a, b in blocks:
        city.frontage(north, +1, a, b, homes, depth=9)
        city.frontage(north, -1, a, b, homes, depth=10)
        city.frontage(beach, -1, a, b, homes, depth=9)
    city.promenade(-899, X2, beach.z1 + beach.half + beach.sidewalk, beach_side=1)
    # marina west of the city: terminal on the quay, pier and ferry out on the water
    mx, mz, my = alola_map.TOWNS["Hau'oli Marina"]
    from .landmarks import place as lplace
    lplace(t, bl.ferry_terminal, mx - 7, my, mz + 4, "south", rng, label="Hau'oli Marina", dest="Heahea City")
    bl.pier(t.c, mx - 2, SEA + 1, mz + 9, "north", length=40, width=5)
    bl.ferry_ship(t.c, mx + 6, SEA + 1, mz + 14, "north", rng, "S.S. Heahea")
    return city
