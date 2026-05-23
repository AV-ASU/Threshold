"""Smaller interior areas: void, bandit cave, shop, easter egg room,
kid's house. Combat scenes (bandit cave, easter egg room) respawn
their standard enemy set on every entry; respawned enemies drop
nothing 85% of the time -- except on the very first easter_egg_room
visit, where every kill drops (gated by the first_easter_egg flag)."""
import random
import pygame
from constants import TILE
from entities.npc import NPC
from entities.decoration import Decoration
from .base import Scene, chest_interact
from .dialogue import (
    static_figure_dialogue, doll_dialogue,
    kid_dialogue, shopkeep_dialogue, _evidence,
)


def build_void():
    """Round-5 redesign: the void is empty substrate. Two items the
    player came for sit in a single chest (round-11: previously they
    were floor pickups, which respawned every entry). Opening the
    chest sets a save flag so the loot stays one-shot."""
    floor = ["@" * 22 for _ in range(16)]
    objects_l = [["." for _ in range(22)] for _ in range(16)]
    objects_l[8][1] = "B"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("void", floor, objects, music="void")
    sc.add_exit("B", "forest_path", "from_void")
    sc.set_spawn("default", 4, 8)
    sc.set_spawn("from_forest", 4, 8)

    chest_x = 19 * TILE + 16
    chest_y = 8 * TILE + 16
    sc.add_decoration(Decoration(chest_x, chest_y, "chest", open=False))
    sc._void_chest_pos = (chest_x, chest_y)

    sc.on_enter_fn = void_on_enter
    sc.on_interact_fn = void_interact
    return sc


def void_interact(game):
    cx, cy = getattr(game.scene, "_void_chest_pos", (None, None))
    if cx is not None:
        chest_interact(game, game.scene, cx, cy,
                       "chest_void", ["easter_egg", "rust_key"])


def void_on_enter(game, scene):
    """Round-7: no surfaceable notification. The 'this isn't on the map'
    dialog is gone -- the player should feel they've slid sideways out
    of the world without the game pointing it out. The first-time
    evidence file still drops silently in the .archive/ folder."""
    game.audio.force_silence(duration_s=2)
    if not game.save.arg("found_oob_void"):
        game.save.set_arg("found_oob_void", True)
        _evidence(game, "geometry_violation",
            "There is a tree you can walk through."
        )


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
    # The clearing's south threshold now leads back to the mistlands
    # river bank (where the new entrance is). Old saves' from_forest
    # / from_cornfield spawns still resolve to the same in-scene
    # position so loading is non-destructive.
    sc.add_exit("j", "mistlands", "from_clearing")
    sc.set_spawn("default",        9, 11)
    sc.set_spawn("from_mistlands", 9, 11)
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


def _spawn_bandit_cave_enemies(scene, respawning=False):
    from entities.enemy import Enemy
    bandits = [
        Enemy(4 * TILE + 16, 4 * TILE + 16,
              kind="bandit", hp=40, atk=11, speed=1.5,
              drops=["short_sword"]),
        Enemy(10 * TILE + 16, 4 * TILE + 16,
              kind="bandit", hp=40, atk=11, speed=1.5,
              drops=["potion_red"]),
        Enemy(7 * TILE + 16, 2 * TILE + 16,
              kind="bandit", hp=64, atk=16, speed=1.6,
              drops=["bandit_axe", "iron_armor"]),
    ]
    for b in bandits:
        b.respawning = respawning
        scene.add_enemy(b)


