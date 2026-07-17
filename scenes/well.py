"""THE WORKS -- the Basement Level. The cult's underground labour,
reached ONLY through the descent fold in the effigy grove (the rite:
the Invitation at 3 evidence, the school door, the clearing). Seven
rooms descend from the shaft floor to the Deepest Face, where the
blast (powder from the Sump, Mask in hand) opens the fall into the
Depths:

  well_bottom        -- the Shaft Floor (the fold lands you here; its
                        return pane is the way back up)
  well_passage       -- the Timber Racks (first gauntlet)
  works_cistern         -- the Cistern (the dig broke into the river)
  works_sorting      -- the Sorting Hall (shed lives of the claimed)
  works_scriptorium  -- the Scriptorium (the Sign, copied endlessly)
  works_sign         -- the Sign Chamber (lift the Pallid Mask, the keystone item)
  works_deepface    -- the Deepest Face (the dig's end: powder from the
                        Sump blasts the last few feet; the FALL into the
                        old workings is one-way)

THE WAY HOME is KEYED, not one-way (one-way stays the King's signature):
after the grove rite the circle holds you, and the shaft-floor return
pane answers only His face. Crossing up WITH the Mask seals the descent
behind you (descent_sealed) and locks the run to SPREAD; walking the
breach down to the Threshold with it is SEAL. Cultists labour here; the
flashlight works (these are DARK_SCENES, not cult-dark) but their gaze
still finds you, so the gauntlet is run on cover, timing, and the hide
spots. Combat is gone -- contact slams the dread aperture; the danger
is being seen. Cultists respect hiding (player.hidden), so a hide spot
breaks the chase.

Reworks vs. the old build: the rope is CUT -- the only way down is the
rite; the Deep Stair is CUT (the mine never finished; the cult's own
testimony says a few feet of earth remained) -- the way deeper is the
BLAST at the deepest face (powder from the Sump, Mask in hand first).
The Mask is NOT spent at the face (§7): you carry it down and spend it
at the Threshold door to SEAL, or carry it up through the keyed pane and
out (SPREAD). The fork is experiential now -- where you carry His face
-- not a menu.
"""
import math
from constants import TILE
from entities.decoration import Decoration
from entities.npc import NPC
from .base import Scene
from .dialogue import _evidence
from .depths import _box, _cultist, _ambient, _wall, _bevel, _flood, _rect_tiles


# ---- Room 1: the Shaft Floor (key: well_bottom) ----

