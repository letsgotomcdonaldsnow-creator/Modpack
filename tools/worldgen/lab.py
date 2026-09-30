"""A test platform for the CI screenshot tour (only built when ALOLA_LAB=1, never shipped).

It sits on an artificial island in the empty north-east corner of the map and holds a
labelled showroom of every block of the decoration mods we build with, plus sample
buildings, so each new design can be checked in real in-game screenshots.
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

import numpy as np

from .canvas import SEA, Canvas

ENABLED = os.environ.get("ALOLA_LAB") == "1"
X0, Z0, X1, Z1 = 960, -1270, 1270, -960
Y = SEA + 1
CATALOG = Path(__file__).with_name("block_catalog.json")
SHOWROOM = [  # (namespace, regex on the block path or None for all)
    ("saros_road_blocks_mod", None), ("saros_road_signs_mod", None), ("cobblefurnies", None), ("pokeblocks", None),
    ("beachparty", None), ("mcwlights", None), ("wilderflowers", None), ("terrain_slabs", None), ("beautify", None),
    ("wilderwild", r"hibiscus|bush|palm|coconut|cattail|lily|anemone|whip|tube|barnacle|hollowed_oak|shelf_fungi|prickly"
                   r"|tumble|termite|geyser|gabbro|wildflowers|clovers|phlox|lantanas|marigold|carnation|datura|milkweed"
                   r"|pasque|seeding|scorched|display_lantern|stone_chest|algae|pollen|moss|leaf_litter"),
    ("dynamictrees", r"branch|leaves|rooty_(grass|sand|dirt)|trunk"),
    ("mcwroofs", r"^(red_terracotta|gray_terracotta|light_blue_terracotta|oak|spruce|deepslate|red_nether_bricks)_|awning"),
    ("mcwwindows", r"^(oak|birch|jungle|dark_oak)_|^(metal|quartz|stone)_|curtain|blinds"),
    ("mcwdoors", r"^(oak|jungle|birch|spruce|dark_oak)_|^(metal|store|sliding|garage)"),
    ("mcwtrpdoors", r"^(oak|jungle|birch)_"),
    ("mcwstairs", r"^(oak|quartz|sandstone)_"),
    ("mcwfences", r"^oak_|hedge|metal|quartz|sandstone"),
    ("mcwpaths", r"^(andesite|sandstone|brick|cobblestone|oak_planks)_"),
    ("mcwbridges", r"oak|rope|bridge_lantern|bridge_torch"),
    ("mcwfurnitures", r"^oak_"),
    ("handcrafted", r"^(oak_|birch_|kitchen|oven|terracotta|wood_|bench|white)"),
    ("another_furniture", r"^(oak|birch|white|red)_|service_bell"),
    ("supplementaries", r"awning|flower_box|planter|bunting|sconce|doormat|notice_board|globe|item_shelf|jar$|sack"
                        r"|pedestal|candle_holder$|book_pile|hourglass|clock_block|flag_(red|white|yellow)|lunch_basket"
                        r"|safe|statue|wind_vane|sign_post|urn|lamp|hat_stand|timber"),
    ("mcwholidays", r"string_lights|garland$|balloon"),
    ("legendarymonuments", None),
    ("cobblemon", r"apricorn_(planks|log|leaves)|healing|^pc|display|pasture|restoration|fossil|lectern|monitor"
                  r"|incubator|gilded|berry|cake|mint|saccharine"),
]
COLS, ROWS = 8, 3
SAMPLES: list = []   # (name, fn(c, x, y, z)) registered by the building kit for the lab


def _look(cam, target):
    dx, dy, dz = (t - c for t, c in zip(target, cam))
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz)))
    return round(yaw, 1), round(pitch, 1)


def _show_state(name: str, info: dict) -> str:
    props = []
    info = info or {}
    for key, want in (("facing", "south"), ("half", "lower"), ("part", "bottom"), ("type", "bottom")):
        if key in info and want in info[key]:
            props.append(f"{key}={want}")
    return name + (f"[{','.join(props)}]" if props else "")


def platform(c: Canvas):
    i1, i2, j1, j2 = Z0 - c.z0, Z1 - c.z0, X0 - c.x0, X1 - c.x0
    c.height[i1:i2, j1:j2] = Y - 1
    c.water[i1:i2, j1:j2] = -64
    c.top[i1:i2, j1:j2] = c.sid("minecraft:white_concrete")
    c.sub[i1:i2, j1:j2] = c.sid("minecraft:stone")
    c.deep[i1:i2, j1:j2] = c.sid("minecraft:stone")
    c.biome[i1 // 4:i2 // 4, j1 // 4:j2 // 4] = c.bid("minecraft:plains")
    for cx in range(X0 >> 4, (X1 >> 4) + 1):
        for cz in range(Z0 >> 4, (Z1 >> 4) + 1):
            c.touched.add((cx, cz))


def showroom(c: Canvas) -> list[tuple]:
    catalog = json.loads(CATALOG.read_text())
    blocks = []
    for ns, rx in SHOWROOM:
        if ns == "saros_road_blocks_mod":   # every road marking of the plain asphalt block
            for tv in catalog.get("saros_road_blocks_mod:asphalt", {}).get("texture_variant", []):
                blocks.append((f"saros_road_blocks_mod:asphalt[facing=south,texture_variant={tv}]", f"asphalt {tv}"))
        for n in sorted(k for k in catalog if k.startswith(ns + ":")):
            if "potted_" in n or n.endswith(("_wall_sign", "_wall_hanging_sign", "_wall_torch", "_wall_banner")):
                continue
            if rx and not re.search(rx, n.split(":", 1)[1]):
                continue
            blocks.append((_show_state(n, catalog[n]), n.split(":")[1]))
    per = COLS * ROWS
    width = COLS * 3
    views = []
    y = Y - 1
    panels = (len(blocks) + per - 1) // per
    for p in range(panels):
        px = X0 + 4 + (p % 10) * (width + 3)
        pz = Z0 + 4 + (p // 10) * (ROWS * 4 + 5)
        for k, (state, label) in enumerate(blocks[p * per:(p + 1) * per]):
            bx, bz = px + (k % COLS) * 3, pz + (k // COLS) * 4
            c.set(bx, y + 1, bz, state)
            c.sign(bx, y + 1, bz + 1, [label[:15], label[15:30]], wood="birch", rotation=0)
        cx, cz = px + width / 2 - 1.5, pz + ROWS * 2
        cam = (cx, y + 9, cz + 13)
        views.append((f"showroom_{p + 1:02d}", cam, _look(cam, (cx, y + 1, cz)), 12))
    print(f"  lab showroom: {len(blocks)} blocks on {panels} panels")
    return views


def samples(c: Canvas) -> list[tuple]:
    """Sample buildings in a row along the south half of the platform."""
    views = []
    x = X0 + 6
    z = Z1 - 28
    for name, fn in SAMPLES:
        w, d = fn(c, x, Y, z)
        cx, cz = x + w / 2, z + d / 2
        views.append((f"lab_{name}_front", (cx + 0.5, Y + 6, z - 16), _look((cx, Y + 6, z - 16), (cx, Y + 3, cz)), 14))
        views.append((f"lab_{name}_corner", (x - 10, Y + 14, z - 12), _look((x - 10, Y + 14, z - 12), (cx, Y + 2, cz)), 14))
        x += w + 12
        if x > X1 - 40:
            x, z = X0 + 6, z - 38
    return views


def build(c: Canvas) -> list[tuple]:
    if not ENABLED:
        return []
    from . import arch
    from .kit import connect_all
    platform(c)
    arch.register_lab()
    views = showroom(c) + samples(c)
    connect_all(c)
    arch.fix_shapes(c)
    return views
