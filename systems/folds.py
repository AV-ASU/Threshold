"""Spatial folds -- one tile type that both *reveals* and *connects*
another region of the world (mirror and seamless-transition are the same
primitive). A fold lives in ``scene.tile_meta[(tx, ty)]`` as::

    {"fold": True,
     "dir": (-1, 0),              # the approach the fold answers to (unit)
     "to_scene": "country_lane",  # which scene the other side is
     "to_spawn": "from_...",      # spawn there the crossing lands on
     "to_tile": (tx, ty),         # OPTIONAL peek centre (else derived
     "reveal_range": 320.0,       #   from the spawn)
     "cone": 0.45, "window": 2}

Two behaviours, both off the same tile:

* **Reveal** (draw): a fold sits on a map edge (the road's seam). The far
  scene is rendered into the *road band beyond that edge*, aligned so the
  road runs continuously across the seam -- the neighbour shows THROUGH
  the threshold instead of a fade. Only the fold tiles' own lateral band
  is filled, so off-road tiles still show their wrap-clone: the road
  crosses to the neighbour, the wilderness loops -- exactly the map's
  fiction. Far scenes are built once and cached.

* **Cross** (step): standing on a fold tile while heading along its
  ``dir`` moves the player to the far side seamlessly -- no fade. Camera
  re-snaps. Checked before the plain exit so the fold wins a shared tile.

Built on existing primitives (draw_scene_terrain -- the wrap-aware region
renderer, load_scene_now -- the landing). No new tile char, no new
collision rule: a fold tile is whatever floor it was; tile_meta gives it
meaning. Most folds are created by promote_exit (turning an edge exit into
a seam); see ROAD_SEAMS for the main-road network.
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
        from scenes import load_scene          # local: avoid import cycle
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


# ---------------------------------------------------------------------------
# The main-road network: the arteries the player relies on for continuous,
# see-through, fade-free travel. Each entry promotes a scene's named edge
# exits into folds. Deliberately EXCLUDES building doors (a fade reads as
# "stepping inside") and the trap loops (highway_walk 'G', cornfield_maze
# warps -- the disorient IS the horror).
ROAD_SEAMS = {
    "brimley":           ["4", "R"],     # -> country_lane, gravel_road_north
    "country_lane":      ["a", "e"],     # -> brimley, our_house_area
    "our_house_area":    ["a", "e"],     # -> country_lane, forest_path
    "forest_path":       ["a"],          # -> our_house_area
    "gravel_road_north": ["a", "e"],     # -> brimley, backwoods_cabin
    "backwoods_cabin":   ["H"],          # -> gravel_road_north
}


def apply_road_folds(scene):
    """Promote this scene's main-road edge exits into folds. Called once per
    load from load_scene_now (after builder + on_enter, so the exits
    exist). Idempotent; only touches chars listed in ROAD_SEAMS."""
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
    the tiles sit on. Interior (non-edge) exits are left alone. The plain
    exit stays registered as a fallback (the fold check runs first in step
    and wins when it fires)."""
    data = scene.exits.get(char)
    if data is None:
        return 0
    to_scene, to_spawn = data
    tiles = [(tx, ty) for ty, row in enumerate(scene.objects)
             for tx, ch in enumerate(row) if ch == char]
    if not tiles:
        return 0
    xs = [t[0] for t in tiles]
    ys = [t[1] for t in tiles]
    if min(xs) == 0:
        d = (-1, 0)
    elif max(xs) == scene.w - 1:
        d = (1, 0)
    elif min(ys) == 0:
        d = (0, -1)
    elif max(ys) == scene.h - 1:
        d = (0, 1)
    else:
        return 0                           # interior exit: no edge to fold
    for (tx, ty) in tiles:
        scene.tile_meta[(tx, ty)] = {
            "fold": True, "dir": d,
            "to_scene": to_scene, "to_spawn": to_spawn,
            "reveal_range": reveal_range, "cone": cone, "window": window,
        }
    return len(tiles)


