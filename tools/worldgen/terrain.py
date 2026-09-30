"""Heightmap / zone-map terrain synthesis on a numpy grid."""
from __future__ import annotations

import math

import numpy as np

from .canvas import FLAT_FLOOR, SEA, Canvas

# Zones decide surface materials and biomes.
OCEAN, GRASS, BEACH, JUNGLE, VOLCANIC, DESERT, CANYON, SNOW, MEADOW, ROCKY, RAINY, RANCH, TOWN, FOREST, \
    PLATFORM, CAVE_HILL, SAVANNA, FLOWERS, GARDEN = range(19)


def value_noise(shape: tuple[int, int], scale: float, seed: int) -> np.ndarray:
    """Smooth value noise in [-1, 1] sampled on a grid, `scale` blocks per cell."""
    rng = np.random.default_rng(seed)
    gh, gw = int(shape[0] / scale) + 3, int(shape[1] / scale) + 3
    grid = rng.uniform(-1, 1, (gh, gw)).astype(np.float32)
    ys = np.arange(shape[0], dtype=np.float32) / scale
    xs = np.arange(shape[1], dtype=np.float32) / scale
    y0 = ys.astype(np.int32)
    x0 = xs.astype(np.int32)
    ty = ys - y0
    tx = xs - x0
    ty = ty * ty * (3 - 2 * ty)
    tx = tx * tx * (3 - 2 * tx)
    a = grid[y0][:, x0]
    b = grid[y0][:, x0 + 1]
    c = grid[y0 + 1][:, x0]
    d = grid[y0 + 1][:, x0 + 1]
    top = a + (b - a) * tx[None, :]
    bot = c + (d - c) * tx[None, :]
    return top + (bot - top) * ty[:, None]


