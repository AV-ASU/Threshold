"""THE WORKS -- the Basement Level. The cult's underground labour,
reached ONLY by the rope down the village well. Seven rooms descend
from the shaft floor to the Deep Stair, which the keystone (the Pallid
Mask seated in the cult's notes) opens onto the Depths:

  well_bottom        -- the Shaft Floor (rope landing; the way back up)
  well_passage       -- the Drying Racks (first gauntlet)
  works_vats         -- the Cistern (the dig broke into the river)
  works_sorting      -- the Sorting Hall (shed lives of the claimed)
  works_scriptorium  -- the Scriptorium (the Sign, copied endlessly)
  works_sign         -- the Sign Chamber (lift the Pallid Mask; evidence #5)
  works_deepstair    -- the Deep Stair (the keystone opens it; rope snaps)

The rope breaks the instant you press the keystone to the Deep Stair
-- from then there is no climbing back, only deeper. Cultists labour here; the
flashlight works (these are DARK_SCENES, not cult-dark) but their gaze
still finds you, so the gauntlet is run on cover, timing, and the hide
spots. Combat is gone -- contact slams the dread aperture; the danger
is being seen. Cultists respect hiding (player.hidden), so a hide spot
breaks the chase.

Reworks vs. the old build: the well is now the ONLY mouth down (the
barn cellar hatch is sealed); nothing is consumed to land here; and the
way deeper opens only when the keystone -- the Pallid Mask (Sign Chamber)
seated in the cult's notes (Scriptorium) -- is pressed to the Deep Stair.
The stair opens WITHOUT consuming the keystone (§7): you carry it down and
spend it at the Threshold door to SEAL, or turn back while the rope holds
and carry it out to SPREAD. The fork between Seal and Spread lives at that
stair.
"""
import math
from constants import TILE
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence
from .depths import _box, _cultist, _ambient, _wall, _bevel


# ---- Room 1: the Shaft Floor (key: well_bottom) ----