def build_well_bottom():
    # The shaft floor: a round (octagonal) stone pit at the bottom of the
    # cult's mine shaft. No rope, no ladder: the descent fold in the grove
    # lands you here, and its RETURN PANE ('O', walked west) stands where the
    # rope once hung -- symmetric while it lives, dead once the descent
    # seals (descent_sealed).
    floor, objs = _box(12, 10)
    _bevel(objs, 3)
    objs[5][11] = "E"         # east -> the timber racks (deeper)
    objs[2][3]  = "O"         # the way back up: the fold's return pane
    #                             (the marker char: invisible, walkable)
    objects = ["".join(r) for r in objs]
    sc = Scene("well_bottom", floor, objects, music="basement")
    sc.add_exit("E", "well_passage", "from_above")
    sc.add_exit("O", "effigy_grove", "from_well_bottom", direction="west")
    sc.set_spawn("default",   5, 5)
    sc.set_spawn("from_grove", 4, 4)      # land here on the descent (east
    #                                       of the return pane, carried
    #                                       clear of it)
    sc.set_spawn("from_below", 9, 5)      # back up from the racks

    def _up_charge(game, ch):
        if ch == "O" and game.save.flag("descent_sealed"):
            return 0.0
        return 1.0
    sc.fold_charge_fn = _up_charge

    def _up_gate(game, ch):
        if ch != "O":
            return True
        if game.save.flag("descent_sealed"):
            return False
        # The way home answers only His face (the Mask). NOT one-way --
        # one-way stays the King's signature; this pane is KEYED. The
        # crossing itself spends the privilege: the descent seals at
        # your back (descent_sealed), and SPREAD is all that is left.
        if not game.player.inventory.has("pallid_mask"):
            if not game.save.flag("pane_refused_noticed"):
                game.save.set_flag("pane_refused_noticed", True)
                game.audio.play("low_pulse", 0.5)
                game.show_notice("The pane stands where the rope hung, "
                                 "and it does not open. It is waiting on "
                                 "a face.", duration=3.6)
            return False
        game.save.set_flag("descent_sealed", True)
        return True
    sc.exit_gate_fn = _up_gate

    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 22, "candle"))
    # (The "wrong" taxidermy mount was cut, 2026-07 process audit:
    # nobody hung a hunting trophy at the bottom of a mine shaft.)
    # Cobweb grime in the beveled corners away from the ladder.
    sc.add_decoration(Decoration(9 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_decoration(Decoration(1 * TILE + 6, 8 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(3 * TILE + 26, 1 * TILE + 6, "cobweb", ang=0.0))

    # --- Shaft-floor dressing: the head of the haul (2026-07 art pass) ---
    # Fallen shoring timbers collapsed into the SE -- the cover the hide spot
    # crouches behind.
    sc.add_furniture("firewood", [(7, 7)], w=44, h=22, seed=3)
    sc.add_furniture("firewood", [(8, 7)], w=40, h=20, seed=4)
    # Supplies once lowered down the shaft, left to rot against the NE wall, and
    # a stray crate in the SW the second hide spot can crouch behind.
    sc.add_furniture("barrel", [(8, 2)])
    sc.add_furniture("crate", [(2, 6)])
    # The haul head: spoil staged against the walls waiting on a rope
    # that is gone, and the barrow that carried it, parked mid-floor.
    sc.add_furniture("spoil_heap", [(3, 3)], seed=1, see_over=True)
    sc.add_furniture("spoil_heap", [(7, 3)], seed=6, see_over=True)
    sc.add_decoration(Decoration(6 * TILE + 16, 6 * TILE + 16,
                                 "wheelbarrow"))
    # Water seeping to the lowest place (NARRATIVE §2): a thin teal rivulet
    # pooling in the SW. (The drowned-body decal that lay in it was cut by
    # design call, 2026-07 -- the pool and the claw gouges carry the dread.)
    sc.add_decoration(Decoration(4 * TILE + 16, 7 * TILE + 16, "water_trail",
                                 ang=math.pi / 2, seed=5))
    sc.add_decoration(Decoration(5 * TILE + 16, 8 * TILE + 12, "water_trail",
                                 pool=True, seed=9))
    # Grime: the diggers' pick and hand gouges in the stone, mud tracked
    # from the landing. (The old red stains were cut, 2026-07: the mine
    # was dug by the willing; nobody bled anybody down here.)
    sc.add_decoration(Decoration(10 * TILE + 8, 4 * TILE + 16, "claw_marks",
                                 scale=1.8))
    sc.add_decoration(Decoration(5 * TILE + 16, 1 * TILE + 10, "claw_marks",
                                 scale=1.4))
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 16, "mud_footprint"))
    sc.add_decoration(Decoration(6 * TILE + 16, 4 * TILE + 16, "mud_footprint"))
    for mx, my in ((4, 4), (7, 5), (5, 7)):
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))

    sc.hide_spots = []
    _ambient(sc, "low_pulse", 0.12, 9.0, 14.0)

    # TODO #9 -- the SPREAD counterweight. A SPREAD-bound player never
    # passes the Deepest Face fuse (where both roads are spoken), so the
    # fork could end without ever reading as a fork. One interior-voice
    # beat, fired ONCE, on standing at the way up with His face in hand:
    # it names the other road and leaves the crossing itself silent (the
    # fold stays a non-event; the stakes land BEFORE the pane, never on
    # it). Fires for a SEAL-bound backtracker too, which only sharpens
    # the choice. Never evidence.
    def _bottom_on_enter(game, scene):
        if game.save.flag("spread_counterweight"):
            return
        if game.save.flag("descent_sealed"):
            return
        if not game.player.inventory.has("pallid_mask"):
            return
        game.save.set_flag("spread_counterweight", True)
        game.audio.play("low_pulse", 0.5)
        game.dialog.show([
            "[c=dim]The pane stands where the rope hung, and with His "
            "face in your hands you can feel it holding the door open "
            "for you. Up is real again. The roads would run.[/c]",
            "[c=dim]And under your feet the dig runs the other way, down "
            "to the thing this whole town kneels to. You could end it "
            "where it starts. Nobody is coming down here after you to do "
            "it instead.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
    sc.on_enter_fn = _bottom_on_enter

    # The Works gauntlet is walkable both ways for the Mask-bearer; for
    # anyone else the pane above refuses (keyed to His face). The fall
    # through the blasted face (works_deepface) is the one-way step.
    return sc


# ---- Room 2: the Timber Racks (key: well_passage) ----

def build_well_passage():
    # A T-shaped storage gallery, LONG: a 24-tile E-W run with a central
    # north bay jutting up off it (a pocket of racks you have to step
    # into). The dig's LUMBER lives here -- shoring boards came down the
    # shaft and staged in racks on their way to the faces (2026-07: the
    # old "drying corn-doll material" fiction was cut; an obsessive dig
    # runs no craft room, and the second gallery off the haul head is
    # exactly where a mine keeps its timber). Lengthened 2026-07 (the
    # stealth pass): the first gauntlet room teaches reading a patrol at
    # distance, so the run must be long enough for "far" to mean
    # something under the graded suspicion model.
    floor, objs = _box(24, 9)
    _wall(objs, 1, 1, 7, 3)        # seal the upper-left
    _wall(objs, 12, 1, 22, 3)      # seal the upper-right -> central bay at cols 8-11
    objs[5][0] = "F"          # west -> back to the shaft
    objs[5][23] = "E"         # east -> the cistern (deeper)
    # Timber racks (solid shelves) staggered down the corridor + bay,
    # gaps to weave through -- the cover ladder the whole run.
    for cx in (3, 6, 9, 12, 15, 18, 21):
        objs[4][cx] = "s"
    for cx in (4, 7, 10, 13, 16, 19):
        objs[6][cx] = "s"
    objs[2][9] = "s"
    objects = ["".join(r) for r in objs]
    sc = Scene("well_passage", floor, objects, music="basement")
    sc.add_exit("F", "well_bottom", "from_below")
    sc.add_exit("E", "works_cistern",  "from_above")
    sc.set_spawn("default",    8, 5)
    sc.set_spawn("from_above", 1, 5)      # arriving from the shaft
    sc.set_spawn("from_below", 22, 5)     # back from the vats
    # The barn tunnel is nailed shut from below now -- the grove's
    # descent fold is the only way underground.

    # Stores stacked up in the north bay -- a barrel and a crate.
    sc.add_furniture("barrel", [(10, 2)])
    sc.add_furniture("crate", [(8, 1)])
    # Timber SETS where the gallery needs holding (2026-07 art pass):
    # one frame over each portal mouth (uprights flanking the walking
    # lane, the header beam passed under -- the Threshold's grammar in
    # spiked lumber) and one wide frame over the bay entry. The uprights
    # sit on the same tiles the old posts did; the lanes walk under.
    sc.add_furniture("shoring_frame", [(1, 4), (1, 6)],
                     seed=2, ang=math.pi / 2, span=64)
    sc.add_furniture("shoring_frame", [(22, 4), (22, 6)],
                     seed=11, ang=math.pi / 2, span=64)
    sc.add_furniture("shoring_frame", [(8, 3), (11, 3)],
                     seed=5, ang=0.0, span=96)
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(20 * TILE + 16, 7 * TILE + 22, "claw_marks"))
    # Cobweb grime in the high corners of the bay.
    sc.add_decoration(Decoration(8 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(11 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))

    # Sawn lumber staged in the bay pocket and against the south wall --
    # board piles waiting on the faces (this is what the racks are FOR).
    # Kept OFF the walking lane and the rack weave gaps; the far end of
    # the run stands empty: the dig was eating its own stores by the end.
    sc.add_furniture("firewood", [(11, 2)], w=38, h=18, seed=22)
    sc.add_furniture("firewood", [(11, 1)], w=30, h=14, seed=21)
    sc.add_furniture("firewood", [(18, 7)], w=28, h=14, seed=23)
    # Grime: mud tracked from the shaft, a cold drip seeping through.
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 16, "mud_footprint"))
    sc.add_decoration(Decoration(12 * TILE + 16, 7 * TILE + 16, "water_trail",
                                 ang=math.pi / 2, seed=6))
    for mx, my in ((9, 3), (15, 5), (3, 5), (20, 5)):
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))

    # Two enclosed hides spaced down the run (DESIGN.md §12): the gap
    # under the bay's timber rack, and one under a far corridor rack --
    # a long room needs a rooted option in each half, or the east end is
    # a dead sprint. A searcher that loses you will sweep and CHECK them.
    sc.hide_spots = [
        (9 * TILE + 16, 3 * TILE + 8, "under"),    # under the bay rack
        (18 * TILE + 16, 5 * TILE + 8, "under"),   # under the far rack
    ]
    # Two cultists working the corridor, end to end, offset phases --
    # the west half and the east half are never both clear at once.
    sc.add_enemy(_cultist(3 * TILE + 16, 5 * TILE + 16, speed=0.85))
    sc.add_enemy(_cultist(16 * TILE + 16, 5 * TILE + 16, speed=0.85))
    # The lumber work (the JOBS layer, 2026-07 stealth pass): stations at
    # the bay pile and the far stack, so the patrol has a READABLE rhythm
    # the player can learn from cover -- travel, dwell over the boards,
    # move on. Noise and sightings still outrank the chore.
    sc.add_cult_station(10 * TILE + 16, 3 * TILE + 16,
                        face=(0, -1), dwell=(3.0, 5.5))
    sc.add_cult_station(18 * TILE + 16, 6 * TILE + 16,
                        face=(0, 1), dwell=(3.0, 5.5))
    sc.add_cult_station(2 * TILE + 16, 5 * TILE + 16,
                        face=(-1, 0), dwell=(2.0, 4.0))
    _ambient(sc, "cult_breath", 0.16, 5.0, 9.0)
    # Chalk doors -- the motif thickening underground (floor + wall). The
    # first Works door carries the voice beat (rattled).
    sc.add_chalk_door(3 * TILE + 16, 6 * TILE + 16, voice="chalk_works", seed=2)
    sc.add_chalk_door(15 * TILE + 16, 6 * TILE + 16, seed=8)
    sc.add_chalk_door(20 * TILE + 16, 7 * TILE + 28, seed=4, wall=True)
    return sc


# ---- Room 3: the Cistern (key: works_cistern) ----

