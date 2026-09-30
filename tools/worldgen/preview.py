"""Render a top-down PNG of the canvas (stdlib PNG writer)."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np

from .canvas import MIN_Y, NONE, SEA, Canvas

COLORS = {
    "grass_block": (98, 160, 60), "sand": (219, 207, 163), "red_sand": (190, 102, 33), "stone": (125, 125, 125),
    "andesite": (136, 136, 137), "tuff": (108, 109, 102), "snow_block": (240, 250, 250), "packed_ice": (140, 180, 250),
    "basalt": (70, 70, 75), "blackstone": (42, 36, 41), "smooth_basalt": (72, 72, 78), "magma_block": (160, 70, 20),
    "podzol": (91, 63, 24), "coarse_dirt": (119, 85, 59), "rooted_dirt": (144, 103, 76), "mud": (60, 57, 60),
    "moss_block": (89, 109, 45), "gravel": (131, 127, 126), "clay": (160, 166, 179), "smooth_quartz": (235, 229, 222),
    "dirt_path": (148, 122, 65), "terracotta": (152, 94, 67), "water": (40, 110, 200), "lava": (230, 110, 20),
}


def _color(name: str) -> tuple[int, int, int]:
    base = name.split("[", 1)[0].split(":", 1)[-1]
    if base in COLORS:
        return COLORS[base]
    for key, col in (("asphalt", (58, 58, 62)), ("linie", (58, 58, 62)), ("stufe", (58, 58, 62)),
                     ("sidewalk", (175, 175, 170)), ("grass_slab", (98, 160, 60)), ("sand_slab", (219, 207, 163)),
                     ("path_slab", (148, 122, 65)), ("_branch", (100, 80, 50)), ("palm_fronds", (60, 140, 50)),
                     ("hibiscus", (230, 90, 140)), ("wildflowers", (230, 160, 80)), ("flagstone", (200, 190, 150)),
                     ("paving", (190, 180, 150)), ("terracotta", (160, 90, 60)), ("concrete", (200, 200, 200)), ("leaves", (50, 120, 40)),
                     ("log", (100, 80, 50)), ("planks", (170, 130, 80)), ("brick", (150, 80, 70)),
                     ("quartz", (235, 230, 225)), ("glass", (180, 220, 240)), ("wool", (210, 210, 210)),
                     ("stone", (130, 130, 130)), ("slab", (150, 150, 150)), ("stairs", (150, 150, 150)),
                     ("sand", (215, 200, 150)), ("flower", (230, 80, 120)), ("grass", (90, 150, 50)),
                     ("poppy", (200, 40, 40)), ("dandelion", (240, 220, 40)), ("tulip", (230, 120, 60)),
                     ("allium", (180, 100, 220)), ("daisy", (240, 240, 230)), ("cornflower", (80, 110, 230)),
                     ("fern", (80, 140, 50)), ("mud", (90, 70, 60)), ("wood", (150, 110, 70)), ("bush", (60, 110, 40)),
                     ("torch", (250, 200, 80)), ("lamp", (250, 230, 150)), ("fence", (140, 110, 70)),
                     ("concrete", (200, 200, 200)), ("sofa", (200, 50, 50)), ("chair", (160, 120, 80))):
        if key in base:
            return col
    return (200, 60, 200)


def render(c: Canvas, path: Path, scale: int = 1, crop=None) -> None:
    h = c.height.astype(np.int32)
    wl = c.water.astype(np.int32)
    palette = np.array([_color(s) for s in c.states], dtype=np.float32)
    img = palette[c.top].copy()
    top_y = h.copy()
    # overlay placed blocks: highest non-air per column
    air = c.sid("minecraft:air")
    for (cx, cz, sy), sec in c.sections.items():
        x0, z0 = cx * 16 - c.x0, cz * 16 - c.z0
        y0 = MIN_Y + sy * 16
        for ly in range(15, -1, -1):
            layer = sec[ly]
            mask = (layer != NONE) & (layer != air)
            if not mask.any():
                continue
            ys = y0 + ly
            zz, xx = np.nonzero(mask)
            cur = top_y[z0 + zz, x0 + xx]
            upd = ys >= cur
            top_y[z0 + zz[upd], x0 + xx[upd]] = ys
            img[z0 + zz[upd], x0 + xx[upd]] = palette[layer[zz[upd], xx[upd]]]
    water = (wl > top_y)
    depth = np.clip(wl - top_y, 0, 30)
    wcol = np.stack([40 - depth * 0.6, 120 - depth * 1.8, 205 - depth * 2.2], axis=-1)
    lava = c.fluid == c.sid("lava")
    wcol[lava] = (230, 110, 20)
    img = np.where(water[..., None], wcol, img)
    # hillshade
    gz, gx = np.gradient(top_y.astype(np.float32))
    shade = np.clip(1.0 + (-gx - gz) * 0.06, 0.6, 1.35)
    img = img * shade[..., None]
    img = np.clip(img, 0, 255).astype(np.uint8)
    if crop:
        x1, z1, x2, z2 = crop
        img = img[z1 - c.z0:z2 - c.z0, x1 - c.x0:x2 - c.x0]
    if scale > 1:
        img = img[::scale, ::scale]
    hgt, wid = img.shape[:2]
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(hgt))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", wid, hgt, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
