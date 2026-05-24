"""THE WORKS -- the Basement Level. The cult's underground labour,
reached ONLY by the rope down the village well. Seven rooms descend
from the shaft floor to the orb-gate that opens onto the Depths:

  well_bottom        -- the Shaft Floor (rope landing; the way back up)
  well_passage       -- the Drying Racks (first gauntlet)
  works_vats         -- the Tallow Vats
  works_sorting      -- the Sorting Hall (belongings of the vanished)
  works_scriptorium  -- the Scriptorium (the Sign, copied endlessly)
  works_sign         -- the Sign Chamber (take the rubbing; evidence #5)
  works_deepstair    -- the Deep Stair (orb-gate down to the Depths)

The rope breaks the instant you descend carrying the orb -- from then
there is no climbing back, only deeper. Cultists labour here; the
flashlight works (these are DARK_SCENES, not cult-dark) but their gaze
still finds you, so the gauntlet is run on cover, timing, and the hide
spots. Combat is gone -- contact slams the dread aperture; the danger
is being seen. Cultists respect hiding (player.hidden), so a hide spot
breaks the chase.

Reworks vs. the old build: the well is now the ONLY mouth down (the
barn cellar hatch is sealed), and the orb opens the way deeper, from
the Sign Chamber's far side down into the Depths.
"""
import math
from constants import TILE
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence
from .depths import _box, _cultist, _ambient


# ---- Room 1: the Shaft Floor (key: well_bottom) ----

def build_well_bottom():
    floor, objs = _box(10, 8)
    objs[4][9] = "E"          # east -> the drying racks (deeper)
    objs[1][1] = "U"          # ladder up -- climb is interact-gated below
    objects = ["".join(r) for r in objs]
    sc = Scene("well_bottom", floor, objects, music="basement")
    sc.add_exit("E", "well_passage", "from_above")
    sc.set_spawn("default",   4, 4)
    sc.set_spawn("from_well", 2, 2)       # land here on the descent
    sc.set_spawn("from_below", 8, 4)      # back up from the racks

    ladder_x = 1 * TILE + 16
    ladder_y = 1 * TILE + 16
    sc._ladder_pos = (ladder_x, ladder_y)
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(8 * TILE + 16, 6 * TILE + 16, "bloodstain"))
    # A "wrong" mount in the well dark -- too many eyes.
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 18,
                                 "wrong_taxidermy", wall="N", seed=31))
    # Cobweb grime in the corners away from the ladder.
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_decoration(Decoration(1 * TILE + 6, 6 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.hide_spots = [
        (8 * TILE + 16, 1 * TILE + 24, "behind"),   # collapsed-timber nook
    ]
    _ambient(sc, "low_pulse", 0.12, 9.0, 14.0)

    def _on_enter(game, scene):
        # The rope breaks the instant you come down carrying the orb.
        # From here on there is nowhere left but deeper. One-shot,
        # persisted via the well_rope_broken flag.
        if (game.player.inventory.has("orb")
                and not game.save.flag("well_rope_broken")):
            game.save.set_flag("well_rope_broken", True)
            game.audio.play("low_pulse", 0.7)
            game.show_notice(
                "The rope snaps somewhere above you. No climbing back now.",
                duration=4.0)
    sc.on_enter_fn = _on_enter

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - ladder_x) < 40 and abs(py - ladder_y) < 40:
            if game.save.flag("well_rope_broken"):
                game.audio.play("door_locked", 0.5)
                game.show_notice("The rope is gone. Only the dark below.")
                return
            game.audio.play("door_open", 0.6)
            game.begin_transition("village", "from_well")
    sc.on_interact_fn = _interact
    return sc


# ---- Room 2: the Drying Racks (key: well_passage) ----

def build_well_passage():
    floor, objs = _box(14, 8)
    objs[4][0] = "F"          # west -> back to the shaft
    objs[4][13] = "E"         # east -> the tallow vats (deeper)
    # Drying racks (solid shelves) in two rows, gaps to weave through.
    for cx in (3, 5, 8, 10):
        objs[2][cx] = "s"
    for cx in (4, 6, 9, 11):
        objs[5][cx] = "s"
    objects = ["".join(r) for r in objs]
    sc = Scene("well_passage", floor, objects, music="basement")
    sc.add_exit("F", "well_bottom", "from_below")
    sc.add_exit("E", "works_vats",  "from_above")
    sc.set_spawn("default",    6, 4)
    sc.set_spawn("from_above", 1, 4)      # arriving from the shaft
    sc.set_spawn("from_below", 12, 4)     # back from the vats
    # Legacy spawns kept so old saves + the (now unreachable) cult
    # chamber's exit still resolve.
    sc.set_spawn("from_well",    1, 4)
    sc.set_spawn("from_chamber", 12, 4)
    sc.set_spawn("from_barn",    6, 3)

    sc.add_decoration(Decoration(7 * TILE + 16, 3 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 22, "claw_marks"))
    # Cobweb grime in the high corners of the drying racks.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(12 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (4 * TILE + 16, 2 * TILE + 16, "behind"),    # between racks
        (10 * TILE + 16, 5 * TILE + 16, "behind"),
    ]
    # One cultist working the corridor, end to end.
    sc.add_enemy(_cultist(3 * TILE + 16, 4 * TILE + 16, speed=0.85,
                          waypoints=[(11 * TILE + 16, 4 * TILE + 16),
                                     (3 * TILE + 16, 4 * TILE + 16)]))
    _ambient(sc, "cult_breath", 0.16, 5.0, 9.0)
    return sc


