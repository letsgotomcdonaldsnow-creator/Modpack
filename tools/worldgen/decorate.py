"""Routes, vegetation, reefs, signs and buildings on top of the terrain."""
from __future__ import annotations

import math
import random

import numpy as np

from . import alola_map, plants, terrain as T
from .canvas import SEA, Canvas


def run(c: Canvas, t: T.Terrain) -> None:
    rng = random.Random(7)
    path_mask = np.zeros(c.height.shape, dtype=bool)
    for label, pts, width in alola_map.ROUTES:
        draw_route(c, t, pts, width, path_mask, rng)
    t.no_trees |= path_mask
    from . import landmarks
    landmarks.build_all(c, t, rng)          # towns and landmarks (marks t.no_trees)
    for label, pts, width in alola_map.ROUTES:
        route_sign(c, pts, label)
        encounter_grass(c, t, pts, width, rng)
    vegetation(c, t, rng)
    reefs(c, t, rng)


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


def encounter_grass(c: Canvas, t: T.Terrain, points, width, rng):
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
                y = c.surface(xx, zz)
                c.set(xx, y + 1, zz, "minecraft:tall_grass[half=lower]")
                c.set(xx, y + 2, zz, "minecraft:tall_grass[half=upper]")


# -------------------------------------------------------------- vegetation

FLOWERS_WARM = ["minecraft:poppy", "minecraft:dandelion", "minecraft:red_tulip", "minecraft:orange_tulip",
                "minecraft:pink_tulip", "minecraft:allium", "minecraft:oxeye_daisy", "minecraft:cornflower"]


def vegetation(c: Canvas, t: T.Terrain, rng: random.Random):
    grass = c.sid("minecraft:grass_block")
    land = t.land & ~t.no_trees & (c.water < c.height)
    zone = t.zone
    inland = t.inland
    ys, xs = np.nonzero(land)
    order = np.arange(len(ys))
    np.random.default_rng(5).shuffle(order)
    count = 0
    for k in order:
        i, j = int(ys[k]), int(xs[k])
        x, z = j + c.x0, i + c.z0
        zn = int(zone[i, j])
        top = int(c.top[i, j])
        y = int(c.height[i, j])
        roll = rng.random()
        near_coast = inland[i, j] < 14
        if top == grass or zn in (T.GARDEN,):
            if zn in (T.GRASS, T.TOWN, T.FOREST, T.CAVE_HILL, T.RANCH) and near_coast and roll < 0.006:
                plants.palm(c, x, y, z, rng); count += 1
            elif zn == T.JUNGLE and roll < 0.02:
                if rng.random() < 0.25:
                    plants.jungle_tree(c, x, y, z, rng, big=True)
                else:
                    plants.jungle_tree(c, x, y, z, rng)
                count += 1
            elif zn == T.JUNGLE and roll < 0.05:
                plants.bush(c, x, y, z, rng, "jungle")
            elif zn == T.FOREST and roll < 0.012:
                (plants.jungle_tree if rng.random() < 0.3 else plants.round_tree)(c, x, y, z, rng); count += 1
            elif zn in (T.GRASS, T.CAVE_HILL) and roll < 0.0035:
                (plants.palm if rng.random() < 0.4 else plants.round_tree)(c, x, y, z, rng); count += 1
            elif zn == T.SAVANNA and roll < 0.004:
                plants.acacia(c, x, y, z, rng); count += 1
            elif zn == T.RAINY and roll < 0.01:
                plants.dark_oak(c, x, y, z, rng); count += 1
            elif zn == T.GARDEN and roll < 0.01:
                plants.cherry(c, x, y, z, rng); count += 1
            elif zn in (T.RANCH,) and roll < 0.001:
                plants.round_tree(c, x, y, z, rng); count += 1
            elif y > 150 and roll < 0.008:
                plants.spruce(c, x, y, z, rng, snowy=y > 170); count += 1
            elif zn in (T.FLOWERS, T.MEADOW, T.GARDEN) and roll < 0.35:
                c.set(x, y + 1, z, rng.choice(FLOWERS_WARM))
            elif roll < 0.30:
                c.set(x, y + 1, z, "minecraft:short_grass" if rng.random() < 0.85 else "minecraft:fern")
            elif roll < 0.315:
                c.set(x, y + 1, z, rng.choice(FLOWERS_WARM))
        elif zn == T.DESERT and roll < 0.004:
            plants.cactus(c, x, y, z, rng)
        elif zn in (T.DESERT, T.CANYON) and roll < 0.008:
            c.set(x, y + 1, z, "minecraft:dead_bush")
        elif zn == T.SNOW and y > 150 and y < 185 and roll < 0.006:
            plants.spruce(c, x, y, z, rng, snowy=True); count += 1
        elif zn == T.SNOW and roll < 0.5 and c.states[top].endswith("snow_block"):
            pass
        elif zn == T.ROCKY and roll < 0.003:
            plants.boulder(c, x, y, z, rng)
        elif c.states[top] == "minecraft:sand" and near_coast and zn != T.DESERT and roll < 0.002:
            plants.palm(c, x, y, z, rng); count += 1
    print(f"  vegetation: {count} trees")


def reefs(c: Canvas, t: T.Terrain, rng: random.Random):
    """Coral, seagrass and kelp in the warm shallows around the islands."""
    corals = ["tube", "brain", "bubble", "fire", "horn"]
    sea = (~t.land) & (c.height < SEA - 2) & (c.height > SEA - 22)
    ys, xs = np.nonzero(sea)
    for k in range(len(ys)):
        roll = rng.random()
        if roll > 0.09:
            continue
        i, j = int(ys[k]), int(xs[k])
        x, z = j + c.x0, i + c.z0
        y = int(c.height[i, j])
        if roll < 0.012:
            col = rng.choice(corals)
            c.set(x, y, z, f"minecraft:{col}_coral_block")
            c.set(x, y + 1, z, f"minecraft:{col}_coral[waterlogged=true]" if rng.random() < 0.6
                  else f"minecraft:{col}_coral_fan[waterlogged=true]")
        elif roll < 0.06:
            c.set(x, y + 1, z, "minecraft:seagrass")
        elif roll < 0.075 and SEA - y > 6:
            for dy in range(1, rng.randint(3, SEA - y - 1)):
                c.set(x, y + dy, z, "minecraft:kelp_plant")
            c.set(x, y + dy + 1, z, "minecraft:kelp[age=20]")
        elif roll < 0.08:
            c.set(x, y + 1, z, "minecraft:sea_pickle[pickles=3,waterlogged=true]")
