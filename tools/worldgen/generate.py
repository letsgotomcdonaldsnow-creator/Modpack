"""Generate the Alola region world save.

    python -m tools.worldgen.generate --out build/world/Alola --preview build/alola-map.png
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from . import alola_map, preview, terrain
from .canvas import Canvas, write_level_dat

ROOT = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).with_name("block_catalog.json")

VANILLA_BIOMES = {
    terrain.OCEAN: "minecraft:warm_ocean", "deep": "minecraft:lukewarm_ocean",
    terrain.GRASS: "minecraft:plains", terrain.BEACH: "minecraft:beach", terrain.JUNGLE: "minecraft:jungle",
    terrain.VOLCANIC: "minecraft:badlands", terrain.DESERT: "minecraft:desert", terrain.CANYON: "minecraft:eroded_badlands",
    terrain.SNOW: "minecraft:snowy_slopes", terrain.MEADOW: "minecraft:meadow", terrain.ROCKY: "minecraft:stony_peaks",
    terrain.RAINY: "minecraft:swamp", terrain.RANCH: "minecraft:plains", terrain.TOWN: "minecraft:plains",
    terrain.FOREST: "minecraft:forest", terrain.PLATFORM: "minecraft:plains", terrain.CAVE_HILL: "minecraft:forest",
    terrain.SAVANNA: "minecraft:savanna", terrain.FLOWERS: "minecraft:flower_forest", terrain.GARDEN: "minecraft:cherry_grove",
}
# Expanded Ecosphere's tropical biomes, used when the catalog says they exist.
TROPICAL = {
    terrain.GRASS: "wythers:tropical_island", terrain.BEACH: "wythers:tropical_beach",
    terrain.VOLCANIC: "wythers:tropical_volcano", terrain.TOWN: "wythers:tropical_island",
    terrain.JUNGLE: "wythers:tropical_rainforest",
}


def biome_table() -> dict:
    table = dict(VANILLA_BIOMES)
    if CATALOG.exists():
        known = set(json.loads(CATALOG.read_text()).get("#biomes", {}).get("ids", []))
        for zone, name in TROPICAL.items():
            if name in known:
                table[zone] = name
    return table


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "build/world/Alola"))
    ap.add_argument("--preview", default=str(ROOT / "build/alola-map.png"))
    ap.add_argument("--terrain-only", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    c = Canvas(alola_map.X0, alola_map.Z0, alola_map.SIZE, alola_map.SIZE)
    t = terrain.Terrain(c)
    alola_map.build(t)
    t.compute()
    terrain.apply_surface(t, biome_table())
    print(f"terrain: {time.time() - t0:.1f}s")
    if not args.terrain_only:
        from . import decorate
        decorate.run(c, t)
        print(f"decorated: {time.time() - t0:.1f}s")
    preview.render(c, Path(args.preview))
    print(f"preview: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
