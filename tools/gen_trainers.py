#!/usr/bin/env python3
"""Generate Cobblemon NPC trainer classes and dialogues for the Alola region.

Writes alola/data/alola/npcs/*.json and alola/data/alola/dialogues/*.json.
Teams follow Pokémon Sun & Moon. The world's setup function spawns each
trainer at its spot with `spawnnpcat`.

    python tools/gen_trainers.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "alola" / "data" / "alola"


def mon(spec: str, level: int, **extra) -> str:
    parts = [spec, f"level={level}"] + [f"{k}={v}" for k, v in extra.items()]
    return " ".join(parts)


# id: (display name, title shown in dialogue, intro line, win line, skill, team)
TRAINERS = {
    # ---------------------------------------------------------- captains + totems
    "ilima": ("Captain Ilima", "Trial Captain", "Welcome to Verdant Cavern! Defeat the Totem Pokémon lurking here and you clear my trial!",
              "Normalium Z suits you! The Island Challenge continues!", 2,
              [mon("yungoos", 10), mon("smeargle", 11), mon("gumshoos", 12, pokeball="ultra_ball")]),
    "lana": ("Captain Lana", "Trial Captain", "The water at Brooklet Hill is splashing... something big is fishing for challengers!",
             "You did it! Here, take Waterium Z.", 3,
             [mon("chinchou", 18), mon("araquanid", 20), mon("wishiwashi", 20)]),
    "kiawe": ("Captain Kiawe", "Trial Captain", "Wela Volcano Park burns with the fire of my trial! Show me your blazing spirit!",
              "Magnificent! Firium Z is yours.", 3,
              [mon("marowak alolan", 22), mon("salandit", 21), mon("salazzle", 22)]),
    "mallow": ("Captain Mallow", "Trial Captain", "Welcome to the Lush Jungle! Gather the ingredients... oh, and watch out for the Totem!",
               "Tasty battle! Take Grassium Z.", 3,
               [mon("trumbeak", 23), mon("shiinotic", 23), mon("lurantis", 24)]),
    "sophocles": ("Captain Sophocles", "Trial Captain", "Hokulani Observatory's trial is powered by electricity. Let's see if you short-circuit!",
                  "Nice calculations. Electrium Z is yours.", 3,
                  [mon("magnemite", 28), mon("togedemaru", 29), mon("charjabug", 28), mon("vikavolt", 30)]),
    "acerola": ("Captain Acerola", "Trial Captain", "Hee hee... the Thrifty Megamart is closed, but something's still shopping inside...",
                "You're brave! Ghostium Z, just for you.", 3,
                [mon("sableye", 32), mon("drifblim", 32), mon("mimikyu", 33)]),
    "mina": ("Captain Mina", "Trial Captain", "Poni Meadow is my canvas. Paint a victory against my Fairy-types!",
             "Colorful! Take Fairium Z.", 4,
             [mon("klefki", 51), mon("granbull", 51), mon("shiinotic", 51), mon("wigglytuff", 51), mon("ribombee", 51)]),
    "totem_kommoo": ("Totem Kommo-o", "Vast Poni Canyon", "Roarrrr! The Totem Pokémon of Vast Poni Canyon blocks the way!",
                     "The Totem accepts you. Dragonium Z glints on the altar.", 4,
                     [mon("kommoo", 45, pokeball="ultra_ball")]),
    # ---------------------------------------------------------- kahunas (grand trials)
    "hala": ("Kahuna Hala", "Melemele Island Kahuna", "Ho ho! Your grand trial begins now! Show Tapu Koko your strength!",
             "What a battle! You've earned the Fightinium Z.", 3,
             [mon("mankey", 14), mon("makuhita", 14), mon("crabrawler", 15)]),
    "olivia": ("Kahuna Olivia", "Akala Island Kahuna", "My shop can wait. Rock-types are as hard as diamonds!",
               "Brilliant! Rockium Z sparkles for you.", 4,
               [mon("nosepass", 26), mon("boldore", 26), mon("lycanroc", 27)]),
    "nanu": ("Kahuna Nanu", "Ula'ula Island Kahuna", "...Fine. Let's get this over with. A grand trial.",
             "You win. Here, take the Darkinium Z.", 4,
             [mon("sableye", 38), mon("krokorok", 38), mon("persian alolan", 39)]),
    "hapu": ("Kahuna Hapu", "Poni Island Kahuna", "I'm Poni Island's kahuna now! Mudsdale and I will not go easy!",
             "You are strong. Groundium Z is yours.", 5,
             [mon("dugtrio alolan", 47), mon("gastrodon", 47), mon("flygon", 47), mon("mudsdale", 48)]),
    # ---------------------------------------------------------- pokémon league
    "e4_hala": ("Elite Four Hala", "Pokémon League", "The Elite Four begins with me! Let's rumble!",
                "Ho ho! Proceed, challenger!", 5,
                [mon("hariyama", 54), mon("primeape", 54), mon("bewear", 54), mon("poliwrath", 54), mon("crabominable", 55)]),
    "e4_olivia": ("Elite Four Olivia", "Pokémon League", "Rock-hard defense awaits you in my room!",
                  "You shine brighter than any gem.", 5,
                  [mon("relicanth", 54), mon("carbink", 54), mon("golem alolan", 54), mon("probopass", 54), mon("lycanroc", 55)]),
    "e4_acerola": ("Elite Four Acerola", "Pokémon League", "Welcome to my spooky room! Let's play!",
                   "Aww, you won! Good luck with the next one!", 5,
                   [mon("sableye", 54), mon("drifblim", 54), mon("dhelmise", 54), mon("froslass", 54), mon("palossand", 55)]),
    "e4_kahili": ("Elite Four Kahili", "Pokémon League", "Fore! Let's see how far your team can fly!",
                  "A hole in one for you.", 5,
                  [mon("skarmory", 54), mon("crobat", 54), mon("oricorio", 54), mon("mandibuzz", 54), mon("toucannon", 55)]),
    "champion_kukui": ("Professor Kukui", "Pokémon League Founder", "Woo! I've been waiting for this! The first Champion of Alola will be decided right now!",
                       "Woo! You're the first Champion of Alola!", 5,
                       [mon("lycanroc", 57), mon("ninetales alolan", 56), mon("braviary", 56), mon("magnezone", 56),
                        mon("snorlax", 56), mon("incineroar", 58)]),
    # ---------------------------------------------------------- rivals, skull, aether
    "hau": ("Hau", "Your rival", "Alola! Let's have a battle! Malasadas are on me afterwards!",
            "Whoa, you're so strong! Let's get malasadas!", 2,
            [mon("pichu", 12), mon("pikipek", 11), mon("rowlet", 13)]),
    "gladion": ("Gladion", "Team Skull enforcer", "...You. Battle me. Now.",
                "...Tch. You're strong.", 5,
                [mon("golbat", 43), mon("zoroark", 43), mon("lucario", 43), mon("silvally", 45)]),
    "guzma": ("Guzma", "Boss of Team Skull", "Guzma is the one who beats you down and keeps beating you down!",
              "...Guzma lost again?!", 5,
              [mon("golisopod", 37), mon("ariados", 36), mon("masquerain", 36)]),
    "plumeria": ("Plumeria", "Team Skull admin", "You've been messing with my Grunts. Time to pay up.",
                 "Hmph. Not bad.", 4,
                 [mon("golbat", 37), mon("salazzle", 38)]),
    "skull_grunt": ("Team Skull Grunt", "Team Skull", "Yo yo! You're in Po Town now, fool!",
                    "Man, whatevs...", 1,
                    [mon("zubat", 30), mon("salandit", 30), mon("mareanie", 31)]),
    "lusamine": ("Lusamine", "Aether Foundation President", "Welcome to Aether Paradise, my beautiful Pokémon sanctuary.",
                 "How... how could my beautiful Pokémon lose?", 5,
                 [mon("clefable", 50), mon("lilligant", 50), mon("mismagius", 50), mon("milotic", 50), mon("bewear", 51)]),
    # ---------------------------------------------------------- battle tree legends
    "red": ("Red", "Battle Tree", "...", "...", 5,
            [mon("pikachu", 50), mon("lapras", 50), mon("snorlax", 50), mon("venusaur", 50), mon("charizard", 50), mon("blastoise", 50)]),
    "blue": ("Blue", "Battle Tree", "Smell ya later! Just kidding, let's battle!",
             "Hah! You're not bad at all.", 5,
             [mon("pidgeot", 50), mon("alakazam", 50), mon("rhyperior", 50), mon("exeggutor", 50), mon("gyarados", 50), mon("arcanine", 50)]),
}

# Trainer id -> Island Challenge advancement to grant on a win (via battle_victory callback).
ADVANCEMENT_FOR = {
    "ilima": "trial_ilima", "lana": "trial_lana", "kiawe": "trial_kiawe", "mallow": "trial_mallow",
    "sophocles": "trial_sophocles", "acerola": "trial_acerola", "mina": "trial_mina", "totem_kommoo": "trial_vast_poni",
    "hala": "grand_trial_hala", "olivia": "grand_trial_olivia", "nanu": "grand_trial_nanu", "hapu": "grand_trial_hapu",
    "champion_kukui": "champion",
}


def trainer_class(tid: str) -> dict:
    name, title, intro, win, skill, team = TRAINERS[tid]
    return {
        "resourceIdentifier": "cobblemon:npc",
        "hitbox": "player",
        "names": [name],
        "interaction": {"type": "dialogue", "dialogue": f"alola:{tid}"},
        "battleConfiguration": {"canChallenge": True},
        "canDespawn": False,
        "isMovable": False,
        "isInvulnerable": True,
        "isLeashable": False,
        "allowProjectileHits": False,
        "hideNameTag": False,
        "skill": skill,
        "autoHealParty": True,
        "randomizePartyOrder": False,
        "party": {"type": "simple", "pokemon": team},
        "config": config_for(tid),
    }


def config_for(tid: str) -> list[dict]:
    """Cobblemon's own battle_victory callback runs `player_win_command` when a player beats this NPC."""
    adv = ADVANCEMENT_FOR.get(tid)
    cmd = f"advancement grant {{{{player}}}} only alola:island_challenge/{adv}" if adv else ""
    return [
        {"variableName": "player_win_command", "displayName": "Win command",
         "description": "Command run when a player beats this trainer.", "type": "TEXT", "defaultValue": cmd},
        {"variableName": "challenge_cooldown", "displayName": "Cooldown",
         "description": "Ticks before the same player can challenge again.", "type": "NUMBER", "defaultValue": "0"},
    ]


