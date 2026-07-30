"""Smaller interior areas: void, cave, shop, easter egg room,
kid's house. Combat scenes (cave, easter egg room) respawn
their standard enemy set on every entry; respawned enemies drop
nothing 85% of the time -- except on the very first easter_egg_room
visit, where every kill drops (gated by the first_easter_egg flag)."""
import math
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene
from .dialogue import toby_dialogue, hettie_dialogue, _evidence, grant_receipt
def build_clearing():
    """THRESHOLD: the clearing. A small open glade off the river
    bank: a cold fire pit at its centre, cordwood, hung robes, effigy dolls
    on the charred edge, crows in the tree line. The scene is kept because
    `is_clearing` is load-bearing for the flashback and patrol systems.

    It ASSERTS NOTHING about the fiction as of 2026-07 (the burn-site
    conceit was ruled rot and cut with its beat). The props are dressing
    until the glade is given a purpose or removed outright.

    Visual layout (18 wide x 14 tall):
      - Tree-wall border on every edge.
      - Worn dirt path enters from the south at col 9, widening as
        it approaches the fire pit. The path is the only break in
        an otherwise overgrown perimeter.
      - The 'j' tile at (9, 13) is the transition tree. The
        'from_*' spawns sit at (9, 11) -- two rows north of the
        threshold so the player can look around without immediately
        re-firing the exit.
      - Charred patch in cols 5-12, rows 5-8 (centre).
      - The dead fire pit at centre (9, 7), scrap around it.
      - Hanging figures in the canopy NW + NE -- visible above the
        tree wall on either side of the entrance approach.
      - Cordwood stacks at (2, 6) and (15, 6). Solid t tiles; their
        hide spots sit on the walkable tile beside each stack.
      - Cult robes (banner) hung on the west tree. Effigy dolls at
        (4, 6) and (14, 6) sitting on the charred edge.

    Hide spots are colocated with visible cover (cordwood, robes)
    and never on a solid object's tile."""
    floor = []
    for y in range(14):
        row = ""
        for x in range(18):
            if 5 <= x <= 12 and 5 <= y <= 8:
                row += "x"      # charred dirt
            elif x == 9 and 9 <= y <= 12:
                row += "d"      # worn approach path
            elif 8 <= x <= 10 and 11 <= y <= 12:
                row += "d"      # path widens at the threshold
            else:
                row += "g"      # grass
        floor.append(row)
    objects_l = []
    for y in range(14):
        if y == 0 or y == 13:
            objects_l.append(list("T" * 18))
        else:
            row = ["T"] + ["."] * 16 + ["T"]
            objects_l.append(row)
    # Transition tree at the south threshold. Visually identical to
    # a tree, walking onto it sends the player back to cornfield_path.
    objects_l[13][9] = "j"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("clearing", floor, objects, music="wrong")
    # Cordwood stacks flanking the fire pit. Real
    # firewood volumes (2026-07 audit fix: they were raw 't' object tiles,
    # which no tilt set draws -- invisible collision blocks, and the hide
    # spots crouched beside nothing). Two stacks so the clearing reads as
    # a tended ritual site, not a one-prop display.
    sc.add_furniture("firewood", [(2, 6)], w=44, h=24)
    sc.add_furniture("firewood", [(15, 6)], w=44, h=24)
    # The clearing's south threshold leads back to the river road's
    # bank (where the entrance is).
    # The way back out is the pine flank of the river road, where the
    # hidden doorway in the treeline came through (DESIGN.md §15).
    sc.add_exit("j", "river_road", "from_clearing")
    sc.set_spawn("default",          9, 11)
    sc.set_spawn("from_river_road",  9, 11)

    # The dead fire pit at centre -- scaled up so it reads as a gathering
    # fire rather than a campsite. Scrap around it.
    sc.add_decoration(Decoration(9 * TILE + 16, 7 * TILE + 16,
                                 "campfire", scale=3.0))
    sc.add_decoration(Decoration(7 * TILE + 16, 8 * TILE + 16, "bowl"))
    sc.add_decoration(Decoration(11 * TILE + 16, 6 * TILE + 16, "bowl"))
    sc.add_decoration(Decoration(6 * TILE + 16, 7 * TILE + 16,
                                 "phantom_mark"))
    for sx, sy in [(4, 5), (13, 5), (4, 9), (13, 9), (9, 4)]:
        sc.add_decoration(Decoration(sx * TILE + 16, sy * TILE + 16,
                                     "phantom_mark"))
    # Two hanging figures in the canopy, visible behind the tree
    # wall NW and NE of the fire pit.
    sc.add_decoration(Decoration(3 * TILE + 16, 1 * TILE + 24,
                                 "hanging_figure"))
    sc.add_decoration(Decoration(15 * TILE + 16, 1 * TILE + 24,
                                 "hanging_figure"))
    # Cult robes hung on the west tree -- a banner-deco stand-in.
    sc.add_decoration(Decoration(1 * TILE + 16, 8 * TILE + 16,
                                 "banner", color=(110, 90, 50)))
    # Effigy dolls on the charred edge -- small, X-eyed, watching
    # the fire pit.
    sc.add_decoration(Decoration(4 * TILE + 16, 6 * TILE + 16, "doll"))
    sc.add_decoration(Decoration(14 * TILE + 16, 6 * TILE + 16, "doll"))
    # Claw gouges on the charred ground around the fire pit.
    sc.add_decoration(Decoration(6 * TILE + 16, 5 * TILE + 22,
                                 "claw_marks"))
    sc.add_decoration(Decoration(11 * TILE + 16, 5 * TILE + 22,
                                 "claw_marks"))
    # Path-side candles framing the entrance threshold.
    sc.add_decoration(Decoration(8 * TILE + 4, 12 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(10 * TILE + 28, 12 * TILE + 22, "candle"))
    # Two crows in the tree line.
    sc.add_decoration(Decoration(2 * TILE + 8, 1 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(15 * TILE + 8, 1 * TILE + 22, "crow"))
    # Dead crow on the path.
    sc.add_decoration(Decoration(9 * TILE + 16, 10 * TILE + 22,
                                 "dead_crow"))
    # Motes for ambient particles.
    for i in range(8):
        sc.add_decoration(Decoration(40 + i * 50,
                                     60 + (i % 3) * 50, "mote"))

    sc.hide_spots = []

    # Tag the scene as the clearing for the flashback / patrol systems.
    sc.is_clearing = True

    # (THE BURNING is CUT, 2026-07 -- maintainer ruling: the "cult burned
    # their worldly effects here before they went below" conceit was rot, so
    # the beat, its [E] cue, and the burn-site framing are gone. The glade
    # keeps its props as plain dressing; it asserts nothing now. Its stated
    # PURPOSE is an open question -- see TODO #1.)
    return sc
def _shop_update(game, scene, dt):
    # The spike is the fallback: a walk-over pickup, and ONLY once Hettie
    # is dead (while she's alive, talk to her for the tab -- no dead [E]
    # cue advertising the spike).
    if game.save.flag("evidence_maras_receipt"):
        return
    if not game._local_is_dead("Hettie"):
        return
    rx, ry = scene._receipt_pos
    if abs(game.player.x - rx) < 22 and abs(game.player.y - ry) < 22:
        grant_receipt(game)


def build_shop():
    """The General Store, rebuilt as a NESTED warren of subrooms (2026-07, the
    interior-door pass; the pilot for the room redesign): an L-shaped public
    shop floor where Hettie keeps the counter, and a chain of service rooms dug
    off it behind interior doors that MOSTLY START CLOSED. Off the shop's west
    side a plank door opens on a dry-goods STOCKROOM; off the BACK of the
    stockroom a second plank door opens on the cold PANTRY -- two doors deep,
    out of the shop's sight entirely, the true blind spot where the cult tells
    live (the mirror with the wrong silhouette, the wrong_photo). A cloth
    curtain closes off Hettie's little OFFICE nook on the shop's north-east.
    Hettie opens her own way through on her route; the player opens them with
    E, and a shut door on a pursuer breaks the sightline."""
    floor = ["=" * 16 for _ in range(13)]
    objects = [
        "WWWWWWWWWWWWWWWW",   # 0
        "W....W....W....W",   # 1  pantry(1-4) | shop-back(6-9) | office(11-14)
        "W....W.........W",   # 2  office door (col 10, a SIDE wall)
        "WW.WWW....W....W",   # 3  pantry<->stockroom door (col 2)
        "W....W....WWWWWW",   # 4  stockroom | shop | office SW corner (col 10)
        "W..............F",   # 5  stockroom door (col 5); F = out to the yard
        "W....W.........W",   # 6  stockroom | shop
        "W....W.........W",   # 7
        "WWWWWW.........W",   # 8  stockroom S wall closes its SE corner (col 5)
        "W..............W",   # 9
        "W..............W",   # 10
        "W..............W",   # 11
        "WWWWWWWWDWWWWWWW",   # 12  D = exit door back to the field (col 8)
    ]
    # The stockroom receiving-corner ensemble's footprint (see below): the
    # same tiles its old separate crates/table/barrel occupied, as see-over
    # solids, so reachability and the door approaches don't move.
    _rows = [list(r) for r in objects]
    for _sx, _sy in ((1, 4), (1, 5), (3, 6), (4, 7)):
        _rows[_sy][_sx] = "x"
    objects = ["".join(r) for r in _rows]
    sc = Scene("shop", floor, objects, music="home")
    # The General Store stands out on the Brimley bank now; its door
    # opens back onto the field.
    # THE OLD STREET DOOR IS WALLED UP. Brimley the scene is retired
    # (DESIGN.md §15): this building's outdoors is its own YARD now, and
    # a leaf onto a town that no longer exists is a door that does
    # nothing -- which reads as a broken building, not a changed world.
    assert sc.wall_up("D") == 1
    # THE YARD DOOR (DESIGN.md §15). The store's own ground is a scene now,
    # off the store row, and it needs its own way in: a second door in the
    # east wall, opening onto the yard. The south `D` still goes to Brimley
    # and stays until Brimley is retired, so both routes are live and each
    # returns you where you came from.
    sc.add_exit("F", "shop_yard", "from_shop")
    sc.set_spawn("default", 8, 10)
    sc.set_spawn("from_shop_yard", 14, 5)    # one tile west of the F door

    # The three interior doors (2026-07), a nested chain + one nook, deliberately
    # NOT all in the same wall: the stockroom and office doors sit in SIDE (N-S)
    # walls and open east/west, while the pantry door sits in an E-W wall and
    # opens north/south -- the leaves don't all face the same way. Most start
    # CLOSED. The pantry door is two rooms deep, so the cult tells behind it are
    # out of the shop's sight until you open the stockroom, cross it, and open
    # the pantry.
    sc.add_inner_door(5, 5, "plank")         # shop  -> stockroom (faces E-W)
    sc.add_inner_door(2, 3, "plank")         # stockroom -> cold pantry (faces N-S)
    sc.add_inner_door(10, 2, "curtain")      # shop  -> office nook (faces E-W)

    # Hettie stands behind the counter in the shop, facing the entrance.
    hx, hy = 8, 8
    het = NPC(hx * TILE + 16, hy * TILE + 16,
              "Hettie", "hettie", voice="blip_high",
              portrait="hettie",
              dialogue_fn=hettie_dialogue, movement="worker")
    het.talk_reach = 56          # a counter seat: reachable across the till
    # Her JOB (the JOBS layer): the counter mostly, a pass along the empty goods
    # shelves (dusting stock that never comes), and a trip back into the
    # stockroom -- which walks her THROUGH the plank door, so she opens her own
    # way (the auto-open showcase).
    het.stations = [
        {"x": hx * TILE + 16, "y": hy * TILE + 16,
         "dwell": (10.0, 16.0), "face": (0, 1)},     # the counter
        {"x": 8 * TILE + 16, "y": 2 * TILE + 16,
         "dwell": (3.0, 5.0), "face": (0, -1)},      # the back-shop shelves
        {"x": 2 * TILE + 16, "y": 5 * TILE + 16,
         "dwell": (4.0, 7.0), "face": (0, -1)},      # the stockroom
    ]
    sc.add_npc(het)
    # Worn shop rug over the shop floor -- multi-tile + off-grid to
    # break the plank tiling. First, so props draw on top.
    sc.add_decoration(Decoration(8 * TILE + 24, 9 * TILE + 8, "rug",
                                 w=104, h=64, color=(58, 60, 64), seed=31))
    # --- The shop floor (public) ---
    # The long goods runs stand EMPTY (bare_shelf: dust-ghosts where stock
    # stood, one tin left; no deliveries since the new year, DESIGN.md §4 food
    # scarcity). One in the back-shop aisle, one along the east wall.
    sc.add_furniture("bare_shelf", [(6, 1), (7, 1)], w=58, h=18, seed=1)
    sc.add_furniture("bare_shelf", [(12, 6), (13, 6)], w=58, h=18, seed=2)
    # Hettie's counter -- a low see-over volume like the Lodge front desk --
    # plus a stool tucked behind it.
    sc.add_furniture("butcher_counter", [(8, 9)], see_over=True)
    sc.add_furniture("butcher_counter", [(9, 9)], see_over=True)
    sc.add_furniture("chair", [(9, 8)], w=22, h=28)
    # A potbelly stove fills the dead SW corner -- the general-store gathering
    # spot, and the one warmth Hettie still feeds (the stoop line made a hearth:
    # "I keep the lights on. So they know."). A split-wood stack sits beside it.
    sc.add_furniture("stove", [(2, 10)], w=30, h=40, wall="W")
    sc.add_furniture("firewood", [(3, 10)], w=44, h=24)
    # A butter churn parked against the east wall of the shop floor. The dairy
    # stopped coming before the trucks did.
    sc.add_decoration(Decoration(14 * TILE + 10, 10 * TILE + 8,
                                 "butter_churn"))
    # THE LIGHT IS DESIGNED (2026-07 shop pass, per tools/light_audit.py).
    # Lit on purpose: the COUNTER, under Hettie's one kept bulb (the tableau's
    # "one kept bulb burning over the counter" made world-real -- a drop_bulb
    # hung over the till, cold genset electric), with the counter kerosene
    # lamp a small WARM accent inside the cold pool (the additive overlap);
    # and the east shop floor under the bulkhead wall_lamp. Dark on purpose:
    # the NORTH AISLE (the bare dust-ghost shelves half-seen over the lit
    # counter), the stove corner (ember-warm fiction, no pool), the office
    # nook, and the stockroom->pantry chain (candle only, then pitch dark:
    # the cult tells behind two doors read by flashlight or not at all).
    # (hung over the counter's front-centre air: the kerosene lamp keeps the
    # west end, the till the east, and the bulb clears Hettie's body on the
    # N facing -- three things reading as three things, not one blob)
    sc.add_decoration(Decoration(9 * TILE + 0, 9 * TILE + 24, "drop_bulb",
                                 z=42))
    # (the bulkhead lamp is HOODED: its fan aims west into the room, so the
    # wall behind it stays honest dark -- the cone-fixture pilot, TODO #21)
    sc.add_decoration(Decoration(14 * TILE + 16, 9 * TILE + 16, "wall_lamp",
                                 cone=(-1, 0, 55)))
    # The 90% rule (maintainer, 2026-07): with every light on, >=90% of the
    # walkable floor sits in a visible pool -- and the pendants hang in
    # ROWS (maintainer: lights run on one axis, never scatter; cords come
    # off joists and joists run parallel). The shop strings three E-W
    # runs: the main-floor row (the counter bulb is its middle), the
    # mid-floor pair, and the aisle single, plus one centered fixture per
    # service room. The PANTRY is the chosen dark (the cult tells behind
    # two doors read by flashlight or not at all).
    # -- the main-floor row, y = 9*T+24 (the counter bulb above is its
    #    middle at x = 9*T). The WEST one is burned out (the 1-2 broken
    #    rule: no deliveries means no replacement bulbs; Hettie keeps the
    #    counter and aisle burning, the ones people see)
    sc.add_decoration(Decoration(4 * TILE + 16, 9 * TILE + 24, "drop_bulb",
                                 z=38, broken=True))
    sc.add_decoration(Decoration(13 * TILE + 16, 9 * TILE + 24, "drop_bulb",
                                 z=38))
    # -- the mid-floor row, y = 6*T+16; the EAST one is dead too
    sc.add_decoration(Decoration(8 * TILE + 16, 6 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(12 * TILE + 16, 6 * TILE + 16, "drop_bulb",
                                 z=38, broken=True))
    # -- the back-shop aisle single + one centered per service room
    sc.add_decoration(Decoration(8 * TILE + 16, 2 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(12 * TILE + 16, 2 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 16, "drop_bulb",
                                 z=38))
    # A kerosene lamp on the counter is the backup for when the gas runs low.
    sc.add_decoration(Decoration(8 * TILE + 16, 9 * TILE + 2,
                                 "kerosene_lamp"))
    # The old brass till on the counter -- empty since the new year, the amount
    # flag reading nothing ("Till's been empty since the new year" made an
    # object; the tableau-parity pass). Seated on the counter by
    # seat_tabletop_props. Sits east of Hettie's till spot so it never masks her.
    sc.add_decoration(Decoration(9 * TILE + 16, 9 * TILE + 16, "cash_register",
                                 scale=1.1))
    # Mara's tab curled on the receipt spike by the till: the spike rises right
    # at the tab (the world-persistent `papers` at _receipt_pos below), so the
    # two read as one -- slips impaled by the till.
    sc.add_decoration(Decoration(8 * TILE + 16, 9 * TILE + 9, "bill_spike"))
    # Lodge dressing: a mounted buck + trophy walleye high on the back-shop
    # north wall, over the empty aisle.
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    # --- The stockroom (west, first door): THE RECEIVING CORNER (Wave 2
    # ensemble; TODO #24): crate stack + check table + flour barrel composed
    # as ONE object with its wear (the dust ghost of sold-out stock, the
    # stopped tally, the shipped twin's ring stain). The candle stays its
    # own deco, SEATED on the check table, so it keeps emitting. Footprint
    # tiles ('x' stamps below) match the old separates exactly, so
    # reachability + Hettie's (2,5) station are untouched.
    sc.add_decoration(Decoration(1 * TILE + 16, 5 * TILE + 0,
                                 "stockroom_corner", seed=12))
    sc.add_decoration(Decoration(3 * TILE + 24, 6 * TILE + 8, "candle",
                                 z=27))
    sc.add_decoration(Decoration(1 * TILE + 6, 4 * TILE + 6, "cobweb",
                                 ang=0.0))
    # --- The cold pantry (nested, two doors deep): preserves + the cult tells ---
    # Hettie's preserves on the north wall. Nobody has bought any in a while;
    # the contents have all gone the same murky shade.
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 22,
                                 "preserve_shelf", seed=17))
    # A placed DARK SOURCE deepens the pantry past the room's ambient (the
    # reverse light, 2026-07): the cult tells sit in blackness blacker
    # than the gloom, and the flashlight beam is the only honest read.
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 16, "dark_pool",
                                 r=84, depth=52))
    # The cult tells, hidden in the pantry (the true blind spot, out of the
    # shop's sight): the mirror that shows the wrong silhouette, the wrong_photo.
    sc.add_decoration(Decoration(3 * TILE + 16, 1 * TILE + 16, "mirror"))
    sc.add_decoration(Decoration(1 * TILE + 16, 0 * TILE + 22,
                                 "wrong_photo", stage=1))
    # --- Hettie's office nook (north-east, curtain): the calendar, clock, radio ---
    # A low goods shelf, and the wrong radio sits ON it (its art is a thing on
    # a surface; on the bare floor it read as a sticker under the tilt).
    sc.add_furniture("shelf", [(13, 1)], w=28, h=16, seed=7)
    sc.add_decoration(Decoration(13 * TILE + 16, 1 * TILE + 22, "wrong_radio"))
    sc.add_decoration(Decoration(12 * TILE + 16, 0 * TILE + 22, "clock"))
    # Hettie's calendar -- "no deliveries in a while now," the days with
    # nowhere left to count toward (stasis, not a loop -- NARRATIVE §2).
    sc.add_decoration(Decoration(14 * TILE + 16, 0 * TILE + 24, "calendar"))
    sc.add_furniture("chair", [(13, 3)], w=22, h=28)
    for mx, my in [(11, 9), (5, 9), (9, 11)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Mara's store tab (surface evidence; NARRATIVE §6, DESIGN.md §9). You get
    # it by TALKING to Hettie (show her Mara's photo -> her warm handover;
    # play-notes). The curled slip on the spike is only the world-persistent
    # FALLBACK, reachable once Hettie is DEAD, so killing her can never
    # soft-lock the descent. Both funnel through grant_receipt (flag-gated).
    sc._receipt_pos = (8 * TILE + 16, 9 * TILE + 16)
    sc.add_decoration(Decoration(8 * TILE + 16, 9 * TILE + 6, "papers",
                                 seed=23))

    sc.on_update_fn = _shop_update
    sc.hide_spots = []
    return sc
def _barn_update(game, scene, dt):
    # Mara's journal is a WALK-OVER pickup (play-notes: an item, not an
    # [E] prompt). Stepping onto it takes it and drops the PI back into his
    # one year-old dream ON PICKUP (not the 3rd read). The gate beat is
    # logged QUIETLY -- no case note pops before he has read it.
    if game.save.flag("evidence_maras_journal"):
        # Already taken: strip the token the scene rebuild re-adds.
        if any(getattr(d, "tag", None) == "maras_journal"
               for d in scene.decorations):
            scene.decorations = [
                d for d in scene.decorations
                if getattr(d, "tag", None) != "maras_journal"]
        return
    px, py = game.player.x, game.player.y
    jx, jy = scene._journal_pos
    if abs(px - jx) < 22 and abs(py - jy) < 22:
        game.player.inventory.add("mom_notebook", 1)
        game.audio.play("pickup_rare", 0.7)
        game.audio.play("low_pulse", 0.45)
        game.show_notice("Her journal.")
        # The log excerpts quote MARA_JOURNAL_PAGES (systems/items.py) so
        # the evidence beat and the readable journal never drift apart.
        _evidence(game, "maras_journal", [
            "A notebook, shoved down behind the workbench. You know the "
            "hand. It's hers.",
            "Her journal. Three leaves, in a hand that gets calmer "
            "as it goes:",
            "\"They told me grief would pass. It did not pass. It only "
            "learned my name.\"",
            "\"I have started to dream of a door. It is not "
            "frightening. It feels like being remembered.\"",
            "\"They dreamed the same door, every one of them. We are "
            "digging down to it together now. I am not lost. I have "
            "never been this close.\"",
        ], show=False, quiet=True)
        # The door-dream hits ON PICKUP now (play-notes), not the 3rd read.
        if not game.save.flag("flashback_seen"):
            game.save.set_flag("flashback_pending", True)
        scene.decorations = [
            d for d in scene.decorations
            if getattr(d, "tag", None) != "maras_journal"]


def _barn_interact(game):
    hatch_x, hatch_y = game.scene._barn_hatch_pos
    px, py = game.player.x, game.player.y
    # The old tunnel down to the Works has been nailed shut: the
    # rite (the grove's descent fold) is the ONLY way underground
    # now (no secret paths).
    if (abs(px - hatch_x) < 36 and abs(py - hatch_y) < 36):
        game.audio.play("door_locked", 0.6)
        game.show_notice("Nailed fast from the underside. It does "
                         "not give.")


def build_barn():
    """The barn, off the chapel row (its yard is barn_yard), divided (#4c) into a front working
    bay, an open sleeping-floor dormitory, and an enclosed back workroom, split
    by two plank inner doors. Holds Mara's journal
    (a surface trail beat) behind the workbench, and a boarded-over hatch where a
    tunnel down to the Works once ran -- nailed shut now; the rite (the
    grove's descent fold) is the only way underground, and no hatch ever
    will be again. Lodge dressing (mounted buck, walleye,
    antler rack, firewood) and hide spots among the hay-bale shelves."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWWnWWWWWWWWWWW",   # 0  n = barn door (north face)
        "W........W.....W",   # 1  front bay (cols 1-8, rows 1-4) | workroom (cols 10-14)
        "W........W.....W",   # 2
        "W..............W",   # 3  doorway gap in the partition (col 9)
        "W........W.....W",   # 4
        "WWWW.WWWWW.....W",   # 5  front-bay S wall; door gap col 4 -> dormitory
        "W........WWWWWWW",   # 6  back stall sealed off below
        "W..............W",   # 7
        "W..............W",   # 8
        "W..............W",   # 9
        "W..............W",   # 10
        "WWWWWWWWFWWWWWWW",   # 11
    ]
    sc = Scene("barn", floor, objects, music="home")
    # The barn's outdoors is its own yard scene (DESIGN.md §15).
    # THE OLD STREET DOOR IS WALLED UP. Brimley the scene is retired
    # (DESIGN.md §15): this building's outdoors is its own YARD now, and
    # a leaf onto a town that no longer exists is a door that does
    # nothing -- which reads as a broken building, not a changed world.
    assert sc.wall_up("n") == 1
    # THE YARD DOOR (DESIGN.md §15): this building has its own yard
    # scene now, and needs its own way in. The Brimley door above
    # stays live until Brimley is retired.
    sc.add_exit("F", "barn_yard", "from_barn")
    # The workbench (Mara's journal) and the boarded hatch both sit in the
    # back stall -- behind the partition, so they're an indoor blind spot.
    sc.set_spawn("default", 5, 8)
    sc.set_spawn("from_barn_yard", 8, 10)

    # #4c -- the barn reads as a divided working building now, not one open
    # box + a back stall. A row-5 partition splits the upper floor into a
    # FRONT BAY (the entry + the racked gear) and keeps the lower floor the
    # open DORMITORY (all the bedrolls sit down there, so the "slept all over"
    # read stays intact); the old back stall is the WORKROOM (Mara's journal +
    # the sealed hatch). Two plank inner doors, placed in VARIED walls (error
    # class 8): the front-bay door sits in the E-W row-5 wall so its leaf
    # swings N-S; the workroom door in the N-S col-9 wall so its leaf swings
    # E-W. Both start shut; a shut leaf blocks the sight cone, so the workroom
    # is a real back blind spot, not an open gap. Player toggles nearest with E.
    sc.add_inner_door(4, 5, "plank")     # front bay -> dormitory (swings N-S)
    sc.add_inner_door(9, 3, "plank")     # front bay -> workroom (swings E-W)
    # The division cuts the DORMITORY (a DIM_INTERIOR half) off from the
    # front-bay wall_lamp, so hang a second genset bulkhead on the partition's
    # south face to light the sleeping floor (verified in the dark render).
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE + 16, "wall_lamp"))

    # Sized furniture: racked gear runs out front (the diggers' stowed kit;
    # 2026-07 audit fix: these were 'bookshelf' cases, which render with
    # colored BOOK SPINES -- a library bookcase in a barn, the classic
    # place-a-kind-by-its-name trap) and the workbench in the back stall.
    sc.add_furniture("gear_shelf", [(2, 2), (3, 2)], w=54, h=18, seed=9)
    sc.add_furniture("gear_shelf", [(5, 2), (6, 2)], w=54, h=18, seed=10)
    sc.add_furniture("table", [(11, 2), (12, 2)], w=54, h=36)
    sc.add_decoration(Decoration(13 * TILE + 16, 1 * TILE + 24, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 24, "lantern"))
    # Genset-electric main light on the main-floor north wall (the lantern +
    # candle are backup). (2026-07 interior pass.)
    sc.add_decoration(Decoration(7 * TILE + 16, 1 * TILE + 16, "wall_lamp"))
    # The 90% rule + the ROW rule (lights run on one axis, never scatter):
    # the commune strung ONE straight run down the dormitory's length,
    # three pendants at even spacing, plus one centered over the workroom
    # bench (Mara's journal corner). The chosen dark is the dormitory's
    # SE corner.
    # (the run's MIDDLE bulb is burned out -- the 1-2 broken rule: a dead
    # gap in the dead commune's row)
    sc.add_decoration(Decoration(3 * TILE + 16, 8 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(7 * TILE + 16, 8 * TILE + 16, "drop_bulb",
                                 z=38, broken=True))
    sc.add_decoration(Decoration(11 * TILE + 16, 8 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(12 * TILE + 16, 2 * TILE + 16, "drop_bulb",
                                 z=38))
    sc.add_decoration(Decoration(11 * TILE + 16, 3 * TILE + 24,
                                 "bloodstain"))
    # The dormitory's SE corner is a placed dark source (the reverse
    # light): the chosen dark made blacker than ambient, where the dead
    # run's gap points.
    sc.add_decoration(Decoration(13 * TILE + 16, 9 * TILE + 16, "dark_pool",
                                 r=76, depth=42))
    # Northern-MN lodge dressing: a mounted buck + trophy walleye on the
    # north wall, cobwebs in the high corners, an antler coat-rack on
    # the west wall, and a split-wood stack in the SW corner. The floor
    # pieces are collision furniture, tucked clear of the hatch + spawn
    # paths so the room stays passable.
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(14 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_furniture("antler_rack", [(1, 4)], w=22, h=46)
    sc.add_furniture("firewood", [(1, 8), (1, 9)], w=24, h=58)
    # Farm gear gone idle: a dry butter churn against the west wall, and
    # a preserves shelf in the back stall over the workbench.
    sc.add_decoration(Decoration(1 * TILE + 18, 6 * TILE + 8,
                                 "butter_churn"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 22,
                                 "preserve_shelf", seed=21))
    # It read like one farmer's barn, but the newcomers bedded down here in
    # numbers (Toby: "They slept all over then. The barn.") -- dress it so it
    # reads inhabited by MANY. Six bedrolls laid out across the main floor
    # (staggered off the grid, clear of the spawn tile at (5,8), the col-5
    # walk to the back stall, and the door approach), each with a pile of
    # shed belongings beside a couple, plus gear crates -- a commune
    # dormitory, not one farmer's cot.
    for (bx, by, ba) in [(2, 7, 0.0), (3, 9, 0.5), (6, 7, -0.4), (7, 9, 0.2),
                         (4, 7, 0.3), (8, 8, -0.2)]:
        sc.add_decoration(Decoration(bx * TILE + 14, by * TILE + 18,
                                     "bedroll", ang=ba, seed=bx * 7 + by))
    # Their belongings, set down where the fold took them (the effects the
    # Sorting Hall now catalogues, shed at the sleeping place): a folded
    # bundle beside two of the rolls.
    sc.add_decoration(Decoration(3 * TILE + 16, 8 * TILE + 16, "effects_pile",
                                 seed=4))
    sc.add_decoration(Decoration(7 * TILE + 16, 8 * TILE + 16, "effects_pile",
                                 seed=9))
    sc.add_decoration(Decoration(2 * TILE + 18, 10 * TILE + 12, "crate",
                                 seed=3))
    sc.add_decoration(Decoration(7 * TILE + 14, 10 * TILE + 12, "crate",
                                 seed=8))
    # The well-passage tunnel hatch -- a proper cellar_hatch sprite,
    # NOT a chest. Drawn as a wooden floor hatch with iron pull-ring;
    # the player presses E adjacent. In the back stall, row 4 (2026-07
    # audit fix: at row 5 it sat against the stall's south wall and the
    # wall mass fully occluded it under the tilt -- an invisible prop
    # with a live [E] cue).
    hatch_x = 12 * TILE + 16
    hatch_y = 4 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._barn_hatch_pos = (hatch_x, hatch_y)
    sc.add_interactable(hatch_x, hatch_y, 36)   # [E] cue for the sealed hatch
    # Mara's journal, stashed behind the workbench -- a surface trail beat.
    # A WALK-OVER pickup (play-notes: it's an item, not an [E] prompt); the
    # door-dream fires on pickup, handled in _barn_update below.
    sc._journal_pos = (11 * TILE + 16, 3 * TILE + 16)
    _jrnl = Decoration(sc._journal_pos[0], sc._journal_pos[1], "papers", seed=17)
    _jrnl.tag = "maras_journal"
    sc.add_decoration(_jrnl)
    sc.hide_spots = []
    # Chalk doors -- the cult's drawn-door compulsion. The barn (Mara's, the
    # diggers' old quarters) is where the PI first meets the motif: one chalked
    # flat on the floor (the voice beat -- examine it) and one on the wall.
    sc.add_chalk_door(4 * TILE + 16, 9 * TILE + 16, voice="chalk_surface", seed=3)
    sc.add_chalk_door(7 * TILE + 16, 1 * TILE + 10, seed=5, wall=True)

    sc.on_interact_fn = _barn_interact

    sc.on_update_fn = _barn_update
    return sc


def build_toby_house():
    floor = ["=" * 14 for _ in range(10)]
    objects = [
        "WWWWWWWWWiWWWW",   # 0  i = the window Toby watches the corn line through
        "W....W.......W",   # 1  closet (cols 1-4) | the room (cols 6-12)
        "W....W.......W",   # 2
        "W............W",   # 3  curtain doorway in the partition (col 5)
        "W....W.......W",   # 4
        "WWWWWW.......F",   # 5  closet sealed off below
        "W........K...W",   # 6  K = Toby
        "W............W",   # 7
        "W............W",   # 8
        "WWWWJWWWWWWWWW",   # 9  J = exit door back to the field
    ]
    sc = Scene("toby_house", floor, objects, music="home")
    # Toby's house fronts the bank row; its outdoors is toby_yard.
    # THE OLD STREET DOOR IS WALLED UP. Brimley the scene is retired
    # (DESIGN.md §15): this building's outdoors is its own YARD now, and
    # a leaf onto a town that no longer exists is a door that does
    # nothing -- which reads as a broken building, not a changed world.
    assert sc.wall_up("J") == 1
    # THE YARD DOOR (DESIGN.md §15): this building has its own yard
    # scene now, and needs its own way in. The Brimley door above
    # stays live until Brimley is retired.
    sc.add_exit("F", "toby_yard", "from_toby_house")
    sc.set_spawn("default", 8, 7)
    sc.set_spawn("from_toby_yard", 12, 5)
    # The closet doorway (#4c): a maroon CURTAIN across the col-5 partition gap
    # (row 3), the gentlest leaf in the set -- this is the refuge (a SAFE_SCENE),
    # and a drape over a child's closet nook fits a kid's room where a plank door
    # would read too institutional. Drawn shut, it also keeps the closet the
    # blind spot it is meant to be (the corn dolls, the phantom marks, and the
    # crayon King hidden until the player draws it back). The col-5 wall is N-S,
    # so it hangs across an E-W doorway.
    sc.add_inner_door(5, 3, "curtain")

    pos = sc.consume_marker("K")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Toby", "toby", voice="blip_kid",
                       portrait="toby",
                       dialogue_fn=toby_dialogue, movement="idle"))
    # Sized darkwood furniture: a 2x2 kid's bed, a long bookshelf, a
    # small table (toy radio sits on it) and a chair.
    sc.add_furniture("bed", [(10, 6), (11, 6), (10, 7), (11, 7)], w=54, h=54)
    sc.add_furniture("bookshelf", [(7, 1), (8, 1)], w=58, h=18, seed=3)
    sc.add_furniture("table", [(11, 1), (12, 1)], w=54, h=34)
    sc.add_furniture("chair", [(11, 2)], w=22, h=28)
    # The computer used to live here in round 3; in round 4 it migrated to
    # church. Kid's house now reads as a child's room: a small
    # toy radio, candle, banner. No tech.
    sc.add_decoration(Decoration(11 * TILE + 16, 1 * TILE + 8, "radio"))
    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22 , "candle"))
    # Lodge dressing for a hunting-family kid: the child's own trophy
    # walleye mounted on the north wall (replacing the old pennant
    # banners), a corner cobweb, and a kerosene lamp on the table. The
    # unsettling things are tucked in the closet -- the blind spot.
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(11 * TILE + 16, 1 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(12 * TILE + 8, 1 * TILE + 16, "clock"))
    # Toby's own things, played out in secret in the closet: two corn dolls
    # on the floor where he walks them through the procession he saw. A
    # MISSING flyer for his dad -- who walked the road out for help and
    # never came back up it -- hangs out in the room.
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16, "corn_doll"))
    sc.add_decoration(Decoration(3 * TILE + 22, 3 * TILE + 16, "corn_doll"))
    sc.add_decoration(Decoration(12 * TILE + 16, 0 * TILE + 24,
                                 "missing_flyer"))
    # His mother's needlework on the north wall (moved east off the new
    # window), and the canary cage by the partition: empty, door open. The
    # bird went the way the dad did.
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 22, "sampler",
                                 seed=14))
    sc.add_decoration(Decoration(6 * TILE + 16, 2 * TILE + 8, "birdcage"))
    # Toby's WALL OF CRAYON DRAWINGS, taped up crooked across the north wall --
    # the one almost-normal room in Brimley, and that read is the point
    # (draw_toby_tableau). The walkable room had none; only the King drawing
    # hidden in the closet. Placed at varied sub-tile offsets so they break the
    # grid. The dark procession drawing joins them once toby_told (on_enter).
    sc.add_decoration(Decoration(6 * TILE + 12, 0 * TILE + 20,
                                 "crayon_drawing", motif="house"))
    sc.add_decoration(Decoration(7 * TILE + 20, 0 * TILE + 26,
                                 "crayon_drawing", motif="sun"))
    sc.add_decoration(Decoration(10 * TILE + 16, 0 * TILE + 18,
                                 "crayon_drawing", motif="family"))
    # Crayons + a half-drawn sheet on his table (the toy radio shares it).
    sc.add_decoration(Decoration(12 * TILE + 12, 1 * TILE + 16, "crayons"))
    # Chalk phantom-marks in the closet.
    sc.add_decoration(Decoration(1 * TILE + 28, 3 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(4 * TILE + 4, 2 * TILE + 16,
                                 "phantom_mark"))
    for mx, my in [(8, 7), (11, 8), (7, 8)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Hide spots: under the kid's bed (the spot sits on the bed's
    # walkable south lip; flow §25 guards every scene's spots).
    sc.hide_spots = [
        (10 * TILE + 16, 8 * TILE + 8, "under"),
    ]
    # The kid's drawing of the King, pinned up inside the closet (a 'photo'
    # decoration) -- decoration only; no interactable is wired. Out of sight from the
    # room until the player steps into the closet.
    drawing_x = 2 * TILE + 16
    drawing_y = 1 * TILE + 16
    sc.add_decoration(Decoration(drawing_x, drawing_y, "photo"))
    sc._drawing_pos = (drawing_x, drawing_y)

    sc.on_enter_fn = _toby_house_on_enter
    return sc


def _toby_house_on_enter(game, scene):
    """Once Toby has told what he saw (the photo exchange sets `toby_told`), the
    dark crayon drawing of the night procession joins the cheerful ones on his
    wall (draw_toby_tableau). The scene rebuilds each load, so re-add it every
    time the flag holds."""
    if game.save.flag("toby_told"):
        scene.add_decoration(Decoration(8 * TILE + 4, 0 * TILE + 34,
                                        "crayon_drawing", motif="procession"))
