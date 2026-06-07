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
    """THRESHOLD: the church and parsonage. A long nave with a partitioned
    back VESTRY reached through an interior doorway -- the dividing wall blocks
    line of sight, so the vestry is a real indoor blind spot (you can't see who
    or what is back there until you come around to the doorway and look in).
    Door 'm' on the south wall back to the town crossroads; door '?' on the
    north wall to the graveyard behind the church; stairs 'U' up the bell
    tower from the vestry."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWWWWWWWW?WWWWW",   # 0  ? = graveyard gate (north, over the nave)
        "W.U...W........W",   # 1  U = stairs up the bell tower (in the vestry)
        "W...C.W........W",   # 2  C = church-records terminal (placeholder)
        "W.....W........W",   # 3   vestry (cols 1-5) | nave (cols 7-14)
        "W.....W..O.....W",   # 4  O = preacher, out in the nave
        "W.....W........W",   # 5
        "WWW.WWW........W",   # 6  vestry south wall; doorway gap at col 3
        "W..............W",   # 7   the nave opens out under the vestry
        "W..............W",   # 8
        "W..............W",   # 9
        "W..............W",   # 10
        "WWWWWWWWmWWWWWWW",   # 11  m = exit south to the crossroads
    ]
    # Replace the placeholder C with '.' so it doesn't draw as anything,
    # and remember its tile -- the invisible interact NPC + the computer
    # decoration both go there. (We can't put a marker into OBJECT_DEFS
    # for "computer" without polluting the global table.)
    rows = [list(r) for r in objects]
    comp_tx, comp_ty = 4, 2
    rows[comp_ty][comp_tx] = "."
    objects = ["".join(r) for r in rows]

    sc = Scene("old_man_house", floor, objects, music="home")
    # Church now sits on the brimley west bank. The `m` exit routes
    # to the brimley; the legacy `from_village` spawn stays as a
    # save-state fallback.
    sc.add_exit("m", "brimley", "from_old_man_house")
    sc.add_exit("?", "graveyard", "from_church")
    sc.add_exit("U", "bell_tower", "from_church")
    sc.set_spawn("default", 8, 8)
    sc.set_spawn("from_brimley", 8, 10)        # one tile north of the m door
    sc.set_spawn("from_village", 8, 10)        # legacy fallback
    sc.set_spawn("from_graveyard", 10, 1)      # one tile south of the ? door
    sc.set_spawn("from_bell_tower", 2, 2)      # at the foot of the U stairs

    pos = sc.consume_marker("O")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Preacher", "preacher", voice="blip_low",
                       portrait="preacher",
                       dialogue_fn=preacher_dialogue, movement="idle",
                       tag="preacher"))

    # Sized darkwood furniture. The altar + lectern stand at the head of the
    # nave; the preacher's cot is tucked in the vestry.
    sc.add_furniture("table", [(8, 1), (9, 1)], w=54, h=36)
    sc.add_furniture("bookshelf", [(12, 1), (13, 1)], w=58, h=18, seed=4)
    sc.add_furniture("chair", [(9, 2)], w=22, h=28)
    sc.add_furniture("bed", [(1, 4), (1, 5)], w=34, h=56)

    # Computer: a beige CRT decoration plus an invisible solid NPC at the
    # same tile so try_interact() picks it up and the [E] prompt shows.
    comp_x = comp_tx * TILE + 16
    comp_y = comp_ty * TILE + 16
    sc.add_decoration(Decoration(comp_x, comp_y, "computer"))
    sc.add_npc(NPC(comp_x, comp_y, "Terminal", "_invisible",
                   voice="blip_soft", portrait="narrator",
                   dialogue_fn=_open_login_terminal,
                   movement="idle", solid=True, tag="computer"))

    sc.add_decoration(Decoration(13 * TILE + 16, 0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 22, "candle"))
    # The Preacher's parsonage in rural hunting country: a mounted buck
    # + trophy walleye on the north wall (replacing the old banner and
    # stray photo), a cobweb in the vestry corner, and a kerosene lamp on
    # the desk. The old computer is the cult's ancient church-records
    # terminal -- the LOGIN: prompt is unchanged.
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(12 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(14 * TILE + 8, 2 * TILE + 16, "clock"))
    # Phantom-mark chalk on the nave's east wall.
    sc.add_decoration(Decoration(14 * TILE + 4, 6 * TILE + 16,
                                 "phantom_mark"))
    # The Preacher's own hand: the MISSING flyer for the bright young
    # woman he watched go quiet (he warns about her from the pulpit), and
    # the polaroid wall of faces he keeps -- the ones who drifted into the
    # corn and never came back.
    sc.add_decoration(Decoration(0 * TILE + 26, 8 * TILE + 16,
                                 "missing_flyer"))
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 24,
                                 "polaroid_wall"))
    for mx, my in [(10, 7), (12, 8), (9, 9)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    sc.hide_spots = []
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
    bx, by = 9 * TILE + 16, 4 * TILE + 16
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
        "into the corn. And he said so, every Sunday, to the sheriff's "
        "face.",
        "They opened him for it, here on his own floor. He's gone to a "
        "slick the cold won't set.",
        "His collar's still white. His cross lies in the mess. You take it.",
        "[c=dim]This is what naming them costs.[/c]",
    ])


def build_fisherman_cottage():
    """The Sheriff's office. A main room where Vane watches from his desk, and
    a partitioned back RECORDS room (the case board he can't file on, the dead
    payphone, his cartridges) reached through an interior doorway -- the
    dividing wall makes the back room an indoor blind spot."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWWWWWWWWWWWWWW",   # 0
        "W........W.....W",   # 1   main office (cols 1-8) | records (cols 10-14)
        "W........W.....W",   # 2
        "W..............W",   # 3   doorway gap in the partition (col 9)
        "W....Y...W.....W",   # 4   Y = Sheriff, at his desk
        "W........W.....W",   # 5
        "W........WWWWWWW",   # 6   records room sealed off below
        "W..............W",   # 7   the office opens out under the records room
        "W..............W",   # 8
        "W..............W",   # 9
        "W..............W",   # 10
        "WWWWWyWWWWWWWWWW",   # 11  y = exit door back to the field
    ]
    sc = Scene("fisherman_cottage", floor, objects, music="home")
    # The Sheriff's office stands on the Brimley bank now; its door
    # opens back onto the field.
    sc.add_exit("y", "brimley", "from_fisherman_cottage")
    sc.set_spawn("default", 4, 8)
    sc.set_spawn("from_brimley", 5, 10)      # one tile north of the y door
    sc.set_spawn("from_village", 5, 10)      # legacy fallback
    sc.set_spawn("from_town", 5, 10)         # legacy fallback

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

    # Sized darkwood furniture: a long shelf, the desk (radio on it), a 2x2
    # bed in the corner, a chair, and a filing table in the back records room.
    sc.add_furniture("bookshelf", [(1, 1), (2, 1)], w=58, h=18, seed=6)
    sc.add_furniture("table", [(4, 5), (5, 5)], w=54, h=36)
    sc.add_furniture("chair", [(6, 4)], w=22, h=28)
    sc.add_furniture("bed", [(1, 8), (2, 8), (1, 9), (2, 9)], w=54, h=54)
    sc.add_furniture("antler_rack", [(1, 4)], w=22, h=46)
    sc.add_furniture("table", [(11, 4), (12, 4)], w=54, h=36)
    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22, "candle"))
    # Sheriff's office in hunting country: a mounted buck + trophy
    # walleye on the north wall (replacing the old banner), an antler
    # coat-rack against the west wall, and a cobweb in the records corner.
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(14 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # AM radio on the desk, a lantern by the door.
    sc.add_decoration(Decoration(4 * TILE + 16, 5 * TILE + 8, "radio"))
    sc.add_decoration(Decoration(5 * TILE + 16, 9 * TILE + 24, "lantern"))
    # Sheriff Vane's office made specific to the man, with the worst of it
    # tucked into the back room the public never sees: the case board of the
    # disappeared he can't file on (polaroid wall), the Blaine girl's MISSING
    # flyer beside it, the payphone he still lifts to a dead line. A calendar
    # of months he stopped reporting hangs by the front desk.
    sc.add_decoration(Decoration(12 * TILE + 16, 0 * TILE + 24,
                                 "polaroid_wall"))
    sc.add_decoration(Decoration(13 * TILE + 16, 0 * TILE + 24,
                                 "missing_flyer"))
    sc.add_decoration(Decoration(14 * TILE + 16, 3 * TILE + 16, "payphone"))
    sc.add_decoration(Decoration(1 * TILE + 16, 0 * TILE + 24, "calendar"))
    for mx, my in [(4, 7), (6, 8), (3, 9)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    sc.hide_spots = []

    def _fc_on_enter(game, scene):
        # The lawman's cartridges -- the best ammo source in town (one-time),
        # kept in the back records room.
        from .base import drop_ammo_cache
        drop_ammo_cache(game, scene, 13, 4, 6, "ammo_sheriff")
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
    floor = ["=" * 12 for _ in range(10)]
    objects = [
        "WWWoWWWWWWWW",   # 0  o = exit back to village (north face)
        "W.....W....W",   # 1  main room (cols 1-5) | back room (cols 7-10)
        "W.....W....W",   # 2
        "W..........W",   # 3  doorway gap in the partition (col 6)
        "W.....W....W",   # 4
        "WWWWWWW....W",   # 5  back room sealed off below
        "W..........W",   # 6
        "W..........W",   # 7
        "W..........W",   # 8
        "WWWWWWWWWWWW",   # 9  sealed south wall
    ]
    sc = Scene("haunted_house", floor, objects, music="home")
    # Abandoned farmhouse now sits deep south on the brimley
    # west bank.
    sc.add_exit("o", "brimley", "from_haunted_house")
    sc.set_spawn("default",     3, 1)
    sc.set_spawn("from_brimley", 3, 1)
    sc.set_spawn("from_village", 3, 1)         # legacy fallback
    # When the player climbs back up from the cult chamber, they come up
    # through the hatch in the back room. Spawn beside it.
    sc.set_spawn("from_chamber", 9, 4)
    # The abandoned farmhouse. Phantom marks on the walls -- thick in the
    # back room. There's a (sealed) hatch back there too.
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(5 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 7 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(8 * TILE + 16, 1 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(9 * TILE + 28, 2 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(1 * TILE + 28, 3 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(4 * TILE + 16, 7 * TILE + 24,
                                 "bloodstain"))
    for mx, my in [(3, 2), (4, 6), (8, 7)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))

    # Cult-chamber hatch: a sealed dead end, back in the rear room (the
    # blind spot). It once dropped into the old cult chamber (now removed);
    # pressing E just reads the nailed-shut notice. Drawn as a cellar_hatch.
    hatch_x = 8 * TILE + 16
    hatch_y = 3 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._farmhouse_hatch = (hatch_x, hatch_y)
    sc.add_interactable(hatch_x, hatch_y, 36)   # [E] cue for the sealed hatch

    sc.hide_spots = []

    def _farmhouse_interact(game):
        # Sealed. This hatch used to drop into the old cult chamber, which
        # passaged through to the Works -- a shortcut around the well +
        # rope. Closed (NARRATIVE §5/§9: the well is the only way down).
        if (abs(game.player.x - hatch_x) < 36
                and abs(game.player.y - hatch_y) < 36):
            game.audio.play("door_close", 0.5)
    sc.on_interact_fn = _farmhouse_interact

    return sc