# ---- Room 3: the Tallow Vats (key: works_vats) ----

def build_works_vats():
    floor, objs = _box(12, 9)
    objs[4][0] = "F"          # west -> back to the racks
    objs[4][11] = "E"         # east -> the sorting hall
    for tx, ty in [(3, 2), (7, 2), (3, 6), (7, 6)]:   # rendering vats
        objs[ty][tx] = "t"
    objects = ["".join(r) for r in objs]
    sc = Scene("works_vats", floor, objects, music="basement")
    sc.add_exit("F", "well_passage", "from_below")
    sc.add_exit("E", "works_sorting", "from_above")
    sc.set_spawn("default",    5, 4)
    sc.set_spawn("from_above", 1, 4)
    sc.set_spawn("from_below", 10, 4)

    # Steam off the vats, tallow-light, and the residue of the work.
    for tx, ty in [(3, 2), (7, 2), (3, 6), (7, 6)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 6, "smoke"))
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(8 * TILE + 16, 7 * TILE + 16, "gore"))
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 16, "bloodstain"))
    # Cobweb grime in the high corners above the vats.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (5 * TILE + 16, 2 * TILE + 16, "behind"),
        (8 * TILE + 16, 6 * TILE + 16, "behind"),
    ]
    # Two cultists tending the vats on small loops.
    sc.add_enemy(_cultist(2 * TILE + 16, 4 * TILE + 16, speed=0.8,
                          waypoints=[(2 * TILE + 16, 2 * TILE + 16),
                                     (2 * TILE + 16, 6 * TILE + 16)]))
    sc.add_enemy(_cultist(9 * TILE + 16, 5 * TILE + 16, speed=0.8,
                          waypoints=[(9 * TILE + 16, 6 * TILE + 16),
                                     (9 * TILE + 16, 2 * TILE + 16)]))
    _ambient(sc, "low_pulse", 0.14, 6.0, 10.0)
    return sc


# ---- Room 4: the Sorting Hall (key: works_sorting) ----

def build_works_sorting():
    floor, objs = _box(16, 10)
    objs[5][0] = "F"          # west -> back to the vats
    objs[5][15] = "E"         # east -> the scriptorium
    for tx in (3, 6, 9, 12):  # long sorting tables, two rows
        objs[3][tx] = "t"
        objs[7][tx] = "t"
    objects = ["".join(r) for r in objs]
    sc = Scene("works_sorting", floor, objects, music="basement")
    sc.add_exit("F", "works_vats", "from_below")
    sc.add_exit("E", "works_scriptorium", "from_above")
    sc.set_spawn("default",    7, 5)
    sc.set_spawn("from_above", 1, 5)
    sc.set_spawn("from_below", 14, 5)

    # The belongings of the vanished, sorted into piles. Closed cases
    # (chests, never opened by the player) + the stains of the work.
    for tx, ty in [(6, 3), (12, 7)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE - 4,
                                     "chest", open=False))
    sc.add_decoration(Decoration(9 * TILE + 16, 3 * TILE - 4, "chest",
                                 open=False))
    sc.add_decoration(Decoration(4 * TILE + 16, 5 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(10 * TILE + 16, 8 * TILE + 16, "phantom_mark"))
    # A "wrong" mount oversees the catalogued belongings of the
    # vanished, and cobwebs grime the high corners.
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 18,
                                 "wrong_taxidermy", wall="N", seed=17))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc._table_pos = (6 * TILE + 16, 3 * TILE + 16)
    sc.hide_spots = [
        (5 * TILE + 16, 5 * TILE + 16, "behind"),
        (10 * TILE + 16, 3 * TILE + 16, "behind"),
        (10 * TILE + 16, 7 * TILE + 16, "behind"),
    ]
    # Two cultists sorting/patrolling -- the hardest crossing.
    sc.add_enemy(_cultist(4 * TILE + 16, 5 * TILE + 16, speed=0.9,
                          waypoints=[(4 * TILE + 16, 2 * TILE + 16),
                                     (4 * TILE + 16, 8 * TILE + 16)]))
    sc.add_enemy(_cultist(11 * TILE + 16, 5 * TILE + 16, speed=0.9,
                          waypoints=[(13 * TILE + 16, 5 * TILE + 16),
                                     (7 * TILE + 16, 5 * TILE + 16)]))
    _ambient(sc, "whisper", 0.13, 7.0, 12.0)

    def _interact(game):
        tx, ty = sc._table_pos
        if (abs(game.player.x - tx) < 40 and abs(game.player.y - ty) < 40):
            game.show_notice(
                "Coats. Boots. A child's shoe. All folded, all catalogued.",
                duration=3.5)
    sc.on_interact_fn = _interact
    return sc


