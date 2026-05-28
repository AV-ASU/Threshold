"""cornfield_path (key: 'forest_path') -- the dirt road east of
the Clerk's house. Stubble cornfield to the north and south,
the trees thicken at the east end where the road bends into the
woods.

The Preacher walks this road as part of his patrol route. The
cornstalks and dense trees are perfect hide cover.
"""
import re
import random
import pygame
from constants import TILE
from entities.decoration import Decoration
from .base import Scene


def build_forest_path():
    W = 60
    H = 14
    PATH_ROW = 7              # main horizontal walking lane
    SECRET_COL = 19           # column where the path-to-clearing branches off

    floor = []
    for y in range(H):
        if PATH_ROW - 1 <= y <= PATH_ROW + 1:
            floor.append("d" * W)
        else:
            floor.append("g" * W)

    objects_l = []
    for y in range(H):
        if y < 2 or y >= H - 2:
            row = ["C"] * W
        else:
            row = ["."] * W
            row[0] = "C"
            row[W - 1] = "C"
        objects_l.append(row)

    # West passage from outside_innkeeper_house.
    for dy in (-1, 0, 1):
        objects_l[PATH_ROW + dy][0] = "a"
    # The east end is a closed tree wall (the diner spur was removed) --
    # the road just runs into the woods and stops. Tiles stay "C".

    # The clearing is reached via the brimley river bank, not via
    # a secret tree off the cornfield path.

    # Scattered rocks in the open patches.
    rock_positions = [(6, 4), (12, 9), (22, 3), (32, 8), (45, 4), (52, 10)]
    for rx, ry in rock_positions:
        if 2 <= ry < H - 2 and ry != PATH_ROW:
            objects_l[ry][rx] = "R"

    objects = ["".join(r) for r in objects_l]
    sc = Scene("forest_path", floor, objects, music="outside")

    sc.add_exit("a", "our_house_area",  "from_forest")
    # 2-wide passage north into the deeper cornfield (cornfield_maze).
    # Uses the `!` outdoor_passage char so it reads as a gap in the
    # corn rather than a door. Two adjacent tiles so the player walks
    # straight through without having to centre on a single door.
    sc.add_exit("!", "cornfield_maze", "from_forest_path")

    sc.set_spawn("default", 1, PATH_ROW)
    sc.set_spawn("from_our_house_area", 1, PATH_ROW)
    sc.set_spawn("from_cave", W - 2, PATH_ROW)
    sc.set_spawn("from_barn", W - 2, PATH_ROW)
    sc.set_spawn("from_cornfield_maze", 30, PATH_ROW)

    # Ambient grass tufts -- here read as cornstalks. A few crows.
    for _ in range(40):
        gx = random.randint(2, W - 3) * TILE + random.randint(0, 30)
        gy = random.randint(2, H - 3) * TILE + random.randint(0, 30)
        sc.add_decoration(Decoration(gx, gy, "grass_tuft"))
    sc.add_decoration(Decoration(5 * TILE + 8, 2 * TILE + 22, "crow"))
    sc.add_decoration(Decoration(38 * TILE + 8, 11 * TILE + 22, "crow"))

    # Creepy details. Two leafless gnarled trees up against the
    # north and south tree lines so they read as part of the woods
    # but bend wrong. A hanging figure in the deep tree row east of
    # the secret-clearing branch -- the player has to look up off
    # the path to catch it. A dead crow on the road shoulder.
    sc.add_decoration(Decoration(28 * TILE + 16, 1 * TILE + 28, "creepy_tree"))
    sc.add_decoration(Decoration(46 * TILE + 16, 12 * TILE + 8, "creepy_tree"))
    sc.add_decoration(Decoration(36 * TILE + 16, 0 * TILE + 28, "hanging_figure"))
    sc.add_decoration(Decoration(20 * TILE + 16, 9 * TILE + 22, "dead_crow"))

    # (The secret-clearing branch dressing was removed when the
    # cauldron entrance moved to the brimley river bank.)

    # Hide spots: cornstalks along the south fence, behind the rocks,
    # behind the decoy passable trees. The player can melt into the
    # cornfield off the road on either side.
    sc.hide_spots = [
        (10 * TILE + 16, 11 * TILE + 16, "behind"),  # cornstalks south
        (15 * TILE + 16, 4 * TILE + 16, "behind"),   # cornstalks north
        (25 * TILE + 16, 12 * TILE + 16, "behind"),  # cornstalks south
        (32 * TILE + 16, 8 * TILE + 16, "behind"),   # behind a rock
        (42 * TILE + 16, 4 * TILE + 16, "behind"),   # cornstalks north
        (50 * TILE + 16, 1 * TILE + 16, "behind"),   # decoy tree gap
    ]

    sc._fp_W = W
    sc._fp_H = H
    sc._fp_PATH_ROW = PATH_ROW
    sc._fp_SECRET_COL = SECRET_COL

    # Loot crate against an interior corn stalk -- chop with the
    # axe to drop the item from CRATE_LOOT for this coord.
    sc.objects[5][8] = "K"
    # Two-wide gap north into the deeper cornfield. The break in
    # the corn wall reads as a footpath worn through the rows, not
    # a door.
    sc.objects[1][30] = "!"
    sc.objects[1][31] = "!"

    # Hide spot at the START of the cornfield path -- west end, in
    # the corn against the south wall. Gives the player cover the
    # moment they step off the inn yard onto the road.
    sc.hide_spots.insert(0,
        (3 * TILE + 16, 11 * TILE + 16, "behind"))

    def _forest_on_enter(game, scene):
        # First-visit: arm the wind-dies beat. The music silence
        # is restored automatically; we just track the schedule.
        scene._fp_silence_state = "armed" if not game.save.flag(
            "forest_first_silence") else "done"
        scene._fp_silence_t = 0.0
    sc.on_enter_fn = _forest_on_enter

    def _forest_on_update(game, scene, dt):
        # Pacing the wind-cut beat. State machine:
        #   armed   -> count up to ~10s, then enter "cutting"
        #   cutting -> stop the wind track, count to 1.4s, fire
        #              a single faint child_hum, count out to 3s
        #   resume  -> restart the scene's music track, mark done
        #
        # The cut is the loudest beat: the player suddenly notices
        # the world has gone quiet, then hears something a kid would
        # make in the silence, then the wind comes back. The music
        # restart is handled by play_music's same-track guard.
        state = getattr(scene, "_fp_silence_state", "done")
        if state == "done":
            return
        scene._fp_silence_t += dt
        t = scene._fp_silence_t
        if state == "armed" and t >= 10.0:
            scene._fp_silence_state = "cutting"
            scene._fp_silence_t = 0.0
            game.audio.stop_music(fade_ms=400)
            game.audio.current_music = None
        elif state == "cutting":
            if t >= 1.4 and not getattr(scene, "_fp_hum_played", False):
                scene._fp_hum_played = True
                game.audio.play("child_hum", 0.35)
            if t >= 3.0:
                scene._fp_silence_state = "done"
                game.save.set_flag("forest_first_silence", True)
                if not game.audio.music_muted:
                    game.audio.play_music(scene.music, fade_in_ms=600)
    sc.on_update_fn = _forest_on_update

    return sc
