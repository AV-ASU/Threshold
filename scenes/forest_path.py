"""cornfield_path (key: 'cornfield_path') -- the dirt road east of
the Clerk's house. Stubble cornfield to the north and south,
the trees thicken at the east end where the road bends into the
woods.

The Preacher walks this road as part of his patrol route. The
cornstalks and dense trees are perfect hide cover.
"""
import random
from constants import TILE
from entities.decoration import Decoration
from .base import Scene


def build_cornfield_path():
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

    # No hard corn-wall perimeter -- the scattered forest band is
    # stamped below. Floor pre-built; objects start fully open.
    objects_l = []
    for y in range(H):
        row = ["."] * W
        objects_l.append(row)

    # West passage from our_house_area.
    for dy in (-1, 0, 1):
        objects_l[PATH_ROW + dy][0] = "a"

    # Scattered rocks in the open patches.
    rock_positions = [(6, 4), (12, 9), (22, 3), (32, 8), (45, 4), (52, 10)]
    for rx, ry in rock_positions:
        if 2 <= ry < H - 2 and ry != PATH_ROW:
            objects_l[ry][rx] = "R"

    # South-edge exit to brimley (macro-loop closer). 'S' on the last
    # row at col 30; players walking south off the path reach it.
    SOUTH_EXIT_COL = 30
    objects_l[H - 1][SOUTH_EXIT_COL] = "S"

    # ---- Permeable forest band ----
    # Replaces the old hard corn-wall north/south perimeter. Same helper
    # as brimley so the visual treatment of the wrap is consistent.
    floor_ll_fp = [list(r) for r in floor]
    def _fp_protected(tx, ty):
        # West passage corridor (3 rows by 5 cols).
        if tx <= 4 and PATH_ROW - 1 <= ty <= PATH_ROW + 1:
            return True
        # East end -- keep the road tile visible coming in.
        if tx >= W - 5 and PATH_ROW - 1 <= ty <= PATH_ROW + 1:
            return True
        # North maze exit corridor (col 30-31, rows 0-2).
        if tx in (29, 30, 31) and ty <= 2:
            return True
        # South brimley exit corridor (col 30, rows H-3..H-1).
        if tx in (29, 30, 31) and ty >= H - 3:
            return True
        # The path row itself is always clear.
        if ty == PATH_ROW:
            return True
        return False
    _fp_bushes = []
    from .base import scatter_forest_band
    scatter_forest_band(floor_ll_fp, objects_l, W, H,
                        depth=3, seed=71,
                        # Forest_path is thin -- depth 3 covers the full
                        # north + south corn rows.
                        tree_density=0.55, passable_ratio=0.55,
                        bush_density=0.16,
                        protected=_fp_protected,
                        place_bush=lambda px, py:
                            _fp_bushes.append((px, py)))
    floor = ["".join(r) for r in floor_ll_fp]
    objects = ["".join(r) for r in objects_l]
    sc = Scene("cornfield_path", floor, objects, music="outside")
    for bx, by in _fp_bushes:
        sc.add_decoration(Decoration(bx, by, "bush"))
    # Walk through the woods only to be spit out where you walked in.
    # Both axes wrap so the trees become a trap, not a wall. The
    # explicit exits (back to the yard / on to cornfield_maze) stay
    # as specific tiles; everything else just folds.
    sc.wrap_x = True
    sc.wrap_y = True

    sc.add_exit("a", "lodge_yard",  "from_forest")
    # 2-wide passage north into the deeper cornfield (cornfield_maze).
    # Uses the `!` outdoor_passage char so it reads as a gap in the
    # corn rather than a door. Two adjacent tiles so the player walks
    # straight through without having to centre on a single door.
    sc.add_exit("!", "cornfield_maze", "from_cornfield_path")
    # South exit to brimley -- closes the macro-loop. Walking south long
    # enough through brimley -> cornfield_maze -> forest_path -> here
    # brings you back to brimley north.
    sc.add_exit("S", "brimley", "from_cornfield_path")

    sc.set_spawn("default", 1, PATH_ROW)
    sc.set_spawn("from_lodge_yard", 1, PATH_ROW)
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

    # ---- Worn-road detail (2026-07 pass) ----
    # The cult files north to the maze mouth: a corn doll set where the
    # rows break, bootprints crossing the road toward it, and claw
    # furrows in the dirt where something was dragged the other way.
    sc.add_decoration(Decoration(29 * TILE + 16, 2 * TILE + 8,
                                 "corn_doll"))
    sc.add_decoration(Decoration(30 * TILE + 16, 5 * TILE + 16,
                                 "mud_footprint"))
    sc.add_decoration(Decoration(30 * TILE + 24, 3 * TILE + 24,
                                 "mud_footprint"))
    sc.add_decoration(Decoration(33 * TILE + 16, 7 * TILE + 16,
                                 "claw_marks"))
    # An abandoned harvest: a wheelbarrow left mid-field, going to rust.
    sc.add_decoration(Decoration(46 * TILE + 16, 4 * TILE + 16,
                                 "wheelbarrow"))
    # Dead leaves drifting the road.
    for lx, ly in ((10, 6), (26, 8), (44, 7)):
        sc.add_decoration(Decoration(lx * TILE + 16, ly * TILE + 16,
                                     "leaves"))
    # Litter along the cover lanes (noise traps): tins dumped on the
    # north shoulder, a bottle gone to pieces on the south.
    sc.add_noise_trap(14 * TILE + 16, 4 * TILE + 16, "cans", seed=21)
    sc.add_noise_trap(40 * TILE + 16, 10 * TILE + 16, "glass", seed=22)

    # (The secret-clearing branch dressing was removed when the
    # clearing entrance moved to the brimley river bank.)

    # No hide spots: the player melts into the cornfield off either road
    # shoulder (walkable corn cover) and breaks sight behind the trees.
    sc.hide_spots = []

    sc._fp_W = W
    sc._fp_H = H
    sc._fp_PATH_ROW = PATH_ROW
    sc._fp_SECRET_COL = SECRET_COL

    # Two-wide gap north into the deeper cornfield. The break in
    # the corn wall reads as a footpath worn through the rows, not
    # a door.
    sc.objects[1][30] = "!"
    sc.objects[1][31] = "!"

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
