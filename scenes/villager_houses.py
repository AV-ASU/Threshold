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


def build_church():
    """THRESHOLD: the church and parsonage. A long nave lined with PEWS
    (2026-07 redecoration -- it read as a bare room without them) leading to
    an altar at the head: a plain wooden CROSS on the wall, candles on the
    altar table. A partitioned back VESTRY (the parsonage: the preacher's cot,
    a mounted buck, the bell-tower stairs) is reached through an interior
    doorway -- the dividing wall blocks line of sight, so the vestry is a real
    indoor blind spot. Door 'm' on the south wall back to the town crossroads;
    door '?' on the north wall to the graveyard behind the church; stairs 'U'
    up the bell tower from the vestry."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWWWWWWWW?WWWWW",   # 0  ? = graveyard gate (north, over the nave)
        "W.U...W........W",   # 1  U = stairs up the bell tower (in the vestry)
        "W...C.W........W",   # 2  C = legacy terminal marker (cut, blanked below)
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
    # Replace the placeholder C (a legacy terminal marker; the church
    # LOGIN terminal was cut, C5) with '.' so it renders as plain floor.
    # Nothing stands on the tile now.
    rows = [list(r) for r in objects]
    comp_tx, comp_ty = 4, 2
    rows[comp_ty][comp_tx] = "."
    objects = ["".join(r) for r in rows]

    sc = Scene("church", floor, objects, music="home")
    # Church now sits on the brimley west bank. The `m` exit routes
    # to the brimley.
    sc.add_exit("m", "brimley", "from_church")
    sc.add_exit("?", "graveyard", "from_church")
    sc.add_exit("U", "bell_tower", "from_church")
    sc.set_spawn("default", 8, 8)
    sc.set_spawn("from_brimley", 8, 10)        # one tile north of the m door
    sc.set_spawn("from_graveyard", 10, 1)      # one tile south of the ? door
    sc.set_spawn("from_bell_tower", 2, 2)      # at the foot of the U stairs

    pos = sc.consume_marker("O")
    if pos:
        tx, ty = pos
        rev = NPC(tx * TILE + 16, ty * TILE + 16,
                  "Preacher", "preacher", voice="blip_low",
                  portrait="preacher",
                  dialogue_fn=preacher_dialogue, movement="worker",
                  tag="preacher")
        # His JOB (the JOBS layer): the lectern at the head of the
        # nave (working the sermon that gets him killed), a slow walk
        # down the empty nave, a spell at the vestry cot.
        rev.stations = [
            {"x": 8 * TILE + 16, "y": 2 * TILE + 16,
             "dwell": (8.0, 14.0), "face": (0, 1)},      # the lectern
            {"x": 8 * TILE + 16, "y": 8 * TILE + 16,
             "dwell": (3.0, 6.0), "face": (0, 1)},       # the empty nave (center aisle)
            {"x": 4 * TILE + 16, "y": 4 * TILE + 16,
             "dwell": (3.0, 6.0), "face": (-1, 0)},      # the vestry cot
        ]
        sc.add_npc(rev)

    # Sized darkwood furniture. The altar + lectern stand at the head of the
    # nave; the preacher's cot is tucked in the vestry.
    sc.add_furniture("table", [(8, 1), (9, 1)], w=54, h=36)
    sc.add_furniture("bookshelf", [(12, 1), (13, 1)], w=58, h=18, seed=4)
    sc.add_furniture("chair", [(9, 2)], w=22, h=28)
    sc.add_furniture("bed", [(1, 4), (1, 5)], w=34, h=56)

    # PEWS down the nave (2026-07 redecoration -- the church read as a bare
    # room without them). Single-tile pews abut into benches: two benches per
    # row, left + right of a narrow center aisle (cols 7-8, aligned with the
    # south door and the altar). Three rows in the lower nave; the front is
    # left open (a country church with more pews than flock). The west margin
    # (cols 1-3) stays clear so the vestry doorway at (3, 6) is reachable.
    for r in (7, 8, 9):
        for c in (4, 5, 6):          # left bench
            sc.add_furniture("pew", [(c, r)])
        for c in (9, 10, 11):        # right bench
            sc.add_furniture("pew", [(c, r)])

    # The altar dressing (2026-07): a plain wooden CROSS on the wall above the
    # altar, and two candles standing ON the altar table (seated by
    # seat_tabletop_props). Austere, a poor country parish, not gilded.
    sc.add_decoration(Decoration(8 * TILE + 24, 0 * TILE + 16, "wall_cross"))
    sc.add_decoration(Decoration(8 * TILE + 6, 1 * TILE + 8, "candle"))
    sc.add_decoration(Decoration(9 * TILE + 20, 1 * TILE + 8, "candle"))
    sc.add_decoration(Decoration(13 * TILE + 16, 0 * TILE + 22, "candle"))
    # Genset-electric main light on the nave's north wall by the chancel (the
    # altar candles are the devotion, not the wiring). (2026-07 interior pass.)
    sc.add_decoration(Decoration(12 * TILE + 16, 1 * TILE + 16, "wall_lamp"))
    # The parsonage's hunting-country dressing lives in the VESTRY (the
    # preacher's living quarters), not over the altar: a mounted buck on the
    # vestry's north wall. (The cobweb + desk lamp are added below.)
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(14 * TILE + 8, 2 * TILE + 16, "clock"))
    # Phantom-mark chalk on the nave's east wall.
    sc.add_decoration(Decoration(14 * TILE + 4, 6 * TILE + 16,
                                 "phantom_mark"))
    # Parsonage dressing: a varnish-dark oil portrait of some prior
    # reverend at the head of the nave (the face long sunk into the
    # murk), and a stitched psalm sampler in the vestry, coming undone.
    sc.add_decoration(Decoration(14 * TILE + 16, 0 * TILE + 22,
                                 "oil_portrait", seed=7))
    sc.add_decoration(Decoration(3 * TILE + 16, 0 * TILE + 22, "sampler",
                                 seed=19))
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
    """Once the Preacher damns himself (the flock exchange's PRESS branch
    sets `preacher_doomed`; scenes/dialogue.py CRANE_CONVO), he leaves his
    pulpit and goes to the river after his flock, believing they can be
    talked home (2026-07 rework; the body is found on the Brimley
    riverbank, scenes/brimley.py). The scene is rebuilt each load, so the
    builder re-adds the live Preacher every time; here we remove him and
    let the emptied church point at the water."""
    if not game.save.flag("preacher_doomed"):
        return
    scene.npcs = [n for n in scene.npcs
                  if getattr(n, "tag", None) != "preacher"]
    if not game.save.flag("church_empty_seen"):
        game.save.set_flag("church_empty_seen", True)
        # Trimmed (play-notes): the atmospheric line is cut; the river-mud
        # pointer stays because it is the only in-church signal toward the
        # riverbank body (load-bearing for the preacher discovery).
        game.dialog.show([
            "[c=dim]Mud on the aisle boards, dried in a line toward the "
            "door. River mud.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")


def build_sheriff_office():
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
    sc = Scene("sheriff_office", floor, objects, music="home")
    # The Sheriff's office stands on the Brimley bank now; its door
    # opens back onto the field.
    sc.add_exit("y", "brimley", "from_sheriff_office")
    sc.set_spawn("default", 4, 8)
    sc.set_spawn("from_brimley", 5, 10)      # one tile north of the y door

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
    # Genset-electric main light on the office's north wall over the desk (the
    # lantern + candle are the backup Vane keeps oiled). (2026-07 interior pass.)
    sc.add_decoration(Decoration(7 * TILE + 16, 1 * TILE + 16, "wall_lamp"))
    # A candle on the records-room filing table (2026-07 audit fix: every
    # light lived in the main room, so the case board and the booking slip
    # sat unreadable in the dark in the real player view). Vane works his
    # files by candlelight; seat_tabletop_props stands it on the table.
    sc.add_decoration(Decoration(12 * TILE + 8, 4 * TILE + 8, "candle"))
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
    # A varnish-dark portrait of a lawman who held the office before
    # Vane, and the washstand by his cot -- he lives at his desk now.
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 22,
                                 "oil_portrait", seed=4))
    sc.add_decoration(Decoration(3 * TILE + 20, 8 * TILE + 8, "washstand"))
    for mx, my in [(4, 7), (6, 8), (3, 9)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Mara's booking slip, in the back records room's filing table (surface
    # a surface trail beat; NARRATIVE §6, DESIGN.md §9). It lives in the FILES, not
    # on Vane -- reachable whether he is alive, dead, or never spoken to
    # (world-persistent; killing him can never soft-lock the descent).
    sc._record_pos = (11 * TILE + 16, 4 * TILE + 16)
    sc.add_decoration(Decoration(11 * TILE + 16, 4 * TILE + 6, "papers",
                                 seed=41))
    sc.add_interactable(sc._record_pos[0], sc._record_pos[1], 40)

    def _office_interact(game):
        rx, ry = sc._record_pos
        if abs(game.player.x - rx) > 40 or abs(game.player.y - ry) > 40:
            return
        if game.save.flag("evidence_maras_record"):
            return
        game.player.inventory.add("detention_record", 1)
        game.audio.play("pickup_rare", 0.7)
        _evidence(game, "maras_record", [
            "A booking slip in the Sheriff's records. Blaine, Mara.",
            "Held a night for a disturbance on the main road, shouting at "
            "the sky. Released at dawn, no charge filed.",
        ], show=False)
        if hasattr(game, "show_notice"):
            game.show_notice("Her booking slip.")
    sc.on_interact_fn = _office_interact
    sc.hide_spots = []

    def _fc_on_enter(game, scene):
        # The lawman's cartridges -- the best ammo source in town (one-time),
        # kept in the back records room. EARNED, not free (DESIGN.md §2): the
        # drop waits until Vane hands over the cabinet (the trust-gated "cache"
        # exchange sets vane_gave_cache and also drops it live). Neglect him
        # and the town's one weapon cache stays locked -- the gun is never
        # required, so this soft-locks nothing.
        if game.save.flag("vane_gave_cache"):
            from .base import drop_ammo_cache
            drop_ammo_cache(game, scene, 13, 4, 6, "ammo_sheriff")
    sc.on_enter_fn = _fc_on_enter
    return sc


def build_abandoned_farmhouse():
    """A plain abandoned farmhouse interior: a candle, a couple of
    motes, otherwise bare. (The old two-stage glitch-wall trick -- a
    passable south-face tile that dropped the player into a haunted
    `haunted_house_glitch` version -- was CUT; the south face is now
    solid, and the one live beat is the nailed-shut cult-chamber hatch
    in the rear room.)"""
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
    sc = Scene("abandoned_farmhouse", floor, objects, music="home")
    # Abandoned farmhouse now sits deep south on the brimley
    # west bank.
    sc.add_exit("o", "brimley", "from_abandoned_farmhouse")
    sc.set_spawn("default",     3, 1)
    sc.set_spawn("from_brimley", 3, 1)
    # When the player climbs back up from the cult chamber, they come up
    # through the hatch in the back room. Spawn beside it.
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
    # What the family left when they went: a preserves shelf nobody came
    # back for, and a birdcage standing open in all that bare floor.
    # (Shelf at col 1, 2026-07 audit fix: it hung centred over the col-3
    # exit door -- a cupboard drawn across the only way out.)
    sc.add_decoration(Decoration(1 * TILE + 16, 0 * TILE + 22,
                                 "preserve_shelf", seed=23))
    sc.add_decoration(Decoration(4 * TILE + 16, 2 * TILE + 16, "birdcage"))
    for mx, my in [(3, 2), (4, 6), (8, 7)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))

    # Cult-chamber hatch: a sealed dead end, back in the rear room (the
    # blind spot). It once dropped into the old cult chamber (now removed);
    # pressing E plays a locked sound + a sealed-hatch notice (C14d). Drawn
    # as a cellar_hatch.
    hatch_x = 8 * TILE + 16
    hatch_y = 3 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._farmhouse_hatch = (hatch_x, hatch_y)
    sc.add_interactable(hatch_x, hatch_y, 36)   # [E] cue for the sealed hatch

    sc.hide_spots = []

    def _farmhouse_interact(game):
        # Sealed. This hatch used to drop into the old cult chamber, which
        # passaged through to the Works -- a shortcut around the descent.
        # Closed (NARRATIVE §7/§9: the grove fold is the only way down).
        if (abs(game.player.x - hatch_x) < 36
                and abs(game.player.y - hatch_y) < 36):
            game.audio.play("door_close", 0.5)
            game.show_notice("The hatch is sealed shut. It does not budge.")
    sc.on_interact_fn = _farmhouse_interact

    return sc