def build_bandit_cave():
    """Main cave room. Round-5 expansion: doors in three walls connect to
    sub-rooms (north -> boss, west -> stash, east -> stash). Bandits
    respawn here on every entry, drop-gated 85% empty."""
    floor = ["x" * 14 for _ in range(12)]
    objects_l = []
    for y in range(12):
        if y == 0 or y == 11:
            objects_l.append(list("#" * 14))
        else:
            row = ["#"] + ["."] * 12 + ["#"]
            objects_l.append(row)
    objects_l[11][7] = "F"      # south: back to forest_path
    objects_l[0][7] = "u"       # north: into boss room
    objects_l[5][0] = "w"       # west wall door
    objects_l[5][13] = "v"      # east wall door
    objects = ["".join(r) for r in objects_l]
    sc = Scene("bandit_cave", floor, objects, music="cave")
    sc.combat = True
    sc.add_exit("F", "forest_path",        "from_cave")
    sc.add_exit("u", "bandit_cave_boss",   "from_cave")
    sc.add_exit("w", "bandit_cave_west",   "from_cave")
    sc.add_exit("v", "bandit_cave_east",   "from_cave")
    sc.set_spawn("default",     7, 10)
    sc.set_spawn("from_forest", 7, 10)
    sc.set_spawn("from_boss",   7,  1)     # one tile south of u
    sc.set_spawn("from_west",   1,  5)     # one tile east of w
    sc.set_spawn("from_east",   12, 5)     # one tile west of v
    # Loot moved off the floor and into a chest at the back of the
    # room (round-9). The chest is not locked -- standard E-interact
    # opens it; loot doesn't respawn.
    chest_x = 7 * TILE + 16
    chest_y = 2 * TILE + 16 + 24
    sc.add_decoration(Decoration(chest_x, chest_y, "chest", open=False))
    sc._cave_chest_pos = (chest_x, chest_y)
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(11 * TILE + 16, 2 * TILE + 16, "candle"))
    sc.on_enter_fn = bandit_cave_on_enter
    sc.on_interact_fn = bandit_cave_interact
    return sc


def bandit_cave_on_enter(game, scene):
    """Re-spawn bandits on every entry. Drop-gated 85% empty. Also
    sync the chest decoration's open-visual to the save flag."""
    scene.enemies = []
    _spawn_bandit_cave_enemies(scene, respawning=True)
    for deco in scene.decorations:
        if deco.kind == "chest":
            deco.kwargs["open"] = game.save.flag("chest_cave_main")


def bandit_cave_interact(game):
    cx, cy = getattr(game.scene, "_cave_chest_pos", (None, None))
    if cx is not None:
        chest_interact(game, game.scene, cx, cy,
                       "chest_cave_main", ["potion_clear"])


def _spawn_west_stash_enemy(scene):
    from entities.enemy import Enemy
    e = Enemy(4 * TILE + 16, 3 * TILE + 16,
              kind="bandit", hp=34, atk=10, speed=1.5,
              drops=["bread"])
    e.respawning = True
    scene.add_enemy(e)


def build_bandit_cave_west():
    floor = ["x" * 7 for _ in range(6)]
    objects = [
        "#######",
        "#.....#",
        "#.....#",
        "#.....w",
        "#.....#",
        "#######",
    ]
    sc = Scene("bandit_cave_west", floor, objects, music="cave")
    sc.combat = True
    sc.add_exit("w", "bandit_cave", "from_west")
    sc.set_spawn("default",   5, 3)
    sc.set_spawn("from_cave", 5, 3)        # one tile west of w
    # Loot in a chest, not on the floor (round-9). Unlocked.
    chest_x = 2 * TILE + 16
    chest_y = 2 * TILE + 16
    sc.add_decoration(Decoration(chest_x, chest_y, "chest", open=False))
    sc._west_chest_pos = (chest_x, chest_y)
    sc.add_decoration(Decoration(4 * TILE + 16,  0 * TILE + 22 , "candle"))
    # Red herring: a small chalk mark on the back wall. Looks like a
    # symbol from the void. Means nothing.
    sc.add_decoration(Decoration(3 * TILE + 16, 1 * TILE + 18, "phantom_mark"))

    def _on_enter(g, s):
        s.enemies.clear()
        _spawn_west_stash_enemy(s)
        for deco in s.decorations:
            if deco.kind == "chest":
                deco.kwargs["open"] = g.save.flag("chest_cave_west")

    def _on_interact(g):
        cx, cy = getattr(g.scene, "_west_chest_pos", (None, None))
        if cx is not None:
            chest_interact(g, g.scene, cx, cy,
                           "chest_cave_west", ["potion_red"])

    sc.on_enter_fn = _on_enter
    sc.on_interact_fn = _on_interact
    return sc


