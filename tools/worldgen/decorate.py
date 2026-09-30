"""Routes, vegetation, reefs, signs and buildings on top of the terrain."""
from __future__ import annotations

import math
import random

import numpy as np

from . import alola_map, terrain as T
from .canvas import SEA, Canvas


def run(c: Canvas, t: T.Terrain) -> None:
    rng = random.Random(7)
    path_mask = np.zeros(c.height.shape, dtype=bool)
    for label, pts, width in alola_map.ROUTES:
        draw_route(c, t, pts, width, path_mask, rng)
    t.no_trees |= path_mask
    from . import landmarks, nature
    landmarks.build_all(c, t, rng)          # towns and landmarks (marks t.no_trees)
    wild = nature.Nature(c, t, rng)
    wild.terrain_slabs()
    for label, pts, width in alola_map.ROUTES:
        route_sign(c, pts, label)
        encounter_grass(c, t, pts, width, rng, wild.slabbed)
    wild.vegetation()
    wild.waters_edge()
    wild.reefs()
    print("  nature: " + ", ".join(f"{v} {k}" for k, v in sorted(wild.stats.items())))


# ------------------------------------------------------------------ routes

def _line(points, step=1.0):
    for (x1, z1), (x2, z2) in zip(points, points[1:]):
        n = max(1, int(math.hypot(x2 - x1, z2 - z1) / step))
        for i in range(n):
            f = i / n
            yield x1 + (x2 - x1) * f, z1 + (z2 - z1) * f
    yield points[-1]


def _smooth(points, passes=2):
    pts = list(points)
    for _ in range(passes):
        out = [pts[0]]
        for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
            out += [(0.75 * x1 + 0.25 * x2, 0.75 * z1 + 0.25 * z2), (0.25 * x1 + 0.75 * x2, 0.25 * z1 + 0.75 * z2)]
        out.append(pts[-1])
        pts = out
    return pts


def draw_route(c: Canvas, t: T.Terrain, points, width, mask, rng):
    pts = list(_line(_smooth(points), 1.0))
    ys = []
    for x, z in pts:
        i, j = int(z) - c.z0, int(x) - c.x0
        ys.append(float(c.height[i, j]))
    ys = np.array(ys)
    k = 25
    if len(ys) > k:
        kernel = np.ones(k) / k
        padded = np.pad(ys, k // 2, mode="edge")
        ys = np.convolve(padded, kernel, mode="valid")[: len(pts)]
    path = c.sid("minecraft:dirt_path")
    edge = [c.sid("minecraft:coarse_dirt"), c.sid("minecraft:gravel"), c.sid("minecraft:grass_block")]
    r = width / 2
    for (x, z), y in zip(pts, ys):
        y = int(round(max(y, SEA + 1)))
        ri = int(math.ceil(r)) + 1
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                d = math.hypot(dx, dz)
                if d > r + 1:
                    continue
                xx, zz = int(x) + dx, int(z) + dz
                if not c.inside(xx, zz):
                    continue
                i, j = zz - c.z0, xx - c.x0
                if not t.land[i, j] or not math.isnan(t.fixed[i, j]):
                    continue
                if d <= r:
                    old = c.height[i, j]
                    c.height[i, j] = y
                    if old > y:  # cut into slopes: keep a clean wall of the old surface below
                        pass
                    c.top[i, j] = path if rng.random() > 0.08 else edge[rng.randrange(2)]
                    c.sub[i, j] = c.sid("minecraft:dirt")
                    mask[i, j] = True
                else:
                    c.height[i, j] = int(round((c.height[i, j] + y) / 2))


def route_sign(c: Canvas, points, label):
    if label.startswith("Route to") or label.endswith("path") or "(" in label:
        return
    x, z = points[0]
    dx, dz = points[1][0] - x, points[1][1] - z
    n = math.hypot(dx, dz) or 1
    sx, sz = int(x + dz / n * 4), int(z - dx / n * 4)
    if not c.inside(sx, sz) or c.is_water(sx, sz):
        return
    y = c.surface(sx, sz) + 1
    rot = int(round((math.degrees(math.atan2(-dx, dz)) % 360) / 22.5)) % 16
    c.set(sx, y, sz, "minecraft:spruce_fence")
    c.sign(sx, y + 1, sz, [label, "", "Alola Region", ""], wood="spruce", rotation=rot)


def encounter_grass(c: Canvas, t: T.Terrain, points, width, rng, slabbed=None):
    """Patches of tall grass beside the route, where wild Pokémon hide."""
    pts = list(_line(points, 30.0))
    for idx, (x, z) in enumerate(pts[1:-1]):
        side = 1 if idx % 2 else -1
        (x2, z2) = pts[idx + 2]
        dx, dz = x2 - x, z2 - z
        n = math.hypot(dx, dz) or 1
        cx, cz = x + side * dz / n * (width / 2 + 4), z - side * dx / n * (width / 2 + 4)
        for ox in range(-4, 5):
            for oz in range(-3, 4):
                if rng.random() < 0.15:
                    continue
                xx, zz = int(cx) + ox, int(cz) + oz
                if not c.inside(xx, zz) or c.is_water(xx, zz):
                    continue
                i, j = zz - c.z0, xx - c.x0
                if t.no_trees[i, j] or c.states[c.top[i, j]] != "minecraft:grass_block":
                    continue
                if slabbed is not None and slabbed[i, j]:
                    continue
                y = c.surface(xx, zz)
                c.set(xx, y + 1, zz, "minecraft:tall_grass[half=lower]")
                c.set(xx, y + 2, zz, "minecraft:tall_grass[half=upper]")
