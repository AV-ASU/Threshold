"""Interiors for the four villager houses. Each is a small
one-room interior with a single NPC resident and an exit back to
the parent overworld scene."""
import math
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene
from .dialogue import (
    preacher_dialogue, sheriff_dialogue, _evidence,
)


def _open_login_terminal(game, npc):
    """Invisible-NPC dialogue handler bolted onto the computer's tile.
    Pressing E next to the computer opens the LOGIN: text-input modal.
    The modal accepts the User-D### credential. Anything else returns
    ACCESS DENIED. The credential is stored
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
    # Church now sits on the brimley west bank. The `m` exit routes
    # to the brimley; the legacy `from_village` spawn stays as a
    # save-state fallback.
    sc.add_exit("m", "brimley", "from_old_man_house")
    sc.add_exit("?", "graveyard", "from_church")
    sc.add_exit("U", "bell_tower", "from_church")
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_brimley", 4, 5)       # one tile north of m door
    sc.set_spawn("from_village", 4, 5)         # legacy fallback
    sc.set_spawn("from_graveyard", 4, 1)       # one tile south of ? door
    sc.set_spawn("from_bell_tower", 7, 1)      # one tile west of U stairs

    pos = sc.consume_marker("O")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Preacher", "preacher", voice="blip_low",
                       portrait="preacher",
                       dialogue_fn=preacher_dialogue, movement="idle",
                       tag="preacher"))

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
    # The Preacher's own hand: the MISSING flyer for the bright young
    # woman he watched go quiet (he warns about her from the pulpit), and
    # the polaroid wall of faces he keeps -- the ones who drifted into the
    # corn and never came back.
    sc.add_decoration(Decoration(0 * TILE + 26, 3 * TILE + 16,
                                 "missing_flyer"))
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 24,
                                 "polaroid_wall"))
    for mx, my in [(4, 4), (6, 3), (5, 4)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Hide spots: behind the desk, behind the shelf.
    sc.hide_spots = [
        (3 * TILE + 16, 2 * TILE + 24, "behind"),
        (7 * TILE + 16, 2 * TILE + 24, "behind"),
    ]
    sc.on_enter_fn = old_man_house_on_enter
    return sc


def old_man_house_on_enter(game, scene):
    """Once the Preacher damns himself (the 2nd conversation sets
    `preacher_doomed`), the cult silences him for naming them. The scene is
    rebuilt each load, so the builder re-adds the live Preacher every time;
    here we remove him and lay out his remains + the cross (evidence #4)."""
    if not game.save.flag("preacher_doomed"):
        return
    scene.npcs = [n for n in scene.npcs
                  if getattr(n, "tag", None) != "preacher"]
    bx, by = 5 * TILE + 16, 5 * TILE + 16
    scene.add_decoration(Decoration(bx - 6, by + 9, "bloodstain"))
    scene.add_decoration(Decoration(bx + 9, by - 6, "gore"))
    scene.add_decoration(Decoration(bx, by, "body"))
    scene.add_npc(NPC(bx, by, "The Preacher", "_invisible",
                      voice="blip_soft", portrait="narrator",
                      dialogue_fn=preacher_body_examine,
                      movement="idle", solid=True, tag="preacher_body"))


def preacher_body_examine(game, npc):
    """E on the Preacher's remains: take his cross + log evidence #4 once."""
    if game.save.flag("cross_taken"):
        game.dialog.show(["What's left of him. The flies have found it."],
                         speaker="", voice="blip_soft", portrait="narrator")
        return
    game.save.set_flag("cross_taken", True)
    game.player.inventory.add("cross", 1)
    game.audio.play("pickup_rare", 0.7)
    game.audio.play("low_pulse", 0.5)
    _evidence(game, "the_preacher", [
        "The Preacher. He watched the strangers drift into town and vanish "
        "into the corn -- and he said so, every Sunday, to the sheriff's "
        "face.",
        "They opened him for it, here on his own floor. He's gone to a "
        "slick the cold won't set.",
        "His collar's still white. His cross lies in the mess. You take it.",
        "[c=dim]This is what naming them costs.[/c]",
    ])


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
    sc.add_exit("y", "brimley", "from_fisherman_cottage")
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_brimley", 4, 5)       # arrive from Brimley
    sc.set_spawn("from_village", 4, 5)         # legacy fallback
    sc.set_spawn("from_town", 4, 5)            # legacy fallback

    pos = sc.consume_marker("Y")
    if pos:
        tx, ty = pos
        # The Sheriff sits at his desk. He doesn't patrol -- the lesser
        # cult walks the roads. He just watches the player from the
        # chair. The first read is friendly; later visits dim him.
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Sheriff", "sheriff",
                       voice="blip_gruff", portrait="sheriff",
                       dialogue_fn=sheriff_dialogue, movement="watch"))

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
    # Sheriff Vane's office made specific to the man: the case board of
    # the disappeared he can't file on (polaroid wall), the Blaine girl's
    # MISSING flyer beside it, a payphone he still lifts to a dead line,
    # and a calendar of months he stopped reporting.
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 24,
                                 "polaroid_wall"))
    sc.add_decoration(Decoration(5 * TILE + 16, 0 * TILE + 24,
                                 "missing_flyer"))
    sc.add_decoration(Decoration(8 * TILE + 16, 3 * TILE + 16, "payphone"))
    sc.add_decoration(Decoration(1 * TILE + 16, 0 * TILE + 24, "calendar"))
    for mx, my in [(4, 3), (5, 4), (3, 5)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Hide spots: behind the desk, under the table.
    sc.hide_spots = [
        (3 * TILE + 16, 2 * TILE + 24, "behind"),
        (7 * TILE + 16, 2 * TILE + 24, "under"),
    ]

    def _fc_on_enter(game, scene):
        # The lawman's cartridges -- the best ammo source in town (one-time).
        from .base import drop_ammo_cache
        drop_ammo_cache(game, scene, 8, 4, 6, "ammo_sheriff")
    sc.on_enter_fn = _fc_on_enter
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
    # Abandoned farmhouse now sits deep south on the brimley
    # west bank.
    sc.add_exit("o", "brimley", "from_haunted_house")
    sc.set_spawn("default",     3, 1)
    sc.set_spawn("from_brimley", 3, 1)
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

    # Cult-chamber hatch: a sealed dead end. It once dropped into the old
    # cult chamber (now removed); pressing E just reads the nailed-shut
    # notice. Drawn as a cellar_hatch (wood box + iron pull-ring).
    hatch_x = 4 * TILE + 16
    hatch_y = 5 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._farmhouse_hatch = (hatch_x, hatch_y)
    sc.add_interactable(hatch_x, hatch_y, 36)   # [E] cue for the sealed hatch

    sc.hide_spots = [
        (2 * TILE + 16, 4 * TILE + 24, "behind"),
        (6 * TILE + 16, 4 * TILE + 24, "behind"),
    ]

    def _farmhouse_interact(game):
        # Sealed. This hatch used to drop into the old cult chamber, which
        # passaged through to the Works -- a shortcut around the well +
        # rope. Closed (NARRATIVE §5/§9: the well is the only way down).
        if (abs(game.player.x - hatch_x) < 36
                and abs(game.player.y - hatch_y) < 36):
            game.audio.play("door_close", 0.5)
            game.show_notice("The hatch is nailed shut from below. Whatever's "
                             "down there, it isn't for you to reach this way.")
    sc.on_interact_fn = _farmhouse_interact

    return sc