def speakers() -> dict:
    return {
        "npc": {"name": {"type": "expression", "expression": "q.npc.name"}, "face": "q.npc.face(false);"},
        "player": {"name": {"type": "expression", "expression": "q.player.username"}, "face": "q.player.face();"},
    }


def trainer_dialogue(tid: str) -> dict:
    name, title, intro, win, skill, team = TRAINERS[tid]
    return {
        "initializationAction": "(q.npc.is_in_battle_with(q.player) || !q.npc.is_doing_activity('minecraft:idle', 'cobblemon:battling')) ? q.dialogue.close()",
        "speakers": speakers(),
        "pages": [
            {"id": "intro", "speaker": "npc", "lines": [title + ": " + intro],
             "input": {"type": "option", "vertical": False, "options": [
                 {"text": "Battle!", "value": "battle",
                  "action": ["q.dialogue.close();", "q.npc.start_battle(q.player);"]},
                 {"text": "Not yet", "value": "cancel", "action": "q.dialogue.set_page('later');"},
             ]}},
            {"id": "later", "speaker": "npc", "lines": ["Come back when you're ready!"], "input": "q.dialogue.close();"},
        ],
    }


def nurse_class() -> dict:
    return {
        "resourceIdentifier": "cobblemon:npc", "hitbox": "player", "names": ["Nurse"],
        "interaction": {"type": "dialogue", "dialogue": "alola:nurse"},
        "canDespawn": False, "isMovable": False, "isInvulnerable": True, "isLeashable": False,
        "allowProjectileHits": False,
    }


