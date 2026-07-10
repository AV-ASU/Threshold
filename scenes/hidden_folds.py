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
    """A CROP CIRCLE in the corn north of Brimley, above the river --
    the clearing the cult once worked, at the mouth of their mine.
    Reached ONLY through the school rite's pane (the maze walk-in fold
    was cut, 2026-07: the rite hid this place). The
    corn itself is the border: an oval of cut ground pressed into an
    unbroken field, charred at the heart. A dead fire pit at centre,
    effigy-dolls in a ring, THREE weathered standing stones (organic,
    seeded -- siblings, never copies) with the nailed-up faces on one of
    them -- the work without the worker (the closing rite claimed the
    town at once, NARRATIVE §4 / DESIGN.md §1).

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
    # The crop circle: an OVAL clearing pressed into solid corn. Inside
    # the oval the ground is open (charred at the heart, grass out to
    # the rim); everything outside it is standing corn -- the border IS
    # the field. The clearing is CLEAN-CUT and big: the corn stays a
    # distant rim, never crowding the fire, the stones or the door
    # (the tall stalk standees lean over a tile or two at most).
    def _in_clearing(tx, ty):
        dx = (tx - 13) / 11.6
        dy = (ty - 9) / 8.0
        return dx * dx + dy * dy <= 1.0

    def _in_char(tx, ty):
        dx = (tx - 13) / 4.4
        dy = (ty - 8.5) / 3.2
        return dx * dx + dy * dy <= 1.0

    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            row.append("x" if _in_char(tx, ty) else "g")
        floor_rows.append("".join(row))
    objects_l = []
    for ty in range(H):
        row = []
        for tx in range(W):
            row.append("." if _in_clearing(tx, ty) else "C")
        objects_l.append(row)
    # Three ORGANIC standing stones around the ring -- solid, see-over
    # footprints ('x' object) so they block walking but never sight.
    for sx, sy in ((9, 5), (18, 12), (7, 12)):
        objects_l[sy][sx] = "x"
    # THE WAY DOWN: the fold tile at the dead fire ('O', a marker char:
    # invisible, walkable), walked SOUTH into --
    # a deliberate step into the pane, never crossed by the natural
    # east-west walk through the clearing.
    objects_l[8][13] = "O"
    # The school door's grove-side pane ('M'), south of the ring. Walked
    # SOUTH.
    objects_l[13][13] = "M"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("effigy_grove", floor_rows, objects, music="outside")
    # Part of the continuous outside world -- transitions in and out
    # are fade-less.
    sc.wrap_x = False
    sc.wrap_y = False
    sc.add_exit("O", "well_bottom", "from_grove", direction="south")
    sc.add_exit("M", "schoolhouse", "from_grove", direction="south")
    sc.set_spawn("default", 2, 9)
    # Back up out of the well: beside the fire, carried westward so
    # arrival never re-fires the south-walked crossing.
    sc.set_spawn("from_well_bottom", 12, 8)
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
    # Deep Stair lesson): the first press lays the stakes out in
    # sensation, the second begins the FULL door-dream (a pure
    # cutscene). Completion tears the pane open and keys the way home to
    # His face. Re-armed on every scene exit.
    sc._rite_pos = (13 * TILE + 16, 8 * TILE + 16)
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
        # Re-arm the two-press rite each visit (the Deep Stair lesson:
        # a player who steps away and returns gets the warning again).
        game.save.set_flag("rite_laid", False)
    sc.on_exit_fn = _grove_exit

    def _grove_update(game, scene, dt):
        # THE LOOM: a low, ominous bed that swells as evidence is found
        # -- the fold's charge made audible. A repeating low pulse,
        # louder and FASTER as the way down clarifies (ev 0: a faint
        # beat every ~5.5s; ev 3: a strong one every ~2s), panned to
        # the fire and leaning harder the closer you stand to it. Falls
        # silent once the Deep Stair seals the descent.
        if game.save.flag("descent_sealed"):
            return
        t = getattr(scene, "_loom_t", 0.0) - dt
        if t <= 0.0:
            ev = min(3, game._evidence_count())
            charge = 0.15 + 0.85 * (ev / 3.0)
            fx, fy = 13 * TILE + 16, 8 * TILE + 16
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
    # The dead fire pit on the fold tile itself, the Sign painted under
    # it. (The fold's gold pool relights the charred ring as the frame
    # clarifies; the way down stands IN the fire.)
    sc.add_decoration(Decoration(13 * TILE + 16, 8 * TILE + 16, "brazier"))
    sc.add_decoration(Decoration(13 * TILE + 16, 8 * TILE + 16,
                                 "yellow_sign"))
    # Effigy circle around the fire -- six small chairs/effigies on
    # the charred ring. Each represents a local the priest was working
    # against.
    effigy_ring = [
        (11, 6), (15, 6), (11, 10), (15, 10), (10, 8), (17, 8),
    ]
    for tx, ty in effigy_ring:
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "small_chair"))
    # THREE standing stones, organic and asymmetric (distinct seeds).
    # The nailed-up faces moved from the old tree-wall board onto the
    # north-west stone -- fixed to the rock, watching the fire.
    sc.add_decoration(Decoration(9 * TILE + 16, 5 * TILE + 16,
                                 "standing_stone", seed=11))
    sc.add_decoration(Decoration(18 * TILE + 16, 12 * TILE + 16,
                                 "standing_stone", seed=47))
    sc.add_decoration(Decoration(7 * TILE + 16, 12 * TILE + 16,
                                 "standing_stone", seed=83))
    sc.add_decoration(Decoration(9 * TILE + 16, 5 * TILE + 6,
                                 "polaroid_wall"))
    # One old stain on the approach, one mark off the ring -- kept sparse
    # so the fire, the stones and the fold stay the focus.
    sc.add_decoration(Decoration(8 * TILE + 16, 9 * TILE + 16,
                                 "bloodstain"))
    sc.add_decoration(Decoration(11 * TILE + 16, 12 * TILE + 16,
                                 "phantom_mark"))
    # ---- No worker ----
    # There is no worker here. The closing rite claimed the whole town
    # at once (NARRATIVE §4 / DESIGN.md §1), so individual cursing -- and the figure
    # who'd do it -- is gone. The grove is left as the work without the
    # worker: the dead fire, the effigy ring, the nailed-up faces, all
    # tended by no one you'll ever see: a maker-less dread tableau.
    sc.hide_spots = []
    return sc
