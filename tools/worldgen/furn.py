"""Furniture and decoration picker.

Each piece lists decoration-mod blocks in order of preference, then a vanilla
fallback. At generation time the first id that exists in block_catalog.json
(built by CI from every jar in the pack) is used, with only the properties
that block really has, so a missing mod never breaks the world.
"""
from __future__ import annotations

import json
from pathlib import Path

from .canvas import parse_state

CATALOG_PATH = Path(__file__).with_name("block_catalog.json")
_catalog: dict | None = None


def catalog() -> dict:
    global _catalog
    if _catalog is None:
        _catalog = json.loads(CATALOG_PATH.read_text()) if CATALOG_PATH.exists() else {}
    return _catalog


def exists(name: str) -> bool:
    cat = catalog()
    if not cat:
        return name.startswith("minecraft:")
    return name in cat


def fit(state: str) -> str:
    """Drop properties/values the block does not have (keeps the world loadable)."""
    name, props = parse_state(state)
    info = catalog().get(name)
    if info is None:
        return state
    if not info:  # blockstate file lists no variants: keep what we asked for (unknown keys are ignored on load)
        return state
    kept = {k: v for k, v in props.items() if k in info and (not info[k] or v in info[k])}
    body = ",".join(f"{k}={v}" for k, v in kept.items())
    return f"{name}[{body}]" if body else name


