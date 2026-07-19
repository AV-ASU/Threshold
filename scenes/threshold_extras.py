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
    -- they all went below (the procession Toby watched). The chalk-door
    rite reopens their school door to the work-clearing. Hide spots:
    behind the cot banks, in the shoved-desk corner."""
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
    # THE SCHOOL DOOR: the commune's own way to the work-clearing. The
    # fold tile 'O' (a marker char: invisible, walkable) sits on the
    # indoor campfire spot; the rite (sweeten
    # the air at the fire, then draw the final door on the board) opens
    # it, and from then on it simply stands. Walked NORTH into.
    objects[4] = objects[4][:9] + "O" + objects[4][10:]
    sc = Scene("schoolhouse", floor, objects, music="home")
    sc.add_exit("H", "brimley", "from_school")
    sc.add_exit("O", "effigy_grove", "from_school", direction="north")
    sc.set_spawn("default", 7, 9)
    sc.set_spawn("from_brimley", 7, 10)       # one tile north of the H door
    # Back through the pane from the grove: one tile south of it, carried
    # southward so arrival never re-fires the north-walked crossing.
    sc.set_spawn("from_grove", 9, 5)

    def _door_charge(game, ch):
        if ch != "O":
            return 1.0
        if not game.save.flag("school_door_open"):
            return 0.0
        # Forms over a few seconds the moment it is drawn; on any later
        # load it simply stands.
        t0 = getattr(game, "_school_door_t0", None)
        if t0 is None:
            return 1.0
        import pygame as _pg
        return min(1.0, (_pg.time.get_ticks() - t0) / 2500.0)
    sc.fold_charge_fn = _door_charge

    def _door_gate(game, ch):
        if ch != "O":
            return True
        return (game.save.flag("school_door_open")
                and _door_charge(game, "O") >= 0.999)
    sc.exit_gate_fn = _door_gate

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
    # Genset-electric main light: two bulkhead lamps on the north wall
    # (the chalkboard wall), flanking the window, over the crammed cot rows
    # (the guttered candles are what the commune bedded down by). (2026-07.)
    sc.add_decoration(Decoration(4 * TILE + 16, 1 * TILE + 16, "wall_lamp"))
    sc.add_decoration(Decoration(11 * TILE + 16, 1 * TILE + 16, "wall_lamp"))
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

    # The chalkboard: a flavor beat until the rite is ready, then the act
    # itself (draw the final door). The rite's components live in the
    # room: chalk on the teacher's desk, incense among the cot relics,
    # the indoor campfire to burn it on.
    sc._board_pos = (7 * TILE + 16, 0 * TILE + 16)
    sc._chalk_pos = (2 * TILE + 16, 1 * TILE + 16)     # the teacher's desk
    sc._incense_pos = (12 * TILE + 16, 5 * TILE + 16)  # beside an east cot
    sc._fire_pos = (9 * TILE + 16, 4 * TILE + 16)      # the indoor campfire
    sc.add_interactable(sc._board_pos[0], sc._board_pos[1], 44)
    sc.add_interactable(sc._fire_pos[0], sc._fire_pos[1], 36)

    def _school_on_enter(game, scene):
        # Glimmer-mark the rite components still on offer (the woodshed
        # pattern) so they read as takeable among the relics.
        for pos, flag in ((scene._chalk_pos, "chalk_taken"),
                          (scene._incense_pos, "incense_taken")):
            if not game.save.flag(flag):
                scene.add_decoration(Decoration(pos[0], pos[1], "item_drop"))
                scene.add_interactable(pos[0], pos[1], 36)
        # The incense smoke still hangs once it has been burned.
        if game.save.flag("school_incense_lit"):
            scene.add_decoration(Decoration(scene._fire_pos[0],
                                            scene._fire_pos[1] - 8, "smoke"))
        if game.save.flag("schoolhouse_seen"):
            return
        game.save.set_flag("schoolhouse_seen", True)

    def _school_interact(game):
        px, py = game.player.x, game.player.y
        save = game.save
        inv = game.player.inventory
        # Chalk on the teacher's desk.
        cx, cy = sc._chalk_pos
        if abs(px - cx) < 36 and abs(py - cy) < 36:
            if not save.flag("chalk_taken"):
                save.set_flag("chalk_taken", True)
                inv.add("chalk", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("A stub of chalk off the teacher's desk.")
                game.scene.clear_ground_marker(cx, cy)
                return
        # Incense among the cot relics.
        ix, iy = sc._incense_pos
        if abs(px - ix) < 36 and abs(py - iy) < 36:
            if not save.flag("incense_taken"):
                save.set_flag("incense_taken", True)
                inv.add("incense", 1)
                game.audio.play("pickup_rare", 0.7)
                game.show_notice("Dried incense, left beside a cot.")
                game.scene.clear_ground_marker(ix, iy)
                return
        # The indoor campfire: where the air is sweetened.
        fx, fy = sc._fire_pos
        if abs(px - fx) < 36 and abs(py - fy) < 36:
            if save.flag("school_incense_lit"):
                game.show_notice("The smoke hangs in the room and does "
                                 "not drift.")
                return
            if inv.has("rite_envelope") and inv.has("incense"):
                inv.remove("incense", 1)
                save.set_flag("school_incense_lit", True)
                game.audio.play("low_pulse", 0.5)
                sc.add_decoration(Decoration(fx, fy - 8, "smoke"))
                game.dialog.show([
                    "[c=dim](You set the bundle on the cold ash and light "
                    "it. The smoke goes up in one straight line, sweet and "
                    "cold, and then it stops going anywhere. It hangs.)[/c]",
                    "[c=dim]The room smells the way it must have smelled "
                    "every night they slept here.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            if inv.has("rite_envelope"):
                game.audio.play("low_pulse", 0.4)
                game.show_notice("A fire burned flat on the floorboards. "
                                 "Sweeten the air, the sheet says. You "
                                 "have nothing to burn.")
                return
            game.show_notice("They burned a fire inside, on the "
                             "floorboards, the way squatters do.")
            return
        # The chalkboard.
        bx, by = sc._board_pos
        if abs(px - bx) <= 44 and abs(py - by) <= 44:
            if save.flag("school_door_open"):
                game.dialog.show([
                    "[c=dim](The lesson, the shrinking doors, and at the "
                    "corner your own hand, the smallest one. It is the "
                    "only door on the board that is open.)[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            if (inv.has("rite_envelope")
                    and save.flag("school_incense_lit")
                    and inv.has("chalk")):
                save.set_flag("school_door_open", True)
                import pygame as _pg
                game._school_door_t0 = _pg.time.get_ticks()
                game.audio.force_silence()
                game.audio.play("low_pulse", 0.9)
                game.dialog.show([
                    "[c=dim](The sequence stops one door short of the "
                    "corner. You set the chalk where the last hand left "
                    "off and draw it once more. Smaller. The smallest "
                    "one.)[/c]",
                    "[c=dim]The chalk goes through the board like a knife "
                    "through paper, and behind you the smoke leans toward "
                    "the old fire.[/c]",
                    "[c=dim]Something stands up in the middle of the "
                    "room.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            if inv.has("rite_envelope") and save.flag("school_incense_lit"):
                game.show_notice("The last door wants drawing. You have "
                                 "nothing to draw with.")
                return
            if inv.has("rite_envelope"):
                game.dialog.show([
                    "[c=dim](The chalkboard. Under a child's faded lesson, "
                    "the same door is drawn over and over, smaller and "
                    "smaller, to the corner.)[/c]",
                    "[c=dim]The sequence stops one door short. The "
                    "smallest one was never drawn. The sheet in your "
                    "pocket says the air comes first.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            game.dialog.show([
                "[c=dim](The chalkboard. Under a child's faded lesson, the "
                "same door is drawn over and over, smaller and smaller, to "
                "the corner.)[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return

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
    lodge_yard (from_country_lane). No interior building, no
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
    # East passage (e) -- to lodge_yard
    for dy in (-1, 0, 1):
        objects_l[6 + dy][W - 1] = "e"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("country_lane", floor_rows, objects, music="outside")
    sc.add_exit("a", "brimley", "from_country_lane")
    # East now lands on the ARRIVAL ROAD (the looping road W of the Lodge),
    # whose dirt path carries on east to the yard.
    sc.add_exit("e", "arrival_road", "from_country_lane")
    sc.set_spawn("default", 1, 6)
    # Player walked WEST off the arrival road: lands at the east end of the
    # lane, facing west toward town. (from_lodge_yard kept as an alias for
    # any save that still routes straight here.)
    sc.set_spawn("from_arrival_road", W - 2, 6)
    sc.set_spawn("from_lodge_yard", W - 2, 6)
    # Player walked EAST out of Brimley: lands at the west end of
    # the lane, facing east toward home.
    sc.set_spawn("from_brimley", 1, 6)

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

    # ---- The walked-out road (2026-07 detail pass) ----
    # The locals who went to flag down help walked EAST down this lane
    # and never came back: bootprints along the road that head east and
    # simply stop, well short of the seam.
    for fx, fy in ((17, 6), (20, 5), (23, 6), (25, 6)):
        sc.add_decoration(Decoration(fx * TILE + 16, fy * TILE + 16,
                                     "mud_footprint"))
    # The busted south fence sheds a plank; tins dumped off the north
    # shoulder (both noise traps along the cover lanes).
    sc.add_noise_trap(24 * TILE + 16, 9 * TILE + 16, "plank", seed=25)
    sc.add_noise_trap(9 * TILE + 16, 3 * TILE + 16, "cans", seed=26)
    for lx, ly in ((6, 4), (28, 8)):
        sc.add_decoration(Decoration(lx * TILE + 16, ly * TILE + 16,
                                     "leaves"))
    sc.hide_spots = []
    return sc


def build_graveyard():
    """Small graveyard behind the church. Iron fence, two crooked
    rows of headstones. One stone near the gate can be read.

    Hide spots: behind the larger headstones, in the gardener's
    shed at the back.
    """
    # Trodden dirt runs from the gate up through the plot, and the ground
    # around the stones is turned earth, not lawn (2026-07 audit: uniform
    # green grass read as a mown yard, not a neglected burial plot).
    floor_l = [list("g" * 14) for _ in range(10)]
    for py in (6, 7, 8):                    # the gate path, worn in
        floor_l[py][8] = "d"
    floor_l[5][8] = "d"
    for px, py in [(3, 2), (6, 2), (9, 2), (3, 4), (6, 4), (9, 4),
                   (3, 6), (6, 6), (9, 6), (4, 4), (7, 6)]:
        floor_l[py][px] = "d"               # turned earth at the graves
    floor = ["".join(r) for r in floor_l]
    objects = [
        "TTTTTTTTTTTTTT",   # 0  trees behind the fence
        "T............T",   # 1
        "T............T",   # 2  (the headstones are real props now, below)
        "T............T",   # 3
        "T............T",   # 4
        "T............T",   # 5
        "T............T",   # 6
        "T............T",   # 7
        "T............T",   # 8
        "TTTTTTTTHTTTTT",   # 9  H = exit south back to town
    ]
    sc = Scene("graveyard", floor, objects, music="village")
    # The graves: real carved headstone volumes (2026-07 audit fix: they
    # were 'R' ROCK tiles -- nine natural boulders standing in for the
    # scene's core identity object, on a perfect 3x3 lattice). Each stone
    # keeps its tile for collision but is jittered off the grid centre
    # and seeded so the slabs lean and vary; no two are colinear. The
    # worn stone (3,2) stays dead on its anchor: the candle, dead crow,
    # and the readable examine all key to that point.
    _stone_jit = [((3, 2), 0, 0, 3), ((6, 2), 9, -6, 11), ((9, 2), -7, 5, 4),
                  ((3, 4), 6, 7, 8), ((6, 4), -9, -4, 15), ((9, 4), 5, 9, 2),
                  ((3, 6), -6, -8, 9), ((6, 6), 8, 3, 6), ((9, 6), -4, -9, 13)]
    for (gtx, gty), jx, jy, gseed in _stone_jit:
        sc.add_furniture("headstone", [(gtx, gty)], dx=jx, dy=jy, seed=gseed)
    # Exit back into the church (the gate is in the back of the
    # parsonage). Routes to church, which has spawn
    # 'from_graveyard' set up.
    sc.add_exit("H", "church", "from_graveyard")
    sc.set_spawn("default", 7, 7)
    sc.set_spawn("from_church", 7, 7)

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
    sc.skybox_kind = "overcast"   # open-sky clearing, not the night void
    sc.add_exit("H", "gravel_road_north", "from_backwoods_cabin")
    sc.add_exit("D", "backwoods_cabin_interior", "from_outside")
    sc.set_spawn("default", 7, 9)
    sc.set_spawn("from_road", 7, 9)
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
    # Cordwood stack behind the cabin (west of door) -- a real firewood
    # volume (2026-07 audit fix: it was a raw 't' object tile, which no
    # tilt set draws and whose kind is TABLE anyway -- an invisible solid
    # that would have read as a dining table in a forest clearing).
    sc.add_furniture("firewood", [(3, 8)], w=44, h=22)
    # A hunter lived here: his antler rack stands against the cabin's
    # south face, west of the door (the docstring always promised hunter
    # tells; the yard read as any-shack without one).
    sc.add_furniture("antler_rack", [(5, 8)], w=22, h=46)
    # The lantern stands by the stump so the notepad (the one clue here)
    # sits inside its light pool in the real graded view (2026-07 audit
    # fix: the only light was clear across the yard from the only clue).
    sc.add_decoration(Decoration(9 * TILE + 20, 9 * TILE + 10, "lantern"))
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
    # Enclosed hide (the 2026-07 stealth pass, TODO #5): burrowed into
    # the hunter's cordwood stack behind the cabin.
    sc.hide_spots = [
        (3 * TILE + 16, 9 * TILE + 16, "in"),        # in the firewood stack
    ]

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
        "W.....W....W",   # 3  (the table is real furniture now, below)
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
    # The table as a real furniture volume (2026-07 audit fix: it was a
    # raw 't' object tile, which no tilt set draws -- the room's one
    # furniture piece was an invisible collision block and the candle
    # floated on bare boards). The candle seats on its top.
    sc.add_furniture("table", [(3, 3)], w=30, h=26)
    # A home, before it wasn't: the stove that heated it and the cot in
    # the back nook (2026-07 audit: without them the room read as a bare
    # wood box with crime-scene props, not a lived-in cabin).
    sc.add_furniture("stove", [(5, 1)], w=30, h=40)
    sc.add_furniture("cot", [(8, 3)], w=30, h=16)
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
    # A homestead that was lived in until it wasn't: the washstand still
    # by the door, a preserves shelf in the back nook nobody came back
    # to empty.
    sc.add_decoration(Decoration(1 * TILE + 18, 1 * TILE + 28, "washstand"))
    sc.add_decoration(Decoration(9 * TILE + 20, 0 * TILE + 22,
                                 "preserve_shelf", seed=27))
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
        "WWWWiWWWiWWW",    # 0  north-wall window slits (12 wide, matching
        #                       the rest -- row 0 carried a stray 13th tile)
        "W..........W",    # 1
        "W..........W",    # 2
        "i..........i",    # 3  east/west window slits
        "W..........W",    # 4  (the bell housing is real furniture now, below)
        "W..........W",    # 5
        "W..........W",    # 6
        "W..........W",    # 7
        "W..........W",    # 8
        "WWWWiWWLWWWW",    # 9  south-wall slit + L = stairs down to the church
    ]
    sc = Scene("bell_tower", floor_rows, objects, music="home")
    sc.add_exit("L", "church", "from_bell_tower")
    sc.set_spawn("default", 5, 8)
    sc.set_spawn("from_church", 7, 8)        # at the foot of the L stairs
    # The 2x2 bell-stock at centre as a real timber platform volume (a
    # scaled-up table box; 2026-07 audit fix: it was four raw 't' object
    # tiles, which no tilt set draws -- the column the player circles was
    # an invisible collision block and the bell hung off nothing).
    sc.add_furniture("table", [(5, 4), (6, 4), (5, 5), (6, 5)], scale=2.0)
    # The bell hangs off the housing's south face (drawn upward from its
    # lip, so under tilt it reads in front of the solid housing box),
    # with the pull rope dropping to hand height below it. E on the
    # rope rings it: the peal masks every small noise on the surface
    # and pulls the cult across Brimley to the church door
    # (Game._ring_bell / _tick_bell; the BELL_* config block).
    sc.add_decoration(Decoration(5 * TILE + 32, 5 * TILE + 28,
                                 "church_bell"))
    sc.add_decoration(Decoration(5 * TILE + 32, 6 * TILE + 5, "rope"))
    sc.add_interactable(5 * TILE + 32, 6 * TILE + 16, 44)
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16,
                                 "phantom_mark"))
    for i in range(8):
        sc.add_decoration(Decoration(40 + i * 36,
                                     60 + (i % 3) * 50, "mote"))
    sc.hide_spots = []

    def _bell_interact(game):
        px, py = game.player.x, game.player.y
        if (abs(px - (5 * TILE + 32)) > 44
                or abs(py - (6 * TILE + 16)) > 44):
            return
        game._ring_bell()
    sc.on_interact_fn = _bell_interact

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
    Two exits: south `!` back to cornfield_path; north `^` continues
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
    # South exit (back to cornfield_path) in lane 3 (cols 11-12).
    objects_l[H - 1][11] = "!"
    objects_l[H - 1][12] = "!"
    # North exit (into brimley) in lane 3 (cols 11-12).
    objects_l[0][11] = "^"
    objects_l[0][12] = "^"
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

    # ---- In-maze direction-fold RELOCATION tiles ----
    # Different from the scene-fold tiles above: these don't open a
    # new scene; they teleport you to ELSEWHERE IN THE SAME MAZE.
    # They are ordinary direction-gated exits whose target is the maze
    # itself (registered with add_exit below); Game.cross_fold handles
    # the same-scene case with no load and the camera carried, so the
    # swap is invisible at the moment of crossing. The player notices
    # when their surroundings stop matching. The chars 'I' and 'Q'
    # mark them in the objects layer (both render as floor, so the
    # relocation tiles are invisible -- the lie is the world itself,
    # never a visible frame).
    # 'I' at (8, 6) walked SOUTH -> teleport to (16, 19) (top of
    # lane 2 -> bottom of lane 4).
    objects_l[6][8] = "I"
    # 'Q' at (16, 11) walked NORTH -> teleport to (3, 19) (mid of
    # lane 4 -> bottom of lane 1).
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
    # camouflaged the same way brimley / cornfield_path are. Interior
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
        # South cornfield_path exit (cols 11, 12 at row H-1).
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
    sc.add_exit("!", "cornfield_path", "from_cornfield_maze")
    sc.add_exit("^", "brimley",   "from_cornfield_maze")
    # In-maze relocations: same-scene direction-gated folds (the 'I'/'Q'
    # tiles placed above). The target is the maze itself; Game.cross_fold
    # relocates with no load and the camera carried. Silent by canon --
    # _build_fold_cache skips same-scene folds, so no frame is drawn.
    sc.add_exit("I", "cornfield_maze", "reloc_I", direction="south")
    sc.add_exit("Q", "cornfield_maze", "reloc_Q", direction="north")
    sc.set_spawn("reloc_I", 16, 19)
    sc.set_spawn("reloc_Q", 3, 19)
    sc.set_spawn("default", 11, H - 2)
    sc.set_spawn("from_cornfield_path", 11, H - 2)
    sc.set_spawn("from_brimley", 11, 1)
    sc.set_spawn("from_brimley_south", 11, 1)
    # Return from effigy_grove -- one east of the Z tile so the player
    # doesn't immediately re-trigger walking west.
    # Return from the additional hidden-scene folds. One tile inland
    # from each fold tile in the direction the player came back from.

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
        # The 'I'/'Q' relocations that used to live here are ordinary
        # direction-gated exits now (Game.cross_fold handles the
        # same-scene swap). Only the corn-rustle ambient remains.
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
            _evidence(game, "scarecrow",
                "A scarecrow."
            )
            return
    sc.on_interact_fn = _cornfield_maze_interact

    # Litter in the lanes (2026-07 sound overhaul): tins dumped in lane
    # 2, and a crow posted in lane 4 that flushes screaming -- the maze
    # punishes a careless line even when nothing can see you.
    sc.add_noise_trap(6 * TILE + 16, 8 * TILE + 16, "cans", seed=13)
    sc.add_noise_trap(16 * TILE + 16, 10 * TILE + 16, "crow", seed=14)

    sc.hide_spots = []
    return sc
