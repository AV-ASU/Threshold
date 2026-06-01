"""outside_innkeeper_house (key: 'our_house_area') -- the gravel
yard behind the Clerk's house. The pickup truck is parked here.
A small woodshed off to the south holds the splitting axe. The dirt
road leaves east toward town; a path west connects to the river/
brimley escape route.

The basement is reached from inside the Clerk's house (the
kitchen cellar hatch). A previous build placed a redundant cellar
bulkhead in this yard too -- removed because it created a one-way
trip (basement only exits via the kitchen ladder) and a duplicate
"door to the basement" two tiles outside the same building.

THRESHOLD reskin: original 'our_house_area' had two houses, a patrol,
a rust-key cellar gate, and respawning enemies. All cut. The second house is now a woodshed (no interior
scene, just an interactable door that yields the splitting axe).
Sheriff patrols this scene as part of his random outdoor route
(wired in Pass F).
"""
import math
import random
from constants import TILE
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
    # The yard's open ground -- the permeable forest band is stamped
    # below. Lodge structure (W roof walls, H back door) preserved in
    # the protected ring; west/east passages stay clear.
    objects = [
        "........................",   # 0
        "........................",   # 1
        "...WWWWW................",   # 2  Clerk's house north wall
        "...WrrrW................",   # 3  roof
        "...WrrrW................",   # 4  roof
        "...WWHWW................",   # 5  H = back door of the Clerk's house
        "a......................e",   # 6  west passage (river path)
        "a......................e",   # 7  east passage (cornfield_path)
        "a......................e",   # 8
        "........................",   # 9
        "........................",   # 10
        "........................",   # 11
        "........................",   # 12
        "........................",   # 13
        "........................",   # 14
        "........................",   # 15
        "........................",   # 16
        "........................",   # 17
    ]
    sc = Scene("our_house_area", floor, objects, music="village")
    # The Lodge yard wraps on the x axis. The country lane comes in
    # from the west; walking east through or past the yard wraps back
    # to its west side. The road past the Lodge to the highway doesn't
    # exist in fiction -- there is no past-the-Lodge; the fold makes
    # sure of it.
    sc.wrap_x = True
    # H = back door of the Clerk's house. Returns to 'house' scene
    # (the kitchen/living/hallway).
    sc.add_exit("H", "house", "from_our_house_area")
    # Outdoor passages: west to the country lane that leads to
    # village; east to the cornfield path. The lane is an intermediate
    # scene so the village isn't one step from the front yard.
    sc.add_exit("a", "country_lane", "from_our_house_area")
    sc.add_exit("e", "forest_path", "from_our_house_area")
    # Direction-sensitive hidden fold: walking NORTH across the 'M'
    # tile (one of the yard's path tiles south of the Lodge) opens
    # onto Mara's arrival -- the night she walked up onto this porch
    # with a suitcase. From any other angle it's just yard floor.
    sc.add_exit("M", "lodge_arrival", "from_our_house_area",
                direction="north")
    # Carve the M tile into the yard at (5, 12), south of the Lodge
    # back door so the player passes it walking up to the porch.
    yard_obj = [list(r) for r in sc.objects]
    yard_obj[12][5] = "M"
    # ---- Permeable forest band ----
    # Replaces the old hard corn-wall perimeter. Same helper as brimley
    # so the visual treatment of the wrap is consistent. Lodge structure
    # + door passages stay protected.
    floor_ll_yd = [list(r) for r in sc.floor]
    YARD_W = len(yard_obj[0]); YARD_H = len(yard_obj)
    def _yd_protected(tx, ty):
        # West + east passage corridors (rows 6-8 deep into the band).
        if 6 <= ty <= 8:
            return True
        # Lodge structure footprint + porch approach.
        if 2 <= tx <= 7 and 2 <= ty <= 6:
            return True
        # The road row stub (5-9 north + south stubs of road).
        if 5 <= ty <= 9 and tx >= 5:
            return True
        # The 'M' directional tile + path to it.
        if tx == 5 and 9 <= ty <= 12:
            return True
        return False
    _yd_bushes = []
    from .base import scatter_forest_band
    scatter_forest_band(floor_ll_yd, yard_obj, YARD_W, YARD_H,
                        depth=3, seed=83,
                        tree_density=0.50, passable_ratio=0.65,
                        bush_density=0.18,
                        protected=_yd_protected,
                        place_bush=lambda px, py:
                            _yd_bushes.append((px, py)))
    sc.floor = floor_ll_yd
    sc.objects = yard_obj
    for bx, by in _yd_bushes:
        sc.add_decoration(Decoration(bx, by, "bush"))

    sc.set_spawn("default", 12, 7)
    sc.set_spawn("from_house", 5, 6)             # one south of back door
    sc.set_spawn("from_country_lane", 1, 7)      # one east of west passage
    sc.set_spawn("from_village", 1, 7)           # legacy save alias
    sc.set_spawn("from_forest", 22, 7)           # one west of east passage
    sc.set_spawn("from_river", 1, 7)             # west passage spawn alias
    sc.set_spawn("from_woodshed", 12, 7)         # legacy fallback
    # Return spawn from the lodge_arrival fold -- lands the player
    # one tile south of the directional M tile so they don't
    # immediately re-trigger the fold.
    sc.set_spawn("from_lodge_arrival", 5, 13)

    # The pickup truck -- a decoration the player can SEE but not
    # use. The player's car (the escape vehicle) is on the Brimley
    # east bank; this truck is the Clerk's. Now drawn at
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
        px, py = game.player.x, game.player.y
        # Bloody handprint on the back door -- atmosphere, not a clue.
        # show_notice keeps it as a corner-line that doesn't interrupt
        # play with a full dialog pop.
        hx, hy = sc._handprint_pos
        if abs(px - hx) < 48 and abs(py - hy) < 48:
            game.show_notice(
                "Handprint on the back door. Palm-out. Someone leaving.")
            return
        # The Clerk's pickup is visible-but-useless. Examining it turns
        # the noun into worldbuilding: he doesn't drive it because there
        # is nowhere in Brimley for him to go.
        tx, ty = 20 * TILE + 16, 12 * TILE + 16
        if abs(px - tx) < 56 and abs(py - ty) < 56:
            game.show_notice(
                "The Clerk's truck. He doesn't drive it. None of them do.")
    sc.on_interact_fn = _outside_interact

    # Atmosphere -- chimney smoke from the house, a couple of crows,
    # scattered grass. No patrol NPC. No enemy spawn.
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
    # Bloody handprint smearing the south face of the Clerk's house,
    # right by the back door (col 5, row 5). The comment above this
    # block has long promised one; the prop is finally placed, and the
    # yard's interact gives it a voice.
    handprint_x = 6 * TILE + 16
    handprint_y = 5 * TILE + 28
    sc.add_decoration(Decoration(handprint_x, handprint_y, "bloodstain",
                                 scale=0.9))
    sc._handprint_pos = (handprint_x, handprint_y)
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
    """A woodshed off the village crossroads (where it actually sits --
    not the Arcadia yard). Single room: splitting axe on the wall, a coil
    of rope on the workbench, a chopping stump in the centre. Locked from
    outside; the Clerk keeps the key (found in his cellar)."""
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
    sc.add_exit("h", "brimley", "from_woodshed")
    sc.set_spawn("default",            4, 3)
    sc.set_spawn("from_brimley_shed",  4, 3)
    sc.set_spawn("from_village_shed",  4, 3)   # legacy fallback
    sc.set_spawn("from_yard",          4, 3)   # legacy fallback

    rope_pos   = (2 * TILE + 16, 2 * TILE + 16)
    axe_pos    = (5 * TILE + 16, 2 * TILE + 16)
    flash_pos  = (3 * TILE + 16, 4 * TILE + 16)   # on the chopping stump
    sc._rope_pos = rope_pos
    sc._axe_pos  = axe_pos
    sc._flash_pos = flash_pos
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
        # Flashlight left on the chopping stump in the centre.
        if abs(px - flash_pos[0]) < 36 and abs(py - flash_pos[1]) < 36:
            if not game.save.flag("flashlight_taken"):
                game.save.set_flag("flashlight_taken", True)
                game.player.inventory.add("flashlight", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("A flashlight. Press [F] in the dark -- "
                                 "but light draws the eye.")
                return
    sc.on_interact_fn = _woodshed_interact

    def _woodshed_on_enter(game, scene):
        # The axe, rope and flashlight had no world object AND no [E] cue
        # -- three critical items you'd walk right past. Glimmer-mark each
        # one still on offer and register it for the [E] prompt; drop the
        # marker once it's been taken.
        for pos, flag in ((axe_pos, "axe_taken"),
                          (rope_pos, "rope_taken"),
                          (flash_pos, "flashlight_taken")):
            if not game.save.flag(flag):
                scene.add_decoration(Decoration(pos[0], pos[1], "item_drop"))
                scene.add_interactable(pos[0], pos[1], 36)
        # A box of cartridges by the hunting gear (this is a hunting town).
        from .base import drop_ammo_cache
        drop_ammo_cache(game, scene, 4, 3, 6, "ammo_woodshed")
    sc.on_enter_fn = _woodshed_on_enter
    return sc
