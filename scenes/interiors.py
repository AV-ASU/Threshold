"""Smaller interior areas: void, bandit cave, shop, easter egg room,
kid's house. Combat scenes (bandit cave, easter egg room) respawn
their standard enemy set on every entry; respawned enemies drop
nothing 85% of the time -- except on the very first easter_egg_room
visit, where every kill drops (gated by the first_easter_egg flag)."""
import math
import random
import pygame
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene, chest_interact
from .dialogue import kid_dialogue, shopkeep_dialogue, _evidence
def build_void_boss():
    """THRESHOLD: the clearing. A small open glade in the dense
    woods at the south end of the cornfield_path's secret branch.
    Cast-iron cauldron suspended on a triangular iron frame, fire
    pit dug into the earth beneath. Sigils carved into the
    surrounding stones. Charred ground spreading from the fire pit.

    Visual layout (18 wide x 14 tall):
      - Tree-wall border on every edge.
      - Worn dirt path enters from the south at col 9, widening as
        it approaches the cauldron. The path is the only break in
        an otherwise overgrown perimeter.
      - The 'j' tile at (9, 13) is the transition tree. The
        'from_*' spawns sit at (9, 11) -- two rows north of the
        threshold so the player can look around without immediately
        re-firing the exit.
      - Charred patch in cols 5-12, rows 5-8 (centre).
      - Cauldron + iron frame at centre (9, 7), bloody pile flanks
        on either side -- offerings being prepared.
      - Hanging figures in the canopy NW + NE -- visible above the
        tree wall on either side of the entrance approach.
      - Cordwood stacks at (2, 6) and (15, 6). Solid t tiles; their
        hide spots sit on the walkable tile beside each stack.
      - Cult robes (banner) hung on the west tree. Effigy dolls at
        (4, 6) and (14, 6) sitting on the charred edge.

    Hide spots are colocated with visible cover (cordwood, robes,
    iron frame) and never on a solid object's tile."""
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

    # Cast-iron cauldron + frame at centre, lit and steaming.
    sc.add_decoration(Decoration(9 * TILE + 16, 7 * TILE + 16,
                                 "cauldron", lit=True))
    # ONE bloodstain directly under the cauldron (the fire pit
    # drip), not a spatter pattern. The cauldron itself reads
    # heavy enough.
    sc.add_decoration(Decoration(9 * TILE + 16, 8 * TILE + 16,
                                 "bloodstain"))
    # ONE bloody pile flanking the cauldron -- offering being
    # prepared. Two reads as redundant.
    sc.add_decoration(Decoration(6 * TILE + 16, 7 * TILE + 16,
                                 "bloody_pile"))
    for sx, sy in [(4, 5), (13, 5), (4, 9), (13, 9), (9, 4)]:
        sc.add_decoration(Decoration(sx * TILE + 16, sy * TILE + 16,
                                     "phantom_mark"))
    # Two hanging figures in the canopy, visible behind the tree
    # wall NW and NE of the cauldron.
    sc.add_decoration(Decoration(3 * TILE + 16, 1 * TILE + 24,
                                 "hanging_figure"))
    sc.add_decoration(Decoration(15 * TILE + 16, 1 * TILE + 24,
                                 "hanging_figure"))
    # Cult robes hung on the west tree -- a banner-deco stand-in.
    sc.add_decoration(Decoration(1 * TILE + 16, 8 * TILE + 16,
                                 "banner", color=(110, 90, 50)))
    # Effigy dolls on the charred edge -- small, X-eyed, watching
    # the cauldron.
    sc.add_decoration(Decoration(4 * TILE + 16, 6 * TILE + 16, "doll"))
    sc.add_decoration(Decoration(14 * TILE + 16, 6 * TILE + 16, "doll"))
    # Claw gouges on the charred ground around the fire pit.
    sc.add_decoration(Decoration(6 * TILE + 16, 5 * TILE + 22,
                                 "claw_marks"))
    sc.add_decoration(Decoration(11 * TILE + 16, 5 * TILE + 22,
                                 "claw_marks"))
    # (Bloody handprint trail removed -- the cordwood + dolls +
    # bloody pile already read clearly. The cauldron site shouldn't
    # be wallpapered in blood marks.)
    # Path-side candles framing the entrance threshold.
    sc.add_decoration(Decoration(8 * TILE + 4, 12 * TILE + 22, "candle"))
    sc.add_decoration(Decoration(10 * TILE + 28, 12 * TILE + 22, "candle"))
    # Two crows in the tree line.
    sc.add_decoration(Decoration(2 * TILE + 8, 1 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(15 * TILE + 8, 1 * TILE + 22, "crow"))
    # Dead crow on the path -- the cult feeds them to the fire too.
    sc.add_decoration(Decoration(9 * TILE + 16, 10 * TILE + 22,
                                 "dead_crow"))
    # Motes for ambient particles.
    for i in range(8):
        sc.add_decoration(Decoration(40 + i * 50,
                                     60 + (i % 3) * 50, "mote"))

    # Hide spots colocated with VISIBLE cover. Each spot lands on
    # an open walkable tile directly beside the cover prop -- never
    # ON the prop itself, so leaving cover doesn't clip the player
    # into a solid tile.
    sc.hide_spots = [
        (3 * TILE + 16, 6 * TILE + 16, "behind"),    # beside W cordwood
        (14 * TILE + 16, 6 * TILE + 16, "behind"),   # beside E cordwood
        (1 * TILE + 16, 9 * TILE + 16, "behind"),    # beside cult robes
        (5 * TILE + 16, 7 * TILE + 16, "behind"),    # beside W bloody pile
    ]

    # Tag the scene as the clearing for the flashback / patrol systems.
    sc.is_clearing = True

    cauldron_x, cauldron_y = 9 * TILE + 16, 7 * TILE + 16
    def _void_boss_interact(game):
        px, py = game.player.x, game.player.y
        if abs(px - cauldron_x) > 40 or abs(py - cauldron_y) > 40:
            return
        _evidence(game, "the_cauldron",
            "Nothing here."
        )
    sc.on_interact_fn = _void_boss_interact
    return sc
def build_shop():
    floor = ["=" * 12 for _ in range(8)]
    objects = [
        "WWWWWWWWWWWW",
        "W..........W",
        "W..ss..ss..W",
        "W..........W",
        "W..t.S.....W",   # S = shopkeep marker (behind the counter table)
        "W..c.......W",
        "W.....D....W",
        "WWWWWWWWWWWW",
    ]
    sc = Scene("shop", floor, objects, music="home")
    # The General Store stands out on the Brimley bank now; its door
    # opens back onto the field.
    sc.add_exit("D", "brimley", "from_shop")
    sc.set_spawn("default", 6, 5)
    sc.set_spawn("from_brimley", 5, 6)       # arrive from Brimley
    sc.set_spawn("from_village", 5, 6)         # legacy fallback
    sc.set_spawn("from_town", 5, 6)            # legacy fallback

    pos = sc.consume_marker("S")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Store-Owner", "shopkeep", voice="blip_high",
                       portrait="shopkeep",
                       dialogue_fn=shopkeep_dialogue, movement="idle"))
    # Shop dressing: a candle on the counter, a radio on the back
    # shelf (use the wrong_radio variant -- it creeps the dial), a
    # hanging sign banner over the door, two crows behind the
    # window glass, a single mirror on the east wall (the wrong
    # silhouette in the glass is the cult tell), a clock that
    # stopped, motes for atmosphere, and a wrong_photo on the
    # back wall.
    # Worn shop rug over the open floor -- multi-tile + off-grid to
    # break the plank tiling. First, so props draw on top.
    sc.add_decoration(Decoration(7 * TILE + 24, 4 * TILE + 8, "rug",
                                 w=104, h=64, color=(58, 60, 64), seed=31))
    # Sized darkwood furniture: two long shop bookshelves of goods, the
    # counter table, a stool behind it.
    sc.add_furniture("bookshelf", [(3, 2), (4, 2)], w=58, h=18, seed=1)
    sc.add_furniture("bookshelf", [(7, 2), (8, 2)], w=58, h=18, seed=2)
    sc.add_furniture("table", [(3, 4), (4, 4)], w=58, h=38)
    sc.add_furniture("chair", [(3, 5)], w=22, h=28)
    sc.add_decoration(Decoration(6 * TILE + 16, 2 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16, "wrong_radio"))
    # Lodge dressing: a mounted buck + trophy walleye on the north wall
    # (the old hanging shop banner is gone -- this is hunting/fishing
    # country), a kerosene lamp on the counter, and a cobweb in the NW
    # corner. The mirror + wrong_photo cult tells stay.
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(9 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(4 * TILE + 16, 4 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(10 * TILE + 16, 4 * TILE + 16, "mirror"))
    sc.add_decoration(Decoration(8 * TILE + 16, 1 * TILE + 22, "clock"))
    sc.add_decoration(Decoration(4 * TILE + 16, 1 * TILE + 22,
                                 "wrong_photo", stage=1))
    for mx, my in [(7, 4), (9, 5), (5, 5)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Hide spots colocated with cover (beside shelves / counter).
    sc.hide_spots = [
        (4 * TILE + 16, 4 * TILE + 16, "behind"),   # beside counter
        (4 * TILE + 16, 2 * TILE + 16, "behind"),   # beside W shelf
        (8 * TILE + 16, 2 * TILE + 16, "behind"),   # beside E shelf
    ]
    return sc
def build_barn():
    """Small barn on the brimley east bank. Holds Mara's journal
    (evidence #2) behind the workbench, and a boarded-over hatch where a
    tunnel down to the Works once ran -- nailed shut now, since the well
    is the only way underground. Lodge dressing (mounted buck, walleye,
    antler rack, firewood) and hide spots among the hay-bale shelves."""
    floor = ["=" * 10 for _ in range(8)]
    objects = [
        "WWWWnWWWWW",   # 0  n = barn door (north face)
        "W........W",   # 1
        "W..s..s..W",   # 2  shelves stand in for stacked hay bales
        "W........W",   # 3
        "W........W",   # 4
        "W..t.....W",   # 5  workbench
        "W........W",   # 6
        "WWWWWWWWWW",   # 7
    ]
    sc = Scene("barn", floor, objects, music="home")
    # Barn now sits deep south-east on the brimley east bank.
    sc.add_exit("n", "brimley", "from_barn")
    # Round-13: tunnel from the barn down to the well_passage. A
    # ladder hatch tile in the back of the barn (col 8, row 6).
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_brimley", 4, 1)       # one tile south of n door
    sc.set_spawn("from_village", 4, 1)         # legacy fallback
    sc.set_spawn("from_well_passage", 7, 6)    # one tile west of the hatch

    # Sized furniture: stacked hay-bale shelves and a workbench.
    sc.add_furniture("bookshelf", [(2, 2), (3, 2)], w=54, h=18, seed=9)
    sc.add_furniture("bookshelf", [(5, 2), (6, 2)], w=54, h=18, seed=10)
    sc.add_furniture("table", [(3, 5), (4, 5)], w=54, h=36)
    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 24, "lantern"))
    sc.add_decoration(Decoration(4 * TILE + 16, 5 * TILE + 24,
                                 "bloodstain"))
    # Northern-MN lodge dressing: a mounted buck + trophy walleye on the
    # north wall, cobwebs in the high corners, an antler coat-rack on
    # the east wall, and a split-wood stack in the SW corner. The floor
    # pieces are collision furniture, tucked clear of the hatch + spawn
    # paths so the room stays passable.
    sc.add_decoration(Decoration(6 * TILE + 16, 0 * TILE + 22, "buck_head",
                                 wall="N"))
    sc.add_decoration(Decoration(2 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(1 * TILE + 6, 1 * TILE + 6, "cobweb",
                                 ang=0.0))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_furniture("antler_rack", [(8, 4)], w=22, h=46)
    sc.add_furniture("firewood", [(1, 5), (1, 6)], w=24, h=58)
    # The well-passage tunnel hatch -- a proper cellar_hatch sprite,
    # NOT a chest. Drawn as a wooden floor hatch with iron pull-ring;
    # the player presses E adjacent to descend.
    hatch_x = 8 * TILE + 16
    hatch_y = 6 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._barn_hatch_pos = (hatch_x, hatch_y)
    # Mara's journal, stashed behind the workbench -- evidence #2.
    sc._journal_pos = (3 * TILE + 16, 5 * TILE + 16)
    # Hide spots colocated with cover -- behind the hay-bale shelves
    # (player stands on a walkable tile beside each shelf, NOT on the
    # solid shelf tile). The under-workbench spot was previously on
    # the chest; now sits beside the workbench.
    sc.hide_spots = [
        (4 * TILE + 16, 2 * TILE + 16, "behind"),   # beside W shelf
        (7 * TILE + 16, 2 * TILE + 16, "behind"),   # beside E shelf
        (4 * TILE + 16, 5 * TILE + 16, "under"),    # beside workbench
    ]

    def _barn_interact(game):
        px, py = game.player.x, game.player.y
        # Mara's journal behind the workbench (evidence #2). Grants the
        # journal item so the page-3 inventory flashback still fires.
        jx, jy = sc._journal_pos
        if abs(px - jx) < 40 and abs(py - jy) < 40:
            if game.save.flag("evidence_maras_journal"):
                game.show_notice("You have her journal. Read it again from "
                                 "your kit.")
                return
            game.player.inventory.add("mom_notebook", 1)
            game.audio.play("pickup_rare", 0.7)
            game.audio.play("low_pulse", 0.45)
            _evidence(game, "maras_journal", [
                "A notebook, shoved down behind the workbench. You know the "
                "hand -- it's hers, the same as the letter.",
                "Her journal. The last entries, in a hand that gets calmer "
                "as it goes:",
                "\"I just had this urge to go north. Stopped for gas in this "
                "town. Everyone smiles like I'm already home.\"",
                "\"I had Him wrong. He isn't out past the corn -- He's under "
                "it. You don't walk to Him. You go down.\"",
                "\"There's a mouth below the town. The others went ahead of "
                "me, down it, and not one has climbed back up. Tomorrow I "
                "follow them down. I feel so close now.\"",
            ])
            return
        # The old tunnel down to the Works has been nailed shut: the
        # well is the ONLY way underground now (no secret paths).
        if (abs(px - hatch_x) < 36 and abs(py - hatch_y) < 36):
            game.audio.play("door_locked", 0.6)
            game.show_notice("Boarded over and nailed shut from below.")
    sc.on_interact_fn = _barn_interact
    return sc


def build_kid_house():
    floor = ["=" * 10 for _ in range(8)]
    objects = [
        "WWWWWWWWWW",
        "W........W",
        "W..t..s..W",
        "W..c.....W",
        "W..K.....W",   # K = kid marker
        "W..b.....W",
        "W....J...W",
        "WWWWWWWWWW",
    ]
    sc = Scene("kid_house", floor, objects, music="home")
    # Kid's house now sits middle-south on the brimley east bank.
    sc.add_exit("J", "brimley", "from_kid_house")
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_brimley", 4, 6)
    sc.set_spawn("from_village", 4, 6)         # legacy fallback

    pos = sc.consume_marker("K")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Village Kid", "kid", voice="blip_kid",
                       portrait="kid",
                       dialogue_fn=kid_dialogue, movement="idle"))
    # Sized darkwood furniture: a 2x2 kid's bed, a long bookshelf, a
    # small table (toy radio sits on it) and a chair.
    sc.add_furniture("bed", [(2, 5), (3, 5), (2, 6), (3, 6)], w=54, h=54)
    sc.add_furniture("bookshelf", [(5, 2), (6, 2)], w=58, h=18, seed=3)
    sc.add_furniture("table", [(2, 2), (3, 2)], w=54, h=34)
    sc.add_furniture("chair", [(3, 3)], w=22, h=28)
    # The computer used to live here in round 3; in round 4 it migrated to
    # old_man_house. Kid's house now reads as a child's room: a small
    # toy radio, candle, banner. No tech.
    sc.add_decoration(Decoration(3 * TILE + 16, 2 * TILE + 8, "radio"))
    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22 , "candle"))
    # Lodge dressing for a hunting-family kid: the child's own trophy
    # walleye mounted on the north wall (replacing the old pennant
    # banners), a corner cobweb, and a kerosene lamp on the table. The
    # wall-mounted kid's drawing (a 'photo' pickup) stays -- it's lore.
    sc.add_decoration(Decoration(4 * TILE + 16, 0 * TILE + 24,
                                 "mounted_fish"))
    sc.add_decoration(Decoration(8 * TILE + 26, 1 * TILE + 6, "cobweb",
                                 ang=math.pi / 2))
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 2,
                                 "kerosene_lamp"))
    sc.add_decoration(Decoration(8 * TILE + 8, 2 * TILE + 16, "clock"))
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
    # Chalk phantom-marks on the walls.
    sc.add_decoration(Decoration(1 * TILE + 28, 2 * TILE + 16,
                                 "phantom_mark"))
    sc.add_decoration(Decoration(8 * TILE + 4, 4 * TILE + 16,
                                 "phantom_mark"))
    for mx, my in [(5, 3), (6, 4), (4, 5)]:
        sc.add_decoration(Decoration(mx * TILE + 16, my * TILE + 16,
                                     "mote"))
    # Hide spots: under the kid's bed, behind the shelf.
    sc.hide_spots = [
        (3 * TILE + 16, 5 * TILE + 24, "under"),
        (7 * TILE + 16, 2 * TILE + 24, "behind"),
    ]
    # The kid's drawing on the wall (a 'photo' decoration) -- examinable
    # flavor, grants nothing.
    drawing_x = 6 * TILE + 16
    drawing_y = 1 * TILE + 16
    sc.add_decoration(Decoration(drawing_x, drawing_y, "photo"))
    sc._drawing_pos = (drawing_x, drawing_y)

    def _kid_house_interact(game):
        # The kid's drawing on the wall -- flavor lore, examinable only.
        if (abs(game.player.x - drawing_x) < 36
                and abs(game.player.y - drawing_y) < 36):
            game.show_notice("A child's drawing pinned to the wall: a tall "
                             "figure in yellow, the people lifted toward it.")
    sc.on_interact_fn = _kid_house_interact
    return sc