def _spawn_east_stash_enemy(scene):
    from entities.enemy import Enemy
    e = Enemy(4 * TILE + 16, 3 * TILE + 16,
              kind="bandit", hp=34, atk=10, speed=1.5,
              drops=["short_sword"])
    e.respawning = True
    scene.add_enemy(e)


def build_bandit_cave_east():
    floor = ["x" * 7 for _ in range(6)]
    objects = [
        "#######",
        "#.....#",
        "#.....#",
        "v.....#",
        "#.....#",
        "#######",
    ]
    sc = Scene("bandit_cave_east", floor, objects, music="cave")
    sc.combat = True
    sc.add_exit("v", "bandit_cave", "from_east")
    sc.set_spawn("default",   1, 3)
    sc.set_spawn("from_cave", 1, 3)        # one tile east of v
    # Round-9: floor loot replaced with two unlocked chests, one for
    # the bread, one for the brass_key. Each has its own save flag.
    chest_a = (5 * TILE + 16, 2 * TILE + 16)
    chest_b = (2 * TILE + 16, 2 * TILE + 16)
    sc.add_decoration(Decoration(*chest_a, "chest", open=False))
    sc.add_decoration(Decoration(*chest_b, "chest", open=False))
    sc._east_chest_a = chest_a
    sc._east_chest_b = chest_b
    # Red herrings: a chalk symbol scratched on the wall + a phantom
    # mark on the cave floor. Neither leads anywhere -- they're bait
    # for ARG players to chase.
    sc.add_decoration(Decoration(3 * TILE + 16, 4 * TILE + 16, "phantom_mark"))
    sc.add_decoration(Decoration(5 * TILE + 16,  0 * TILE + 22 , "candle"))

    def _on_enter(g, s):
        s.enemies.clear()
        _spawn_east_stash_enemy(s)
        # Sync chest visuals to flags
        flags = {chest_a: "chest_cave_east_bread",
                 chest_b: "chest_cave_east_key"}
        for deco in s.decorations:
            if deco.kind != "chest":
                continue
            for (cx, cy), flag in flags.items():
                if abs(deco.x - cx) < 4 and abs(deco.y - cy) < 4:
                    deco.kwargs["open"] = g.save.flag(flag)
                    break

    def _on_interact(g):
        cx, cy = g.scene._east_chest_a
        if chest_interact(g, g.scene, cx, cy,
                          "chest_cave_east_bread", ["bread"]):
            return
        cx, cy = g.scene._east_chest_b
        if chest_interact(g, g.scene, cx, cy,
                          "chest_cave_east_key", ["brass_key"]):
            return

    sc.on_enter_fn = _on_enter
    sc.on_interact_fn = _on_interact
    return sc


def _on_policeman_kill(game):
    """Boss-kill side effect: generate the user_code on the first kill
    and add the policeman's Badge to the player's inventory. The badge
    item description surfaces the code (e.g. 'Rusted. D-234') via
    effective_desc(), so the player reads the credential out of their
    pack and types it into the LOGIN terminal.

    Round-9: replaces the round-8 evidence drop. The credential is no
    longer narrated by the substrate -- it's a physical artefact in
    the world."""
    if game.save.arg("user_code") is not None:
        return
    digits = "".join(random.choice("0123456789") for _ in range(3))
    # Stored in the lowercase d-### form to match the Badge surface
    # text; the LOGIN terminal compares case-insensitively and accepts
    # any string whose digit-run matches the saved digits.
    code = f"d-{digits}"
    game.save.set_arg("user_code", code)
    game.player.inventory.add("badge", 1)
    game.audio.play("pickup_rare", 0.7)
    game.show_notice("Got: Badge.")


