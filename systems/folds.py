"""Spatial folds -- one tile type that both *reveals* and *connects*
another region of the world (mirror and seamless-transition are the same
primitive). A fold lives in ``scene.tile_meta[(tx, ty)]`` as::

    {"fold": True,
     "dir": (1, 0),               # the approach the fold answers to (unit)
     "to_scene": "country_lane",  # which scene the other side is
     "to_tile": (55, 13),         # tile in that scene the fold mirrors/lands on
     "reveal_range": 320.0,       # px the peek begins to show within
     "cone": 0.45}                # sight-cone half-angle (min dot vs facing)

Two behaviours, both driven off the *same* tile + the same view-cone test:

* **Reveal** (draw): while a fold tile is inside the player's sight cone,
  a window of the far region is rendered into the world *at the fold's
  on-screen position*, so the other side shows through the tile -- using
  ``draw_scene_terrain`` (the existing wrap-aware region renderer) onto an
  off-screen surface, then blitted. The far scene is built once and cached.

* **Cross** (step): when the player stands on a fold tile *and* is heading
  along its ``dir``, they are moved to the far side seamlessly (no fade --
  unlike a normal exit, which fades via begin_transition). Camera re-snaps.

The fold is deliberately a thin layer over primitives that already exist
(Scene.in_sight_cone, Scene.wrap_offsets, draw_scene_terrain,
load_scene_now). It adds no new tile char and no new collision rule: a
fold tile is whatever floor it was drawn as; tile_meta gives it meaning.
"""

import pygame

from constants import SCREEN_W, SCREEN_H, TILE
from scenes.base import draw_scene_terrain


# Far scenes are built lazily and cached so the reveal doesn't rebuild a
# whole Scene every frame. Keyed by scene key. Cleared on run reset.
_FAR_CACHE = {}


def reset_cache():
    """Drop cached far-side scenes (call on New Game / run reset)."""
    _FAR_CACHE.clear()


def _far_scene(key):
    sc = _FAR_CACHE.get(key)
    if sc is None:
        # Local import to avoid a cycle (scenes -> ... -> folds).
        from scenes import load_scene
        sc = load_scene(key)
        _FAR_CACHE[key] = sc
    return sc


def _iter_folds(scene):
    """Yield (tx, ty, meta) for every fold tile in the scene."""
    meta = getattr(scene, "tile_meta", None)
    if not meta:
        return
    for (tx, ty), m in meta.items():
        if m.get("fold"):
            yield tx, ty, m


# The main-road network: the arteries the player can rely on for
# continuous, see-through, fade-free travel. Each entry promotes the named
# edge exits of a scene into folds. Deliberately EXCLUDES:
#   - building doors (H/D/M etc.): a fade reads as "stepping inside".
#   - trap loops (highway_walk 'G', cornfield_maze warps): the fade/disorient
#     IS the horror; making them seamless would defeat them.
# Keyed by scene -> the exit chars on that scene that are main road.
ROAD_SEAMS = {
    "brimley":           ["4", "R"],         # -> country_lane, gravel_road_north
    "country_lane":      ["a", "e"],         # -> brimley, our_house_area
    "our_house_area":    ["a", "e"],         # -> country_lane, forest_path
    "forest_path":       ["a"],              # -> our_house_area
    "gravel_road_north": ["a", "e"],         # -> brimley, backwoods_cabin
    "backwoods_cabin":   ["H"],              # -> gravel_road_north
}


def apply_road_folds(scene):
    """Promote this scene's main-road edge exits into folds (see-through,
    seamless). Called once per load from load_scene_now, after the builder
    + on_enter. Idempotent: rebuilds tile_meta fold entries each load, and
    only touches chars listed in ROAD_SEAMS for this scene."""
    chars = ROAD_SEAMS.get(scene.key)
    if not chars:
        return 0
    n = 0
    for ch in chars:
        n += promote_exit(scene, ch)
    return n


def promote_exit(scene, char, *, reveal_range=320.0, cone=0.45, window=2):
    """Turn an existing edge exit into a fold: every tile carrying ``char``
    becomes a seamless, see-through seam to the same target/spawn the plain
    exit already names. The approach direction is inferred from which edge
    the tiles sit on (left edge -> answers a westward walk, etc.), so a
    main road reads as continuous travel -- the neighbour shows through and
    you cross without a fade -- while building doors and trap exits keep
    their plain (fading) behaviour.

    The plain exit is left registered too: it's the fallback if the player
    somehow lands on the tile without satisfying the fold's direction (the
    fold check runs first in step() and wins when it fires)."""
    data = scene.exits.get(char)
    if data is None:
        return 0
    to_scene, to_spawn = data
    tiles = [(tx, ty) for ty, row in enumerate(scene.objects)
             for tx, ch in enumerate(row) if ch == char]
    if not tiles:
        return 0
    # Infer approach dir from the tiles' position on the map edge.
    xs = [t[0] for t in tiles]
    ys = [t[1] for t in tiles]
    on_left = min(xs) == 0
    on_right = max(xs) == scene.w - 1
    on_top = min(ys) == 0
    on_bottom = max(ys) == scene.h - 1
    if on_left:
        d = (-1, 0)
    elif on_right:
        d = (1, 0)
    elif on_top:
        d = (0, -1)
    elif on_bottom:
        d = (0, 1)
    else:
        # Interior exit (not an edge): no obvious approach -- skip, leave
        # it as a plain exit.
        return 0
    for (tx, ty) in tiles:
        scene.tile_meta[(tx, ty)] = {
            "fold": True, "dir": d,
            "to_scene": to_scene, "to_spawn": to_spawn,
            "reveal_range": reveal_range, "cone": cone, "window": window,
        }
    return len(tiles)


