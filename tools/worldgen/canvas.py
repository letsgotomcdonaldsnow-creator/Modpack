"""World canvas: column terrain + sparse block placements, written as a 1.21.1 world.

Terrain is stored per column (surface height, top/sub/deep blocks, fluid level)
so a 2560x2560 map fits in memory. Buildings, trees and props are stored as
sparse 16^3 sections. `save()` packs everything into Anvil region files.
"""
from __future__ import annotations

import gzip
import json
import math
import struct
import time
import zlib
from pathlib import Path

import numpy as np

from . import nbt

DATA_VERSION = 3955  # Minecraft 1.21.1
MIN_Y, MAX_Y = -64, 320
HEIGHT = MAX_Y - MIN_Y
NONE = 0  # "no override" marker in placement sections

# Ocean floor and water of the flat world generator used outside the map.
FLAT_FLOOR = 40
SEA = 62

BLOCK_ENTITY_IDS = {
    "sign": "minecraft:sign", "hanging_sign": "minecraft:hanging_sign", "chest": "minecraft:chest",
    "barrel": "minecraft:barrel", "bed": "minecraft:bed", "campfire": "minecraft:campfire",
    "banner": "minecraft:banner", "lectern": "minecraft:lectern", "bell": "minecraft:bell",
    "decorated_pot": "minecraft:decorated_pot", "furnace": "minecraft:furnace", "smoker": "minecraft:smoker",
    "blast_furnace": "minecraft:blast_furnace", "chiseled_bookshelf": "minecraft:chiseled_bookshelf",
    "jukebox": "minecraft:jukebox", "brewing_stand": "minecraft:brewing_stand", "trapped_chest": "minecraft:trapped_chest",
    "ender_chest": "minecraft:ender_chest", "enchanting_table": "minecraft:enchanting_table",
    "beacon": "minecraft:beacon", "skull": "minecraft:skull", "conduit": "minecraft:conduit",
}


def parse_state(state: str) -> tuple[str, dict[str, str]]:
    if "[" in state:
        name, rest = state.split("[", 1)
        props = dict(p.split("=", 1) for p in rest.rstrip("]").split(",") if p)
    else:
        name, props = state, {}
    if ":" not in name:
        name = "minecraft:" + name
    return name, props


def canonical(state: str) -> str:
    name, props = parse_state(state)
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]"


def block_entity_id(name: str) -> str | None:
    ns, path = name.split(":", 1)
    if ns != "minecraft":
        return None
    if path.endswith("_hanging_sign") or path.endswith("_wall_hanging_sign"):
        return "minecraft:hanging_sign"
    if path.endswith("_sign"):
        return "minecraft:sign"
    if path.endswith("_bed"):
        return "minecraft:bed"
    if path.endswith("_banner"):
        return "minecraft:banner"
    if path.endswith("shulker_box"):
        return "minecraft:shulker_box"
    if path.endswith("_head") or path.endswith("_skull"):
        return "minecraft:skull"
    if path in ("campfire", "soul_campfire"):
        return "minecraft:campfire"
    return BLOCK_ENTITY_IDS.get(path)


