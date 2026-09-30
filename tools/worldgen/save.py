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
        + "execute store result score #npcs alola_setup if entity @e[type=cobblemon:npc]\n"
        + "scoreboard players set #done alola_setup 1\n"
        + 'tellraw @a [{"text":"[Alola] ","color":"gold"},{"text":"The Alola region is ready. Alola!","color":"yellow"}]\n'
        + "schedule function alola_region:release 200t\n")
    (fn / "release.mcfunction").write_text("".join(f"forceload remove {cx * 16} {cz * 16}\n" for cx, cz in chunks))
    print(f"  setup datapack: {len(buildings.SETUP)} commands over {len(chunks)} chunks")


def defer_entity_rendered(c: Canvas) -> int:
    """Blocks drawn only by a block entity renderer (the catalog's #entity_rendered: flags, clocks, sign posts,
    animated dolls...) need their mod's block entity, which the region writer cannot make. Leave air in the
    save and let the setup function place them with /setblock, which creates the block entity."""
    import numpy as np
    from . import furn
    from .canvas import MIN_Y, parse_state
    ids = set(furn.catalog().get("#entity_rendered", {}).get("ids", []))
    sids = [i for i, st in enumerate(c.states) if i and parse_state(st)[0] in ids]
    if not sids:
        return 0
    air = c.sid("minecraft:air")
    n = 0
    for (cx, cz, sy), sec in c.sections.items():
        hit = np.isin(sec, sids)
        if not hit.any():
            continue
        for ly, lz, lx in zip(*np.nonzero(hit)):
            x, y, z = cx * 16 + int(lx), MIN_Y + sy * 16 + int(ly), cz * 16 + int(lz)
            buildings.SETUP.append((x, y, z, f"setblock {x} {y} {z} {c.states[sec[ly, lz, lx]]}"))
            sec[ly, lz, lx] = air
            n += 1
    return n


def save_world(c: Canvas, out: Path, name: str = "Alola") -> None:
    if out.exists():
        shutil.rmtree(out)
    deferred = defer_entity_rendered(c)
    if deferred:
        print(f"  {deferred} block-entity-rendered blocks will be placed in game")
    n = c.save_regions(out / "region", log=lambda *_: None)
    write_level_dat(out / "level.dat", name, SPAWN)
    icon = ROOT / "icon.png"
    if icon.exists():
        shutil.copy2(icon, out / "icon.png")
    write_setup_pack(out)
    from . import multiplayer
    multiplayer.write_waystones(out)
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"  world: {n} chunks, {size / 1e6:.1f} MB -> {out}")


def used_states(c: Canvas) -> list[str]:
    return sorted(set(c.states[1:]))
