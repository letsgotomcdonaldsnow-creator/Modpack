"""The Alola region: island shapes, relief, zones, towns and routes.

Coordinates are Minecraft blocks (x east, z south). The map spans
x, z in [-1280, 1280). Layout follows the Sun & Moon town map:
Melemele in the north-west, Akala in the south-west, Ula'ula (the largest,
with Mount Lanakila) in the north-east, Poni in the south-east, and Aether
Paradise floating between Melemele and Akala.
"""
from __future__ import annotations

from .terrain import (BEACH, CANYON, CAVE_HILL, DESERT, FLOWERS, FOREST, GARDEN, GRASS, JUNGLE, MEADOW,
                      PLATFORM, RAINY, RANCH, ROCKY, SAVANNA, SNOW, TOWN, VOLCANIC, Terrain)

X0, Z0, SIZE = -1280, -1280, 2560

# ---------------------------------------------------------------- places
# name: (x, z, ground y) -- ground y is the flattened height of the site
TOWNS = {
    # Melemele Island
    "Hau'oli City": (-790, -440, 66),
    "Hau'oli Marina": (-955, -452, 65),
    "Hau'oli Outskirts": (-600, -468, 67),
    "Iki Town": (-555, -770, 92),
    "Route 2 Pokemon Center": (-900, -600, 74),
    "Hau'oli Cemetery": (-935, -655, 78),
    "Verdant Cavern": (-835, -715, 80),
    "Melemele Meadow": (-1030, -800, 84),
    "Ruins of Conflict": (-575, -905, 112),
    "Ten Carat Hill": (-1085, -620, 70),
    "Kala'e Bay": (-760, -870, 64),
    "Big Wave Beach": (-455, -575, 64),
    "Player's House": (-520, -470, 67),
    "Kukui's Lab": (-470, -500, 65),
    # Aether Paradise
    "Aether Paradise": (-300, -60, 70),
    # Akala Island
    "Heahea City": (-890, 300, 66),
    "Paniola Town": (-870, 545, 75),
    "Paniola Ranch": (-1000, 590, 74),
    "Brooklet Hill": (-835, 765, 78),
    "Royal Avenue": (-640, 300, 70),
    "Hano Grand Resort": (-360, 330, 66),
    "Wela Volcano Park": (-610, 560, 138),
    "Route 8": (-455, 570, 70),
    "Lush Jungle": (-370, 670, 72),
    "Konikoni City": (-565, 820, 66),
    "Memorial Hill": (-440, 815, 80),
    "Ruins of Life": (-790, 860, 96),
    # Ula'ula Island
    "Malie City": (40, -330, 66),
    "Malie Garden": (10, -420, 67),
    "Mount Hokulani": (170, -660, 170),
    "Blush Mountain": (390, -175, 80),
    "Tapu Village": (650, -215, 78),
    "Haina Desert": (810, -250, 72),
    "Ruins of Abundance": (850, -300, 76),
    "Thrifty Megamart": (620, -30, 66),
    "Aether House": (420, -35, 66),
    "Ula'ula Meadow": (250, -95, 70),
    "Po Town": (130, -140, 70),
    "Pokemon League": (470, -470, 232),
    # Poni Island
    "Seafolk Village": (290, 480, 63),
    "Poni Wilds": (345, 385, 67),
    "Hapu's House": (455, 370, 72),
    "Ruins of Hope": (575, 285, 88),
    "Exeggutor Island": (395, 205, 66),
    "Altar of the Sunne": (680, 430, 160),
    "Vast Poni Canyon": (660, 570, 80),
    "Poni Plains": (860, 620, 70),
    "Battle Tree": (915, 365, 80),
    "Poni Meadow": (735, 790, 70),
    "Resolution Cave": (905, 790, 72),
    "Poni Grove": (500, 700, 70),
}

