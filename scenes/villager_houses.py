"""Interiors for the four villager houses. Each is a small
one-room interior with a single NPC resident and an exit back to
the parent overworld scene."""
import math
import random
import pygame
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene
from .dialogue import (
    old_man_dialogue, fisherman_dialogue, innkeeper_dialogue, _evidence,
)


def _open_login_terminal(game, npc):
    """Invisible-NPC dialogue handler bolted onto the computer's tile.
    Pressing E next to the computer opens the LOGIN: text-input modal.
    The modal accepts the User-D### credential dropped by the bandit
    boss. Anything else returns ACCESS DENIED. The credential is stored
    lowercase ('user-d###') so the case-insensitive compare just lowers
    the input."""
    def _on_submit(s):
        # Round-9: credential compare is digit-only. The Badge in the
        # player's pocket reads as "D-234"; the saved arg is "d-234".
        # Accept anything whose digit-run matches the saved digits, so
        # "D-234", "d-234", "234", and the legacy "user-d234" form all
        # validate.
        import re
        saved = game.save.arg("user_code") or ""
        attempt = (s or "").strip()
        m = re.search(r"\d+", saved)
        saved_digits = m.group() if m else None
        m = re.search(r"\d+", attempt)
        attempt_digits = m.group() if m else None
        ok = bool(saved_digits) and saved_digits == attempt_digits
        if ok:
            if not game.save.flag("terminal_unlocked"):
                game.save.set_flag("terminal_unlocked", True)
            game.audio.play("arg_chime", 0.7)
            game.show_notice("ACCESS GRANTED.")
            # A bulletin loads in dialog on every grant so the player
            # can re-read it from the terminal at any time.
            game.dialog.show([
                "[c=dim](The terminal flickers. A bulletin loads.)[/c]",
                "[c=dim]The text is blank.[/c]",
                "[c=dim]error: Connection Terminated...[/c]",
            ], speaker="", voice="blip_soft", portrait="narrator")
        else:
            game.audio.play("door_locked", 0.7)
            game.show_notice("ACCESS DENIED.")
    def _on_cancel():
        game.audio.play("menu_close", 0.5)
    if hasattr(game, "text_input") and game.text_input is not None:
        game.audio.play("menu_open", 0.6)
        game.text_input.open(prompt="LOGIN:",
                             on_submit=_on_submit, on_cancel=_on_cancel)
    else:
        # Defensive fallback so the prompt isn't silent if the modal
        # somehow hasn't been wired in yet.
        game.show_notice("The terminal hums quietly.")