def _spawn_boss(scene):
    from entities.enemy import Enemy
    # Round-9: renamed Foreman -> Policeman, sprite swapped to a navy
    # uniform with a gold badge on the chest. HP stays at 160 (doubled
    # in round-9). Drops the same arsenal but the badge is delivered
    # via on_kill (added to inventory) so the credential is in pocket
    # rather than in evidence.
    boss = Enemy(4 * TILE + 16, 3 * TILE + 16,
                 kind="policeman", hp=160, atk=11, speed=1.3,
                 aggro=180, atk_range=22,
                 drops=["iron_armor"],
                 can_shoot=True, shoot_cd=1.6, shoot_dmg=14,
                 shoot_range=260,
                 projectile_color=(255, 240, 180),
                 projectile_speed=320,
                 shoot_sfx="pistol_shot",
                 on_kill=_on_policeman_kill)
    # Boss drops always fire (bypasses the 85% suppression). Killing him
    # is the gate that creates the LOGIN code, so the loot pop must be
    # certain.
    boss.respawning = False
    scene.add_enemy(boss)


def build_bandit_cave_boss():
    floor = ["x" * 10 for _ in range(8)]
    objects = [
        "##&#######",   # 0  & = fake stone wall to the void_boss arena
        "#........#",   # 1
        "#........#",   # 2
        "#........#",   # 3
        "#........#",   # 4
        "#........#",   # 5
        "#........#",   # 6
        "####u#####",   # 7  u = exit back to bandit_cave
    ]
    sc = Scene("bandit_cave_boss", floor, objects, music="cave")
    sc.combat = True
    sc.add_exit("u", "bandit_cave", "from_boss")
    # The & exit is gated by bandit_cave_boss_on_enter: when the player
    # lacks the broken_crutch or has already won/died at the void boss,
    # the on_enter swaps the tile back to "#" (solid) so the exit cannot
    # be reached. The dict mapping is kept either way -- tile is what
    # gates access, not the exits dict.
    sc.add_exit("&", "void_boss",   "from_cave_boss")
    sc.set_spawn("default",   4, 6)
    sc.set_spawn("from_cave", 4, 6)        # one tile north of u
    sc.add_decoration(Decoration(2 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.on_enter_fn = bandit_cave_boss_on_enter
    return sc


def bandit_cave_boss_on_enter(game, scene):
    """Spawn the bandit foreman on every entry until the user_code has
    been generated. After the first kill, the foreman half of the room
    is empty -- the credential is one-time.

    Round-9: also gate the secret fake stone wall on the north face
    that leads to the void_boss arena. The wall is only kept passable
    while the player carries the broken_crutch AND has not yet won or
    died at the void boss. After resolution the wall is sealed back to
    a normal "#" forever, so the boss arena stays one-shot."""
    scene.enemies = []
    if game.save.arg("user_code") is None:
        _spawn_boss(scene)
    has_crutch = game.player.inventory.has("broken_crutch")
    void_resolved = (game.save.flag("void_boss_won")
                     or game.save.flag("void_path_closed"))
    open_path = has_crutch and not void_resolved
    # The & sits at row 0, col 2 in the build. Flip it directly each
    # entry: passable & if conditions hold, solid # otherwise. Even if
    # a previous entry already swapped it, this is idempotent.
    scene.objects[0][2] = "&" if open_path else "#"


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
    # General store now opens onto the town street.
    sc.add_exit("D", "town", "from_shop")
    sc.set_spawn("default", 6, 5)
    sc.set_spawn("from_mistlands", 5, 6)       # legacy fallback
    sc.set_spawn("from_village", 5, 6)         # legacy fallback
    sc.set_spawn("from_town", 5, 6)            # arrive from the town street

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
    sc.add_decoration(Decoration(6 * TILE + 16, 2 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 2 * TILE + 16, "wrong_radio"))
    sc.add_decoration(Decoration(7 * TILE + 16, 6 * TILE + 22,
                                 "banner", color=(140, 100, 60)))
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


def _spawn_easter_egg_enemies(scene, respawning=False):
    from entities.enemy import Enemy
    # Round-10: doll enemies returned to this room (round-9 had moved
    # them to the barn; the user kept the dolls here and only the
    # old_doll *item* lives in the barn chest now). Three kids + two
    # dolls + one bandit, same wave the room ran in earlier rounds.
    enemies = [
        Enemy(3 * TILE + 16, 3 * TILE + 16, kind="kid",
              hp=18, atk=7, speed=1.7, drops=["bread"]),
        Enemy(7 * TILE + 16, 3 * TILE + 16, kind="kid",
              hp=18, atk=7, speed=1.7),
        Enemy(11 * TILE + 16, 3 * TILE + 16, kind="kid",
              hp=18, atk=7, speed=1.7),
        Enemy(5 * TILE + 16, 6 * TILE + 16, kind="doll",
              hp=24, atk=9, speed=1.5, drops=["potion_red"]),
        Enemy(9 * TILE + 16, 6 * TILE + 16, kind="doll",
              hp=24, atk=9, speed=1.5),
        Enemy(7 * TILE + 16, 1 * TILE + 16, kind="bandit",
              hp=90, atk=14, speed=1.3, drops=["old_pistol", "iron_armor"]),
    ]
    for e in enemies:
        e.respawning = respawning
        scene.add_enemy(e)


def build_easter_egg_room():
    floor = ["," * 16 for _ in range(12)]
    objects_l = []
    for y in range(12):
        if y == 0 or y == 11:
            objects_l.append(list("W" * 16))
        else:
            row = ["W"] + ["."] * 14 + ["W"]
            objects_l.append(row)
    objects_l[11][7] = "U"
    objects = ["".join(r) for r in objects_l]
    sc = Scene("easter_egg_room", floor, objects, music="easter")
    sc.combat = True
    sc.add_exit("U", "bedroom", "from_easter")
    sc.set_spawn("default", 7, 10)
    sc.set_spawn("from_bedroom", 7, 10)

    for px in range(3, 14, 3):
        sc.add_decoration(Decoration(px * TILE + 16,  0 * TILE + 22 , "candle"))
        sc.add_decoration(Decoration(px * TILE + 16, 10 * TILE + 8, "candle"))
    sc.add_decoration(Decoration(7 * TILE + 16, 1 * TILE + 16, "banner",
                                 color=(220, 200, 60)))
    sc.on_enter_fn = easter_egg_on_enter
    return sc


def easter_egg_on_enter(game, scene):
    """Re-spawn the wave on every entry. Drops are guaranteed on the
    first-ever entry (respawning=False); subsequent visits use the
    standard 85% drop-suppression rule (respawning=True).

    Round-9: dolls moved to the barn, so the named-doll loot path and
    the polaroid-on-entry evidence drop are gone from this scene. The
    daughter_room transformation now triggers off the barn chest
    pickup instead."""
    scene.enemies = []
    first_visit = not game.save.flag("first_easter_egg")
    if first_visit:
        game.save.set_flag("first_easter_egg", True)
    _spawn_easter_egg_enemies(scene, respawning=not first_visit)
    game.show_notice("...?")


def build_barn():
    """Small barn south of the village square. Three wolves prowl
    inside on first entry; killing them all flags the guard outside
    the player's house as dead. The first wolf carries a slobbery_key
    that opens the locked chest at the back of the barn -- inside is
    the old_doll (round-9 move from easter_egg_room). Two doll enemies
    also live here now, perched among the bales. Wolves + dolls do
    NOT respawn -- one-shot encounter."""
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
    # Barn now sits deep south-east on the mistlands east bank.
    sc.add_exit("n", "mistlands", "from_barn")
    # Round-13: tunnel from the barn down to the well_passage. A
    # ladder hatch tile in the back of the barn (col 8, row 6).
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_mistlands", 4, 1)       # one tile south of n door
    sc.set_spawn("from_village", 4, 1)         # legacy fallback
    sc.set_spawn("from_well_passage", 7, 6)    # one tile west of the hatch

    sc.add_decoration(Decoration(7 * TILE + 16, 5 * TILE + 16, "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 1 * TILE + 24, "lantern"))
    sc.add_decoration(Decoration(4 * TILE + 16, 5 * TILE + 24,
                                 "bloodstain"))
    # The well-passage tunnel hatch -- a proper cellar_hatch sprite,
    # NOT a chest. Drawn as a wooden floor hatch with iron pull-ring;
    # the player presses E adjacent to descend.
    hatch_x = 8 * TILE + 16
    hatch_y = 6 * TILE + 16
    sc.add_decoration(Decoration(hatch_x, hatch_y, "cellar_hatch"))
    sc._barn_hatch_pos = (hatch_x, hatch_y)
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
        if (abs(game.player.x - hatch_x) < 36
                and abs(game.player.y - hatch_y) < 36):
            game.audio.play("door_open", 0.6)
            game.show_notice("You climb down into the dark.")
            game.begin_transition("well_passage", "from_barn")
    sc.on_interact_fn = _barn_interact
    return sc


# THRESHOLD: combat is gone, so the barn no longer hosts the
# wolf encounter and the daughter-room doll quest doesn't surface
# from a chest in the back. The functions that drove that flow
# (`barn_on_enter`, `barn_interact`, `_spawn_barn_wolves`,
# `_wolf_killed`, `_barn_go_dirty`) were dead code -- never wired
# into the scene -- and have been removed. The barn is now just
# the well-passage hatch room.


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
    # Kid's house now sits middle-south on the mistlands east bank.
    sc.add_exit("J", "mistlands", "from_kid_house")
    sc.set_spawn("default", 5, 5)
    sc.set_spawn("from_mistlands", 4, 6)
    sc.set_spawn("from_village", 4, 6)         # legacy fallback

    pos = sc.consume_marker("K")
    if pos:
        tx, ty = pos
        sc.add_npc(NPC(tx * TILE + 16, ty * TILE + 16,
                       "Village Kid", "kid", voice="blip_kid",
                       portrait="kid",
                       dialogue_fn=kid_dialogue, movement="idle"))
    # The computer used to live here in round 3; in round 4 it migrated to
    # old_man_house. Kid's house now reads as a child's room: a small
    # toy radio, candle, banner. No tech.
    sc.add_decoration(Decoration(3 * TILE + 16, 2 * TILE + 8, "radio"))
    sc.add_decoration(Decoration(7 * TILE + 16,  0 * TILE + 22 , "candle"))
    sc.add_decoration(Decoration(2 * TILE + 16, 5 * TILE + 16, "banner",
                                 color=(140, 60, 70)))
    sc.add_decoration(Decoration(8 * TILE + 16, 5 * TILE + 16, "banner",
                                 color=(220, 180, 70)))
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
    # The kid's drawing pickup -- on the wall (visually a 'photo'
    # decoration), takeable on first interaction.
    drawing_x = 6 * TILE + 16
    drawing_y = 1 * TILE + 16
    sc.add_decoration(Decoration(drawing_x, drawing_y, "photo"))
    sc._drawing_pos = (drawing_x, drawing_y)

    def _kid_house_interact(game):
        # If close to the drawing and not yet taken, pick it up.
        if (abs(game.player.x - drawing_x) < 36
                and abs(game.player.y - drawing_y) < 36):
            if game.save.flag("kid_drawing_taken"):
                game.show_notice("There is nothing else on the wall.")
                return
            game.save.set_flag("kid_drawing_taken", True)
            game.player.inventory.add("kid_drawing", 1)
            game.audio.play("pickup", 0.7)
            game.show_notice("You take the drawing off the wall.")
    sc.on_interact_fn = _kid_house_interact
    return sc
