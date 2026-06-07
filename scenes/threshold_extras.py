"""Additional scenes added to the registry.

  schoolhouse        -- one-room schoolhouse, empty for months.
  graveyard          -- behind the church. One readable headstone.
"""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence


def _backwoods_note_pickup(game):
    game.save.set_flag("backwoods_note_taken", True)
    _evidence(game, "backwoods_note",
        "A small stash.")


def build_schoolhouse():
    """The one-room schoolhouse on the Brimley bank -- but the cult took it over
    as a COMMUNE before they moved underground. The schoolroom bones still show
    (the chalkboard, a teacher's desk, the children's desks shoved into a corner
    to clear the floor), and over them: rows of cots where the congregation
    bedded down crammed together, their bowls and guttered candles still beside
    them, the chalkboard scrawled over with the door-motif. Empty now, cobwebbed
    -- they all went down the well. Hide spots: behind the cot banks, in the
    shoved-desk corner."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWWWWWWiWWWWWWWW",   # 0  N wall (the chalkboard) + window
        "W..............W",    # 1
        "W..............W",    # 2
        "W..............W",    # 3
        "W..............W",    # 4
        "W..............W",    # 5
        "W..............W",    # 6
        "W..............W",    # 7
        "W..............W",    # 8
        "W..............W",    # 9
        "W..............W",    # 10
        "WWWWWWWHWWWWWWWW",    # 11  H = exit south, onto the field
    ]
    sc = Scene("schoolhouse", floor, objects, music="home")
    sc.add_exit("H", "brimley", "from_school")
    sc.set_spawn("default", 7, 9)
    sc.set_spawn("from_brimley", 7, 10)       # one tile north of the H door
    sc.set_spawn("from_village", 7, 10)
    sc.set_spawn("from_town_crossroads", 7, 10)
    sc.set_spawn("from_town", 7, 10)

    # The schoolroom remnants: the teacher's desk shoved askew to the NW front,
    # and the children's desks ALL pushed into the SE corner -- a jumbled pile of
    # little desks + chairs cleared off the floor to make room for the cots.
    sc.add_furniture("table", [(2, 1)], w=54, h=34)              # teacher's desk
    sc.add_furniture("table", [(12, 9), (13, 9)], w=54, h=34)    # piled desks
    sc.add_furniture("table", [(12, 10), (13, 10)], w=54, h=30)
    for (dx, dy) in ((11, 9), (11, 10), (12, 8), (11, 8), (13, 8)):  # little desks
        sc.add_furniture("small_chair", [(dx, dy)])
    sc.add_furniture("chair", [(3, 1)])                          # the teacher's chair
    # chairs shoved off the desks, knocked over into the room
    sc.add_decoration(Decoration(10 * TILE + 16, 9 * TILE + 16, "overturned_chair"))
    sc.add_decoration(Decoration(6 * TILE + 16, 6 * TILE + 16, "overturned_chair"))
    sc.add_decoration(Decoration(9 * TILE + 16, 8 * TILE + 16, "overturned_chair"))

    # The commune: two banks of cots crammed against the long walls, a narrow
    # aisle down the middle. Where several people lived, in rows, for months.
    west = [(2, 3), (4, 3), (2, 5), (4, 5), (2, 7), (4, 7)]
    east = [(11, 3), (13, 3), (11, 5), (13, 5), (11, 7), (13, 7)]
    for (cx, cy) in west + east:
        sc.add_furniture("cot", [(cx, cy)])
    # Their effects, still beside the beds -- bowls they ate from, candle stubs
    # burned down, a kerosene lamp, an old dark stain. People were here.
    for (bx, by) in ((3, 4), (12, 4), (3, 8), (12, 6), (5, 6)):
        sc.add_decoration(Decoration(bx * TILE + 16, by * TILE + 16, "bowl"))
    sc.add_decoration(Decoration(3 * TILE + 16, 6 * TILE + 8, "candle"))
    sc.add_decoration(Decoration(12 * TILE + 16, 8 * TILE + 8, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 8, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 14, 2 * TILE + 2, "kerosene_lamp"))
    sc.add_decoration(Decoration(8 * TILE + 16, 7 * TILE + 16, "bloodstain",
                                 scale=1.6))

    # The schoolroom CHALKBOARD on the N wall, the children's faded lesson
    # scrawled over with the cult's door-compulsion (the door drawn over and
    # over, shrinking into a corner). A couple of chalk smudges flank it.
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 20, "chalkboard"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 28, "phantom_mark"))
    sc.add_decoration(Decoration(4 * TILE + 8, 0 * TILE + 28, "phantom_mark"))
    # A corn-husk doll left on a cot -- the one overt cult tell among the relics.
    sc.add_decoration(Decoration(13 * TILE + 16, 3 * TILE + 6, "corn_doll"))

    # The remnants of a campfire they burned INSIDE, on the wood floor in a
    # cleared spot off the aisle -- reckless, the way squatters do.
    sc.add_decoration(Decoration(9 * TILE + 16, 4 * TILE + 16, "campfire"))

    # Children's crayon drawings scattered on the floor -- most ordinary (a
    # house, a sun, little figures), a couple of them wrong (a black door + a
    # tall yellow figure). Left where the children left them.
    for (gx, gy, gs) in ((6, 3, 3), (5, 6, 4), (5, 8, 5), (10, 7, 6),
                         (6, 9, 7), (4, 5, 8)):
        sc.add_decoration(Decoration(gx * TILE + 16, gy * TILE + 16,
                                     "child_drawing", seed=gs))

    # Abandoned a while: cobwebs strung in the high corners over the cots, a
    # stopped clock, dust in the dim light.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb", ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_decoration(Decoration(1 * TILE + 6, 10 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(9 * TILE + 16, 1 * TILE + 22, "clock"))
    for i in range(6):
        sc.add_decoration(Decoration(150 + i * 70, 200 + (i % 3) * 70, "mote"))

    sc.hide_spots = []

    # The chalkboard reads as a flavor beat (not counted evidence).
    sc._board_pos = (7 * TILE + 16, 0 * TILE + 16)
    sc.add_interactable(sc._board_pos[0], sc._board_pos[1], 44)

    def _school_on_enter(game, scene):
        if game.save.flag("schoolhouse_seen"):
            return
        game.save.set_flag("schoolhouse_seen", True)

    def _school_interact(game):
        px, py = game.player.x, game.player.y
        bx, by = sc._board_pos
        if abs(px - bx) <= 44 and abs(py - by) <= 44:
            game.dialog.show([
                "[c=dim](The chalkboard. Under a child's faded lesson, the same "
                "door is drawn over and over, smaller and smaller, to the "
                "corner.)[/c]",
                "[c=dim]Whoever did it ran out of board before they ran out of "
                "the need to draw it.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")

    sc.on_enter_fn = _school_on_enter
    sc.on_interact_fn = _school_interact
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
    objects = ["".join(r) for r in objects_l]
    sc = Scene("country_lane", floor_rows, objects, music="outside")
    sc.add_exit("a", "brimley", "from_country_lane")
    # East now lands on the ARRIVAL ROAD (the looping road W of the Lodge),
    # whose dirt path carries on east to the yard.
    sc.add_exit("e", "arrival_road", "from_country_lane")
    # Direction-sensitive hidden fold: walking EAST across the 'M2'
    # tile (a piece of road past the lodge gate, late on the lane)
    # opens onto the highway that doesn't end -- where the locals
    # who walked out to flag down help are still walking. From any
    # other angle the tile reads as floor.
    sc.add_exit("Q", "highway_walk", "from_country_lane",
                direction="east")
    objects_ll = [list(r) for r in objects]
    if 0 <= 6 < len(objects_ll) and W - 4 < len(objects_ll[6]):
        objects_ll[6][W - 4] = "Q"
    sc.objects = objects_ll
    sc.set_spawn("default", 1, 6)
    # Player walked WEST off the arrival road: lands at the east end of the
    # lane, facing west toward town. (from_our_house_area kept as an alias for
    # any save that still routes straight here.)
    sc.set_spawn("from_arrival_road", W - 2, 6)
    sc.set_spawn("from_our_house_area", W - 2, 6)
    # Player walked EAST out of Brimley: lands at the west end of
    # the lane, facing east toward home.
    sc.set_spawn("from_brimley", 1, 6)
    sc.set_spawn("from_village", 1, 6)   # legacy alias
    # Return spawn from the highway_walk fold -- lands one west of
    # the U tile so the player doesn't immediately re-trigger.
    sc.set_spawn("from_highway_walk", W - 5, 6)

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
    sc.hide_spots = []
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

    sc.hide_spots = []

    # Boarded-over panel of nailed planks set into the east iron-fence/
    # tree line -- a chop-target for the axe that opens onto an empty,
    # long-looted pocket. (Whatever was cached here is long gone.)
    sc.objects[7][13] = "q"

    sc.add_interactable(sc._worn_stone[0], sc._worn_stone[1], 36)  # [E] cue

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
    sc.add_exit("a", "brimley", "from_gravel_road")
    sc.set_spawn("default", 7, H - 2)
    sc.set_spawn("from_brimley", 7, H - 2)
    sc.set_spawn("from_village", 7, H - 2)   # legacy alias
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

    sc.hide_spots = []
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
    sc.add_interactable(notepad_x, notepad_y, 40)   # [E] cue for the note
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
    sc.hide_spots = []

    def _backwoods_interact(game):
        nx, ny = sc._notepad_pos
        if (abs(game.player.x - nx) < 40
                and abs(game.player.y - ny) < 40):
            if not game.save.flag("backwoods_note_taken"):
                _backwoods_note_pickup(game)
    sc.on_interact_fn = _backwoods_interact
    return sc


def build_backwoods_cabin_interior():
    """A cabin interior. Chair tipped, cup on the floor, a smear on
    the boards. The cellar key is on the floor. The door was left
    open."""
    floor = ["=" * 12 for _ in range(9)]
    objects = [
        "WWWWWWWWWWWW",   # 0
        "W.....W....W",   # 1  main room (cols 1-5) | back nook (cols 7-10)
        "W..........W",   # 2  doorway gap in the partition (col 6)
        "W..t..W....W",   # 3  table
        "WWWWWWW....W",   # 4  nook sealed off below
        "W..........W",   # 5
        "W..........W",   # 6
        "W...D......W",   # 7  D = exit door
        "WWWWWWWWWWWW",   # 8
    ]
    sc = Scene("backwoods_cabin_interior", floor, objects, music="home")
    sc.add_exit("D", "backwoods_cabin", "from_interior")
    sc.set_spawn("default",     4, 5)
    sc.set_spawn("from_outside", 4, 6)
    sc.add_decoration(Decoration(3 * TILE + 16, 3 * TILE + 6, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 16,
                                 "overturned_chair"))
    sc.add_decoration(Decoration(4 * TILE + 16, 5 * TILE + 22,
                                 "bowl", filled=False))
    sc.add_decoration(Decoration(5 * TILE + 16, 6 * TILE + 16,
                                 "bloodstain"))
    # The claw-marks are gouged into the back nook -- out of sight from the
    # door until the player comes around the partition.
    sc.add_decoration(Decoration(8 * TILE + 16, 1 * TILE + 24,
                                 "claw_marks"))
    sc.hide_spots = []
    return sc


def build_river_crossing():
    """Plank footbridge across the brimley river. South exit `a`
    returns to brimley; north end of the scene is a small bank
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
    # South exit (back to brimley) -- one passage tile at the
    # south river opening.
    objects_l[H - 1][12] = "a"
    # North-bank cache: a `q` boarded panel set into the north
    # tree line at col 5, with a 1-tile alcove pocket.
    objects_l[0][5] = "q"
    # Sigil on the bridge midway.
    objects = ["".join(r) for r in objects_l]
    sc = Scene("river_crossing", floor_rows, objects, music="wind")
    sc.add_exit("a", "brimley", "from_river_crossing")
    sc.set_spawn("default", 12, H - 2)
    sc.set_spawn("from_brimley", 12, H - 2)

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

    sc.hide_spots = []
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
    # A 12x10 lookout with a solid 2x2 bell housing dead centre: a column
    # you circle, so whatever is on its far side is an indoor blind spot.
    floor_rows = ["=" * 12 for _ in range(10)]
    objects = [
        "WWWWiWWWiWWWW",   # 0  north-wall window slits
        "W..........W",    # 1
        "W..........W",    # 2
        "i..........i",    # 3  east/west window slits
        "W....tt....W",    # 4  the bell housing (solid) at centre
        "W....tt....W",    # 5
        "W..........W",    # 6
        "W..........W",    # 7
        "W..........W",    # 8
        "WWWWiWWLWWWW",    # 9  south-wall slit + L = stairs down to the church
    ]
    sc = Scene("bell_tower", floor_rows, objects, music="home")
    sc.add_exit("L", "old_man_house", "from_bell_tower")
    sc.set_spawn("default", 5, 8)
    sc.set_spawn("from_church", 7, 8)        # at the foot of the L stairs
    # The bell hangs in the central housing. Use a lantern + rope as a
    # stand-in -- we don't have a `bell` deco.
    sc.add_decoration(Decoration(5 * TILE + 32, 4 * TILE + 16, "lantern"))
    sc.add_decoration(Decoration(5 * TILE + 32, 4 * TILE + 34, "rope"))
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16,
                                 "phantom_mark"))
    for i in range(8):
        sc.add_decoration(Decoration(40 + i * 36,
                                     60 + (i % 3) * 50, "mote"))
    sc.hide_spots = []

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
    into the brimley -- the maze led you somewhere wrong.
    Lanes are dotted with `:` corn patches: walk into one and
    you're hidden, but only as long as you stay in the patch."""
    # Larger maze (was 20x18) -- more room for the new dead-end pocket
    # clusters and the secret pass-through. Wall cols 4, 9, 14, 19;
    # lanes between are 3-4 tiles wide (1-3, 5-8, 10-13, 15-18, 20-22).
    W, H = 24, 22
    floor_rows_l = [list("d" * W) for _ in range(H)]
    objects_l = []
    for y in range(H):
        row = ["C"] * W if (y == 0 or y == H - 1) else ["."] * W
        if y not in (0, H - 1):
            row[0] = "C"
            row[W - 1] = "C"
        objects_l.append(row)
    # South exit (back to forest_path) in lane 3 (cols 11-12).
    objects_l[H - 1][11] = "!"
    objects_l[H - 1][12] = "!"
    # North exit (into brimley) in lane 3 (cols 11-12).
    objects_l[0][11] = "^"
    objects_l[0][12] = "^"
    # The fold-grove access -- a regular-looking lane tile in lane 2.
    # Walking WEST across it opens the fold-grove (effigy_grove).
    objects_l[10][6] = "Z"
    # Internal corn walls at cols 4, 9, 14, 19 running N-S. Lanes
    # between: 1-3, 5-8, 10-13, 15-18, 20-22. The player loses
    # sightline immediately -- over the stalks there is only sky.
    WALL_COLS = (4, 9, 14, 19)
    for col in WALL_COLS:
        for y in range(1, H - 1):
            objects_l[y][col] = "C"
    # Per-wall pass-throughs at DIFFERENT rows so the maze isn't a
    # ladder of fully-aligned breaks. Each wall opens at its own
    # set of rows; the player swaps lanes by finding the gap.
    pass_throughs = {
        4:  [3, 9, 15, 19],
        9:  [5, 12, 17, 20],
        14: [4, 11, 16, 20],
        19: [6, 13, 18],
    }
    for col, rows in pass_throughs.items():
        for y in rows:
            objects_l[y][col] = "."
    # Horizontal corn-wall segments INSIDE lanes -- real dead-ends.
    # The player walking a lane hits these and has to back out to a
    # pass-through. Layout tuned so each cluster pocket is reachable
    # via exactly one route + the wrap.
    dead_ends = [
        # (row, col_start, col_end)
        (7,  1, 3),       # lane 1 dead-end (upper) -- creates the OFFERING pocket below
        (16, 1, 3),       # lane 1 dead-end (lower)
        (12, 5, 8),       # lane 2 dead-end (mid)
        (18, 5, 8),       # lane 2 dead-end (lower)
        (7,  15, 18),     # lane 4 dead-end (upper)
        (17, 15, 18),     # lane 4 dead-end (lower) -- CURSE-WORK pocket above
        (4,  20, 22),     # lane 5 dead-end (upper) -- WATCHING pocket below
        (11, 20, 22),     # lane 5 dead-end (mid)
        (18, 20, 22),     # lane 5 dead-end (lower)
    ]
    for row, c0, c1 in dead_ends:
        for col in range(c0, c1 + 1):
            objects_l[row][col] = "C"
    # SECRET PASS-THROUGH. The CURSE-WORK pocket's south dead-end wall
    # at row 17 cols 15-18 looks solid like the others -- but one tile
    # (col 17) is passable 'A'. Player walks the pocket, sees the
    # ritual, pushes south against what looks like another wall, and
    # gets through into the south end of lane 4. Hide is the whole
    # point: it reads as a dead-end from above.
    objects_l[17][17] = "A"
    # Fix the exits: clear the row near the corner walls so the
    # 2-wide exit tiles are actually reachable.
    objects_l[H - 2][11] = "."
    objects_l[H - 2][12] = "."
    objects_l[1][11]     = "."
    objects_l[1][12]     = "."

    # ---- Direction-sensitive hidden-scene folds (more secret areas) ----
    # Same mechanic as the Z curse-grove tile, just opening onto two
    # other small clearings. Each is a lane tile that looks like
    # nothing; walking through it in the matching direction opens the
    # hidden scene. From any other angle the tile is just floor.
    # Lane 5 (cols 20-22): walking EAST through (21, 8) opens the
    # husk_grove -- where the cult assembles the corn-dolls.
    objects_l[8][21] = "P"
    # Lane 1 (cols 1-3): walking WEST through (2, 14) opens the
    # scarecrow_ring -- a ring of scarecrows facing inward around a
    # Sign.
    objects_l[14][2] = "S"

    # ---- In-maze direction-fold RELOCATION tiles ----
    # Different from the scene-fold tiles above: these don't open a
    # new scene; they teleport you to ELSEWHERE IN THE SAME MAZE.
    # Walking through one in the matching direction snaps you to the
    # destination tile with the camera adjusted so the swap is
    # seamless. Handled in _maze_on_update below. The chars 'I' and
    # 'Q' mark them in the objects layer (rendered as floor).
    # 'I' at (8, 6) walked SOUTH -> teleport to (16, 19) (top of
    # lane 2 -> bottom of lane 4).
    objects_l[6][8] = "I"
    # 'Q' at (16, 11) walked NORTH -> teleport to (3, 19) (mid of
    # lane 4 -> bottom of lane 1). 'Q' renders as floor (it maps to
    # None), so the relocation tile is invisible.
    objects_l[11][16] = "Q"

    # ---- Visible perimeter side passages ----
    # Carve clear dirt lanes through the perimeter band on the west
    # and east edges. Each is 2 tiles deep, looks like an obvious way
    # out of the maze. The wrap (wrap_x) fires when the player walks
    # off the edge and they appear on the OPPOSITE edge -- so the
    # passage loops instead of escaping.
    #
    # CRITICAL: a passage only loops if the SAME row is open on BOTH
    # edges. Walking west off (0, row) lands the player on (W-1, row);
    # if that tile is solid corn the move is blocked and the "exit"
    # dead-ends against an invisible wall. So passages are carved in
    # MATCHED PAIRS -- both col 0 and col W-1 open at each row. Rows
    # chosen so the adjacent inland tile (lane 1 / lane 5) is already
    # clear, keeping the passage reachable from inside the maze.
    SIDE_PASSAGE_ROWS = [2, 8, 14, 20]
    for row in SIDE_PASSAGE_ROWS:
        for px in (0, W - 1):
            objects_l[row][px] = "."
            floor_rows_l[row][px] = "d"
            # Carve the adjacent inland tile too so the passage has depth.
            nx = px + (1 if px == 0 else -1)
            objects_l[row][nx] = "."
            floor_rows_l[row][nx] = "d"
    # No loot crates in the corn maze. A wooden crate sitting in a
    # cornfield reads as game-y, and an "empty crate" reward is
    # anti-payoff. The maze rewards exploration with discovery of
    # cult-adjacent atmospheric clusters instead (added as
    # decorations after Scene construction below).
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
        (1, 4),  (3, 9),  (2, 14), (3, 18),    # lane 1
        (6, 3),  (7, 10), (5, 14), (8, 19),    # lane 2
        (10, 5), (12, 9), (11, 14),(13, 19),   # lane 3
        (16, 5), (17, 11),(15, 14),(18, 19),   # lane 4
        (21, 7), (20, 14),(22, 19),            # lane 5
    ]
    for cx, cy in cover_patches:
        if not (0 <= cx < W and 0 <= cy < H):
            continue
        if cy in (0, H - 1) or cx in (0, W - 1) + WALL_COLS:
            continue
        floor_rows_l[cy][cx] = ":"
    # ---- Permeable corn band around the perimeter ----
    # The maze identity is endless corn -- but the OUTER wall was a
    # hard ring of solid C. Soften it with the shared scatter helper
    # using corn chars ('C' solid + 'A' passable) so the wrap is
    # camouflaged the same way brimley / forest_path are. Interior
    # corn-wall cols (3, 7, 11, 15) stay untouched -- that's the maze
    # design and must not be perforated. The existing :-corn-cover
    # patches are also preserved.
    def _maze_protected(tx, ty):
        # Interior corn-wall columns -- the maze structure itself.
        if tx in WALL_COLS:
            return True
        # North brimley exit (cols 11, 12 at row 0).
        if tx in (11, 12) and ty == 0:
            return True
        # South forest_path exit (cols 11, 12 at row H-1).
        if tx in (11, 12) and ty == H - 1:
            return True
        # Direction-sensitive fold tiles.
        if (tx, ty) in ((6, 10), (21, 8), (2, 14)):
            return True
        # In-maze relocation tiles.
        if (tx, ty) in ((8, 6), (16, 11)):
            return True
        # Spawn-row tiles.
        if (tx, ty) in ((11, 1), (12, 1), (11, H - 2), (12, H - 2)):
            return True
        # Visible perimeter side-passage tiles (clear lanes through
        # the band, not corn). References SIDE_PASSAGE_ROWS directly so
        # the two can't drift -- if the band re-walls a passage row its
        # wrap dead-ends against invisible corn on the opposite edge.
        if (tx == 0 or tx == W - 1) and ty in SIDE_PASSAGE_ROWS:
            return True
        return False
    _maze_bushes = []
    from .base import scatter_forest_band
    scatter_forest_band(floor_rows_l, objects_l, W, H,
                        depth=2, seed=131,
                        # Use corn chars instead of trees -- the maze
                        # camouflage is corn, not woods.
                        solid_char="C", passable_char="A",
                        # The maze is small and dense; bigger band
                        # density would make the perimeter impassable.
                        tree_density=0.62, passable_ratio=0.55,
                        bush_density=0.14,
                        # Skip the dim-grass blotch -- the maze floor
                        # is dirt 'd' not grass 'g' so it'd no-op anyway,
                        # but keep the corn-cover :-cover blotch.
                        blotch_dim=0.0, blotch_corn=0.0,
                        protected=_maze_protected,
                        place_bush=lambda px, py:
                            _maze_bushes.append((px, py)))
    floor_rows = ["".join(r) for r in floor_rows_l]
    objects = ["".join(r) for r in objects_l]
    sc = Scene("cornfield_maze", floor_rows, objects, music="outside")
    for bx, by in _maze_bushes:
        sc.add_decoration(Decoration(bx, by, "bush"))

    # ---- Dead-end cult clusters ----
    # The maze's three new dead-end pockets each hold a cluster of
    # props that tell the player something specific about what the
    # cult does in the corn. Each cluster is small (3-5 decorations),
    # placed so it's only visible to a player who pushed past a
    # pass-through and hit the dead-end wall. The reward IS the
    # recognition -- no loot, no inventory pickup.

    # ---- Lane 1 OFFERING POCKET ----
    # Below the row-7 dead-end wall, above the row-16 dead-end.
    # A corn altar (cobs + husks + a candle stub) and a single
    # corn-doll at its foot. Someone has been here recently.
    sc.add_decoration(Decoration(2 * TILE + 16, 12 * TILE + 16,
                                 "corn_altar"))
    sc.add_decoration(Decoration(1 * TILE + 16, 13 * TILE + 16,
                                 "corn_doll"))
    sc.add_decoration(Decoration(3 * TILE + 16, 14 * TILE + 22,
                                 "phantom_mark"))

    # ---- Lane 4 CURSE-WORK POCKET ----
    # Between the row-7 and row-17 dead-end walls. The cult's curse
    # circle: a yellow sign worked into the ground at the centre,
    # four corn-dolls placed at the cardinal points, two candles.
    # The south wall hides the secret pass-through at col 17.
    sc.add_decoration(Decoration(16 * TILE + 16, 12 * TILE + 16,
                                 "yellow_sign"))
    # Four corn-dolls at the cardinal points around the sign.
    sc.add_decoration(Decoration(16 * TILE + 16, 10 * TILE + 16,
                                 "corn_doll"))   # north
    sc.add_decoration(Decoration(16 * TILE + 16, 14 * TILE + 16,
                                 "corn_doll"))   # south
    sc.add_decoration(Decoration(15 * TILE + 16, 12 * TILE + 16,
                                 "corn_doll"))   # west
    sc.add_decoration(Decoration(17 * TILE + 16, 12 * TILE + 16,
                                 "corn_doll"))   # east
    sc.add_decoration(Decoration(15 * TILE + 16, 11 * TILE + 8,
                                 "candle"))
    sc.add_decoration(Decoration(17 * TILE + 16, 13 * TILE + 8,
                                 "candle"))

    # ---- Lane 5 WATCHING POCKET ----
    # Between the row-4 and row-11 dead-end walls. A taller stalk
    # marker -- the cult's flag: the next to be taken. A dead crow
    # at its foot.
    sc.add_decoration(Decoration(21 * TILE + 16, 7 * TILE + 16,
                                 "stalk_marker"))
    sc.add_decoration(Decoration(22 * TILE + 16, 8 * TILE + 22,
                                 "dead_crow"))
    sc.add_decoration(Decoration(20 * TILE + 16, 9 * TILE + 16,
                                 "phantom_mark"))
    # The corn never ends (bible §1). The maze wraps on BOTH axes so
    # walking any direction long enough brings you back to where you
    # started -- corn looks the same in every direction, so the loop
    # feels natural until the player realises no direction escapes it.
    sc.wrap_x = True
    sc.wrap_y = True
    sc.add_exit("!", "forest_path", "from_cornfield_maze")
    sc.add_exit("^", "brimley",   "from_cornfield_maze")
    # Direction-sensitive hidden fold: walking WEST across the 'Z'
    # tile (a regular-looking lane tile in the middle of the maze)
    # opens onto the fold-grove (effigy_grove). From any other angle the
    # tile reads as floor. Bible §8: the cult's work-clearing, tended by
    # no one. Char 'Z' chosen because 'C' is the cornstalk
    # tile char and would conflict.
    sc.add_exit("Z", "effigy_grove", "from_cornfield_maze",
                direction="west")
    # Additional direction-sensitive secret-area folds.
    sc.add_exit("P", "husk_grove", "from_cornfield_maze",
                direction="east")
    sc.add_exit("S", "scarecrow_ring", "from_cornfield_maze",
                direction="west")
    sc.set_spawn("default", 11, H - 2)
    sc.set_spawn("from_forest_path", 11, H - 2)
    sc.set_spawn("from_cornfield", 11, H - 2)
    sc.set_spawn("from_brimley", 11, 1)
    sc.set_spawn("from_brimley_south", 11, 1)
    # Return from effigy_grove -- one east of the Z tile so the player
    # doesn't immediately re-trigger walking west.
    sc.set_spawn("from_effigy_grove", 7, 10)
    # Return from the additional hidden-scene folds. One tile inland
    # from each fold tile in the direction the player came back from.
    sc.set_spawn("from_husk_grove", 20, 8)        # west of (21, 8)
    sc.set_spawn("from_scarecrow_ring", 3, 14)    # east of (2, 14)

    # ---- In-maze relocation handler ----
    # The 'I' and 'Q' tiles teleport the player elsewhere in the maze
    # when crossed in the matching direction. No fade, no scene
    # reload -- the camera is offset to keep the player at the same
    # screen position so the swap is invisible at the moment of the
    # crossing. They notice when their surroundings stop matching.
    _RELOCATIONS = {
        # src (tx, ty): (required_dir, dst_tx, dst_ty)
        (8, 6):   ("south", 16, 19),    # top lane 2 -> bottom lane 4
        (16, 11): ("north", 3, 19),     # mid lane 4 -> bottom lane 1
    }
    _DIR_VEC = {"north": (0, -1), "south": (0, 1),
                "east": (1, 0), "west": (-1, 0)}
    def _maze_on_update(game, scene, dt):
        p = game.player
        ptx = int(p.x // TILE); pty = int(p.y // TILE)
        info = _RELOCATIONS.get((ptx, pty))
        if info is None:
            scene._reloc_armed = True
            return
        # Only fire once per tile entry -- if the player is standing
        # on the tile from a prior frame, don't re-trigger.
        if not getattr(scene, "_reloc_armed", True):
            return
        req_dir, dx_tx, dx_ty = info
        vec = _DIR_VEC[req_dir]
        fx, fy = p.facing
        dot = vec[0] * fx + vec[1] * fy
        if dot < 0.6:
            return
        # Match -- teleport. Preserve screen position so the camera
        # doesn't jump.
        screen_dx = p.x - game.cam_x
        screen_dy = p.y - game.cam_y
        p.x = dx_tx * TILE + 16
        p.y = dx_ty * TILE + 16
        game.cam_x = p.x - screen_dx
        game.cam_y = p.y - screen_dy
        scene._reloc_armed = False
    # NOTE: on_update_fn is assigned ONCE, further down, to a combined
    # handler that runs both this relocation logic and the corn-rustle
    # ambient. Assigning it here would be overwritten by that later
    # assignment (it was -- the relocation feature was silently dead).

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
        # In-maze direction-fold relocations ('I'/'Q' tiles) first --
        # this used to live in its own on_update_fn that this handler
        # silently overwrote, so the feature never ran.
        _maze_on_update(game, scene, dt)
        # Corn-rustle ambient.
        scene._rustle_t = getattr(scene, "_rustle_t", 3.0) - dt
        if scene._rustle_t <= 0:
            scene._rustle_t = random.uniform(2.5, 6.0)
            game.audio.play("breath", 0.18)
    sc.on_update_fn = _cornfield_maze_on_update
    sc.add_interactable(sc._scarecrow_pos[0], sc._scarecrow_pos[1], 40)  # [E] cue

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

    sc.hide_spots = []
    return sc


# ---------------------------------------------------------------------------
# The town. A populated main street -- the civic centre of the world.
#
# Wired to: the general store (shop), the sheriff's office
# (fisherman_cottage), the schoolhouse, and the road south back to the
# village/farm. The church stays out in the brimley, so the town
# reaches it the long way, through the fields.
# ---------------------------------------------------------------------------
def build_town():
    """Retired. The town came apart into the fog -- its street, civic
    buildings (Store, Sheriff, Schoolhouse) and residents now live in
    the brimley, displayed as Brimley. This stub survives only so a
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
        game.begin_transition("brimley", "from_village")

    sc.triggers.append({
        "rect": (0, 0, 5 * TILE, 5 * TILE),
        "fn": _bounce, "once": False, "fired": False,
    })
    return sc