def build_old_man_house():
    """THRESHOLD: the church and parsonage. Single combined room.
    Door 'm' on the south wall back to the town crossroads. Door
    '?' on the north wall to the graveyard behind the church."""
    floor = ["=" * 10 for _ in range(8)]
    objects = [
        "WWWW?WWWWW",   # ? = graveyard gate (north)
        "W..C....UW",   # C = computer placeholder; U = stairs to bell tower
        "W..t..s..W",
        "W..c.....W",
        "W........W",
        "W.O....b.W",   # O = preacher (still old_man_dialogue)
        "W....m...W",   # m = exit south to crossroads
        "WWWWWWWWWW",
    ]
    # Replace the placeholder C with '.' so it doesn't draw as anything,
    # and remember its tile -- the invisible interact NPC + the computer
    # decoration both go there. (We can't put a marker into OBJECT_DEFS
    # for "computer" without polluting the global table.)
    rows = [list(r) for r in objects]
    comp_tx, comp_ty = 3, 1
    rows[comp_ty][comp_tx] = "."
    objects = ["".join(r) for r in rows]

    sc = Scene("old_man_house", floor, objects, music="home")
    # Church now sits on the mistlands west bank. The `m` exit routes
    # to the mistlands; the legacy `from_village` spawn stays as a
    # save-state fallback.
    sc.add_exit("m", "mistlands", "from_old_man_house")
    sc.add_exit("?", "graveyard", "from_church")
    sc.add_exit("U", "bell_tower", "from_church")
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_mistlands", 4, 5)       # one tile north of m door
    sc.set_spawn("from_village", 4, 5)         # legacy fallback
    sc.set_spawn("from_graveyard", 4, 1)       # one tile south of ? door
    sc.set_spawn("from_bell_tower", 7, 1)      # one tile west of U stairs

    pos = sc.consume_marker("O")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Old Man", "old", voice="blip_low", portrait="old",
                       dialogue_fn=old_man_dialogue, movement="idle"))

    # Sized darkwood furniture.
    sc.add_furniture("table", [(2, 2), (3, 2)], w=54, h=36)
    sc.add_furniture("bookshelf", [(5, 2), (6, 2)], w=58, h=18, seed=4)
    sc.add_furniture("chair", [(3, 3)], w=22, h=28)
    sc.add_furniture("bed", [(7, 4), (7, 5)], w=34, h=56)

    # Computer: a beige CRT decoration plus an invisible solid NPC at the
    # same tile so try_interact() picks it up and the [E] prompt shows.
    comp_x = comp_tx * TILE + 16
    comp_y = comp_ty * TILE + 16
    sc.add_decoration(Decoration(comp_x, comp_y, "computer"))
    sc.add_npc(NPC(comp_x, comp_y, "Terminal", "_invisible",
                   voice="blip_soft", portrait="narrator",
                   dialogue_fn=_open_login_terminal,
                   movement="idle", solid=True, tag="computer"))

    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(8 * TILE + 16, 5 * TILE + 24, "candle"))
    # The Preacher's parsonage in rural hunting country: a mounted buck
    # + trophy walleye on the north wall (replacing the old banner and
    # stray photo), a cobweb in the NW corner, and a kerosene lamp on
    # the desk. The old computer is the cult's ancient church-records
    # terminal -- the LOGIN: prompt is unchanged.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(8 * TILE + 8, 2 * TILE + 16, "clock"))
    # Phantom-mark chalk on the wall.
    sc.add_decoration(Decoration(8 * TILE + 4, 4 * TILE + 16,
                                 "phantom_mark"))
    for mx, my in [(4, 4), (6, 3), (5, 4)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Hide spots: behind the desk, behind the shelf.
    sc.hide_spots = [
        (3 * TILE + 16, 2 * TILE + 24, "behind"),
        (7 * TILE + 16, 2 * TILE + 24, "behind"),
    ]
    return sc


def build_fisherman_cottage():
    floor = ["=" * 10 for _ in range(8)]
    objects = [
        "WWWWWWWWWW",
        "W........W",
        "W..s..t..W",
        "W..b..c..W",
        "W........W",
        "W..Y.....W",   # Y = fisherman marker
        "W....y...W",   # y = exit door
        "WWWWWWWWWW",
    ]
    sc = Scene("fisherman_cottage", floor, objects, music="home")
    # The Sheriff's office stands on the Brimley bank now; its door
    # opens back onto the field.
    sc.add_exit("y", "mistlands", "from_fisherman_cottage")
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_mistlands", 4, 5)       # arrive from Brimley
    sc.set_spawn("from_village", 4, 5)         # legacy fallback
    sc.set_spawn("from_town", 4, 5)            # legacy fallback

    pos = sc.consume_marker("Y")
    if pos:
        tx, ty = pos
        # The Sheriff sits at his desk. He doesn't patrol -- the lesser
        # cult walks the roads. He just watches the player from the
        # chair. The first read is friendly; later visits dim him.
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Sheriff", "policeman",
                       voice="blip_gruff", portrait="guard",
                       dialogue_fn=fisherman_dialogue, movement="watch"))

    # Sized darkwood furniture: a long shelf, a desk (radio on it), a
    # 2x2 bed, a chair.
    sc.add_furniture("bookshelf", [(2, 2), (3, 2)], w=54, h=18, seed=6)
    sc.add_furniture("table", [(6, 2), (7, 2)], w=54, h=36)
    sc.add_furniture("bed", [(2, 3), (3, 3), (2, 4), (3, 4)], w=54, h=54)
    sc.add_furniture("chair", [(6, 3)], w=22, h=28)
    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
    # Sheriff's office in hunting country: a mounted buck + trophy
    # walleye on the north wall (replacing the old banner), an antler
    # coat-rack against the west wall, and a cobweb in the NE corner.
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_furniture("antler_rack", [(1, 4)], w=22, h=46)
    # AM radio on the desk, a lantern by the door.
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 16, "radio"))
    sc.add_decoration(Decoration(8 * TILE + 16, 5 * TILE + 24, "lantern"))
    for mx, my in [(4, 3), (5, 4), (3, 5)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Hide spots: behind the desk, under the table.
    sc.hide_spots = [
        (3 * TILE + 16, 2 * TILE + 24, "behind"),
        (7 * TILE + 16, 2 * TILE + 24, "under"),
    ]
    return sc


def build_haunted_house():
    """Round-10 rework: now the 'normal' face of a two-stage house.
    On first entry it looks like a plain empty interior -- a candle,
    a couple of motes, otherwise bare. The trick is the south face:
    one tile is a glitch wall (passable wood). Walking through it
    drops the player into the haunted version of the same house
    (haunted_house_glitch), which is where the phantom marks, broken
    table, bloodstains, and the path to the portal room live.

    Two seal conditions both turn the glitch wall back into a real W
    on subsequent entries:
      * haunted_glitch_sealed -- the player walked back out of the
        haunted version through its north door (point-2 of the spec)
      * symbol_portal_used    -- the player took the portal route
                                 from the haunted version
    Either way, after one trip through, the route is closed."""
    # THRESHOLD: cleaned up the void buffer + passable % glitch
    # wall the original used to drop the player into the alternate
    # haunted version. South face is now solid; row 7 was an open
    # void buffer and is now a sealed wall row so the player can't
    # walk into nothing.
    floor = ["=" * 8 for _ in range(8)]
    objects = [
        "WWWoWWWW",   # 0  o = exit back to village (north face)
        "W......W",   # 1
        "W......W",   # 2
        "W......W",   # 3
        "W......W",   # 4
        "W......W",   # 5
        "W......W",   # 6
        "WWWWWWWW",   # 7  sealed south wall
    ]
    sc = Scene("haunted_house", floor, objects, music="home")
    # Abandoned farmhouse now sits deep south on the mistlands
    # west bank.
    sc.add_exit("o", "mistlands", "from_haunted_house")
    sc.set_spawn("default",     3, 1)
    sc.set_spawn("from_mistlands", 3, 1)
    sc.set_spawn("from_village", 3, 1)         # legacy fallback
    # When the player climbs back up from the cult chamber, they
    # come up through the hatch in the south of the room, not the
    # village door at the north. Spawn one tile north of the hatch
    # so they don't auto-trigger it.
    sc.set_spawn("from_chamber", 4, 4)
    # The abandoned farmhouse. Phantom marks on the walls. There's
    # a hatch in the back that drops down to the well_passage.
    sc.add_decoration(Decoration(6 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(1 * TILE + 28, 3 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(6 * TILE + 4, 5 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(4 * TILE + 16, 3 * TILE + 24,
                                 "bloodstain"))
    for mx, my in [(2, 2), (5, 3), (3, 4)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))

    # Cult-chamber hatch: press E in the south part of the room to
    # descend. The hatch is the only way to reach symbol_portal_room
    # in THRESHOLD (the void buffer + glitch trick is gone). Drawn
    # as a cellar_hatch (wood box + iron pull-ring), NOT a chest.
    hatch_x = 4 * TILE + 16
    hatch_y = 5 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._farmhouse_hatch = (hatch_x, hatch_y)

    sc.hide_spots = [
        (2 * TILE + 16, 4 * TILE + 24, "behind"),
        (6 * TILE + 16, 4 * TILE + 24, "behind"),
    ]

    def _farmhouse_interact(game):
        if (abs(game.player.x - hatch_x) < 36
                and abs(game.player.y - hatch_y) < 36):
            game.audio.play("door_open", 0.6)
            game.show_notice("You drop into the dark.")
            game.begin_transition("symbol_portal_room", "from_farmhouse")
    sc.on_interact_fn = _farmhouse_interact

    sc.on_enter_fn = haunted_house_on_enter
    return sc


def haunted_house_on_enter(game, scene):
    """THRESHOLD: glitch wall is gone -- the cult-chamber access is
    a hatch interact. The on_enter also drops a small stash pickup in
    the NW corner once per save."""
    if not game.save.flag("batteries_haunted_taken"):
        scene.add_item(
            1 * TILE + 16, 1 * TILE + 16, "charcoal",
            on_pickup=lambda g: g.save.set_flag(
                "batteries_haunted_taken", True),
        )


def build_haunted_house_glitch():
    """Round-10: the haunted face of the house. Same 8-wide footprint
    on top, but extends an extra eight rows of @ void floor below the
    south wall. The south wall has its own glitch tile; walking
    through it drops onto the void floor, which extends invisibly
    south to a trigger that fires the symbol_portal_room transition.

    Two ways out:
      * North door (o) -> village. on_exit fires haunted_glitch_sealed,
        which turns the normal haunted_house's south wall into a real
        W on the next entry.
      * Walk south through the second glitch wall + invisible-floor
        path to the portal room. The portal room sets symbol_portal_used
        which also seals the route."""
    floor = []
    for y in range(16):
        if y < 7:
            floor.append("=" * 8)
        else:
            floor.append("@" * 8)
    objects = [
        "WWWoWWWW",   # 0  north door back to village
        "W......W",   # 1
        "W.t....W",   # 2  broken table
        "W......W",   # 3
        "W....c.W",   # 4  displaced chair
        "W......W",   # 5
        "WWW%WWWW",   # 6  inner glitch wall to the void path
        "........",   # 7
        "........",   # 8
        "........",   # 9
        "........",   # 10
        "........",   # 11
        "........",   # 12
        "........",   # 13
        "........",   # 14
        "........",   # 15  trigger zone -> symbol_portal_room
    ]
    sc = Scene("haunted_house_glitch", floor, objects, music="home")
    sc.add_exit("o", "village", "from_haunted_house")
    sc.set_spawn("default",      3, 1)
    sc.set_spawn("from_normal",  3, 1)             # entry from the normal house
    sc.set_spawn("from_village", 3, 1)             # safety fallback
    # Haunted dressing -- candles, scratch marks, bloodstains. None
    # of the void-floor rows have decorations; that path is meant to
    # read as empty / invisible.
    sc.add_decoration(Decoration(6 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 24, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(4 * TILE + 16, 1 * TILE + 18, "phantom_mark"))
    sc.add_decoration(Decoration(6 * TILE + 16, 3 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 18, "phantom_mark"))
    sc.add_decoration(Decoration(3 * TILE + 16, 5 * TILE + 24, "bloodstain"))
    sc.add_decoration(Decoration(5 * TILE + 16, 5 * TILE + 16, "bloodstain"))

    def _portal_trigger(game):
        if game.state == "transition": return
        if game.save.flag("symbol_portal_used"): return
        game.audio.play("blip_glitch", 0.55)
        game.begin_transition("symbol_portal_room", "from_haunted")

    # Trigger covers the bottom two rows of the void path so the
    # transition fires when the player has actually walked far enough
    # south to be off the visible house portion.
    sc.triggers.append({
        "rect": (0, 14 * TILE, 8 * TILE, 16 * TILE),
        "fn": _portal_trigger, "once": True, "fired": False,
    })

    sc.on_exit_fn = haunted_glitch_on_exit
    return sc


def haunted_glitch_on_exit(game, scene):
    """When the player leaves the haunted version, check the target
    of the transition. If they walked back out via the north door
    (target == 'village'), seal the route. If they took the portal
    path (target == 'symbol_portal_room'), the portal flow sets
    symbol_portal_used for us -- but we still set haunted_glitch_sealed
    here defensively so the normal house's wall is sealed regardless
    of which exit was taken."""
    target = (game.transition_target or (None, None))[0]
    if target in ("village", "symbol_portal_room"):
        game.save.set_flag("haunted_glitch_sealed", True)


def build_symbol_portal_room():
    """Underground stone room beneath the abandoned farmhouse. A
    short ladder up to the farmhouse on the west; a passage east to
    the well_passage. The room is just a place.
    """
    floor = ["x" * 12 for _ in range(10)]
    objects_l = []
    for y in range(10):
        if y == 0 or y == 9:
            objects_l.append(list("#" * 12))
        else:
            row = ["#"] + ["."] * 10 + ["#"]
            objects_l.append(row)
    # Ladder up to the farmhouse on the west wall, passage east.
    objects_l[5][0] = "U"
    objects_l[5][11] = "e"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("symbol_portal_room", floor, objects, music="void")
    sc.add_exit("U", "haunted_house", "from_chamber")
    sc.add_exit("e", "well_passage", "from_chamber")
    sc.set_spawn("default",        2, 5)
    sc.set_spawn("from_haunted",   1, 5)
    sc.set_spawn("from_farmhouse", 1, 5)
    sc.set_spawn("from_well_passage", 10, 5)

    sym_x = 7 * TILE + 16
    sym_y = 5 * TILE + 16
    sc.add_decoration(Decoration(sym_x, sym_y, "symbol"))
    # Candles around the altar.
    for cx, cy in [(5, 3), (9, 3), (5, 7), (9, 7)]:
        sc.add_decoration(Decoration(cx * TILE + 16, cy * TILE + 16,
                                     "candle"))
    # Cult robes on a hook (banner deco).
    sc.add_decoration(Decoration(2 * TILE + 16, 7 * TILE + 16,
                                 "banner", color=(110, 90, 50)))
    # Ambient bloodstains and a claw gouge on the south wall.
    sc.add_decoration(Decoration(7 * TILE + 16, 3 * TILE + 24,
                                 "bloodstain"))
    sc.add_decoration(Decoration(8 * TILE + 16, 8 * TILE + 22,
                                 "claw_marks"))
    sc.hide_spots = [
        # Behind the cult robes hung on the west wall hook.
        (2 * TILE + 16, 7 * TILE + 16, "behind"),
        # Behind the north candle row.
        (5 * TILE + 16, 3 * TILE + 16, "behind"),
    ]

    return sc


def build_locked_house():
    """Red herring: the brass_key found in bandit_cave_east opens this
    house. No NPC, no quest, no evidence file. The let-down IS the point
    -- but the room should look lived-in-then-left, not blank-canvas
    empty. Dust, scattered furniture, a faded family photo over the bed.

    Note: village uses 'z' (solid) as the locked-from-outside door;
    inside the house we use 'D' (non-solid) so the player can walk back
    out without unlocking from the inside."""
    floor = ["=" * 8 for _ in range(6)]
    objects = [
        "WWWDWWWW",   # 0  D = exit door north (passable from inside)
        "W......W",   # 1   <- spawn (col 3); kept clear so the door is approachable
        "W.tc..sW",   # 2  table + chair clustered; shelf shoved against east wall
        "W......W",   # 3
        "W.b....W",   # 4  bed against west wall, alone
        "WWWWWWWW",   # 5
    ]
    sc = Scene("locked_house", floor, objects, music="home")
    sc.add_exit("D", "village", "from_locked_house")
    sc.set_spawn("default", 3, 1)
    sc.set_spawn("from_village", 3, 1)

    # Sized darkwood furniture: a small table + chair, a shelf, a bed.
    sc.add_furniture("table", [(2, 2)], w=30, h=34)
    sc.add_furniture("chair", [(3, 2)], w=22, h=28)
    sc.add_furniture("bookshelf", [(5, 2), (6, 2)], w=54, h=18, seed=7)
    sc.add_furniture("bed", [(2, 4), (3, 4)], w=56, h=38)
    # Atmosphere: an old single candle still burning by the table, a
    # faded family-photo frame hung over the bed, and a smattering of
    # floating dust motes that catch the light.
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 3 * TILE + 16, "photo"))
    # A mounted buck left behind on the north wall (replacing the old
    # faded banner) and a cobweb in the corner -- a hunting house, lived
    # in then walked away from. The faded family photos + the clock the
    # inhabitants left running stay, so the let-down still reads as
    # having a story behind it.
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(5 * TILE + 24,  0 * TILE + 22 , "clock"))
    sc.add_decoration(Decoration(2 * TILE + 16, 4 * TILE + 6, "photo"))
    # Dust motes scattered through the interior. Deterministic positions
    # so the room reads consistently on every entry.
    for mx, my in [(3, 2), (4, 3), (5, 1), (2, 4), (6, 3), (4, 4)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))
    return sc


