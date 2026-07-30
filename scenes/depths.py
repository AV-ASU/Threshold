"""The depths -- everything below the basement level: the OLD WORKINGS,
older than the cult's dig. The blast at the Deepest Face
(works_deepface) drops the player here; from this point the only
direction is down.

Floors, top to bottom:
  depths_antechamber  -- the fall zone
  depths_procession   -- the moving-candle column
  depths_hall         -- the kneeling grid
  depths_threshing    -- the threshing floor
  depths_stair        -- the empty spiral down
  dark                -- the hive: the claimed congregation, past names
                         (Mara kneels at the Sign Chamber now)
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
    spot to break the chase. In SCOUT it PURE-ROAMS (DESIGN.md §4) --
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


# --- Shape toolkit (DESIGN.md §10: vary the underground silhouettes) ---
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


def _flood(floor, objs, tiles):
    """Set the given (tx, ty) FLOOR tiles to `~` deep water and return the
    rebuilt floor rows. Only OPEN interior floor (objs[y][x] == '.') is
    flooded, so a tile that landed on a wall, an exit, or a bevel corner is
    skipped -- callers can pass a whole rectangle and let the walls mask it.
    Water tiles stay walkable; the WADE mechanic (systems/config WADE_*)
    slows the player + throws a splash on them. Call BEFORE the objects
    layer is joined to strings (objs is still a list of char lists)."""
    rows = [list(r) for r in floor]
    h = len(rows); w = len(rows[0]) if rows else 0
    for tx, ty in tiles:
        if 0 <= ty < h and 0 <= tx < w and objs[ty][tx] == ".":
            rows[ty][tx] = "~"
    return ["".join(r) for r in rows]


def _rect_tiles(x0, y0, x1, y1):
    """Every (x, y) in an inclusive tile rectangle -- a convenient region to
    hand to _flood()."""
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


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


def _antechamber_interact(game):
    px, py = game.player.x, game.player.y
    if abs(px - (5 * TILE + 16)) < 36 and abs(py - (5 * TILE + 16)) < 36:
        _evidence(game, "the_fall",
            "There is no way back above you, and you are not hurt. Cut stone, worn smooth by years of feet that came this way before you."
        )


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
    # BROKEN timber sets flank the landing on the diagonal (clear of the
    # mid-row passage to the east exit and the cultist's loop): a lone
    # upright each, beam sheared off short -- the old workings' props
    # gave up what they were holding a cycle ago (2026-07: the stone
    # pillars were swapped out; nobody built columns down here).
    sc.add_furniture("shoring_frame", [(7, 3)], seed=4, ang=0.6, span=0)
    sc.add_furniture("shoring_frame", [(3, 7)], seed=10, ang=2.2, span=0)
    # Rubble from the blown floor above -- the landing text says the fall
    # delivered you unbroken, so the zone wears dust and stone, no blood.
    sc.add_decoration(Decoration(5 * TILE + 16, 5 * TILE + 16, "mud_footprint"))
    # Cobweb grime in the beveled corners of the fall zone.
    sc.add_decoration(Decoration(2 * TILE + 6, 2 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 8 * TILE + 26, "cobweb",
                                 ang=math.pi))
    # A supply crate from the old workings, and the gap beneath it: one
    # enclosed hide near the patrol loop (DESIGN.md §12). Beside it,
    # spoil never hauled and a stub of the old rail heading east -- the
    # fall lands you in a working, not a room (2026-07 art pass).
    sc.add_furniture("crate", [(7, 4)])
    sc.add_furniture("spoil_heap", [(6, 3)], seed=3, see_over=True)
    sc.add_decoration(Decoration(8 * TILE + 24, 5 * TILE + 16,
                                 "mine_rail", ang=0.0, seed=9))
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

    sc.on_interact_fn = _antechamber_interact
    return sc


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
        "[c=dim]They walked this in single file, carrying light. Nobody hurried. The wax says nobody ever hurried.[/c]",
    ], speaker="", voice="blip_soft", portrait="narrator")
    if hasattr(game, "_log_note"):
        game._log_note("the_procession", [
            "A candle line tended half a mile under Brimley, wax on "
            "old wax. They filed to their rite the way other towns "
            "file to Sunday service. Unhurried. Certain.",
        ])


def build_depths_procession():
    # A colonnade comb, LONG -- the old workings' main drift, the game's
    # main hallway segment. A 30-tile E-W processional with alcove bays
    # (teeth) jutting off north and south, staggered so the column never
    # reads as one straight sightline. Lengthened 2026-07 (the stealth
    # pass): the graded suspicion model reads on DISTANCE, so the drift
    # must be long enough to watch a patrol before it can read you, and
    # a mine's main haul run should walk long.
    floor, objs = _box(30, 9)
    _wall(objs, 1, 1, 28, 2)            # seal the top band...
    for cx in (3, 4, 8, 9, 13, 14, 18, 19, 23, 24, 27, 28):
        objs[1][cx] = "."               # ...then open north bays (teeth)
        objs[2][cx] = "."
    _wall(objs, 1, 6, 28, 7)           # seal the bottom band...
    for cx in (2, 3, 6, 7, 11, 12, 16, 17, 21, 22, 25, 26):
        objs[6][cx] = "."              # ...then open south bays
        objs[7][cx] = "."
    objs[4][29] = "E"   # east to hall
    objs[8][6] = "D"    # south (off a bay) -> the Old Stores branch
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_procession", floor, objects, music="basement")
    sc.add_exit("E", "depths_hall", "from_procession")
    sc.add_exit("D", "the_old_stores", "from_procession")
    sc.set_spawn("default",          1, 4)
    sc.set_spawn("from_antechamber", 1, 4)
    sc.set_spawn("from_the_old_stores", 6, 6)   # back up from the stores branch
    # A line of candles down the whole drift, suggesting the procession
    # column. (The [E] read stays at col 8 -- flow-guarded.)
    for cx in range(2, 28, 2):
        sc.add_decoration(Decoration(cx * TILE + 16, 4 * TILE + 16,
                                     "candle"))
    # Timber SETS down the drift (2026-07 art pass): each is one frame --
    # two board uprights flanking the walk and a header beam the player
    # passes UNDER, the same structural grammar as the Threshold frame,
    # drawn from yaw-rotated boxes so it holds at every camera angle.
    # The uprights sit on the same tiles the old posts did (collision
    # unchanged); row 4 walks under the beam. Seeded so no two match.
    for px in (5, 10, 16, 21, 26):
        sc.add_furniture("shoring_frame", [(px, 3), (px, 5)],
                         seed=px * 3 + 1, ang=math.pi / 2, span=64)
    # Two more sets stand over south bay MOUTHS, facing the camera --
    # the full frame read (uprights + header beam over the opening, the
    # Threshold's grammar). Pure decoration: their uprights hug the bay
    # cut's wall edges, which are already solid, so collision and the
    # bays' cover value are untouched.
    for bx0 in (6, 21):
        sc.add_decoration(Decoration((bx0 + 0.5) * TILE + 16, 6 * TILE + 2,
                                     "shoring_frame", seed=bx0,
                                     ang=0.0, span=78))
    # The old workings' haul road: stubs of rusted rail down the drift's
    # walking line (the candle line follows a dead mine's road), and the
    # seized ore cart shoved aside into a south bay a cycle ago -- solid,
    # so it doubles as bay cover.
    for rx_ in (7, 13, 19, 25):
        sc.add_decoration(Decoration(rx_ * TILE + 16, 4 * TILE + 16,
                                     "mine_rail", ang=0.0, seed=rx_))
    sc.add_furniture("ore_cart", [(17, 7)], seed=4)
    # Cobweb grime in the high corners of the procession column.
    sc.add_decoration(Decoration(1 * TILE + 6, 3 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(28 * TILE + 26, 3 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # Crates tucked into bays along the run + the gaps under them: three
    # enclosed hides spaced down the drift (DESIGN.md §12) -- the
    # bays themselves are the concealment; these are the rooted options
    # a searcher can sweep and check. A long room needs hides the whole
    # way, or its far half is a dead sprint.
    sc.add_furniture("crate", [(12, 7)])
    sc.add_furniture("crate", [(19, 1)])
    sc.add_furniture("crate", [(26, 7)])
    sc.hide_spots = [
        (11 * TILE + 24, 7 * TILE + 16, "under"),  # beside the mid bay crate
        (19 * TILE + 16, 2 * TILE + 8,  "under"),  # under the north bay crate
        (25 * TILE + 24, 7 * TILE + 16, "under"),  # beside the far bay crate
    ]
    # Three cultists walking the column, single file, spread phases so
    # the drift always has one in view somewhere and passing windows
    # open between them. Endpoints held away from the west-edge spawn
    # (col 1) so the player arrives with breathing room.
    sc.add_enemy(_cultist(5 * TILE + 16, 4 * TILE + 16, speed=0.9))
    sc.add_enemy(_cultist(14 * TILE + 16, 4 * TILE + 16, speed=0.9))
    sc.add_enemy(_cultist(23 * TILE + 16, 4 * TILE + 16, speed=0.9))
    # Candle-tending dwells down the drift (the JOBS layer, 2026-07
    # stealth pass): the walkers pause over the flames in a rhythm the
    # player can read from a bay -- the long room's patrols get a
    # learnable beat instead of pure drift. Sightings still outrank it.
    sc.add_cult_station(6 * TILE + 16, 4 * TILE + 16, pose="chant",
                        face=(0, 1), dwell=(2.5, 4.5))
    sc.add_cult_station(16 * TILE + 16, 4 * TILE + 16, pose="chant",
                        face=(0, 1), dwell=(2.5, 4.5))
    sc.add_cult_station(26 * TILE + 16, 4 * TILE + 16, pose="chant",
                        face=(0, 1), dwell=(2.5, 4.5))
    _ambient(sc, "blip_soft", 0.12, 2.5, 4.5)

    # The procession's one diegetic beat (NARRATIVE §7): the candle line read
    # up close. Wax on old wax -- they filed to the rite many more times
    # than once, and never hurried. Narration + a case NOTE (never
    # evidence; the five canonical beats are locked).
    sc.add_interactable(8 * TILE + 16, 4 * TILE + 16, 36)

    sc.on_interact_fn = _candles_interact
    return sc


def build_depths_hall():
    # A cruciform basilica: a LONG E-W nave to the iron door, crossed by a
    # N-S transept. The corners are solid stone, so the kneeling grid is
    # reached only down the nave and across the crossing. Lengthened
    # 2026-07 (the stealth pass): the nave east of the crossing gives the
    # kneelers a real approach to read, and the pew rows run the length.
    floor, objs = _box(20, 11)
    _wall(objs, 1, 1, 7, 3)        # NW
    _wall(objs, 11, 1, 18, 3)      # NE
    _wall(objs, 1, 7, 7, 9)        # SW
    _wall(objs, 11, 7, 18, 9)      # SE
    objs[5][19] = "E"   # east to threshing floor (the iron door)
    # #14 -- a FINISHED store cut into the big NW corner stone off the nave:
    # the old workings kept gear by the basilica. Cols 4-6, 2 deep, one ADIT
    # down at col 5 (a bench-free column). West of the crossing-trigger rect
    # (cols 8-10) and clear of the bench rows, so the kneel set-piece, the
    # nave run, and the hides are untouched.
    for cx in (4, 5, 6):
        objs[1][cx] = "."
        objs[2][cx] = "."
    objs[3][5] = "."               # the adit down to the nave
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_hall", floor, objects, music="basement")
    sc.add_exit("E", "depths_threshing", "from_hall")
    sc.set_spawn("default",        1, 5)
    sc.set_spawn("from_procession", 1, 5)
    # The east wall holds the iron door the kneeling grid faces.
    # Four cultists in the room: two flanking the door, one on
    # patrol. Hide spots scatter so the player can pick a route.
    sc.add_decoration(Decoration(18 * TILE + 16, 5 * TILE + 16,
                                 "phantom_mark"))
    # (The "wrong" taxidermy mount was cut, 2026-07 process audit: a
    # hunting trophy fails provenance in the old workings -- nobody hung
    # a mount in a mine. The one in the Sorting Hall stays: it sits
    # among the catalogued possessions the congregation shed.)
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(5 * TILE + 16, 6 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(14 * TILE + 16, 4 * TILE + 16, "candle"))
    # Rough plank benches in two rows down BOTH halves of the nave, a
    # clear central aisle (row 5) between them up to the iron door.
    # (2026-07 process audit: PEWS are church joinery nobody hauled down
    # a mine; the kneeling rows sit on backless planks the congregation
    # knocked together from the dig's own lumber.)
    for px in (2, 4, 6):
        sc.add_furniture("plank_bench", [(px, 4)])
        sc.add_furniture("plank_bench", [(px, 6)])
    for px in (12, 15):
        sc.add_furniture("plank_bench", [(px, 4)])
        sc.add_furniture("plank_bench", [(px, 6)])
    # Cobweb grime in the transept ends.
    sc.add_decoration(Decoration(8 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 8 * TILE + 26, "cobweb",
                                 ang=math.pi))
    # The NW store, dressed (#14): crates of the old workings' gear squared
    # into the corner, a kept candle, the count on the back wall, timber over
    # the adit mouth.
    sc.add_decoration(Decoration(5 * TILE + 16, 3 * TILE + 30, "shoring_frame",
                                 seed=21, ang=0.0, span=70))
    sc.add_furniture("crate", [(4, 1)])
    sc.add_furniture("crate", [(6, 1)])
    sc.add_decoration(Decoration(5 * TILE + 16, 1 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(5 * TILE + 16, 1 * TILE + 18, "tally_marks",
                                 wall="N", seed=27))
    # Cover down the nave (2026-07 stealth pass): the benches are
    # see-over (knee-high planks hide nobody standing), which left the
    # aisle a 16-tile naked run once the room was lengthened. Three
    # BROKEN shoring sets stagger along it -- solid, sight-blocking,
    # the old workings' own vocabulary -- so the dash to the door
    # breaks into readable legs (longest exposed run ~5 tiles).
    sc.add_furniture("shoring_frame", [(3, 6)], seed=7, ang=0.5, span=0)
    sc.add_furniture("shoring_frame", [(9, 4)], seed=12, ang=2.4, span=0)
    sc.add_furniture("shoring_frame", [(13, 6)], seed=3, ang=1.1, span=0)
    # Enclosed hides on the nave route (DESIGN.md §12): under a
    # bench in each half, both in the roamer's sweep range -- the east half
    # past the crossing needs its own rooted option once the kneelers
    # wake, or the run to the door is a coin flip.
    sc.hide_spots = [
        (4 * TILE + 16, 5 * TILE + 24, "under"),    # under a west nave bench
        (15 * TILE + 16, 5 * TILE + 24, "under"),   # under an east nave bench
    ]
    # Two stationary cultists kneel at the iron door, facing east.
    # Aggro starts at 0 (oblivious) so they don't react until the
    # crossing trigger flips them. aggro=0 + lock_facing pins them in
    # place (a stationary set-piece, exempt from the SCOUT roam) and keeps
    # them turned toward the door. The third cultist roams, regardless.
    kneel_a = _cultist(17 * TILE + 16, 4 * TILE + 16, speed=0.8)
    kneel_b = _cultist(17 * TILE + 16, 6 * TILE + 16, speed=0.8)
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
        # The narrative half of the trigger (NARRATIVE §4): the grid was
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


def _threshing_interact(game):
    px, py = game.player.x, game.player.y
    if abs(px - (6 * TILE + 16)) < 36 and abs(py - (5 * TILE + 16)) < 36:
        _evidence(game, "threshing_floor",
            "The yield, raked into low heaps: grain, all of it, tithed "
            "down from the fields above."
        )


def build_depths_threshing():
    # A raw cavern -- ragged, bitten-out walls (the room the dig opened into,
    # never squared off), the threshing heaps raked across its floor.
    floor, objs = _box(13, 11)
    _cavern(objs, seed=7, keep_rows=(5,), bite=0.4)
    objs[5][12] = "E"   # east to stair
    # Seep from the broken river pools in the cavern's north and south
    # pockets -- the grain heaps at (4,4)/(4,7) stand in it, so raking over
    # to read them is a slow, loud wade (WADE_*). The central aisle (row 5,
    # kept clear by _cavern) and the east exit stay dry: the through route
    # never forces the water. _flood skips the bitten cavern walls.
    floor = _flood(floor, objs, _rect_tiles(3, 3, 5, 4) + _rect_tiles(3, 7, 5, 8))
    objects = ["".join(r) for r in objs]
    sc = Scene("depths_threshing", floor, objects, music="basement")
    sc.add_exit("E", "depths_stair", "from_threshing")
    sc.set_spawn("default",   1, 5)
    sc.set_spawn("from_hall", 1, 5)
    # Ambient dig labour: miners working the side faces (pickaxe in profile,
    # facing the wall) while chanters sway at the dig's mouth. All idle NPCs
    # with NO tag -> excluded from the cultist-gaze tick (no visibility, no
    # chase, no grab); non-solid. The dig toward the door made present, and
    # the rite chanted over it (NARRATIVE §2 / The Digging note).
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
    # (The old blood-in-the-grain stains were cut, 2026-07: the tithe is
    # an offering carried down by the willing -- nobody bled into it.
    # The heaps and the wading water carry the room.)
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

    sc.on_interact_fn = _threshing_interact
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


def _old_stores_interact(game):
    px, py = game.player.x, game.player.y
    if abs(px - (4 * TILE + 16)) < 36 and abs(py - (9 * TILE + 16)) < 36:
        _evidence(game, "the_old_stores_shelves",
            "Shelves of the dig's gear: lamps burned black, pick hafts "
            "worn down to the grain, every one tagged in the same steady brown hand.")
        return
    nx, ny = game.scene._dig_note_pos
    if abs(px - nx) < 36 and abs(py - ny) < 36:
        if not game.save.flag("old_stores_digging_taken"):
            game.save.set_flag("old_stores_digging_taken", True)
            game.player.inventory.add("cult_digging", 1)
            game.audio.play("pickup_rare", 0.6)
            game._log_note("cult_digging", [
                "The last pages stop being sentences. Just the word door, over and over, pressed hard enough to tear the paper.",
            ])
            game.show_notice("The Digging. Their last pages.")
            return


def build_the_old_stores():
    """The Old Stores off the procession -- a tall hexagonal cell where
    the old workings kept their gear: racked shelves of dead lamps and
    worn tools, every haft tagged in the same steady brown hand. A mine's
    storeroom, nothing more, and the labor it inventories outlived the
    hands that did it. A dead-end pocket of dread and cover. (2026-07
    mine retrofit: the old charnel-vault fiction was a killer-cult relic --
    the claiming cult spills no one, NARRATIVE §2.)"""
    floor, objs = _box(9, 12)
    _bevel(objs, 2)
    objs[0][4] = "F"          # north -> back to the procession
    objects = ["".join(r) for r in objs]
    sc = Scene("the_old_stores", floor, objects, music="basement")
    sc.add_exit("F", "depths_procession", "from_the_old_stores")
    sc.set_spawn("default",         4, 6)
    sc.set_spawn("from_procession", 4, 2)
    # Racked gear shelves (3D) line the niches -- dark tools, gaps where
    # gear went out, one dead lamp; candles gutter between. (2026-07:
    # "shelf" drew book spines; a mine store shelves no library.)
    for sx, sy in [(2, 4), (6, 4), (2, 8), (6, 8)]:
        sc.add_furniture("gear_shelf", [(sx, sy)])
    # A dead lamp left on a shelf -- the old workings' light, burned out a
    # cycle ago (seated onto the shelf top by seat_tabletop_props).
    sc.add_decoration(Decoration(6 * TILE + 16, 4 * TILE + 16,
                                 "kerosene_lamp"))
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
    # Optional lore: The Digging (third, deepest testimony fragment), left
    # on a shelf among the old gear -- the cult's one addition to the
    # stores. Pure lore, gates nothing.
    sc._dig_note_pos = (6 * TILE + 16, 9 * TILE + 16)
    sc.add_interactable(sc._dig_note_pos[0], sc._dig_note_pos[1], 36)

    sc.on_interact_fn = _old_stores_interact
    return sc


def _hive_murmur(game, npc):
    game.dialog.show(
        ["[c=dim]The kneeler doesn't stir. Its lips move, no sound.[/c]"],
        speaker="", voice="blip_soft", portrait="narrator")
# The congregation: hooded, idle, facing the south doorframe they
# worship. Solid, so the player threads between them in the dark.
# (2026-07: Mara is no longer here -- she kneels at the Sign
# Chamber's altar now, where the calling-out stages her rising.
# Down here nothing has a name left; the hive is the ones who went
# first, past answering.)


def build_dark():
    floor, objs = _box(12, 10)
    objs[8][3] = "D"   # south-west to threshold -- off the centre aisle,
                       # so the player never has to push through the rank
    objects = ["".join(r) for r in objs]
    sc = Scene("dark", floor, objects, music="basement")
    sc.add_exit("D", "threshold", "from_dark")
    sc.set_spawn("default",    6, 1)
    sc.set_spawn("from_stair", 6, 1)
    # The hive (CULT_DARK_SCENES: the deepest gloom tier). The beam works
    # here since the 2026-07 light pass, at the usual price; unlit, the
    # dread aperture's clear circle finds the congregation a face at a
    # time. They're NPCs, not enemies: no chase, no contact penalty. The
    # room's whole work is the recognition.
    for kx, ky in [(3, 4), (8, 4), (4, 6), (9, 6), (8, 7), (6, 5)]:
        n = NPC(kx * TILE + 16, ky * TILE + 16, "A kneeler", "cultist",
                dialogue_fn=_hive_murmur, movement="idle")
        n.facing = (0, 1)
        sc.add_npc(n)
    sc.hide_spots = []
    _ambient(sc, "heartbeat", 0.18, 3.5, 5.0)
    return sc


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


def _threshold_seal(game, scene):
    lintel_x, lintel_y = scene._lintel_pos
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
    # DELIBERATE lone-trigger (NOT the blast/grove two-press commit).
    # Unlike the blast (well.py) and the grove rite (hidden_folds.py),
    # there is no *_laid re-arm and no second press here -- ON PURPOSE
    # (C15). The point-of-no-return fork is spent UPSTREAM: the blast at
    # the Deepest Face is the two-press choice (climb out to SPREAD vs
    # light it and FALL, "no way back up"). A player standing at the
    # frame has already chosen the descent AND carried the Mask down;
    # walking it through IS the commit (NARRATIVE §7, Mask-only). A
    # redundant warning here would only blunt that upstream fork, so the
    # crossing stays silent.
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


def _begin_seal_warp(game, scene):
    lintel_x, lintel_y = scene._lintel_pos
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


# What the SEAL's warp drags through the room, and when: the surface world
# arriving where it does not belong, one thing at a time.
_WARP_FOREIGN = [
    (1.60, "bush"), (1.75, "tall_grass"), (1.90, "firewood"),
    (2.05, "grass_tuft"), (2.20, "crate"), (2.35, "barrel"),
    (2.50, "chair"), (2.65, "kerosene_lamp"), (2.80, "corn_doll"),
    (2.95, "wheelbarrow"), (3.10, "calendar"), (3.25, "photo"),
    (3.40, "radio"), (3.55, "doll"), (3.70, "stalk_marker"),
    (3.85, "pew"), (4.05, "town_sign"),
]

# How long the seal's warp takes to strip the room bare.
SEAL_WARP_DUR = 4.8


def build_threshold():
    # An underground RIVER CAVE -- not a box, and LONG: the player comes up from
    # the dark at the far SOUTH and walks a long way north, through a choked
    # stalagmite field, before reaching the frame. Ragged organic rock walls; the
    # artery-river (NARRATIVE §2) is the whole WEST boundary, fed by a wide
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
    # door with no wall, nothing in the opening (NARRATIVE §2). You SEAL by
    # walking THROUGH it carrying the keystone (the Pallid Mask), spent there
    # (§7, Mask-only); the walk-through is handled in on_update below. No [E]
    # prompt, no glow, no smoke. The keystone was carried down (the blast opened the way down
    # WITHOUT spending it), so a player who descended always holds it.
    lintel_x, lintel_y = 7 * TILE + 16, DR * TILE + 16
    sc._lintel_pos = (lintel_x, lintel_y)
    sc.add_decoration(Decoration(lintel_x, lintel_y, "doorframe"))

    # The waterfall: ONE wide spring (~3 tiles) gushing from a hole in the
    # south-west cliff, covering the whole river mouth (NARRATIVE §2 -- the
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

    # The river THREAD (NARRATIVE §2): ONE continuous, organic side-channel that
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

    sc.on_enter_fn = _threshold_on_enter

    # The SEAL: walking THROUGH the empty frame carrying the keystone (the
    # Pallid Mask). The crossing plays as LIVE ACTION first: you go through,
    # and the world FOLLOWS you -- the cave's own dressing tears loose and
    # pours through the frame, then foreign things stream in from beyond
    # the dark (brush, the houses' insides, a pew, the town's NAME, last
    # through before the door slams) -- every acre the cult bent, funneling
    # through the one door. Then the approved black-screen lines + the
    # wordless tableau take over (_play_ending("seal_threshold")). Without
    # the Mask the frame is only a frame; it never opens (NARRATIVE §2).





    sc.on_update_fn = _threshold_update
    return sc