def build_well_bottom():
    # The shaft floor: a round (octagonal) stone pit at the bottom of the
    # well, the rope/ladder dangling at one beveled edge.
    floor, objs = _box(12, 10)
    _bevel(objs, 3)
    objs[5][11] = "E"         # east -> the drying racks (deeper)
    objs[2][3]  = "U"         # ladder up -- climb is interact-gated below
    objects = ["".join(r) for r in objs]
    sc = Scene("well_bottom", floor, objects, music="basement")
    sc.add_exit("E", "well_passage", "from_above")
    sc.set_spawn("default",   5, 5)
    sc.set_spawn("from_well", 4, 3)       # land here on the descent
    sc.set_spawn("from_below", 9, 5)      # back up from the racks

    ladder_x = 3 * TILE + 16
    ladder_y = 2 * TILE + 16
    sc._ladder_pos = (ladder_x, ladder_y)
    sc.add_interactable(ladder_x, ladder_y, 40)   # [E] cue: climb the rope/ladder up
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE + 16, "bloodstain"))
    # A "wrong" mount in the well dark -- too many eyes.
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 18,
                                 "wrong_taxidermy", wall="N", seed=31))
    # Cobweb grime in the beveled corners away from the ladder.
    sc.add_decoration(Decoration(9 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_decoration(Decoration(1 * TILE + 6, 8 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.hide_spots = [
        (8 * TILE + 16, 6 * TILE + 16, "behind"),   # collapsed-timber nook
        (3 * TILE + 16, 6 * TILE + 16, "behind"),
    ]
    _ambient(sc, "low_pulse", 0.12, 9.0, 14.0)

    # The rope no longer snaps on the way down -- you can retreat up the
    # ladder through the whole Works gauntlet. The point of no return is
    # OPENING THE DEEP STAIR (committing to the Depths); that snaps it
    # (works_deepstair, below). The playscript now lives deep in the
    # Works (the Scriptorium), so it is never carried down from above.

    def _interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - ladder_x) < 40 and abs(py - ladder_y) < 40:
            if game.save.flag("well_rope_broken"):
                game.audio.play("door_locked", 0.5)
                game.show_notice("The rope is gone. Only the dark below.")
                return
            game.audio.play("door_open", 0.6)
            game.begin_transition("brimley", "from_well")
    sc.on_interact_fn = _interact
    return sc


# ---- Room 2: the Drying Racks (key: well_passage) ----

def build_well_passage():
    # A T-shaped drying corridor: a long E-W run with a central north bay
    # jutting up off it (a pocket of racks you have to step into).
    floor, objs = _box(16, 9)
    _wall(objs, 1, 1, 5, 3)        # seal the upper-left
    _wall(objs, 10, 1, 14, 3)      # seal the upper-right -> central bay at cols 6-9
    objs[5][0] = "F"          # west -> back to the shaft
    objs[5][15] = "E"         # east -> the cistern (deeper)
    # Drying racks (solid shelves) staggered in the corridor + bay, gaps
    # to weave through.
    for cx in (3, 6, 9, 12):
        objs[4][cx] = "s"
    for cx in (4, 7, 10, 13):
        objs[6][cx] = "s"
    objs[2][7] = "s"
    objects = ["".join(r) for r in objs]
    sc = Scene("well_passage", floor, objects, music="basement")
    sc.add_exit("F", "well_bottom", "from_below")
    sc.add_exit("E", "works_vats",  "from_above")
    sc.set_spawn("default",    6, 5)
    sc.set_spawn("from_above", 1, 5)      # arriving from the shaft
    sc.set_spawn("from_below", 14, 5)     # back from the vats
    # Legacy spawns kept so old saves + the (now unreachable) cult
    # chamber's exit still resolve. The barn tunnel is nailed shut from
    # below now -- the well is the only way underground.
    sc.set_spawn("from_well",    1, 5)
    sc.set_spawn("from_chamber", 14, 5)

    # Stores stacked up in the north bay -- a barrel and a crate.
    sc.add_furniture("barrel", [(8, 2)])
    sc.add_furniture("crate", [(6, 1)])
    sc.add_decoration(Decoration(8 * TILE + 16, 5 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(13 * TILE + 16, 7 * TILE + 22, "claw_marks"))
    # Cobweb grime in the high corners of the bay.
    sc.add_decoration(Decoration(6 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(9 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (8 * TILE + 16, 1 * TILE + 24, "behind"),    # up in the bay (blind)
        (4 * TILE + 16, 7 * TILE + 16, "behind"),    # between racks
        (11 * TILE + 16, 7 * TILE + 16, "behind"),
    ]
    # One cultist working the corridor, end to end.
    sc.add_enemy(_cultist(3 * TILE + 16, 5 * TILE + 16, speed=0.85))
    _ambient(sc, "cult_breath", 0.16, 5.0, 9.0)
    return sc


# ---- Room 3: the Cistern (key: works_vats) ----

def build_works_vats():
    # A cruciform cistern: four flooded arms off a central crossing, the
    # corners walled off into solid stone, a basin sunk in each arm.
    floor, objs = _box(13, 11)
    _wall(objs, 1, 1, 3, 3)        # NW
    _wall(objs, 9, 1, 11, 3)       # NE
    _wall(objs, 1, 7, 3, 9)        # SW
    _wall(objs, 9, 7, 11, 9)       # SE
    objs[5][0] = "F"          # west -> back to the racks
    objs[5][12] = "E"         # east -> the sorting hall
    objs[10][6] = "D"         # south arm -> the overflow sump (dead-end branch)
    objects = ["".join(r) for r in objs]
    sc = Scene("works_vats", floor, objects, music="basement")
    sc.add_exit("F", "well_passage", "from_below")
    sc.add_exit("E", "works_sorting", "from_above")
    sc.add_exit("D", "the_sump", "from_vats")
    sc.set_spawn("default",    6, 5)
    sc.set_spawn("from_above", 1, 5)
    sc.set_spawn("from_below", 11, 5)
    sc.set_spawn("from_the_sump", 6, 8)   # back up from the sump branch

    # Stone cistern basins brimming with black water -- volumetric props now
    # (round 3D basins), one sunk in each arm, with cold mist rising off them
    # (NARRATIVE 1b: the dig broke into the underground river, the artery to
    # the door). Wet stone, no bodies -- the claiming cult renders no one.
    for tx, ty in [(5, 2), (7, 2), (5, 8), (7, 8)]:
        sc.add_furniture("cistern_basin", [(tx, ty)])
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 6, "smoke"))
    sc.add_decoration(Decoration(6 * TILE + 16, 5 * TILE + 16, "candle"))
    # Cobweb grime in the high corners above the vats.
    sc.add_decoration(Decoration(4 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (6 * TILE + 16, 2 * TILE + 16, "behind"),   # in the north arm (blind)
        (6 * TILE + 16, 8 * TILE + 16, "behind"),   # in the south arm (blind)
    ]
    # Two cultists working the basins -- one walks the N-S arms, one the
    # E-W crossing.
    sc.add_enemy(_cultist(6 * TILE + 16, 5 * TILE + 16, speed=0.8))
    sc.add_enemy(_cultist(9 * TILE + 16, 5 * TILE + 16, speed=0.8))
    _ambient(sc, "low_pulse", 0.14, 6.0, 10.0)

    def _vats_on_enter(game, scene):
        # First entry: the dig hit water. This is the river (NARRATIVE 1b) --
        # the artery the cult followed down toward the door. Gated by the
        # evidence flag (non-canonical, so it doesn't move the King-gate).
        # Flag key kept (works_vats_seen) for save compat.
        if game.save.flag("evidence_works_vats_seen"):
            return
        _evidence(game, "works_vats_seen", [
            "[c=dim]The water runs on, downward, and does not echo back.[/c]",
        ])
    sc.on_enter_fn = _vats_on_enter
    return sc


# ---- Room 4: the Sorting Hall (key: works_sorting) ----

def build_works_sorting():
    # A T-shaped hall: a wide sorting floor with a short north stem in the
    # NE that rises to Mara's cell door.
    floor, objs = _box(16, 11)
    _wall(objs, 1, 1, 10, 3)      # seal the upper hall -> leaves a NE stem (cols 11-14)
    objs[6][0] = "F"          # west -> back to the vats
    objs[6][15] = "E"         # east -> the scriptorium
    objs[0][13] = "M"         # north (top of the stem) -> Mara's cell
    objs[10][4] = "D"         # south -> the holding cells (dead-end branch)
    for tx in (3, 6, 9, 12):  # long sorting tables, two rows on the hall floor
        objs[5][tx] = "t"
        objs[8][tx] = "t"
    objects = ["".join(r) for r in objs]
    sc = Scene("works_sorting", floor, objects, music="basement")
    sc.add_exit("F", "works_vats", "from_below")
    sc.add_exit("E", "works_scriptorium", "from_above")
    sc.add_exit("D", "the_cells", "from_sorting")
    sc.add_exit("M", "maras_room", "from_works_sorting")
    sc.set_spawn("default",    7, 6)
    sc.set_spawn("from_above", 1, 6)
    sc.set_spawn("from_below", 14, 6)
    sc.set_spawn("from_maras_room", 13, 3)   # back down through the stem
    sc.set_spawn("from_the_cells",  4, 9)    # back up from the cells branch

    # The worldly lives the congregation shed when they were claimed --
    # and the effects of the few the fold took -- sorted into piles
    # (NARRATIVE 1b/4: shed lives + the fold's lost, not murder victims).
    # Closed cases
    # (chests, never opened by the player -- interactive=False so they
    # don't show a dead [E] prompt) + the stains of the work.
    for tx, ty in [(5, 7), (12, 9)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE - 4,
                                     "chest", open=False, interactive=False))
    sc.add_decoration(Decoration(9 * TILE + 16, 7 * TILE - 4, "chest",
                                 open=False, interactive=False))
    sc.add_decoration(Decoration(4 * TILE + 16, 6 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(10 * TILE + 16, 9 * TILE + 16, "phantom_mark"))
    # A "wrong" mount oversees the catalogued lives the claimed shed,
    # and cobwebs grime the high corners.
    sc.add_decoration(Decoration(8 * TILE + 16, 3 * TILE + 18,
                                 "wrong_taxidermy", wall="N", seed=17))
    sc.add_decoration(Decoration(1 * TILE + 6, 4 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 26, 4 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # Crates of catalogued effects stacked up in the north stem.
    sc.add_furniture("crate", [(11, 2)])
    sc.add_furniture("crate", [(12, 2)])
    sc._table_pos = (6 * TILE + 16, 5 * TILE + 16)
    sc.hide_spots = [
        (5 * TILE + 16, 6 * TILE + 16, "behind"),
        (11 * TILE + 16, 6 * TILE + 16, "behind"),
        (13 * TILE + 16, 2 * TILE + 16, "behind"),   # up in the stem (blind)
    ]
    # Two cultists sorting/patrolling -- the hardest crossing.
    sc.add_enemy(_cultist(4 * TILE + 16, 6 * TILE + 16, speed=0.9))
    sc.add_enemy(_cultist(11 * TILE + 16, 6 * TILE + 16, speed=0.9))
    _ambient(sc, "whisper", 0.13, 7.0, 12.0)

    def _interact(game):
        tx, ty = sc._table_pos
        if (abs(game.player.x - tx) < 40 and abs(game.player.y - ty) < 40):
            if not game.save.flag("sorting_recognized"):
                game.save.set_flag("sorting_recognized", True)
                game.dialog.show([
                    "[c=dim]A child's shoe. Folded.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
            else:
                game.show_notice("A child's shoe. Folded.", duration=3.0)
    sc.on_interact_fn = _interact
    return sc


# ---- Mara's Room (key: maras_room) -- a convert's cell off the Sorting Hall ----

def build_maras_room():
    """Mara Blaine's cell, a side room off the Sorting Hall. She didn't
    rent a lodge room and vanish -- she moved IN, down here among the
    cult's works. A cot, a burnt-down candle, her cult robe on a peg, and
    folded in it the unsent letter to her father. Evidence #1: she came,
    and she joined willingly."""
    floor, objs = _box(10, 9)
    # A cramped cell with the cot walled off in a back alcove behind an
    # interior partition + doorway -- so the robe + letter (evidence #1) sit
    # in an indoor blind spot, unseen from the cell until the player rounds
    # the wall.
    for y in range(1, 5):
        objs[y][4] = "#"          # east wall of the alcove
    objs[3][4] = "."              # ...with a doorway gap
    for x in range(1, 4):
        objs[4][x] = "#"          # south wall of the alcove
    objs[8][5] = "F"              # south -> back up to the Sorting Hall
    objects = ["".join(r) for r in objs]
    sc = Scene("maras_room", floor, objects, music="basement")
    sc.add_exit("F", "works_sorting", "from_maras_room")
    sc.set_spawn("default", 5, 7)
    sc.set_spawn("from_works_sorting", 5, 7)

    sc._cot_pos = (2 * TILE + 16, 2 * TILE + 16)
    sc.add_interactable(sc._cot_pos[0], sc._cot_pos[1], 46)  # [E] cue: robe + letter (evidence #1)
    sc.add_furniture("bed", [(1, 1), (1, 2)], w=34, h=52)
    sc.add_decoration(Decoration(6 * TILE + 16, 1 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(8 * TILE + 16, 6 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(1 * TILE + 6, 7 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    for mx, my in [(6, 5), (4, 7)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))
    sc.hide_spots = [
        (2 * TILE + 16, 3 * TILE + 16, "under"),   # under the cot (in the alcove)
    ]
    _ambient(sc, "whisper", 0.10, 8.0, 13.0)

    def _interact(game):
        cx, cy = sc._cot_pos
        if (abs(game.player.x - cx) > 44 or abs(game.player.y - cy) > 48):
            return
        if game.save.flag("evidence_maras_room"):
            game.show_notice("Her cot, her robe. You've read what's here.")
            return
        game.player.inventory.add("robe", 1)
        # The unsent letter is its own item so the player still carries
        # her last sane line into the Dark -- re-readable from inventory.
        game.player.inventory.add("unsent_letter", 1)
        game.audio.play("pickup_rare", 0.7)
        _evidence(game, "maras_room", [
            "Her cell. A cot, a burnt-down candle, a cult robe on a peg -- "
            "worn soft. Chosen.",
            "Folded inside the robe: a letter to her father. Stamped, never "
            "mailed. It opens \"Dad.\"",
            "\"...I'm sorry for how I left. I couldn't explain it and have "
            "it sound sane. The dreams aren't dreams anymore -- they're "
            "full of answers. I'm just hunting the questions now. Don't "
            "come after me. I'm not lost. I've never been this close.\"",
            "This is a room someone moved into. Blaine hired you to bring "
            "her home. She was already home.",
        ])
    sc.on_interact_fn = _interact
    return sc


# ---- Room 5: the Scriptorium (key: works_scriptorium) ----

def build_works_scriptorium():
    # An octagonal vaulted scriptorium, copying desks ringed under the dome.
    floor, objs = _box(14, 9)
    _bevel(objs, 2)
    objs[4][0] = "F"          # west -> back to the sorting hall
    objs[4][13] = "E"         # east -> the sign chamber
    for tx, ty in [(4, 2), (8, 2), (6, 5)]:   # copying desks
        objs[ty][tx] = "t"
    objects = ["".join(r) for r in objs]
    sc = Scene("works_scriptorium", floor, objects, music="basement")
    sc.add_exit("F", "works_sorting", "from_below")
    sc.add_exit("E", "works_sign", "from_above")
    sc.set_spawn("default",    7, 4)
    sc.set_spawn("from_above", 2, 4)
    sc.set_spawn("from_below", 11, 4)

    # The Sign, copied over and over onto the walls.
    for tx, ty in [(3, 1), (6, 1), (10, 1), (10, 6)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "yellow_sign"))
    sc.add_decoration(Decoration(8 * TILE + 16, 2 * TILE + 6, "candle"))
    # Two stone columns hold up the vault.
    sc.add_furniture("pillar", [(4, 6)])
    sc.add_furniture("pillar", [(9, 6)])
    # Cobweb grime in the beveled corners of the scriptorium.
    sc.add_decoration(Decoration(2 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(11 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc._desk_pos = (4 * TILE + 16, 2 * TILE + 16)
    sc.add_interactable(sc._desk_pos[0], sc._desk_pos[1], 40)  # [E] cue: the Playscript
    sc.hide_spots = [
        (6 * TILE + 16, 6 * TILE + 16, "behind"),
        (10 * TILE + 16, 6 * TILE + 16, "behind"),
    ]
    # One scribe, kneeling at a desk, oblivious (aggro 0) -- unless you
    # cross into its lane. Locked facing toward its work.
    scribe = _cultist(5 * TILE + 16, 2 * TILE + 16, speed=0.8)
    scribe.aggro = 0
    scribe.facing = (-1, 0)
    scribe.lock_facing = True
    sc.add_enemy(scribe)
    _ambient(sc, "blip_soft", 0.11, 3.0, 5.0)

    def _interact(game):
        dx, dy = sc._desk_pos
        if (abs(game.player.x - dx) > 40 or abs(game.player.y - dy) > 40):
            return
        # The cult's notes -- the deep-gate key -- the one bound, whole
        # volume among the congregation's endless flat copies of the Sign.
        # Their own record, not a copy. Taken here, carried to the Deep Stair.
        if not game.save.flag("scriptorium_playscript_taken"):
            game.save.set_flag("scriptorium_playscript_taken", True)
            game.player.inventory.add("playscript", 1)
            game.audio.play("pickup_rare", 0.7)
            game.audio.play("low_pulse", 0.45)
            game.dialog.show([
                "[c=dim]Among the loose copies, one volume is bound and "
                "whole -- their own notes, not the Sign traced again. A "
                "mask-shaped recess in the cover. You take it.[/c]",
                "[c=dim]The scribe is wet to the knee.[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        game.show_notice(
            "The Sign, copied over and over across every surface -- a "
            "thousand flat echoes. None of them the thing itself.",
            duration=4.0)
    sc.on_interact_fn = _interact
    return sc


# ---- Room 6: the Sign Chamber (key: works_sign) ----

def build_works_sign():
    # An apse: the north end rounded (beveled) around the altar, the
    # congregation floor opening out square to the south.
    floor, objs = _box(13, 11)
    _bevel(objs, 3, corners=("NW", "NE"))
    objs[5][0] = "F"          # west -> back to the scriptorium
    objs[5][12] = "E"         # east -> the deep stair
    objects = ["".join(r) for r in objs]
    sc = Scene("works_sign", floor, objects, music="void")
    sc.add_exit("F", "works_scriptorium", "from_below")
    sc.add_exit("E", "works_deepstair", "from_above")
    sc.set_spawn("default",    6, 9)      # enter from the south, away from it
    sc.set_spawn("from_above", 1, 5)
    sc.set_spawn("from_below", 11, 5)

    # The Yellow Sign, daubed vast across the apse -- the cult's 2D
    # *brand* of Him. The thing itself, evidence #5, is the Pallid Mask on
    # the altar (a pedestal) in the apse. You lift it at the altar.
    sign_x = 6 * TILE + 16
    sc._sign_pos = (6 * TILE + 16, 2 * TILE + 20)   # the altar, not the wall
    sc.add_decoration(Decoration(6 * TILE + 16, 2 * TILE + 24, "pedestal"))
    # [E] cue at the altar -- the Mask / rite choice is the key decision
    # of the run and must read as interactable.
    sc.add_interactable(sc._sign_pos[0], sc._sign_pos[1], 50)
    # The Sign itself -- one large glyph centred in the apse, flanked by
    # two smaller ones, ringed with candles.
    sc.add_decoration(Decoration(sign_x, 1 * TILE + 18, "yellow_sign"))
    sc.add_decoration(Decoration(4 * TILE + 16, 1 * TILE + 16, "yellow_sign"))
    sc.add_decoration(Decoration(8 * TILE + 16, 1 * TILE + 16, "yellow_sign"))
    for tx in (4, 5, 7, 8):
        sc.add_decoration(Decoration(tx * TILE + 16, 3 * TILE + 16, "candle"))
    # Pews behind the kneeling congregation.
    for px in (4, 6, 8):
        sc.add_furniture("pew", [(px, 7)])
    # Cobweb grime in the square south corners.
    sc.add_decoration(Decoration(1 * TILE + 6, 9 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(11 * TILE + 26, 9 * TILE + 26, "cobweb",
                                 ang=math.pi))
    sc.hide_spots = [
        (2 * TILE + 16, 8 * TILE + 16, "behind"),
        (10 * TILE + 16, 8 * TILE + 16, "behind"),
    ]
    # The congregation: three kneelers facing the Sign (north), plus one
    # patrol on the east flank. Kneelers start oblivious (aggro 0).
    for kx in (4, 6, 8):
        k = _cultist(kx * TILE + 16, 5 * TILE + 16, speed=0.8)
        k.aggro = 0
        k.facing = (0, -1)
        k.lock_facing = True
        sc.add_enemy(k)
    sc.add_enemy(_cultist(10 * TILE + 16, 7 * TILE + 16, speed=0.9))
    _ambient(sc, "whisper", 0.16, 5.0, 9.0)

    def _take_mask(game):
        game.save.set_flag("sign_rubbing_taken", True)
        game.player.inventory.add("sigil_rubbing", 1)
        game.audio.play("pickup_rare", 0.7)
        game.audio.play("low_pulse", 0.5)
        _evidence(game, "the_sign", [
            "On the altar, beneath the daubed Sign: a mask. Pale as a "
            "drowned face, the eyeholes black.",
            "Every scrawl in this place is a flat copy of it. This is the "
            "thing itself.",
            "You lift it. Lighter than it should be, and warm. It knows "
            "your hands.",
            "His face. You're holding His face.",
        ])

    def _interact(game):
        sx, sy = sc._sign_pos
        if (abs(game.player.x - sx) > 44 or abs(game.player.y - sy) > 56):
            return
        if game.save.flag("sign_rubbing_taken"):
            game.show_notice("The altar is bare. You have His face.")
            return
        # Two instincts at the altar (NARRATIVE §6). Lifting the mask is the
        # controlled keystone-removal the chosen endings need. Tearing the
        # whole rite down here -- the obvious heroic move -- is THE TRAP:
        # the rite is the only lid on Him, and breaking it before the source
        # (the Threshold) is sealed lets His influence out uncontained. It is
        # always pre-seal here, so this is always the catastrophe.
        def _pick(idx):
            if idx == 0:
                _take_mask(game)
            elif idx == 1:
                game._play_ending("rite_broken")
        game.dialog.show_choice(
            "The mask on the altar. The Sign daubed above it. The kneeling "
            "at your back. The whole sick machine of it, here in reach.",
            ["Lift the mask.", "Tear it down -- end this."],
            _pick, speaker="", voice="blip_soft", portrait="narrator")
    sc.on_interact_fn = _interact
    return sc


# ---- Room 7: the Deep Stair / keystone gate (key: works_deepstair) ----

def build_works_deepstair():
    # An octagonal gate chamber, the Deep Stair sunk in the north face.
    floor, objs = _box(11, 9)
    _bevel(objs, 2)
    objs[4][0] = "F"          # west -> back to the sign chamber
    objs[2][5] = "L"          # the stair down (visual; gated by Mask + Play)
    objects = ["".join(r) for r in objs]
    sc = Scene("works_deepstair", floor, objects, music="void")
    sc.add_exit("F", "works_sign", "from_below")
    sc.set_spawn("default",    5, 5)
    sc.set_spawn("from_above", 2, 4)
    sc.set_spawn("from_below", 8, 4)

    gate_x = 5 * TILE + 16
    gate_y = 2 * TILE + 16
    sc._gate_pos = (gate_x, gate_y)
    sc.add_interactable(gate_x, gate_y, 40)   # [E] cue: the Deep Stair (keystone gate)
    sc.add_decoration(Decoration(3 * TILE + 16, 2 * TILE + 6, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE + 16, "bloodstain"))
    # Cobweb grime in the beveled corners by the keystone gate.
    sc.add_decoration(Decoration(2 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (8 * TILE + 16, 6 * TILE + 16, "behind"),
        (2 * TILE + 16, 6 * TILE + 16, "behind"),
    ]
    _ambient(sc, "low_pulse", 0.12, 10.0, 15.0)

    def _interact(game):
        if (abs(game.player.x - gate_x) > 40
                or abs(game.player.y - gate_y) > 40):
            return
        if game.save.flag("deepstair_open"):
            game.begin_transition("depths_antechamber", "from_above")
            return
        inv = game.player.inventory
        has_play = inv.has("playscript")
        has_mask = inv.has("sigil_rubbing")     # the Pallid Mask
        if not (has_play and has_mask):
            game.audio.play("door_locked", 0.5)
            if not has_play and not has_mask:
                game.show_notice("A slot the size of a folded book, and "
                                 "above it a socket the shape of a face. "
                                 "Both empty.")
            elif not has_play:
                game.show_notice("His face fits the socket above. But the "
                                 "slot below -- a folded book's size -- "
                                 "stays empty.")
            else:
                game.show_notice("Their notes fit the slot. But the socket "
                                 "above -- the shape of a face -- stays "
                                 "empty.")
            return
        # Both in hand: lay out the fork once, commit on the next press.
        # Turning back keeps the keystone for the rope -- the Spread road
        # (carry His face out). Pressing it here OPENS the stair but does
        # NOT consume it (§7): you carry the keystone down and spend it at
        # the Threshold door -- the Seal road.
        if not game.save.flag("deepstair_fork_seen"):
            game.save.set_flag("deepstair_fork_seen", True)
            game.audio.play("low_pulse", 0.5)
            game.dialog.show([
                "[c=dim](His face fits the socket; their notes fit the slot "
                "below. The keystone, whole. Press it to the stone and the "
                "stair will open.)[/c]",
                "You have enough. The register, the names, the Preacher, the "
                "girl her father sent you for -- and the keystone in your "
                "hands.",
                "The town belongs to Him; that is why not one of them can "
                "leave. But you were never claimed. His Sign, carried out by "
                "the one soul He never took -- the fold opens only for that. "
                "Climb out while the rope holds, and let the world learn His "
                "name.",
                "[s=slow]Or you carry the keystone down, past her, to the "
                "thing all of this kneels to -- and give it to the door.[/s]",
                "[c=dim](Press again to open the stair and carry the keystone "
                "down -- or turn back, while the rope still holds.)[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        # Commit -- press the keystone to the stone. The stair OPENS to His
        # own authority but the keystone is NOT spent here (§7 rework): you
        # keep the Mask and the notes and carry them down to the Threshold
        # door. Point of no return: the rope far above snaps.
        game.save.set_flag("deepstair_open", True)
        game.save.set_flag("well_rope_broken", True)
        game.audio.force_silence()
        game.audio.play("low_pulse", 0.95)
        game.show_notice("You press the keystone to the stone. It knows its "
                         "own -- the stair grinds open, and far above, the "
                         "rope snaps. You lift the keystone away again and go "
                         "down. Only down, now.", duration=4.5)
        game.begin_transition("depths_antechamber", "from_above")
    sc.on_interact_fn = _interact

    def _on_exit(game, scene):
        # Re-arm the two-press fork each visit: clearing this means a player
        # who steps away to weigh the Spread road and returns gets the
        # warning again before the irreversible commit -- never a lone-press
        # point-of-no-return. Harmless after committing (deepstair_open wins).
        game.save.set_flag("deepstair_fork_seen", False)
    sc.on_exit_fn = _on_exit
    return sc


# ---- Side branch: the Overflow Sump (key: the_sump) off the Cistern ----

def build_the_sump():
    """A round overflow sump off the Cistern -- a dead-end pocket where the
    dug-into river pools and goes nowhere. Octagonal, flooded, cold. The
    diggers left a stash of cartridges on the dry ledge (one-time)."""
    floor, objs = _box(10, 9)
    _bevel(objs, 3)
    objs[0][5] = "F"          # north -> back up to the Cistern
    objects = ["".join(r) for r in objs]
    sc = Scene("the_sump", floor, objects, music="basement")
    sc.add_exit("F", "works_vats", "from_the_sump")
    sc.set_spawn("default",   5, 5)
    sc.set_spawn("from_vats", 5, 2)
    # Black water pooled in two stone basins, a barrel + crate of the diggers'
    # supplies on the dry ledge, cold mist rising, a candle.
    sc.add_furniture("cistern_basin", [(4, 6)])
    sc.add_furniture("cistern_basin", [(6, 6)])
    sc.add_furniture("barrel", [(7, 4)])
    sc.add_furniture("crate", [(3, 4)])
    for tx, ty in [(3, 5), (6, 6), (4, 7)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 6, "smoke"))
    sc.add_decoration(Decoration(5 * TILE + 16, 3 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 6, 5 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(7 * TILE + 26, 5 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = [
        (3 * TILE + 16, 6 * TILE + 16, "behind"),
        (7 * TILE + 16, 6 * TILE + 16, "behind"),
    ]
    _ambient(sc, "low_pulse", 0.12, 8.0, 13.0)

    def _on_enter(game, scene):
        from .base import drop_ammo_cache
        drop_ammo_cache(game, scene, 5, 6, 4, "ammo_sump")
    sc.on_enter_fn = _on_enter
    return sc


# ---- Side branch: the Holding Cells (key: the_cells) off the Sorting Hall ----

def build_the_cells():
    """A short corridor of holding cells off the Sorting Hall -- a comb of
    narrow stalls where the claimed were kept the first night, before they
    stopped needing keeping. Empty now, doors hanging. A dead-end branch:
    cover, dread, and the cult's whisper."""
    floor, objs = _box(12, 11)
    # A central corridor with cell stalls combed off the east and west walls.
    _wall(objs, 1, 1, 10, 1)            # seal the top...
    objs[1][5] = "."
    objs[1][6] = "."                    # ...leaving the entry throat to the hall
    for cy in (3, 5, 7):                # cell dividers reaching in from each side
        _wall(objs, 1, cy, 3, cy)
        _wall(objs, 8, cy, 10, cy)
    objs[0][5] = "F"          # north -> back to the Sorting Hall
    objects = ["".join(r) for r in objs]
    sc = Scene("the_cells", floor, objects, music="basement")
    sc.add_exit("F", "works_sorting", "from_the_cells")
    sc.set_spawn("default",     5, 2)
    sc.set_spawn("from_sorting", 5, 2)
    # The leavings of the kept: bare cots in the stalls, old stains, a corn
    # doll left behind. Phantom marks scratched at child height.
    sc.add_furniture("cot", [(2, 4)])           # west cell
    sc.add_furniture("cot", [(9, 6)])           # east cell
    sc.add_furniture("cot", [(2, 8)])           # west cell
    sc.add_decoration(Decoration(9 * TILE + 16, 4 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(2 * TILE + 16, 6 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(9 * TILE + 16, 8 * TILE + 16, "corn_doll"))
    sc.add_decoration(Decoration(9 * TILE + 28, 4 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(2 * TILE + 28, 6 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(6 * TILE + 16, 9 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(1 * TILE + 6, 9 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.hide_spots = [
        (3 * TILE + 16, 4 * TILE + 16, "behind"),   # beside a west cot
        (8 * TILE + 16, 6 * TILE + 16, "behind"),   # beside an east cot
        (6 * TILE + 16, 6 * TILE + 16, "behind"),   # in the corridor
    ]
    _ambient(sc, "whisper", 0.13, 6.0, 11.0)

    def _on_enter(game, scene):
        if game.save.flag("first_cells"):
            return
        game.save.set_flag("first_cells", True)
        game.show_notice("A row of stalls, the doors standing open. They only "
                         "needed locks the first night. After that, no one "
                         "wanted to leave.", duration=4.0)
    sc.on_enter_fn = _on_enter
    return sc