def build_works_cistern():
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
    # Flood the N and S arms (the basin arms + the sump branch): reaching a
    # basin, the SE hide, or the sump means WADING (slow + a loud splash the
    # basin workers converge on). The E-W crossing (rows 4-6) stays dry, so
    # the through route W<->E is a dry corridor -- the water is a risk you
    # take on, not a wall (WADE_*).
    floor = _flood(floor, objs, _rect_tiles(4, 1, 8, 3) + _rect_tiles(4, 7, 8, 9))
    objects = ["".join(r) for r in objs]
    sc = Scene("works_cistern", floor, objects, music="basement")
    sc.add_exit("F", "well_passage", "from_below")
    sc.add_exit("E", "works_sorting", "from_above")
    sc.add_exit("D", "the_sump", "from_vats")
    sc.set_spawn("default",    6, 5)
    sc.set_spawn("from_above", 1, 5)
    sc.set_spawn("from_below", 11, 5)
    sc.set_spawn("from_the_sump", 6, 8)   # back up from the sump branch

    # Stone cistern basins brimming with black water -- volumetric props now
    # (round 3D basins), one sunk in each arm, with cold mist rising off them
    # (NARRATIVE §2: the dig broke into the underground river, the artery to
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
    # One enclosed hide (DESIGN.md §12): the dry lee under the SE
    # basin's lip -- inside the patrol's own arm, so it is a risky option
    # a searcher can sweep, not a panic room.
    sc.hide_spots = [
        (7 * TILE + 16, 9 * TILE + 8, "under"),   # under the SE basin lip
    ]
    # Two cultists working the basins -- one walks the N-S arms, one the
    # E-W crossing.
    sc.add_enemy(_cultist(6 * TILE + 16, 5 * TILE + 16, speed=0.8))
    sc.add_enemy(_cultist(9 * TILE + 16, 5 * TILE + 16, speed=0.8))
    _ambient(sc, "low_pulse", 0.14, 6.0, 10.0)
    # The diggers' DEWATERING PUMP on the west arm (a hand pitcher pump
    # on a driven well point; the dig broke into the river and has to be
    # pumped or it drowns): knock the arm loose and the hose run clanks
    # and hisses -- a lure that pulls the basin workers off the crossing
    # until one of them wedges it still. (Kind stays "valve": the noise
    # mechanic + tests key on it; this is a fiction/art reskin, 2026-07.)
    sc.add_decoration(Decoration(2 * TILE + 16, 4 * TILE + 6, "valve"))
    sc.add_noise_source(
        2 * TILE + 16, 4 * TILE + 12, "valve", period=1.1, reach=380.0,
        sfx="valve_hiss",
        on_notice="You knock the pump arm loose. The hose line begins "
                  "to clank and hiss.",
        off_notice="You wedge the pump arm still.",
        silenced_notice="A hand wedges the pump arm still. The hiss "
                        "dies in the line.")
    # A loose plank over the south-arm runoff channel.
    sc.add_noise_trap(6 * TILE + 16, 7 * TILE + 16, "plank", seed=11)
    # The basin work: the two cultists tend the four vats in rounds --
    # stand at a lip, chant over the black water, move to the next
    # (systems/stealth.errand_step; noise and sightings outrank the
    # chore). What the valve lure pulls them OFF of.
    sc.add_cult_station(5 * TILE + 16, 3 * TILE + 16, pose="chant",
                        face=(0, -1), dwell=(3.0, 6.0))
    sc.add_cult_station(7 * TILE + 16, 3 * TILE + 16, pose="chant",
                        face=(0, -1), dwell=(3.0, 6.0))
    sc.add_cult_station(5 * TILE + 16, 7 * TILE + 16, pose="chant",
                        face=(0, 1), dwell=(3.0, 6.0))
    sc.add_cult_station(7 * TILE + 16, 7 * TILE + 16, pose="chant",
                        face=(0, 1), dwell=(3.0, 6.0))

    def _vats_on_enter(game, scene):
        # First entry: the dig hit water. This is the river (NARRATIVE §2) --
        # the artery the cult followed down toward the door. Gated by the
        # evidence flag (non-canonical, so it doesn't move the King-gate).
        # The note key is works_cistern_seen (the Water Below).
        if game.save.flag("evidence_works_cistern_seen"):
            return
        _evidence(game, "works_cistern_seen", [
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
    objs[10][4] = "D"         # south -> the bunk cells (dead-end branch)
    # (the sorting tables are 3D furniture now -- added after the scene is built,
    # same footprint the cult AI routes around)
    objects = ["".join(r) for r in objs]
    sc = Scene("works_sorting", floor, objects, music="basement")
    sc.add_exit("F", "works_cistern", "from_below")
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
    # (NARRATIVE §2/4: shed lives + the fold's lost, not murder victims).
    # Closed cases
    # (chests, never opened by the player -- interactive=False so they
    # don't show a dead [E] prompt).
    for tx, ty in [(5, 7), (12, 9)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE - 4,
                                     "chest", open=False, interactive=False))
    sc.add_decoration(Decoration(9 * TILE + 16, 7 * TILE - 4, "chest",
                                 open=False, interactive=False))
    sc.add_decoration(Decoration(10 * TILE + 16, 9 * TILE + 16, "phantom_mark"))
    # A "wrong" mount among the catalogued lives the claimed shed --
    # somebody's trophy buck, carried down with the rest of a life and
    # hung where its owner left off (the one mount underground that
    # SURVIVES provenance). Cobwebs grime the high corners.
    sc.add_decoration(Decoration(8 * TILE + 16, 3 * TILE + 18,
                                 "wrong_taxidermy", wall="N", seed=17))
    sc.add_decoration(Decoration(1 * TILE + 6, 4 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 26, 4 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # Crates of catalogued effects stacked up in the north stem.
    sc.add_furniture("crate", [(11, 2)])
    sc.add_furniture("crate", [(12, 2)])
    # The sorting tables themselves -- 3D worktops (were flat tiles), two rows
    # across the hall floor, the same footprint the cult AI routes around.
    for tx in (3, 6, 9, 12):
        sc.add_furniture("table", [(tx, 5)], w=30, h=20)
        sc.add_furniture("table", [(tx, 8)], w=30, h=20)
    # The shed lives sorted into piles on the floor between the tables -- a
    # folded coat, a shoe, a hat, a child's toy in each (NARRATIVE §2/4).
    for (ex, ey, es) in ((4, 6, 1), (7, 7, 2), (10, 6, 3),
                         (3, 7, 4), (12, 7, 5), (8, 9, 6)):
        sc.add_decoration(Decoration(ex * TILE + 16, ey * TILE + 16,
                                     "effects_pile", seed=es))
    # (The missing-flyer + polaroid wall were cut, 2026-07: a wall of "the
    # vanished" read as a killer cult tracking victims. The shed lives in
    # the effects piles carry the room; nobody down here was hunted.)
    # The warehouse work (2026-07 art pass): the barrow that moved the
    # cases, parked between the table rows, and inventory tallies
    # scratched on the wall over the sorting.
    sc.add_decoration(Decoration(7 * TILE + 16, 4 * TILE + 16,
                                 "wheelbarrow"))
    sc.add_decoration(Decoration(4 * TILE + 16, 3 * TILE + 20,
                                 "tally_marks", wall="N", seed=8))
    # more grime: mud worked across the floor, motes in the dead air.
    sc.add_decoration(Decoration(7 * TILE + 16, 9 * TILE + 16, "mud_footprint"))
    for mx, my in ((5, 4), (10, 7), (13, 5)):
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))
    sc._table_pos = (6 * TILE + 16, 5 * TILE + 16)
    # The hardest crossing gets two enclosed hides among the cover lanes
    # (DESIGN.md §12): under a sorting table in each row. Both sit on
    # the patrol floor itself -- reachable mid-route, sweepable.
    sc.hide_spots = [
        (6 * TILE + 16, 6 * TILE + 8, "under"),    # under a north-row table
        (9 * TILE + 16, 9 * TILE + 8, "under"),    # under a south-row table
    ]
    # Two cultists sorting/patrolling -- the hardest crossing.
    sc.add_enemy(_cultist(4 * TILE + 16, 6 * TILE + 16, speed=0.9))
    sc.add_enemy(_cultist(11 * TILE + 16, 6 * TILE + 16, speed=0.9))
    _ambient(sc, "whisper", 0.13, 7.0, 12.0)
    # Glass litter between the sorting rows -- a jar knocked off a
    # table long ago, never swept. The crossing's floor bites back.
    sc.add_noise_trap(8 * TILE + 16, 6 * TILE + 16, "glass", seed=12)
    # The sorting work: stations along the table rows. The two
    # patrollers stand at the tables handling the shed lives, then
    # move down the row -- the room reads as a working floor, not a
    # guard post (noise and sightings still outrank the chore).
    sc.add_cult_station(3 * TILE + 16, 6 * TILE + 16,
                        face=(0, -1), dwell=(3.5, 6.5))
    sc.add_cult_station(9 * TILE + 16, 7 * TILE + 16,
                        face=(0, 1), dwell=(3.5, 6.5))
    sc.add_cult_station(12 * TILE + 16, 6 * TILE + 16,
                        face=(0, -1), dwell=(3.5, 6.5))

    def _interact(game):
        tx, ty = sc._table_pos
        if (abs(game.player.x - tx) < 40 and abs(game.player.y - ty) < 40):
            # Examining the catalogued lives the diggers shed fires the PI's
            # voice (the dig's scale -- first fear). A distinct trigger from
            # the chalk doors: different thing, different words.
            game._descent_voice("descent_dig")
    sc.on_interact_fn = _interact
    return sc


# ---- Mara's Room (key: maras_room) -- a convert's cell off the Sorting Hall ----

def build_maras_room():
    """Mara Blaine's cell, a side room off the Sorting Hall. She didn't
    rent a lodge room and vanish -- she moved IN, down here among the
    cult's works. A cot, a burnt-down candle, her cult robe on a peg, and
    folded in it the unsent letter to her father. The letter (a deep trail beat): she came,
    and she joined willingly."""
    floor, objs = _box(10, 9)
    # A cramped cell with the cot walled off in a back alcove behind an
    # interior partition + doorway -- so the robe + letter (a deep trail beat) sit
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
    sc.add_interactable(sc._cot_pos[0], sc._cot_pos[1], 46)  # [E] cue: robe + letter (a deep trail beat)
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
            return
        game.player.inventory.add("robe", 1)
        # The unsent letter is its own item so the player still carries
        # her last sane line into the Dark -- re-readable from inventory.
        game.player.inventory.add("unsent_letter", 1)
        game.audio.play("pickup_rare", 0.7)
        _evidence(game, "maras_room", [
            "Her cell. A cot, a burnt-down candle, a cult robe on a peg, "
            "worn soft. Chosen.",
            "Folded inside the robe: a letter to her father. Stamped, never "
            "mailed. It opens \"Dad.\"",
            "\"There was going to be a baby. A boy. I never told you, and "
            "then I could not find a way to tell you the rest. I almost "
            "decided different, right at the last, and then I wanted him "
            "more than I have ever wanted anything. He came still.\"",
            "\"I keep finding ways it was my fault. I know that isn't sane. "
            "I keep finding them anyway. I wanted a son the way you wanted "
            "a daughter, Dad. Somebody to wait up for.\"",
            "\"Don't come after me. I'm not lost. I've never been this "
            "close.\" It stops there. No signature.",
            "A journal page, weighted flat under the candle: \"I was the last "
            "one in. The rest had been here since the summer, and "
            "still they looked up when I came down the road like they had set "
            "a place for me. Whatever it cost them to give in, it cost me next "
            "to nothing. I was driving north before I had even finished "
            "dreaming it.\"",
            "This is a room someone moved into. Blaine hired you to bring "
            "her home. She was already home.",
            "The letter is addressed to a man you cannot reach. You are "
            "the only one who will ever read it.",
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
    objects = ["".join(r) for r in objs]
    sc = Scene("works_scriptorium", floor, objects, music="basement")
    # The three copying desks as real furniture volumes (2026-07 audit fix:
    # they were raw 't' object tiles, which no tilt set draws -- the desks
    # were invisible collision blocks, the Calling/Mara [E] cues floated
    # over bare floor, and the "under the centre desk" hide crouched under
    # nothing). School desks the commune carried down, so small.
    for dtx, dty in [(4, 2), (8, 2), (6, 5)]:   # copying desks
        sc.add_furniture("table", [(dtx, dty)], w=30, h=26)
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
    # Timber sets hold the span -- the widest room the diggers cut,
    # propped with the same spiked-lumber frames as the rest of the dig
    # (2026-07: the stone columns were swapped out; the scribes copied
    # the Sign under planks, not architecture). Walk-under at (4,6) and
    # (9,6); the upright tiles flank them.
    sc.add_furniture("shoring_frame", [(3, 6), (5, 6)],
                     seed=6, ang=0.0, span=64)
    sc.add_furniture("shoring_frame", [(8, 6), (10, 6)],
                     seed=14, ang=0.0, span=64)
    # Cobweb grime in the beveled corners of the scriptorium.
    sc.add_decoration(Decoration(2 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(11 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # The copying desks are the SCHOOL'S desks -- the commune stripped
    # the building it slept in (Vane: they filled the school; Toby's
    # lesson is still on the board) and carried the furniture down.
    # Child-size chairs still seated at two of them sell it without a
    # word (2026-07 process audit; free canon from NARRATIVE §4).
    sc.add_furniture("small_chair", [(4, 3)])
    sc.add_furniture("small_chair", [(8, 3)])
    sc._desk_pos = (4 * TILE + 16, 2 * TILE + 16)
    sc.add_interactable(sc._desk_pos[0], sc._desk_pos[1], 40)  # [E] cue: The Calling (grants cult_calling)
    # Mara's OWN copy of the Sign, at a second desk (deep evidence; she
    # laboured, willing hands, DESIGN.md §9). A room that is not her cell.
    sc._mara_desk_pos = (8 * TILE + 16, 2 * TILE + 16)
    sc.add_interactable(sc._mara_desk_pos[0], sc._mara_desk_pos[1], 40)
    # One enclosed hide (DESIGN.md §12): under the centre copying
    # desk -- echoes the safe-room "under" spots, but down here it is
    # checkable, and the scribe's lane is a step away.
    sc.hide_spots = [
        (6 * TILE + 16, 6 * TILE + 8, "under"),    # under the centre desk
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
        px, py = game.player.x, game.player.y
        # The first of the congregation's testimony fragments (The Calling),
        # bound and whole among their endless flat copies of the Sign. Pure
        # lore -- it gates nothing (the keystone is the Mask alone now). The
        # cult's voice is the item description; the PI's reaction is the note
        # below. Reading it ALSO seeds the §8 want-to-leave (descent_leave).
        dx, dy = sc._desk_pos
        if abs(px - dx) < 40 and abs(py - dy) < 40:
            if not game.save.flag("scriptorium_calling_taken"):
                game.save.set_flag("scriptorium_calling_taken", True)
                game.player.inventory.add("cult_calling", 1)
                game.audio.play("pickup_rare", 0.7)
                game.audio.play("low_pulse", 0.45)
                game._log_note("cult_calling", [
                    "Every hand different. Every one of them grateful. I keep "
                    "waiting for the page where somebody admits they were "
                    "tricked. It isn't here.",
                ])
                game.show_notice("The Calling. Their own testimony.")
                # Carrying off their confessions seeds the want-to-leave (the
                # King's pull to bear the Sign out, felt as the PI's own
                # sourceless urge, never named). The testimony itself reads
                # from the kit, not on pickup; the PI's interior pull fires
                # here.
                game._descent_voice("descent_leave")
            return
        # Mara's OWN hand at the Sign (the dig, a deep trail beat; DESIGN.md §9). Proof
        # she was one of the willing, not a captive -- the same hand as the
        # journal and the letter, working the cult's compulsion. Files
        # silently; the leaf itself reads from the kit.
        mx, my = sc._mara_desk_pos
        if abs(px - mx) < 40 and abs(py - my) < 40:
            if game.save.flag("evidence_maras_dig"):
                return
            game.player.inventory.add("maras_scrawl", 1)
            game.audio.play("pickup_rare", 0.7)
            game.audio.play("low_pulse", 0.45)
            _evidence(game, "maras_dig", [
                "A leaf pulled from a copying desk. The Sign, inked over and "
                "over down the page.",
                "The hand is hers. The same as the journal, the same as the "
                "letter.",
                "No captive draws this.",
            ], show=False)
            game.show_notice("The Sign, in her hand.")
            return
    sc.on_interact_fn = _interact
    # The scribes drew doors as obsessively as they copied the Sign -- swarm
    # the floor + walls with chalk doors, none overlapping (the room reads as
    # a compulsion, not a workshop). The testimony desk is left clear.
    sc.scatter_chalk_doors(4, seed=44, wall_count=2)
    return sc


# ---- Room 6: the Sign Chamber (key: works_sign) ----

# THE CONFRONTATION (2026-07, NARRATIVE §4/§6). The calling-out walks
# her to you; this is the exchange it opens. She cannot be argued home:
# asked to come away, no one leaves; asked the way out, there is none.
# The father card is the PLAYER'S OWN ASK, never automatic -- it breaks
# her certainty (the slip), she sees what is actually in front of her,
# stalls, and turns back lucid ("ends": the talk closes and the staging
# folds her back to the rank). CANON INVARIANTS: she never names what
# she dug for -- every "he" in her mouth stays undivided between her son
# and her god (the letter in her cell holds the noun; her mouth never
# does) -- and full lucidity changes nothing. No exchange is a rescue.
MARA_CONVO = {
    "id":    "mara_confront",
    "name":  "Mara",
    "voice": "blip_mid",
    "pi_voice": "blip_soft",
    "prompt": "She stands out of the rank, waiting.",
    "leave":  "Say nothing.",
    "greet": {
        "flag": "mara_confront_greeted",
        "beats": [
            ("npc", "My father sent you. Of course he did. He never could "
                    "let a thing stay lost."),
            ("npc", "Tell him what I told him at the start. I'm not lost. "
                    "I've never been this close."),
            ("npc", "[c=dim]I was not taken. I was answered, and I went to it gladly.[/c]"),
        ],
    },
    "exchanges": [
        {
            "key": "leave",
            "label": "Come with me.",
            "q": "Come with me, Mara. Right now. I'll get you out.",
            "once": True,
            "beats": [
                ("npc", "Out."),
                ("npc", "Nobody leaves, mister. Nobody has left since the "
                        "winter. You have walked the roads by now. You know "
                        "it better than the ones who quit trying."),
                ("npc", "And why would I go. He is right there. A few feet of earth, and he is right there."),
            ],
        },
        {
            "key": "way_out",
            "label": "How do I get out?",
            "q": "Then tell me how I get out. There has to be a way out.",
            "once": True,
            "beats": [
                ("npc", "There isn't. We can't. None of us can."),
                ("npc", "It is not a wall, mister. A wall has a far side. "
                        "Every way out of this town is a way further in."),
                ("npc", "Go home, while the town still lets you think you can."),
            ],
        },
        # The Walter card. The slip: her certainty breaks, the light goes
        # out, and she surfaces into an ordinary nightmare -- her hands,
        # the hunger, a man from the world. Then the stall, and the turn.
        {
            "key": "father",
            "label": "Your father is waiting.",
            "q": "Walter is waiting, Mara. Your father. He picks up the "
                 "phone every time it rings.",
            "once": True,
            "ends": True,
            "on_ask": lambda g: g.save.set_flag("mara_lucid", True),
            "beats": [
                ("npc", "My father."),
                ("npc", "[c=dim]He used to wait up. However late I came "
                        "home. He never said a word about it, but the "
                        "kitchen light would be on.[/c]"),
                ("npc", "The light."),
                ("npc", "It went out. It just went out. All this time there "
                        "was a light at the bottom of the dig, under a door, "
                        "like a house where somebody is waiting up. I could "
                        "see it with my eyes open. I am looking right at "
                        "where it was."),
                ("npc", "My hands. Look at my hands. When did I eat, mister. "
                        "What day is it, outside."),
                ("npc", "You are real. You came from outside. What am I "
                        "doing down here."),
                ("pi",  "Come home. Come with me, right now, and don't look "
                        "back."),
                ("npc", "[c=dim]Home.[/c]"),
                ("npc", "Say what is up there for me. Out loud. Say what I go back to."),
                ("npc", "Nothing. It happened, and up there it stays "
                        "happened, every morning, forever. Down here it is "
                        "not finished happening. Down here he is still "
                        "coming."),
                ("npc", "There is no out, mister. Not for me. Only deeper."),
                ("npc", "[c=dim]Tell my father I was happy here. Tell him "
                        "whatever makes him stop.[/c]"),
            ],
        },
        # The name-beat (TODO #22b). Bear-gated: only the man carrying the
        # boy's bear can say his name. Meant kindly, it is the one word she
        # cannot survive: it splits the fused "he" she has guarded for
        # months. She DETONATES (seizes the PI, the rite's stillness cracks,
        # the rank stirs), reveals the bottom of her (she has always known
        # he is not down there, and digs anyway), and REFUSES the bear
        # (2026-07 ruling). Her fate is unchanged: she turns back to the
        # dig. INVARIANT: Mara never says the name -- only the PI and the
        # tag do (guarded, flow §28c).
        {
            "key": "name",
            "label": "Say the boy's name.",
            "q": "You would have been a good mother to him, Mara. To Sam.",
            "avail": lambda g: g.player.inventory.has("bear"),
            "once": True,
            "ends": True,
            "on_ask": lambda g: g.save.set_flag("mara_named", True),
            "beats": [
                ("npc", "[c=dim]She goes still in a way the kneeling ones do "
                        "not. Something behind her face tears loose.[/c]"),
                ("npc", "Don't. You don't get to carry that name down here "
                        "and set it down in front of me."),
                ("npc", "[c=dim]Her hand closes on your coat, hard. Down the "
                        "aisle the rank stirs all at once, like one body "
                        "turning over in its sleep. The air pulls tight.[/c]"),
                ("pi",  "[c=dim](You hold out the bear. The tag toward her, the name toward her.)[/c]"),
                ("npc", "[c=dim]She looks at it the way you would look at "
                        "your own hand if it came off in the dark. She does "
                        "not take it. She cannot make her arms cross the "
                        "space.[/c]"),
                ("npc", "Put it away. Put it AWAY."),
                ("npc", "You think I don't know. You think I clawed my way "
                        "down into this dark because I believe he is here, "
                        "waiting up for me."),
                ("npc", "He is not here. He was never anywhere. I knew it "
                        "the day they laid him in my arms already gone, and "
                        "I know it now, with my hands in this dirt."),
                ("npc", "But while I am still going down toward something, he is still somewhere ahead of me. Stop digging and he is nowhere at all. That is what you are asking me to put down. Not the dig. Him."),
                ("npc", "So keep your bear. I will go back down to the only "
                        "place he is still coming."),
                ("npc", "[c=dim]She lets go of your coat, turns, and kneels "
                        "back into the rank. Her hands find the dirt. The "
                        "chamber settles, as though nothing rose.[/c]"),
            ],
        },
    ],
}


def _mara_voice(game, npc):
    """Mara's confrontation -- the #6 payoff (NARRATIVE §4). The case was
    never a rescue; the calling-out walks her to you and this opens the
    exchange (MARA_CONVO above). Mara is proof, not a counted beat; the calling-out fires the moment it opens,
    whatever the player asks. Full lucidity changes nothing: the father
    card breaks her certainty and she still turns back to the dig. After
    it, she has gone back to the kneeling. (A shot Mara forfeits #6: the
    confrontation was the evidence, and the gate still opens on the
    other five beats.)"""
    st = getattr(game, "_mara_stage", None)
    if st is not None and st.get("step", 0) < 3:
        return   # the staging is already walking her to you; let it land
    if game.save.flag("hive_seen"):
        game.dialog.show(
            ["[c=dim]She has gone back to the kneeling. She won't look at "
             "you again.[/c]"],
            speaker="", voice="blip_soft", portrait="narrator")
        return
    game.save.set_flag("hive_seen", True)
    game.audio.force_silence()
    game.audio.play("low_pulse", 0.6)
    # Mara is PROOF, not a filed beat (NARRATIVE §6, DESIGN.md §9): the
    # calling-out fires (hive_seen, the confrontation) but nothing lands in
    # the evidence log -- the trail already ended at the found person. The
    # PI's reaction keeps a home as a case NOTE, silent (no narrator
    # interrupt before the menu opens).
    game._log_note("the_congregation", [
        "Mara, kneeling with the congregation. Turned. There was never anyone to bring back.",
    ])
    from ui.conversation import open_conversation
    open_conversation(game, npc, MARA_CONVO)
    # TODO #7 -- the lure chain, felt ONCE (NARRATIVE §1/§10 fence: never
    # stated, no chain named; the PI starts the thought and declines to
    # finish it). A caption under her greeting, only for a player who
    # lived the dream (flashback_seen); for anyone else her lines stand
    # alone.
    if game.save.flag("flashback_seen"):
        game.dialog.show([
            "[c=dim](A door in your sleep, a year back. Then a grief job "
            "you had no reason to take, and an itch that drove you north "
            "with it.)[/c]",
            "[c=dim](And every road in handed you here. To her, kneeling. "
            "You start the arithmetic of that, and you put it down. Some "
            "sums you don't finish standing up.)[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")


def build_works_sign():
    # An apse: the north end rounded (beveled) around the altar, the
    # congregation floor opening out square to the south.
    floor, objs = _box(13, 11)
    _bevel(objs, 3, corners=("NW", "NE"))
    objs[5][0] = "F"          # west -> back to the scriptorium
    objs[5][12] = "E"         # east -> the Deepest Face
    objects = ["".join(r) for r in objs]
    sc = Scene("works_sign", floor, objects, music="void")
    sc.add_exit("F", "works_scriptorium", "from_below")
    sc.add_exit("E", "works_deepface", "from_above")
    sc.set_spawn("default",    6, 9)      # enter from the south, away from it
    sc.set_spawn("from_above", 1, 5)
    sc.set_spawn("from_below", 11, 5)

    # The Yellow Sign, daubed vast across the apse -- the cult's 2D
    # *brand* of Him. The thing itself, the keystone item, is the Pallid Mask on
    # the altar (a pedestal) in the apse. You lift it at the altar.
    sign_x = 6 * TILE + 16
    sc._sign_pos = (6 * TILE + 16, 2 * TILE + 20)   # the altar, not the wall
    sc.add_decoration(Decoration(6 * TILE + 16, 2 * TILE + 24, "pedestal"))
    # [E] cue at the altar -- the Mask / rite choice is the key decision
    # of the run and must read as interactable.
    sc.add_interactable(sc._sign_pos[0], sc._sign_pos[1], 50)
    # The Sign itself -- one large painted face centred in the apse,
    # flanked by two smaller ones, ringed with candles (the daubs the
    # Mask on the altar is the original of).
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
    # Hides stay sparse + risky here on purpose (DESIGN.md §12): one
    # spot under the west pew, a pew-length from the kneeling congregation.
    sc.hide_spots = [
        (4 * TILE + 16, 8 * TILE + 8, "under"),    # under the west pew
    ]
    # The congregation (2026-07 staging rework, settled with the user):
    # the kneelers at the Mask's foot are set-piece NPCs now -- no tag,
    # so no gaze, no chase, no grab (the ones IN the rite never break
    # from it; the east patrol stays the room's live threat) -- and MARA
    # KNEELS AMONG THEM, one more hood in the rank until the room says
    # her name (the calling-out below). Mara is proof; the calling-out lands here now but does not count.
    sc._kneelers = []
    for kx in (4, 5, 7, 8):
        k = NPC(kx * TILE + 16, 5 * TILE + 16, "A kneeler", "cultist",
                movement="idle", no_prompt=True)
        k.pose = "kneel"
        k.facing = (0, -1)
        sc.add_npc(k)
        sc._kneelers.append(k)
    mara = NPC(6 * TILE + 16, 5 * TILE + 16, "Mara", "cultist",
               dialogue_fn=_mara_voice, movement="idle")
    mara.pose = "kneel"
    mara.facing = (0, -1)
    sc.add_npc(mara)
    sc._mara = mara
    sc._mara_home = (mara.x, mara.y)
    sc.add_enemy(_cultist(10 * TILE + 16, 7 * TILE + 16, speed=0.9))
    # The rite-holder: one cultist bowed at the altar's foot, holding the rite,
    # oblivious to you. An NPC with NO tag -> excluded from the cultist-gaze
    # tick entirely (no visibility, no chase, no grab); pose='kneel'; non-solid
    # so it never blocks the Mask. The closing rite made present, not told
    # (NARRATIVE §2: the rite claims the collective).
    holder = NPC(6 * TILE + 16, 3 * TILE + 16, "The rite-holder", "cultist",
                 movement="idle", solid=False, no_prompt=True)
    holder.facing = (0, -1)
    holder.pose = "chant"
    sc.add_npc(holder)

    # THE CALLING-OUT (2026-07, settled with the user). First entry into
    # the nave: the kneelers rise one by one and turn to you, one of them
    # says her name at the room, and Mara stands up out of the rank and
    # comes to you for the exchange (_mara_voice; Mara is proof, not a counted beat). Then the
    # room folds back to the kneeling as if you had never come in. The
    # trigger is a walk-on band, never an E-press, so it cannot steal the
    # altar's Mask/rite choice.
    def _call_out(game):
        if game.save.flag("mara_called"):
            return
        if getattr(game, "_mara_stage", None) is not None:
            return
        game.save.set_flag("mara_called", True)
        game._mara_stage = {"t": 0.0, "step": 0, "sc": sc}
        game.audio.play("low_pulse", 0.55)
    sc.triggers.append({
        "rect": (1 * TILE, 2 * TILE, 11 * TILE, 7 * TILE),
        "fn": _call_out,
        "once": True,
        "fired": False,
    })

    def _sign_update(game, scene, dt):
        st = getattr(game, "_mara_stage", None)
        if st is None:
            return
        # A stage born on a torn-down scene instance (the player walked
        # out mid-beat) dies here: the room resets to the kneeling, and
        # Mara's E-press still carries the full exchange (no soft-lock).
        if st.get("sc") is not scene:
            game._mara_stage = None
            return
        mn = getattr(scene, "_mara", None)
        if mn is None or not getattr(mn, "alive", True):
            game._mara_stage = None
            return
        st["t"] += dt
        t = st["t"]
        p = game.player

        def _face(n, tx, ty):
            dx, dy = tx - n.x, ty - n.y
            dd = math.hypot(dx, dy) or 1.0
            n.facing = (dx / dd, dy / dd)
        # The patrol holds off while the room performs.
        for e in scene.enemies:
            if getattr(e, "kind", "") == "cultist" and e.alive:
                e._stun_t = max(getattr(e, "_stun_t", 0.0), 0.3)
                e._cult_state = "scout"
                e._suspicion = 0.0
        if st["step"] == 0:
            # The kneelers rise one by one, and turn to face you.
            for i, k in enumerate(scene._kneelers):
                if t > 0.4 + 0.3 * i and getattr(k, "pose", None) == "kneel":
                    k.pose = None
                    _face(k, p.x, p.y)
                    game.audio.play("wood_creak", 0.22)
            if t > 0.4 + 0.3 * len(scene._kneelers) + 0.6:
                st["step"] = 1
                caller = min(scene._kneelers,
                             key=lambda k: math.hypot(k.x - p.x, k.y - p.y))
                # No speaker label: just her name, said at the room.
                game.float_speech.begin(caller, ["Mara."], name="")
        elif st["step"] == 1:
            if t > 3.1:
                st["step"] = 2
                mn.pose = None
                _face(mn, p.x, p.y)
                game.audio.play("low_pulse", 0.5)
        elif st["step"] == 2:
            # She comes to you. A straight walk (the nave is open floor);
            # the exchange fires when she arrives, or wherever she stands
            # if you keep backing away from her.
            dx, dy = p.x - mn.x, p.y - mn.y
            d = math.hypot(dx, dy)
            if t > 3.8 and d > 40.0:
                step_len = min(52.0 * dt, d - 38.0)
                mn.x += dx / d * step_len
                mn.y += dy / d * step_len
                _face(mn, p.x, p.y)
            if (t > 3.8 and d <= 42.0) or t > 10.0:
                st["step"] = 3
                _face(mn, p.x, p.y)
                _mara_voice(game, mn)
        elif st["step"] == 3:
            # Her confrontation runs LIVE (floats + the ask menu; the
            # world keeps moving). The rank folds back once the talk
            # ends: the father card ("ends"), the player picking "Say
            # nothing.", or walking out of earshot.
            cv = getattr(game, "_convo", None)
            if cv is None or not cv.active:
                st["step"] = 4
        elif st["step"] == 4:
            hx, hy = scene._mara_home
            dx, dy = hx - mn.x, hy - mn.y
            d = math.hypot(dx, dy)
            if d > 3.0:
                step_len = min(48.0 * dt, d)
                mn.x += dx / d * step_len
                mn.y += dy / d * step_len
                _face(mn, hx, hy)
            else:
                mn.x, mn.y = hx, hy
                mn.pose = "kneel"
                mn.facing = (0, -1)
                for k in scene._kneelers:
                    k.pose = "kneel"
                    k.facing = (0, -1)
                # Hold the closer while the lure caption is still up (C1).
                # It is a narrator caption with no on_complete, so
                # narration.begin() would NOT preserve its unread page
                # (ui/narration.py) -- showing over it would drop it. Mara
                # has already settled home above, so returning early each
                # frame is idempotent; the stage re-enters step 4 until the
                # caption clears, then the closer shows.
                if getattr(game, "narration", None) is not None \
                        and game.narration.active:
                    return
                game._mara_stage = None
                # The one that never moved is the room's last word
                # (TODO #8; NARRATIVE §2: the self dissolved into the
                # work).
                game.dialog.show([
                    "[c=dim]The one bowed at the altar's foot never "
                    "paused. Not when they rose. Not at her name. Its "
                    "share of the rite is the whole of it now.[/c]",
                ], speaker="", voice="blip_soft", portrait="narrator")
    sc.on_update_fn = _sign_update
    _ambient(sc, "whisper", 0.16, 5.0, 9.0)

    def _take_mask(game):
        game.save.set_flag("pallid_mask_taken", True)
        game.player.inventory.add("pallid_mask", 1)
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
        # The TEMPTATION lands as the recognition finishes: with His face in
        # hand comes the certainty it is the way OUT -- the Spread off-ramp
        # (NARRATIVE §8). The recognition routes through whichever channel
        # DialogueBox.show picked (the frameless caption for narrator text,
        # the modal band otherwise), so chain off the channel that is
        # actually live -- an on_complete parked on an inactive modal never
        # fires (the 2026-07 audit found this beat dead).
        # The note (and its one-shot flag) files NOW: a scene load clears
        # the caption channel WITHOUT firing chained callbacks, so only
        # the on-screen beat may ride the chain, never the note.
        game._descent_voice("descent_mask", note_only=True)
        _tempt = lambda: game._descent_voice_beat("descent_mask")
        if game.dialog.active:
            game.dialog.on_complete = _tempt
        elif getattr(game, "narration", None) is not None \
                and game.narration.active:
            game.narration.on_complete = _tempt
        else:
            _tempt()

    def _interact(game):
        sx, sy = sc._sign_pos
        if (abs(game.player.x - sx) > 44 or abs(game.player.y - sy) > 56):
            return
        if game.save.flag("pallid_mask_taken"):
            return
        # Two instincts at the altar (NARRATIVE §8). Lifting the mask is the
        # controlled keystone-removal the chosen endings need. Tearing the
        # whole rite down here -- the obvious heroic move -- is THE TRAP:
        # the rite is the only lid on Him, and breaking it before the source
        # (the Threshold) is sealed lets His influence out uncontained. It is
        # always pre-seal here, so this is always the catastrophe.
        # PRESENTED as the altar close-up tableau (#2b): His face on the hewn
        # stone under the daubed Sign, the kneeling behind. The two instincts
        # ride on as the tableau menu -- LIFT (the keystone, the Spread/Seal
        # fork) or TEAR IT DOWN (BREAK, the trap: the rite is the only lid, so
        # breaking it before the source is sealed floods Him out uncontained;
        # always pre-seal here, so always the catastrophe -> rite_broken).
        game._open_altar_tableau(
            on_lift=lambda: _take_mask(game),
            on_break=lambda: game._play_ending("rite_broken"))

    def _sign_on_enter(game, scene):
        # C14c: once the Mask is lifted, _interact early-returns, so drop
        # the altar's [E] cue to stop a phantom prompt on backtrack. Scenes
        # rebuild each load, so this re-applies cleanly on every re-entry.
        if game.save.flag("pallid_mask_taken"):
            scene.interactables = [t for t in scene.interactables
                                   if (t[0], t[1]) != scene._sign_pos]
    sc.on_enter_fn = _sign_on_enter
    sc.on_interact_fn = _interact
    return sc


# ---- Room 7: the Deepest Face (works_deepface) ----
# The dig's end. The cult's testimony says it plain: "a few feet of
# earth left between us and the door". The mine NEVER finished -- there
# is no stair, no gate, only the dead face where the digging stopped.
# The PI opens it the miner's way: powder from the diggers' stores (the
# Sump), laid and lit at the face. The blast drops the floor and he
# FALLS into something older than the dig (depths_antechamber, the fall
# zone -- cut stone worn smooth by feet that came before the cult).

def build_works_deepface():
    # An octagonal dead-end chamber, the dig's final face in the north wall.
    floor, objs = _box(11, 9)
    _bevel(objs, 2)
    objs[4][0] = "F"          # west -> back to the sign chamber
    objects = ["".join(r) for r in objs]
    sc = Scene("works_deepface", floor, objects, music="void")
    sc.add_exit("F", "works_sign", "from_below")
    sc.set_spawn("default",    5, 5)
    sc.set_spawn("from_above", 2, 4)
    sc.set_spawn("from_below", 8, 4)

    gate_x = 5 * TILE + 16
    gate_y = 2 * TILE + 16
    sc._gate_pos = (gate_x, gate_y)
    sc.add_interactable(gate_x, gate_y, 40)   # [E] cue: the deepest face
    # Mining detritus at the face: spades down, claw-gouged stone.
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 16, "claw_marks",
                                 scale=1.5))
    sc.add_decoration(Decoration(6 * TILE + 16, 2 * TILE + 12, "claw_marks",
                                 scale=1.2))
    sc.add_decoration(Decoration(3 * TILE + 16, 2 * TILE + 6, "candle"))
    # The arc's end (2026-07 art pass): the last shifts counted on the
    # rock beside the face, spoil nobody hauled, hafts downed where the
    # digging stopped. The work just... stops, a few feet short.
    sc.add_decoration(Decoration(3 * TILE + 16, 0 * TILE + 20,
                                 "tally_marks", wall="N", seed=3))
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 20,
                                 "tally_marks", wall="N", seed=12))
    sc.add_furniture("spoil_heap", [(7, 4)], seed=8, see_over=True)
    sc.add_furniture("firewood", [(3, 5)], w=30, h=16, seed=6)
    # Cobweb grime in the beveled corners by the keystone gate.
    sc.add_decoration(Decoration(2 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = []
    _ambient(sc, "low_pulse", 0.12, 10.0, 15.0)

    def _interact(game):
        if (abs(game.player.x - gate_x) > 40
                or abs(game.player.y - gate_y) > 40):
            return
        inv = game.player.inventory
        if game.save.flag("depths_breached"):
            # The blown floor: re-descend the hole (the fall is one-way;
            # this is the mouth of it).
            game.audio.play("low_pulse", 0.6)
            game.begin_transition("depths_antechamber", "from_above")
            return
        if not inv.has("powder"):
            game.audio.play("low_pulse", 0.4)
            game.dialog.show([
                "[c=dim](The dig stops here. Dead earth, picked at and "
                "given up on. You put your ear to it, and you would "
                "swear there is a hollow behind it.)[/c]",
                "A charge would open it. A dig like this keeps powder "
                "somewhere.",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        if not inv.has("pallid_mask"):
            # The investigator's discipline: you do not blow a scene
            # before you have seen all of it. (Mechanically: the Mask
            # first -- the temptation -- then the refusal.)
            game.audio.play("low_pulse", 0.4)
            game.dialog.show([
                "[c=dim](You lay the charge out, and stop. The thing all "
                "of this kneels to is still down here somewhere, and you "
                "have not seen its face.)[/c]",
                "Finish the sweep first. Then the wall.",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        # Powder + the Mask in hand: lay the fork out once, commit on the
        # next press. This is where Seal and Spread part in practice:
        # climb out with His face and the world learns His name (SPREAD),
        # or light it and go down to the door (no way back up from the
        # fall). The Mask is NOT spent here (§7): it is spent at the
        # Threshold, or carried out.
        if not game.save.flag("blast_laid"):
            game.save.set_flag("blast_laid", True)
            game.audio.play("low_pulse", 0.5)
            game.dialog.show([
                "[c=dim](You set the charge against the last few feet of "
                "earth and run the fuse back. Your hands are steady. You "
                "note that the way you note evidence.)[/c]",
                "You have enough. The register, the names, the Preacher, "
                "the girl her father sent you for, and His face in your "
                "hands. The way up answers it. The car answers it. You "
                "could climb out and let the world learn His name.",
                "[s=slow]Or you light it, and you cut this thing off at "
                "its source.[/s]",
                "[c=dim](Your thumb finds the striker. Once it catches, there is no way back up from where this goes.)[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        # Light it. The wall goes, and the floor goes with it -- the dig
        # breaks into the OLD workings and the PI falls through, delivered
        # (depths_antechamber on_interact carries the_fall beat).
        inv.remove("powder", 1)
        game.save.set_flag("depths_breached", True)
        game.audio.force_silence()
        game.audio.play("low_pulse", 1.0)
        game.audio.play("hit", 0.9)
        game.show_notice("The charge takes the wall, and the floor goes "
                         "with it. You drop with the stone into a dark "
                         "the dig never reached.", duration=4.5)
        game.begin_transition("depths_antechamber", "from_above")
    sc.on_interact_fn = _interact

    def _on_exit(game, scene):
        # Re-arm the two-press fuse each visit: a player who steps away to
        # weigh the Spread road and returns gets the warning again before
        # the irreversible commit -- never a lone-press point-of-no-return.
        # Harmless after the blast (depths_breached wins).
        game.save.set_flag("blast_laid", False)
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
    # Flood the south pool -- the two basins and the swallow-hole stand in
    # black water (WADE_*): crossing to them is a slow, loud wade. The north
    # ledge (rows 2-4: the diggers' barrel/crate + the DRY powder store) and
    # the spawn row stay dry -- the powder is canonically "kept dry" here.
    floor = _flood(floor, objs, _rect_tiles(2, 6, 7, 7))
    objects = ["".join(r) for r in objs]
    sc = Scene("the_sump", floor, objects, music="basement")
    sc.add_exit("F", "works_cistern", "from_the_sump")
    sc.set_spawn("default",   5, 5)
    sc.set_spawn("from_vats", 5, 2)
    # Black water pooled in two stone basins, a barrel + crate of the diggers'
    # supplies on the dry ledge, cold mist rising, a candle. The water does not
    # sit -- a sink in the floor turns it slowly DOWN (the same artery as the
    # surface river-sink, deeper now).
    sc.add_furniture("cistern_basin", [(4, 6)])
    sc.add_furniture("cistern_basin", [(6, 6)])
    sc.add_decoration(Decoration(5 * TILE + 16, 7 * TILE + 16, "swallow_hole"))
    sc.add_furniture("barrel", [(7, 4)])
    sc.add_furniture("crate", [(3, 4)])
    for tx, ty in [(3, 5), (6, 6), (4, 7)]:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 6, "smoke"))
    sc.add_decoration(Decoration(5 * TILE + 16, 3 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 6, 5 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.add_decoration(Decoration(7 * TILE + 26, 5 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.hide_spots = []
    _ambient(sc, "low_pulse", 0.12, 8.0, 13.0)

    def _on_enter(game, scene):
        from .base import drop_ammo_cache
        drop_ammo_cache(game, scene, 5, 6, 4, "ammo_sump")
    sc.on_enter_fn = _on_enter

    # Optional lore: The Bargain (second testimony fragment), left among the
    # diggers' supplies on the dry ledge. Pure lore, gates nothing.
    sc._note_pos = (3 * TILE + 16, 4 * TILE + 16)
    sc.add_interactable(sc._note_pos[0], sc._note_pos[1], 40)

    # The diggers' POWDER STORE -- the charge that opens the deepest
    # face. Kept dry on the ledge by the barrel.
    sc._powder_pos = (7 * TILE + 16, 4 * TILE + 16)
    sc.add_interactable(sc._powder_pos[0], sc._powder_pos[1], 40)

    def _interact(game):
        pxp, pyp = sc._powder_pos
        if (abs(game.player.x - pxp) <= 40
                and abs(game.player.y - pyp) <= 40
                and not game.save.flag("powder_taken")):
            game.save.set_flag("powder_taken", True)
            game.player.inventory.add("powder", 1)
            game.audio.play("pickup_rare", 0.7)
            game.show_notice("Blasting powder, kept dry on the ledge. "
                             "Enough to open a few feet of dead earth.")
            return
        nx, ny = sc._note_pos
        if abs(game.player.x - nx) > 40 or abs(game.player.y - ny) > 40:
            return
        if not game.save.flag("sump_bargain_taken"):
            game.save.set_flag("sump_bargain_taken", True)
            game.player.inventory.add("cult_bargain", 1)
            game.audio.play("pickup_rare", 0.6)
            game._log_note("cult_bargain", [
                "They write about the bargain like a debt almost paid off. "
                "Not one of them can say what they put up for it, only that "
                "the last payment is close. I never took a confession this "
                "happy.",
            ])
            game.show_notice("The Bargain. Their own testimony.")
            return
    sc.on_interact_fn = _interact
    return sc


# ---- Side branch: the Bunk Cells (key: the_cells) off the Sorting Hall ----

def build_the_cells():
    """The diggers' bunk cells off the Sorting Hall -- a comb of narrow
    dug stalls the congregation slept in between shifts, a cot and a
    candle apiece (Mara's room up the hall is the same kind of cell,
    kept). Empty now: the ones who dug here are past sleeping. A dead-end
    branch: cover, dread, and the cult's whisper. (2026-07 mine retrofit:
    the old kept-overnight captivity fiction was a killer-cult relic --
    nobody was ever kept; the claimed never know, NARRATIVE §2. Scene
    key stays the_cells -- load-bearing.)"""
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
    # The diggers' leavings: bare cots in the stalls, a corn doll left on
    # a bunk, phantom marks scratched beside the pillows -- the door
    # followed them into sleep.
    sc.add_furniture("cot", [(2, 4)])           # west cell
    sc.add_furniture("cot", [(9, 6)])           # east cell
    sc.add_furniture("cot", [(2, 8)])           # west cell
    sc.add_decoration(Decoration(9 * TILE + 16, 8 * TILE + 16, "corn_doll"))
    sc.add_decoration(Decoration(9 * TILE + 28, 4 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(2 * TILE + 28, 6 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(6 * TILE + 16, 9 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(1 * TILE + 6, 9 * TILE + 26, "cobweb",
                                 ang=-math.pi / 2))
    sc.hide_spots = []
    _ambient(sc, "whisper", 0.13, 6.0, 11.0)

    return sc