def build_daughter_room():
    """The daughter's bedroom -- accessed once the old_doll has been
    taken from easter_egg_room. Pre-polaroid: a small pink-banner room
    with dolls implied via decorations. Post-polaroid: same shape, but
    the bright pink has faded, the dolls' presence reads as broken,
    and bloodstains streak the floor."""
    floor = ["=" * 8 for _ in range(6)]
    objects = [
        "WWWDWWWW",   # 0
        "W......W",   # 1   <- spawn
        "W..b...W",   # 2  small bed
        "W......W",   # 3
        "W..s...W",   # 4  shelf (where her dolls live)
        "WWWWWWWW",   # 5
    ]
    sc = Scene("daughter_room", floor, objects, music="home")
    sc.add_exit("D", "house", "from_daughter_room")
    sc.set_spawn("default", 3, 1)
    sc.set_spawn("from_house", 3, 1)
    # Sized furniture (kept through on_enter's decoration reset below).
    sc.add_furniture("bed", [(3, 2), (3, 3)], w=34, h=52)
    sc.add_furniture("bookshelf", [(2, 4), (3, 4)], w=54, h=18, seed=8)
    sc.on_enter_fn = daughter_room_on_enter
    return sc


_FURNITURE_KINDS = ("bed", "bookshelf", "table", "chair", "wardrobe", "stove")