def nurse_dialogue() -> dict:
    return {
        "initializationAction": [
            "c.npc.set_chatting();",
            "v.healer = c.npc.find_nearby_block('cobblemon:healing_machine');",
            "v.has_healer = v.healer != 0;",
            "v.full_health = c.player.is_party_at_full_health();",
            "v.has_charge = v.has_healer == true && v.full_health == false && q.player.can_heal_at_healer(v.healer) == true;",
            "v.landing_page = !v.has_healer ? 'no_healer' : (v.full_health ? 'full_health' : (v.has_charge ? 'has_charge' : 'no_charge'));",
        ],
        "speakers": speakers(),
        "pages": [
            {"id": "greeting", "speaker": "npc", "lines": ["Alola! Welcome to the Pokémon Center."],
             "input": "q.dialogue.set_page(v.landing_page);"},
            {"id": "no_healer", "speaker": "npc", "lines": ["Oh dear, the healing machine is missing..."], "input": "q.dialogue.close();"},
            {"id": "full_health", "speaker": "npc", "lines": ["Your Pokémon are already in perfect health! We hope to see you again!"],
             "input": "q.dialogue.close();"},
            {"id": "no_charge", "speaker": "npc", "lines": ["The machine is recharging. Please come back a little later!"],
             "input": "q.dialogue.close();"},
            {"id": "has_charge", "speaker": "npc", "lines": ["Shall I restore your Pokémon to full health?"],
             "input": {"type": "option", "vertical": False, "options": [
                 {"text": "Yes, please", "value": "yes", "action": [
                     "v.callback_dialogue = 'alola:nurse_healed';",
                     "c.npc.run_action_effect('npc_heal_player_pokemon');",
                     "q.dialogue.close();"]},
                 {"text": "No thanks", "value": "no", "action": "q.dialogue.set_page('bye');"}]}},
            {"id": "bye", "speaker": "npc", "lines": ["We hope to see you again!"], "input": "q.dialogue.close();"},
        ],
    }