# ---- Room 5: the Scriptorium (key: works_scriptorium) ----

def build_works_scriptorium():
    floor, objs = _box(12, 8)
    objs[4][0] = "F"          # west -> back to the sorting hall
    objs[4][11] = "E"         # east -> the sign chamber
    for tx, ty in [(3, 2), (7, 2), (5, 5)]:   # copying desks
        objs[ty][tx] = "t"
    objects = ["".join(r) for r in objs]
    sc = Scene("works_scriptorium", floor, objects, music="basement")
    sc.add_exit("F", "works_sorting", "from_below")
    sc.add_exit("E", "works_sign", "from_above")
    sc.set_spawn("default",    6, 4)
    sc.set_spawn("from_above", 1, 4)
    sc.set_spawn("from_below", 10, 4)

    # The Sign, copied over and over onto the walls.
    for tx, ty in [(2, 1), (5, 1), (9, 1), (10, 6)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "yellow_sign"))
    sc.add_decoration(Decoration(7 * TILE + 16, 2 * TILE + 6, "candle"))
    # Cobweb grime in the high corners of the scriptorium.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc._desk_pos = (3 * TILE + 16, 2 * TILE + 16)
    sc.hide_spots = [
        (5 * TILE + 16, 5 * TILE + 16, "behind"),
        (9 * TILE + 16, 5 * TILE + 16, "behind"),
    ]
    # One scribe, kneeling at a desk, oblivious (aggro 0) -- unless you
    # cross into its lane. Locked facing toward its work.
    scribe = _cultist(4 * TILE + 16, 2 * TILE + 16, speed=0.8,
                      waypoints=[(4 * TILE + 16, 2 * TILE + 16)])
    scribe.aggro = 0
    scribe.facing = (-1, 0)
    scribe.lock_facing = True
    sc.add_enemy(scribe)
    _ambient(sc, "blip_soft", 0.11, 3.0, 5.0)

    def _interact(game):
        dx, dy = sc._desk_pos
        if (abs(game.player.x - dx) < 40 and abs(game.player.y - dy) < 40):
            game.show_notice(
                "The Sign, copied over and over. To take your own you'd "
                "need charcoal and paper.", duration=4.0)
    sc.on_interact_fn = _interact
    return sc


# ---- Room 6: the Sign Chamber (key: works_sign) ----

