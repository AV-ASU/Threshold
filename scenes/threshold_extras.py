"""Additional scenes added to the registry.

  schoolhouse        -- one-room schoolhouse, empty for months.
  graveyard          -- behind the church. One readable headstone.
"""
import math
import random
import pygame
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence


def _backwoods_note_pickup(game):
    game.save.set_flag("backwoods_note_taken", True)
    _evidence(game, "backwoods_note",
        "A small stash.")


def _forest_cache_pickup(game):
    game.save.set_flag("forest_cache_taken", True)
    _evidence(game, "forest_cache",
        "A small stash."
    )


def _school_cache_pickup(game):
    game.save.set_flag("school_cache_taken", True)
    _evidence(game, "school_cache",
        "A small stash."
    )


def build_schoolhouse():
    """One-room rural schoolhouse on the edge of town. Closed for
    months. A small desk at the front of the room. Hide spots: in
    the coat closet, under the teacher's desk, behind the storage
    shelf at the back."""
    floor = ["=" * 14 for _ in range(10)]
    objects = [
        "WWWWiWWWWWWWWW",   # 0  window
        "W............W",   # 1
        "W..t.........W",   # 2  teacher's desk (table sprite)
        "W..c.........W",   # 3  teacher's chair
        "W............W",   # 4
        "W..tt..tt....W",   # 5  student desks
        "W..cc..cc....W",   # 6
        "W..tt..tt....W",   # 7
        "W..cc..cc..s.W",   # 8  storage shelf at back
        "WWWWWWHWWWWWWW",   # 9  H = exit south back to town (col 6,
                            #     aligned with the central aisle so
                            #     the door isn't blocked by a chair)
    ]
    sc = Scene("schoolhouse", floor, objects, music="home")
    # The schoolhouse stands on the Brimley bank now; its door opens
    # back onto the field.
    sc.add_exit("H", "mistlands", "from_school")
    # The original spawn at (7, 7) was inside a student desk
    # (boxed in three sides). Spawn in the centre aisle at row 8.
    sc.set_spawn("default", 6, 8)
    sc.set_spawn("from_mistlands", 6, 8)        # arrive from Brimley
    sc.set_spawn("from_village", 6, 8)
    sc.set_spawn("from_town_crossroads", 6, 8)
    sc.set_spawn("from_town", 6, 8)

    # Chalk marks on the walls.
    sc.add_decoration(Decoration(13 * TILE + 4, 2 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(0 * TILE + 28, 7 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 28,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(10 * TILE + 16, 0 * TILE + 28,
                                 "phantom_mark"))

    # A clock that's stopped, a candle, motes.
    sc.add_decoration(Decoration(7 * TILE + 16, 1 * TILE + 22, "clock"))
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(11 * TILE + 16,  0 * TILE + 22 , "candle"))
    for i in range(6):
        sc.add_decoration(Decoration(50 + i * 60,
                                     80 + (i % 3) * 50, "mote"))

    # The teacher's desk has the kid's report-card -- a generic
    # "photo" decoration the player can interact with, generating
    # an evidence beat once.
    desk_x = 3 * TILE + 16
    desk_y = 3 * TILE + 16
    sc._teacher_desk = (desk_x, desk_y)

    sc.hide_spots = [
        (3 * TILE + 16, 3 * TILE + 24, "under"),     # teacher's desk
        (11 * TILE + 16, 8 * TILE + 24, "behind"),   # storage shelf
        (1 * TILE + 28, 5 * TILE + 16, "behind"),    # against the west wall
    ]

    # Boarded NE alcove: the teacher boarded over a corner cubby
    # before she vanished. (12,1) is the boarded panel; (12,2) is
    # newly walled so the alcove is a true 1-tile pocket. Behind it,
    # a torn diary page in her handwriting.
    sc.objects[1][12] = "q"
    sc.objects[2][12] = "W"

    def _schoolhouse_on_enter(game, scene):
        if not game.save.flag("school_cache_taken"):
            scene.add_item(
                12 * TILE + 16, 1 * TILE + 16, "diary_page_2",
                on_pickup=_school_cache_pickup,
            )
    sc.on_enter_fn = _schoolhouse_on_enter

    def _schoolhouse_interact(game):
        if (abs(game.player.x - desk_x) < 36
                and abs(game.player.y - desk_y) < 36):
            if not game.save.flag("school_desk_searched"):
                game.save.set_flag("school_desk_searched", True)
                _evidence(game, "school_desk",
                    "Just papers."
                )
            else:
                game.show_notice("Just papers.")
    sc.on_interact_fn = _schoolhouse_interact

    return sc


def build_country_lane():
    """A worn rural road between the Clerk's yard and the town
    crossroads. Long thin scene -- 32 wide x 12 tall -- so the
    walk feels like time passing rather than a single doorway. The
    road itself is a 3-tile dirt strip in the middle; corn / wild
    grass on either side; a busted wooden fence runs along the
    south edge. A single creepy_tree on the north side at midway.

    Two exits: west `a` -> village (from_country_lane), east `e` ->
    our_house_area (from_country_lane). No interior building, no
    NPCs by default; the Sheriff patrol can pass through here as
    part of his route (already wired by tag, no extra work).
    """
    W, H = 32, 12
    floor_rows = []
    for y in range(H):
        if 5 <= y <= 7:
            floor_rows.append("d" * W)
        else:
            floor_rows.append("g" * W)
    objects_l = []
    for y in range(H):
        if y < 2 or y >= H - 2:
            # THRESHOLD: country lane is now flanked by cornfields,
            # not woods. Tree perimeter replaced with cornstalk.
            row = ["C"] * W
        else:
            row = ["."] * W
            row[0] = "C"
            row[W - 1] = "C"
        objects_l.append(row)
    # West passage (a) -- to village
    for dy in (-1, 0, 1):
        objects_l[6 + dy][0] = "a"
    # East passage (e) -- to our_house_area
    for dy in (-1, 0, 1):
        objects_l[6 + dy][W - 1] = "e"
    # Loot crate against the south corn band -- a stash someone
    # left for an arranged pickup that never came. Holds a
    # diary page (per CRATE_LOOT).
    objects_l[4][8] = "K"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("country_lane", floor_rows, objects, music="outside")
    sc.add_exit("a", "village", "from_country_lane")
    sc.add_exit("e", "our_house_area", "from_country_lane")
    sc.set_spawn("default", 1, 6)
    # Player walked WEST out of our_house_area: lands at the east
    # end of the lane, facing west toward town.
    sc.set_spawn("from_our_house_area", W - 2, 6)
    # Player walked EAST out of village: lands at the west end of
    # the lane, facing east toward home.
    sc.set_spawn("from_village", 1, 6)

    # Atmosphere -- corn tufts on both sides of the road, a few
    # crows, a leaning fence post deco, one creepy_tree, a dead
    # crow on the road, a missing-flyer pinned to a fence.
    rng = random.Random(2028)
    for _ in range(36):
        gx = rng.randint(2, W - 3) * TILE + rng.randint(0, 30)
        gy = rng.randint(0, H - 1) * TILE + rng.randint(0, 30)
        ty_ = gy // TILE
        if 5 <= ty_ <= 7:   # keep the road clear
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.add_decoration(Decoration(8 * TILE + 8, 1 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(22 * TILE + 8, 10 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(15 * TILE + 16, 1 * TILE + 28,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(18 * TILE + 16, 7 * TILE + 22,
                                 "dead_crow"))
    sc.add_decoration(Decoration(11 * TILE + 16, 9 * TILE + 16,
                                 "missing_flyer"))
    # Hide spots colocated with cover (cornstalks).
    sc.hide_spots = [
        (5 * TILE + 16, 3 * TILE + 16, "behind"),
        (12 * TILE + 16, 9 * TILE + 16, "behind"),
        (24 * TILE + 16, 3 * TILE + 16, "behind"),
    ]
    return sc


def build_graveyard():
    """Small graveyard behind the church. Iron fence, two crooked
    rows of headstones. One stone near the gate can be read.

    Hide spots: behind the larger headstones, in the gardener's
    shed at the back.
    """
    floor = ["g" * 14 for _ in range(10)]
    objects = [
        "TTTTTTTTTTTTTT",   # 0  trees behind the fence
        "T............T",   # 1
        "T..R..R..R...T",   # 2  headstones (rocks)
        "T............T",   # 3
        "T..R..R..R...T",   # 4
        "T............T",   # 5
        "T..R..R..R...T",   # 6
        "T............T",   # 7
        "T............T",   # 8
        "TTTTTTTTHTTTTT",   # 9  H = exit south back to town
    ]
    sc = Scene("graveyard", floor, objects, music="village")
    # Exit back into the church (the gate is in the back of the
    # parsonage). Routes to old_man_house, which has spawn
    # 'from_graveyard' set up.
    sc.add_exit("H", "old_man_house", "from_graveyard")
    sc.set_spawn("default", 7, 7)
    sc.set_spawn("from_church", 7, 7)
    sc.set_spawn("from_town_crossroads", 7, 7)

    # A worn, anonymous headstone -- the leftmost top row.
    worn_stone = (3 * TILE + 16, 2 * TILE + 16)
    sc._worn_stone = worn_stone
    # Three crooked headstones, middle row -- names long gone.
    sc._grave_stones = [
        (3 * TILE + 16, 4 * TILE + 16),
        (6 * TILE + 16, 4 * TILE + 16),
        (9 * TILE + 16, 4 * TILE + 16),
    ]

    # Bloodstain near the back row -- a fresh disturbance.
    sc.add_decoration(Decoration(6 * TILE + 16, 6 * TILE + 24,
                                 "bloodstain"))
    # Crows on the fence line, plus a dead crow on the worn plot.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(worn_stone[0] - 12,
                                 worn_stone[1] + 18, "dead_crow"))
    # A lone candle on the worn stone -- still burning.
    sc.add_decoration(Decoration(worn_stone[0], worn_stone[1] - 8,
                                 "candle"))
    # A leaning creepy_tree at the back of the plot, a hanging
    # figure visible behind the north tree wall (something's
    # wrong here too), and a bloody handprint on the rear stone.
    sc.add_decoration(Decoration(11 * TILE + 16, 7 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 28,
                                 "hanging_figure"))
    # (Bloody handprint on the rear stone removed -- the hanging
    # figure + creepy_tree + fresh dirt already do the work.)
    # Phantom-mark sigils on a few stones (chalk, not eyeballs).
    sc.add_decoration(Decoration(6 * TILE + 16, 4 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(9 * TILE + 16, 4 * TILE + 16,
                                 "phantom_mark"))
    # More grass tufts so the field doesn't read empty.
    rng = random.Random(2028)
    for _ in range(20):
        gx = rng.randint(2, 11) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, 8) * TILE + rng.randint(0, 30)
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))

    sc.hide_spots = [
        (6 * TILE + 16, 6 * TILE + 24, "behind"),     # middle row stones
        (9 * TILE + 16, 2 * TILE + 24, "behind"),     # rear row stones
        (1 * TILE + 28, 7 * TILE + 16, "behind"),     # west fence
    ]

    # Boarded-over panel of nailed planks set into the east iron-fence/
    # tree line -- a chop-target for the axe that opens onto an empty,
    # long-looted pocket. (Whatever was cached here is long gone.)
    sc.objects[7][13] = "q"

    def _graveyard_interact(game):
        # The worn anonymous headstone.
        mx, my = sc._worn_stone
        if (abs(game.player.x - mx) < 36
                and abs(game.player.y - my) < 36):
            if not game.save.flag("read_worn_stone"):
                game.save.set_flag("read_worn_stone", True)
                game.audio.play("low_pulse", 0.35)
                game.dialog.show([
                    "[c=dim](A weather-worn headstone.)[/c]",
                    "[c=dim]The name has worn away.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                _evidence(game, "worn_stone",
                    "A weathered headstone."
                )
            else:
                game.dialog.show([
                    "[c=dim]A worn headstone.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
            return
        # Other stones -- any of the three.
        for i, (sx, sy) in enumerate(sc._grave_stones):
            if (abs(game.player.x - sx) < 36
                    and abs(game.player.y - sy) < 36):
                game.dialog.show([
                    "[c=dim](A fresh stone.)[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
    sc.on_interact_fn = _graveyard_interact

    return sc


def build_gravel_road_north():
    """Long thin gravel road running north out of town. South exit
    `a` returns to village; north exit `e` reaches backwoods_cabin.
    Tall scene (14 wide x 22 tall) so the walk feels like distance.
    Cornstalks + dead crows on either side; no NPC by default. The
    Choir and Hound patrols both spawn here as part of their route
    (wired via `_sheriff_scenes` in systems/game.py)."""
    W, H = 14, 22
    floor_rows = []
    for y in range(H):
        row = []
        for x in range(W):
            if 6 <= x <= 8:
                row.append("d")            # gravel road through middle
            else:
                row.append("g")
        floor_rows.append("".join(row))
    objects_l = []
    for y in range(H):
        if y < 1 or y >= H - 1:
            row = ["T"] * W
        else:
            row = ["."] * W
            row[0] = "T"
            row[W - 1] = "T"
        objects_l.append(row)
    # North exit (e) -> backwoods_cabin. South exit (a) -> village.
    objects_l[0][7] = "e"
    objects_l[H - 1][7] = "a"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("gravel_road_north", floor_rows, objects, music="outside")
    sc.add_exit("e", "backwoods_cabin", "from_road")
    sc.add_exit("a", "village", "from_gravel_road")
    sc.set_spawn("default", 7, H - 2)
    sc.set_spawn("from_village", 7, H - 2)
    sc.set_spawn("from_backwoods_cabin", 7, 1)

    rng = random.Random(2031)
    for _ in range(50):
        gx = rng.randint(1, W - 2) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, H - 2) * TILE + rng.randint(0, 30)
        tx_ = gx // TILE
        if 6 <= tx_ <= 8:
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.add_decoration(Decoration(2 * TILE + 16, 4 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(11 * TILE + 16, 14 * TILE + 16, "creepy_tree"))
    sc.add_decoration(Decoration(7 * TILE + 16, 11 * TILE + 16, "dead_crow"))
    sc.add_decoration(Decoration(3 * TILE + 8, 1 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(10 * TILE + 8, 19 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(7 * TILE + 16, 8 * TILE + 16,
                                 "phantom_mark"))
    # Boarded-over panel of nailed planks set into the east tree line at
    # midway -- a chop-target that opens onto an empty, long-looted alcove.
    sc.objects[10][13] = "q"

    sc.hide_spots = [
        (3 * TILE + 16, 6 * TILE + 16, "behind"),
        (10 * TILE + 16, 12 * TILE + 16, "behind"),
        (3 * TILE + 16, 16 * TILE + 16, "behind"),
    ]
    return sc


def build_backwoods_cabin():
    """The Hunter's bunkhouse. Small log cabin sitting in a clearing
    at the north end of the gravel road. Door is a facade `l` --
    the cabin doesn't model an interior. Tally-marks on the wall
    (decoration) and a notepad on a stump out front (interactable
    evidence). Behind the cabin: a stack of cordwood (visible
    cover) and a hide spot. The Hunter patrol prefers this scene
    when it's roaming -- the cabin is its home base."""
    W, H = 16, 12
    floor_rows = []
    for y in range(H):
        row = []
        for x in range(W):
            if y == H - 1:
                row.append("g")
            elif 4 <= x <= 11 and 3 <= y <= 7:
                row.append("=")            # cabin interior floor
            else:
                row.append("g")
            # Worn dirt path approaching from south
            if 7 <= x <= 8 and 8 <= y <= 11:
                row[-1] = "d"
        floor_rows.append("".join(row))
    objects_l = []
    for y in range(H):
        if y == 0 or y == H - 1:
            row = ["T"] * W
        else:
            row = ["."] * W
            row[0] = "T"
            row[W - 1] = "T"
        objects_l.append(row)
    # Cabin footprint: cols 4-11, rows 3-7. Door `l` (facade) on
    # south face row 7 col 7. Roof tiles inside.
    for cx in range(4, 12):
        objects_l[3][cx] = "W"
        objects_l[7][cx] = "W"
    for ry in (4, 5, 6):
        objects_l[ry][4] = "W"
        objects_l[ry][11] = "W"
        for cx in range(5, 11):
            objects_l[ry][cx] = "r"
    objects_l[3][7] = "i"                # window on north face
    objects_l[7][7] = "D"                # door to interior (south face)
    # South exit `H` to gravel_road_north.
    objects_l[H - 1][7] = "H"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("backwoods_cabin", floor_rows, objects, music="outside")
    sc.add_exit("H", "gravel_road_north", "from_backwoods_cabin")
    sc.add_exit("D", "backwoods_cabin_interior", "from_outside")
    sc.set_spawn("default", 7, 9)
    sc.set_spawn("from_road", 7, 9)
    sc.set_spawn("from_gravel_road_north", 7, 9)
    sc.set_spawn("from_interior", 7, 8)

    # Tally-mark sigil (phantom_mark stand-in) on the south face
    # of the cabin, beside the door. Animal traps in the yard.
    # Hanging figure visible in the trees behind. A crow on the
    # roof. Dead crow at the threshold.
    sc.add_decoration(Decoration(5 * TILE + 16, 7 * TILE + 22,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(10 * TILE + 16, 7 * TILE + 22,
                                 "claw_marks"))
    sc.add_decoration(Decoration(2 * TILE + 16, 9 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(13 * TILE + 16, 2 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 28,
                                 "hanging_figure"))
    sc.add_decoration(Decoration(7 * TILE + 8, 3 * TILE + 16, "crow"))
    sc.add_decoration(Decoration(7 * TILE + 16, 8 * TILE + 22,
                                 "dead_crow"))
    # Cordwood stack behind the cabin (west of door).
    sc.objects[8][3] = "t"
    sc.add_decoration(Decoration(2 * TILE + 16, 9 * TILE + 16, "lantern"))
    # Notepad on a stump out front.
    notepad_x = 10 * TILE + 16
    notepad_y = 9 * TILE + 16
    sc._notepad_pos = (notepad_x, notepad_y)
    sc.add_decoration(Decoration(notepad_x, notepad_y, "wrong_photo"))
    # Grass / motes
    rng = random.Random(2032)
    for _ in range(18):
        gx = rng.randint(1, W - 2) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, H - 2) * TILE + rng.randint(0, 30)
        ty_ = gy // TILE
        tx_ = gx // TILE
        if 3 <= ty_ <= 7 and 4 <= tx_ <= 11:   # keep cabin clear
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.hide_spots = [
        (3 * TILE + 16, 8 * TILE + 16, "behind"),     # cordwood
        (12 * TILE + 16, 5 * TILE + 16, "behind"),    # east of cabin
        (1 * TILE + 28, 6 * TILE + 16, "behind"),     # west tree line
    ]

    def _backwoods_interact(game):
        nx, ny = sc._notepad_pos
        if (abs(game.player.x - nx) < 40
                and abs(game.player.y - ny) < 40):
            if not game.save.flag("backwoods_note_taken"):
                _backwoods_note_pickup(game)
            else:
                game.show_notice("You've read enough.")
    sc.on_interact_fn = _backwoods_interact
    return sc


def build_backwoods_cabin_interior():
    """A cabin interior. Chair tipped, cup on the floor, a smear on
    the boards. The cellar key is on the floor. The door was left
    open."""
    floor = ["=" * 8 for _ in range(7)]
    objects = [
        "WWWWWWWW",
        "W..t...W",
        "W......W",
        "W......W",
        "W......W",
        "W...D..W",
        "WWWWWWWW",
    ]
    sc = Scene("backwoods_cabin_interior", floor, objects, music="home")
    sc.add_exit("D", "backwoods_cabin", "from_interior")
    sc.set_spawn("default",     4, 4)
    sc.set_spawn("from_outside", 4, 4)
    sc.add_decoration(Decoration(3 * TILE + 16, 1 * TILE + 6, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 3 * TILE + 16,
                                 "overturned_chair"))
    sc.add_decoration(Decoration(5 * TILE + 16, 3 * TILE + 22,
                                 "bowl", filled=False))
    sc.add_decoration(Decoration(4 * TILE + 16, 4 * TILE + 16,
                                 "bloodstain"))
    sc.add_decoration(Decoration(6 * TILE + 16, 1 * TILE + 24,
                                 "claw_marks"))
    sc.hide_spots = [
        (1 * TILE + 24, 1 * TILE + 24, "behind"),
        (6 * TILE + 16, 4 * TILE + 16, "behind"),
    ]
    return sc


def build_river_crossing():
    """Plank footbridge across the mistlands river. South exit `a`
    returns to mistlands; north end of the scene is a small bank
    with a boarded cache pocket gated by `q`. Atmospheric: rotted
    boards, dead crows on the rails, fog. Sheriff patrols here too
    (the bridge is a bottleneck that suits a roving deputy).

    Layout (24 wide x 14 tall):
      - River runs N-S through cols 11-13.
      - Plank bridge across rows 6-7 at the river cols.
      - Player enters at south end of bridge (col 12, row 13).
      - North bank (rows 1-5) holds the boarded cache pocket at
        col 12 row 1 (gated by `q`).
    """
    W, H = 24, 14
    river_cols = (11, 12, 13)
    bridge_rows = (6, 7)
    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if tx in river_cols and ty not in bridge_rows:
                row.append("~")            # river water
            else:
                row.append("g")
        floor_rows.append("".join(row))
    objects_l = []
    for ty in range(H):
        row = ["."] * W
        if ty == 0 or ty == H - 1:
            row = ["T"] * W
            for cx in river_cols:
                row[cx] = "."             # leave river open at edges
        else:
            row[0] = "T"
            row[-1] = "T"
        if ty in bridge_rows:
            for cx in river_cols:
                row[cx] = "$"             # bridge plank
        objects_l.append(row)
    # South exit (back to mistlands) -- one passage tile at the
    # south river opening.
    objects_l[H - 1][12] = "a"
    # North-bank cache: a `q` boarded panel set into the north
    # tree line at col 5, with a 1-tile alcove pocket.
    objects_l[0][5] = "q"
    # Sigil on the bridge midway.
    objects = ["".join(r) for r in objects_l]
    sc = Scene("river_crossing", floor_rows, objects, music="wind")
    sc.add_exit("a", "mistlands", "from_river_crossing")
    sc.set_spawn("default", 12, H - 2)
    sc.set_spawn("from_mistlands", 12, H - 2)

    # Decorations: dead crow on the rail, fog motes, a hanging
    # figure visible in the north trees, a creepy_tree on the
    # west bank, one bloody handprint on the south end of the
    # bridge (someone bled crossing).
    sc.add_decoration(Decoration(12 * TILE + 16, 7 * TILE + 22,
                                 "dead_crow"))
    sc.add_decoration(Decoration(3 * TILE + 16, 3 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(20 * TILE + 16, 3 * TILE + 16,
                                 "creepy_tree"))
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 28,
                                 "hanging_figure"))
    sc.add_decoration(Decoration(12 * TILE + 16, 8 * TILE + 16,
                                 "bloody_handprint"))
    for i in range(10):
        sc.add_decoration(Decoration(40 + i * 50,
                                     90 + (i % 4) * 50, "mote"))
    rng = random.Random(2033)
    for _ in range(20):
        gx = rng.randint(1, W - 2) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, H - 2) * TILE + rng.randint(0, 30)
        tx_ = gx // TILE
        if tx_ in river_cols:
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))

    # Boarded-over panel at col 5 row 0 -- a chop-target that opens onto
    # an empty, long-looted pocket.

    sc.hide_spots = [
        (3 * TILE + 16, 5 * TILE + 16, "behind"),     # west bank trees
        (20 * TILE + 16, 5 * TILE + 16, "behind"),    # east bank trees
        (3 * TILE + 16, 11 * TILE + 16, "behind"),    # west south bank
    ]
    return sc


def build_bell_tower():
    """Top of the church bell tower. A small square room with a
    bell at centre, four narrow window slits looking out over
    the town. Stairs `L` (ladder_down) on the south back to the
    church. The view delivers one evidence beat the first time
    the player climbs up: at night, lights move on every street
    even though nobody is supposed to be out.

    Layout (10 wide x 8 tall): all wall border. Bell decoration
    at (5, 3). Hide spot behind the bell hoist."""
    W, H = 10, 8
    floor_rows = ["=" * W for _ in range(H)]
    objects_l = []
    for y in range(H):
        if y == 0 or y == H - 1:
            row = ["W"] * W
        else:
            row = ["."] * W
            row[0] = "W"
            row[W - 1] = "W"
        objects_l.append(row)
    # Window slits in the four cardinal walls.
    objects_l[0][2] = "i"
    objects_l[0][7] = "i"
    objects_l[H - 1][2] = "i"
    objects_l[H - 1][7] = "i"
    objects_l[3][0] = "i"
    objects_l[3][W - 1] = "i"
    # Stairs back down to the church.
    objects_l[H - 1][7] = "L"        # overrides the south slit at (7, H-1)
    objects = ["".join(r) for r in objects_l]
    sc = Scene("bell_tower", floor_rows, objects, music="home")
    sc.add_exit("L", "old_man_house", "from_bell_tower")
    sc.set_spawn("default", 5, H - 2)
    sc.set_spawn("from_church", 6, H - 2)
    # The bell at centre. Use a heavy table sprite plus a chair
    # underneath as a stand-in -- we don't have a `bell` deco.
    bell_x = 5 * TILE + 16
    bell_y = 3 * TILE + 16
    sc.add_decoration(Decoration(bell_x, bell_y, "lantern"))
    sc.add_decoration(Decoration(bell_x, bell_y + 18, "rope"))
    sc.objects[3][5] = "t"           # bell hoist (solid prop)
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16,
                                 "phantom_mark"))
    for i in range(8):
        sc.add_decoration(Decoration(40 + i * 30,
                                     50 + (i % 3) * 40, "mote"))
    sc.hide_spots = [
        (4 * TILE + 16, 3 * TILE + 16, "behind"),    # behind the hoist
        (6 * TILE + 16, 3 * TILE + 16, "behind"),    # other side of hoist
    ]

    def _bell_tower_on_enter(game, scene):
        if game.save.flag("bell_tower_seen"):
            return
        game.save.set_flag("bell_tower_seen", True)
        # First visit: a single evidence beat from the lookout.
        _evidence(game, "bell_tower_view",
                  "From the bell tower the town is small.")
    sc.on_enter_fn = _bell_tower_on_enter
    return sc


def build_cornfield_maze():
    """Deeper into the cornfield from the cornfield path. Walls of
    head-high corn on every side; narrow lanes between rows; the
    sky is the only thing you can see over the stalks. A scarecrow
    at the centre that isn't quite where it was a moment ago.
    Two exits: south `!` back to forest_path; north `^` continues
    into the mistlands -- the maze led you somewhere wrong.
    Lanes are dotted with `:` corn patches: walk into one and
    you're hidden, but only as long as you stay in the patch."""
    W, H = 20, 18
    # Floor: dirt by default. Specific tiles flipped to `:` (dense
    # corn cover) further down so the maze has tactical hide
    # patches mixed into the lanes.
    floor_rows_l = [list("d" * W) for _ in range(H)]
    objects_l = []
    for y in range(H):
        row = ["C"] * W if (y == 0 or y == H - 1) else ["."] * W
        if y not in (0, H - 1):
            row[0] = "C"
            row[W - 1] = "C"
        objects_l.append(row)
    # 2-wide passage south back to the forest_path. Two adjacent
    # `!` tiles in the south corn wall so the player walks straight
    # out through a footpath worn through the rows. Row 16 col 11
    # is cleared from the lane-wall pass below so the second exit
    # tile is actually reachable (was a one-tile exit before).
    objects_l[H - 1][10] = "!"
    objects_l[H - 1][11] = "!"
    # 2-wide passage north into the mistlands. The maze has a
    # second exit; the player who pushes through the field comes
    # out into the fog instead of back to the road. Frees the
    # cornfield from being a dead-end detour.
    objects_l[0][9]  = "^"
    objects_l[0][10] = "^"
    # Real cornfield rows: corn walls at cols 3, 7, 11, 15 running
    # N-S. Lanes between are 3 tiles wide (cols 1-2, 4-6, 8-10,
    # 12-14, 16-18). The player loses sightline immediately --
    # over the stalks there is only sky.
    for col in (3, 7, 11, 15):
        for y in range(1, H - 1):
            objects_l[y][col] = "C"
    # Two horizontal break rows so the lanes connect. Each break
    # opens the corn at every wall col on that row -- the player
    # can swap lanes there and only there.
    for y in (5, 11):
        for col in (3, 7, 11, 15):
            objects_l[y][col] = "."
    # One extra single-cell cut so the maze isn't a perfect grid:
    # between the south spawn and the central break, opening just
    # the col-7 wall at row 14 lets the player slip into the
    # mid-east lane without first walking all the way north.
    objects_l[14][7] = "."
    # Fix the south exit: clear the row-16 corn at col 11 so both
    # `!` tiles below are actually reachable. (Was blocked by the
    # lane-wall loop above.) Also clear row-1 col 9 so both north
    # exits are reachable.
    objects_l[H - 2][11] = "."
    objects_l[1][9]      = "."
    # Loot crate at (5, 6) -- chopped with the axe yields its item
    # from CRATE_LOOT (spare_batteries).
    objects_l[6][5] = "K"
    # Corn cover patches scattered through the lanes. The `:`
    # floor tile flips player.hidden to "corn" while the player
    # stands on it; cultist sight cones can't lock through them.
    # Placed mid-lane so they're reachable from the break rows
    # but not a guaranteed corridor cover -- the player chooses
    # when to dive in. All coords (col, row) lie in OPEN lanes
    # (cols 1-2, 4-6, 8-10, 12-14, 16-18; rows 1..16); none on
    # the perimeter walls (rows 0, 17) or the inner wall cols
    # (3, 7, 11, 15).
    cover_patches = [
        (1, 3),  (2, 7),  (2, 13), (5, 4),
        (8, 1),  (8, 9),  (8, 14), (10, 6),
        (12, 13),(13, 2), (16, 8), (17, 12),
    ]
    for cx, cy in cover_patches:
        # Sanity gate -- skip if (cx, cy) lands on a wall col/row
        # so a future re-tune can't silently bury the patch.
        if not (0 <= cx < W and 0 <= cy < H):
            continue
        if cy in (0, H - 1) or cx in (0, W - 1, 3, 7, 11, 15):
            continue
        floor_rows_l[cy][cx] = ":"
    floor_rows = ["".join(r) for r in floor_rows_l]
    objects = ["".join(r) for r in objects_l]
    sc = Scene("cornfield_maze", floor_rows, objects, music="outside")
    sc.add_exit("!", "forest_path", "from_cornfield_maze")
    sc.add_exit("^", "mistlands",   "from_cornfield_maze")
    sc.set_spawn("default", 10, H - 2)
    sc.set_spawn("from_forest_path", 10, H - 2)
    sc.set_spawn("from_cornfield", 10, H - 2)
    sc.set_spawn("from_mistlands", 10, 1)

    # Scarecrow at the centre dead-end. Hanging-figure deco is
    # close enough to a scarecrow silhouette -- placed just south
    # of the row-8 cornwall break.
    scarecrow_x = 10 * TILE + 16
    scarecrow_y = 6 * TILE + 16
    sc.add_decoration(Decoration(scarecrow_x, scarecrow_y,
                                 "hanging_figure"))
    sc._scarecrow_pos = (scarecrow_x, scarecrow_y)
    # Dead crows pinned to the stalks. Phantom-mark trampled into
    # the dirt. Decorations sit on lanes (even cols) so they
    # aren't buried inside a corn tile.
    sc.add_decoration(Decoration(8 * TILE + 16, 10 * TILE + 22,
                                 "dead_crow"))
    sc.add_decoration(Decoration(14 * TILE + 16, 5 * TILE + 22,
                                 "dead_crow"))
    sc.add_decoration(Decoration(10 * TILE + 16, 13 * TILE + 16,
                                 "phantom_mark"))
    rng = random.Random(2034)
    for _ in range(40):
        gx = rng.randint(1, W - 2) * TILE + rng.randint(0, 30)
        gy = rng.randint(1, H - 2) * TILE + rng.randint(0, 30)
        ty_ = gy // TILE
        tx_ = gx // TILE
        if 9 <= tx_ <= 11 and ty_ >= 14:    # keep the entrance path clear
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))

    # Boarded cache at the deep north dead-end pocket.
    sc.objects[1][2] = "q"

    def _cornfield_maze_on_enter(game, scene):
        scene._rustle_t = random.uniform(2.0, 4.0)
    sc.on_enter_fn = _cornfield_maze_on_enter

    def _cornfield_maze_on_update(game, scene, dt):
        scene._rustle_t = getattr(scene, "_rustle_t", 3.0) - dt
        if scene._rustle_t <= 0:
            scene._rustle_t = random.uniform(2.5, 6.0)
            game.audio.play("breath", 0.18)
    sc.on_update_fn = _cornfield_maze_on_update

    def _cornfield_maze_interact(game):
        sx, sy = sc._scarecrow_pos
        if (abs(game.player.x - sx) < 40
                and abs(game.player.y - sy) < 40):
            if not game.save.flag("scarecrow_evidence"):
                _evidence(game, "scarecrow",
                    "A scarecrow."
                )
            return
    sc.on_interact_fn = _cornfield_maze_interact

    sc.hide_spots = [
        (2 * TILE + 16, 6 * TILE + 16, "behind"),     # west lane
        (16 * TILE + 16, 11 * TILE + 16, "behind"),   # east lane
        (10 * TILE + 16, 11 * TILE + 16, "behind"),   # central
    ]
    return sc