def nurse_healed() -> dict:
    return {"speakers": speakers(), "pages": [
        {"id": "healed", "speaker": "npc", "lines": ["Your Pokémon have been restored to full health. We hope to see you again!"],
         "input": "q.dialogue.close();"}]}


def main() -> None:
    for sub in ("npcs", "dialogues"):
        d = DATA / sub
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    for tid in TRAINERS:
        (DATA / "npcs" / f"{tid}.json").write_text(json.dumps(trainer_class(tid), indent=2, ensure_ascii=False) + "\n")
        (DATA / "dialogues" / f"{tid}.json").write_text(json.dumps(trainer_dialogue(tid), indent=2, ensure_ascii=False) + "\n")
    (DATA / "npcs" / "nurse.json").write_text(json.dumps(nurse_class(), indent=2) + "\n")
    (DATA / "dialogues" / "nurse.json").write_text(json.dumps(nurse_dialogue(), indent=2, ensure_ascii=False) + "\n")
    (DATA / "dialogues" / "nurse_healed.json").write_text(json.dumps(nurse_healed(), indent=2, ensure_ascii=False) + "\n")
    (DATA / "trainer_species.json").unlink(missing_ok=True)
    print(f"Wrote {len(TRAINERS)} trainers + nurse")


if __name__ == "__main__":
    main()
