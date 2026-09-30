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
        c = self.c
        self.t.built[min(zs) - c.z0:max(zs) - c.z0 + 1, min(xs) - c.x0:max(xs) - c.x0 + 1] = True
        return True

    def finish(self):
        """Signals at the junctions, and hand the open lots to the gardeners (Nature.gardens)."""
        streets.junctions(self.c, self.streets, self.rng)
        c, t = self.c, self.t
        ys, xs = np.nonzero(self.occ)
        if not len(ys):
            return
        i1, i2, j1, j2 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        open_ = ~self.occ[i1:i2, j1:j2]
        flat = c.height[i1:i2, j1:j2] == self.y
        dry = c.water[i1:i2, j1:j2] <= c.height[i1:i2, j1:j2]
        t.garden[i1:i2, j1:j2] |= open_ & flat & dry

    def frontage(self, s: streets.Street, side: int, a: int, b: int, items: Iterable, depth: int, gap=2):
        """Line buildings up along street `s` between positions a..b (x for E-W streets, z for N-S),
        on side -1 (north/west) or +1 (south/east). `items` yields (fn, W, D, kw)."""
        off = streets.front(s, side)
        pos = a
        for fn, W, D, kw in items:
            if pos + W - 1 > b:
                break
            if D > depth:             # shrink the building to the lot
                if "D" in kw:
                    kw = {**kw, "D": kw["D"] - (D - depth)}
                D = depth
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


FILLER_SHOPS = [("cafe", "Café"), ("market", "Market"), ("apparel", "Boutique"), ("office", "Offices"),
                ("mart", "Convenience Store"), ("cafe", "Juice Bar"), ("salon", "Hair Salon"), ("office", "Bank")]


def _shop_items(rng, shops, depth, floors=(2, 3), style="modern"):
    """The named shops first, then ordinary ones for as long as there are lots. `style` may be a list."""
    k = 0
    while True:
        kind, label = shops[k] if k < len(shops) else rng.choice(FILLER_SHOPS)
        k += 1
        W = rng.choice([11, 13])
        st = rng.choice(style) if isinstance(style, (list, tuple)) else style
        yield arch.shop, W, depth, {"kind": kind, "label": label, "W": W, "D": depth, "floors": rng.choice(floors),
                                    "style": st}


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
    it = _shop_items(rng, shops, 11)
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
    city.finish()
    return city


def quay(city: City, x1, z1, x2, z2, pave="mcwpaths:andesite_flagstone"):
    """Harbour quay: flagstones, lamps, benches, bollards and palms."""
    c, y, rng = city.c, city.y, city.rng
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if c.inside(x, z) and not c.is_water(x, z):
                i, j = z - c.z0, x - c.x0
                c.height[i, j] = y
                c.top[i, j] = c.sid(pave)
    for x in range(x1 + 3, x2, 12):
        furn.place_tall(c, x, y + 1, z1 + 1, "street_lamp")
        c.set(x + 4, y + 1, z1 + 1, furn.piece("bench", "north"))
        c.set(x + 8, y + 1, z1, "minecraft:polished_blackstone_wall")
    city.mark(x1, z1, x2, z2)


# ================================================================== Heahea City

