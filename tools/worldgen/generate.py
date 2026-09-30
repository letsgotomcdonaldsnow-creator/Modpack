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


def check_states(c) -> list[str]:
    from .canvas import parse_state
    cat = json.loads(CATALOG.read_text()) if CATALOG.exists() else {}
    if "minecraft:stone" not in cat:
        print("catalog has no vanilla report yet; skipping the block check")
        return []
    problems = []
    for state in c.states[1:]:
        name, props = parse_state(state)
        if name not in cat:
            problems.append(f"unknown block {state}")
            continue
        info = cat[name]
        for k, v in props.items():
            if info and k in info and info[k] == ["true"] and v == "false":
                continue   # multipart blockstates only mention the 'true' side of booleans
            if info and (k not in info or (info[k] and v not in info[k])):
                problems.append(f"{state}: property {k}={v} not valid (has {info.get(k, 'no such property')})")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "build/world/Alola"))
    ap.add_argument("--preview", default=str(ROOT / "build/alola-map.png"))
    ap.add_argument("--terrain-only", action="store_true")
    ap.add_argument("--crops", nargs="*", default=[])
    ap.add_argument("--crop-radius", type=int, default=130)
    ap.add_argument("--zoom", type=int, default=1, help="upscale factor for the crop images")
    ap.add_argument("--save", action="store_true", help="write the world save")
    ap.add_argument("--check", action="store_true", help="fail if a block or property is not in the catalog")
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
    from . import lab
    lab_views = lab.build(c)
    if args.save:
        from . import save
        save.save_world(c, Path(args.out))
        Path(args.out).parent.joinpath("world-blocks.json").write_text(json.dumps(save.used_states(c), indent=0))
        from . import tour
        tour.write(c, Path(args.out).parent / "tour" / "alola_tour", lab_views)
        print(f"saved: {time.time() - t0:.1f}s")
    if args.check:
        problems = check_states(c)
        for prob in problems[:100]:
            print("WORLD-BLOCK-ERROR:", prob)
        if problems:
            print(f"{len(problems)} block state problems")
            return 1
        print("All block states exist in the pack.")
    preview.render(c, Path(args.preview))
    if args.crops:
        from . import alola_map as am
        for name in args.crops:
            x, z, _ = am.TOWNS[name]
            r = args.crop_radius
            out = Path(args.preview).with_name("crop-" + name.lower().replace(" ", "-").replace("'", "") + ".png")
            preview.render(c, out, crop=(x - r, z - r, x + r, z + r), zoom=args.zoom)
    print(f"preview: {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