def _far_tile(m, far):
    """The tile in the far scene the peek is centred on. Explicit
    ``to_tile`` wins; otherwise derive it from the landing spawn so a
    promoted road exit needs no hand-typed coordinates."""
    if "to_tile" in m:
        return m["to_tile"]
    spawn = m.get("to_spawn", "default")
    sp = far.spawns.get(spawn) or far.spawns.get("default")
    if sp:
        return int(sp[0] // TILE), int(sp[1] // TILE)
    return far.w // 2, far.h // 2


def player_tile(game):
    return int(game.player.x // TILE), int(game.player.y // TILE)


def fold_at(scene, tx, ty):
    """The fold meta at a tile, or None."""
    m = getattr(scene, "tile_meta", None)
    if not m:
        return None
    d = m.get((tx, ty))
    return d if (d and d.get("fold")) else None


def draw_reveals(game, surf):
    """Render the far side of every in-sight fold into ``surf`` (the world
    layer, after terrain, before actors). Pure presentation: touches no
    game state."""
    scene = game.scene
    p = game.player
    fx, fy = p.facing
    for tx, ty, m in _iter_folds(scene):
        # Centre of the fold tile, in world px.
        wx = tx * TILE + TILE // 2
        wy = ty * TILE + TILE // 2
        cone = m.get("cone", 0.45)
        rng = m.get("reveal_range", 320.0)
        if not scene.in_sight_cone(p.x, p.y, fx, fy, wx, wy,
                                   cos_thresh=cone, max_dist=rng):
            continue
        far = _far_scene(m["to_scene"])
        ftx, fty = _far_tile(m, far)
        # Build the far window centred on the target tile, the same size as
        # a small patch around the fold (a single-tile "mirror"): a 5x5 tile
        # window reads as a doorway-sized peek without ballooning cost.
        half = m.get("window", 2)
        x0, y0 = ftx - half, fty - half
        x1, y1 = ftx + half + 1, fty + half + 1
        win_w = (x1 - x0) * TILE
        win_h = (y1 - y0) * TILE
        peek = pygame.Surface((win_w, win_h)).convert()
        # cam so that far tile (x0,y0) maps to peek origin.
        draw_scene_terrain(peek, far, x0 * TILE, y0 * TILE, x0, y0, x1, y1)
        # Blit so the *centre* of the window sits over the fold tile centre.
        dst_x = int(wx - game.cam_x - win_w // 2)
        dst_y = int(wy - game.cam_y - win_h // 2)
        if (dst_x > SCREEN_W or dst_y > SCREEN_H
                or dst_x + win_w < 0 or dst_y + win_h < 0):
            continue
        surf.blit(peek, (dst_x, dst_y))


def try_cross(game):
    """If the player is on a fold tile and heading along its ``dir``, move
    them to the far side seamlessly (no fade). Returns True if a crossing
    happened. Called from step() before the normal exit check so the fold
    takes precedence over any plain exit sharing the tile."""
    scene = game.scene
    tx, ty = player_tile(game)
    m = fold_at(scene, tx, ty)
    if m is None:
        return False
    dx, dy = m.get("dir", (0, 0))
    fx, fy = game.player.facing
    # Heading roughly the fold's way? (same cone test, tight.)
    if (dx * fx + dy * fy) < m.get("cross_dot", 0.6):
        return False
    # Seamless: load far scene at the landing, no transition fade.
    spawn = m.get("to_spawn")
    if spawn:
        game.load_scene_now(m["to_scene"], spawn, keep_music=True)
    else:
        # No named spawn: land on the explicit target tile directly.
        # load_scene_now needs a spawn id; use 'default' then override the
        # coords so the landing is exactly the mirrored tile.
        ftx, fty = m["to_tile"]
        game.load_scene_now(m["to_scene"], "default", keep_music=True)
        game.player.x = ftx * TILE + TILE // 2
        game.player.y = fty * TILE + TILE // 2
        game._update_camera(snap=True)
    return True