# route polylines: (label, points, width)
ROUTES = [
    # Melemele
    ("Route 1", [(-520, -480), (-530, -560), (-510, -640), (-540, -710), (-555, -745)], 4),
    ("Route 1 (Hau'oli Outskirts)", [(-660, -470), (-600, -468), (-540, -472)], 5),
    ("Route 2", [(-905, -470), (-905, -540), (-900, -600), (-885, -660), (-850, -700)], 4),
    ("Route 3", [(-900, -620), (-960, -680), (-1000, -740), (-1030, -790)], 4),
    ("Mahalo Trail", [(-555, -800), (-570, -845), (-575, -890)], 3),
    ("Route 1 to Ten Carat", [(-940, -470), (-1030, -520), (-1080, -600)], 3),
    ("Route 3 to Kala'e Bay", [(-1000, -760), (-900, -820), (-790, -860)], 3),
    # Akala
    ("Route 4", [(-880, 350), (-900, 420), (-880, 500), (-870, 530)], 4),
    ("Route 5", [(-860, 575), (-850, 650), (-840, 730)], 4),
    ("Route 6", [(-845, 530), (-760, 470), (-700, 380), (-650, 320)], 4),
    ("Route 7", [(-620, 330), (-600, 400), (-610, 470), (-610, 500)], 4),
    ("Route 8", [(-560, 560), (-500, 570), (-455, 570), (-420, 610), (-385, 650)], 4),
    ("Route to Hano", [(-610, 300), (-500, 310), (-400, 325)], 4),
    ("Diglett's Tunnel", [(-460, 610), (-500, 700), (-540, 790)], 3),
    ("Akala Outskirts", [(-610, 830), (-700, 850), (-770, 860)], 3),
    ("Memorial Hill path", [(-520, 820), (-450, 815)], 3),
    # Ula'ula
    ("Route 10", [(90, -370), (120, -460), (150, -560), (165, -640)], 4),
    ("Route 11", [(100, -300), (200, -270), (300, -220)], 4),
    ("Route 12", [(300, -220), (390, -190), (480, -180)], 4),
    ("Route 13", [(480, -180), (560, -190), (640, -210)], 4),
    ("Haina Desert trail", [(660, -215), (760, -240), (845, -290)], 3),
    ("Route 14", [(650, -200), (660, -120), (630, -45)], 4),
    ("Route 15", [(600, -40), (500, -40), (420, -40)], 4),
    ("Route 16", [(420, -40), (330, -70), (260, -95)], 4),
    ("Route 17", [(250, -95), (190, -120), (150, -140)], 4),
    ("Mount Lanakila path", [(640, -230), (590, -330), (530, -410), (480, -455)], 3),
    # Poni
    ("Poni Wilds", [(310, 470), (340, 400), (400, 380), (455, 372)], 4),
    ("Ancient Poni Path", [(455, 370), (520, 330), (570, 295)], 3),
    ("Poni Breaker Coast", [(455, 372), (560, 420), (640, 470)], 3),
    ("Vast Poni Canyon trail", [(620, 560), (660, 520), (675, 470), (680, 440)], 3),
    ("Poni Plains road", [(660, 580), (760, 610), (860, 620)], 4),
    ("Poni Gauntlet", [(860, 610), (900, 520), (915, 400)], 3),
    ("Poni Meadow path", [(760, 620), (740, 700), (735, 780)], 3),
    ("Poni Coast", [(735, 790), (820, 800), (900, 790)], 3),
    ("Poni Grove path", [(440, 380), (470, 540), (500, 690)], 3),
]


