#!/usr/bin/env python3
"""Generate the Alola spawn boosts in alola/data/alola/spawn_pool_world/.

For every Alola native (Generation 7 species and Alolan forms that Cobblemon
implements), copy Cobblemon's own spawn entries (so levels, buckets, spawn
positions, times and fluid rules stay correct) and re-point the copies at the
biomes where that Pokémon lives in Sun & Moon: tropical islands, beaches,
jungles, volcanoes and warm seas. Weights are doubled so Alola natives are
the everyday sight on the islands, while the rest of the Pokédex still spawns
as normal.

Run it again after changing the Cobblemon pin in modlist.toml:

    python tools/gen_alola_spawns.py 1.7.3
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "alola" / "data" / "alola" / "spawn_pool_world"
GITLAB = "https://gitlab.com/api/v4/projects/cable-mc%2Fcobblemon/repository"
DATA = "common/src/main/resources/data/cobblemon/spawn_pool_world"

TROPICS = "#cobblemon:is_tropical_island"
BEACH = "#cobblemon:is_beach"
JUNGLE = "#cobblemon:is_jungle"
VOLCANO = "#cobblemon:is_volcanic"
WARM_SEA = ["#cobblemon:is_warm_ocean", "#cobblemon:is_lukewarm_ocean"]

# species (as Cobblemon writes it in spawn files) -> (island, habitat biomes)
ALOLA = {
    # Melemele Island: Route 1, Ten Carat Hill, Melemele Meadow
    "pikipek": ("Melemele", [TROPICS, JUNGLE]),
    "trumbeak": ("Melemele", [TROPICS, JUNGLE]),
    "toucannon": ("Melemele", [TROPICS, JUNGLE]),
    "yungoos": ("Melemele", [TROPICS, BEACH]),
    "gumshoos": ("Melemele", [TROPICS, BEACH]),
    "rattata alolan": ("Melemele", [TROPICS, BEACH]),
    "raticate alolan": ("Melemele", [TROPICS, BEACH]),
    "meowth alolan": ("Melemele", [TROPICS, BEACH]),
    "persian alolan": ("Melemele", [TROPICS, BEACH]),
    "cutiefly": ("Melemele", [TROPICS, JUNGLE]),
    "ribombee": ("Melemele", [TROPICS, JUNGLE]),
    "crabrawler": ("Melemele", [BEACH, TROPICS]),
    "grimer alolan": ("Melemele", [TROPICS, BEACH]),
    "muk alolan": ("Melemele", [TROPICS, BEACH]),
    # Akala Island: Lush Jungle, Wela Volcano Park, Brooklet Hill, Paniola Ranch
    "bounsweet": ("Akala", [JUNGLE, TROPICS]),
    "steenee": ("Akala", [JUNGLE, TROPICS]),
    "tsareena": ("Akala", [JUNGLE, TROPICS]),
    "fomantis": ("Akala", [JUNGLE, TROPICS]),
    "lurantis": ("Akala", [JUNGLE, TROPICS]),
    "morelull": ("Akala", [JUNGLE, TROPICS]),
    "shiinotic": ("Akala", [JUNGLE, TROPICS]),
    "comfey": ("Akala", [JUNGLE, TROPICS]),
    "dewpider": ("Akala", [JUNGLE, TROPICS]),
    "araquanid": ("Akala", [JUNGLE, TROPICS]),
    "salandit": ("Akala", [VOLCANO]),
    "salazzle": ("Akala", [VOLCANO]),
    "marowak alolan": ("Akala", [VOLCANO]),
    "mudbray": ("Akala", [TROPICS]),
    "mudsdale": ("Akala", [TROPICS]),
    "stufful": ("Akala", [TROPICS, JUNGLE]),
    "bewear": ("Akala", [TROPICS, JUNGLE]),
    "wishiwashi": ("Akala", [*WARM_SEA, TROPICS]),
    "mareanie": ("Akala", [*WARM_SEA, BEACH]),
    "toxapex": ("Akala", [*WARM_SEA, BEACH]),
    "wimpod": ("Akala", [BEACH, TROPICS]),
    "golisopod": ("Akala", [BEACH, TROPICS]),
    "sandygast": ("Akala", [BEACH, TROPICS]),
    "palossand": ("Akala", [BEACH, TROPICS]),
    "pyukumuku": ("Akala", [BEACH, *WARM_SEA]),
    # Ula'ula Island: Blush Mountain, Mount Hokulani, Route 11
    "geodude alolan": ("Ula'ula", [VOLCANO, TROPICS]),
    "graveler alolan": ("Ula'ula", [VOLCANO, TROPICS]),
    "golem alolan": ("Ula'ula", [VOLCANO, TROPICS]),
    "turtonator": ("Ula'ula", [VOLCANO]),
    "togedemaru": ("Ula'ula", [TROPICS]),
    "komala": ("Ula'ula", [TROPICS, JUNGLE]),
    "mimikyu": ("Ula'ula", [TROPICS, JUNGLE]),
    # Poni Island: Seafolk Village, Poni Wilds, Vast Poni Canyon
    "bruxish": ("Poni", [*WARM_SEA, TROPICS]),
    "dhelmise": ("Poni", [*WARM_SEA]),
    "jangmoo": ("Poni", [VOLCANO, TROPICS]),
    "hakamoo": ("Poni", [VOLCANO, TROPICS]),
    "kommoo": ("Poni", [VOLCANO]),
    "exeggutor alolan": ("Poni", [BEACH, TROPICS]),
}

WEIGHT_FACTOR = 2.0


def gitlab_json(path: str, ref: str):
    url = f"{GITLAB}/files/{urllib.parse.quote(path, safe='')}/raw?ref={ref}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read())


def gitlab_tree(path: str, ref: str) -> list[str]:
    names, page = [], 1
    while True:
        url = f"{GITLAB}/tree?ref={ref}&path={urllib.parse.quote(path)}&per_page=100&page={page}"
        with urllib.request.urlopen(url, timeout=60) as resp:
            batch = json.loads(resp.read())
        if not batch:
            return names
        names += [b["name"] for b in batch]
        page += 1


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else "1.7.3"
    files = gitlab_tree(DATA, ref)
    by_species: dict[str, str] = {}
    for name in files:
        stem = name.removesuffix(".json").split("_", 1)[-1]
        by_species.setdefault(stem, name)

    per_island: dict[str, list[dict]] = {}
    missing = []
    for species, (island, habitat) in ALOLA.items():
        base = species.split()[0]
        fname = by_species.get(base)
        if not fname:
            missing.append(species)
            continue
        spawns = gitlab_json(f"{DATA}/{fname}", ref).get("spawns", [])
        matched = [s for s in spawns if s.get("pokemon") == species]
        if not matched:
            missing.append(species)
            continue
        for s in matched:
            s = json.loads(json.dumps(s))
            s["id"] = f"alola-{s['id']}"
            s["weight"] = round(float(s.get("weight", 1.0)) * WEIGHT_FACTOR, 3)
            cond = s.setdefault("condition", {})
            cond["biomes"] = habitat
            anti = s.get("anticondition", {})
            if "biomes" in anti:
                anti["biomes"] = [b for b in anti["biomes"] if b not in habitat]
                if not anti["biomes"]:
                    del anti["biomes"]
                if not anti:
                    s.pop("anticondition")
            per_island.setdefault(island, []).append(s)

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("alola_*.json"):
        old.unlink()
    for island, spawns in per_island.items():
        slug = island.lower().replace("'", "")
        data = {"enabled": True, "neededInstalledMods": [], "neededUninstalledMods": [], "spawns": spawns}
        (OUT / f"alola_{slug}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"{island}: {len(spawns)} spawn entries")
    if missing:
        print("Not spawnable in this Cobblemon version (skipped):", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