def fbm(shape, scale, seed, octaves=4) -> np.ndarray:
    total = np.zeros(shape, dtype=np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        total += amp * value_noise(shape, max(2.0, scale / (2 ** o)), seed + o * 101)
        norm += amp
        amp *= 0.5
    return total / norm


class Terrain:
    def __init__(self, canvas: Canvas, seed: int = 2016):
        self.c = canvas
        self.seed = seed
        shape = (canvas.d, canvas.w)
        zs = np.arange(canvas.z0, canvas.z0 + canvas.d, dtype=np.float32)
        xs = np.arange(canvas.x0, canvas.x0 + canvas.w, dtype=np.float32)
        self.X, self.Z = np.meshgrid(xs, zs)
        self.land = np.zeros(shape, dtype=bool)
        self.elev = np.zeros(shape, dtype=np.float32)     # extra height above the coastal ramp
        self.zone = np.full(shape, OCEAN, dtype=np.uint8)
        self.noise = fbm(shape, 96, seed, 5)
        self.detail = fbm(shape, 12, seed + 7, 2)
        self.fixed = np.full(shape, np.nan, dtype=np.float32)   # forced heights (towns, paths)
        self.lakes = np.full(shape, -1, dtype=np.int16)          # lake water level where >= 0
        self.no_trees = np.zeros(shape, dtype=bool)
        self.carved = np.zeros(shape, dtype=np.float32)
        self.field = np.full(shape, -1.0, dtype=np.float32)
        self.coast = fbm(shape, 72, seed + 31, 4)

    # ------------------------------------------------------------ shapes
    def ellipse_mask(self, cx, cz, rx, rz, rot=0.0, wobble=0.12, seed=0):
        dx, dz = self.X - cx, self.Z - cz
        ca, sa = math.cos(rot), math.sin(rot)
        u, v = dx * ca + dz * sa, -dx * sa + dz * ca
        ang = np.arctan2(v / rz, u / rx)
        rng = np.random.default_rng(self.seed + seed)
        mod = np.ones_like(ang)
        for k in range(2, 7):
            mod += wobble / k * rng.uniform(0.5, 1.5) * np.sin(k * ang + rng.uniform(0, 6.28))
        r = np.sqrt((u / rx) ** 2 + (v / rz) ** 2)
        return r <= mod

    def island_field(self, cx, cz, rx, rz, rot=0.0, wobble=0.14, seed=0):
        dx, dz = self.X - cx, self.Z - cz
        ca, sa = math.cos(rot), math.sin(rot)
        u, v = dx * ca + dz * sa, -dx * sa + dz * ca
        ang = np.arctan2(v / rz, u / rx)
        rng = np.random.default_rng(self.seed + seed)
        mod = np.ones_like(ang)
        for k in range(2, 9):
            mod += wobble / k * rng.uniform(0.5, 1.5) * np.sin(k * ang + rng.uniform(0, 6.28))
        r = np.sqrt((u / rx) ** 2 + (v / rz) ** 2)
        return 1 - r / mod

    def add_island(self, cx, cz, rx, rz, rot=0.0, wobble=0.14, seed=0, zone=GRASS):
        f = self.island_field(cx, cz, rx, rz, rot, wobble, seed)
        self.field = np.maximum(self.field, f)
        m = f + self.coast * 0.14 > 0
        self.zone[m & (self.zone == OCEAN)] = zone
        return m

    def cut_bay(self, cx, cz, rx, rz, rot=0.0, seed=0):
        f = self.island_field(cx, cz, rx, rz, rot, 0.08, seed)
        self.field = np.where(f > 0, np.minimum(self.field, -f), self.field)

    def paint(self, cx, cz, rx, rz, zone, rot=0.0, wobble=0.2, seed=0, only_land=True):
        m = self.ellipse_mask(cx, cz, rx, rz, rot, wobble, seed)
        if only_land:
            m &= self.land | ((self.field + self.coast * 0.14) > 0)
        self.zone[m] = zone
        return m

    # ----------------------------------------------------------- relief
    def _r(self, x, z):
        return np.sqrt((self.X - x) ** 2 + (self.Z - z) ** 2)

    def hill(self, x, z, r, h, sharp=2.0):
        d = self._r(x, z) / r
        self.elev += h * np.exp(-(d ** sharp))

    def cone(self, x, z, r, h, crater_r=0, crater_depth=0):
        d = self._r(x, z)
        prof = np.clip(1 - d / r, 0, 1) ** 1.3 * h
        if crater_r:
            inside = d < crater_r
            rim = h * (1 - crater_r / r) ** 1.3
            prof = np.where(inside, rim - crater_depth * (1 - (d / crater_r) ** 2), prof)
        self.elev = np.maximum(self.elev, prof) if h > 0 else self.elev + prof

    def mesa(self, x, z, rx, rz, h, rot=0.0, seed=0):
        m = self.ellipse_mask(x, z, rx, rz, rot, 0.18, seed)
        soft = self.ellipse_mask(x, z, rx * 1.15, rz * 1.15, rot, 0.18, seed)
        self.elev = np.where(m, np.maximum(self.elev, h), np.where(soft, np.maximum(self.elev, h * 0.55), self.elev))

    def carve(self, points, width, depth):
        """Cut a winding valley/canyon along a polyline (depth relative to current elevation)."""
        for (x1, z1), (x2, z2) in zip(points, points[1:]):
            seg = max(1, int(math.hypot(x2 - x1, z2 - z1) / 4))
            for t in np.linspace(0, 1, seg):
                x, z = x1 + (x2 - x1) * t, z1 + (z2 - z1) * t
                d = self._r(x, z)
                cut = np.clip(1 - d / width, 0, 1) ** 0.6 * depth
                self.carved = np.maximum(self.carved, cut)

    BLEND_MAX = 48      # widest apron round a flattened site

    def _box(self, xa, za, xb, zb):
        """Array slices covering a world box grown by BLEND_MAX, clipped to the canvas."""
        m = self.BLEND_MAX
        i1 = max(0, za - m - self.c.z0); i2 = min(self.c.d, zb + m + 1 - self.c.z0)
        j1 = max(0, xa - m - self.c.x0); j2 = min(self.c.w, xb + m + 1 - self.c.x0)
        return slice(i1, i2), slice(j1, j2)

    def flatten(self, x1, z1, x2, z2, y, margin=16, zone=None):
        xa, xb = min(x1, x2), max(x1, x2)
        za, zb = min(z1, z2), max(z1, z2)
        dx = np.maximum(np.maximum(xa - self.X, self.X - xb), 0)
        dz = np.maximum(np.maximum(za - self.Z, self.Z - zb), 0)
        d = np.sqrt(dx ** 2 + dz ** 2)
        core = d == 0
        self.fixed[core] = y
        self.land |= core
        sz, sx = self._box(xa, za, xb, zb)
        self._blend_targets.append((sz, sx, d[sz, sx].astype(np.float32), y, margin))
        self.no_trees |= core
        if zone is not None:
            self.zone[core] = zone

    def disk_flat(self, x, z, r, y, margin=12, zone=None):
        d = self._r(x, z)
        core = d <= r
        self.fixed[core] = y
        self.land |= core
        sz, sx = self._box(int(x - r), int(z - r), int(x + r), int(z + r))
        self._blend_targets.append((sz, sx, np.maximum(d[sz, sx] - r, 0).astype(np.float32), y, margin))
        self.no_trees |= core
        if zone is not None:
            self.zone[core] = zone

    def lake(self, x, z, rx, rz, level, depth=5, rot=0.0, seed=0):
        m = self.ellipse_mask(x, z, rx, rz, rot, 0.15, seed)
        self.lakes[m] = level
        self._lake_masks.append((m, level, depth))
        self.no_trees |= m

    # ------------------------------------------------------------ build
    def begin(self):
        self._blend_targets = []
        self._lake_masks = []

    def compute(self):
        """Resolve all of the above into canvas columns."""
        c = self.c
        self.land |= (self.field + self.coast * 0.14) > 0
        self.land &= ~((self.field < -0.5) & (np.isnan(self.fixed)))
        land = self.land.copy()
        self.zone[~land] = OCEAN
        self.zone[land & (self.zone == OCEAN)] = GRASS
        # distance inland (steps of erosion) and offshore (steps of dilation)
        inland = np.zeros(land.shape, dtype=np.int16)
        cur = land.copy()
        for i in range(40):
            nxt = cur.copy()
            nxt[1:, :] &= cur[:-1, :]
            nxt[:-1, :] &= cur[1:, :]
            nxt[:, 1:] &= cur[:, :-1]
            nxt[:, :-1] &= cur[:, 1:]
            inland += nxt
            cur = nxt
        off = np.zeros(land.shape, dtype=np.int16)
        cur = land.copy()
        for i in range(48):
            nxt = cur.copy()
            nxt[1:, :] |= cur[:-1, :]
            nxt[:-1, :] |= cur[1:, :]
            nxt[:, 1:] |= cur[:, :-1]
            nxt[:, :-1] |= cur[:, 1:]
            off += ~nxt
            cur = nxt
        off = 48 - np.minimum(off, 48)  # 0 at coast .. 48 far
        off = np.where(land, 0, 48 - off)
        self.inland = inland

        ramp = np.minimum(inland, 36).astype(np.float32) * 0.28
        h = SEA + 1 + ramp + self.elev * (0.25 + 0.75 * np.clip(inland / 12.0, 0, 1)) \
            + self.noise * 5.0 * np.clip(inland / 10.0, 0, 1) + self.detail * 1.2
        seabed = SEA - 2 - off * 0.6 + self.noise * 2
        h = np.where(land, h, np.maximum(seabed, FLAT_FLOOR))
        # far ocean exactly matches the flat generator
        h = np.where((~land) & (off >= 34), FLAT_FLOOR, h)

        h = h - self.carved
        # ease every flattened site into the land round it: the apron widens with the height difference
        # (about 2.4 blocks out per block of height) and follows a smoothstep, so no slope is steeper than ~0.6
        for sz, sx, d, y, margin in self._blend_targets:
            hs = h[sz, sx]
            m = np.clip(np.abs(hs - y) * 2.4, margin, self.BLEND_MAX)
            t = np.clip(1 - d / m, 0, 1)
            w = t * t * (3 - 2 * t)
            apron = (d > 0) & land[sz, sx]
            hs[apron] = hs[apron] * (1 - w[apron]) + y * w[apron]
        fixed = ~np.isnan(self.fixed)
        h[fixed] = self.fixed[fixed]
        hi = np.round(h).astype(np.int16)
        water = np.where(land, np.int16(-64), np.int16(SEA)).astype(np.int16)
        dry = land & (self.lakes < 0)
        hi[dry] = np.maximum(hi[dry], SEA + 1)
        for mask, level, depth in self._lake_masks:
            hi[mask] = np.minimum(hi[mask], level - 1 - np.clip(self.inland_from(mask), 0, depth))
            water[mask] = level
            # graded shores: the ground climbs 0.7 blocks per block away from the waterline
            # instead of standing as a wall around the lake (flattened town sites are left alone)
            ring = mask.copy()
            for d in range(1, 14):
                grown = ring.copy()
                grown[1:, :] |= ring[:-1, :]
                grown[:-1, :] |= ring[1:, :]
                grown[:, 1:] |= ring[:, :-1]
                grown[:, :-1] |= ring[:, 1:]
                edge = grown & ~ring & ~fixed
                hi[edge] = np.minimum(hi[edge], level + int(d * 0.7))
                ring = grown
        c.height[:] = hi
        c.water[:] = water
        self.h = hi

        # slope for rock exposure
        gz, gx = np.gradient(hi.astype(np.float32))
        self.slope = np.sqrt(gx ** 2 + gz ** 2)

    def inland_from(self, mask: np.ndarray) -> np.ndarray:
        d = np.zeros(mask.shape, dtype=np.int16)
        cur = mask.copy()
        for _ in range(6):
            nxt = cur.copy()
            nxt[1:, :] &= cur[:-1, :]
            nxt[:-1, :] &= cur[1:, :]
            nxt[:, 1:] &= cur[:, :-1]
            nxt[:, :-1] &= cur[:, 1:]
            d += nxt
            cur = nxt
        return d[mask]


# ------------------------------------------------------------------ surface

SURFACE = {
    # zone: (top, sub, deep)
    GRASS: ("grass_block", "dirt", "stone"),
    BEACH: ("sand", "sand", "sandstone"),
    JUNGLE: ("grass_block", "dirt", "stone"),
    VOLCANIC: ("basalt[axis=y]", "blackstone", "blackstone"),
    DESERT: ("sand", "sand", "sandstone"),
    CANYON: ("red_sand", "terracotta", "terracotta"),
    SNOW: ("snow_block", "packed_ice", "stone"),
    MEADOW: ("grass_block", "dirt", "stone"),
    ROCKY: ("stone", "stone", "stone"),
    RAINY: ("mud", "dirt", "stone"),
    RANCH: ("grass_block", "dirt", "stone"),
    TOWN: ("grass_block", "dirt", "stone"),
    FOREST: ("grass_block", "dirt", "stone"),
    PLATFORM: ("smooth_quartz", "quartz_block", "white_concrete"),
    CAVE_HILL: ("grass_block", "dirt", "stone"),
    SAVANNA: ("grass_block", "coarse_dirt", "stone"),
    FLOWERS: ("grass_block", "dirt", "stone"),
    GARDEN: ("moss_block", "dirt", "stone"),
    OCEAN: ("sand", "sand", "stone"),
}

CANYON_BANDS = ["terracotta", "orange_terracotta", "red_terracotta", "yellow_terracotta", "terracotta",
                "white_terracotta", "light_gray_terracotta", "brown_terracotta", "orange_terracotta", "red_terracotta"]


def apply_surface(t: Terrain, biome_for_zone: dict[int, str], seed: int = 3) -> None:
    c = t.c
    ids = {z: tuple(c.sid(b) for b in mats) for z, mats in SURFACE.items()}
    zone = t.zone
    top = np.zeros(zone.shape, dtype=np.uint16)
    sub = np.zeros(zone.shape, dtype=np.uint16)
    deep = np.zeros(zone.shape, dtype=np.uint16)
    for z, (a, b, d) in ids.items():
        m = zone == z
        top[m], sub[m], deep[m] = a, b, d
    h = c.height
    land = t.land
    # beaches along low coasts
    beach = land & (t.inland <= 4) & (h <= SEA + 3) & np.isin(zone, [GRASS, JUNGLE, FOREST, MEADOW, SAVANNA, FLOWERS, RANCH])
    top[beach], sub[beach] = ids[BEACH][0], ids[BEACH][1]
    # steep slopes show rock
    steep = land & (t.slope > 2.2) & ~np.isin(zone, [CANYON, SNOW, VOLCANIC, PLATFORM, DESERT])
    rng = np.random.default_rng(seed)
    rocks = np.array([c.sid("stone"), c.sid("andesite"), c.sid("tuff"), c.sid("stone")], dtype=np.uint16)
    top[steep] = rocks[rng.integers(0, 4, int(steep.sum()))]
    # snow line on high peaks, frozen tops
    high = land & (h >= 178)
    top[high], sub[high] = c.sid("snow_block"), c.sid("packed_ice")
    # volcanic rock in natural patches (smooth noise, not per-block speckle): tuff and gabbro on the
    # lower flanks, basalt and blackstone higher up, scorched sand drifts, magma only near the summit
    vol = zone == VOLCANIC
    if vol.any():
        det = t.detail
        hv = h[vol].astype(np.float32)
        top_h = float(hv.max()) if hv.size else 0.0
        low = h < top_h - 45
        pal = {
            "tuff": c.sid("tuff"), "gabbro": c.sid("wilderwild:gabbro"), "basalt": c.sid("basalt[axis=y]"),
            "smooth": c.sid("smooth_basalt"), "black": c.sid("blackstone"), "scorched": c.sid("wilderwild:scorched_red_sand"),
            "magma": c.sid("magma_block"), "gravel": c.sid("gravel"),
        }
        vt = np.where(det > 0.45, pal["scorched"],
             np.where(det > 0.15, pal["smooth"],
             np.where(det > -0.2, pal["basalt"],
             np.where(det > -0.5, pal["black"], pal["gabbro"]))))
        vt = np.where(low & (det < 0.1), np.where(det < -0.3, pal["tuff"], pal["gravel"]), vt)
        near_top = h > top_h - 12
        speck = rng.random(zone.shape) < 0.12
        vt = np.where(near_top & speck, pal["magma"], vt)
        top[vol] = vt[vol].astype(np.uint16)
    # canyon strata: color by height
    can = zone == CANYON
    band = np.array([c.sid(b) for b in CANYON_BANDS], dtype=np.uint16)
    top[can & (t.slope > 1.2)] = band[(h[can & (t.slope > 1.2)] // 3) % len(band)]
    deep[can] = band[(h[can] // 3) % len(band)]
    sub[can] = deep[can]
    # rainy: mix mud and podzol
    rain = zone == RAINY
    top[rain & (t.detail > 0.1)] = c.sid("podzol")
    # grass variety
    grassy = land & np.isin(zone, [GRASS, JUNGLE, FOREST, SAVANNA, MEADOW, FLOWERS, RANCH, TOWN])
    patchy = grassy & (t.detail > 0.55) & ~steep
    top[patchy & (zone == JUNGLE)] = c.sid("podzol")
    top[patchy & (zone == SAVANNA)] = c.sid("coarse_dirt")
    top[patchy & (zone == FOREST)] = c.sid("rooted_dirt")
    # underwater floors
    sea = ~land
    top[sea] = np.where(h[sea] > SEA - 6, c.sid("sand"),
                        np.where(t.detail[sea] > 0.3, c.sid("gravel"), c.sid("sand"))).astype(np.uint16)
    sub[sea] = c.sid("sand")
    deep[sea] = c.sid("stone")
    lakes = t.lakes >= 0
    top[lakes] = np.where(t.detail[lakes] > 0, c.sid("clay"), c.sid("gravel")).astype(np.uint16)
    far = sea & (h == FLAT_FLOOR)
    top[far], sub[far] = c.sid("sand"), c.sid("sand")
    c.top[:], c.sub[:], c.deep[:] = top, sub, deep
    c.fluid[:] = c.sid("water")
    # lava in volcanic crater lakes
    lava_lakes = lakes & (zone == VOLCANIC)
    c.fluid[lava_lakes] = c.sid("lava")

    # biomes on a 4x4 grid (majority-free: sample the cell centre)
    zc = zone[2::4, 2::4]
    hc = h[2::4, 2::4]
    lc = land[2::4, 2::4]
    bgrid = np.zeros(zc.shape, dtype=np.uint16)
    for z, name in biome_for_zone.items():
        bgrid[zc == z] = c.bid(name)
    beach_c = beach[2::4, 2::4]
    if "beach" in biome_for_zone.get("_extra", {}):
        pass
    bgrid[beach_c & lc] = c.bid(biome_for_zone[BEACH])
    bgrid[(hc >= 178) & lc] = c.bid(biome_for_zone[SNOW])
    deep_sea = (~lc) & (hc < SEA - 22)
    bgrid[~lc] = c.bid(biome_for_zone[OCEAN])
    bgrid[deep_sea] = c.bid(biome_for_zone.get("deep", biome_for_zone[OCEAN]))
    far_c = (~lc) & (hc == FLAT_FLOOR)
    bgrid[far_c] = 0  # warm_ocean, same as the flat generator
    c.biome[:] = bgrid