def heahea(t, rng):
    from . import alola_map, buildings as bl
    x0, z0, y = alola_map.TOWNS["Heahea City"]
    city = City(t, y, rng)
    S = streets.Street
    X1, X2 = x0 - 76, x0 + 76
    # harbour: ferry terminal, pier and ship on the north shore
    city.building(bl.ferry_terminal, x0 - 60, z0 - 38, "north", 15, 9, label="Heahea Ferry Terminal",
                  dest="Hau'oli / Malie")
    bl.pier(t.c, x0 - 58, SEA + 1, z0 - 62, "north", length=24)
    bl.ferry_ship(t.c, x0 - 50, SEA + 1, z0 - 72, "west", rng, "S.S. Malie")
    main = S(X1, z0 - 10, X2, z0 - 10, y, lanes=2, sidewalk=3)
    south = S(X1, z0 + 32, X2, z0 + 32, y, lanes=1, sidewalk=2)
    crosses = [S(x, z0 - 10, x, z0 + 32, y, lanes=1, sidewalk=2, crossings=0) for x in (x0 - 45, x0, x0 + 45)]
    for s in (main, south, *crosses):
        city.street(s)
    quay(city, X1, z0 - 45, X2, z0 - 34)
    fz = main.z1 + streets.front(main, +1)
    city.building(bl.pokemon_center, x0 - 20, fz, "north", 17, 15, name="Heahea City")
    fzn = main.z1 + streets.front(main, -1)
    city.building(bl.hotel, x0 + 8, fzn, "south", 25, 13, label="Tide Song Hotel", floors=5, W=25, D=13,
                  trim="minecraft:light_blue_concrete")
    shops = [("office", "Dimensional Research Lab"), ("surf", "Surf Association"), ("bureau", "Tourist Bureau"),
             ("malasada", "Malasada Shop"), ("apparel", "Apparel Shop"), ("cafe", "Heahea Café"),
             ("mart", "Poké Mart"), ("salon", "Salon")]
    it = _shop_items(rng, shops, 12)
    blocks = [(X1 + 1, x0 - 51), (x0 - 39, x0 - 6), (x0 + 6, x0 + 39), (x0 + 51, X2)]
    for a, b in blocks:
        city.frontage(main, -1, a, b, it, depth=12)
        city.frontage(main, +1, a, b, it, depth=12)
    homes = _houses(rng, ["plantation", "hauoli"], 11, n=60)
    for a, b in blocks:
        city.frontage(south, -1, a, b, homes, depth=11)
        city.frontage(south, +1, a, b, homes, depth=11)
    city.finish()
    return city


# =================================================================== Malie City

def malie(t, rng):
    from . import alola_map, buildings as bl
    x0, z0, y = alola_map.TOWNS["Malie City"]
    city = City(t, y, rng)
    S = streets.Street
    X1, X2 = x0 - 88, x0 + 88
    city.building(bl.ferry_terminal, x0 - 80, z0 + 50, "south", 15, 9, label="Malie Ferry Terminal",
                  dest="Heahea / Seafolk")
    bl.pier(t.c, x0 - 110, SEA + 1, z0 + 20, "east", length=26)
    bl.ferry_ship(t.c, x0 - 120, SEA + 1, z0 + 40, "east", rng, "S.S. Seafolk")
    main = S(X1, z0, X2, z0, y, lanes=2, sidewalk=3, lamps="paper_lamp")
    north = S(X1, z0 - 42, X2, z0 - 42, y, lanes=1, sidewalk=2, lamps="paper_lamp")
    south = S(X1 + 40, z0 + 40, X2, z0 + 40, y, lanes=1, sidewalk=2, lamps="paper_lamp")
    crosses = [S(x, z0 - 42, x, z0 + 40, y, lanes=1, sidewalk=2, crossings=0, lamps="paper_lamp")
               for x in (x0 - 45, x0 + 45)]
    for s in (main, north, south, *crosses):
        city.street(s)
    city.building(bl.pokemon_center, x0 - 30, main.z1 + streets.front(main, -1), "south", 17, 15, name="Malie City")
    city.building(bl.hotel, x0 - 10, north.z1 + streets.front(north, -1), "south", 27, 12, label="Malie Library",
                  floors=2, W=27, D=12, wall="minecraft:stripped_dark_oak_wood[axis=y]", trim="minecraft:red_concrete")
    shops = [("office", "Malie Community Center"), ("apparel", "Apparel Shop"), ("malasada", "Malasada Shop"),
             ("mart", "Poké Mart"), ("cafe", "Tea House"), ("market", "Kantonian Goods"), ("salon", "Salon")]
    it = _shop_items(rng, shops, 12, style="malie")
    blocks = [(X1 + 1, x0 - 51), (x0 - 39, x0 + 39), (x0 + 51, X2)]
    for a, b in blocks:
        city.frontage(main, -1, a, b, it, depth=12)
        city.frontage(main, +1, a, b, it, depth=12)
    homes = _houses(rng, ["malie"], 11, n=80)
    for a, b in blocks:
        city.frontage(north, +1, a, b, homes, depth=11)
        city.frontage(north, -1, a, b, homes, depth=11)
        city.frontage(south, -1, a, b, homes, depth=11)
        city.frontage(south, +1, a, b, homes, depth=11)
    city.finish()
    return city