# ---------------------------------------------------------------------------
# The town. A populated main street -- the civic centre of the world.
#
# Wired to: the general store (shop), the sheriff's office
# (fisherman_cottage), the schoolhouse, and the road south back to the
# village/farm. The church stays out in the mistlands, so the town
# reaches it the long way, through the fields.
# ---------------------------------------------------------------------------
def build_town():
    """Retired. The town came apart into the fog -- its street, civic
    buildings (Store, Sheriff, Schoolhouse) and residents now live in
    the mistlands, displayed as Brimley. This stub survives only so a
    save left standing in the old 'town' scene bounces straight out to
    Brimley on load, instead of soft-locking on a missing scene."""
    floor = ["g" * 5 for _ in range(5)]
    objects = ["." * 5 for _ in range(5)]
    sc = Scene("town", floor, objects, music="wind")
    for name in ("default", "from_village", "from_shop", "from_sheriff",
                 "from_school", "from_town_crossroads"):
        sc.set_spawn(name, 2, 2)

    def _bounce(game):
        if game.state == "transition":
            return
        game.begin_transition("mistlands", "from_village")

    sc.triggers.append({
        "rect": (0, 0, 5 * TILE, 5 * TILE),
        "fn": _bounce, "once": False, "fired": False,
    })
    return sc