def build(t: Terrain) -> None:
    t.begin()
    # ------------------------------------------------ Melemele Island (NW)
    t.add_island(-770, -640, 360, 250, rot=-0.15, seed=11)
    t.add_island(-1040, -620, 120, 170, seed=12)                     # Ten Carat Hill lobe (west)
    t.add_island(-570, -840, 110, 110, seed=13)                      # Mahalo Trail headland (north-east)
    t.add_island(-470, -540, 90, 90, seed=14)                        # Big Wave Beach cape (east)
    t.cut_bay(-760, -915, 90, 50, seed=15)                           # Kala'e Bay
    t.paint(-790, -445, 190, 50, TOWN, seed=16)
    t.paint(-1030, -790, 90, 70, FLOWERS, seed=17)                   # Melemele Meadow
    t.paint(-1075, -620, 90, 110, ROCKY, seed=18)                    # Ten Carat Hill
    t.paint(-840, -700, 70, 50, CAVE_HILL, seed=19)                  # Verdant Cavern hill
    t.paint(-700, -650, 160, 120, FOREST, seed=20)
    t.hill(-1080, -625, 85, 48)
    t.hill(-835, -720, 55, 26)
    t.hill(-560, -770, 90, 30, sharp=1.6)                            # Iki Town's hill
    t.hill(-575, -900, 50, 50)                                       # Ruins of Conflict cliff
    t.hill(-720, -660, 140, 22)
    # Aether Paradise is built as a platform on stilts over the sea (see landmarks).
    # ------------------------------------------------ Akala Island (SW)
    t.add_island(-640, 560, 400, 330, rot=0.1, seed=21)
    t.add_island(-900, 330, 120, 90, seed=22)                        # Heahea peninsula
    t.add_island(-360, 360, 110, 90, seed=23)                        # Hano cape
    t.add_island(-790, 850, 110, 70, seed=24)                        # Ruins of Life headland
    t.paint(-610, 560, 110, 110, VOLCANIC, wobble=0.1, seed=25)
    t.paint(-380, 660, 120, 110, JUNGLE, seed=26)
    t.paint(-1000, 590, 90, 80, RANCH, seed=27)
    t.paint(-840, 740, 90, 80, FOREST, seed=28)
    t.paint(-700, 380, 120, 80, SAVANNA, seed=29)
    t.cone(-610, 560, 170, 82, crater_r=26, crater_depth=12)         # Wela Volcano
    t.lake(-610, 560, 20, 20, level=126, depth=4, seed=30)           # lava crater
    t.hill(-440, 815, 45, 18)                                        # Memorial Hill
    t.hill(-790, 860, 50, 34)                                        # Ruins of Life hill
    t.hill(-835, 770, 70, 14)
    t.lake(-850, 745, 34, 20, level=76, depth=4, seed=31)            # Brooklet Hill pools
    t.lake(-815, 790, 22, 15, level=73, depth=3, seed=32)
    # ------------------------------------------------ Ula'ula Island (NE)
    t.add_island(430, -390, 520, 420, rot=0.08, seed=41)
    t.add_island(40, -350, 130, 150, seed=42)                        # Malie peninsula
    t.add_island(820, -250, 170, 140, seed=43)                       # Haina Desert
    t.add_island(620, -40, 140, 70, seed=44)                         # south coast
    t.paint(820, -250, 150, 120, DESERT, seed=45)
    t.paint(130, -130, 60, 45, RAINY, seed=46)                       # Po Town
    t.paint(200, -110, 90, 50, RAINY, seed=47)                       # Route 17
    t.paint(250, -95, 50, 35, FLOWERS, seed=48)                      # Ula'ula Meadow
    t.paint(10, -420, 50, 40, GARDEN, seed=49)                       # Malie Garden
    t.paint(40, -320, 110, 70, TOWN, seed=50)
    t.paint(470, -470, 190, 190, SNOW, wobble=0.15, seed=51)
    t.paint(390, -180, 70, 55, VOLCANIC, seed=52)                    # Blush Mountain
    t.paint(170, -650, 90, 80, ROCKY, seed=53)
    t.paint(300, -600, 160, 120, FOREST, seed=54)
    t.cone(470, -470, 300, 170)                                      # Mount Lanakila
    t.cone(170, -660, 120, 102)                                      # Mount Hokulani
    t.hill(390, -180, 70, 26)                                        # Blush Mountain
    t.hill(830, -260, 120, 6, sharp=1.2)                             # dunes
    # ------------------------------------------------ Poni Island (SE)
    t.add_island(640, 600, 420, 320, rot=-0.05, seed=61)
    t.add_island(330, 460, 90, 90, seed=62)                          # Seafolk bay side
    t.add_island(575, 300, 80, 70, seed=63)                          # Ruins of Hope point
    t.add_island(920, 380, 110, 100, seed=64)                        # Battle Tree
    t.add_island(395, 205, 48, 40, seed=65, zone=BEACH)              # Exeggutor Island
    t.cut_bay(290, 505, 45, 35, seed=66)                             # Seafolk harbour
    t.paint(670, 520, 130, 150, CANYON, wobble=0.1, seed=67)
    t.paint(860, 640, 110, 90, SAVANNA, seed=68)
    t.paint(735, 790, 90, 60, FLOWERS, seed=69)
    t.paint(500, 700, 80, 70, JUNGLE, seed=70)
    t.mesa(670, 520, 115, 140, 92, seed=71)
    t.carve([(620, 575), (650, 540), (665, 500), (672, 470), (680, 445)], 16, 70)
    t.hill(905, 790, 45, 22)
    t.hill(575, 290, 40, 22)

    # ------------------------------------------------ flattened sites
    for name, (x, z, y) in TOWNS.items():
        if name in BUILT_ON_WATER:
            continue
        r = SITE_RADIUS.get(name, 24)
        if name in RECT_SITES:
            hw, hd = RECT_SITES[name]
            t.flatten(x - hw, z - hd, x + hw, z + hd, y, margin=18, zone=TOWN if name not in NATURAL_SITES else None)
        else:
            t.disk_flat(x, z, r, y, margin=14, zone=None if name in NATURAL_SITES else TOWN)


