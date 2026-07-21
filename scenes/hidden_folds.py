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
    §2/§5). The MINE MOUTH is an ADIT dug into the TOP (north) rock face of
    the hollow (2026-07 rework): a dark tunnel mouth cut into a rock outcrop
    (a wall mass), a timber SET over it, the haul rope hanging cut, the yard
    in front dug down to bare dirt with the ore carts on their rail and the
    heaped spoil. The congregation's empty effigy chairs stand in the hollow
    facing the adit -- the work without the worker (the closing rite claimed
    the town at once, NARRATIVE §4 / DESIGN.md §1). The corn is still the
    border on every dry side. (The old crop-circle dressing -- the dead
    fire, the standing stones, the nailed-up faces, and then the mid-hollow
    black pit -- was cut on the way to this adit, 2026-07.)

    THE WAY DOWN is the mine SHAFT itself (2026-07 rework: no rift-portal,
    no evidence re-gate -- the way here was already earned upstream, §3/§4).
    THE RITE (E at the shaft lip, two-press) plays the FULL door-dream
    (begin_rite_dream, cutscene only); the dream IS the descent -- on
    completion _grove_update carries the PI down to well_bottom. The CIRCLE
    HOLDS: the school pane ('M') refuses while the way down lives; the seal
    is DISCOVERED, never announced. The way home (well_bottom's pane) answers
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

    # THE ADIT: the mine mouth is a tunnel dug into the TOP (north) rock face
    # of the hollow -- not a pit in the grass. A dark tunnel MOUTH (@ void)
    # opens SOUTH out of a ROCK OUTCROP (a wall mass), the working yard in
    # front of it dug down to bare dirt. The way down is the door-dream rite
    # at the mouth (E), no fold.
    _adit_mouth = {(14, 2), (15, 2)}                 # the dark tunnel mouth
    _rock_face = ({(tx, 1) for tx in range(12, 18)}  # the outcrop it is cut into
                  | {(12, 2), (13, 2), (16, 2), (17, 2)})

    def _in_yard(tx, ty):                             # the dug dirt working yard
        return 3 <= ty <= 6 and 12 <= tx <= 17

    floor_rows = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if (tx, ty) in _adit_mouth:
                row.append("@")            # the tunnel mouth: black
            elif _in_river(tx, ty):
                row.append("~")            # river water (banks auto-reed)
            elif _in_bank(tx, ty):
                row.append(";")            # worked mud bank at the water
            elif _in_yard(tx, ty) and _in_clearing(tx, ty):
                row.append("d")            # the dug dirt yard before the mouth
            else:
                row.append("g")
        floor_rows.append("".join(row))
    objects_l = []
    for ty in range(H):
        row = []
        for tx in range(W):
            if (tx, ty) in _rock_face:
                row.append("W")            # the mine's rock outcrop (a wall mass)
            elif (tx, ty) in _adit_mouth:
                row.append(".")            # the mouth is walkable (no corn/rock)
            elif _in_river(tx, ty) or _in_bank(tx, ty) or _in_clearing(tx, ty):
                row.append(".")            # walkable: water, bank, or clearing
            else:
                row.append("C")            # standing corn -- the border
        objects_l.append(row)
    # THE WAY DOWN is the mine ADIT (the mouth at (14, 2) + the E-press rite),
    # not a rift-pane exit -- so there is no 'O' tile. The descent is the
    # door-dream; _grove_update carries the PI down the moment it completes.
    # The school door's grove-side pane ('M'), in the hollow. Walked SOUTH.
    objects_l[13][13] = "M"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("effigy_grove", floor_rows, objects, music="outside")
    # Part of the continuous outside world -- transitions in and out
    # are fade-less.
    sc.wrap_x = False
    sc.wrap_y = False
    sc.add_exit("M", "schoolhouse", "from_grove", direction="south")
    sc.set_spawn("default", 5, 9)
    # Back up out of the well: beside the fire, carried WEST so arrival
    # never re-fires the south-walked crossing.
    sc.set_spawn("from_well_bottom", 13, 9)
    # In through the school door: one tile north of its return pane.
    sc.set_spawn("from_school", 13, 12)

    # ---- The ONE state-driven fold: the school pane ('M') ----
    # The descent is no longer a rift-portal: it is the physical mine shaft
    # below (the two-press rite + door-dream, _grove_interact). The only fold
    # that SHOWS here is the school pane -- the way back, dead while the
    # circle holds (after the rite, before the Mask seals the descent).
    def _charge(game, ch):
        if ch != "M":
            return 1.0
        if (game.save.flag("rite_performed")
                and not game.save.flag("descent_sealed")):
            return 0.0                     # the circle holds: the pane is dead
        if not game.save.flag("school_door_open"):
            return 0.0
        # The school door forms over a few seconds when first drawn; on any
        # later load it simply stands.
        t0 = getattr(game, "_school_door_t0", None)
        if t0 is None:
            return 1.0
        import pygame as _pg
        return min(1.0, (_pg.time.get_ticks() - t0) / 2500.0)
    sc.fold_charge_fn = _charge

    def _gate(game, ch):
        if ch != "M":
            return True
        if (game.save.flag("rite_performed")
                and not game.save.flag("descent_sealed")):
            # The circle holds you (one sensation line, once).
            if not game.save.flag("grove_held_noticed"):
                game.save.set_flag("grove_held_noticed", True)
                game.audio.play("low_pulse", 0.5)
                game.show_notice("The way you came does not open. The "
                                 "circle holds. There is only down.",
                                 duration=3.4)
            return False
        return (game.save.flag("school_door_open")
                and _charge(game, "M") >= 0.999)
    sc.exit_gate_fn = _gate

    # ---- THE DESCENT (E at the shaft mouth) ----
    # The mine mouth is physical, but the rope is CUT (NARRATIVE §7): you
    # cannot climb down. Two-press commit (never a lone-press point of no
    # return): the first press lays the stakes at the lip, the second begins
    # the FULL door-dream (a pure cutscene). The dream IS the descent -- on
    # completion the shaft has you and _grove_update carries you down. NO
    # evidence gate: the way here was already earned upstream (Sable's
    # Invitation at 3 evidence, then the school rite). Re-armed on every exit.
    sc._rite_pos = (14 * TILE + 16, 3 * TILE + 16)
    sc.add_interactable(sc._rite_pos[0], sc._rite_pos[1], 44)

    def _grove_interact(game):
        fx, fy = sc._rite_pos
        if (abs(game.player.x - fx) > 44
                or abs(game.player.y - fy) > 44):
            return
        save = game.save
        if save.flag("descent_sealed"):
            game.show_notice("Cold air climbs out of the mine. It is done "
                             "with this place.")
            return
        if not save.flag("rite_laid"):
            save.set_flag("rite_laid", True)
            game.audio.play("low_pulse", 0.5)
            game.dialog.show([
                "[c=dim](You stand at the mouth of the mine. A few feet in, "
                "the floor drops away into a shaft, and the cut rope hangs "
                "into it, frayed, a body's length, then nothing.)[/c]",
                "[c=dim]You have stood here before. A year ago, asleep, at "
                "a door you never reached.[/c]",
                "[c=dim](Press again to go down.)[/c]",
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
        # THE DESCENT: once the rite-dream has run, the shaft HAS you --
        # carry the PI down to the works (the dream IS the descent). Fires
        # the frame the dream ends; you cannot linger at the lip. You only
        # return to the grove holding the Mask, and coming up seals the
        # descent, so this never re-fires.
        if (game.save.flag("rite_performed")
                and not game.save.flag("descent_sealed")):
            game.load_scene_now("well_bottom", "from_grove")
            return
        if game.save.flag("descent_sealed"):
            return
        # THE LOOM: a low bed at the shaft mouth -- the dark under the mine
        # breathing, panned to the shaft and leaning in as you near it.
        t = getattr(scene, "_loom_t", 0.0) - dt
        if t <= 0.0:
            fx, fy = 14 * TILE + 16, 3 * TILE + 16
            d = math.hypot(game.player.x - fx, game.player.y - fy)
            prox = max(0.25, 1.0 - d / (12 * TILE))
            pan = game.audio.pan_for_world(fx, game.player.x)
            game.audio.play("low_pulse", min(0.7, 0.18 + 0.4 * prox),
                            pan=pan)
            t = 3.2
        scene._loom_t = t
    sc.on_update_fn = _grove_update

    def _grove_enter(game, scene):
        # No first-sight rift beat now: the mine mouth is a physical place,
        # not a clarifying portal. (grove_seen kept for any downstream read.)
        game.save.set_flag("grove_seen", True)
    sc.on_enter_fn = _grove_enter

    # ---- Decorations ----
    # THE ADIT MOUTH (the way down): a timber SET stands over the tunnel
    # mouth -- uprights flanking the walking lane, a header beam passed under
    # (the mine's own grammar, from the Timber Racks). The haul rope hangs
    # from the header into the dark, CUT (NARRATIVE §7). The Sign is daubed
    # at the threshold. You go down by the rite (the door-dream), never a
    # climb; E at the mouth is the descent.
    sc.add_furniture("shoring_frame", [(13, 3), (16, 3)],
                     seed=5, ang=0.0, span=96)
    sc.add_decoration(Decoration(14 * TILE + 22, 2 * TILE + 26, "rope"))
    sc.add_decoration(Decoration(15 * TILE + 16, 3 * TILE + 10,
                                 "yellow_sign"))
    # THE HAUL HEAD: a working mine mouth. The rail the ore carts ran on
    # leads from the mouth out into the yard -- one cart still on the line,
    # one tipped off it; the dug spoil is heaped where they threw it, hauled
    # out while the rope still held. The yard ground is dug down to dirt.
    for _rx, _ry in ((14, 4), (14, 5), (15, 6)):
        sc.add_decoration(Decoration(_rx * TILE + 16, _ry * TILE + 16,
                                     "mine_rail"))
    sc.add_decoration(Decoration(14 * TILE + 16, 5 * TILE + 8,
                                 "ore_cart", seed=3))
    sc.add_decoration(Decoration(16 * TILE + 20, 6 * TILE + 16,
                                 "ore_cart", seed=7))
    sc.add_decoration(Decoration(12 * TILE + 12, 4 * TILE + 16,
                                 "spoil_heap", seed=5))
    sc.add_decoration(Decoration(17 * TILE + 16, 4 * TILE + 16,
                                 "spoil_heap", seed=9))
    sc.add_decoration(Decoration(13 * TILE + 16, 6 * TILE + 16,
                                 "spoil_heap", seed=2))
    # The congregation's EFFIGY CRESCENT: empty chairs in the hollow, drawn
    # up facing the adit they knelt toward -- a rank, not a tidy ring. Each
    # stands for a local the cult worked against.
    for tx, ty in ((10, 9), (13, 10), (16, 10), (18, 9)):
        sc.add_decoration(Decoration(tx * TILE + 16, ty * TILE + 16,
                                     "small_chair"))
    # One old stain in the yard, one mark off the crescent -- kept sparse so
    # the adit and the haul gear stay the focus.
    sc.add_decoration(Decoration(13 * TILE + 16, 7 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(11 * TILE + 16, 11 * TILE + 16,
                                 "phantom_mark"))
    # The way they came: the night procession filed up to the mouth
    # (NARRATIVE §5, Toby's witness). Bootprints worn up from the hollow --
    # staggered off the grid so the trail wanders.
    for _fx, _fy in ((12, 9), (13, 8), (13, 7)):
        sc.add_decoration(Decoration(_fx * TILE + 14, _fy * TILE + 18,
                                     "mud_footprint"))
    # ---- No worker ----
    # There is no worker here. The closing rite claimed the whole town
    # at once (NARRATIVE §4 / DESIGN.md §1), so individual cursing -- and the figure
    # who'd do it -- is gone. The grove is left as the work without the
    # worker: the adit, the empty effigy chairs, the haul gear abandoned
    # mid-work, all tended by no one you'll ever see.
    sc.hide_spots = []
    return sc
