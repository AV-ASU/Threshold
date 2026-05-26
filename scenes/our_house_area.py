"""outside_innkeeper_house (key: 'our_house_area') -- the gravel
yard behind the Clerk's house. The pickup truck is parked here.
A small woodshed off to the south holds the splitting axe. The dirt
road leaves east toward town; a path west connects to the river/
mistlands escape route.

The basement is reached from inside the Clerk's house (the
kitchen cellar hatch). A previous build placed a redundant cellar
bulkhead in this yard too -- removed because it created a one-way
trip (basement only exits via the kitchen ladder) and a duplicate
"door to the basement" two tiles outside the same building.

THRESHOLD reskin: original 'our_house_area' had two houses, a guard
patrol, a rust-key cellar gate, and bandit respawns after a guard
death. All cut. The second house is now a woodshed (no interior
scene, just an interactable door that yields the splitting axe).
Sheriff patrols this scene as part of his random outdoor route
(wired in Pass F).
"""
import math
import random
import pygame
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence


def _yard_cache_pickup(game):
    game.save.set_flag("yard_cache_taken", True)
    _evidence(game, "yard_cache",
        "A small stash."
    )


def build_our_house_area():
    # 24w x 18h. The Clerk's house occupies the upper-left quadrant
    # with a back door (H) into the kitchen. A woodshed sits in the
    # lower-left with a door (h) you interact with to take the axe. The
    # bulkhead cellar entry sits behind the house at the top of the
    # yard. The dirt road runs east-west across the middle.
    floor = [
        "gggggggggggggggggggggggg",   # 0
        "gggggggggggggggggggggggg",   # 1
        "gggggggggggggggggggggggg",   # 2
        "gggggggggggggggggggggggg",   # 3
        "gggggggggggggggggggggggg",   # 4
        "ggggggdddddddddddddddddd",   # 5  short stub dirt north of footpath
        "dddddddddddddddddddddddd",   # 6  3-tile dirt footpath
        "dddddddddddddddddddddddd",   # 7
        "dddddddddddddddddddddddd",   # 8
        "ggggggdddddddddddddddddd",   # 9  short stub south
        "gggggggggggggggggggggggg",   # 10
        "gggggggggggggggggggggggg",   # 11
        "gggggggggggggggggggggggg",   # 12
        "gggggggggggggggggggggggg",   # 13
        "gggggggggggggggggggggggg",   # 14
        "gggggggggggggggggggggggg",   # 15
        "gggggggggggggggggggggggg",   # 16
        "gggggggggggggggggggggggg",   # 17
    ]
    # THRESHOLD reskin: the tree perimeter is now a cornfield wall.
    # The yard sits inside the Clerk's crops; you can't see past
    # the stalks. The legacy yard woodshed is gone -- the only shed
    # is the locked one in the village/farm scene. The yard is now
    # just the inn's back door, the pickup truck, and open ground.
    objects = [
        "CCCCCCCCCCCCCCCCCCCCCCCC",   # 0
        "C......................C",   # 1
        "C..WWWWW...............C",   # 2  Clerk's house north wall
        "C..WrrrW...............C",   # 3  roof
        "C..WrrrW...............C",   # 4  roof
        "C..WWHWW...............C",   # 5  H = back door of the Clerk's house
        "a......................e",   # 6  west passage (river path)
        "a......................e",   # 7  east passage (cornfield_path)
        "a......................e",   # 8
        "C......................C",   # 9
        "C......................C",   # 10
        "C......................C",   # 11
        "C......................C",   # 12
        "C......................C",   # 13
        "C......................C",   # 14
        "C......................C",   # 15
        "C......................C",   # 16
        "CCCCCCCCCCCCCCCCCCCCCCCC",   # 17
    ]
    sc = Scene("our_house_area", floor, objects, music="village")
    # H = back door of the Clerk's house. Returns to 'house' scene
    # (the kitchen/living/hallway).
    sc.add_exit("H", "house", "from_our_house_area")
    # Outdoor passages: west to the country lane that leads to
    # village; east to the cornfield path that leads to the diner /
    # car. The lane is an intermediate scene so the village isn't
    # one step from the front yard.
    sc.add_exit("a", "country_lane", "from_our_house_area")
    sc.add_exit("e", "forest_path", "from_our_house_area")

    sc.set_spawn("default", 12, 7)
    sc.set_spawn("from_house", 5, 6)             # one south of back door
    sc.set_spawn("from_country_lane", 1, 7)      # one east of west passage
    sc.set_spawn("from_village", 1, 7)           # legacy save alias
    sc.set_spawn("from_forest", 22, 7)           # one west of east passage
    sc.set_spawn("from_river", 1, 7)             # west passage spawn alias
    sc.set_spawn("from_woodshed", 12, 7)         # legacy fallback

    # The pickup truck -- a decoration the player can SEE but not
    # use. The player's car (the escape vehicle) is at the
    # diner_gas_station; this truck is the Clerk's. Now drawn at
    # vehicle scale (~2 tiles wide); a 2x1 footprint of solid 'X'
    # invisible tiles under it makes the player bump correctly.
    sc.add_decoration(Decoration(20 * TILE + 16, 12 * TILE + 16,
                                 "pickup_truck"))
    objects = [list(r) for r in sc.objects]
    for tx in (19, 20, 21):
        if 0 <= tx < sc.w:
            objects[12][tx] = "X"
    sc.objects = objects

    # Hide spots: BESIDE the pickup truck (tile is solid now, so
    # the player has to crouch in the gap), in the back of the
    # yard against the corn perimeter, two more along the corn.
    sc.hide_spots = [
        (22 * TILE + 16, 12 * TILE + 16, "behind"),  # beside pickup
        (5 * TILE + 16, 15 * TILE + 16, "behind"),   # south corn band
        (15 * TILE + 16, 16 * TILE + 16, "behind"),  # south corn band
        (1 * TILE + 28, 10 * TILE + 16, "behind"),   # west corn band
    ]

    def _outside_interact(game):
        # No interactable shed in the yard anymore. The user-facing
        # shed lives in the village/farm scene. Yard is open ground.
        return
    sc.on_interact_fn = _outside_interact

    # Atmosphere -- chimney smoke from the house, a couple of crows,
    # scattered grass. No guard NPC. No bandit spawn.
    sc.add_decoration(Decoration(5 * TILE + 16, 2 * TILE - 6, "smoke"))
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE - 4, "lantern"))
    sc.add_decoration(Decoration(2 * TILE + 8, 0 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(20 * TILE + 8, 16 * TILE + 22, "crow"))
    # Yard dressing: a clothesline (banner deco) between two lantern
    # posts, a garden bloodstain near the woodshed (something happened
    # here), a creepy_tree at the NE corner of the yard, two dead
    # crows on the dirt road, a bloody handprint smearing the back
    # door. The Clerk's window has a faint passing-figure already
    # baked into the tile draw -- watch the south face of his house.
    sc.add_decoration(Decoration(10 * TILE + 16, 10 * TILE + 16,
                                 "banner", color=(220, 220, 200)))  # clothesline
    sc.add_decoration(Decoration(8 * TILE + 16, 10 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(12 * TILE + 16, 10 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(21 * TILE + 16, 2 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(17 * TILE + 16, 7 * TILE + 16, "dead_crow"))
    # Small mailbox on the road shoulder (use a gas_pump deco -- close
    # enough silhouette; future polish could carve a true mailbox).
    sc.add_decoration(Decoration(11 * TILE + 16, 9 * TILE + 16,
                                 "phantom_mark"))   # mark in the dirt
    rng = random.Random(2026)
    for _ in range(20):
        gx = rng.randint(1, 22) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, 16) * TILE + rng.randint(0, 30)
        tx_ = gx // TILE; ty_ = gy // TILE
        if 2 <= ty_ <= 5 and 3 <= tx_ <= 7: continue
        if 11 <= ty_ <= 14 and 3 <= tx_ <= 7: continue
        if 6 <= ty_ <= 8: continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))

    return sc


def build_woodshed():
    """The Clerk's woodshed interior. Single room. Splitting axe
    on the wall, a coil of rope on the workbench, a chopping stump in
    the centre. Locked from outside; the key is taken from the
    Clerk at night."""
    floor = ["=" * 8 for _ in range(6)]
    objects = [
        "WWWWWWWW",
        "W......W",
        "W.t....W",   # workbench (rope sits on this)
        "W......W",
        "W...h..W",   # h = exit door (back to the yard)
        "WWWWWWWW",
    ]
    sc = Scene("woodshed", floor, objects, music="home")
    # `h` exit always returns the player to the village/farm scene
    # now -- the yard shed has been removed, the village shed is
    # the only entry/exit.
    sc.add_exit("h", "village", "from_woodshed")
    sc.set_spawn("default",            4, 3)
    sc.set_spawn("from_village_shed",  4, 3)
    sc.set_spawn("from_yard",          4, 3)   # legacy fallback

    rope_pos   = (2 * TILE + 16, 2 * TILE + 16)
    axe_pos    = (5 * TILE + 16, 2 * TILE + 16)
    sc._rope_pos = rope_pos
    sc._axe_pos  = axe_pos
    # Sized workbench (the rope sits on it).
    sc.add_furniture("table", [(2, 2), (3, 2)], w=54, h=36)
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(4 * TILE + 20, 3 * TILE + 8, "bloodstain",
                                 scale=2.6))
    # It IS a woodshed: a split-wood stack against the west wall, a
    # kerosene lamp on the workbench, and cobwebs in the corners. The
    # firewood is collision furniture, set clear of the axe/rope/door.
    sc.add_furniture("firewood", [(1, 3), (1, 4)], w=24, h=58)
    sc.add_decoration(Decoration(3 * TILE + 16, 2 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(6 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (2 * TILE + 16, 3 * TILE + 16, "behind"),     # behind workbench
        (6 * TILE + 16, 1 * TILE + 24, "behind"),     # NE corner
    ]

    def _woodshed_interact(game):
        px, py = game.player.x, game.player.y
        # Axe on the wall.
        if abs(px - axe_pos[0]) < 36 and abs(py - axe_pos[1]) < 36:
            if not game.save.flag("axe_taken"):
                game.save.set_flag("axe_taken", True)
                game.player.inventory.add("lumber_axe", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("Splitting axe.")
                return
        # Rope on the bench.
        if abs(px - rope_pos[0]) < 36 and abs(py - rope_pos[1]) < 36:
            if not game.save.flag("rope_taken"):
                game.save.set_flag("rope_taken", True)
                game.player.inventory.add("rope", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("Coil of rope. Long enough for the well.")
                return
    sc.on_interact_fn = _woodshed_interact
    return sc
