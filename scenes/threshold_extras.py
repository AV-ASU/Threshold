"""Additional scenes added to the registry.

  schoolhouse        -- one-room schoolhouse, empty for months.
  graveyard          -- behind the church. One readable headstone.
  diner_gas_station  -- closed-up diner with a gas pump. The
                        player's CAR is parked here. Reaching the
                        car with the keys triggers the car-escape
                        ending.
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


def _river_cache_pickup(game):
    game.save.set_flag("river_cache_taken", True)
    _evidence(game, "river_cache",
        "A small stash.")


def _grave_cache_pickup(game):
    game.save.set_flag("grave_cache_taken", True)
    _evidence(game, "grave_cache",
        "A small stash."
    )


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

    # The teacher's desk -- the player can interact with it to generate
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
    """A worn rural road between the Innkeeper's yard and the town
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

    # Mom's stone -- the leftmost top row.
    moms_stone = (3 * TILE + 16, 2 * TILE + 16)
    sc._moms_stone = moms_stone
    # The kid's family stones -- middle row, three crooked headstones.
    sc._kids_family_stones = [
        (3 * TILE + 16, 4 * TILE + 16),     # father
        (6 * TILE + 16, 4 * TILE + 16),     # mother
        (9 * TILE + 16, 4 * TILE + 16),     # sister
    ]

    # Bloodstain near the back row -- a fresh disturbance.
    sc.add_decoration(Decoration(6 * TILE + 16, 6 * TILE + 24,
                                 "bloodstain"))
    # Crows on the fence line, plus a dead crow on Mom's plot.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(moms_stone[0] - 12,
                                 moms_stone[1] + 18, "dead_crow"))
    # A lone candle on Mom's stone -- still burning.
    sc.add_decoration(Decoration(moms_stone[0], moms_stone[1] - 8,
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

    # Boarded shortcut: a panel of nailed-on planks set into the east
    # iron-fence/tree line. Behind it, the groundskeeper's emergency
    # cache -- batteries wrapped in oilskin. Chop with the axe to open.
    sc.objects[7][13] = "q"

    def _graveyard_on_enter(game, scene):
        if not game.save.flag("grave_cache_taken"):
            scene.add_item(
                13 * TILE + 16, 7 * TILE + 16, "charcoal",
                on_pickup=_grave_cache_pickup,
            )
    sc.on_enter_fn = _graveyard_on_enter

    def _graveyard_interact(game):
        # Mom's stone reading.
        mx, my = sc._moms_stone
        if (abs(game.player.x - mx) < 36
                and abs(game.player.y - my) < 36):
            if not game.save.flag("read_moms_stone"):
                game.save.set_flag("read_moms_stone", True)
                game.audio.play("low_pulse", 0.35)
                game.dialog.show([
                    "[c=dim](A weather-worn headstone.)[/c]",
                    "[c=dim]The name has worn away.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                _evidence(game, "moms_stone",
                    "A weathered headstone."
                )
            else:
                game.dialog.show([
                    "[c=dim]A worn headstone.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
            return
        # Other stones -- any of the three.
        for i, (sx, sy) in enumerate(sc._kids_family_stones):
            if (abs(game.player.x - sx) < 36
                    and abs(game.player.y - sy) < 36):
                game.dialog.show([
                    "[c=dim](A fresh stone.)[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
    sc.on_interact_fn = _graveyard_interact

    return sc


def build_diner_gas_station():
    """An OUTDOOR forecourt: the player walks east out of the
    cornfield path and arrives in a gravel lot, NOT inside a
    building. The closed-up diner sits as a building footprint on
    the north side of the lot (door faces south); a single gas
    pump stands at centre with the player's car parked beside it;
    a payphone at the south-east corner. Wide grass shoulder + tree
    line wraps the lot.

    Reaching the car with the car_keys in inventory triggers the
    car-escape ending (wired in Pass H -- this scene only places
    the geometry).

    Layout (20 wide x 14 tall):
      Row 0..1   tree wall + sky
      Row 2..5   diner building footprint (cols 4..11), door 'l'
                  facing south on row 5 col 7. The door is FACADE
                  (locked / boarded over) -- the player can read
                  the sign but not enter.
      Row 6..10  open gravel lot. Gas pump + car at centre, payphone
                  at SE corner.
      Row 11..12 grass shoulder
      Row 13     tree wall except for H exit south to forest_path.

    Hide spots: behind the diner building (alley row 5/6), behind
    the car, against the tree line east. Each spot lands on a
    walkable tile beside cover, never on solid prop.
    """
    W, H = 20, 14
    # Floor: gravel lot in centre rows, grass shoulder + dirt path
    # leading south to the H exit.
    floor_rows = []
    for y in range(H):
        if 6 <= y <= 10:
            floor_rows.append("_" * W)            # gravel
        elif 11 <= y <= 12:
            row = list("g" * W)
            # Dirt path south from gas pump down to the H exit.
            for cx in range(9, 12):
                row[cx] = "d"
            floor_rows.append("".join(row))
        else:
            floor_rows.append("g" * W)
    objects_l = []
    for y in range(H):
        if y == 0 or y == H - 1:
            objects_l.append(list("T" * W))
        else:
            row = ["."] * W
            row[0] = "T"
            row[W - 1] = "T"
            objects_l.append(row)
    # H exit south to forest_path (cornfield).
    objects_l[H - 1][10] = "H"
    # Diner building footprint (cols 4..11, rows 2..5). South face
    # has a 'l' (facade/locked door) at col 7 row 5 -- the diner is
    # closed; player can read but not enter. North face + roof tiles.
    for cx in range(4, 12):
        objects_l[2][cx] = "W"
        objects_l[5][cx] = "W"
    for ry in (3, 4):
        objects_l[ry][4] = "W"
        objects_l[ry][11] = "W"
        for cx in range(5, 11):
            objects_l[ry][cx] = "r"
    # Window in the north face + facade door in the south face.
    objects_l[2][7] = "i"
    objects_l[5][7] = "l"
    objects = ["".join(r) for r in objects_l]

    sc = Scene("diner_gas_station", floor_rows, objects, music="outside")
    sc.add_exit("H", "forest_path", "from_diner")
    # Spawns: arriving from forest_path (south), spawn one row north
    # of the H exit so the player doesn't auto-retrigger.
    sc.set_spawn("default", 10, 12)
    sc.set_spawn("from_forest", 10, 12)
    sc.set_spawn("from_cornfield", 10, 12)

    # Gas pump + payphone. The player's car USED to be parked
    # here too, but has been moved to the mistlands east bank --
    # the diner now reads as a closed-up landmark, not a launch
    # pad. (Old saves still load; the car decoration just no
    # longer renders in this scene.)
    pump_x = 9 * TILE + 16
    pump_y = 8 * TILE + 16
    payphone_x = 17 * TILE + 16
    payphone_y = 10 * TILE + 16
    sc.add_decoration(Decoration(pump_x, pump_y, "gas_pump"))
    sc.add_decoration(Decoration(payphone_x, payphone_y, "payphone"))
    # Solid invisible tiles under the pump + payphone so the
    # player has to walk around them.
    objects_list = [list(r) for r in sc.objects]
    objects_list[8][9] = "X"     # gas pump
    objects_list[10][17] = "X"   # payphone
    sc.objects = objects_list
    # Diner signage: a banner hung over the south wall.
    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 28,
                                 "banner", color=(160, 50, 60)))
    # Closed-for-business clock above the door.
    sc.add_decoration(Decoration(7 * TILE + 16, 4 * TILE + 22, "clock"))
    # Two crows on the diner roof.
    sc.add_decoration(Decoration(5 * TILE + 8, 3 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(10 * TILE + 8, 3 * TILE + 22, "crow"))
    # Grass tufts scattered through the shoulders.
    rng = random.Random(2029)
    for _ in range(20):
        gx = rng.randint(1, W - 2) * TILE + rng.randint(0, 30)
        gy = rng.randint(0, H - 1) * TILE + rng.randint(0, 30)
        ty_ = gy // TILE
        if 6 <= ty_ <= 10 or 2 <= ty_ <= 5:   # keep lot/building clear
            continue
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    # One dead crow at the foot of the gas pump.
    sc.add_decoration(Decoration(8 * TILE + 16, 9 * TILE + 22,
                                 "dead_crow"))
    # Hide spots beside cover (NOT on the solid pump tiles).
    sc.hide_spots = [
        (16 * TILE + 16, 10 * TILE + 16, "behind"), # beside the payphone
        (3 * TILE + 16, 6 * TILE + 16, "behind"),   # alley west of diner
        (8 * TILE + 16, 7 * TILE + 16, "behind"),   # beside the pump
    ]

    def _diner_interact(game):
        if (abs(game.player.x - payphone_x) < 40
                and abs(game.player.y - payphone_y) < 40):
            game.audio.play("static", 0.4)
            game.show_notice("The line is dead.")
    sc.on_interact_fn = _diner_interact

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
    # Boarded shortcut: a panel of nailed planks set into the east
    # tree line at midway -- a small alcove with a battery cache.
    sc.objects[10][13] = "q"

    def _gravel_on_enter(game, scene):
        if not game.save.flag("gravel_cache_taken"):
            scene.add_item(
                13 * TILE + 16, 10 * TILE + 16, "charcoal",
                on_pickup=lambda g: g.save.set_flag(
                    "gravel_cache_taken", True),
            )
    sc.on_enter_fn = _gravel_on_enter

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
    sc.add_decoration(Decoration(notepad_x, notepad_y, "paper"))
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
    def _on_enter(game, scene):
        if not game.save.flag("cellar_key_taken"):
            scene.add_item(
                4 * TILE + 16, 4 * TILE + 16, "cellar_key",
                on_pickup=lambda g: g.save.set_flag(
                    "cellar_key_taken", True),
            )
    sc.on_enter_fn = _on_enter
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

    # Boarded cache pocket at col 5 row 0 -- chop the q to access
    # an oilskin packet of spare batteries.
    def _river_on_enter(game, scene):
        if not game.save.flag("river_cache_taken"):
            scene.add_item(
                5 * TILE + 16, 0 * TILE + 16, "charcoal",
                on_pickup=_river_cache_pickup,
            )
    sc.on_enter_fn = _river_on_enter

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
        if not game.save.flag("cornfield_cache_taken"):
            scene.add_item(
                2 * TILE + 16, 1 * TILE + 16, "charcoal",
                on_pickup=lambda g: g.save.set_flag(
                    "cornfield_cache_taken", True),
            )
        # The Innkeeper's missing crate of bottles. Stashed in the
        # east-lane dead-end pocket -- straw-packed, six bottles,
        # heavier than it looks.
        if not game.save.flag("liquor_crate_taken"):
            scene.add_item(
                17 * TILE + 16, 16 * TILE + 16, "liquor_crate",
                on_pickup=lambda g: g.save.set_flag(
                    "liquor_crate_taken", True),
            )
        scene._rustle_t = random.uniform(2.0, 4.0)
    sc.on_enter_fn = _cornfield_maze_on_enter

    # Hidden note tile -- a phantom_mark in the centre lane that
    # the player can interact with to read the truth about the
    # crate. Reveals 'religious service' euphemism for the cult
    # rite. Sets a save flag the innkeeper dialogue checks so the
    # turn-in line shifts when the player has read it.
    note_x = 9 * TILE + 16
    note_y = 8 * TILE + 16
    sc.add_decoration(Decoration(note_x, note_y, "phantom_mark"))
    sc._crate_note_pos = (note_x, note_y)

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
        # The crate-note: a folded slip pinned to a corn stalk.
        # Reading it once sets `crate_note_read` so the Innkeeper
        # turn-in line shifts.
        nx, ny = sc._crate_note_pos
        if (abs(game.player.x - nx) < 36
                and abs(game.player.y - ny) < 36):
            if game.save.flag("crate_note_read"):
                game.dialog.show([
                    "[c=dim]A slip pinned to the stalk.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            game.save.set_flag("crate_note_read", True)
            game.audio.play("pickup", 0.5)
            game.dialog.show([
                "[c=dim](A folded slip pinned to a stalk.)[/c]",
                "[c=dim]A note about the crate.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            _evidence(game, "service_note",
                "A note about the crate."
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
