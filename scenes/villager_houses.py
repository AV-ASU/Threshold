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
        "WWWWWWWWWW?iiWWW",   # 0  ? = graveyard gate; ii = tall chancel windows
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

    # The vestry doorway (the gap at col 3 in the row-6 dividing wall) gets a
    # swinging plank leaf (#4c): a shut door blocks the sight cone, so the
    # vestry (the preacher's quarters + the bell-tower stairs) is a real
    # shut-able blind spot a pursuer's line of sight breaks on, not just an
    # open gap. Starts closed; the preacher opens his own way through on his
    # cot round, the player toggles it with E. It sits in an E-W wall run, so
    # the leaf swings north-south (the shop's stockroom/pantry doors are the
    # E-W-swinging pair, keeping the game's inner doors varied per error class 8).
    sc.add_inner_door(3, 6, "plank")

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

    # Crane's LECTERN, at the head of the nave just south of the preacher's
    # spot -- his whole seat, the centrepiece of his close-up tableau
    # (draw_crane_tableau): the open book on the slanted board, the cross on the
    # front. The walkable church had only the bare altar table (tableau-parity
    # pass). Decoration = no collision, so he stands behind it and reads over it.
    sc.add_decoration(Decoration(8 * TILE + 16, 3 * TILE + 12, "lectern"))
    # The bell rope, hanging dead at the west edge of the chancel where the
    # tower drops through the ceiling (the tableau's left-edge rope; the bell
    # has not swung in years).
    sc.add_decoration(Decoration(7 * TILE + 16, 4 * TILE + 16, "rope",
                                 seed=3, scale=1.2))
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
    # The 90% rule: bulbs on drop cords down the nave roof (a poor parish
    # wired once, decades back) + one in the vestry. The chosen dark is the
    # nave's far corners past the pew banks.
    sc.add_decoration(Decoration(3 * TILE + 16, 3 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(8 * TILE + 16, 5 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(4 * TILE + 16, 8 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(11 * TILE + 16, 8 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(8 * TILE + 0, 10 * TILE + 0, "drop_bulb",
                                 z=38))
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
    """The Sheriff's office (#4c redesign, 2026-07): FOUR rooms, not a box + a
    back room. A cross of partition walls quarters the interior into a public
    FRONT (the entry off the field), Vane's OFFICE (his desk + cot, behind a
    see-over front counter), the back RECORDS room (the case board he can't
    file on, the payphone, his ammo cabinet, Mara's booking slip), and a
    BOOKING room with the barred holding CELL. Connected by inner doors in
    varied walls: a see-over `half` counter (front<->office), `plank` leaves
    (office<->records, records<->booking), and the cell's `bars` gate."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWiiWWWWWWWWWWW",   # 0  ii = cold north windows behind Vane's desk
        "W.....W........W",   # 1  OFFICE (cols 1-5) | RECORDS (cols 7-14)
        "W.....W........W",   # 2
        "W..............W",   # 3  (6,3) office<->records doorway
        "W..Y..W........W",   # 4  Y = Sheriff Vane, at his desk
        "W.....W........W",   # 5
        "WWW.WWWWWW.WWWWW",   # 6  cross wall; (3,6) counter, (10,6) records door
        "W.....W........W",   # 7  FRONT (cols 1-5) | BOOKING (cols 7-14)
        "W.....W.....W.WW",   # 8  cell north wall; bars gate at (13,8)
        "W.....W.....W..W",   # 9  the holding cell (cols 13-14, rows 9-10)
        "W.....W.....W..W",   # 10
        "WWWWWyWWWWWWWWWW",   # 11  y = exit door back to the field
    ]
    sc = Scene("sheriff_office", floor, objects, music="home")
    # The Sheriff's office stands on the Brimley bank; its door opens back onto
    # the field.
    sc.add_exit("y", "brimley", "from_sheriff_office")
    sc.set_spawn("default", 3, 8)            # in the public front
    sc.set_spawn("from_brimley", 5, 10)      # one tile north of the y door
    # Four rooms, connected by inner doors in VARIED walls (error class 8):
    #  - the FRONT COUNTER: a see-over `half` leaf on the row-6 wall (swings
    #    N-S), so the public front and Vane's office read across it.
    #  - the RECORDS door: a `plank` leaf on the col-6 wall (swings E-W).
    #  - the BOOKING door: a `plank` leaf on the row-6 wall (swings N-S).
    #  - the CELL: a see-through `bars` gate (swings N-S) into the barred
    #    holding cell (empty -- Mara was "released at dawn"). All but the
    #    counter start shut, and a shut leaf breaks a pursuer's line of sight,
    #    so the records room and the booking cell are real indoor blind spots.
    sc.add_inner_door(6, 3, "plank")         # office  <-> records (swings E-W)
    sc.add_inner_door(3, 6, "half")          # front   <-> office  (counter, N-S)
    sc.add_inner_door(10, 6, "plank")        # records <-> booking (swings N-S)
    sc.add_inner_door(13, 8, "bars")         # booking -> holding cell (swings N-S)

    pos = sc.consume_marker("Y")
    if pos:
        tx, ty = pos
        # Vane sits at his desk behind the counter. He doesn't patrol -- the
        # cult walks the roads. He watches the player over the counter.
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Sheriff", "sheriff",
                       voice="blip_gruff", portrait="sheriff",
                       dialogue_fn=sheriff_dialogue, movement="watch"))

    # ---- OFFICE (NW): Vane's working room ----
    # His desk (radio on it), the cot + washstand tucked along the west wall
    # (he lives at his desk now), and the antler coat-rack.
    sc.add_furniture("table", [(3, 3), (4, 3)], w=54, h=36)   # Vane's desk
    sc.add_furniture("bed", [(1, 1), (1, 2)], w=34, h=56)     # his cot, W wall
    sc.add_furniture("antler_rack", [(1, 4)], w=22, h=46)
    sc.add_furniture("bookshelf", [(4, 5), (5, 5)], w=58, h=18, seed=6)  # law books
    sc.add_decoration(Decoration(3 * TILE + 16, 3 * TILE + 8, "radio"))
    sc.add_decoration(Decoration(1 * TILE + 20, 3 * TILE + 8, "washstand"))
    # Genset-electric main light + a backup candle Vane keeps oiled, and a
    # drop cord over the desk itself (the 90% rule: the lawman does not
    # work his own files in the dark).
    sc.add_decoration(Decoration(4 * TILE + 16, 1 * TILE + 16, "wall_lamp"))
    sc.add_decoration(Decoration(3 * TILE + 16, 4 * TILE + 0, "drop_bulb",
                                 z=42))
    sc.add_decoration(Decoration(5 * TILE + 16, 4 * TILE + 8, "candle"))
    # Hunting-country office: a mounted buck + the trophy walleye over the desk
    # (N wall, the pair), the calendar of months he stopped reporting (stopped
    # JAN 15), a cobweb.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(1 * TILE + 16, 0 * TILE + 24, "mounted_fish"))
    sc.add_decoration(Decoration(5 * TILE + 16, 0 * TILE + 22, "calendar"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb", ang=0.0))

    # ---- FRONT (SW): the public entry, off the field ----
    # A waiting bench (two chairs) and a side table, a former lawman's portrait
    # on the wall, a lantern by the door, and its own genset light.
    sc.add_furniture("chair", [(1, 8)], w=22, h=28)
    sc.add_furniture("chair", [(1, 9)], w=22, h=28)
    sc.add_furniture("table", [(2, 10)], w=30, h=30)
    # A former lawman's portrait on a SOLID stretch of the counter wall (col 5,
    # clear of the counter door at col 3 -- error class 7: never over a door).
    sc.add_decoration(Decoration(5 * TILE + 16, 6 * TILE + 30, "oil_portrait",
                                 seed=9))
    sc.add_decoration(Decoration(2 * TILE + 16, 7 * TILE + 16, "wall_lamp"))
    sc.add_decoration(Decoration(4 * TILE + 16, 10 * TILE + 24, "lantern"))
    sc.add_decoration(Decoration(2 * TILE + 16, 9 * TILE + 16, "drop_bulb",
                                 z=38))

    # ---- RECORDS (NE): the back file room ----
    # The case board of the disappeared Vane can't file on (polaroid wall), the
    # Blaine girl's MISSING flyer beside it, the dead payphone, a varnish-dark
    # portrait of the lawman before him, and the tall arms cabinet (his cache).
    sc.add_furniture("gun_cabinet", [(14, 1)], w=28, h=54)
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 24, "polaroid_wall"))
    sc.add_decoration(Decoration(10 * TILE + 16, 0 * TILE + 24, "missing_flyer"))
    sc.add_decoration(Decoration(12 * TILE + 16, 0 * TILE + 22, "oil_portrait",
                                 seed=4))
    sc.add_decoration(Decoration(14 * TILE + 16, 3 * TILE + 16, "payphone"))
    sc.add_decoration(Decoration(14 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    # Genset light for the file room + a drop cord over the filing table's
    # east end (the 90% rule; the payphone corner reads).
    sc.add_decoration(Decoration(9 * TILE + 16, 1 * TILE + 16, "wall_lamp"))
    sc.add_decoration(Decoration(12 * TILE + 16, 3 * TILE + 16, "drop_bulb",
                                 z=38))
    # Mara's booking slip, in the records-room filing table (a surface trail
    # beat; NARRATIVE §6, DESIGN.md §9). It lives in the FILES, not on Vane --
    # reachable whether he is alive, dead, or never spoken to (world-persistent;
    # killing him can never soft-lock the descent). A candle lights the table.
    sc.add_furniture("table", [(11, 4), (12, 4)], w=54, h=36)
    sc.add_decoration(Decoration(8 * TILE + 8, 4 * TILE + 8, "candle"))
    sc._record_pos = (11 * TILE + 16, 4 * TILE + 16)
    sc.add_decoration(Decoration(11 * TILE + 16, 4 * TILE + 6, "papers",
                                 seed=41))
    sc.add_interactable(sc._record_pos[0], sc._record_pos[1], 40)

    # ---- BOOKING (SE) + the holding CELL ----
    # A booking desk, and the barred cell (empty, a faint old stain) behind its
    # see-through gate -- the sliver of cell in Vane's tableau
    # (draw_vane_tableau). Its own genset light.
    sc.add_furniture("table", [(8, 8), (9, 8)], w=54, h=36)   # booking desk
    sc.add_furniture("chair", [(8, 9)], w=22, h=28)
    sc.add_decoration(Decoration(9 * TILE + 16, 7 * TILE + 16, "wall_lamp"))
    # Drop cords over the cell approach and the booking floor (the 90%
    # rule): the law lights its own bars. The chosen dark is the cell's
    # inner corner.
    sc.add_decoration(Decoration(11 * TILE + 16, 9 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(7 * TILE + 16, 9 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(13 * TILE + 20, 10 * TILE + 24, "bloodstain",
                                 scale=1.4))
    sc.add_decoration(Decoration(14 * TILE + 26, 8 * TILE + 6, "cobweb",
                                 ang=math.pi))

    for mx, my in [(4, 2), (9, 3), (3, 9), (10, 9)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))

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
        # exchange sets vane_gave_cache and also drops it live). Neglect him and
        # the town's one weapon cache stays locked -- the gun is never required,
        # so this soft-locks nothing.
        if game.save.flag("vane_gave_cache"):
            from .base import drop_ammo_cache
            drop_ammo_cache(game, scene, 13, 4, 6, "ammo_sheriff")
    sc.on_enter_fn = _fc_on_enter
    return sc


def build_abandoned_farmhouse():
    """An abandoned FOUR-ROOM farmhouse (#4c): a KITCHEN (the entry), a
    PARLOR, a BEDROOM, and a BACK ROOM, quartered by a cross of partition
    walls and connected by three inner doors. Candle-lit and strewn with a
    fled family's left-behind belongings; the one live beat is the
    nailed-shut cult-chamber hatch in the back room."""
    floor = ["=" * 12 for _ in range(10)]
    # #4c -- a proper FOUR-ROOM farmhouse, not one box + a side room. A cross
    # of partition walls (the col-6 vertical + the row-4 horizontal, meeting
    # at the solid (6,4) corner) quarters the interior into a KITCHEN (NW, the
    # entry), a PARLOR (NE), a BEDROOM (SW), and a BACK ROOM (SE, the sealed
    # hatch). (The old two-stage glitch-wall trick -- a passable south-face
    # tile that dropped the player into a haunted `haunted_house_glitch`
    # version -- was CUT; the south face is solid.)
    objects = [
        "WWWoWWWWWWWW",   # 0  o = exit back to Brimley (north face)
        "W.....W....W",   # 1  KITCHEN (NW, cols 1-5) | PARLOR (NE, cols 7-10)
        "W..........W",   # 2  (6,2) = door gap, kitchen <-> parlor
        "W.....W....W",   # 3
        "WW.WWWWW.WWW",   # 4  horizontal cross wall; (2,4) + (8,4) door gaps
        "W.....W....W",   # 5  BEDROOM (SW) | BACK ROOM (SE)
        "W.....W....W",   # 6
        "W.....W....W",   # 7
        "W.....W....W",   # 8
        "WWWWWWWWWWWW",   # 9  sealed south wall
    ]
    sc = Scene("abandoned_farmhouse", floor, objects, music="home")
    # Abandoned farmhouse, deep south on the brimley west bank.
    sc.add_exit("o", "brimley", "from_abandoned_farmhouse")
    sc.set_spawn("default",     3, 1)      # in the kitchen, at the door
    sc.set_spawn("from_brimley", 3, 1)

    # Three inner doors quartering the house, placed in VARIED walls (error
    # class 8): the kitchen<->parlor door sits in the N-S col-6 wall so it
    # swings E-W; the two doors through the E-W row-4 cross wall swing N-S. A
    # curtain hangs over the bedroom, plank leaves elsewhere. All start shut;
    # a shut leaf blocks the sight cone, so the back room (the hatch) and the
    # bedroom are real blind spots off the entry.
    sc.add_inner_door(6, 2, "plank")       # kitchen <-> parlor  (swings E-W)
    sc.add_inner_door(2, 4, "curtain")     # kitchen <-> bedroom (swings N-S)
    sc.add_inner_door(8, 4, "plank")       # parlor  <-> back room (swings N-S)

    # A house left mid-life, gone abandoned. Phantom marks scratched into the
    # floorboards (phantom_mark is a floor decal -- it warps onto the floor
    # under the tilt, not the walls), one per room. A candle still burning in
    # each room is the only light (the farmhouse keeps the darker gloom +
    # candles, not the genset bulbs); who lit them, in an empty house.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22, "candle"))   # kitchen
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 22, "candle"))   # parlor
    sc.add_decoration(Decoration(3 * TILE + 16, 6 * TILE + 16, "candle"))   # bedroom
    sc.add_decoration(Decoration(8 * TILE + 16, 6 * TILE + 16, "candle"))   # back room
    sc.add_decoration(Decoration(1 * TILE + 28, 3 * TILE + 16, "phantom_mark"))  # kitchen
    sc.add_decoration(Decoration(8 * TILE + 16, 1 * TILE + 16, "phantom_mark"))  # parlor
    sc.add_decoration(Decoration(2 * TILE + 16, 7 * TILE + 16, "phantom_mark"))  # bedroom
    sc.add_decoration(Decoration(9 * TILE + 28, 6 * TILE + 16, "phantom_mark"))  # back room
    sc.add_decoration(Decoration(4 * TILE + 16, 7 * TILE + 24, "bloodstain"))    # bedroom
    # What the family left when they went: a preserves shelf nobody came back
    # for on the kitchen wall, a birdcage standing open in the parlor, the bed
    # still in the bedroom.
    sc.add_decoration(Decoration(1 * TILE + 16, 0 * TILE + 22,
                                 "preserve_shelf", seed=23))
    sc.add_decoration(Decoration(9 * TILE + 16, 2 * TILE + 16, "birdcage"))
    sc.add_furniture("bed", [(1, 7), (1, 8)], w=34, h=56)
    for mx, my in [(3, 2), (4, 6), (9, 7)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16, "mote"))

    # Dressing follow-up (2026-07): the quartered rooms read as empty boxes,
    # but a fled family leaves a house FULL of what it could not carry. Scatter
    # left-behind belongings, one or two per room -- all non-solid decorations,
    # so collision, nav, and reachability are untouched: a wash basin and a
    # knocked-over chair in the kitchen; a family portrait and the mother's
    # needlework still hung in the parlor; a basin and another fallen chair in
    # the bedroom; dead leaves blown in and a chair in the back room. Placed
    # clear of the candles, the doors, the spawn, and the hatch.
    sc.add_decoration(Decoration(5 * TILE + 16, 2 * TILE + 16, "washstand"))
    sc.add_decoration(Decoration(4 * TILE + 12, 3 * TILE + 20,
                                 "overturned_chair"))
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 22,
                                 "oil_portrait", seed=6))
    sc.add_decoration(Decoration(10 * TILE + 16, 0 * TILE + 22,
                                 "sampler", seed=11))
    sc.add_decoration(Decoration(4 * TILE + 16, 5 * TILE + 16, "washstand"))
    sc.add_decoration(Decoration(5 * TILE + 12, 8 * TILE + 20,
                                 "overturned_chair"))
    sc.add_decoration(Decoration(10 * TILE + 16, 5 * TILE + 16, "leaves"))
    sc.add_decoration(Decoration(7 * TILE + 12, 6 * TILE + 20,
                                 "overturned_chair"))

    # Cult-chamber hatch: a sealed dead end in the BACK ROOM (SE, a blind spot
    # two doors off the entry). It once dropped into the old cult chamber (now
    # removed); pressing E plays a locked sound + a sealed-hatch notice.
    hatch_x = 8 * TILE + 16
    hatch_y = 7 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._farmhouse_hatch = (hatch_x, hatch_y)
    sc.add_interactable(hatch_x, hatch_y, 36)   # [E] cue for the sealed hatch

    sc.hide_spots = []

    def _farmhouse_interact(game):
        # Sealed. The grove fold is the only way down (NARRATIVE §7/§9).
        if (abs(game.player.x - hatch_x) < 36
                and abs(game.player.y - hatch_y) < 36):
            game.audio.play("door_close", 0.5)
            game.show_notice("The hatch is sealed shut. It does not budge.")
    sc.on_interact_fn = _farmhouse_interact

    return sc
