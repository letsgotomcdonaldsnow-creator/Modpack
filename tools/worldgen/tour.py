"""Camera tour of the finished world, used by CI to take in-game screenshots.

`write(c, out)` writes a datapack that, once a player is in the world, switches them to
spectator mode and teleports them through every viewpoint, announcing each one in chat
as `TOUR <n> <name>` so tools/tour.sh knows when to take the screenshot.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from . import alola_map
from .canvas import SEA, Canvas
from .kit import B

PLACED: list[dict] = []   # buildings recorded by landmarks.place


def record(fn_name: str, label, x, y, z, facing, W, D):
    PLACED.append(dict(kind=fn_name, label=label, x=x, y=y, z=z, facing=facing, W=W, D=D))


def _look(cam, target):
    dx, dy, dz = (t - c for t, c in zip(target, cam))
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz)))
    return round(yaw, 1), round(pitch, 1)


def orbit(c: Canvas, name, tx, tz, ty=None, dist=60, height=35, azimuth=180.0):
    """Camera `dist` blocks from the target in compass direction `azimuth` (180 = south of it)."""
    if ty is None:
        ty = c.surface(tx, tz) if c.inside(tx, tz) else SEA
    a = math.radians(azimuth)
    cx, cz = int(tx + dist * math.sin(a)), int(tz - dist * math.cos(a))   # compass: 0 north, 90 east
    ground = c.surface(cx, cz) if c.inside(cx, cz) else SEA
    cy = max(ground + 4, ty + height)
    return (name, (cx + 0.5, cy, cz + 0.5), _look((cx, cy, cz), (tx, ty + 4, tz)))


def inside(c: Canvas, name, p, u, w, look_w, v=1.6):
    """Eye-level camera inside a placed building at local (u, w), looking deeper into it."""
    b = B(c, p["x"], p["y"], p["z"], p["facing"])
    x, y, z = b.world(u, 0, w)
    tx, ty, tz = b.world(u, 0, look_w)
    return (name, (x + 0.5, y + v, z + 0.5), _look((x, y + v, z), (tx, ty + 1, tz)))


def facade(c: Canvas, name, p, dist=14, height=4):
    """Camera in front of a placed building looking at its front."""
    b = B(c, p["x"], p["y"], p["z"], p["facing"])
    u = p["W"] / 2
    x, y, z = b.world(int(u), 0, -dist)
    tx, ty, tz = b.world(int(u), 0, p["D"] // 3)
    return (name, (x + 0.5, y + height, z + 0.5), _look((x, y + height, z), (tx, ty + 4, tz)))


def _first(kind, label=None):
    for p in PLACED:
        if p["kind"] == kind and (label is None or p["label"] == label):
            return p
    return None


def views(c: Canvas) -> list[tuple]:
    T = alola_map.TOWNS
    v = []

    def town(name, **kw):
        x, z, y = T[name]
        v.append(orbit(c, name.lower().replace(" ", "_").replace("'", ""), x, z, y, **kw))

    # islands from the air
    # (kept within the 10-chunk render distance of the tour client)
    v.append(orbit(c, "melemele_from_air", -700, -560, 70, dist=110, height=95, azimuth=150))
    v.append(orbit(c, "akala_from_air", -700, 420, 90, dist=110, height=95, azimuth=200))
    v.append(orbit(c, "ulaula_from_air", 250, -330, 90, dist=110, height=95, azimuth=160))
    v.append(orbit(c, "poni_from_air", 560, 420, 80, dist=110, height=95, azimuth=210))
    # towns and landmarks
    town("Hau'oli City", dist=70, height=30)
    v.append(("hauoli_boulevard", (-880.5, 74, -454.5), _look((-880, 74, -454), (-800, 68, -462))))
    v.append(("hauoli_plaza", (-790.5, 72, -418.5), _look((-790, 72, -418), (-790, 67, -440))))
    v.append(("hauoli_north_street", (-760.5, 71, -497.5), _look((-760, 71, -497), (-700, 68, -497))))

    def street(name, x, z, tx, tz, h=5):
        y = c.surface(x, z) + h
        v.append((name, (x + 0.5, y, z + 0.5), _look((x, y, z), (tx, y - h + 2, tz))))

    hx, hz, _ = T["Heahea City"]
    street("heahea_main_street", hx - 70, hz - 10, hx + 10, hz - 10)
    mx, mz, _ = T["Malie City"]
    street("malie_main_street", mx - 80, mz, mx + 10, mz)
    kx, kz, _ = T["Konikoni City"]
    street("konikoni_market", kx - 60, kz, kx + 20, kz)
    ix, iz, _ = T["Iki Town"]
    street("iki_town_stage", ix, iz + 28, ix, iz, h=8)
    town("Hau'oli Marina", dist=50, height=20, azimuth=150)
    town("Iki Town", dist=55, height=28)
    town("Player's House", dist=35, height=14)
    town("Route 2 Pokemon Center", dist=45, height=18, azimuth=240)
    town("Verdant Cavern", dist=40, height=18)
    town("Ten Carat Hill", dist=60, height=30)
    town("Aether Paradise", dist=120, height=50, azimuth=160)
    town("Heahea City", dist=70, height=30)
    town("Paniola Town", dist=50, height=22)
    town("Paniola Ranch", dist=60, height=25)
    town("Brooklet Hill", dist=50, height=25)
    town("Royal Avenue", dist=60, height=28)
    town("Hano Grand Resort", dist=70, height=30)
    town("Wela Volcano Park", dist=70, height=40)
    town("Lush Jungle", dist=50, height=25)
    town("Konikoni City", dist=70, height=30)
    town("Malie City", dist=75, height=30)
    town("Malie Garden", dist=40, height=18)
    town("Mount Hokulani", dist=60, height=30)
    town("Tapu Village", dist=50, height=25)
    town("Po Town", dist=70, height=35)
    town("Haina Desert", dist=60, height=30)
    town("Pokemon League", dist=80, height=40)
    town("Seafolk Village", dist=60, height=25)
    town("Vast Poni Canyon", dist=70, height=40)
    town("Exeggutor Island", dist=60, height=30)
    town("Battle Tree", dist=70, height=35)
    # close-ups
    pc = _first("pokemon_center")
    if pc:
        v.append(facade(c, "pokemon_center_front", pc))
        v.append(inside(c, "pokemon_center_inside", pc, pc["W"] // 2, 1, pc["D"] - 2))
    house = next((p for p in PLACED if p["kind"] == "house" and p["label"] is None and p["W"] >= 10), None)
    if house:
        v.append(facade(c, "house_front", house, dist=10, height=3))
        v.append(inside(c, "house_inside", house, house["W"] // 2, 1, house["D"] - 2))
    return v


def write(c: Canvas, out: Path, extra: list[tuple] | None = None) -> list[tuple]:
    """Write the tour datapack. `extra` are (name, pos, rot, dwell) views, e.g. of the lab."""
    vs = [(n, pos, rot, 30) for n, pos, rot in views(c)] + list(extra or [])
    if out.exists():
        shutil.rmtree(out)
    fn = out / "data" / "alola_tour" / "function"
    (fn / "v").mkdir(parents=True)
    (out / "pack.mcmeta").write_text(json.dumps({"pack": {"pack_format": 48, "description": "Alola camera tour (CI)"}}))
    tags = out / "data" / "minecraft" / "tags" / "function"
    tags.mkdir(parents=True)
    (tags / "tick.json").write_text(json.dumps({"values": ["alola_tour:tick"]}))
    (tags / "load.json").write_text(json.dumps({"values": ["alola_tour:load"]}))
    (fn / "load.mcfunction").write_text("scoreboard objectives add tour dummy\n")
    # wait for a player, then start once
    (fn / "tick.mcfunction").write_text(
        "execute unless entity @a run return 0\n"
        "scoreboard players add #t tour 1\n"
        "execute if score #t tour matches 200 run function alola_tour:start\n")
    (fn / "start.mcfunction").write_text(
        "gamemode spectator @a\n"
        "time set 5000\n"
        "gamerule doDaylightCycle false\n"
        "weather clear 1000000\n"
        "gamerule doWeatherCycle false\n"
        "gamerule doMobSpawning false\n"
        'tellraw @a {"text":"TOUR START"}\n'
        "schedule function alola_tour:v/1 100t\n")
    (fn / "s").mkdir()
    for i, (name, (x, y, z), (yaw, pitch), dwell) in enumerate(vs, 1):
        # v/i moves the camera; s/i (dwell seconds later) says "SHOT", the script grabs the screen
        # right away, and the camera only moves on 4 seconds after that.
        (fn / "v" / f"{i}.mcfunction").write_text(
            f"tp @a {x} {y} {z} {yaw} {pitch}\n"
            f'tellraw @a {{"text":"TOUR {i} {name} {dwell}"}}\n'
            f"schedule function alola_tour:s/{i} {max(1, dwell - 4) * 20}t\n")
        nxt = f"alola_tour:v/{i + 1}" if i < len(vs) else "alola_tour:end"
        (fn / "s" / f"{i}.mcfunction").write_text(
            f'tellraw @a {{"text":"SHOT {i} {name}"}}\n'
            f"schedule function {nxt} 80t\n")
    (fn / "end.mcfunction").write_text('tellraw @a {"text":"TOUR END"}\n')
    total = sum(v[3] for v in vs)
    print(f"  tour datapack: {len(vs)} viewpoints ({total // 60} min) -> {out}")
    return vs