def daughter_room_on_enter(game, scene):
    # Keep the sized furniture; clear only the dressing so the
    # polaroid-state props can be rebuilt fresh.
    scene.decorations = [d for d in scene.decorations
                         if getattr(d, "kind", "") in _FURNITURE_KINDS]
    polaroid = game.save.flag("polaroid_taken")
    # One-shot dim popup the first time the player walks into the
    # polaroid-altered version.
    if polaroid and not game.save.flag("daughter_dog_line_seen"):
        game.save.set_flag("daughter_dog_line_seen", True)
        game.dialog.show([
            "[c=dim]Nothing here.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
    # The pink banner stays in both states -- its warm -> faded-grey
    # colour shift is the room's whole emotional beat, not generic
    # filler. Lodge dressing is limited to cobwebs added here (the
    # on_enter wipe above strips everything but the sized furniture).
    if polaroid:
        # Faded pink-grey banner
        scene.add_decoration(Decoration(6 * TILE + 16,  0 * TILE + 22 , "banner",
                                        color=(120, 90, 100)))
        scene.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16, "phantom_mark"))
        scene.add_decoration(Decoration(6 * TILE + 16, 3 * TILE + 16, "phantom_mark"))
        scene.add_decoration(Decoration(2 * TILE + 16, 4 * TILE + 16, "phantom_mark"))
        scene.add_decoration(Decoration(4 * TILE + 16, 3 * TILE + 24, "bloodstain"))
        scene.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 24, "bloodstain"))
        # Cobwebs in both high corners -- the room has gone to decay.
        scene.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                        ang=0.0))
        scene.add_decoration(Decoration(6 * TILE + 26, 1 * TILE + 6, "cobweb",
                                        ang=math.pi / 2))
        # Heavy dust
        for mx, my in [(2, 2), (3, 3), (5, 2), (4, 4), (6, 3), (5, 3), (3, 4)]:
            scene.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))
    else:
        # Warm pink banner
        scene.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
        scene.add_decoration(Decoration(6 * TILE + 16,  0 * TILE + 22 , "banner",
                                        color=(220, 130, 170)))
        # A single cobweb in the corner -- even the kept room is old.
        scene.add_decoration(Decoration(6 * TILE + 26, 1 * TILE + 6, "cobweb",
                                        ang=math.pi / 2))
        # Light dust
        for mx, my in [(4, 2), (5, 3)]:
            scene.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))