# ================================================================ Konikoni City

def konikoni(t, rng):
    from . import alola_map, buildings as bl, special as sp
    x0, z0, y = alola_map.TOWNS["Konikoni City"]
    city = City(t, y, rng)
    S = streets.Street
    X1, X2 = x0 - 66, x0 + 66
    market_paving = ("mcwpaths:brick_basket_weave_paving", "mcwpaths:brick_running_bond",
                     "mcwpaths:brick_basket_weave_paving", "minecraft:red_terracotta")
    main = S(X1, z0, X2, z0, y, lanes=1, sidewalk=2, crossings=0, paving=market_paving,
             walk="mcwpaths:sandstone_flagstone", lamps="paper_lamp")
    south = S(X1, z0 + 30, x0 + 40, z0 + 30, y, lanes=1, sidewalk=2, crossings=0, paving=market_paving,
              walk="mcwpaths:sandstone_flagstone", lamps="paper_lamp")
    cross = S(x0, z0, x0, z0 + 30, y, lanes=1, sidewalk=2, crossings=0, paving=market_paving,
              walk="mcwpaths:sandstone_flagstone", lamps="paper_lamp")
    for s in (main, south, cross):
        city.street(s)
    city.building(sp.lighthouse, x0 + 58, z0 + 30, "north", 9, 9)
    city.building(bl.pokemon_center, x0 - 40, main.z1 + streets.front(main, -1), "south", 17, 15, name="Konikoni City")
    shops = [("apparel", "Olivia's Jewelry"), ("market", "Herb Shop"), ("market", "Incense Shop"),
             ("market", "Konikoni Market"), ("cafe", "Noodle Restaurant"), ("mart", "Poké Mart")]
    it = _shop_items(rng, shops, 10, floors=(1, 2, 2, 3), style=["konikoni", "konikoni", "malie", "modern"])
    for a, b in ((X1 + 1, x0 - 6), (x0 + 6, X2)):
        city.frontage(main, -1, a, b, it, depth=10)
        city.frontage(main, +1, a, b, it, depth=9)
    homes = _houses(rng, ["konikoni", "konikoni", "malie", "plantation"], 10, n=40)
    for a, b in ((X1 + 1, x0 - 6), (x0 + 6, x0 + 40)):
        city.frontage(south, -1, a, b, homes, depth=9)
        city.frontage(south, +1, a, b, homes, depth=10)
    # strings of red lanterns across the market street
    c = t.c
    for x in range(X1 + 4, X2, 8):
        for dz in range(-3, 4):
            c.set(x, y + 6, z0 + dz, "minecraft:chain[axis=z]" if dz % 3 else furn.piece("paper_lamp"))
        for dz in (-4, 4):
            for v in range(1, 7):
                if c.get(x, y + v, z0 + dz) == "minecraft:air":
                    c.set(x, y + v, z0 + dz, "minecraft:dark_oak_fence")
    # market stalls down alternate sides of the street, and a gateway at each end
    for k, x in enumerate(range(X1 + 8, X2 - 6, 14)):
        if abs(x - x0) < 8:
            continue
        market_stall(c, x, y, z0 + (2 if k % 2 else -2), "north" if k % 2 else "south", rng)
    for gx in (X1, X2):
        paifang(c, gx, y, z0, rng, "Konikoni City")
    city.finish()
    return city


