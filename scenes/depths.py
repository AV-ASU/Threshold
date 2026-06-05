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
    """Wire a periodic ambient sfx to scene.on_update_fn. Each room
    gets its own cue + period so the depths read as different
    spaces, not one repeated basement."""
    scene._amb_t = random.uniform(lo, hi)
    def _tick(game, sc, dt):
        sc._amb_t -= dt
        if sc._amb_t <= 0:
            sc._amb_t = random.uniform(lo, hi)
            game.audio.play(sfx, vol)
    scene.on_update_fn = _tick


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
    # Two pillar-style hide spots flanking the diamond.
    sc.hide_spots = [
        (4 * TILE + 16, 8 * TILE + 16, "behind"),
        (6 * TILE + 16, 2 * TILE + 16, "behind"),
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
                "The rope is gone above you and you are not hurt. The way "
                "down didn't want you broken, only delivered. Cut stone, "
                "worn smooth by years of feet that came this way before you."
            )
    sc.on_interact_fn = _interact

    def _on_enter(game, scene):
        if game.save.flag("first_antechamber"):
            return
        game.save.set_flag("first_antechamber", True)
        game.show_notice("This is what the well was a throat for. The work "
                         "of the town goes on down here, in the dark.",
                         duration=4.0)
    sc.on_enter_fn = _on_enter
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
    sc.hide_spots = [
        (3 * TILE + 16, 1 * TILE + 24, "behind"),    # up in a north bay
        (11 * TILE + 16, 7 * TILE + 16, "behind"),   # down in a south bay
        (6 * TILE + 16, 7 * TILE + 16, "behind"),
    ]
    # Two cultists walking the column, single file, opposite phases
    # so they meet between (5..12) and pass each other. Endpoints
    # held away from the west-edge spawn (col 1) so the player
    # arrives with breathing room.
    sc.add_enemy(_cultist(5 * TILE + 16, 4 * TILE + 16, speed=0.9))
    sc.add_enemy(_cultist(11 * TILE + 16, 4 * TILE + 16, speed=0.9))
    _ambient(sc, "blip_soft", 0.12, 2.5, 4.5)

    def _on_enter(game, scene):
        if game.save.flag("first_procession"):
            return
        game.save.set_flag("first_procession", True)
        game.show_notice("A column of candles, walked single file. They came "
                         "down here singing, once. Now they only walk.",
                         duration=4.0)
    sc.on_enter_fn = _on_enter
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
    sc.hide_spots = [
        (9 * TILE + 16, 1 * TILE + 24, "behind"),    # north transept arm
        (9 * TILE + 16, 8 * TILE + 16, "behind"),    # south transept arm
        (2 * TILE + 16, 5 * TILE + 16, "behind"),    # west nave aisle
        (8 * TILE + 16, 6 * TILE + 16, "behind"),    # at the crossing
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
    sc.triggers.append({
        "rect": (8 * TILE, 1 * TILE, 11 * TILE, 10 * TILE),
        "fn": _alert_kneelers,
        "once": True,
        "fired": False,
    })
    _ambient(sc, "whisper", 0.14, 7.0, 12.0)

    def _on_enter(game, scene):
        if game.save.flag("first_hall"):
            return
        game.save.set_flag("first_hall", True)
        game.show_notice("Rows worn into the floor where knees have pressed, "
                         "all of them turned to the iron door. They are "
                         "waiting for it to open.", duration=4.0)
    sc.on_enter_fn = _on_enter
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
    for mx, my, mf, mp in [(5, 8, (-1, 0), "mine"), (7, 8, (1, 0), "mine"),
                           (4, 9, (-1, 0), "mine"),
                           (6, 9, (0, 1), "chant"), (8, 9, (0, 1), "chant")]:
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
    sc.hide_spots = [
        (3 * TILE + 16, 3 * TILE + 16, "behind"),
        (9 * TILE + 16, 7 * TILE + 16, "behind"),
    ]
    _ambient(sc, "step_grass", 0.22, 3.5, 6.0)
    sc.add_interactable(6 * TILE + 16, 5 * TILE + 16, 36)   # [E] cue: the threshing heaps

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - (6 * TILE + 16)) < 36 and abs(py - (5 * TILE + 16)) < 36:
            _evidence(game, "threshing_floor",
                "The yield, raked into low heaps: grain, all of it, tithed "
                "down from the fields above. The town's whole harvest, given "
                "over to the dark below, season on season, carried down and "
                "never carried back up. An offering. Not a stockpile."
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
    sc.hide_spots = [
        (4 * TILE + 16, 2 * TILE + 16, "behind"),
        (5 * TILE + 16, 8 * TILE + 16, "behind"),
    ]
    _ambient(sc, "low_pulse", 0.10, 11.0, 16.0)

    def _on_enter(game, scene):
        if game.save.flag("first_depthstair"):
            return
        game.save.set_flag("first_depthstair", True)
        game.show_notice("The stair spirals down past the last of the "
                         "candlelight. No guards. Nothing down here needs "
                         "guarding. No one who reaches it ever turns back.",
                         duration=4.0)
    sc.on_enter_fn = _on_enter
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
    sc.hide_spots = [
        (2 * TILE + 16, 6 * TILE + 16, "behind"),
        (6 * TILE + 16, 6 * TILE + 16, "behind"),
    ]
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
                game.dialog.show([
                    "[c=dim]Racked with one digger's leavings, their last "
                    "pages. The hand starts steady and comes apart. You take "
                    "it.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
                return
            game.show_notice("A digger's leavings, racked and labelled.",
                             duration=3.0)
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
    game.dialog.show([
        "[c=dim](You say her name. The hooded head lifts. It is Mara.)[/c]",
        "\"My father sent you. Of course he did. He never could let a thing "
        "stay lost.\"",
        "[s=slow]\"Tell him what I told him at the start. I'm not lost. I have "
        "never been this close.\"[/s]",
        "[c=dim]\"There was no one down here to bring back. I was not taken. I "
        "was answered, and I went to it gladly. Go home, while the town still "
        "lets you think you can.\"[/c]",
    ], speaker="", voice="blip_soft", portrait="narrator")
    _evidence(game, "the_congregation", [
        "Mara, kneeling with the congregation. Turned. There was never "
        "anyone to bring back. Only this, and now you're in it with her.",
    ])


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
    sc.hide_spots = [
        (1 * TILE + 24, 8 * TILE + 16, "behind"),
        (10 * TILE + 16, 1 * TILE + 24, "behind"),
    ]
    _ambient(sc, "heartbeat", 0.18, 3.5, 5.0)
    return sc


def build_threshold():
    # An underground RIVER CAVE -- not a box. Ragged rock walls, a stalagmite
    # floor, and the artery-river (NARRATIVE 1b) forming the whole WEST boundary.
    # The one place the cave goes WRONG is the doorframe: there the floor lies
    # impossibly level and swept clear, geometry serving the door (1b -- the seed
    # of the spatial fold). The player comes up from the dark to the SOUTH and
    # walks the cave north to the frame -- the dream-walk made real.
    W, H = 14, 13
    floor, objs = _box(W, H)
    floor = [list(r) for r in floor]          # mutable rows for the edits below
    # Gnaw an organic cave edge, but keep the central approach (entry S -> door
    # N) and the door's row open so the apron stays clean and reachable.
    _cavern(objs, seed=771, keep_cols=(6, 7, 8), keep_rows=(4,))
    # Rough packed-stone cave floor throughout (the apron is reset smoother below).
    for _y in range(H):
        for _x in range(W):
            floor[_y][_x] = "x"
    # The artery: a river channel hard against the west rock, IMPASSABLE
    # (invisible-solid over the water) so it reads as one boundary WALL of the
    # cave -- the source the thread of water crept from to the frame.
    for _y in range(2, H - 2):
        for _x in (1, 2):
            objs[_y][_x] = "X"
            floor[_y][_x] = "~"
    objs[4][3] = "."          # a lick of water onto the bank, where the thread
    floor[4][3] = "~"         # leaves the river toward the frame
    # The threshold APRON: a clean, level clearing around the frame (rows 2-6,
    # cols 5-9) -- smoother dark stone, and (below) no stalagmite intrudes on it.
    # The cave's true wrongness is that this order exists down here at all.
    for _y in range(2, 7):
        for _x in range(5, 10):
            if objs[_y][_x] == ".":          # don't punch through carved rock
                floor[_y][_x] = "."
    objects = ["".join(r) for r in objs]
    sc = Scene("threshold", floor, objects, music="void")
    sc.skybox_kind = "void"
    sc.set_spawn("default",   7, 11)
    sc.set_spawn("from_dark", 7, 11)
    # Doorframe on the apron (the cave's north-centre). Pressing E presses the
    # KEYSTONE -- the Pallid Mask -- into the door and seals it (the
    # seal_threshold ending), CONSUMING it (§7 rework, Mask-only: the cult's
    # notes are pure lore now and gate nothing). The keystone was carried down
    # (the Deep Stair opened WITHOUT spending it), so a player who descended
    # always holds it here.
    lintel_x, lintel_y = 7 * TILE + 16, 4 * TILE + 16
    sc._lintel_pos = (lintel_x, lintel_y)
    sc.add_interactable(lintel_x, lintel_y, 40)   # [E] cue: seal the Threshold (END IT)
    # The frame itself: a real standing doorframe (NARRATIVE 1b), NOT solid --
    # you can walk through it and stand in the same room on the far side. The
    # smoke rises from its opening.
    sc.add_decoration(Decoration(lintel_x, lintel_y, "doorframe"))
    sc.add_decoration(Decoration(lintel_x, lintel_y - TILE, "smoke"))

    # Stalagmites choking the organic cave floor -- everywhere BUT the swept
    # apron, the river, and the central walking lane. Solid (invisible-solid
    # under each), so they shape the space like real rock; hand-placed clear of
    # the col-7 approach so the walk to the frame is never blocked.
    _stals = [(4, 8), (3, 6), (5, 10), (4, 11), (3, 9), (5, 7),
              (10, 5), (11, 7), (12, 9), (10, 8), (11, 11), (9, 10),
              (12, 4), (11, 3), (12, 6)]
    for (sx, sy) in _stals:
        if not (0 <= sy < H and 0 <= sx < W) or sc.objects[sy][sx] != ".":
            continue
        sc.objects[sy][sx] = "X"             # collision; the prop draws over it
        sc.add_decoration(Decoration(sx * TILE + 16, sy * TILE + 16,
                                     "stalagmite", seed=sx * 31 + sy * 17))

    # The river THREAD (NARRATIVE 1b). The river found the lowest, flattest floor
    # in the earth; a single thread crept off it, crossed the cave, reached the
    # frame, and CROSSED ITS PLANE. It leaves the west channel, meanders the floor
    # to the door's foot, pools there, and a thread carries on THROUGH the empty
    # frame to the far stone -- water passing where a body cannot. Floor decals,
    # so they lie in the level floor and warp with it under the tilt.
    _thread = [(2, 4, 0.0), (3, 4, 0.2), (4, 5, 0.5), (5, 5, 0.4), (6, 4, 0.7)]
    for (tx, ty, ang) in _thread:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "water_trail", ang=ang, seed=tx * 13 + ty))
    sc.add_decoration(Decoration(lintel_x, lintel_y + 6, "water_trail",
                                 pool=True, seed=99))
    for ty in (3, 2):                        # the thread crossing the plane
        sc.add_decoration(Decoration(lintel_x, ty * TILE + 16, "water_trail",
                                     ang=math.pi / 2, seed=ty * 7))

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

    def _threshold_interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - lintel_x) > 40 or abs(py - lintel_y) > 40:
            return
        inv = game.player.inventory
        # The door seals only to the keystone -- the Pallid Mask -- carried
        # down from the Deep Stair (§6/§7, Mask-only). Spend it at the frame.
        # (The descent guarantees you hold it; the guard is belt-and-
        # suspenders against a soft-lock.)
        if not inv.has("sigil_rubbing"):
            game.show_notice("The frame is cold and blank. You have nothing "
                             "to give it.")
            return
        game.audio.force_silence()
        game.audio.play("arg_chime", 0.7)
        inv.remove("sigil_rubbing", 1)
        game.dialog.show([
            "[c=dim](You set both hands to the cold frame. His face, the "
            "keystone you carried all this way. You press it into the "
            "door.)[/c]",
            "[c=dim](The frame takes it. Nothing of His is left in your hands "
            "now. Nothing to give it but the rest of you.)[/c]",
            "[s=slow][c=dim]...the smoke stops.[/c][/s]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        _evidence(game, "the_seal", "It is done.")
        game._play_ending("seal_threshold")
    sc.on_interact_fn = _threshold_interact
    return sc
