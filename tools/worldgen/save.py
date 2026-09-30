"""Write the world save: regions, level.dat, icon and the one-time setup datapack."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import buildings
from .canvas import Canvas, write_level_dat

ROOT = Path(__file__).resolve().parents[2]
SPAWN = (-520, 68, -460)   # in front of the player's house on Melemele Island


def write_setup_pack(world: Path) -> None:
    pack = world / "datapacks" / "alola_region"
    if pack.exists():
        shutil.rmtree(pack)
    fn = pack / "data" / "alola_region" / "function"
    fn.mkdir(parents=True)
    (pack / "pack.mcmeta").write_text(json.dumps({"pack": {"pack_format": 48,
                                                           "description": "Alola region: first-load setup"}}, indent=2))
    tags = pack / "data" / "minecraft" / "tags" / "function"
    tags.mkdir(parents=True)
    (tags / "load.json").write_text(json.dumps({"values": ["alola_region:load"]}))
    chunks = sorted({(x >> 4, z >> 4) for x, y, z, cmd in buildings.SETUP})
    (fn / "load.mcfunction").write_text(
        "scoreboard objectives add alola_setup dummy\n"
        "execute unless score #done alola_setup matches 1 run function alola_region:setup\n")
    (fn / "setup.mcfunction").write_text(
        "# Load every chunk that gets a Pokémon Center machine or a trainer, then place them a moment later.\n"
        + "".join(f"forceload add {cx * 16} {cz * 16}\n" for cx, cz in chunks)
        + "schedule function alola_region:spawn 60t\n")
    # Cobblemon commands are macro lines ($...$(e)) so they are parsed when they run, after Cobblemon has
    # loaded its NPC classes and species, not when the datapack is first read.
    def line(cmd: str) -> str:
        if cmd.startswith(("spawnnpcat", "spawnpokemonat")):
            return f"${cmd}$(e)\n"
        return f"{cmd}\n"
    (fn / "spawn_all.mcfunction").write_text("".join(line(cmd) for x, y, z, cmd in buildings.SETUP))
    (fn / "spawn.mcfunction").write_text(
        'function alola_region:spawn_all {e:""}\n'
        + "scoreboard players set #done alola_setup 1\n"
        + 'tellraw @a [{"text":"[Alola] ","color":"gold"},{"text":"The Alola region is ready. Alola!","color":"yellow"}]\n'
        + "schedule function alola_region:release 200t\n")
    (fn / "release.mcfunction").write_text("".join(f"forceload remove {cx * 16} {cz * 16}\n" for cx, cz in chunks))
    print(f"  setup datapack: {len(buildings.SETUP)} commands over {len(chunks)} chunks")


def save_world(c: Canvas, out: Path, name: str = "Alola") -> None:
    if out.exists():
        shutil.rmtree(out)
    n = c.save_regions(out / "region", log=lambda *_: None)
    write_level_dat(out / "level.dat", name, SPAWN)
    icon = ROOT / "icon.png"
    if icon.exists():
        shutil.copy2(icon, out / "icon.png")
    write_setup_pack(out)
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"  world: {n} chunks, {size / 1e6:.1f} MB -> {out}")


def used_states(c: Canvas) -> list[str]:
    return sorted(set(c.states[1:]))
