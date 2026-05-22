"""Below the village well: well_bottom (ladder, fall zone) and
well_passage (tunnel hub). The interact in well_bottom consumes the
polaroid and drops the player into the depths.
"""
from constants import TILE
from entities.decoration import Decoration
from .base import Scene
from .dialogue import _evidence


def build_well_bottom():
    floor = ["x" * 10 for _ in range(8)]
    objects_l = []
    for y in range(8):
        if y == 0 or y == 7:
            objects_l.append(list("#" * 10))
        else:
            row = ["#"] + ["."] * 8 + ["#"]
            objects_l.append(row)
    objects_l[1][5] = "U"          # ladder up to the village
    objects_l[3][9] = "F"          # passage east to well_passage
    objects = ["".join(r) for r in objects_l]
    sc = Scene("well_bottom", floor, objects, music="basement")
    sc.add_exit("F", "well_passage", "from_well")
    sc.set_spawn("default", 4, 1)
    sc.set_spawn("from_well", 4, 1)
    sc.set_spawn("from_passage", 7, 3)

    ladder_x  = 5 * TILE + 16
    ladder_y  = 1 * TILE + 16
    binding_x = 5 * TILE + 16
    binding_y = 5 * TILE + 16
    sc._ladder_pos  = (ladder_x, ladder_y)
    sc._binding_pos = (binding_x, binding_y)

    sc.add_decoration(Decoration(1 * TILE + 24, 4 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 16, "bloodstain"))
    sc.hide_spots = [
        (1 * TILE + 24, 6 * TILE + 16, "behind"),
        (8 * TILE + 16, 6 * TILE + 16, "behind"),
    ]

    def _well_bottom_interact(game):
        px, py = game.player.x, game.player.y
        # Ladder -- gated on having tied the rope at the top.
        if abs(px - ladder_x) < 40 and abs(py - ladder_y) < 40:
            if not game.save.flag("well_rope_tied"):
                game.audio.play("door_locked", 0.5)
                game.show_notice("Daylight, far up. The rope isn't tied.")
                return
            game.save.set_flag("well_rope_broken", True)
            game.save.set_flag("well_rope_tied", False)
            game.audio.play("door_open", 0.6)
            game.show_notice("The rope breaks as you climb out.")
            game.begin_transition("village", "from_well")
            return
        # With the polaroid, the player can trigger the descent and
        # the floor opens. Without it, a neutral note.
        if abs(px - binding_x) < 40 and abs(py - binding_y) < 40:
            if game.player.inventory.has("polaroid"):
                _begin_binding_ritual(game)
                return
            _evidence(game, "well_descent",
                "Nothing here."
            )
            return
    sc.on_interact_fn = _well_bottom_interact
    return sc


def _begin_binding_ritual(game):
    """Player places the polaroid here; it is consumed and the floor
    opens. One-way transition to depths_antechamber. Permanent."""
    if game.save.flag("descent_complete"):
        return
    game.save.set_flag("descent_complete", True)
    inv = game.player.inventory
    if inv.has("polaroid"):
        inv.remove("polaroid", 1)
    game.audio.force_silence()
    game.audio.play("low_pulse", 0.95)
    game.dialog.show([
        "[c=dim]The stone opens under your boots.[/c]",
    ], speaker="", voice="blip_soft", portrait="narrator")
    _evidence(game, "the_binding",
        "Nothing here."
    )
    game.begin_transition("depths_antechamber", "from_above")


def build_well_passage():
    floor = ["x" * 10 for _ in range(7)]
    objects_l = []
    for y in range(7):
        if y == 0 or y == 6:
            objects_l.append(list("#" * 10))
        else:
            row = ["#"] + ["."] * 8 + ["#"]
            objects_l.append(row)
    objects_l[3][0] = "F"          # west: back to well_bottom
    objects_l[1][9] = "v"          # east: cult chamber (symbol_portal_room)
    objects_l[6][5] = "u"          # south: barn cellar hatch
    objects = ["".join(r) for r in objects_l]
    sc = Scene("well_passage", floor, objects, music="basement")
    sc.add_exit("F", "well_bottom",         "from_passage")
    sc.add_exit("v", "symbol_portal_room",  "from_well_passage")
    sc.add_exit("u", "barn",                "from_well_passage")
    sc.set_spawn("default",      1, 3)
    sc.set_spawn("from_well",    1, 3)
    sc.set_spawn("from_chamber", 8, 1)
    sc.set_spawn("from_barn",    5, 5)

    gore_x = 6 * TILE + 16
    gore_y = 3 * TILE + 16
    sc._gore_pos = (gore_x, gore_y)
    sc.add_decoration(Decoration(gore_x, gore_y, "gore"))
    sc.add_decoration(Decoration(4 * TILE + 16, 3 * TILE + 16, "bloodstain"))
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(3 * TILE + 16, 0 * TILE + 22, "claw_marks"))
    sc.hide_spots = [
        (3 * TILE + 16, 5 * TILE + 16, "behind"),
        (6 * TILE + 16, 1 * TILE + 24, "behind"),
    ]

    def _well_passage_interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - gore_x) < 40 and abs(py - gore_y) < 40:
            _evidence(game, "second_chamber",
                "Nothing here."
            )
    sc.on_interact_fn = _well_passage_interact
    return sc
