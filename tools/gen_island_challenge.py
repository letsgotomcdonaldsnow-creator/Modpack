#!/usr/bin/env python3
"""Generate the Island Challenge advancement tab and its reward functions.

Writes alola/data/alola/advancement/island_challenge/*.json and
alola/data/alola/function/rewards/*.mcfunction. Edit the tables below and
re-run:  python tools/gen_island_challenge.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "alola" / "data" / "alola"
ADV = DATA / "advancement" / "island_challenge"
FUN = DATA / "function" / "rewards"
NS = "alola:island_challenge"

# Item ids of the Z-Ring and Z-Crystals added by Cobblemon: Mega Showdown.
Z_RING = "mega_showdown:z-ring"
Z = "mega_showdown:{}_z"


def mon(species: str, *aspects: str) -> dict:
    return {"id": "cobblemon:pokemon_model",
            "components": {"cobblemon:pokemon_item": {"species": f"cobblemon:{species}", "aspects": list(aspects)}}}


def item(item_id: str) -> dict:
    return {"id": item_id}


def catch_type(poke_type: str, count: int) -> dict:
    return {"trigger": "cobblemon:catch_pokemon", "conditions": {"type": poke_type, "count": count}}


def win_battles(count: int) -> dict:
    return {"trigger": "cobblemon:battles_won", "conditions": {"count": count}}


def has_advancements(*names: str) -> dict:
    return {"trigger": "minecraft:tick", "conditions": {"player": [{
        "condition": "minecraft:entity_properties", "entity": "this",
        "predicate": {"type_specific": {"type": "minecraft:player",
                                        "advancements": {f"{NS}/{n}": True for n in names}}}}]}}


def say(color: str, *parts: str) -> str:
    text = [{"text": "[Island Challenge] ", "color": "gold", "bold": True}]
    text += [{"text": p, "color": color, "bold": False} for p in parts]
    return f"tellraw @s {json.dumps(text, ensure_ascii=False)}"


# name, parent, icon, title, description, frame, criteria, gifts, message
STEPS = [
    ("root", None, item("cobblemon:poke_ball"), "Alola!",
     "Welcome to the Alola region: four tropical islands and a challenge to become its first Champion",
     "task", {"arrive": {"trigger": "minecraft:tick"}}, [],
     "Alola! Choose your partner Pokémon, then take on the island trials. Press L to follow your progress."),
    ("partner", "root", mon("rowlet"), "Choose Your Partner",
     "Pick Rowlet, Litten or Popplio as your first Pokémon",
     "task", {"starter": {"trigger": "cobblemon:pick_starter"}}, ["cobblemon:poke_ball 10", "cobblemon:potion 5"],
     "Every trainer in Alola begins with a partner. Catch a few more friends before the festival at Iki Town!"),
    ("festival", "partner", item(Z_RING), "The Festival at Iki Town",
     "Win your first Pokémon battle to earn a Z-Ring from Kahuna Hala",
     "goal", {"win": win_battles(1)}, [Z_RING, "cobblemon:great_ball 5"],
     "Kahuna Hala hands you a Z-Ring. Put a Z-Crystal on your Pokémon to unleash Z-Moves!"),

    # Melemele Island
    ("trial_ilima", "festival", mon("gumshoos"), "Trial of Ilima: Verdant Cavern",
     "Melemele Island: catch 3 Normal-type Pokémon", "task",
     {"catch": catch_type("normal", 3)}, [Z.format("normalium")],
     "Captain Ilima is impressed! You obtained Normalium Z."),
    ("grand_trial_hala", "trial_ilima", mon("crabrawler"), "Grand Trial: Kahuna Hala",
     "Melemele Island: win 10 Pokémon battles", "goal",
     {"win": win_battles(10)}, [Z.format("fightinium"), "cobblemon:great_ball 10"],
     "Kahuna Hala acknowledges your strength! You obtained Fightinium Z. On to Akala Island!"),

    # Akala Island
    ("trial_lana", "grand_trial_hala", mon("wishiwashi"), "Trial of Lana: Brooklet Hill",
     "Akala Island: catch 5 Water-type Pokémon", "task",
     {"catch": catch_type("water", 5)}, [Z.format("waterium")],
     "Captain Lana cheers! You obtained Waterium Z."),
    ("trial_kiawe", "trial_lana", mon("salazzle"), "Trial of Kiawe: Wela Volcano Park",
     "Akala Island: catch 5 Fire-type Pokémon", "task",
     {"catch": catch_type("fire", 5)}, [Z.format("firium")],
     "Captain Kiawe strikes a pose! You obtained Firium Z."),
    ("trial_mallow", "trial_kiawe", mon("lurantis"), "Trial of Mallow: Lush Jungle",
     "Akala Island: catch 5 Grass-type Pokémon", "task",
     {"catch": catch_type("grass", 5)}, [Z.format("grassium")],
     "Captain Mallow shares her Mallow Special! You obtained Grassium Z."),
    ("grand_trial_olivia", "trial_mallow", mon("geodude", "alolan"), "Grand Trial: Kahuna Olivia",
     "Akala Island: win 25 Pokémon battles", "goal",
     {"win": win_battles(25)}, [Z.format("rockium"), "cobblemon:ultra_ball 5"],
     "Kahuna Olivia is floored! You obtained Rockium Z. On to Ula'ula Island!"),

    # Ula'ula Island
    ("trial_sophocles", "grand_trial_olivia", mon("togedemaru"), "Trial of Sophocles: Hokulani Observatory",
     "Ula'ula Island: catch 5 Electric-type Pokémon", "task",
     {"catch": catch_type("electric", 5)}, [Z.format("electrium")],
     "Captain Sophocles' machine approves! You obtained Electrium Z."),
    ("trial_acerola", "trial_sophocles", mon("mimikyu"), "Trial of Acerola: Thrifty Megamart",
     "Ula'ula Island: catch 5 Ghost-type Pokémon", "task",
     {"catch": catch_type("ghost", 5)}, [Z.format("ghostium")],
     "Captain Acerola giggles. You obtained Ghostium Z."),
    ("grand_trial_nanu", "trial_acerola", mon("persian", "alolan"), "Grand Trial: Kahuna Nanu",
     "Ula'ula Island: win 50 Pokémon battles", "goal",
     {"win": win_battles(50)}, [Z.format("darkinium"), "cobblemon:ultra_ball 10"],
     "Kahuna Nanu shrugs... and hands over Darkinium Z. On to Poni Island!"),

    # Poni Island
    ("trial_mina", "grand_trial_nanu", mon("ribombee"), "Trial of Mina: Poni Meadow",
     "Poni Island: catch 5 Fairy-type Pokémon", "task",
     {"catch": catch_type("fairy", 5)}, [Z.format("fairium")],
     "Captain Mina paints you a picture. You obtained Fairium Z."),
    ("trial_vast_poni", "trial_mina", mon("kommoo"), "Vast Poni Canyon",
     "Poni Island: catch 3 Dragon-type Pokémon", "task",
     {"catch": catch_type("dragon", 3)}, [Z.format("dragonium")],
     "The Totem Pokémon of the canyon falls! You obtained Dragonium Z."),
    ("grand_trial_hapu", "trial_vast_poni", mon("mudsdale"), "Grand Trial: Kahuna Hapu",
     "Poni Island: win 75 Pokémon battles", "goal",
     {"win": win_battles(75)}, [Z.format("groundium"), "cobblemon:ultra_ball 10"],
     "Kahuna Hapu and Mudsdale bow to you. You obtained Groundium Z. The Pokémon League awaits!"),
    ("champion", "grand_trial_hapu", item("cobblemon:master_ball"), "First Champion of Alola",
     "Clear every trial and grand trial, then win 100 Pokémon battles", "challenge",
     {"trials": has_advancements("trial_ilima", "grand_trial_hala", "trial_lana", "trial_kiawe", "trial_mallow",
                                 "grand_trial_olivia", "trial_sophocles", "trial_acerola", "grand_trial_nanu",
                                 "trial_mina", "trial_vast_poni", "grand_trial_hapu"),
      "battles": win_battles(100)},
     ["cobblemon:master_ball", "cobblemon:rare_candy 5"],
     "You are the first Champion of the Alola region! Congratulations!"),

    # Side quests
    ("poke_ride", "partner", mon("mudsdale"), "Poké Ride",
     "Ride one of your Pokémon", "task",
     {"ride": {"trigger": "minecraft:started_riding", "conditions": {"player": [{
         "condition": "minecraft:entity_properties", "entity": "this",
         "predicate": {"vehicle": {"type": "cobblemon:pokemon"}}}]}}}, [], None),
    ("poke_pelago", "partner", item("cobblemon:pasture"), "Poké Pelago",
     "Put a Pokémon to work in a pasture", "task",
     {"pasture": {"trigger": "cobblemon:pasture_use"}}, [], None),
    ("island_scan", "partner", item("cobblemon:ultra_ball"), "Pokédex Completion: 100",
     "Catch 100 Pokémon", "goal",
     {"catch": catch_type("any", 100)}, ["cobblemon:ultra_ball 10"], "Professor Kukui is thrilled with your Pokédex!"),
    ("shiny", "island_scan", item("cobblemon:shiny_stone"), "A Different Color",
     "Catch a shiny Pokémon", "challenge",
     {"shiny": {"trigger": "cobblemon:catch_shiny_pokemon", "conditions": {"count": 1}}}, [], None),
    ("alolan_variants", "island_scan", mon("vulpix", "alolan"), "Alolan Variants",
     "Catch or evolve all ten Alolan forms: Rattata, Raichu, Sandshrew, Vulpix, Diglett, Meowth, "
     "Geodude, Grimer, Exeggutor and Marowak", "challenge",
     {s: {"trigger": "cobblemon:aspects_collected",
          "conditions": {"species": f"cobblemon:{s}", "aspects": ["alolan"]}}
      for s in ("rattata", "raichu", "sandshrew", "vulpix", "diglett", "meowth", "geodude", "grimer",
                "exeggutor", "marowak")},
     ["cobblemon:rare_candy 3"], "Regional variants! The Alola region's own spin on familiar Pokémon."),
    ("ultra_space", "island_scan", item("minecraft:end_crystal"), "Beyond the Ultra Wormhole",
     "Travel to the End, Alola's Ultra Space, where the Ultra Beasts come from", "goal",
     {"end": {"trigger": "minecraft:changed_dimension", "conditions": {"to": "minecraft:the_end"}}}, [], None),
]


def main() -> None:
    for d in (ADV, FUN):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    names = {s[0] for s in STEPS}
    for name, parent, icon, title, desc, frame, criteria, gifts, message in STEPS:
        assert parent is None or parent in names, parent
        adv = {}
        if parent:
            adv["parent"] = f"{NS}/{parent}"
        display = {"icon": icon, "title": {"text": title}, "description": {"text": desc}, "frame": frame,
                   "show_toast": True, "announce_to_chat": parent is not None, "hidden": False}
        if parent is None:
            display["background"] = "minecraft:textures/block/sand.png"
        adv["display"] = display
        adv["criteria"] = criteria
        adv["requirements"] = [[k] for k in criteria]
        lines = []
        if message:
            lines.append(say("yellow" if frame == "task" else "aqua", message))
        for g in gifts:
            lines.append(f"give @s {g}")
        if lines:
            (FUN / f"{name}.mcfunction").write_text("\n".join(lines) + "\n", encoding="utf-8")
            adv["rewards"] = {"function": f"alola:rewards/{name}"}
        adv["sends_telemetry_event"] = False
        (ADV / f"{name}.json").write_text(json.dumps(adv, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(STEPS)} advancements")


if __name__ == "__main__":
    main()