# piece: candidate states (first existing wins). Use {facing} for the direction the piece faces.
PIECES: dict[str, list[str]] = {
    "chair": ["mcwfurnitures:oak_chair[facing={facing}]", "handcrafted:oak_chair[facing={facing}]",
              "another_furniture:oak_chair[facing={facing}]", "minecraft:oak_stairs[facing={back}]"],
    "chair_modern": ["mcwfurnitures:oak_modern_chair[facing={facing}]", "mcwfurnitures:stripped_oak_modern_chair[facing={facing}]",
                     "minecraft:quartz_stairs[facing={back}]"],
    "stool": ["mcwfurnitures:oak_stool_chair[facing={facing}]", "another_furniture:oak_stool", "minecraft:oak_slab"],
    "table": ["mcwfurnitures:oak_table", "handcrafted:oak_table", "another_furniture:oak_table", "minecraft:oak_fence"],
    "table_top": ["minecraft:oak_pressure_plate"],
    "sofa": ["cobblefurnies:red_sofa[facing={facing}]", "another_furniture:red_sofa[facing={facing}]", "minecraft:red_wool"],
    "sofa_white": ["cobblefurnies:white_sofa[facing={facing}]", "another_furniture:white_sofa[facing={facing}]", "minecraft:white_wool"],
    "desk": ["mcwfurnitures:oak_desk[facing={facing}]", "handcrafted:oak_desk[facing={facing}]", "minecraft:oak_planks"],
    "counter": ["mcwfurnitures:oak_counter[facing={facing}]", "handcrafted:oak_counter[facing={facing}]",
                "minecraft:smooth_quartz"],
    "kitchen_drawer": ["mcwfurnitures:oak_kitchen_cabinet[facing={facing}]", "mcwfurnitures:oak_counter[facing={facing}]",
                       "minecraft:barrel[facing=up]"],
    "kitchen_sink": ["mcwfurnitures:oak_kitchen_sink[facing={facing}]", "minecraft:water_cauldron[level=3]"],
    "fridge": ["cobblefurnies:light_fridge[facing={facing}]", "minecraft:iron_block"],
    "stove": ["minecraft:smoker[facing={facing}]"],
    "bookshelf": ["mcwfurnitures:oak_bookshelf[facing={facing}]", "handcrafted:oak_shelf[facing={facing}]", "minecraft:bookshelf"],
    "wardrobe": ["mcwfurnitures:oak_wardrobe[facing={facing}]", "minecraft:spruce_planks"],
    "drawer": ["mcwfurnitures:oak_drawer[facing={facing}]", "handcrafted:oak_nightstand[facing={facing}]",
               "minecraft:chiseled_bookshelf[facing={facing}]"],
    "lamp": ["cobblefurnies:white_lamp", "mcwlights:white_lamp", "minecraft:lantern[hanging=false]"],
    "ceiling_lamp": ["mcwlights:oak_ceiling_fan_light", "mcwlights:light_gray_ceiling_light", "minecraft:lantern[hanging=true]"],
    "wall_lamp": ["mcwlights:wall_lantern[facing={facing}]", "minecraft:wall_torch[facing={facing}]"],
    "street_lamp": ["mcwlights:classic_street_lamp", "minecraft:lantern[hanging=false]"],
    "tv": ["cobblefurnies:tv[facing={facing}]", "minecraft:black_concrete"],
    "plant": ["cobblefurnies:potted_pothos", "minecraft:potted_fern"],
    "plant_big": ["cobblefurnies:mini_topiary", "supplementaries:planter", "minecraft:flowering_azalea"],
    "pot_flower": ["minecraft:potted_red_tulip", "minecraft:potted_poppy"],
    "rug": ["minecraft:red_carpet"],
    "beach_chair": ["beachparty:beach_chair[facing={facing}]", "beachparty:deck_chair[facing={facing}]",
                    "minecraft:white_carpet"],
    "umbrella": ["beachparty:beach_parasol", "beachparty:parasol", "minecraft:red_banner"],
    "hammock": ["beachparty:hammock[facing={facing}]", "minecraft:white_wool"],
    "palm_bar": ["beachparty:palm_bar", "beachparty:palm_bar_stool", "minecraft:bamboo_block"],
    "palm_log": ["beachparty:palm_log[axis=y]", "minecraft:jungle_log[axis=y]"],
    "palm_leaves": ["beachparty:palm_leaves[persistent=true]", "minecraft:jungle_leaves[persistent=true]"],
    "sandcastle": ["beachparty:sandcastle", "minecraft:sandstone_wall"],
    "radio": ["beachparty:radio[facing={facing}]", "minecraft:jukebox"],
    "sign_post": ["supplementaries:sign_post", "minecraft:oak_fence"],
    "flag": ["supplementaries:flag_red[facing={facing}]", "minecraft:red_banner"],
    "jar": ["supplementaries:jar", "minecraft:decorated_pot"],
    "crate": ["another_furniture:oak_shelf[facing={facing}]", "minecraft:barrel[facing=up]"],
    "pokeball_deco": ["cobblefurnies:red_poke_wool", "minecraft:red_concrete"],
    "pc_sofa": ["cobblefurnies:red_sofa[facing={facing}]", "handcrafted:red_couch[facing={facing}]", "minecraft:red_wool"],
    "vending": ["minecraft:light_blue_concrete"],
    "trash": ["mcwfurnitures:oak_bin", "minecraft:composter"],
    "fence_iron": ["mcwfences:railing_iron_bars", "minecraft:iron_bars"],
    "path_tile": ["mcwpaths:stone_crystal_floor_path", "minecraft:smooth_stone"],
    "roof_red": ["mcwroofs:red_concrete_roof[facing={facing}]", "minecraft:red_nether_brick_stairs[facing={facing}]"],
    "window": ["mcwwindows:oak_window", "minecraft:glass_pane"],
    "shutter": ["mcwwindows:oak_shutter[facing={facing}]", "minecraft:oak_trapdoor[facing={facing},half=top,open=true]"],
    "bench": ["another_furniture:oak_bench[facing={facing}]", "mcwfurnitures:oak_bench[facing={facing}]",
              "minecraft:oak_stairs[facing={back}]"],
    "flower_box": ["another_furniture:oak_flower_box", "mcwfurnitures:oak_flower_box", "minecraft:potted_poppy"],
    "tiki_torch": ["mcwlights:bamboo_tiki_torch", "minecraft:torch"],
    "paper_lamp": ["mcwlights:red_paper_lamp", "minecraft:lantern[hanging=false]"],
    "pc_chair": ["cobblefurnies:poke_ball_chair[facing={facing}]", "minecraft:red_concrete"],
    "pc_desk": ["cobblefurnies:poke_ball_desk[facing={facing}]", "minecraft:white_concrete"],
    "pool_tile": ["cobblefurnies:pool_ceramic", "minecraft:light_blue_concrete"],
    "lab_floor": ["cobblefurnies:lab_floor", "minecraft:smooth_quartz"],
    "kitchen_floor": ["cobblefurnies:kitchen_floor", "minecraft:white_concrete"],
    "poke_wool_red": ["cobblefurnies:red_poke_wool", "minecraft:red_wool"],
    "poke_carpet": ["cobblefurnies:red_poke_wool_carpet", "minecraft:red_carpet"],
    "armchair": ["cobblefurnies:red_armchair[facing={facing}]", "minecraft:red_wool"],
    "curtain": ["cobblefurnies:white_curtain[facing={facing}]", "minecraft:white_carpet"],
    "toilet": ["cobblefurnies:light_toilet[facing={facing}]", "minecraft:cauldron"],
    "bonsai": ["cobblefurnies:bonsai_plant", "minecraft:potted_azalea_bush"],
    "statue_pikachu": ["cobblefurnies:statue_pikachu[facing={facing}]", "minecraft:yellow_concrete"],
    "doll_rowlet": ["pokeblocks:gigantic_pokedoll_rowlet[facing={facing}]", "minecraft:green_wool"],
    "doll_mimikyu": ["pokeblocks:gigantic_pokedoll_mimikyu[facing={facing}]", "minecraft:yellow_wool"],
    "doll_palossand": ["pokeblocks:gigantic_pokedoll_palossand[facing={facing}]", "minecraft:sand"],
    "sun_lounger": ["beachparty:beach_sun_lounger[facing={facing}]", "minecraft:white_carpet"],
    "beach_towel": ["beachparty:beach_towel[facing={facing}]", "minecraft:light_blue_carpet"],
    "palm_chair": ["beachparty:palm_chair[facing={facing}]", "minecraft:jungle_stairs[facing={back}]"],
    "palm_bar_stool": ["beachparty:palm_bar_stool", "minecraft:jungle_fence"],
    "cocktail": ["beachparty:coconut_cocktail", "minecraft:potted_dandelion"],
    "coconut": ["beachparty:hanging_coconut", "minecraft:cocoa[age=2,facing={facing}]"],
    "mini_fridge": ["beachparty:mini_fridge[facing={facing}]", "minecraft:white_concrete"],
    "display_case": ["cobblemon:display_case[facing={facing}]", "minecraft:glass"],
}

OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def piece(name: str, facing: str = "south") -> str:
    """Resolved block state for a furniture piece, in the builder's canonical frame."""
    for cand in PIECES[name]:
        state = cand.format(facing=facing, back=OPPOSITE[facing])
        if exists(parse_state(state)[0]):
            return fit(state)
    return fit(PIECES[name][-1].format(facing=facing, back=OPPOSITE[facing]))

def place_tall(c, x, y, z, name: str, facing: str = "south") -> None:
    """Place a piece at (x, y, z); multi-part posts (Macaw's lamps, tiki torches) get stacked."""
    state = piece(name, facing)
    base, props = parse_state(state)
    parts = catalog().get(base, {}).get("part", [])
    if {"bottom", "middle", "top"} <= set(parts):
        extra = {k: v for k, v in props.items() if k != "part"}
        extra.setdefault("lit", "true") if "lit" in catalog().get(base, {}) else None
        for i, part in enumerate(("bottom", "middle", "top")):
            body = ",".join(f"{k}={v}" for k, v in {**extra, "part": part}.items())
            c.set(x, y + i, z, f"{base}[{body}]")
    else:
        c.set(x, y, z, state)
