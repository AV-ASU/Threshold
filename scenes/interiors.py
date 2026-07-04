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
from .dialogue import tisdale_boy_dialogue, hettie_dialogue, _evidence
def build_void_boss():
    """THRESHOLD: the clearing -- the BURN SITE. A small open glade off
    the brimley river bank where the claimed burned their worldly
    effects before they went below (the surface twin of the Sorting
    Hall's shed lives, NARRATIVE 1b/3): a fire pit big enough to stand
    a family around, cold now, ringed by what wouldn't burn. No pot, no
    offerings -- the claiming cult eats no one (the eat-cult imagery
    scrub); what fed this fire was luggage.

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
      - The dead fire pit at centre (9, 7), the unburnable slag
        around it.
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
    # a tree, walking onto it sends the player back to forest_path.
    objects_l[13][9] = "j"
    # Cordwood stacks (decorative -- solid table tile). Two stacks
    # so the clearing reads as a tended ritual site, not a one-prop
    # display.
    objects_l[6][2] = "t"
    objects_l[6][15] = "t"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("void_boss", floor, objects, music="wrong")
    # The clearing's south threshold now leads back to the brimley
    # river bank (where the new entrance is). Old saves' from_forest
    # / from_cornfield spawns still resolve to the same in-scene
    # position so loading is non-destructive.
    sc.add_exit("j", "brimley", "from_clearing")
    sc.set_spawn("default",        9, 11)
    sc.set_spawn("from_brimley", 9, 11)
    sc.set_spawn("from_forest",    9, 11)   # legacy alias
    sc.set_spawn("from_cornfield", 9, 11)   # legacy alias

    # The dead fire pit at centre -- scaled up so it reads as the
    # communal burn, not a campsite. Around it, what wouldn't burn:
    # bowls and effects, left where the fire spat them.
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
    # (Blood dressing removed with the eat-cult scrub -- the burn
    # site renders no one; the dread is the luggage in the ash.)
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

    pyre_x, pyre_y = 9 * TILE + 16, 7 * TILE + 16
    sc.add_interactable(pyre_x, pyre_y, 40)   # [E] cue for the fire pit
    def _void_boss_interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - pyre_x) > 40 or abs(py - pyre_y) > 40:
            return
        # Flavor narration only -- NOT one of the six canonical beats, so
        # it never touches the evidence count or the King-gate.
        _evidence(game, "the_burning",
            "A fire pit big enough to stand a family around, cold a long "
            "while. What it burned was not all wood. Buckles, bowl rims, "
            "boot eyelets, a watch case, slagged in the ash. People "
            "burned their things here. All of their things."
        )
    sc.on_interact_fn = _void_boss_interact
    return sc
def build_shop():
    """The General Store. A front shop where Hettie keeps the counter, and a
    partitioned back STOREROOM through an interior doorway -- the dividing wall
    makes it an indoor blind spot, and that's where the cult tells live (the
    mirror with the wrong silhouette, the wrong_photo), unseen from the front
    until the player steps back through the door."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWWWWWWWWWWWWWW",   # 0
        "W.....W........W",   # 1  storeroom (cols 1-5) | shop floor (cols 7-14)
        "W.....W........W",   # 2
        "W.....W........W",   # 3
        "W..............W",   # 4  doorway gap in the partition (col 6)
        "W.....W........W",   # 5
        "WWWWWWW........W",   # 6  storeroom sealed off below
        "W..............W",   # 7
        "W.........S....W",   # 8  S = Hettie, behind the counter
        "W..............W",   # 9
        "W..............W",   # 10
        "WWWWWWWWDWWWWWWW",   # 11  D = exit door back to the field
    ]
    sc = Scene("shop", floor, objects, music="home")
    # The General Store stands out on the Brimley bank now; its door
    # opens back onto the field.
    sc.add_exit("D", "brimley", "from_shop")
    sc.set_spawn("default", 7, 9)
    sc.set_spawn("from_brimley", 8, 10)      # one tile north of the D door
    sc.set_spawn("from_village", 8, 10)      # legacy fallback
    sc.set_spawn("from_town", 8, 10)         # legacy fallback

    pos = sc.consume_marker("S")
    if pos:
        tx, ty = pos
        het = NPC(tx * TILE + 16, ty * TILE + 16,
                  "Hettie", "hettie", voice="blip_high",
                  portrait="hettie",
                  dialogue_fn=hettie_dialogue, movement="worker")
        # Her JOB (GAME_CHANGES §19): the counter mostly, a pass along
        # the empty goods shelves (dusting stock that never comes), a
        # trip to the storeroom preserves through the partition door.
        het.stations = [
            {"x": tx * TILE + 16, "y": ty * TILE + 16,
             "dwell": (10.0, 16.0), "face": (0, 1)},     # the counter
            {"x": 9 * TILE + 16, "y": 2 * TILE + 16,
             "dwell": (3.0, 5.0), "face": (0, -1)},      # the bare shelves
            {"x": 3 * TILE + 16, "y": 1 * TILE + 24,
             "dwell": (4.0, 7.0), "face": (0, -1)},      # the preserves
        ]
        sc.add_npc(het)
    # Worn shop rug over the open floor -- multi-tile + off-grid to
    # break the plank tiling. First, so props draw on top.
    sc.add_decoration(Decoration(10 * TILE + 24, 9 * TILE + 8, "rug",
                                 w=104, h=64, color=(58, 60, 64), seed=31))
    # Sized darkwood furniture. The two long goods runs on the shop floor
    # stand EMPTY (bare_shelf: dust-ghosts where stock stood, one tin left;
    # no deliveries since the new year, NARRATIVE 8 food scarcity). Hettie
    # keeps a real counter now -- a low see-over volume like the Lodge
    # front desk -- plus a stool, and stocked shelves in the back room
    # (her preserves; nobody buys, so those never emptied).
    sc.add_furniture("bare_shelf", [(8, 1), (9, 1)], w=58, h=18, seed=1)
    sc.add_furniture("bare_shelf", [(11, 1), (12, 1)], w=58, h=18, seed=2)
    sc.add_furniture("butcher_counter", [(9, 9)], see_over=True)
    sc.add_furniture("butcher_counter", [(10, 9)], see_over=True)
    sc.add_furniture("chair", [(10, 8)], w=22, h=28)
    sc.add_furniture("bookshelf", [(1, 1), (2, 1)], w=58, h=18, seed=4)
    sc.add_furniture("table", [(4, 2)], w=30, h=30)
    sc.add_decoration(Decoration(9 * TILE + 16, 9 * TILE + 2, "candle"))
    # A low goods shelf finishes the north-wall run, and the wrong radio
    # sits ON it (its art is a thing on a surface; on the bare floor it
    # read as a sticker under the tilt).
    sc.add_furniture("shelf", [(13, 1)], w=28, h=16, seed=7)
    sc.add_decoration(Decoration(13 * TILE + 16, 1 * TILE + 22, "wrong_radio"))
    # Lodge dressing on the shop floor: a mounted buck + trophy walleye on
    # the north wall, a kerosene lamp on the counter. The cobweb hangs in
    # the storeroom corner.
    sc.add_decoration(Decoration(8 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(11 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(9 * TILE + 16, 9 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    # Storeroom stock: a shelf of Hettie's preserves. Nobody has bought
    # any in a while; the contents have all gone the same murky shade.
    sc.add_decoration(Decoration(3 * TILE + 16, 0 * TILE + 22,
                                 "preserve_shelf", seed=17))
    # A butter churn parked by the east wall. The dairy stopped coming
    # before the trucks did.
    sc.add_decoration(Decoration(14 * TILE + 10, 9 * TILE + 8,
                                 "butter_churn"))
    # The cult tells, hidden in the back storeroom (the blind spot): the
    # mirror that shows the wrong silhouette, and a wrong_photo on the wall.
    sc.add_decoration(Decoration(1 * TILE + 16, 3 * TILE + 16, "mirror"))
    sc.add_decoration(Decoration(4 * TILE + 16, 1 * TILE + 22,
                                 "wrong_photo", stage=1))
    sc.add_decoration(Decoration(14 * TILE + 16, 1 * TILE + 22, "clock"))
    # Hettie's calendar -- "no deliveries in a while now," the days with
    # nowhere left to count toward (stasis, not a loop -- NARRATIVE 1b).
    sc.add_decoration(Decoration(7 * TILE + 16, 0 * TILE + 24, "calendar"))
    for mx, my in [(8, 7), (12, 8), (10, 10)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    sc.hide_spots = []
    return sc
def build_barn():
    """Small barn on the brimley east bank. Holds Mara's journal
    (evidence #2) behind the workbench, and a boarded-over hatch where a
    tunnel down to the Works once ran -- nailed shut now; the rite (the
    grove's descent fold) is the only way underground, and no hatch ever
    will be again. Lodge dressing (mounted buck, walleye,
    antler rack, firewood) and hide spots among the hay-bale shelves."""
    floor = ["=" * 16 for _ in range(12)]
    objects = [
        "WWWWnWWWWWWWWWWW",   # 0  n = barn door (north face)
        "W........W.....W",   # 1  main floor (cols 1-8) | back stall (cols 10-14)
        "W........W.....W",   # 2
        "W..............W",   # 3  doorway gap in the partition (col 9)
        "W........W.....W",   # 4
        "W........W.....W",   # 5
        "W........WWWWWWW",   # 6  back stall sealed off below
        "W..............W",   # 7
        "W..............W",   # 8
        "W..............W",   # 9
        "W..............W",   # 10
        "WWWWWWWWWWWWWWWW",   # 11
    ]
    sc = Scene("barn", floor, objects, music="home")
    # Barn now sits deep south-east on the brimley east bank.
    sc.add_exit("n", "brimley", "from_barn")
    # The workbench (Mara's journal) and the boarded hatch both sit in the
    # back stall -- behind the partition, so they're an indoor blind spot.
    sc.set_spawn("default", 5, 8)
    sc.set_spawn("from_brimley", 4, 1)       # one tile south of n door
    sc.set_spawn("from_village", 4, 1)         # legacy fallback
    sc.set_spawn("from_well_passage", 11, 5)   # beside the hatch in the stall

    # Sized furniture: stacked hay-bale shelves out front and the workbench
    # in the back stall.
    sc.add_furniture("bookshelf", [(2, 2), (3, 2)], w=54, h=18, seed=9)
    sc.add_furniture("bookshelf", [(5, 2), (6, 2)], w=54, h=18, seed=10)
    sc.add_furniture("table", [(11, 2), (12, 2)], w=54, h=36)
    sc.add_decoration(Decoration(13 * TILE + 16, 1 * TILE + 24, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 24, "lantern"))
    sc.add_decoration(Decoration(11 * TILE + 16, 3 * TILE + 24,
                                 "bloodstain"))
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
    # The well-passage tunnel hatch -- a proper cellar_hatch sprite,
    # NOT a chest. Drawn as a wooden floor hatch with iron pull-ring;
    # the player presses E adjacent to descend. In the back stall.
    hatch_x = 12 * TILE + 16
    hatch_y = 5 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._barn_hatch_pos = (hatch_x, hatch_y)
    sc.add_interactable(hatch_x, hatch_y, 36)   # [E] cue for the sealed hatch
    # Mara's journal, stashed behind the workbench -- evidence #2.
    sc._journal_pos = (11 * TILE + 16, 3 * TILE + 16)
    # [E] cue so the player knows there's something behind the workbench.
    sc.add_interactable(sc._journal_pos[0], sc._journal_pos[1], 40)
    sc.hide_spots = []
    # Chalk doors -- the cult's drawn-door compulsion. The barn (Mara's, the
    # diggers' old quarters) is where the PI first meets the motif: one chalked
    # flat on the floor (the voice beat -- examine it) and one on the wall.
    sc.add_chalk_door(4 * TILE + 16, 9 * TILE + 16, voice="chalk_surface", seed=3)
    sc.add_chalk_door(7 * TILE + 16, 1 * TILE + 10, seed=5, wall=True)

    def _barn_interact(game):
        px, py = game.player.x, game.player.y
        # Mara's journal behind the workbench (evidence #2). Grants the
        # journal item so the page-3 inventory flashback still fires.
        jx, jy = sc._journal_pos
        if abs(px - jx) < 40 and abs(py - jy) < 40:
            if game.save.flag("evidence_maras_journal"):
                return
            game.player.inventory.add("mom_notebook", 1)
            game.audio.play("pickup_rare", 0.7)
            game.audio.play("low_pulse", 0.45)
            # File the case beat silently; the journal itself reads from the
            # kit (its entries are the item desc), not forced on pickup.
            # The log excerpts quote MARA_JOURNAL_PAGES (systems/items.py)
            # so the evidence beat and the readable journal can never
            # drift apart again: the ache, the door, the glad dig down.
            _evidence(game, "maras_journal", [
                "A notebook, shoved down behind the workbench. You know the "
                "hand. It's hers, the same as the letter.",
                "Her journal. Three leaves, in a hand that gets calmer "
                "as it goes:",
                "\"They told me grief would pass. It did not pass. It only "
                "learned my name.\"",
                "\"I have started to dream of a door. It is not "
                "frightening. It feels like being remembered.\"",
                "\"They dreamed the same door, every one of them. We are "
                "digging down to it together now. I am not lost. I have "
                "never been this close.\"",
            ], show=False)
            game.show_notice("Her journal.")
            return
        # The old tunnel down to the Works has been nailed shut: the
        # rite (the grove's descent fold) is the ONLY way underground
        # now (no secret paths).
        if (abs(px - hatch_x) < 36 and abs(py - hatch_y) < 36):
            game.audio.play("door_locked", 0.6)
    sc.on_interact_fn = _barn_interact
    return sc


def build_kid_house():
    floor = ["=" * 14 for _ in range(10)]
    objects = [
        "WWWWWWWWWWWWWW",   # 0
        "W....W.......W",   # 1  closet (cols 1-4) | the room (cols 6-12)
        "W....W.......W",   # 2
        "W............W",   # 3  doorway gap in the partition (col 5)
        "W....W.......W",   # 4
        "WWWWWW.......W",   # 5  closet sealed off below
        "W........K...W",   # 6  K = the Tisdale boy
        "W............W",   # 7
        "W............W",   # 8
        "WWWWJWWWWWWWWW",   # 9  J = exit door back to the field
    ]
    sc = Scene("kid_house", floor, objects, music="home")
    # Kid's house now sits middle-south on the brimley east bank.
    sc.add_exit("J", "brimley", "from_kid_house")
    sc.set_spawn("default", 8, 7)
    sc.set_spawn("from_brimley", 4, 8)         # one tile north of the J door
    sc.set_spawn("from_village", 4, 8)         # legacy fallback

    pos = sc.consume_marker("K")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "the Tisdale boy", "tisdale_boy", voice="blip_kid",
                       portrait="tisdale_boy",
                       dialogue_fn=tisdale_boy_dialogue, movement="idle"))
    # Sized darkwood furniture: a 2x2 kid's bed, a long bookshelf, a
    # small table (toy radio sits on it) and a chair.
    sc.add_furniture("bed", [(10, 6), (11, 6), (10, 7), (11, 7)], w=54, h=54)
    sc.add_furniture("bookshelf", [(7, 1), (8, 1)], w=58, h=18, seed=3)
    sc.add_furniture("table", [(11, 1), (12, 1)], w=54, h=34)
    sc.add_furniture("chair", [(11, 2)], w=22, h=28)
    # The computer used to live here in round 3; in round 4 it migrated to
    # old_man_house. Kid's house now reads as a child's room: a small
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
    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22 , "candle"))
    # Toby's own things, played out in secret in the closet: two corn dolls
    # on the floor where he walks them through the procession he saw. A
    # MISSING flyer for his dad -- who walked the road out for help and
    # never came back up it -- hangs out in the room.
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16, "corn_doll"))
    sc.add_decoration(Decoration(3 * TILE + 22, 3 * TILE + 16, "corn_doll"))
    sc.add_decoration(Decoration(12 * TILE + 16, 0 * TILE + 24,
                                 "missing_flyer"))
    # His mother's needlework over the bed, and the canary cage by the
    # partition: empty, door open. The bird went the way the dad did.
    sc.add_decoration(Decoration(9 * TILE + 24, 0 * TILE + 22, "sampler",
                                 seed=14))
    sc.add_decoration(Decoration(6 * TILE + 16, 2 * TILE + 8, "birdcage"))
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
    # decoration) -- examinable flavor, grants nothing. Out of sight from the
    # room until the player steps into the closet.
    drawing_x = 2 * TILE + 16
    drawing_y = 1 * TILE + 16
    sc.add_decoration(Decoration(drawing_x, drawing_y, "photo"))
    sc._drawing_pos = (drawing_x, drawing_y)

    return sc
