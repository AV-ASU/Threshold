"""The depths -- everything below the basement level. The ritual at
well_bottom drops the player here; from this point the only
direction is down.

Floors, top to bottom:
  depths_antechamber  -- the fall zone
  depths_procession   -- the moving-candle column
  depths_hall         -- the kneeling grid
  depths_threshing    -- the threshing floor
  depths_stair        -- the empty spiral down
  dark                -- the hive: the congregation + Mara, turned (scene
                         key kept; was the old-family-bodies room)
  threshold           -- the doorframe

Hooded chasers populate the first three rooms. The flashlight is
force-disabled in all depths scenes. Hide spots placed liberally so
the player has cover to recover in.
"""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from entities.enemy import Enemy
from entities.npc import NPC
from .base import Scene
from .dialogue import _evidence


def _ambient(scene, sfx, vol, lo, hi):
    """Wire a periodic ambient sfx to the scene. Each room gets its
    own cue + period so the depths read as different spaces, not one
    repeated basement. Rides Scene.add_ambient, so it no longer
    claims on_update_fn for itself."""
    scene.add_ambient(sfx, vol, lo, hi)


def _cultist(x, y, speed=1.0):
    """Hooded chaser. Combat is gone, so atk is forced to 0 every
    tick by Enemy.update; the danger is contact -- the dread
    aperture slams to 0 if a cultist touches the player. Slightly
    slower than the player's walk so cover-running works. Aggro
    is short (~180px line of sight) and respects player.hidden, so
    the player can sneak past in cover and stand still in a hide
    spot to break the chase. In SCOUT it PURE-ROAMS (NARRATIVE §8) --
    no preset route; it picks its own reachable goals and paths around
    cover. Pin a stationary set-piece (a kneeler) by setting aggro=0 +
    lock_facing on the returned enemy instead of a one-point route."""
    e = Enemy(x, y, kind="cultist", hp=1, atk=0, speed=speed,
              aggro=180, atk_range=22, ai="chase",
              drops=[], can_charge=False)
    e.respawning = False
    e.respects_hide = True
    return e


def _box(w, h):
    """Return a (floor, objects) pair for a w x h walled room with
    walkable interior. Caller punches exits into objects after."""
    floor = ["x" * w for _ in range(h)]
    objects_l = []
    for y in range(h):
        if y == 0 or y == h - 1:
            objects_l.append(list("#" * w))
        else:
            row = ["#"] + ["."] * (w - 2) + ["#"]
            objects_l.append(row)
    return floor, objects_l


# --- Shape toolkit (CAMERA.md Phase 4: vary the underground silhouettes) ---
#
# The underground was a stack of identical rectangles. Under the tilted
# blind-spot camera the *shape* of a room is what makes a corner a place to
# hide or get cornered, so these carve distinct footprints out of a `_box`:
# octagons, L-bends, crosses, T's, apses, ragged caverns. Each just stamps
# '#' (solid wall) onto the interior; callers keep exits on open edges and
# place props/spawns in the remaining floor.

def _wall(objs, x0, y0, x1, y1, ch="#"):
    """Fill an inclusive tile rectangle with solid wall (clamped in-bounds)."""
    h = len(objs); w = len(objs[0])
    for y in range(max(0, y0), min(h, y1 + 1)):
        for x in range(max(0, x0), min(w, x1 + 1)):
            objs[y][x] = ch


def _bevel(objs, n, corners=("NW", "NE", "SW", "SE")):
    """Stair-step a 45-degree wall triangle of leg `n` into each named
    corner -- bevel all four and a rectangle reads as an octagon; bevel two
    on one side and it reads as an apse / hexagon."""
    h = len(objs); w = len(objs[0])
    for k in range(1, n + 1):
        span = n + 1 - k            # cells to wall inward at depth k
        if "NW" in corners:
            _wall(objs, 1, k, span, k)
        if "NE" in corners:
            _wall(objs, w - 1 - span, k, w - 2, k)
        if "SW" in corners:
            _wall(objs, 1, h - 1 - k, span, h - 1 - k)
        if "SE" in corners:
            _wall(objs, w - 1 - span, h - 1 - k, w - 2, h - 1 - k)