def market_stall(c: Canvas, x, y, z, facing, rng):
    """A 3x2 market stall: barrel-and-crate counter, corner posts, a striped canopy, goods and a lantern."""
    b = arch.Bld(c, x - 1 if facing == "south" else x + 1, y, z, facing)
    goods = ["minecraft:melon", "minecraft:pumpkin", "minecraft:hay_block[axis=y]", "minecraft:potted_red_tulip",
             "minecraft:potted_cactus", "minecraft:cake", "minecraft:potted_bamboo", "minecraft:decorated_pot[facing=south]"]
    col = rng.choice(["red", "orange", "yellow", "white"])
    for u in range(3):
        b.set(u, 1, 0, "minecraft:barrel[facing=up]" if u % 2 else furn.piece("crate"))
        b.set(u, 2, 0, rng.choice(goods))
    for u in (-1, 3):
        for w in (0, 1):
            for v in (1, 2):
                b.set(u, v, w, "minecraft:dark_oak_fence")
    for u in range(-1, 4):
        for w in (-1, 0, 1):
            b.set(u, 3, w, f"minecraft:{col if (u + w) % 2 else 'white'}_wool" if w == 0 else f"minecraft:{col}_carpet"
                  if (u + w) % 2 else "minecraft:white_carpet")
    b.set(1, 1, 1, "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight]")


def paifang(c: Canvas, x, y, z, rng, name):
    """A red gateway across a north-south span at x: two pillars on stone bases, a coloured beam and a tiled
    double roof with upturned ends."""
    b = arch.Bld(c, x, y, z - 5, "west")
    for u in (0, 10):
        b.set(u, 1, 0, "minecraft:polished_blackstone")
        for v in range(2, 8):
            b.set(u, v, 0, "minecraft:red_concrete")
    for u in range(-1, 12):
        b.set(u, 6, 0, "minecraft:red_nether_bricks" if u % 3 else "minecraft:gold_block")
        b.set(u, 8, 0, "minecraft:dark_oak_planks")
        for w, fc in ((-1, "south"), (1, "north")):
            b.set(u, 9, w, f"minecraft:deepslate_tile_stairs[facing={fc},half=bottom,shape=straight]")
        b.set(u, 9, 0, "minecraft:deepslate_tiles")
        b.set(u, 10, 0, "minecraft:deepslate_tile_slab[type=bottom]")
    for u, fc in ((-2, "west"), (12, "east")):             # upturned ends
        b.set(u, 9, 0, f"minecraft:deepslate_tile_stairs[facing={fc},half=bottom,shape=straight]")
    for u in range(3, 8):
        b.set(u, 7, 0, "minecraft:red_concrete")
    b.sign(5, 7, -1, [name], wood="dark_oak", glow=True)
    for u in (2, 8):
        b.set(u, 5, 0, "minecraft:lantern[hanging=true]")


# ================================================================= Paniola Town

def paniola(t, rng):
    from . import alola_map, buildings as bl
    x0, z0, y = alola_map.TOWNS["Paniola Town"]
    city = City(t, y, rng)
    S = streets.Street
    dirt = ("minecraft:coarse_dirt", "minecraft:dirt_path", "minecraft:coarse_dirt", "minecraft:packed_mud")
    main = S(x0 - 42, z0, x0 + 42, z0, y, lanes=1, sidewalk=2, crossings=0, paving=dirt,
             walk="minecraft:spruce_planks")
    city.street(main)
    city.building(bl.pokemon_center, x0 - 40, main.z1 + streets.front(main, -1), "south", 17, 15, name="Paniola Town")
    shops = [("cafe", "Paniola Saloon"), ("market", "General Store"), ("mart", "Poké Mart"), ("office", "Ranch Office")]
    it = _shop_items(rng, shops, 11, floors=(2,), style="paniola")
    city.frontage(main, +1, x0 - 40, x0 + 40, it, depth=11)
    homes = _houses(rng, ["paniola"], 11, n=20)
    city.frontage(main, -1, x0 - 40, x0 + 40, homes, depth=11)
    city.finish()
    return city
