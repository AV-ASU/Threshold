"""The effigy grove -- the rite-hidden clearing at the mouth of the
cult's mine, north of Brimley above the river.

The congregation walked here openly once: the night procession Toby
followed came down the river to this ground BEFORE the closing rite.
The rite is what hid it -- since the seal its edges wear the fold's own
wrap, nothing reaches it on foot, and the school rite's pane is the only
thread in (the walk-in discovery folds were cut 2026-07, and their
orphaned clearings husk_grove / scarecrow_ring with them). The grove is
in SEAMLESS_WORLD_SCENES so the crossing carries no fade.
"""
import math
import random
from constants import TILE
from entities.decoration import Decoration
from entities.npc import NPC
from .base import Scene


# ----- #2: The Work-Clearing (no worker) ----------------------------

def build_effigy_grove():
    """A worked HOLLOW on the near bank of the river north of Brimley --
    the clearing the cult dug at, at the mouth of their mine. Reached ONLY
    through the school rite's pane (the maze walk-in fold was cut, 2026-07:
    the rite hid this place). REDESIGNED 2026-07 from a symmetric crop
    circle into a river site: the RIVER runs the full height down the east
    side (a real bending course, in at the top and out at the bottom, its
    banks auto-reeded), and the clearing is an asymmetric lobed hollow
    worked into the corn on its near bank. The diggers followed the water
    DOWN to this ground and the night procession filed along it (NARRATIVE
    §2/§5), so the DUG MOUTH faces the water: the dead fire east of centre,
    a shoring frame behind the descent, the spoil hauled in a line to the
    bank, the ore cart left at the water's edge. The congregation's
    effigy-dolls kneel in a CRESCENT facing the fire, THREE weathered
    standing stones (organic, seeded -- siblings, never copies) scattered
    through the hollow with the nailed-up faces on one -- the work without
    the worker (the closing rite claimed the town at once, NARRATIVE §4 /
    DESIGN.md §1). The corn is still the border on every dry side.

    THE WAY DOWN lives here now: a fold stands over the dead fire ('O'),
    clarifying with the evidence count (fold_charge_fn, the meter). At 3
    evidence with the Invitation, THE RITE (E at the fire, two-press)
    plays the FULL door-dream (begin_rite_dream, cutscene only); on
    completion the pane tears OPEN (the regular standing rift; one
    presentation, one family) and the CIRCLE HOLDS: the school pane
    ('M') refuses while the way down lives --
    the seal is DISCOVERED, never announced. The way home (well_bottom's pane) answers
    only His face; surfacing with the Mask sets descent_sealed (the
    SPREAD lock) and the circle lets go."""
    W, H = 26, 19
    # THE MINE-MOUTH AT THE RIVER (2026-07 makeover). The grove is a HOLLOW
    # worked into the corn on the near bank of the river the diggers followed
    # DOWN to this ground (NARRATIVE §2/§5) -- not a tidy crop circle. The
    # river runs the FULL height down the EAST side (a real course, bending,
    # in at the top and out at the bottom, so it reads as a river and never a
    # pond) and auto-draws its reeds + wet glint (emit_tilt_water_reeds),
    # matching the Brimley river. West of the water the clearing is an
    # ASYMMETRIC lobed hollow, its worked mud bank meeting the river and
    # charred at the dead fire. The corn is still the border on every dry
    # side; the river is bounded top/bottom by the map edge and east by more
    # corn, so the circle holds (the only ways out stay the two folds).
    def river_col(ty):
        return 21.0 + 1.3 * math.sin((ty - 2) * 0.42)

    def _in_river(tx, ty):
        return abs(tx - river_col(ty)) <= 1.4

    def _in_bank(tx, ty):              # the worked mud strip on the west bank
        return -3.0 <= (tx - river_col(ty)) < -1.4

    def _in_clearing(tx, ty):
        if _in_river(tx, ty):
            return False
        dx = (tx - 11.0) / 10.6
        dy = (ty - 9.0) / 8.3
        ang = math.atan2(dy, dx)
        # A lobed edge, not a clean ellipse: the hollow reads worked, organic.
        lobe = (1.0 + 0.12 * math.sin(3.0 * ang + 0.7)
                + 0.06 * math.sin(5.0 * ang - 1.1))
        return (dx * dx + dy * dy) <= lobe

    def _in_char(tx, ty):             # charred ground at the dead fire
        dx = (tx - 15.0) / 2.8
        dy = (ty - 9.0) / 2.3
        return dx * dx + dy * dy <= 1.0

    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if _in_river(tx, ty):
                row.append("~")            # river water (banks auto-reed)
            elif _in_char(tx, ty):
                row.append("x")            # charred fire ground
            elif _in_bank(tx, ty):
                row.append(";")            # worked mud bank at the water
            else:
                row.append("g")
        floor_rows.append("".join(row))
    objects_l = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if _in_river(tx, ty) or _in_bank(tx, ty) or _in_clearing(tx, ty):
                row.append(".")            # walkable: water, bank, or clearing
            else:
                row.append("C")            # standing corn -- the border
        objects_l.append(row)
    # Three ORGANIC standing stones scattered through the hollow -- solid,
    # see-over footprints ('x' object) so they block walking but never sight.
    for sx, sy in ((8, 5), (6, 9), (9, 13)):
        objects_l[sy][sx] = "x"
    # THE WAY DOWN: the dead fire, east of the hollow's centre facing the
    # river ('O', an invisible walkable marker), walked SOUTH into the
    # descent -- the dug mouth, its spoil hauled to the water they followed.
    objects_l[9][15] = "O"
    # The school door's grove-side pane ('M'), in the clearing away from the
    # water. Walked SOUTH.
    objects_l[13][13] = "M"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("effigy_grove", floor_rows, objects, music="outside")
    # Part of the continuous outside world -- transitions in and out
    # are fade-less.
    sc.wrap_x = False
    sc.wrap_y = False
    sc.add_exit("O", "well_bottom", "from_grove", direction="south")
    sc.add_exit("M", "schoolhouse", "from_grove", direction="south")
    sc.set_spawn("default", 5, 9)
    # Back up out of the well: beside the fire, carried WEST so arrival
    # never re-fires the south-walked crossing.
    sc.set_spawn("from_well_bottom", 13, 9)
    # In through the school door: one tile north of its return pane.
    sc.set_spawn("from_school", 13, 12)

    # ---- The two state-driven folds ----
    def _charge(game, ch):
        ev = game._evidence_count()
        if ch == "O":
            if game.save.flag("descent_sealed"):
                return 0.0
            if game.save.flag("rite_performed"):
                # The pane, tearing fully open over a few seconds after
                # the dream; 1.0 on later loads. (The REGULAR standing
                # rift pane: the rift family has one presentation.)
                t0 = getattr(game, "_rite_fold_t0", None)
                if t0 is None:
                    return 1.0
                import pygame as _pg
                return min(1.0, (_pg.time.get_ticks() - t0) / 2500.0)
            # Pre-rite: a thread of gold at 0 evidence, a fully formed
            # (but shut) frame at 3. The frame IS the evidence meter.
            return min(1.0, 0.15 + 0.85 * (ev / 3.0))
        if ch == "M" and (game.save.flag("rite_performed")
                          and not game.save.flag("descent_sealed")):
            # The circle holds you: while the way down lives, the school
            # pane is dead.
            return 0.0
        if ch == "M":
            if not game.save.flag("school_door_open"):
                return 0.0
            # The school door forms over a few seconds when it is first
            # drawn; on any later load it simply stands.
            t0 = getattr(game, "_school_door_t0", None)
            if t0 is None:
                return 1.0
            import pygame as _pg
            return min(1.0, (_pg.time.get_ticks() - t0) / 2500.0)
        return 1.0
    sc.fold_charge_fn = _charge

    def _gate(game, ch):
        sealed_in = (game.save.flag("rite_performed")
                     and not game.save.flag("descent_sealed"))
        if ch == "O":
            if game.save.flag("descent_sealed"):
                return False
            if game.save.flag("rite_performed"):
                return _charge(game, "O") >= 0.999
            # Shut until the rite. Once, say why in sensation.
            if not game.save.flag("grove_fold_refused"):
                game.save.set_flag("grove_fold_refused", True)
                game.audio.play("low_pulse", 0.4)
                game.show_notice("The light over the fire will not take "
                                 "your weight. Not yet.", duration=3.2)
            return False
        if ch == "M":
            if sealed_in:
                # The circle holds you (one sensation line, once).
                if not game.save.flag("grove_held_noticed"):
                    game.save.set_flag("grove_held_noticed", True)
                    game.audio.play("low_pulse", 0.5)
                    game.show_notice("The way you came does not open. "
                                     "The circle holds. There is only "
                                     "down.", duration=3.4)
                return False
            return (game.save.flag("school_door_open")
                    and _charge(game, "M") >= 0.999)
        return True
    sc.exit_gate_fn = _gate

    # ---- THE RITE (E at the dead fire) ----
    # Two-press commit (never a lone-press point of no return; the
    # point-of-no-return lesson): the first press lays the stakes out in
    # sensation, the second begins the FULL door-dream (a pure
    # cutscene). Completion tears the pane open and keys the way home to
    # His face. Re-armed on every scene exit.
    sc._rite_pos = (15 * TILE + 16, 9 * TILE + 16)
    sc.add_interactable(sc._rite_pos[0], sc._rite_pos[1], 44)

    def _grove_interact(game):
        fx, fy = sc._rite_pos
        if (abs(game.player.x - fx) > 44
                or abs(game.player.y - fy) > 44):
            return
        save = game.save
        if save.flag("descent_sealed"):
            game.show_notice("Cold ash. The fire is done with this place.")
            return
        if save.flag("rite_performed"):
            game.show_notice("The fire is open. The way down waits.")
            return
        if game._evidence_count() < 3:
            game.audio.play("low_pulse", 0.4)
            game.show_notice("The thread of gold stands in the dead "
                             "fire, not finished forming.")
            return
        if not game.player.inventory.has("rite_envelope"):
            game.audio.play("low_pulse", 0.4)
            game.show_notice("The fire is ready for something. You were "
                             "never given what it wants.")
            return
        if not save.flag("rite_laid"):
            save.set_flag("rite_laid", True)
            game.audio.play("low_pulse", 0.5)
            game.dialog.show([
                "[c=dim](You stand over the dead fire. The gold stands "
                "fully formed in it now, and the air leans toward it the "
                "way a room leans toward an open window.)[/c]",
                "[c=dim]You know what this is. You stood in front of it "
                "once, a year ago, asleep, and you did not answer.[/c]",
                "[c=dim](Press again to close your eyes.)[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
            return
        game.begin_rite_dream()
    sc.on_interact_fn = _grove_interact

    def _grove_exit(game, scene):
        # Re-arm the two-press rite each visit (the point-of-no-return lesson:
        # a player who steps away and returns gets the warning again).
        game.save.set_flag("rite_laid", False)
    sc.on_exit_fn = _grove_exit

    def _grove_update(game, scene, dt):
        # THE LOOM: a low, ominous bed that swells as evidence is found
        # -- the fold's charge made audible. A repeating low pulse,
        # louder and FASTER as the way down clarifies (ev 0: a faint
        # beat every ~5.5s; ev 3: a strong one every ~2s), panned to
        # the fire and leaning harder the closer you stand to it. Falls
        # silent once the descent seals (descent_sealed).
        if game.save.flag("descent_sealed"):
            return
        t = getattr(scene, "_loom_t", 0.0) - dt
        if t <= 0.0:
            ev = min(3, game._evidence_count())
            charge = 0.15 + 0.85 * (ev / 3.0)
            fx, fy = 15 * TILE + 16, 9 * TILE + 16
            d = math.hypot(game.player.x - fx, game.player.y - fy)
            prox = max(0.25, 1.0 - d / (12 * TILE))
            pan = game.audio.pan_for_world(fx, game.player.x)
            game.audio.play("low_pulse",
                            min(0.85, 0.16 + 0.55 * charge * prox),
                            pan=pan)
            t = 5.5 - 3.5 * charge
        scene._loom_t = t
    sc.on_update_fn = _grove_update

    def _grove_enter(game, scene):
        if game.save.flag("grove_seen"):
            return
        game.save.set_flag("grove_seen", True)
        if (game._evidence_count() < 3
                and not game.save.flag("descent_sealed")):
            game.dialog.show([
                "[c=dim](Something over the dead fire catches the light. "
                "A thread of gold, standing on end. You lose it when you "
                "look straight at it.)[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
    sc.on_enter_fn = _grove_enter

    # ---- Decorations ----
    # The dead fire on the fold tile, the Sign painted under it. (The fold's
    # gold pool relights the charred ground as the frame clarifies; the way
    # down stands IN the fire.)
    sc.add_decoration(Decoration(15 * TILE + 16, 9 * TILE + 16, "brazier"))
    sc.add_decoration(Decoration(15 * TILE + 16, 9 * TILE + 16, "yellow_sign"))
    # The congregation's EFFIGY CRESCENT: small chairs/effigies drawn up in
    # an arc on the hollow's west, all opening toward the fire and the dug
    # mouth beyond it -- a rank that knelt facing the water, not a tidy ring.
    # Each stands for a local the cult was working against.
    effigy_crescent = [
        (13, 5), (11, 6), (10, 8), (10, 10), (11, 12), (12, 13),
    ]
    for tx, ty in effigy_crescent:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "small_chair"))
    # THREE standing stones, organic and asymmetric (distinct seeds),
    # scattered through the hollow. The nailed-up faces are fixed to the
    # north-west stone, turned toward the fire.
    sc.add_decoration(Decoration(8 * TILE + 16, 5 * TILE + 16,
                                 "standing_stone", seed=11))
    sc.add_decoration(Decoration(6 * TILE + 16, 9 * TILE + 16,
                                 "standing_stone", seed=47))
    sc.add_decoration(Decoration(9 * TILE + 16, 13 * TILE + 16,
                                 "standing_stone", seed=83))
    sc.add_decoration(Decoration(8 * TILE + 16, 5 * TILE + 6,
                                 "polaroid_wall"))
    # One old stain by the fire, one mark off the crescent -- kept sparse so
    # the fire, the stones and the fold stay the focus.
    sc.add_decoration(Decoration(12 * TILE + 16, 10 * TILE + 16,
                                 "bloodstain"))
    sc.add_decoration(Decoration(10 * TILE + 16, 12 * TILE + 16,
                                 "phantom_mark"))
    # THE DUG MOUTH ON THE RIVER: the way down is the mine mouth, and the dig
    # FACED the water the diggers followed (NARRATIVE §2/§5). A timber shoring
    # frame stands behind the descent (north, the far side under the tilt)
    # framing the pane like an adit; the spoil they dug is hauled east in a
    # line toward the bank, and the cart they hauled it in is left at the
    # water's edge -- so the descent reads as worked ground running down to
    # the river, not just a fire.
    sc.add_decoration(Decoration(15 * TILE + 16, 7 * TILE + 16,
                                 "shoring_frame"))
    sc.add_decoration(Decoration(16 * TILE + 12, 8 * TILE + 16,
                                 "spoil_heap", seed=5))
    sc.add_decoration(Decoration(18 * TILE + 20, 9 * TILE + 16,
                                 "spoil_heap", seed=9))
    sc.add_decoration(Decoration(18 * TILE + 16, 11 * TILE + 16,
                                 "ore_cart", seed=3))
    # The way they came: the night procession filed along the river to this
    # fire (NARRATIVE §5, Toby's witness). Bootprints worn down the near bank
    # to the dead fire -- staggered off the grid so the trail wanders.
    for _fx, _fy in ((16, 5), (16, 7), (15, 8)):
        sc.add_decoration(Decoration(_fx * TILE + 14, _fy * TILE + 18,
                                     "mud_footprint"))
    # ---- No worker ----
    # There is no worker here. The closing rite claimed the whole town
    # at once (NARRATIVE §4 / DESIGN.md §1), so individual cursing -- and the figure
    # who'd do it -- is gone. The grove is left as the work without the
    # worker: the dead fire, the effigy ring, the nailed-up faces, all
    # tended by no one you'll ever see: a maker-less dread tableau.
    sc.hide_spots = []
    return sc
