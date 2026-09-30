"""Natural dressing of the islands, done after towns and routes are placed.

* Terrain Slabs: every one-block step of natural ground gets a half slab of the same
  material, so hills and routes are smooth to walk and look like the game's rounded slopes.
* Dynamic Trees: forest, jungle, savanna, mountain and garden trees are built from real
  Dynamic Trees branches on rooty soil, so they have tapering trunks and fall when chopped.
* Wilder Wild / Wilder Flowers: palms with fronds and coconuts, hibiscus, bushes,
  wildflower carpets, fallen hollow logs, cattails, lily pads, prickly pears, geysers,
  anemones, sea whips and tube worms, chosen per zone.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

import numpy as np

from . import terrain as T
from .canvas import NONE, SEA, Canvas

TS = "terrain_slabs:"
WW = "wilderwild:"
DT = "dynamictrees:"
AIR = "minecraft:air"

SLAB_FOR = {
    "minecraft:grass_block": TS + "grass_slab[type=bottom,snowy=false]",
    "minecraft:sand": TS + "sand_slab[type=bottom]",
    "minecraft:red_sand": TS + "red_sand_slab[type=bottom]",
    "minecraft:dirt": TS + "dirt_slab[type=bottom]",
    "minecraft:coarse_dirt": TS + "coarse_slab[type=bottom]",
    "minecraft:rooted_dirt": TS + "rooted_dirt_slab[type=bottom]",
    "minecraft:podzol": TS + "podzol_slab[type=bottom,snowy=false]",
    "minecraft:dirt_path": TS + "path_slab[type=bottom]",
    "minecraft:gravel": TS + "gravel_slab[type=bottom]",
    "minecraft:snow_block": TS + "snow_slab[type=bottom]",
    "minecraft:stone": TS + "terrain_stone_slab[type=bottom]",
    "minecraft:andesite": TS + "terrain_andesite_slab[type=bottom]",
    "minecraft:diorite": TS + "terrain_diorite_slab[type=bottom]",
    "minecraft:granite": TS + "terrain_granite_slab[type=bottom]",
    "minecraft:tuff": TS + "terrain_tuff_slab[type=bottom]",
    "minecraft:calcite": TS + "calcite_slab[type=bottom]",
    "minecraft:clay": TS + "clay_slab[type=bottom]",
    "minecraft:mud": TS + "mud_slab[type=bottom]",
    "minecraft:packed_mud": TS + "packed_mud_slab[type=bottom]",
    "minecraft:moss_block": TS + "moss_slab[type=bottom]",
    "minecraft:basalt[axis=y]": TS + "basalt_slab[type=bottom]",
    "minecraft:smooth_basalt": TS + "smooth_basalt_slab[type=bottom]",
    "minecraft:blackstone": TS + "terrain_blackstone_slab[type=bottom]",
    "minecraft:sandstone": TS + "terrain_sandstone_slab[type=bottom]",
    "minecraft:packed_ice": TS + "packed_ice_slab[type=bottom]",
    "minecraft:terracotta": TS + "terracotta_slab[type=bottom]",
    **{f"minecraft:{col}_terracotta": TS + f"{col}_terracotta_slab[type=bottom]"
       for col in ("white", "orange", "yellow", "red", "brown", "light_gray", "black", "cyan", "light_blue")},
}
ROOTY = {
    "minecraft:grass_block": "rooty_grass_block", "minecraft:dirt": "rooty_dirt", "minecraft:coarse_dirt": "rooty_coarse_dirt",
    "minecraft:podzol": "rooty_podzol", "minecraft:sand": "rooty_sand", "minecraft:red_sand": "rooty_red_sand",
    "minecraft:moss_block": "rooty_moss_block", "minecraft:mud": "rooty_mud", "minecraft:rooted_dirt": "rooty_rooted_dirt",
    "minecraft:gravel": "rooty_gravel", "minecraft:clay": "rooty_clay",
}
HIBISCUS = [WW + f"{c}_hibiscus" for c in ("pink", "red", "yellow", "white", "purple")]
WILDFLOWER_BEDS = ["wilderflowers:cheery_wildflowers", "wilderflowers:playful_wildflowers",
                   "wilderflowers:hopeful_wildflowers", "wilderflowers:moody_wildflowers"]
DIRS4 = ("north", "east", "south", "west")


def is_air(c: Canvas, x, y, z) -> bool:
    return c.get(x, y, z) == AIR


class Nature:
    def __init__(self, c: Canvas, t: T.Terrain, rng: random.Random):
        self.c, self.t, self.rng = c, t, rng
        self.slabbed = np.zeros(c.height.shape, dtype=bool)
        self.taken = np.zeros(c.height.shape, dtype=bool)   # trunks, logs and big plants (keeps trees apart)
        self.stats = defaultdict(int)

    # ---------------------------------------------------------------- helpers
    def ij(self, x, z):
        return z - self.c.z0, x - self.c.x0

    def top_state(self, x, z) -> str:
        i, j = self.ij(x, z)
        return self.c.states[self.c.top[i, j]]

    def plant(self, x, y, z, state):
        """Place a small plant on the ground at column (x, z); y is the ground height."""
        c = self.c
        i, j = self.ij(x, z)
        if self.slabbed[i, j]:
            return False   # (Terrain Slabs' *_on_top blockstates are not registered blocks in 1.21.1)
        if not is_air(c, x, y + 1, z):
            return False
        c.set(x, y + 1, z, state)
        return True

    def tall(self, x, y, z, base, extra="", props_upper=None):
        """Two-block plant (tall grass, large fern, datura, bush...)."""
        c = self.c
        i, j = self.ij(x, z)
        if self.slabbed[i, j] or not is_air(c, x, y + 1, z) or not is_air(c, x, y + 2, z):
            return False
        sep = "," if extra else ""
        c.set(x, y + 1, z, f"{base}[{extra}{sep}half=lower]")
        c.set(x, y + 2, z, f"{base}[{extra}{sep}half=upper]")
        return True

    def free_disc(self, x, z, r) -> bool:
        i, j = self.ij(x, z)
        c = self.c
        if i - r < 0 or j - r < 0 or i + r >= c.d or j + r >= c.w:
            return False
        return not (self.taken[i - r:i + r + 1, j - r:j + r + 1].any()
                    or self.t.no_trees[i - r:i + r + 1, j - r:j + r + 1].any())

    def take(self, x, z, r):
        i, j = self.ij(x, z)
        self.taken[max(0, i - r):i + r + 1, max(0, j - r):j + r + 1] = True

    # ------------------------------------------------------------ terrain slabs
    def terrain_slabs(self):
        c, t = self.c, self.t
        h = c.height.astype(np.int32)
        dry = t.land & (c.water <= c.height)
        up = np.zeros(h.shape, dtype=bool)
        for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = np.roll(h, (dz, dx), axis=(0, 1))
            nd = np.roll(dry, (dz, dx), axis=(0, 1))
            up |= (nb == h + 1) & nd
        up[0, :] = up[-1, :] = up[:, 0] = up[:, -1] = False
        cand = dry & up
        ys, xs = np.nonzero(cand)
        slab_sid = {c.sid(k): v for k, v in SLAB_FOR.items()}
        n = 0
        for i, j in zip(ys.tolist(), xs.tolist()):
            slab = slab_sid.get(int(c.top[i, j]))
            if slab is None:
                continue
            x, z, y = j + c.x0, i + c.z0, int(h[i, j]) + 1
            if not is_air(c, x, y, z):
                continue
            c.set(x, y, z, slab)
            self.slabbed[i, j] = True
            n += 1
        self.stats["terrain slabs"] = n

    # ------------------------------------------------------------ Dynamic Trees
    def dt_tree(self, x, y, z, family="oak", size=1.0, shape=None) -> bool:
        try:
            return self._dt_tree(x, y, z, family, size, shape)
        except ValueError:   # no room to grow (blocks are only placed once the whole tree is planned)
            return False

    def _dt_tree(self, x, y, z, family="oak", size=1.0, shape=None) -> bool:
        """A Dynamic Trees tree: rooty soil, a branch network with pipe-model radii and leaf clusters."""
        c, rng = self.c, self.rng
        shape = shape or family
        ground = self.top_state(x, z)
        soil = ROOTY.get(ground, "rooty_dirt")
        nodes: dict[tuple, tuple | None] = {}
        kids: dict[tuple, list] = defaultdict(list)
        tips: list[tuple] = []
        canopy: list[tuple] = []           # (point, rh, rv) leaf clusters

        def add(p, parent):
            if p in nodes:
                return False
            if not is_air(c, *p):
                return False
            nodes[p] = parent
            if parent is not None:
                kids[parent].append(p)
            return True

        def limb(start, angle, length, rise, split=0.0, cluster=(2.6, 1.7)):
            """Grow a 6-connected limb from `start` towards `angle` (radians), climbing `rise` per step."""
            if start not in nodes:
                return start
            px, py, pz = start
            fx, fy, fz = float(px), float(py), float(pz)
            dx, dz = math.cos(angle), math.sin(angle)
            cur = start
            for step in range(length):
                fx += dx
                fz += dz
                fy += rise
                target = (round(fx), round(fy), round(fz))
                # walk axis by axis so the chain stays face-connected
                while cur != target:
                    ax = max(range(3), key=lambda a: abs(target[a] - cur[a]))
                    nxt = list(cur)
                    nxt[ax] += 1 if target[ax] > cur[ax] else -1
                    nxt = tuple(nxt)
                    if not add(nxt, cur):
                        tips.append(cur)
                        canopy.append((cur, *cluster))
                        return cur
                    cur = nxt
                if split and step == length // 2 and rng.random() < split:
                    limb(cur, angle + rng.choice((-1, 1)) * rng.uniform(0.6, 1.0), max(2, length // 2), rise * 1.2,
                         0.0, (cluster[0] * 0.85, cluster[1]))
                if step >= length // 2 and rng.random() < 0.35:
                    canopy.append((cur, cluster[0] * 0.7, cluster[1] * 0.8))
            tips.append(cur)
            canopy.append((cur, *cluster))
            return cur

        root = (x, y + 1, z)
        if not add(root, None):
            return False

        def trunk(height, lean=(0, 0), lean_from=99):
            cur = root
            for k in range(1, height):
                nx, ny, nz = cur[0], cur[1] + 1, cur[2]
                if k >= lean_from and rng.random() < 0.5:
                    side = (cur[0] + lean[0], cur[1], cur[2] + lean[1])
                    if add(side, cur):
                        cur = side
                if not add((cur[0], cur[1] + 1, cur[2]), cur):
                    break
                cur = (cur[0], cur[1] + 1, cur[2])
            if cur[1] - root[1] < min(3, height - 1):
                raise ValueError("trunk blocked")   # nothing is placed yet; dt_tree() skips this tree
            return cur

        s = size
        if shape == "oak":
            top = trunk(max(3, int(rng.randint(4, 6) * s)))
            n = rng.randint(3, 5)
            base_a = rng.uniform(0, math.tau)
            for k in range(n):
                start_h = rng.randint(max(1, top[1] - root[1] - 3), top[1] - root[1])
                start = (x, root[1] + start_h, z)
                if start not in nodes:
                    start = top
                limb(start, base_a + k * math.tau / n + rng.uniform(-0.4, 0.4), int(rng.randint(3, 5) * s),
                     rng.uniform(0.35, 0.7), split=0.6, cluster=(2.8 * min(1.3, s), 1.9))
            limb(top, rng.uniform(0, math.tau), 2, 1.2, cluster=(2.6, 2.0))
            maxr = 7
        elif shape == "birch":
            top = trunk(int(rng.randint(7, 10) * s))
            for k in range(rng.randint(2, 3)):
                h0 = rng.randint(top[1] - root[1] - 4, top[1] - root[1] - 1)
                limb((x, root[1] + h0, z), rng.uniform(0, math.tau), 2, 0.8, cluster=(2.0, 1.6))
            limb(top, 0, 1, 1.0, cluster=(2.2, 2.2))
            maxr = 5
        elif shape == "jungle":
            top = trunk(int(rng.randint(11, 17) * s))
            n = rng.randint(3, 4)
            base_a = rng.uniform(0, math.tau)
            for k in range(n):
                h0 = rng.randint(top[1] - root[1] - 4, top[1] - root[1])
                limb((x, root[1] + h0, z), base_a + k * math.tau / n, rng.randint(3, 5), 0.3, split=0.5,
                     cluster=(3.3, 1.8))
            limb(top, 0, 1, 1.0, cluster=(3.5, 2.2))
            maxr = 8
        elif shape == "acacia":
            lean = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            top = trunk(rng.randint(4, 6), lean, lean_from=2)
            n = rng.randint(2, 3)
            base_a = math.atan2(lean[1], lean[0])
            for k in range(n):
                limb(top, base_a + (k - (n - 1) / 2) * 1.3, rng.randint(3, 5), 0.45, cluster=(3.4, 1.1))
            maxr = 6
        elif shape == "dark_oak":
            top = trunk(rng.randint(4, 6))
            n = rng.randint(4, 6)
            for k in range(n):
                h0 = rng.randint(2, top[1] - root[1])
                limb((x, root[1] + h0, z), k * math.tau / n + rng.uniform(-0.3, 0.3), rng.randint(3, 5), 0.3,
                     split=0.5, cluster=(3.2, 1.8))
            limb(top, 0, 1, 1.0, cluster=(3.0, 2.0))
            maxr = 8
        elif shape == "cherry":
            top = trunk(rng.randint(3, 4))
            n = rng.randint(3, 4)
            base_a = rng.uniform(0, math.tau)
            for k in range(n):
                limb(top, base_a + k * math.tau / n, rng.randint(3, 5), 0.55, split=0.5, cluster=(3.2, 2.0))
            maxr = 6
        elif shape == "spruce":
            height = int(rng.randint(9, 14) * s)
            top = trunk(height)
            for lvl in range(3, height - 1, 2):
                reach = max(1, round(3 * (1 - lvl / height)) + 1)
                for a in range(4):
                    if rng.random() < 0.85:
                        limb((x, root[1] + lvl, z), a * math.pi / 2 + (lvl % 4) * 0.4, reach, -0.15,
                             cluster=(1.6 + reach * 0.3, 1.0))
            limb(top, 0, 1, 1.0, cluster=(1.4, 1.8))
            maxr = 6
        else:
            raise ValueError(shape)

        # pipe model: tips radius 1, thicker towards the root
        area: dict[tuple, float] = {}

        def grow_area(p):
            stack = [(p, False)]
            while stack:
                q, done = stack.pop()
                if done:
                    area[q] = max(1.0, sum(area[k] for k in kids[q]) + 0.3) if kids[q] else 1.0
                else:
                    stack.append((q, True))
                    stack.extend((k, False) for k in kids[q])

        grow_area(root)
        for p, parent in nodes.items():
            r = min(maxr, max(1, math.ceil(math.sqrt(area[p]) - 0.2)))
            c.set(*p, f"{DT}{family}_branch[radius={r},waterlogged=false]")
        # Vanilla leaves: the Dynamic Trees Fabric beta only tints its own leaves after an integrated server starts
        # (grey in singleplayer screenshots, likely untinted for dedicated-server clients).
        leaf = f"minecraft:{family}_leaves[persistent=true]"
        for (cx, cy, cz), rh, rv in canopy:
            self._cluster(cx, cy, cz, rh, rv, leaf)
        if shape == "jungle":
            self._vines_around(canopy)
        # No rooty soil: without it Dynamic Trees never ticks this tree, so its tips cannot rot
        # (DT only counts its own leaves as support) and the tree stays exactly as built.
        self.take(x, z, 2 if shape != "spruce" else 1)
        self.stats[f"dynamic {family} trees"] += 1
        return True

    def _cluster(self, cx, cy, cz, rh, rv, state, density=0.9):
        c, rng = self.c, self.rng
        ri, vi = int(math.ceil(rh)), int(math.ceil(rv))
        for dy in range(-vi, vi + 1):
            for dx in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    # flatter underside, rounder top
                    e = (dx * dx + dz * dz) / (rh * rh) + ((dy - 0.3) ** 2) / (rv * rv)
                    if e > 1.0 or (e > 0.7 and rng.random() > density):
                        continue
                    p = (cx + dx, cy + dy, cz + dz)
                    if is_air(c, *p):
                        c.set(*p, state)

    def _vines_around(self, canopy):
        c, rng = self.c, self.rng
        for (cx, cy, cz), rh, rv in canopy:
            for _ in range(4):
                a = rng.uniform(0, math.tau)
                vx, vz = cx + round(math.cos(a) * (rh + 1)), cz + round(math.sin(a) * (rh + 1))
                vy = cy
                # hang from the first leaf block found above
                for side, prop in (((1, 0), "west"), ((-1, 0), "east"), ((0, 1), "north"), ((0, -1), "south")):
                    lx, lz = vx - side[0], vz - side[1]
                    if "leaves" in c.get(lx, vy, lz) and is_air(c, vx, vy, vz):
                        for k in range(rng.randint(2, 6)):
                            if not is_air(c, vx, vy - k, vz):
                                break
                            c.set(vx, vy - k, vz, f"minecraft:vine[{prop}=true]")
                        break

    # --------------------------------------------------------------- palms
    def palm(self, x, y, z, tall=None) -> bool:
        """Wilder Wild palm: curved trunk, a star of drooping fronds and hanging coconuts."""
        c, rng = self.c, self.rng
        i, j = self.ij(x, z)
        if self.slabbed[i, j]:
            return False
        h = tall or rng.randint(6, 11)
        lean = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        px, pz = x, z
        log = WW + "palm_log[axis=y]"
        trunk = []
        for k in range(1, h + 1):
            if k in (h // 2, (3 * h) // 4) and rng.random() < 0.75:
                px, pz = px + lean[0], pz + lean[1]
            trunk.append((px, y + k, pz))
        if not all(is_air(c, *p) for p in trunk) or not is_air(c, px, y + h + 2, pz):
            return False
        for p in trunk:
            c.set(*p, log)
        top = y + h
        frond = WW + "palm_fronds[distance=1,persistent=true,waterlogged=false]"
        c.set(px, top + 1, pz, frond)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            diag = dx and dz
            length = rng.randint(2, 3) if diag else rng.randint(3, 5)
            for s in range(1, length + 1):
                drop = 0 if s < 2 else (1 if s < 4 else 2)
                fy = top + 1 - drop + (1 if s == 1 and not diag else 0)
                if is_air(c, px + dx * s, fy, pz + dz * s):
                    c.set(px + dx * s, fy, pz + dz * s, frond)
        c.set(px, top + 2, pz, frond)
        coco = WW + "coconut[age=2,hanging=true,stage=0]"
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if rng.random() < 0.55 and is_air(c, px + dx, top, pz + dz):
                c.set(px + dx, top + 1, pz + dz, frond)
                c.set(px + dx, top, pz + dz, coco)
        self.take(x, z, 1)
        self.stats["palms"] += 1
        return True

    # ---------------------------------------------------------- small things
    def leaf_bush(self, x, y, z, leaves="minecraft:oak_leaves", flowers=None):
        c, rng = self.c, self.rng
        i, j = self.ij(x, z)
        if self.slabbed[i, j]:
            return
        r = rng.uniform(1.1, 1.8)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for dy in (1, 2):
                    d = math.hypot(dx, dz) + (dy - 1) * 0.9
                    if d <= r and is_air(c, x + dx, y + dy, z + dz) and (dy == 1 or d < r - 0.4):
                        st = leaves
                        if flowers and rng.random() < 0.35:
                            st = flowers
                        c.set(x + dx, y + dy, z + dz, st.replace("]", ",persistent=true]") if "[" in st
                              else st + "[persistent=true]")
        self.take(x, z, 1)

    def ww_bush(self, x, y, z):
        if self.rng.random() < 0.6:
            self.tall(x, y, z, WW + "bush", "age=3")
        else:
            self.plant(x, y, z, WW + "bush[age=2,half=lower]")

    def fallen_log(self, x, y, z, wood="oak"):
        c, rng = self.c, self.rng
        axis = rng.choice("xz")
        n = rng.randint(3, 5)
        cells = [(x + k, z) if axis == "x" else (x, z + k) for k in range(n)]
        for (lx, lz) in cells:
            if not c.inside(lx, lz) or c.surface(lx, lz) != y or c.is_water(lx, lz) or not is_air(c, lx, y + 1, lz):
                return
            ii, jj = self.ij(lx, lz)
            if self.slabbed[ii, jj] or self.t.no_trees[ii, jj]:
                return
        hollow = f"{WW}hollowed_{wood}_log[axis={axis}]"
        for k, (lx, lz) in enumerate(cells):
            c.set(lx, y + 1, lz, hollow)
            if rng.random() < 0.4:
                c.set(lx, y + 2, lz, "minecraft:moss_carpet")
            elif rng.random() < 0.25:
                side = "north" if axis == "x" else "east"
                ox, oz = (0, -1) if axis == "x" else (1, 0)
                if is_air(c, lx + ox, y + 1, lz + oz):
                    c.set(lx + ox, y + 1, lz + oz,
                          f"{WW}brown_shelf_fungi[face=wall,facing={side},shelf_fungus_stage={rng.randint(1, 3)}]")
        self.take(x, z, 1)
        self.stats["fallen logs"] += 1

    def boulder(self, x, y, z, mats=("minecraft:stone", "minecraft:andesite", "minecraft:mossy_cobblestone")):
        c, rng = self.c, self.rng
        r = rng.uniform(1.0, 1.8)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for dy in range(0, 3):
                    if math.sqrt(dx * dx + dz * dz + (dy * 1.4) ** 2) <= r and is_air(c, x + dx, y + dy + 1, z + dz):
                        c.set(x + dx, y + dy + 1, z + dz, rng.choice(mats))
        self.take(x, z, 2)

    def flower_bed(self, x, y, z, bed):
        amt = self.rng.randint(2, 4)
        self.plant(x, y, z, f"{bed}[facing={self.rng.choice(DIRS4)},flower_amount={amt}]")

    # ------------------------------------------------------------- per zone
    def meadow_palette(self, x, z):
        """The four nectar meadows: yellow (Melemele), pink (Akala), red (Ula'ula), purple (Poni)."""
        if x < -350 and z < 0:
            return ["minecraft:dandelion", WW + "marigold", "minecraft:sunflower", "wilderflowers:cheery_wildflowers",
                    WW + "yellow_hibiscus", "minecraft:oxeye_daisy"]
        if x < -350:
            return ["minecraft:pink_tulip", "minecraft:pink_petals", WW + "pink_hibiscus", WW + "phlox",
                    "wilderflowers:playful_wildflowers", "minecraft:peony"]
        if z < 150:
            return ["minecraft:poppy", WW + "carnation", WW + "red_hibiscus", "minecraft:red_tulip", WW + "lantanas",
                    "minecraft:rose_bush"]
        return [WW + "pasqueflower", "minecraft:allium", WW + "purple_hibiscus", "wilderflowers:moody_wildflowers",
                "minecraft:lilac", WW + "phlox"]

    def put_flower(self, x, y, z, name):
        if name in ("minecraft:sunflower", "minecraft:peony", "minecraft:rose_bush", "minecraft:lilac"):
            self.tall(x, y, z, name)
        elif name in ("minecraft:pink_petals", WW + "phlox", WW + "lantanas", WW + "wildflowers", WW + "clovers") \
                or name.startswith("wilderflowers:"):
            self.flower_bed(x, y, z, name)
        else:
            self.plant(x, y, z, name)

    def vegetation(self):
        c, t, rng = self.c, self.t, self.rng
        grass = c.sid("minecraft:grass_block")
        sandish = {c.sid("minecraft:sand"), c.sid("minecraft:red_sand")}
        dry = t.land & ~t.no_trees & (c.water <= c.height)
        ys, xs = np.nonzero(dry)
        order = np.arange(len(ys))
        np.random.default_rng(5).shuffle(order)
        zone, inland, height = t.zone, t.inland, c.height
        for k in order.tolist():
            i, j = int(ys[k]), int(xs[k])
            x, z = j + c.x0, i + c.z0
            zn = int(zone[i, j])
            top = int(c.top[i, j])
            y = int(height[i, j])
            r = rng.random()
            coast = inland[i, j] < 16
            on_grass = top == grass

            if top in sandish and zn not in (T.DESERT, T.CANYON):
                if coast and inland[i, j] > 2 and r < 0.012 and self.free_disc(x, z, 3):
                    self.palm(x, y, z)
                elif r < 0.004:
                    self.plant(x, y, z, "minecraft:dead_bush")
                elif r < 0.0055:
                    self.plant(x, y, z, "beachparty:seashell_block")
                continue

            if zn == T.JUNGLE and on_grass or zn == T.JUNGLE and c.states[top] == "minecraft:podzol":
                if r < 0.012 and self.free_disc(x, z, 4):
                    self.dt_tree(x, y, z, "jungle", size=rng.uniform(0.8, 1.2))
                elif r < 0.02 and self.free_disc(x, z, 2):
                    self.dt_tree(x, y, z, "jungle", size=0.45, shape="oak")
                elif r < 0.05:
                    self.leaf_bush(x, y, z, "minecraft:jungle_leaves")
                elif r < 0.052:
                    self.fallen_log(x, y, z, "jungle")
                elif r < 0.07:
                    self.plant(x, y, z, rng.choice(HIBISCUS))
                elif r < 0.16:
                    self.tall(x, y, z, "minecraft:large_fern")
                elif r < 0.36:
                    self.plant(x, y, z, "minecraft:fern")
                elif r < 0.56:
                    self.plant(x, y, z, "minecraft:short_grass")
                elif r < 0.575:
                    self.ww_bush(x, y, z)
                continue

            if zn in (T.FOREST, T.CAVE_HILL) and on_grass or zn == T.FOREST and c.states[top] == "minecraft:rooted_dirt":
                if r < 0.011 and self.free_disc(x, z, 3):
                    fam = rng.choices(("oak", "birch", "jungle"), (0.65, 0.2, 0.15))[0]
                    self.dt_tree(x, y, z, fam, size=rng.uniform(0.8, 1.25))
                elif r < 0.03:
                    self.leaf_bush(x, y, z, "minecraft:oak_leaves", "minecraft:flowering_azalea_leaves" if rng.random() < 0.3 else None)
                elif r < 0.0315:
                    self.fallen_log(x, y, z, rng.choice(("oak", "birch")))
                elif r < 0.035:
                    self.plant(x, y, z, rng.choice(("minecraft:brown_mushroom", "minecraft:red_mushroom")))
                elif r < 0.06:
                    self.flower_bed(x, y, z, rng.choice((WW + "wildflowers", WW + "clovers") + tuple(WILDFLOWER_BEDS)))
                elif r < 0.10:
                    self.plant(x, y, z, "minecraft:fern")
                elif r < 0.13:
                    self.tall(x, y, z, "minecraft:tall_grass")
                elif r < 0.45:
                    self.plant(x, y, z, "minecraft:short_grass")
                elif r < 0.46:
                    self.ww_bush(x, y, z)
                continue

            if zn in (T.MEADOW, T.FLOWERS) and on_grass:
                pal = self.meadow_palette(x, z)
                if zn == T.FLOWERS and r < 0.004 and self.free_disc(x, z, 3):
                    self.dt_tree(x, y, z, rng.choice(("oak", "birch")), size=0.9)
                elif r < 0.55:
                    self.put_flower(x, y, z, pal[int(rng.random() ** 1.6 * len(pal))])
                elif r < 0.62:
                    self.tall(x, y, z, "minecraft:tall_grass")
                elif r < 0.85:
                    self.plant(x, y, z, "minecraft:short_grass")
                continue

            if zn == T.GARDEN:
                if r < 0.02 and self.free_disc(x, z, 3):
                    self.dt_tree(x, y, z, "cherry")
                elif r < 0.03:
                    self.leaf_bush(x, y, z, "minecraft:azalea_leaves", "minecraft:flowering_azalea_leaves")
                elif r < 0.25:
                    self.flower_bed(x, y, z, "minecraft:pink_petals")
                continue

            if zn == T.RAINY:
                if r < 0.01 and self.free_disc(x, z, 4):
                    self.dt_tree(x, y, z, "dark_oak")
                elif r < 0.012:
                    self.fallen_log(x, y, z, "dark_oak")
                elif r < 0.02:
                    self.plant(x, y, z, rng.choice(("minecraft:brown_mushroom", "minecraft:red_mushroom")))
                elif r < 0.12:
                    self.plant(x, y, z, "minecraft:moss_carpet")
                elif r < 0.30:
                    self.plant(x, y, z, "minecraft:fern")
                elif r < 0.45:
                    self.plant(x, y, z, "minecraft:short_grass")
                continue

            if zn in (T.SAVANNA, T.RANCH) and on_grass:
                if zn == T.SAVANNA and r < 0.003 and self.free_disc(x, z, 4):
                    self.dt_tree(x, y, z, "acacia")
                elif zn == T.RANCH and r < 0.0008 and self.free_disc(x, z, 4):
                    self.dt_tree(x, y, z, "oak", size=1.2)
                elif zn == T.SAVANNA and r < 0.0034:
                    self.plant(x, y, z, WW + "termite_mound[termites_awake=false]")
                elif r < 0.01:
                    self.ww_bush(x, y, z)
                elif r < 0.06:
                    self.tall(x, y, z, "minecraft:tall_grass")
                elif r < 0.07:
                    self.flower_bed(x, y, z, WW + "clovers" if zn == T.RANCH else WW + "wildflowers")
                elif r < 0.45:
                    self.plant(x, y, z, "minecraft:short_grass")
                continue

            if zn in (T.GRASS, T.TOWN) and on_grass:
                town = zn == T.TOWN
                if coast and r < (0.008 if town else 0.009) and self.free_disc(x, z, 3):
                    self.palm(x, y, z)
                elif not town and r < 0.0065 and self.free_disc(x, z, 4):
                    self.dt_tree(x, y, z, "oak", size=rng.uniform(0.8, 1.1))
                elif r < 0.012:
                    self.plant(x, y, z, rng.choice(HIBISCUS))
                elif r < 0.018:
                    self.ww_bush(x, y, z)
                elif r < 0.022 and not town:
                    self.leaf_bush(x, y, z, "minecraft:azalea_leaves", "minecraft:flowering_azalea_leaves")
                elif r < 0.04:
                    self.flower_bed(x, y, z, rng.choice(WILDFLOWER_BEDS + [WW + "wildflowers", WW + "clovers"]))
                elif r < 0.05:
                    self.plant(x, y, z, rng.choice(("minecraft:dandelion", "minecraft:poppy", "minecraft:azure_bluet",
                                                    "minecraft:oxeye_daisy", WW + "seeding_dandelion")))
                elif r < (0.07 if town else 0.10):
                    self.tall(x, y, z, "minecraft:tall_grass")
                elif r < (0.28 if town else 0.50):
                    self.plant(x, y, z, "minecraft:short_grass")
                continue

            if zn == T.DESERT:
                if r < 0.0025:
                    self.cactus(x, y, z)
                elif r < 0.005:
                    self.plant(x, y, z, WW + "prickly_pear[age=3]")
                elif r < 0.006:
                    self.plant(x, y, z, WW + "tumbleweed_plant[age=3]")
                elif r < 0.014:
                    self.plant(x, y, z, "minecraft:dead_bush")
                continue

            if zn == T.CANYON:
                if r < 0.006:
                    self.plant(x, y, z, "minecraft:dead_bush")
                elif r < 0.007:
                    self.plant(x, y, z, WW + "prickly_pear[age=2]")
                continue

            if zn == T.VOLCANIC:
                if r < 0.0015 and not self.slabbed[i, j]:
                    c.set(x, y, z, WW + "geyser[facing=up]")
                    self.stats["geysers"] += 1
                elif r < 0.004:
                    self.plant(x, y, z, "minecraft:dead_bush")
                continue

            if zn == T.SNOW or y > 150:
                if 140 < y < 186 and r < 0.007 and self.free_disc(x, z, 3):
                    self.dt_tree(x, y, z, "spruce", size=rng.uniform(0.8, 1.1))
                elif on_grass and r < 0.2:
                    self.plant(x, y, z, "minecraft:short_grass")
                continue

            if zn == T.ROCKY:
                if r < 0.003:
                    self.boulder(x, y, z)
                elif r < 0.02:
                    self.plant(x, y, z, "minecraft:short_grass" if on_grass else "minecraft:dead_bush")
                continue

            if on_grass and r < 0.3:
                self.plant(x, y, z, "minecraft:short_grass")

    def cactus(self, x, y, z):
        c = self.c
        i, j = self.ij(x, z)
        if self.slabbed[i, j]:
            return
        for k in range(1, self.rng.randint(2, 4) + 1):
            if not is_air(c, x, y + k, z):
                return
            c.set(x, y + k, z, "minecraft:cactus")

    # ------------------------------------------------------------ fresh water
    def waters_edge(self):
        """Cattails, lily pads and sugar cane around lakes and ponds."""
        c, t, rng = self.c, self.t, self.rng
        lake = (t.lakes >= 0) & (c.water > c.height)
        ys, xs = np.nonzero(lake)
        for i, j in zip(ys.tolist(), xs.tolist()):
            x, z = j + c.x0, i + c.z0
            depth = int(c.water[i, j]) - int(c.height[i, j])
            wl = int(c.water[i, j])
            r = rng.random()
            if c.fluid[i, j] != c.sid("water"):
                continue
            if depth == 1 and r < 0.25:
                c.set(x, wl, z, WW + "cattail[half=lower,swaying=false,waterlogged=true]")
                c.set(x, wl + 1, z, WW + "cattail[half=upper,swaying=false,waterlogged=false]")
            elif depth >= 2 and r < 0.05:
                c.set(x, wl + 1, z, rng.choice((WW + "flowering_lily_pad", "minecraft:lily_pad")))
            elif depth >= 2 and r < 0.12:
                c.set(x, int(c.height[i, j]) + 1, z, "minecraft:seagrass")
        # sugar cane on the banks
        bank = t.land & (c.water <= c.height) & ~t.no_trees
        near = np.zeros_like(bank)
        for dz, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            near |= np.roll(lake, (dz, dx), axis=(0, 1))
        ys, xs = np.nonzero(bank & near)
        for i, j in zip(ys.tolist(), xs.tolist()):
            if rng.random() < 0.12 and not self.slabbed[i, j]:
                x, z, y = j + c.x0, i + c.z0, int(c.height[i, j])
                # cane needs water right beside the block it grows on
                if not any(lake[i + di, j + dj] and c.water[i + di, j + dj] == y
                           for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    continue
                for k in range(1, rng.randint(2, 4)):
                    if is_air(c, x, y + k, z):
                        c.set(x, y + k, z, "minecraft:sugar_cane[age=0]")

    # ------------------------------------------------------------------ reefs
    def reefs(self):
        """Coral gardens, anemones, sea whips, tube worms and kelp in the warm shallows."""
        c, t, rng = self.c, self.t, self.rng
        corals = ["tube", "brain", "bubble", "fire", "horn"]
        sea = (~t.land) & (c.height < SEA - 2) & (c.height > SEA - 22)
        ys, xs = np.nonzero(sea)
        for i, j in zip(ys.tolist(), xs.tolist()):
            r = rng.random()
            if r > 0.13:
                continue
            x, z = j + c.x0, i + c.z0
            y = int(c.height[i, j])
            depth = SEA - y
            if r < 0.014:
                col = rng.choice(corals)
                c.set(x, y, z, f"minecraft:{col}_coral_block")
                c.set(x, y + 1, z, f"minecraft:{col}_coral[waterlogged=true]" if rng.random() < 0.6
                      else f"minecraft:{col}_coral_fan[waterlogged=true]")
            elif r < 0.05:
                c.set(x, y + 1, z, "minecraft:seagrass")
            elif r < 0.058 and depth > 4:
                c.set(x, y + 1, z, "minecraft:tall_seagrass[half=lower]")
                c.set(x, y + 2, z, "minecraft:tall_seagrass[half=upper]")
            elif r < 0.07:
                c.set(x, y + 1, z, WW + "sea_anemone")
            elif r < 0.082:
                c.set(x, y + 1, z, WW + "sea_whip")
            elif r < 0.09:
                n = rng.randint(1, 3)
                if n == 1:
                    c.set(x, y + 1, z, WW + "tube_worms[part=single]")
                else:
                    for k in range(n):
                        part = "bottom" if k == 0 else ("top" if k == n - 1 else "middle")
                        c.set(x, y + 1 + k, z, f"{WW}tube_worms[part={part}]")
            elif r < 0.105 and depth > 7:
                top = rng.randint(3, depth - 2)
                for dy in range(1, top):
                    c.set(x, y + dy, z, "minecraft:kelp_plant")
                c.set(x, y + top, z, "minecraft:kelp[age=20]")
            elif r < 0.11:
                c.set(x, y + 1, z, "minecraft:sea_pickle[pickles=3,waterlogged=true]")

    def run(self):
        self.terrain_slabs()
        self.vegetation()
        self.waters_edge()
        self.reefs()
        print("  nature: " + ", ".join(f"{v} {k}" for k, v in sorted(self.stats.items())))