def _cavern(objs, seed, keep_rows=(), keep_cols=(), bite=0.55):
    """Gnaw an irregular cave edge: walk the interior border tiles and turn
    some to wall, deterministically by `seed`. Rows/cols in keep_* are left
    clear so exits + the central aisle stay open."""
    import random
    h = len(objs); w = len(objs[0])
    rng = random.Random(seed)
    edge = []
    for x in range(1, w - 1):
        edge += [(x, 1), (x, h - 2)]
    for y in range(1, h - 1):
        edge += [(1, y), (w - 2, y)]
    for (x, y) in edge:
        if y in keep_rows or x in keep_cols:
            continue
        if rng.random() < bite:
            objs[y][x] = "#"
            # occasionally bite one cell deeper for a lumpy edge
            if rng.random() < 0.4:
                yy = y + (1 if y < h // 2 else -1)
                xx = x + (1 if x < w // 2 else -1)
                if 1 <= yy < h - 1 and 1 <= xx < w - 1:
                    objs[yy][x] = "#"


def build_depths_antechamber():
    # A diamond pit -- the fall zone, walls beveled steeply back to a
    # near-diamond so you land in the middle of an open drop.
    floor, objs = _box(11, 11)
    _bevel(objs, 4)
    objs[5][10] = "E"   # east passage to procession
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_antechamber", floor, objects, music="basement")
    sc.add_exit("E", "depths_procession", "from_antechamber")
    sc.set_spawn("default",   5, 6)
    sc.set_spawn("from_above", 5, 5)
    sc.add_decoration(Decoration(3 * TILE + 16, 3 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 7 * TILE + 16, "candle"))
    # Two stone pillars flank the landing on the diagonal (clear of the
    # mid-row passage to the east exit and the cultist's loop).
    sc.add_furniture("pillar", [(7, 3)])
    sc.add_furniture("pillar", [(3, 7)])
    sc.add_decoration(Decoration(5 * TILE + 16, 5 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(6 * TILE + 16, 7 * TILE + 16, "bloodstain"))
    # Cobweb grime in the beveled corners of the fall zone.
    sc.add_decoration(Decoration(2 * TILE + 6, 2 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 8 * TILE + 26, "cobweb",
                                 ang=math.pi))
    # A supply crate from the old workings, and the gap beneath it: one
    # enclosed hide near the patrol loop (STEALTH_REWORK §6).
    sc.add_furniture("crate", [(7, 4)])
    sc.hide_spots = [
        (7 * TILE + 16, 5 * TILE + 8, "under"),    # under the old crate
    ]
    # One cultist patrolling a small loop around the landing.
    sc.add_enemy(_cultist(7 * TILE + 16, 6 * TILE + 16, speed=0.85))
    _ambient(sc, "cult_breath", 0.18, 6.0, 10.0)

    sc.add_interactable(5 * TILE + 16, 5 * TILE + 16, 36)   # [E] cue for the landing
    # Chalk doors -- the motif at its worst, this deep. The voice beat (panic)
    # rides examining one; placed clear of the landing so it never steals the
    # the_fall evidence.
    sc.add_chalk_door(3 * TILE + 16, 5 * TILE + 16, voice="chalk_deep", seed=6)
    sc.add_chalk_door(7 * TILE + 16, 3 * TILE + 10, seed=1, wall=True)

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - (5 * TILE + 16)) < 36 and abs(py - (5 * TILE + 16)) < 36:
            _evidence(game, "the_fall",
                "There is no way back above you and you are not hurt. The "
                "way down didn't want you broken, only delivered. Cut stone, "
                "worn smooth by years of feet that came this way before you."
            )
    sc.on_interact_fn = _interact
    return sc


def build_depths_procession():
    # A colonnade comb: a long E-W processional with alcove bays (teeth)
    # jutting off north and south, staggered so the column never reads as
    # one straight sightline.
    floor, objs = _box(16, 9)
    _wall(objs, 1, 1, 14, 2)            # seal the top band...
    for cx in (3, 4, 8, 9, 12, 13):    # ...then open north bays (teeth)
        objs[1][cx] = "."
        objs[2][cx] = "."
    _wall(objs, 1, 6, 14, 7)           # seal the bottom band...
    for cx in (2, 3, 6, 7, 11, 12):    # ...then open south bays
        objs[6][cx] = "."
        objs[7][cx] = "."
    objs[4][15] = "E"   # east to hall
    objs[8][6] = "D"    # south (off a bay) -> the ossuary (dead-end branch)
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_procession", floor, objects, music="basement")
    sc.add_exit("E", "depths_hall", "from_procession")
    sc.add_exit("D", "the_ossuary", "from_procession")
    sc.set_spawn("default",          1, 4)
    sc.set_spawn("from_antechamber", 1, 4)
    sc.set_spawn("from_the_ossuary", 6, 6)   # back up from the ossuary branch
    # A line of candles along the centre, suggesting the procession
    # column. Two cultists walking it at this hour.
    for cx in range(2, 14, 2):
        sc.add_decoration(Decoration(cx * TILE + 16, 4 * TILE + 16,
                                     "candle"))
    # A colonnade of stone pillars flanking the central walk (clear of the
    # bays and the walking line).
    for px in (5, 10):
        sc.add_furniture("pillar", [(px, 3)])
        sc.add_furniture("pillar", [(px, 5)])
    # Cobweb grime in the high corners of the procession column.
    sc.add_decoration(Decoration(1 * TILE + 6, 3 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 26, 3 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # A crate tucked in a south bay + the gap under it: one enclosed hide
    # off the column (STEALTH_REWORK §6) -- the bays themselves are the
    # concealment; this is the rooted option a searcher can check.
    sc.add_furniture("crate", [(12, 7)])
    sc.hide_spots = [
        (11 * TILE + 24, 7 * TILE + 16, "under"),  # beside the bay crate
    ]
    # Two cultists walking the column, single file, opposite phases
    # so they meet between (5..12) and pass each other. Endpoints
    # held away from the west-edge spawn (col 1) so the player
    # arrives with breathing room.
    sc.add_enemy(_cultist(5 * TILE + 16, 4 * TILE + 16, speed=0.9))
    sc.add_enemy(_cultist(11 * TILE + 16, 4 * TILE + 16, speed=0.9))
    _ambient(sc, "blip_soft", 0.12, 2.5, 4.5)

    # The procession's one diegetic beat (TODO #8): the candle line read
    # up close. Wax on old wax -- they filed to the rite many more times
    # than once, and never hurried. Narration + a case NOTE (never
    # evidence; the six canonical beats are locked).
    sc.add_interactable(8 * TILE + 16, 4 * TILE + 16, 36)

    def _candles_interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - (8 * TILE + 16)) > 36 or abs(py - (4 * TILE + 16)) > 36:
            return
        if game.save.flag("procession_candles_read"):
            game.dialog.show([
                "[c=dim]The wax holds its little lights steady. Nobody "
                "hurried here. The wax says nobody ever hurried.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        game.save.set_flag("procession_candles_read", True)
        game.audio.play("low_pulse", 0.4)
        game.dialog.show([
            "[c=dim]A line of candles down the dark, burned to coins. Each "
            "one stands in older wax, and older wax under that.[/c]",
            "[c=dim]They walked this in single file, carrying light, many "
            "more times than once. Nobody hurried. The wax says nobody "
            "ever hurried.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        if hasattr(game, "_log_note"):
            game._log_note("the_procession", [
                "A candle line tended half a mile under Brimley, wax on "
                "old wax. They filed to their rite the way other towns "
                "file to Sunday service. Unhurried. Certain.",
            ])
    sc.on_interact_fn = _candles_interact
    return sc


def build_depths_hall():
    # A cruciform basilica: a long E-W nave to the iron door, crossed by a
    # N-S transept near its middle. The corners are solid stone, so the
    # kneeling grid is reached only down the nave and across the crossing.
    floor, objs = _box(15, 11)
    _wall(objs, 1, 1, 7, 3)        # NW
    _wall(objs, 11, 1, 13, 3)      # NE
    _wall(objs, 1, 7, 7, 9)        # SW
    _wall(objs, 11, 7, 13, 9)      # SE
    objs[5][14] = "E"   # east to threshing floor (the iron door)
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_hall", floor, objects, music="basement")
    sc.add_exit("E", "depths_threshing", "from_hall")
    sc.set_spawn("default",        1, 5)
    sc.set_spawn("from_procession", 1, 5)
    # The east wall holds the iron door the kneeling grid faces.
    # Three cultists in the room: two flanking the door, one on
    # patrol. Hide spots scatter so the player can pick a route.
    sc.add_decoration(Decoration(13 * TILE + 16, 5 * TILE + 16,
                                 "phantom_mark"))
    # A "wrong" mount watching from the transept wall -- belongs to the dark.
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 18,
                                 "wrong_taxidermy", wall="N", seed=21))
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(5 * TILE + 16, 6 * TILE + 16, "candle"))
    # Pews in two rows down the nave, a clear central aisle (row 5) between
    # them up to the iron door.
    for px in (2, 4, 6):
        sc.add_furniture("pew", [(px, 4)])
        sc.add_furniture("pew", [(px, 6)])
    # Cobweb grime in the transept ends.
    sc.add_decoration(Decoration(8 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 8 * TILE + 26, "cobweb",
                                 ang=math.pi))
    # One enclosed hide on the nave route (STEALTH_REWORK §6): under a
    # pew, in the roamer's sweep range.
    sc.hide_spots = [
        (4 * TILE + 16, 5 * TILE + 24, "under"),   # under a nave pew
    ]
    # Two stationary cultists kneel at the iron door, facing east.
    # Aggro starts at 0 (oblivious) so they don't react until the
    # crossing trigger flips them. aggro=0 + lock_facing pins them in
    # place (a stationary set-piece, exempt from the SCOUT roam) and keeps
    # them turned toward the door. The third cultist roams, regardless.
    kneel_a = _cultist(12 * TILE + 16, 4 * TILE + 16, speed=0.8)
    kneel_b = _cultist(12 * TILE + 16, 6 * TILE + 16, speed=0.8)
    for k in (kneel_a, kneel_b):
        k.aggro = 0
        k.facing = (1, 0)
        k.lock_facing = True
    sc.add_enemy(kneel_a)
    sc.add_enemy(kneel_b)
    # A third cultist roams the transept freely (pure-roam SCOUT).
    sc.add_enemy(_cultist(9 * TILE + 16, 8 * TILE + 16, speed=0.95))

    # Crossing trigger: stepping into the transept crossing on the way to
    # the door wakes the kneelers.
    def _alert_kneelers(game):
        for e in sc.enemies:
            if e.kind == "cultist" and getattr(e, "aggro", 0) == 0:
                e.aggro = 600
                e.lock_facing = False
        game.audio.play("low_pulse", 0.55)
        # The narrative half of the trigger (TODO #8): the grid was
        # facing the door, and it turns as one body. Not startled. Called.
        game.show_notice("The kneeling rise together. Not startled. Called.",
                         duration=2.8)
    sc.triggers.append({
        "rect": (8 * TILE, 1 * TILE, 11 * TILE, 10 * TILE),
        "fn": _alert_kneelers,
        "once": True,
        "fired": False,
    })
    _ambient(sc, "whisper", 0.14, 7.0, 12.0)

    return sc


def build_depths_threshing():
    # A raw cavern -- ragged, bitten-out walls (the room the dig opened into,
    # never squared off), the threshing heaps raked across its floor.
    floor, objs = _box(13, 11)
    _cavern(objs, seed=7, keep_rows=(5,), bite=0.4)
    objs[5][12] = "E"   # east to stair
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_threshing", floor, objects, music="basement")
    sc.add_exit("E", "depths_stair", "from_threshing")
    sc.set_spawn("default",   1, 5)
    sc.set_spawn("from_hall", 1, 5)
    # Ambient dig labour: miners working the side faces (pickaxe in profile,
    # facing the wall) while chanters sway at the dig's mouth. All idle NPCs
    # with NO tag -> excluded from the cultist-gaze tick (no visibility, no
    # chase, no grab); non-solid. The dig toward the door made present, and
    # the rite chanted over it (NARRATIVE 1b / The Digging note).
    # NB: keep these on OPEN floor (rows 8-9 have wall pillars at cols 2/5/8) --
    # a body stamped on a '#' is embedded in the wall and never draws.
    for mx, my, mf, mp in [(6, 8, (-1, 0), "mine"), (7, 8, (1, 0), "mine"),
                           (4, 9, (-1, 0), "mine"),
                           (6, 9, (0, 1), "chant"), (9, 9, (0, 1), "chant")]:
        nm = "A digger" if mp == "mine" else "A chanter"
        m = NPC(mx * TILE + 16, my * TILE + 16, nm, "cultist",
                movement="idle", solid=False, no_prompt=True)
        m.facing = mf
        m.pose = mp
        sc.add_npc(m)
    # The yield. Grain mixed with old blood. Hide spots tuck into the cavern's
    # pockets.
    for bx, by in [(4, 4), (6, 5), (8, 6), (5, 7), (7, 4)]:
        sc.add_decoration(Decoration(bx * TILE + 16, by * TILE + 16,
                                     "bloodstain"))
    # The yield itself: raked cones of tithed grain (3D heaps), clear of the
    # central walk (row 5) and the heap the player reads (6, 5).
    for gx, gy in [(4, 4), (8, 4), (4, 7), (8, 7)]:
        sc.add_furniture("grain_heap", [(gx, gy)])
    sc.add_decoration(Decoration(6 * TILE + 16, 5 * TILE + 16,
                                 "phantom_mark"))
    # Diegetic light: wall torches set against the side walls so the dig reads
    # without the flashlight (Game._draw_dark punches each one's warm pool into
    # the gloom). Flank the upper room and the dig face below.
    for tx, ty in [(2, 3), (10, 3), (2, 7), (10, 7)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "wall_torch"))
    # Cobweb grime in the cavern's bitten corners.
    sc.add_decoration(Decoration(2 * TILE + 6, 2 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 2 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = []
    _ambient(sc, "step_grass", 0.22, 3.5, 6.0)
    sc.add_interactable(6 * TILE + 16, 5 * TILE + 16, 36)   # [E] cue: the threshing heaps

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - (6 * TILE + 16)) < 36 and abs(py - (5 * TILE + 16)) < 36:
            _evidence(game, "threshing_floor",
                "The yield, raked into low heaps: grain, all of it, tithed "
                "down from the fields above. The town's whole harvest, given "
                "over to the dark below, carried down and never carried "
                "back up. An offering. Not a stockpile."
            )
    sc.on_interact_fn = _interact
    return sc


def build_depths_stair():
    # An octagonal shaft -- the stair head opening into a round well that
    # spirals down into the Dark.
    floor, objs = _box(9, 11)
    _bevel(objs, 3)
    objs[10][4] = "D"   # south to dark
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_stair", floor, objects, music="basement")
    sc.add_exit("D", "dark", "from_stair")
    sc.set_spawn("default",        1, 5)
    sc.set_spawn("from_threshing", 1, 5)
    # One candle at the head of the stair. The Stair is empty per
    # design -- silence is the keeper.
    sc.add_decoration(Decoration(4 * TILE + 16, 4 * TILE + 16, "candle"))
    sc.hide_spots = []
    _ambient(sc, "low_pulse", 0.10, 11.0, 16.0)

    return sc


def build_the_ossuary():
    """A bone vault off the procession -- a tall hexagonal cell where the
    fold's lost are shelved: not the murdered (the cult kills no one), but
    the ones the dark took early, their leavings racked and labelled. A
    dead-end pocket of dread and cover."""
    floor, objs = _box(9, 12)
    _bevel(objs, 2)
    objs[0][4] = "F"          # north -> back to the procession
    objects = ["".join(r) for r in objs]
    sc = Scene("the_ossuary", floor, objects, music="basement")
    sc.add_exit("F", "depths_procession", "from_the_ossuary")
    sc.set_spawn("default",         4, 6)
    sc.set_spawn("from_procession", 4, 2)
    # Racks of shelved bones (3D) line the niches, old stains beneath them;
    # candles gutter between.
    for sx, sy in [(2, 4), (6, 4), (2, 8), (6, 8)]:
        sc.add_furniture("bone_rack", [(sx, sy)])
        sc.add_decoration(Decoration(sx * TILE + 16, sy * TILE + 16,
                                     "bloodstain"))
    sc.add_decoration(Decoration(4 * TILE + 16, 3 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(2 * TILE + 16, 6 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(6 * TILE + 16, 9 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(1 * TILE + 6, 9 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(7 * TILE + 26, 9 * TILE + 6, "cobweb",
                                 ang=math.pi))
    sc.hide_spots = []
    _ambient(sc, "whisper", 0.12, 7.0, 12.0)
    sc.add_interactable(4 * TILE + 16, 9 * TILE + 16, 36)   # [E] cue: the shelves
    # Optional lore: The Digging (third, deepest testimony fragment), racked
    # with one lost digger's leavings. Pure lore, gates nothing.
    sc._dig_note_pos = (6 * TILE + 16, 9 * TILE + 16)
    sc.add_interactable(sc._dig_note_pos[0], sc._dig_note_pos[1], 36)

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - (4 * TILE + 16)) < 36 and abs(py - (9 * TILE + 16)) < 36:
            _evidence(game, "the_ossuary_shelves",
                "Shelves of leavings: shoes, spectacles, a wedding band worn "
                "thin, racked and labelled in the Clerk's hand. Not trophies. "
                "An inventory of everything the dark took before it learned to "
                "leave the body walking.")
            return
        nx, ny = sc._dig_note_pos
        if abs(px - nx) < 36 and abs(py - ny) < 36:
            if not game.save.flag("ossuary_digging_taken"):
                game.save.set_flag("ossuary_digging_taken", True)
                game.player.inventory.add("cult_digging", 1)
                game.audio.play("pickup_rare", 0.6)
                game._log_note("cult_digging", [
                    "The last pages stop being sentences. Just the word door, "
                    "over and over, pressed hard enough to tear the paper. "
                    "Whatever these people used to be, the digging finished it.",
                ])
                game.show_notice("The Digging. Their last pages.")
                return
    sc.on_interact_fn = _interact
    return sc


def _mara_voice(game, npc):
    """Mara's one-shot recognition -- the #6 payoff. The case was never a
    rescue; you went deeper and found her already gone. After it, she has
    gone back to the kneeling."""
    if game.save.flag("hive_seen"):
        game.dialog.show(
            ["[c=dim]She has gone back to the kneeling. She won't look at "
             "you again.[/c]"],
            speaker="", voice="blip_soft", portrait="narrator")
        return
    game.save.set_flag("hive_seen", True)
    game.audio.force_silence()
    game.audio.play("low_pulse", 0.6)

    def _lure_collision():
        # TODO #7 -- the lure chain, felt ONCE (NARRATIVE §1/§10 fence:
        # never stated, no chain named; the PI starts the thought and
        # declines to finish it). Only for a player who lived the dream
        # (flashback_seen); for anyone else her lines stand alone.
        if not game.save.flag("flashback_seen"):
            return
        game.dialog.show([
            "[c=dim](A door in your sleep, a year back. Then a grief job "
            "you had no reason to take, and an itch that drove you north "
            "with it.)[/c]",
            "[c=dim](And every road in handed you here. To her, kneeling. "
            "You start the arithmetic of that, and you put it down. Some "
            "sums you don't finish standing up.)[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")

    # File evidence #6 FIRST and silently (show=False): the log + the
    # King-gate land immediately, and the one-line evidence dialog no
    # longer CLOBBERS her four lines (dialog.show replaces the open
    # box, so the old order showed the player only the summary and the
    # whole exchange was lost). The notebook keeps the summary text.
    _evidence(game, "the_congregation", [
        "Mara, kneeling with the congregation. Turned. There was never "
        "anyone to bring back. Only this, and now you're in it with her.",
    ], show=False)
    game.dialog.show([
        "[c=dim](You say her name. The hooded head lifts. It is Mara.)[/c]",
        "\"My father sent you. Of course he did. He never could let a thing "
        "stay lost.\"",
        "[s=slow]\"Tell him what I told him at the start. I'm not lost. I have "
        "never been this close.\"[/s]",
        "[c=dim]\"There was no one down here to bring back. I was not taken. I "
        "was answered, and I went to it gladly. Go home, while the town still "
        "lets you think you can.\"[/c]",
    ], speaker="", voice="blip_soft", portrait="narrator",
        on_complete=_lure_collision)


def build_dark():
    floor, objs = _box(12, 10)
    objs[8][3] = "D"   # south-west to threshold -- off the centre aisle,
                       # so the player never has to push through Mara
    objects = ["".join(r) for r in objs]
    sc = Scene("dark", floor, objects, music="basement")
    sc.add_exit("D", "threshold", "from_dark")
    sc.set_spawn("default",    6, 1)
    sc.set_spawn("from_stair", 6, 1)
    # The hive. The flashlight is force-off here (CULT_DARK_SCENES) so the
    # dread aperture's clear circle is the only light -- you find the
    # congregation a face at a time. They're NPCs, not enemies: no chase,
    # no contact penalty. The room's whole work is the recognition.
    def _murmur(game, npc):
        game.dialog.show(
            ["[c=dim]The kneeler doesn't stir. Its lips move, no sound.[/c]"],
            speaker="", voice="blip_soft", portrait="narrator")
    # The congregation: hooded, idle, facing the south doorframe they
    # worship. Solid, so the player threads between them in the dark.
    for kx, ky in [(3, 4), (8, 4), (4, 6), (9, 6), (8, 7)]:
        n = NPC(kx * TILE + 16, ky * TILE + 16, "A kneeler", "cultist",
                dialogue_fn=_murmur, movement="idle")
        n.facing = (0, 1)
        sc.add_npc(n)
    # Mara, front and centre on the aisle -- the one head that lifts when
    # you speak. Just one more hooded kneeler until you reach her.
    mara = NPC(6 * TILE + 16, 5 * TILE + 16, "Mara", "cultist",
               dialogue_fn=_mara_voice, movement="idle")
    mara.facing = (0, -1)
    sc.add_npc(mara)
    sc.hide_spots = []
    _ambient(sc, "heartbeat", 0.18, 3.5, 5.0)
    return sc


def build_threshold():
    # An underground RIVER CAVE -- not a box, and LONG: the player comes up from
    # the dark at the far SOUTH and walks a long way north, through a choked
    # stalagmite field, before reaching the frame. Ragged organic rock walls; the
    # artery-river (NARRATIVE 1b) is the whole WEST boundary, fed by a wide
    # waterfall at the south-west and running off the north edge. The one place
    # the cave goes WRONG is the doorframe: a 5x5 of impossibly smooth, level
    # grey stone swept utterly clear of stalagmites -- geometry serving the door
    # (the seed of the spatial fold), its emptiness the more uncanny for the
    # choked field crowding right to its edge. Nothing here is man-made.
    W, H = 14, 40
    floor, objs = _box(W, H)
    floor = [list(r) for r in floor]          # mutable rows for the edits below
    # Carve the organic cave edge, but keep the WEST columns (the river + its
    # bank live there) and the central approach lane out of the carve so the
    # river meander reads cleanly and the walk is never walled off.
    _cavern(objs, seed=771, keep_cols=(1, 2, 3, 4, 6, 7, 8))
    for _y in range(H):
        for _x in range(W):
            floor[_y][_x] = "x"
    # The artery: a MEANDERING river near the west cliff. Its 2-wide channel
    # wanders east/west down the long cave (a sine meander); where it swings east
    # toward the middle, normal stone floor shows between it and the west wall --
    # a proper riverBANK, so the river reads as CURVING, not a line ruled flush
    # to the rock. IMPASSABLE (invisible-solid over water), OPEN off the north.
    def _river_span(ty):
        we = 1 + int(round(2 * (0.5 + 0.5 * math.sin(ty * 0.40 + 0.7))))  # west 1..3
        return we, we + 1                                                  # 2-wide
    for _y in range(0, H - 1):
        we, ea = _river_span(_y)
        for _x in range(we, ea + 1):
            objs[_y][_x] = "X"; floor[_y][_x] = "~"
    # The doorframe sits MID-cave (row DR): the player walks far up from the far
    # south to reach it, and there is open cave + river NORTH of it, giving the
    # water room to pass through and loop back into the river. A 5x5 of smooth
    # grey stone ("0") is swept clear around the frame.
    DR = 25
    for _y in range(DR - 2, DR + 3):
        for _x in range(5, 10):
            objs[_y][_x] = "."; floor[_y][_x] = "0"
    objects = ["".join(r) for r in objs]
    sc = Scene("threshold", floor, objects, music="void")
    sc.skybox_kind = "void"
    sc.set_spawn("default",   7, 38)
    sc.set_spawn("from_dark", 7, 38)
    # Doorframe on the apron (the cave's north-centre). It is ONLY a frame -- a
    # door with no wall, nothing in the opening (NARRATIVE 1b). You SEAL by
    # walking THROUGH it carrying the keystone (the Pallid Mask), spent there
    # (§7, Mask-only); the walk-through is handled in on_update below. No [E]
    # prompt, no glow, no smoke. The keystone was carried down (the Deep Stair
    # opened WITHOUT spending it), so a player who descended always holds it.
    lintel_x, lintel_y = 7 * TILE + 16, DR * TILE + 16
    sc._lintel_pos = (lintel_x, lintel_y)
    sc.add_decoration(Decoration(lintel_x, lintel_y, "doorframe"))

    # The waterfall: ONE wide spring (~3 tiles) gushing from a hole in the
    # south-west cliff, covering the whole river mouth (NARRATIVE 1b -- the
    # artery's visible source). The river flows north from here.
    sc.add_decoration(Decoration(2 * TILE + 16, 37 * TILE + 16, "waterfall",
                                 w=110))

    # Stalagmites choking the long floor in organic clusters -- crowding right up
    # to the apron's edge (a dense ring) so the swept 5x5 reads as a wound of
    # order in the chaos, its emptiness the more noticeable. The central cols 6-8
    # lane stays clear so the long walk is never blocked. Solid; size varies.
    rng = random.Random(913)
    for ty in range(2, H - 1):
        for tx in range(3, W - 1):
            if sc.objects[ty][tx] != ".":
                continue
            if 5 <= tx <= 9 and DR - 2 <= ty <= DR + 2:   # the clean apron
                continue
            if 6 <= tx <= 8 and ty >= DR - 2:             # the central approach lane
                continue
            ring = ((tx in (4, 10) and DR - 2 <= ty <= DR + 2)
                    or (ty == DR + 3 and tx in (4, 5, 9, 10)))
            if rng.random() < (0.92 if ring else 0.42):
                sc.objects[ty][tx] = "X"
                sc.add_decoration(Decoration(
                    tx * TILE + 16, ty * TILE + 16, "stalagmite",
                    seed=tx * 31 + ty * 17, scale=round(rng.uniform(0.7, 1.3), 2)))

    # The river THREAD (NARRATIVE 1b): ONE continuous, organic side-channel that
    # branches OFF the river (the west wall) and returns to it -- a natural
    # distributary, not a drawn loop across the room. It leaves the channel low
    # in the south-west, is pulled east to the doorframe (the lowest place in the
    # earth; water finds it), passes UNDER the frame, then curves back and
    # rejoins the river up near the north wall. Both ends touch the river; the
    # door is the farthest it reaches. Smoothed into a flowing curve at draw time.
    _tw = [(3.5, 2.0),                         # off the river at the NORTH (H 2)
           (4.6, 4.0), (5.6, 6.5), (5.0, 9.0), (6.0, 11.5), (6.6, 14.0),
           (5.9, 16.5), (6.8, 19.0), (6.3, 21.5), (7.0, 23.5),
           (7.0, 25.0),                        # under the frame (the low point)
           (7.0, 26.5), (6.3, 28.5), (6.9, 30.5), (5.8, 32.5), (4.9, 34.5),
           (3.8, 36.0),
           (2.6, 37.0)]                        # back into the river at the SOUTH (H 37)
    _world = [(c * TILE + 16, r * TILE + 16) for (c, r) in _tw]
    _cx = sum(p[0] for p in _world) / len(_world)
    _cy = sum(p[1] for p in _world) / len(_world)
    sc.add_decoration(Decoration(
        _cx, _cy, "water_channel", seed=42,
        path=[(px - _cx, py - _cy) for (px, py) in _world]))
    # a shallow standing pool gathered at the frame's foot -- the low point
    sc.add_decoration(Decoration(lintel_x, lintel_y + 6, "water_trail",
                                 pool=True, seed=99))

    # Natural cave dressing only -- nothing man-made down here. Cobwebs strung in
    # the ragged high corners + a few drifting mist patches low in the dark.
    for (cwx, cwy, a) in ((1, 1, 0.0), (12, 1, math.pi / 2),
                          (12, 19, math.pi), (1, 37, -math.pi / 2),
                          (12, 37, math.pi)):
        sc.add_decoration(Decoration(cwx * TILE + 6, cwy * TILE + 6,
                                     "cobweb", ang=a))
    for (mx, my) in ((9, 11), (5, 17), (11, 23), (4, 28), (10, 32),
                     (6, 35), (8, 25)):
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mist"))

    def _threshold_on_enter(game, scene):
        if game.save.flag("first_threshold"):
            return
        game.save.set_flag("first_threshold", True)

        def _log_doorframe():
            _evidence(game, "the_doorframe",
                "A doorframe with no wall."
            )
        # 'He knows you': if the PI dreamed this doorway (read Mara's
        # journal through), recognition lands as ONE quiet line first,
        # then the doorframe logs. Otherwise just the doorframe.
        if game.save.flag("flashback_seen"):
            game.dialog.show(
                ["[c=dim]You have stood here before. In sleep.[/c]"],
                speaker="", voice="blip_soft", portrait="narrator",
                on_complete=_log_doorframe)
        else:
            _log_doorframe()
    sc.on_enter_fn = _threshold_on_enter

    # The SEAL: walking THROUGH the empty frame carrying the keystone (the
    # Pallid Mask). The crossing plays as LIVE ACTION first: you go through,
    # and the world FOLLOWS you -- the cave's own dressing tears loose and
    # pours through the frame, then foreign things stream in from beyond
    # the dark (brush, the houses' insides, a pew, the town's NAME, last
    # through before the door slams) -- every acre the cult bent, funneling
    # through the one door. Then the approved black-screen lines + the
    # wordless tableau take over (_play_ending("seal_threshold")). Without
    # the Mask the frame is only a frame; it never opens (NARRATIVE 1b).
    SEAL_WARP_DUR = 4.8
    _WARP_FOREIGN = [
        (1.60, "bush"), (1.75, "tall_grass"), (1.90, "firewood"),
        (2.05, "grass_tuft"), (2.20, "crate"), (2.35, "barrel"),
        (2.50, "chair"), (2.65, "kerosene_lamp"), (2.80, "corn_doll"),
        (2.95, "wheelbarrow"), (3.10, "calendar"), (3.25, "photo"),
        (3.40, "radio"), (3.55, "doll"), (3.70, "stalk_marker"),
        (3.85, "pew"), (4.05, "town_sign"),
    ]

    def _begin_seal_warp(game, scene):
        rng = random.Random(417)
        pending = [(rng.uniform(0.25, 2.0), d) for d in scene.decorations
                   if d.kind != "doorframe"]          # the door itself stays
        game._seal_warp = {
            "t": 0.0, "door": (lintel_x, lintel_y - 2),
            "pending": sorted(pending, key=lambda e: e[0]),
            "flights": [], "foreign": list(_WARP_FOREIGN), "rng": rng,
            "cues": set(),
        }
        game._closure_locked = True                   # he has crossed; hold
        game.dialog.active = False                    # nothing talks over it
        game.narration.clear()
        game.float_speech.active = False
        game.float_speech.speaker = None
        game.notice_text = None
        game.audio.force_silence()
        game.audio.play("arg_chime", 0.7)
        game.audio.flashback_air(True)                # the falling-air bed
        if game.audio.enabled:                        # the pressure under it
            game.audio.drive_channel.play(game.audio.carcosa_drone_snd,
                                          loops=-1)
            game.audio.drive_channel.set_volume(0.0)

    def _threshold_seal(game, scene):
        if (getattr(game, "_ending_active", None)
                or getattr(game, "_seal_warp", None)):
            return                                    # already sealing
        p = game.player
        if p is None:
            return
        if abs(p.x - lintel_x) > 16 or abs(p.y - lintel_y) > 18:
            return                                    # not in the frame yet
        inv = p.inventory
        if not inv.has("pallid_mask"):
            if not game.save.flag("threshold_blank_seen"):
                game.save.set_flag("threshold_blank_seen", True)
                game.show_notice("You step through the frame. You are standing "
                                 "in the same room. It is only a frame, and "
                                 "cold.")
            return
        inv.remove("pallid_mask", 1)                # spent at the door
        # File the beat SILENTLY (show=False): no narrator box may talk
        # over the warp -- the world going through the door IS the line.
        _evidence(game, "the_seal", "It is done.", show=False)
        _begin_seal_warp(game, scene)

    def _tick_seal_warp(game, scene, sw, dt):
        """Drive the live warp: launch the room's dressing, stream in the
        world beyond, fly every flight into the frame (accelerating,
        shrinking, gone), then hand off to the ending."""
        sw["t"] = t = sw["t"] + dt
        dx, dy = sw["door"]
        rng = sw["rng"]
        # The dread builds the whole pour: the drone swells under the
        # falling air, whispers + static stack as the world goes through.
        if game.audio.enabled:
            game.audio.drive_channel.set_volume(
                min(0.55, (t / SEAL_WARP_DUR) * 0.65))
        for cue, at, name, vol in (("w1", 1.8, "whisper", 0.30),
                                   ("s1", 2.4, "static", 0.30),
                                   ("w2", 3.2, "whisper", 0.45),
                                   ("s2", 3.8, "static", 0.35),
                                   ("w3", 4.3, "whisper", 0.55)):
            if t > at and cue not in sw["cues"]:
                sw["cues"].add(cue)
                game.audio.play(name, vol)
        while sw["pending"] and sw["pending"][0][0] <= t:
            _, d = sw["pending"].pop(0)
            dur = max(0.35, min(0.95,
                                math.hypot(d.x - dx, d.y - dy) / 420.0))
            sw["flights"].append({"d": d, "sx": d.x, "sy": d.y,
                                  "t0": t, "dur": dur, "s0": d.scale})
        while sw["foreign"] and sw["foreign"][0][0] <= t:
            _, kind = sw["foreign"].pop(0)
            ang = rng.uniform(0, math.tau)
            rad = rng.uniform(240, 380)
            d = Decoration(dx + math.cos(ang) * rad,
                           dy + math.sin(ang) * rad, kind)
            scene.decorations.append(d)
            sw["flights"].append({"d": d, "sx": d.x, "sy": d.y,
                                  "t0": t, "dur": rng.uniform(0.45, 0.7),
                                  "s0": d.scale})
        done = []
        for f in sw["flights"]:
            p = (t - f["t0"]) / f["dur"]
            if p >= 1.0:
                done.append(f)
                continue
            e = p * p                                 # ease-in: the suck
            f["d"].x = f["sx"] + (dx - f["sx"]) * e
            f["d"].y = f["sy"] + (dy - f["sy"]) * e
            f["d"].scale = f["s0"] * (1.0 - 0.75 * e)
        for f in done:
            sw["flights"].remove(f)
            if f["d"] in scene.decorations:
                scene.decorations.remove(f["d"])
            if rng.random() < 0.35:
                game.audio.play("bump", 0.16)
        if t >= SEAL_WARP_DUR:                        # the room is bare
            game._seal_warp = None
            game.audio.flashback_air(False)
            game._play_ending("seal_threshold")       # force_silence cuts all
            game.audio.play("carcosa_boom", 0.9)      # ...one boom INTO black

    def _threshold_update(game, scene, dt):
        sw = getattr(game, "_seal_warp", None)
        if sw is not None:
            _tick_seal_warp(game, scene, sw, dt)
        else:
            _threshold_seal(game, scene)
    sc.on_update_fn = _threshold_update
    return sc
