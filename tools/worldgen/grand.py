"""Alola's grand landmarks, built to be the highlights of the tour: the Pokémon League."""
from __future__ import annotations

import math
import random

from . import arch, furn
from .buildings import merchant, npc, pokeball_disc, pokeball_face, setup_cmd
from .canvas import Canvas

WHITE = "minecraft:smooth_quartz"
TRIM = "minecraft:quartz_bricks"
PILLAR = "minecraft:quartz_pillar[axis=y]"
GOLD = "minecraft:gold_block"
BLUE = "minecraft:light_blue_stained_glass"
FLOOR = "minecraft:polished_diorite"


def _column(b, u, w, v1, v2):
    b.set(u, v1, w, "minecraft:chiseled_quartz_block")
    for v in range(v1 + 1, v2):
        b.set(u, v, w, PILLAR)
    b.set(u, v2, w, GOLD)


def pokemon_league(c: Canvas, x, y, z, facing, rng: random.Random):
    """(x, y, z) is the front-left corner of the approach; the building runs 58 blocks back."""
    b = arch.Bld(c, x, y, z, facing)
    W, D = 45, 58
    b.clear_above(-2, -2, W + 1, D + 1, 48)
    b.foundation(-1, -1, W, D, "minecraft:polished_deepslate")
    for u in range(-1, W + 1):
        for w in range(-1, D + 1):
            b.set(u, 0, w, "minecraft:polished_andesite" if (u + w) % 2 else "minecraft:andesite")
    cu = W // 2
    # --- approach: grand stairs onto a terrace, lantern columns and banners
    for k in range(4):
        for u in range(cu - 9 + k, cu + 10 - k):
            b.set(u, k + 1, 2 + k, "minecraft:quartz_stairs[facing=north,half=bottom,shape=straight]")
            for kk in range(k):
                b.set(u, kk + 1, 2 + k, WHITE)
    for u in range(4, W - 4):
        for w in range(6, 12):
            for v in range(1, 5):
                b.set(u, v, w, TRIM if v < 4 else WHITE)
    for u in (cu - 11, cu + 11):
        _column(b, u, 4, 1, 9)
        b.set(u, 10, 4, "minecraft:lantern[hanging=false]")
        b.set(u, 7, 3, "minecraft:blue_wall_banner[facing=south]")
    # --- main hall (v 4 = terrace floor level)
    hv = 4
    h1, h2 = 12, 32            # hall depth range (w)
    hu1, hu2 = 6, W - 7
    for u in range(hu1, hu2 + 1):
        for w in range(h1, h2 + 1):
            b.set(u, hv, w, FLOOR if (u + w) % 4 else "minecraft:polished_andesite")
    H = 13
    for v in range(hv + 1, hv + H):
        for u in range(hu1, hu2 + 1):
            for w in (h1, h2):
                b.set(u, v, w, WHITE if v % 4 else TRIM)
        for w in range(h1, h2 + 1):
            for u in (hu1, hu2):
                b.set(u, v, w, WHITE if v % 4 else TRIM)
    # tall arched windows and pilasters
    for u in range(hu1 + 2, hu2 - 1, 4):
        _column(b, u, h1 - 1, hv + 1, hv + H - 1)
        if u + 2 < hu2:
            for v in range(hv + 3, hv + H - 3):
                b.set(u + 2, v, h1, BLUE)
            b.set(u + 2, hv + H - 3, h1, "minecraft:quartz_stairs[facing=south,half=top,shape=straight]")
    for w in range(h1 + 3, h2 - 1, 4):
        for u in (hu1, hu2):
            for v in range(hv + 3, hv + H - 3):
                b.set(u, v, w, BLUE)
    # entrance: triple doorway with a Poké Ball crest and the League's name
    for du in (-1, 0, 1):
        for v in range(hv + 1, hv + 5):
            b.set(cu + du, v, h1, "minecraft:air")
    pokeball_face(b, cu, hv + 8, h1 - 1, 3)
    b.sign(cu, hv + 5, h1 - 1, ["§6POKéMON LEAGUE", "", "Mount Lanakila", "Alola"], wood="dark_oak")
    # vaulted roof along w with a skylight ridge
    span = hu2 - hu1 + 2
    for k in range(span // 2 + 1):
        v = hv + H + (k if k < 6 else 6)
        for w in range(h1 - 1, h2 + 2):
            lu, ru = hu1 - 1 + k, hu2 + 1 - k
            if lu > ru:
                break
            if k < 6:
                b.set(lu, v, w, "minecraft:quartz_stairs[facing=east,half=bottom,shape=straight]")
                b.set(ru, v, w, "minecraft:quartz_stairs[facing=west,half=bottom,shape=straight]")
            else:
                for u in range(lu, ru + 1):
                    b.set(u, v, w, "minecraft:light_blue_stained_glass" if abs(u - cu) <= 2 else WHITE)
                break
    # inside: red carpet, Poké Ball mosaic, Pokémon Center and Mart counters, banners
    for w in range(h1 + 1, h2):
        for du in (-1, 0, 1):
            b.set(cu + du, hv, w, "minecraft:red_concrete")
    pokeball_disc(b, cu, (h1 + h2) // 2, hv, 5)
    for w in range(h1 + 3, h1 + 9):
        b.set(hu1 + 2, hv + 1, w, "minecraft:red_concrete")
        b.set(hu1 + 2, hv + 2, w, "minecraft:smooth_quartz_slab[type=bottom]")
        b.set(hu2 - 2, hv + 1, w, "minecraft:light_blue_concrete")
        b.set(hu2 - 2, hv + 2, w, "minecraft:smooth_quartz_slab[type=bottom]")
    setup_cmd(b, hu1 + 1, hv + 1, h1 + 5, "setblock {x} {y} {z} cobblemon:healing_machine[facing=east]")
    npc(b, hu1 + 1, hv + 1, h1 + 7, "alola:nurse")
    merchant(b, hu2 - 1, hv + 1, h1 + 6, name="League Mart", look="left")
    for u in range(hu1 + 3, hu2 - 2, 6):
        b.set(u, hv + 1, h2 - 2, furn.piece("plant_big"))
        b.set(u, hv + H - 2, h2 - 1, "minecraft:red_wall_banner[facing=south]")
    for du in (-5, 0, 5):
        for w in ((h1 + h2) // 2 - 7, (h1 + h2) // 2 + 1):
            b.set(cu + du, hv + H + 5, w, "mcwlights:golden_chandelier")
    # --- the Elite Four: four themed chambers off a round antechamber behind the hall
    av, ac = hv, 42           # antechamber floor and centre (w)
    for du in range(-8, 9):
        for dw in range(-8, 9):
            d = math.hypot(du, dw)
            if d <= 8.5:
                b.set(cu + du, av, ac + dw, "minecraft:polished_deepslate" if d > 7 else FLOOR)
                for v in range(av + 1, av + 9):
                    if 7.5 < d <= 8.5:
                        b.set(cu + du, v, ac + dw, WHITE if v != av + 8 else GOLD)
                    elif d <= 7.5:
                        b.set(cu + du, v, ac + dw, "minecraft:air")
                # the ceiling is open in the middle: the Champion's stair tower rises from here
                b.set(cu + du, av + 9, ac + dw, WHITE if d > 3.5 else "minecraft:air")
    for v in range(av + 1, av + 4):                      # passage from the hall
        for du in (-1, 0, 1):
            for w in range(h2, ac - 7):
                b.set(cu + du, v, w, "minecraft:air")
    for w in range(h2, ac - 7):
        for du in (-2, 2):
            for v in range(av + 1, av + 5):
                b.set(cu + du, v, w, TRIM)
        for du in (-1, 0, 1):
            b.set(cu + du, av, w, "minecraft:red_concrete")
            b.set(cu + du, av + 4, w, WHITE)
    # two chambers on each side of the antechamber
    chambers = [("e4_hala", "Hala", "Fighting", cu - 20, ac - 6), ("e4_olivia", "Olivia", "Rock", cu + 9, ac - 6),
                ("e4_acerola", "Acerola", "Ghost", cu - 20, ac + 5), ("e4_kahili", "Kahili", "Flying", cu + 9, ac + 5)]
    for cls, who, typ, u0, w0 in chambers:
        _e4_room(b, rng, cls, who, typ, u0, w0, av)
        # corridor from the antechamber
        door_w = w0 + 5
        if u0 < cu:
            for u in range(u0 + 11, cu - 7):
                for v in range(av + 1, av + 4):
                    b.set(u, v, door_w, "minecraft:air")
                b.set(u, av, door_w, "minecraft:red_concrete")
        else:
            for u in range(cu + 8, u0):
                for v in range(av + 1, av + 4):
                    b.set(u, v, door_w, "minecraft:air")
                b.set(u, av, door_w, "minecraft:red_concrete")
    # --- the Champion's tower: spiral stairs to an open-air summit arena
    tc = ac
    for v in range(av + 10, av + 30):
        for du in range(-4, 5):
            for dw in range(-4, 5):
                d = math.hypot(du, dw)
                if 3.5 < d <= 4.5:
                    b.set(cu + du, v, tc + dw, WHITE if (v // 3) % 2 else TRIM)
                elif d <= 3.5:
                    b.set(cu + du, v, tc + dw, "minecraft:air")
    # spiral stair: each step rises half a block (bottom slab, then top slab one step on)
    sv = av + 30
    last = None
    for k in range(2, 2 * (sv - av) - 1):
        a = k * 0.42
        su, sw = round(2.5 * math.cos(a)), round(2.5 * math.sin(a))
        v = av + k // 2
        b.set(cu + su, v, tc + sw, "minecraft:quartz_slab[type=top]" if k % 2 else "minecraft:quartz_slab[type=bottom]")
        last = (su, sw)
    for du in range(-13, 14):
        for dw in range(-13, 14):
            d = math.hypot(du, dw)
            if d <= 13.5:
                b.set(cu + du, sv, tc + dw, "minecraft:polished_andesite" if d > 12 else
                      ("minecraft:white_concrete" if (du // 3 + dw // 3) % 2 else "minecraft:light_gray_concrete"))
                b.set(cu + du, sv - 1, tc + dw, WHITE)
                if 12.5 < d <= 13.5:
                    b.set(cu + du, sv + 1, tc + dw, "minecraft:white_stained_glass_pane")
    pokeball_disc(b, cu, tc, sv, 6)
    for a in range(0, 360, 45):
        pu, pw = round(12.5 * math.cos(math.radians(a))), round(12.5 * math.sin(math.radians(a)))
        _column(b, cu + pu, tc + pw, sv + 1, sv + 7)
        b.set(cu + pu, sv + 8, tc + pw, "minecraft:lantern[hanging=false]")
    for du in (-1, 0, 1):                                # stairwell opening where the spiral arrives
        for dw in (-1, 0, 1):
            b.set(cu + last[0] + du, sv, tc + last[1] + dw, "minecraft:air")
    npc(b, cu, sv + 1, tc + 8, "alola:champion_kukui")
    b.sign(cu, sv + 1, tc + 11, ["Champion", "of Alola", "", "Summit of Lanakila"], wood="dark_oak", wall=False)
    return W, D + 4


# =============================================================== Aether Paradise

AETHER_Y = "minecraft:yellow_concrete"


def _octagon(r, du, dw):
    return abs(du) <= r and abs(dw) <= r and abs(du) + abs(dw) <= r * 1.42


def aether_paradise(c: Canvas, cx, y, cz, rng: random.Random):
    """The Aether Foundation's artificial island: dock ring at sea level, main deck, central tower,
    conservation greenhouse, entrance hall with a Pokémon Center, Lusamine's mansion on a terrace."""
    from .canvas import SEA
    b = arch.Bld(c, cx, y, cz, "south")
    R = 58
    floor_y = SEA - 18
    # support pillars from the sea bed and the dock ring at sea level
    for du in range(-R - 8, R + 9):
        for dw in range(-R - 8, R + 9):
            inner = _octagon(R, du, dw)
            dock = _octagon(R + 8, du, dw) and not _octagon(R + 1, du, dw)
            if dock:
                b.set(du, SEA + 1 - y, dw, AETHER_Y if not _octagon(R + 7, du, dw) else "minecraft:white_concrete")
            if inner:
                edge = not _octagon(R - 1, du, dw)
                b.set(du, 0, dw, "minecraft:white_concrete" if edge else
                      ("minecraft:smooth_quartz" if (du // 6 + dw // 6) % 2 else "minecraft:quartz_block"))
                b.set(du, -1, dw, "minecraft:white_concrete")
                if edge:
                    b.set(du, 1, dw, "minecraft:white_stained_glass_pane")
            if (inner or dock) and du % 12 == 0 and dw % 12 == 0:
                for v in range(floor_y - y, 0 if inner else SEA + 1 - y):
                    b.set(du, v, dw, "minecraft:quartz_pillar[axis=y]")
    # stripes and the landing emblem
    for k in range(-R + 3, R - 2):
        b.set(k, 0, 0, AETHER_Y)
        b.set(0, 0, k, AETHER_Y)
    for du in range(-9, 10):
        for dw in range(-9, 10):
            d = math.hypot(du, dw)
            if d <= 9.4:
                b.set(du, 0, 30 + dw, AETHER_Y if 7.5 < d or abs(du) <= 1 or abs(dw) <= 1 else "minecraft:white_concrete")
    # central tower: banded white drum with windows, glass lift, observation deck on top
    for v in range(1, 46):
        for du in range(-9, 10):
            for dw in range(-9, 10):
                if not _octagon(9, du, dw):
                    continue
                ring = not _octagon(8, du, dw)
                if ring:
                    b.set(du, v, dw, "minecraft:light_blue_stained_glass" if v % 5 in (2, 3) else "minecraft:white_concrete")
                elif v % 5 == 0:
                    b.set(du, v, dw, "minecraft:smooth_quartz")
    for v in range(1, 46):
        for du in (-1, 0, 1):
            for dw in (-1, 0, 1):
                b.set(du, v, dw, "minecraft:air" if (du, dw) == (0, 0) else "minecraft:glass")
    for v in range(1, 45):
        b.set(0, v, -2, "minecraft:ladder[facing=north]")
    for du in (-1, 0, 1):                     # doorway into the tower on the entrance side
        for v in (1, 2, 3):
            for dw in (8, 9):
                b.set(du, v, dw, "minecraft:air")
    for du in range(-14, 15):
        for dw in range(-14, 15):
            if _octagon(14, du, dw) and not _octagon(8, du, dw):
                b.set(du, 46, dw, "minecraft:smooth_quartz")
                if not _octagon(13, du, dw):
                    b.set(du, 47, dw, "minecraft:white_stained_glass_pane")
    b.sign(0, 2, -10, ["Aether Paradise", "", "Aether Foundation", ""], wood="birch", wall=False)
    # conservation area: glass greenhouse with trees, grass, a pond and flowers
    gx, gz = -34, 12
    b.dome(gx, gz, 1, 19, "minecraft:glass")
    b.disc(gx, gz, 0, 18.5, "minecraft:grass_block")
    b.disc(gx, gz, 0, 5.5, "minecraft:water")
    for _ in range(40):
        a, r = rng.uniform(0, math.tau), rng.uniform(7, 16)
        fu, fw = gx + round(r * math.cos(a)), gz + round(r * math.sin(a))
        b.set(fu, 1, fw, rng.choice(["wilderwild:pink_hibiscus", "wilderwild:yellow_hibiscus", "minecraft:allium",
                                     "minecraft:short_grass", "minecraft:fern", "wilderwild:white_hibiscus"]))
    for a in range(0, 360, 60):
        tu, tw = gx + round(11 * math.cos(math.radians(a))), gz + round(11 * math.sin(math.radians(a)))
        for v in range(1, 6):
            b.set(tu, v, tw, "minecraft:birch_log[axis=y]")
        for du in range(-2, 3):
            for dw in range(-2, 3):
                for dv in (5, 6, 7):
                    if abs(du) + abs(dw) + (dv - 6) ** 2 <= 3:
                        b.set(tu + du, dv, tw + dw, "minecraft:azalea_leaves[persistent=true]")
    # entrance hall on the far side of the landing emblem (local +w), with Pokémon Center and Mart
    ew1, ew2 = 36, 50
    for du in range(-14, 15):
        for dw in range(ew1, ew2 + 1):
            wall = abs(du) == 14 or dw in (ew1, ew2)
            for v in range(1, 9):
                b.set(du, v, dw, ("minecraft:light_blue_stained_glass" if 2 <= v <= 6 and dw == ew2 and du % 3
                                  else "minecraft:white_concrete") if wall else "minecraft:air")
            b.set(du, 9, dw, "minecraft:smooth_quartz" if wall else "minecraft:glass" if abs(du) < 10 else "minecraft:smooth_quartz")
    for v in range(1, 5):
        for du in (-2, -1, 0, 1, 2):
            b.set(du, v, ew2, "minecraft:air")
    for du in range(-13, 14):
        b.set(du, 8, ew2 + 1, AETHER_Y)
    for dw in range(ew1 + 2, ew1 + 8):
        b.set(-11, 1, dw, "minecraft:red_concrete"), b.set(-11, 2, dw, "minecraft:smooth_quartz_slab[type=bottom]")
        b.set(11, 1, dw, "minecraft:light_blue_concrete"), b.set(11, 2, dw, "minecraft:smooth_quartz_slab[type=bottom]")
    setup_cmd(b, -12, 1, ew1 + 4, "setblock {x} {y} {z} cobblemon:healing_machine[facing=east]")
    npc(b, -12, 1, ew1 + 6, "alola:nurse")
    merchant(b, 12, 1, ew1 + 5, name="Aether Mart", look="left")
    for dw in range(ew1 + 2, ew2 - 1, 4):
        b.set(-6, 1, dw, furn.piece("sofa_white", "east")), b.set(6, 1, dw, furn.piece("sofa_white", "west"))
    npc(b, 0, 1, ew1 + 3, "alola:gladion")
    from . import multiplayer
    multiplayer.waystone(c, *b.world(8, 1, ew2 - 3), "Aether Paradise", facing="north", pad=False)
    b.sign(0, 7, ew2 + 1, ["Aether Foundation", "", "Welcome to", "Aether Paradise"], wood="birch")
    # Lusamine's mansion on a raised terrace (local -w), facing the tower, with a formal garden
    tv = 6
    for du in range(-24, 25):
        for dw in range(-54, -26):
            if _octagon(R - 2, du, dw):
                for v in range(1, tv):
                    b.set(du, v, dw, "minecraft:white_concrete" if abs(du) == 24 or dw == -27 else "minecraft:smooth_quartz")
                b.set(du, tv, dw, "minecraft:grass_block" if abs(du) > 3 else "minecraft:smooth_quartz")
    for k in range(tv):
        for du in (-2, -1, 0, 1, 2):
            b.set(du, k + 1, -26 + (tv - 1 - k) - tv + 1, "minecraft:quartz_stairs[facing=south,half=bottom,shape=straight]")
    arch.build_house(c, cx + 10, y + tv, cz + 30, "north", rng, style="modern", W=21, D=13, floors=2,
                     label="Lusamine", yard=False)
    for du in range(-22, 23, 4):
        for dw in (-28, -52):
            if abs(du) > 3:
                b.set(du, tv + 1, dw, rng.choice(["minecraft:white_tulip", "wilderwild:white_hibiscus", "minecraft:lily_of_the_valley"]))
    npc(b, 0, tv + 1, -28, "alola:lusamine")
    npc(b, 6, 1, 20, "alola:plumeria")
    return R, R


E4_THEMES = {
    "Fighting": ("minecraft:stripped_oak_wood[axis=y]", "minecraft:bamboo_mosaic", "minecraft:oak_planks",
                 "minecraft:torch", "minecraft:orange_wall_banner"),
    "Rock": ("minecraft:tuff_bricks", "minecraft:calcite", "minecraft:polished_tuff", "minecraft:amethyst_cluster[facing=up]",
             "minecraft:brown_wall_banner"),
    "Ghost": ("minecraft:polished_blackstone_bricks", "minecraft:purple_concrete", "minecraft:crying_obsidian",
              "minecraft:soul_lantern[hanging=false]", "minecraft:purple_wall_banner"),
    "Flying": ("minecraft:white_concrete", "minecraft:light_blue_concrete", "minecraft:white_wool",
               "minecraft:sea_lantern", "minecraft:light_blue_wall_banner"),
}


def _e4_room(b, rng, cls, who, typ, u0, w0, v0):
    wall, floor, accent, light, banner = E4_THEMES[typ]
    S = 11
    for u in range(u0, u0 + S):
        for w in range(w0, w0 + S):
            edge = u in (u0, u0 + S - 1) or w in (w0, w0 + S - 1)
            b.set(u, v0, w, accent if edge else floor)
            for v in range(v0 + 1, v0 + 8):
                b.set(u, v, w, wall if edge else "minecraft:air")
            b.set(u, v0 + 8, w, wall if edge or typ != "Flying" else "minecraft:light_blue_stained_glass")
    pokeball_disc(b, u0 + S // 2, w0 + S // 2, v0, 2)
    for (u, w) in ((u0 + 1, w0 + 1), (u0 + S - 2, w0 + 1), (u0 + 1, w0 + S - 2), (u0 + S - 2, w0 + S - 2)):
        b.set(u, v0 + 1, w, light)
    for u in (u0 + 3, u0 + S - 4):
        b.set(u, v0 + 5, w0 + S - 2, banner + "[facing=south]" if "[" not in banner else banner)
    if typ == "Flying":   # Kahili golfs: a putting green with a flag
        for du in range(-2, 3):
            for dw in range(-1, 2):
                b.set(u0 + S // 2 + du, v0, w0 + 2 + dw, "minecraft:moss_block")
        b.set(u0 + S // 2 + 1, v0 + 1, w0 + 2, "minecraft:white_banner")
    if typ == "Rock":
        for _ in range(6):
            b.set(u0 + rng.randint(1, S - 2), v0 + 1, w0 + rng.randint(1, S - 2), "minecraft:amethyst_cluster[facing=up]")
    if typ == "Ghost":
        for _ in range(5):
            b.set(u0 + rng.randint(1, S - 2), v0 + 7, w0 + rng.randint(1, S - 2), "minecraft:cobweb")
    npc(b, u0 + S // 2, v0 + 1, w0 + S - 3, f"alola:{cls}")
    b.sign(u0 + S // 2, v0 + 3, w0 + S - 2, ["Elite Four", who, f"{typ}-type"], wood="dark_oak")