def build_works_sign():
    floor, objs = _box(12, 10)
    objs[5][0] = "F"          # west -> back to the scriptorium
    objs[5][11] = "E"         # east -> the deep stair
    objects = ["".join(r) for r in objs]
    sc = Scene("works_sign", floor, objects, music="void")
    sc.add_exit("F", "works_scriptorium", "from_below")
    sc.add_exit("E", "works_deepstair", "from_above")
    sc.set_spawn("default",    5, 8)      # enter from the south, away from it
    sc.set_spawn("from_above", 1, 5)
    sc.set_spawn("from_below", 10, 5)

    # The Yellow Sign, daubed vast across the north wall. (Placeholder
    # imagery -- claw/mark clusters + a candle ring -- until a bespoke
    # Sign sprite exists.) The rubbing is taken at its centre.
    sign_x = 5 * TILE + 16
    sign_y = 1 * TILE + 16
    sc._sign_pos = (sign_x, sign_y)
    # The Sign itself -- one large glyph centred on the north wall,
    # flanked by two smaller ones, ringed with candles.
    sc.add_decoration(Decoration(sign_x, 1 * TILE + 18, "yellow_sign"))
    sc.add_decoration(Decoration(3 * TILE + 16, 1 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(7 * TILE + 16, 1 * TILE + 16, "yellow_sign"))
    for tx in (2, 4, 6, 8):
        sc.add_decoration(Decoration(tx * TILE + 16, 2 * TILE + 16, "candle"))
    # Cobweb grime in the low corners (the north wall is all Sign).
    sc.add_decoration(Decoration(1 * TILE + 6, 8 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(10 * TILE + 26, 8 * TILE + 26, "cobweb",
                                 ang=math.pi))
    sc.hide_spots = [
        (2 * TILE + 16, 7 * TILE + 16, "behind"),
        (9 * TILE + 16, 7 * TILE + 16, "behind"),
    ]
    # The congregation: three kneelers facing the Sign (north), plus one
    # patrol on the east flank. Kneelers start oblivious (aggro 0).
    for kx in (3, 5, 7):
        k = _cultist(kx * TILE + 16, 4 * TILE + 16, speed=0.8,
                     waypoints=[(kx * TILE + 16, 4 * TILE + 16)])
        k.aggro = 0
        k.facing = (0, -1)
        k.lock_facing = True
        sc.add_enemy(k)
    sc.add_enemy(_cultist(9 * TILE + 16, 7 * TILE + 16, speed=0.9,
                          waypoints=[(9 * TILE + 16, 3 * TILE + 16),
                                     (9 * TILE + 16, 8 * TILE + 16)]))
    _ambient(sc, "whisper", 0.16, 5.0, 9.0)

    def _interact(game):
        sx, sy = sc._sign_pos
        if (abs(game.player.x - sx) > 44 or abs(game.player.y - sy) > 56):
            return
        if game.save.flag("sign_rubbing_taken"):
            game.show_notice("You already pressed your rubbing of it.")
            return
        if not game.player.inventory.has("charcoal"):
            game.show_notice(
                "The Sign, vast on the stone. You'd need charcoal and "
                "paper to take a rubbing.", duration=4.0)
            return
        game.save.set_flag("sign_rubbing_taken", True)
        game.player.inventory.add("sigil_rubbing", 1)
        game.audio.play("pickup_rare", 0.7)
        game.audio.play("low_pulse", 0.5)
        _evidence(game, "the_sign",
            "A charcoal rubbing of the Sign. Proof of what they kneel to.")
    sc.on_interact_fn = _interact
    return sc


# ---- Room 7: the Deep Stair / orb-gate (key: works_deepstair) ----

def build_works_deepstair():
    floor, objs = _box(10, 8)
    objs[4][0] = "F"          # west -> back to the sign chamber
    objs[2][5] = "L"          # the stair down (visual; gated by the orb)
    objects = ["".join(r) for r in objs]
    sc = Scene("works_deepstair", floor, objects, music="void")
    sc.add_exit("F", "works_sign", "from_below")
    sc.set_spawn("default",    4, 5)
    sc.set_spawn("from_above", 1, 4)
    sc.set_spawn("from_below", 8, 4)

    gate_x = 5 * TILE + 16
    gate_y = 2 * TILE + 16
    sc._gate_pos = (gate_x, gate_y)
    sc.add_decoration(Decoration(3 * TILE + 16, 2 * TILE + 6, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 16, "bloodstain"))
    # Cobweb grime in the high corners by the orb-gate.
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (8 * TILE + 16, 1 * TILE + 24, "behind"),
    ]
    _ambient(sc, "low_pulse", 0.12, 10.0, 15.0)

    def _interact(game):
        if (abs(game.player.x - gate_x) > 40
                or abs(game.player.y - gate_y) > 40):
            return
        if game.save.flag("deepstair_open"):
            game.begin_transition("depths_antechamber", "from_above")
            return
        if not game.player.inventory.has("orb"):
            game.audio.play("door_locked", 0.5)
            game.show_notice("A socket in the black stone. Something round "
                             "belongs here.")
            return
        game.player.inventory.remove("orb", 1)
        game.save.set_flag("deepstair_open", True)
        game.audio.force_silence()
        game.audio.play("low_pulse", 0.95)
        game.show_notice("The stone drinks the orb. The stair grinds open.",
                         duration=4.0)
        game.begin_transition("depths_antechamber", "from_above")
    sc.on_interact_fn = _interact
    return sc