def _far_tile(m, far):
    """The tile in the far scene the seam aligns on. Explicit ``to_tile``
    wins; else derive it from the landing spawn so a promoted road exit
    needs no hand-typed coordinates."""
    if "to_tile" in m:
        return m["to_tile"]
    sp = far.spawns.get(m.get("to_spawn", "default")) or far.spawns.get("default")
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


# ---------------------------------------------------------------------------
# Reveal

def draw_reveals(game, surf):
    """Render the far side of each road seam THROUGH its edge: the
    neighbour fills the road band beyond the map edge, aligned so the road
    runs continuously across it. Drawn after terrain, under actors. Pure
    presentation -- touches no game state."""
    scene = game.scene
    # Group a scene's fold tiles into seams: same target + approach dir.
    seams = {}
    for tx, ty, m in _iter_folds(scene):
        seams.setdefault((m["to_scene"], m["dir"]), []).append((tx, ty, m))
    for (to_scene, d), tiles in seams.items():
        _draw_seam(game, surf, to_scene, d, tiles)


def _draw_seam(game, surf, to_scene, d, tiles):
    cam_x, cam_y = game.cam_x, game.cam_y
    dx, dy = d
    far = _far_scene(to_scene)
    ftx, fty = _far_tile(tiles[0][2], far)
    txs = [t[0] for t in tiles]
    tys = [t[1] for t in tiles]
    tx0, tx1, ty0, ty1 = min(txs), max(txs), min(tys), max(tys)
    # The band centre maps onto the far landing tile, so the far scene is
    # aligned for a continuous road across the seam.
    rtx, rty = (tx0 + tx1) // 2, (ty0 + ty1) // 2
    far_cam_x = (ftx - rtx) * TILE + cam_x
    far_cam_y = (fty - rty) * TILE + cam_y
    # The fold band in screen px, and the threshold edge to spill past.
    band_l = int(tx0 * TILE - cam_x)
    band_r = int((tx1 + 1) * TILE - cam_x)
    band_t = int(ty0 * TILE - cam_y)
    band_b = int((ty1 + 1) * TILE - cam_y)
    if dx < 0:        # west edge: fill left of the band
        cl = pygame.Rect(0, band_t, band_l, band_b - band_t)
    elif dx > 0:      # east edge
        cl = pygame.Rect(band_r, band_t, SCREEN_W - band_r, band_b - band_t)
    elif dy < 0:      # north edge
        cl = pygame.Rect(band_l, 0, band_r - band_l, band_t)
    else:             # south edge
        cl = pygame.Rect(band_l, band_b, band_r - band_l, SCREEN_H - band_b)
    cl = cl.clip(surf.get_rect())
    if cl.width <= 0 or cl.height <= 0:
        return                              # threshold not visible: nothing to show
    # Render the far band into a temp surface and blit it. blit honours the
    # band bounds exactly; set_clip proved unreliable on these surfaces
    # (it was ignored, leaking the whole window). The far cam shifts by the
    # band origin so the scene still lands aligned to the seam.
    tmp = pygame.Surface((cl.width, cl.height)).convert()
    tcx = far_cam_x + cl.left
    tcy = far_cam_y + cl.top
    fx0 = int(tcx // TILE) - 1
    fy0 = int(tcy // TILE) - 1
    fx1 = int((tcx + cl.width) // TILE) + 2
    fy1 = int((tcy + cl.height) // TILE) + 2
    draw_scene_terrain(tmp, far, tcx, tcy, fx0, fy0, fx1, fy1)
    surf.blit(tmp, (cl.left, cl.top))


# ---------------------------------------------------------------------------
# Cross

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
    if (dx * fx + dy * fy) < m.get("cross_dot", 0.6):
        return False                        # not heading the fold's way
    spawn = m.get("to_spawn")
    if spawn:
        game.load_scene_now(m["to_scene"], spawn, keep_music=True)
    else:
        ftx, fty = m["to_tile"]
        game.load_scene_now(m["to_scene"], "default", keep_music=True)
        game.player.x = ftx * TILE + TILE // 2
        game.player.y = fty * TILE + TILE // 2
        game._update_camera(snap=True)
    return True
