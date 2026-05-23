"""village (key: 'village') -- the Innkeeper's farm.

This scene's six villager buildings have been scattered across the
mistlands; what remains here is the Innkeeper's land -- cornfields,
the woodshed, the well, the payphone, and a wheelbarrow of "rusted"
tools.

Cornstalks form the perimeter (replacing the old tree wall) and run
through the field as crop rows. The woodshed is the same interior
the yard's `our_house_area` already opens -- two doors, one shed.
"""
import math
import random
import pygame
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence


def build_village():
    # Floor: grass, with a worn dirt road running E-W (rows 6-8) and
    # short footpaths to the well, the woodshed, and the schoolhouse
    # path tile so the landmarks anchor.
    floor_rows = []
    for y in range(20):
        if 6 <= y <= 8:
            floor_rows.append(list("d" * 36))
        else:
            floor_rows.append(list("g" * 36))
    # Footpath south off the road to the well (col 16, rows 9..11).
    # The well sits just south of the road now -- a clear landmark on
    # entry rather than buried in the deep south of the field.
    for fy in range(9, 12):
        floor_rows[fy][16] = "d"
    # Footpath south-east to the woodshed door (col 24, rows 9..14)
    for fy in range(9, 15):
        floor_rows[fy][24] = "d"
    # Footpath south to the schoolhouse path tile (col 14, rows 9..15)
    for fy in range(9, 16):
        floor_rows[fy][14] = "d"
    floor = ["".join(r) for r in floor_rows]

    # Object map: corn perimeter (was trees), corn crop rows in the
    # north and south bands, the woodshed footprint south-east, and
    # exit tiles preserved.
    rows = []
    rows.append("C" * 36)                                   # 0
    for _ in range(5):                                       # 1..5
        rows.append("C" + "." * 34 + "C")
    rows.append("C" + "." * 34 + "e")                        # 6
    rows.append("C" + "." * 34 + "e")                        # 7
    rows.append("C" + "." * 34 + "e")                        # 8
    for _ in range(10):                                      # 9..18
        rows.append("C" + "." * 34 + "C")
    rows.append("C" * 36)                                    # 19

    rows = [list(r) for r in rows]
    # West-side debris piles -- still need the axe to clear at least
    # one to reach the mistlands.
    rows[6][0] = "*"
    rows[7][0] = "*"
    rows[8][0] = "*"
    # North passage to the gravel road -- a single 'a' tile in the
    # cornstalk wall above the well footpath. Player walks north
    # past the well to reach it.
    rows[0][17] = "a"
    # Schoolhouse footpath -- a "/" tile in the south band.
    rows[16][14] = "/"

    # Corn crop rows running E-W in the north and south bands. Each
    # crop row is a single tile of cornstalk with gaps so the player
    # can walk between rows. Avoid the road, the footpaths, the
    # well/payphone area, and the woodshed footprint.
    crop_north_rows = (2, 4)
    crop_south_rows = (10, 12, 18 - 1)   # 10, 12, 17
    crop_cols_blocked = {14, 16, 24}     # footpaths
    for ty in crop_north_rows:
        for tx in range(2, 34):
            if tx in crop_cols_blocked:
                continue
            if rows[ty][tx] == ".":
                # Punch gaps every 4 tiles so the player can move
                # between rows.
                if tx % 4 != 0:
                    rows[ty][tx] = "C"
    for ty in crop_south_rows:
        for tx in range(2, 34):
            if tx in crop_cols_blocked:
                continue
            if rows[ty][tx] == ".":
                if tx % 4 != 0:
                    rows[ty][tx] = "C"

    # Woodshed footprint south-east of the field. 5w x 4h, door 'h'
    # on north face. THIS is now the only woodshed -- the legacy
    # yard shed has been removed. Door is locked (gated by
    # woodshed_key, given by the Innkeeper on the liquor-crate
    # turn-in).
    shed_left, shed_right = 22, 26
    shed_top, shed_bot = 13, 16
    for cx in range(shed_left, shed_right + 1):
        rows[shed_top][cx] = "W"
        rows[shed_bot][cx] = "W"
    # Door at the north face -- col 24 (matches the footpath above).
    # `z` is the locked-door tile (solid; opens to the woodshed
    # only with the woodshed_key in inventory). The interaction is
    # handled in _village_interact below.
    rows[shed_top][24] = "z"
    for ry in (shed_top + 1, shed_top + 2):
        rows[ry][shed_left] = "W"
        rows[ry][shed_right] = "W"
        for cx in range(shed_left + 1, shed_right):
            rows[ry][cx] = "r"
    # Loot crate just west of the shed -- spare batteries inside.
    rows[16][21] = "K"

    objects = ["".join(r) for r in rows]

    sc = Scene("village", floor, objects, music="village")
    sc.add_exit("e", "country_lane",      "from_village")
    sc.add_exit("4", "mistlands",         "from_village")  # west, after debris
    sc.add_exit("/", "mistlands",         "from_village_road")  # old town road, into Brimley
    sc.add_exit("a", "gravel_road_north", "from_village")

    sc.set_spawn("default",                17, 7)
    sc.set_spawn("from_country_lane",      34, 7)
    sc.set_spawn("from_our_house_area",    34, 7)   # legacy save alias
    sc.set_spawn("from_mistlands",         2, 7)
    sc.set_spawn("from_well",              16, 9)    # climb out beside the well
    sc.set_spawn("from_woodshed",          24, 12)
    sc.set_spawn("from_schoolhouse",       14, 15)
    sc.set_spawn("from_town",              14, 15)
    sc.set_spawn("from_gravel_road",       17, 1)
    # Legacy spawns kept so old saves don't soft-lock to (0,0). They
    # all dump the player on the road by the well.
    for legacy in ("from_old_man_house", "from_shop", "from_kid_house",
                    "from_fisherman_cottage", "from_barn",
                    "from_haunted_house"):
        sc.set_spawn(legacy, 17, 7)

    # The well -- repositioned just south of the road (col 16, row 11)
    # so it reads as a landmark the moment the player walks in. It is
    # the ONLY way down into the Works.
    well_x = 16 * TILE + 16
    well_y = 11 * TILE + 16
    sc.add_decoration(Decoration(well_x, well_y, "well"))
    payphone_x = 8 * TILE + 16
    payphone_y = 13 * TILE + 16
    sc.add_decoration(Decoration(payphone_x, payphone_y, "payphone"))

    # The wheelbarrow of "rusted" tools, parked just outside the
    # woodshed door. The interaction notice contradicts the visible
    # rust -- "all of these rusted tools have been recently cleaned."
    barrow_x = 25 * TILE + 16
    barrow_y = 12 * TILE + 16
    sc.add_decoration(Decoration(barrow_x, barrow_y, "wheelbarrow"))
    sc._barrow_pos = (barrow_x, barrow_y)

    # Atmosphere: chimney smoke from the shed, crows on the corn
    # perimeter, lanterns on the road, a faint phantom_mark on the
    # footpath.
    sc.add_decoration(Decoration(24 * TILE + 16, 13 * TILE - 6, "smoke"))
    sc.add_decoration(Decoration(2 * TILE + 8, 0 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(33 * TILE + 8, 1 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(8 * TILE + 16, 18 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(10 * TILE + 16, 6 * TILE - 4, "lantern"))
    sc.add_decoration(Decoration(28 * TILE + 16, 6 * TILE - 4, "lantern"))
    sc.add_decoration(Decoration(15 * TILE + 16, 16 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(14 * TILE + 16, 13 * TILE + 16,
                                 "phantom_mark"))
    # A creepy_tree at each rear corner, a hanging figure deep in the
    # south corn (only visible from the right angle), dead crows.
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 22,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(33 * TILE + 16, 1 * TILE + 22,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(30 * TILE + 16, 18 * TILE + 22,
                                 "hanging_figure"))
    sc.add_decoration(Decoration(28 * TILE + 16, 8 * TILE + 16,
                                 "dead_crow"))
    # Two watching_wound cuts in the corn perimeter.
    sc.add_decoration(Decoration(0 * TILE + 24, 12 * TILE + 16,
                                 "watching_wound", size="small"))
    sc.add_decoration(Decoration(35 * TILE + 8,  4 * TILE + 16,
                                 "watching_wound", size="small"))
    # Boundary stones / scattered grass across the open field.
    for sx, sy in [(2, 10), (4, 13), (15, 11), (26, 11), (32, 12),
                   (3, 17), (29, 17), (30, 9), (33, 13)]:
        sc.add_decoration(Decoration(sx * TILE + 16, sy * TILE + 16,
                                     "grass_tuft"))
    # Liminal dressing: someone is hunting the vanished out here too --
    # a flyer nailed to the shed, another by the dead payphone -- and a
    # single chair sits in a gap in the corn where no chair belongs.
    sc.add_decoration(Decoration(25 * TILE + 16, 13 * TILE - 4, "missing_flyer"))
    sc.add_decoration(Decoration(6 * TILE + 16, 13 * TILE + 6, "missing_flyer"))
    sc.add_decoration(Decoration(20 * TILE + 16, 17 * TILE + 16, "small_chair"))

    # Hide spots: in the corn rows themselves and behind the shed.
    sc.hide_spots = [
        (4 * TILE + 16,  10 * TILE + 16, "behind"),   # north corn row
        (12 * TILE + 16, 12 * TILE + 16, "behind"),   # south corn row
        (28 * TILE + 16, 17 * TILE + 16, "behind"),   # south corn row
        (24 * TILE + 16, 17 * TILE + 16, "behind"),   # south of shed
        (well_x + 24, well_y, "behind"),              # behind the well
    ]

    def _village_interact(game):
        # Locked shed door -- requires woodshed_key (given by the
        # Innkeeper on liquor-crate turn-in). Once unlocked, the
        # door opens into the same `woodshed` interior the yard's
        # door used to open. Anti-softlock: once the polaroid is
        # taken, the lock forces open (anti-softlock).
        shed_door_x = 24 * TILE + 16
        shed_door_y = shed_top * TILE + 16
        if (abs(game.player.x - shed_door_x) < 40
                and abs(game.player.y - shed_door_y) < 40):
            unlocked = (game.player.inventory.has("woodshed_key")
                        or game.save.flag("polaroid_taken"))
            if not unlocked:
                game.audio.play("door_locked", 0.6)
                game.show_notice(
                    "Locked. The Innkeeper has the key.")
                return
            game.audio.play("door_open", 0.7)
            game.begin_transition("woodshed", "from_village_shed")
            return
        # Wheelbarrow -- the tools are visibly rusted, but the notice
        # contradicts what the player sees. The contradiction is the
        # whole gag.
        bx, by = sc._barrow_pos
        if abs(game.player.x - bx) < 36 and abs(game.player.y - by) < 36:
            game.show_notice(
                "All of these rusted tools have been recently cleaned.",
                duration=4.0,
            )
            if not game.save.flag("barrow_inspected"):
                game.save.set_flag("barrow_inspected", True)
                _evidence(game, "barrow_tools",
                    "Some old tools."
                )
            return
        # The well -- the only way down into the Works. Needs the rope
        # to rig the first descent; once tied, the rope stays as the
        # climb route (down AND back up) until the orb breaks it on a
        # later descent (handled in well_bottom's on_enter).
        if (abs(game.player.x - well_x) < 36
                and abs(game.player.y - well_y) < 36):
            if game.save.flag("well_rope_broken"):
                game.audio.play("door_locked", 0.6)
                game.show_notice("The rope's gone. There's no climbing "
                                 "back down.")
                return
            if game.save.flag("well_rope_tied"):
                game.audio.play("door_open", 0.7)
                game.begin_transition("well_bottom", "from_well")
                return
            if game.player.inventory.has("rope"):
                game.player.inventory.remove("rope", 1)
                game.save.set_flag("well_rope_tied", True)
                game.audio.play("door_open", 0.7)
                game.show_notice("You tie the rope and climb down.")
                game.begin_transition("well_bottom", "from_well")
                return
            game.audio.play("door_locked", 0.7)
            game.show_notice("Too deep without a rope.")
            return
        # Payphone.
        if (abs(game.player.x - payphone_x) < 36
                and abs(game.player.y - payphone_y) < 36):
            game.audio.play("door_distant", 0.6)
            if not game.save.flag("payphone_called"):
                game.save.set_flag("payphone_called", True)
                game.dialog.show([
                    "[c=dim](You pick up the phone.)[/c]",
                    "[c=dim]The line is dead.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
            else:
                game.dialog.show([
                    "[c=dim]The line is dead.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
            return
    sc.on_interact_fn = _village_interact

    def _village_on_enter(game, scene):
        # Persist any debris the player has chopped through. West-edge
        # debris (col 0) promotes to "4" (the mistlands exit char).
        for ty in range(scene.h):
            for tx in range(scene.w):
                if scene.objects[ty][tx] == "*":
                    if game.save.flag(f"debris_broken_village_{tx}_{ty}"):
                        scene.objects[ty][tx] = "4" if tx == 0 else "."
        # First-visit environmental beat: a single faint whisper
        # fires ~14s into the player's first time in the field.
        scene._village_first_t = 0.0
        scene._village_whisper_done = game.save.flag("village_whispered")

    def _village_on_update(game, scene, dt):
        if scene._village_whisper_done:
            return
        scene._village_first_t += dt
        if scene._village_first_t >= 14.0:
            scene._village_whisper_done = True
            game.save.set_flag("village_whispered", True)
            game.audio.play("whisper", 0.40)
    sc.on_enter_fn = _village_on_enter
    sc.on_update_fn = _village_on_update

    rng = random.Random(2027)
    for _ in range(28):
        gx = rng.randint(1, 34) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, 18) * TILE + rng.randint(0, 30)
        tx_ = gx // TILE; ty_ = gy // TILE
        if 6 <= ty_ <= 8: continue                      # road
        if shed_top <= ty_ <= shed_bot and shed_left <= tx_ <= shed_right:
            continue                                    # shed footprint
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))

    return sc