class Canvas:
    def __init__(self, x0: int, z0: int, width: int, depth: int):
        assert x0 % 16 == 0 and z0 % 16 == 0 and width % 16 == 0 and depth % 16 == 0
        self.x0, self.z0, self.w, self.d = x0, z0, width, depth
        self.states: list[str] = ["<none>"]
        self.state_ids: dict[str, int] = {}
        self.air = self.sid("minecraft:air")
        self.height = np.full((depth, width), FLAT_FLOOR, dtype=np.int16)      # surface y
        self.water = np.full((depth, width), SEA, dtype=np.int16)              # fluid top y
        self.top = np.full((depth, width), self.sid("minecraft:sand"), dtype=np.uint16)
        self.sub = np.full((depth, width), self.sid("minecraft:sand"), dtype=np.uint16)
        self.deep = np.full((depth, width), self.sid("minecraft:stone"), dtype=np.uint16)
        self.fluid = np.full((depth, width), self.sid("minecraft:water"), dtype=np.uint16)
        self.biomes: list[str] = ["minecraft:warm_ocean"]
        self.biome_ids: dict[str, int] = {"minecraft:warm_ocean": 0}
        self.biome = np.zeros((depth // 4, width // 4), dtype=np.uint16)
        self.sections: dict[tuple[int, int, int], np.ndarray] = {}
        self.block_entities: dict[tuple[int, int], dict[tuple[int, int, int], dict]] = {}
        self.touched: set[tuple[int, int]] = set()

    # ---------------------------------------------------------------- states
    def sid(self, state: str) -> int:
        key = canonical(state)
        i = self.state_ids.get(key)
        if i is None:
            i = len(self.states)
            self.states.append(key)
            self.state_ids[key] = i
        return i

    def bid(self, biome: str) -> int:
        if ":" not in biome:
            biome = "minecraft:" + biome
        i = self.biome_ids.get(biome)
        if i is None:
            i = len(self.biomes)
            self.biomes.append(biome)
            self.biome_ids[biome] = i
        return i

    # ------------------------------------------------------------ coordinates
    def inside(self, x: int, z: int) -> bool:
        return self.x0 <= x < self.x0 + self.w and self.z0 <= z < self.z0 + self.d

    def surface(self, x: int, z: int) -> int:
        return int(self.height[z - self.z0, x - self.x0])

    def ground(self, x: int, z: int) -> int:
        """Highest solid-ish y: max(surface, water level)."""
        i, j = z - self.z0, x - self.x0
        return int(max(self.height[i, j], self.water[i, j]))

    def is_water(self, x: int, z: int) -> bool:
        i, j = z - self.z0, x - self.x0
        return bool(self.water[i, j] > self.height[i, j])

    # --------------------------------------------------------------- placing
    def set(self, x: int, y: int, z: int, state: str | int, nbt_data: dict | None = None) -> None:
        if not self.inside(x, z) or not (MIN_Y <= y < MAX_Y):
            return
        sid = state if isinstance(state, int) else self.sid(state)
        cx, cz, sy = x >> 4, z >> 4, (y - MIN_Y) >> 4
        key = (cx, cz, sy)
        sec = self.sections.get(key)
        if sec is None:
            sec = np.zeros((16, 16, 16), dtype=np.uint16)
            self.sections[key] = sec
        sec[(y - MIN_Y) & 15, z & 15, x & 15] = sid
        self.touched.add((cx, cz))
        name = self.states[sid].split("[", 1)[0]
        be = block_entity_id(name)
        bes = self.block_entities.setdefault((cx, cz), {})
        bes.pop((x, y, z), None)
        if be or nbt_data:
            entry = {"id": (nbt_data or {}).get("id", be), "x": x, "y": y, "z": z, "keepPacked": nbt.Byte(0)}
            if nbt_data:
                entry.update({k: v for k, v in nbt_data.items() if k != "id"})
            bes[(x, y, z)] = entry

    def get(self, x: int, y: int, z: int) -> str:
        """Best-effort read-back of what will be at a position."""
        if not self.inside(x, z):
            return "minecraft:air"
        sec = self.sections.get((x >> 4, z >> 4, (y - MIN_Y) >> 4))
        if sec is not None:
            v = sec[(y - MIN_Y) & 15, z & 15, x & 15]
            if v != NONE:
                return self.states[v]
        i, j = z - self.z0, x - self.x0
        h, wl = self.height[i, j], self.water[i, j]
        if y <= h:
            return self.states[self.top[i, j] if y == h else self.sub[i, j]]
        if y <= wl:
            return self.states[self.fluid[i, j]]
        return "minecraft:air"

    def fill(self, x1, y1, z1, x2, y2, z2, state) -> None:
        sid = state if isinstance(state, int) else self.sid(state)
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    self.set(x, y, z, sid)

    def sign(self, x, y, z, lines: list[str], wood="oak", wall_facing: str | None = None, rotation=0, glow=False):
        state = f"minecraft:{wood}_wall_sign[facing={wall_facing}]" if wall_facing else f"minecraft:{wood}_sign[rotation={rotation}]"
        lines = (lines + ["", "", "", ""])[:4]
        text = {"has_glowing_text": nbt.Byte(1 if glow else 0), "color": "black",
                "messages": [json.dumps(l, ensure_ascii=False) for l in lines]}
        blank = {"has_glowing_text": nbt.Byte(0), "color": "black", "messages": ['""'] * 4}
        self.set(x, y, z, state, {"id": "minecraft:sign", "is_waxed": nbt.Byte(1), "front_text": text, "back_text": blank})

    # ------------------------------------------------------------------ save
    def chunk_is_default(self, cx: int, cz: int) -> bool:
        if (cx, cz) in self.touched:
            return False
        i, j = cz * 16 - self.z0, cx * 16 - self.x0
        h = self.height[i:i + 16, j:j + 16]
        wl = self.water[i:i + 16, j:j + 16]
        b = self.biome[i // 4:i // 4 + 4, j // 4:j // 4 + 4]
        return bool((h == FLAT_FLOOR).all() and (wl == SEA).all() and (b == 0).all()
                    and (self.top[i:i + 16, j:j + 16] == self.state_ids["minecraft:sand"]).all())

    def _column_blocks(self, cx: int, cz: int) -> np.ndarray:
        i, j = cz * 16 - self.z0, cx * 16 - self.x0
        h = self.height[i:i + 16, j:j + 16].astype(np.int32)[None]
        wl = self.water[i:i + 16, j:j + 16].astype(np.int32)[None]
        top = self.top[i:i + 16, j:j + 16][None]
        sub = self.sub[i:i + 16, j:j + 16][None]
        deep = self.deep[i:i + 16, j:j + 16][None]
        fluid = self.fluid[i:i + 16, j:j + 16][None]
        y = np.arange(MIN_Y, MAX_Y, dtype=np.int32)[:, None, None]
        arr = np.where(y <= h - 4, deep, np.where(y < h, sub, np.where(y == h, top,
                       np.where(y <= wl, fluid, np.uint16(self.air))))).astype(np.uint16)
        arr[0] = self.sid("minecraft:bedrock")
        for sy in range(HEIGHT // 16):
            sec = self.sections.get((cx, cz, sy))
            if sec is not None:
                part = arr[sy * 16:(sy + 1) * 16]
                mask = sec != NONE
                part[mask] = sec[mask]
        return arr

    @staticmethod
    def _pack(indices: np.ndarray, bits: int) -> nbt.LongArray:
        per = 64 // bits
        n = len(indices)
        count = math.ceil(n / per)
        padded = np.zeros(count * per, dtype=np.uint64)
        padded[:n] = indices
        padded = padded.reshape(count, per)
        shifts = (np.arange(per, dtype=np.uint64) * np.uint64(bits))
        longs = np.bitwise_or.reduce(padded << shifts, axis=1)
        return nbt.LongArray(longs.view(np.int64))

    def _palette_entry(self, sid: int) -> dict:
        name, props = parse_state(self.states[sid])
        entry = {"Name": name}
        if props:
            entry["Properties"] = props
        return entry

    def encode_chunk(self, cx: int, cz: int) -> dict:
        arr = self._column_blocks(cx, cz)
        i, j = cz * 16 - self.z0, cx * 16 - self.x0
        bcols = self.biome[i // 4:i // 4 + 4, j // 4:j // 4 + 4]  # [z][x]
        bu, binv = np.unique(bcols, return_inverse=True)
        bpal = [self.biomes[b] for b in bu]
        bidx = np.tile(binv.reshape(4, 4)[None], (4, 1, 1)).reshape(-1)
        biomes = {"palette": bpal}
        if len(bpal) > 1:
            biomes["data"] = self._pack(bidx, max(1, math.ceil(math.log2(len(bpal)))))
        sections = []
        for sy in range(HEIGHT // 16):
            part = arr[sy * 16:(sy + 1) * 16].reshape(-1)
            u, inv = np.unique(part, return_inverse=True)
            states = {"palette": [self._palette_entry(int(s)) for s in u]}
            if len(u) > 1:
                states["data"] = self._pack(inv.astype(np.uint64), max(4, math.ceil(math.log2(len(u)))))
            sections.append({"Y": nbt.Byte(sy + MIN_Y // 16), "block_states": states, "biomes": dict(biomes)})
        return {
            "DataVersion": DATA_VERSION,
            "xPos": cx, "zPos": cz, "yPos": MIN_Y // 16,
            "Status": "minecraft:full",
            "LastUpdate": nbt.Long(0), "InhabitedTime": nbt.Long(0),
            "isLightOn": nbt.Byte(0),
            "sections": sections,
            "block_entities": list(self.block_entities.get((cx, cz), {}).values()),
            "structures": {"starts": {}, "References": {}},
        }

    def save_regions(self, region_dir: Path, log=print) -> int:
        region_dir.mkdir(parents=True, exist_ok=True)
        chunks_by_region: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for cz in range(self.z0 // 16, (self.z0 + self.d) // 16):
            for cx in range(self.x0 // 16, (self.x0 + self.w) // 16):
                if not self.chunk_is_default(cx, cz):
                    chunks_by_region.setdefault((cx >> 5, cz >> 5), []).append((cx, cz))
        total = 0
        now = 1_700_000_000  # fixed so identical worlds produce identical files
        for (rx, rz), chunks in sorted(chunks_by_region.items()):
            locations = bytearray(4096)
            stamps = bytearray(4096)
            body = bytearray()
            for cx, cz in chunks:
                raw = zlib.compress(nbt.encode(self.encode_chunk(cx, cz)), 6)
                payload = struct.pack(">IB", len(raw) + 1, 2) + raw
                payload += b"\0" * ((-len(payload)) % 4096)
                offset = 2 + len(body) // 4096
                sectors = len(payload) // 4096
                idx = 4 * ((cx & 31) + (cz & 31) * 32)
                locations[idx:idx + 4] = struct.pack(">I", (offset << 8) | sectors)
                stamps[idx:idx + 4] = struct.pack(">I", now)
                body += payload
            (region_dir / f"r.{rx}.{rz}.mca").write_bytes(bytes(locations) + bytes(stamps) + bytes(body))
            total += len(chunks)
            log(f"  region r.{rx}.{rz}: {len(chunks)} chunks")
        return total


def write_level_dat(path: Path, name: str, spawn: tuple[int, int, int], seed: int = 7_2016) -> None:
    flat_layers = [
        {"block": "minecraft:bedrock", "height": 1},
        {"block": "minecraft:stone", "height": FLAT_FLOOR - 5 - MIN_Y},
        {"block": "minecraft:sand", "height": 5},
        {"block": "minecraft:water", "height": SEA - FLAT_FLOOR},
    ]
    data = {
        "DataVersion": DATA_VERSION,
        "version": 19133,
        "LevelName": name,
        "GameType": 0,
        "Difficulty": nbt.Byte(2),
        "hardcore": nbt.Byte(0),
        "allowCommands": nbt.Byte(1),
        "initialized": nbt.Byte(1),
        "WasModded": nbt.Byte(1),
        "SpawnX": spawn[0], "SpawnY": spawn[1], "SpawnZ": spawn[2],
        "SpawnAngle": nbt.Float(0.0),
        "Time": nbt.Long(0), "DayTime": nbt.Long(1000), "LastPlayed": nbt.Long(0),
        "raining": nbt.Byte(0), "thundering": nbt.Byte(0), "rainTime": 0, "thunderTime": 0,
        "clearWeatherTime": 0,
        "Version": {"Id": DATA_VERSION, "Name": "1.21.1", "Series": "main", "Snapshot": nbt.Byte(0)},
        "enabled_features": ["minecraft:vanilla"],
        # multiplayer-friendly: no creeper/fire damage to the towns, keep your Poké Balls when you faint
        "GameRules": {"spawnRadius": "0", "doInsomnia": "false", "doPatrolSpawning": "false",
                      "doTraderSpawning": "false", "spawnChunkRadius": "2", "mobGriefing": "false",
                      "doFireTick": "false", "keepInventory": "true", "playersSleepingPercentage": "50"},
        "WorldGenSettings": {
            "seed": nbt.Long(seed),
            "generate_features": nbt.Byte(0),
            "bonus_chest": nbt.Byte(0),
            "dimensions": {
                "minecraft:overworld": {
                    "type": "minecraft:overworld",
                    "generator": {"type": "minecraft:flat", "settings": {
                        "biome": "minecraft:warm_ocean", "features": nbt.Byte(0), "lakes": nbt.Byte(0),
                        "layers": flat_layers, "structure_overrides": []}},
                },
                "minecraft:the_nether": {
                    "type": "minecraft:the_nether",
                    "generator": {"type": "minecraft:noise", "settings": "minecraft:nether",
                                  "biome_source": {"type": "minecraft:multi_noise", "preset": "minecraft:nether"}},
                },
                "minecraft:the_end": {
                    "type": "minecraft:the_end",
                    "generator": {"type": "minecraft:noise", "settings": "minecraft:end",
                                  "biome_source": {"type": "minecraft:the_end"}},
                },
            },
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as f:
        f.write(nbt.encode({"Data": data}))