SITE_RADIUS = {
    "Iki Town": 46, "Ruins of Conflict": 16, "Verdant Cavern": 14, "Melemele Meadow": 20, "Ten Carat Hill": 18,
    "Kala'e Bay": 14, "Big Wave Beach": 16, "Route 2 Pokemon Center": 20, "Hau'oli Cemetery": 22,
    "Player's House": 16, "Kukui's Lab": 14, "Paniola Town": 44, "Paniola Ranch": 40, "Brooklet Hill": 16,
    "Wela Volcano Park": 26, "Route 8": 30, "Lush Jungle": 18, "Memorial Hill": 18, "Ruins of Life": 16,
    "Malie Garden": 36, "Mount Hokulani": 28, "Blush Mountain": 22, "Tapu Village": 34, "Haina Desert": 16,
    "Ruins of Abundance": 16, "Aether House": 16, "Ula'ula Meadow": 16, "Pokemon League": 34,
    "Poni Wilds": 14, "Hapu's House": 16, "Ruins of Hope": 16, "Exeggutor Island": 18, "Altar of the Sunne": 22,
    "Vast Poni Canyon": 16, "Poni Plains": 18, "Battle Tree": 38, "Poni Meadow": 18, "Resolution Cave": 12,
    "Poni Grove": 16, "Hano Grand Resort": 40, "Royal Avenue": 44,
}
RECT_SITES = {
    "Hau'oli City": (175, 38), "Hau'oli Marina": (30, 24), "Hau'oli Outskirts": (60, 20), "Heahea City": (80, 50),
    "Konikoni City": (70, 40), "Malie City": (90, 60), "Po Town": (48, 38), "Thrifty Megamart": (34, 26),
    "Seafolk Village": (40, 30), "Aether Paradise": (1, 1),
}
NATURAL_SITES = {
    "Verdant Cavern", "Melemele Meadow", "Ten Carat Hill", "Kala'e Bay", "Big Wave Beach", "Brooklet Hill",
    "Lush Jungle", "Haina Desert", "Ruins of Abundance", "Ula'ula Meadow", "Poni Wilds", "Vast Poni Canyon",
    "Poni Plains", "Poni Meadow", "Resolution Cave", "Poni Grove", "Exeggutor Island", "Wela Volcano Park",
    "Altar of the Sunne", "Mount Hokulani", "Blush Mountain", "Memorial Hill", "Ruins of Life", "Ruins of Hope",
    "Ruins of Conflict", "Pokemon League", "Aether Paradise",
}
BUILT_ON_WATER = {"Aether Paradise", "Seafolk Village"}
