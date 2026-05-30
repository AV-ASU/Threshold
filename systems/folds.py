"""Seam previews -- the see-through half of the world's seamless
transitions. The game already CROSSES outdoor scenes without a fade
(``Game.begin_transition`` swaps the scene and preserves screen position
whenever both scenes are in ``SEAMLESS_WORLD_SCENES``). This module adds
the matching *visual*: as you near such a seam, the neighbouring scene is
rendered THROUGH the map edge -- the road runs continuously across the
threshold instead of cutting to the next screen.

One rule, derived from the game's own classifier: a seam previews iff the
crossing is seamless. That is exactly "every transition that isn't a door
/ rope / ladder" -- ``SEAMLESS_WORLD_SCENES`` is the continuous outside
world, so indoor scenes (house, bedroom, shops...) and underground scenes
(the works, the well, the depths) are excluded automatically. They keep
their fade; nothing folds into them.

Mechanically the preview is pure presentation: it reads the scene's live
edge exits, keeps only the ones whose target is also seamless-world, and
fills the band beyond that edge with the neighbour (via the wrap-aware
``draw_scene_terrain``), aligned on the landing spawn so the road lines
up. It touches no game state and adds no tile char or collision rule.
"""

import pygame

from constants import SCREEN_W, SCREEN_H, TILE
from scenes.base import draw_scene_terrain


# Neighbour scenes are built lazily and cached so a preview doesn't rebuild
# a whole Scene every frame. Keyed by scene key. Cleared on run reset.
_FAR_CACHE = {}


def reset_cache():
    """Drop cached neighbour scenes (call on New Game / run reset)."""
    _FAR_CACHE.clear()


def _far_scene(key):
    sc = _FAR_CACHE.get(key)
    if sc is None:
        from scenes import load_scene          # local: avoid import cycle
        sc = load_scene(key)
        _FAR_CACHE[key] = sc
    return sc


def _seamless_set():
    # Local import to avoid a module-load cycle (game imports scenes which
    # ... eventually imports this). The set is the single source of truth
    # for "continuous outside world": indoor + underground scenes are not
    # in it, so they never preview.
    from systems.game import SEAMLESS_WORLD_SCENES
    return SEAMLESS_WORLD_SCENES


_DIR_FROM_EDGE = {"W": (-1, 0), "E": (1, 0), "N": (0, -1), "S": (0, 1)}


def _edge_of(scene, tiles):
    """Which map edge a run of exit tiles sits on, or None if interior.
    Interior exits (warps, e.g. the cornfield groves' inward mouths) have
    no edge band to spill a preview into."""
    xs = [t[0] for t in tiles]
    ys = [t[1] for t in tiles]
    if min(xs) == 0:
        return "W"
    if max(xs) == scene.w - 1:
        return "E"
    if min(ys) == 0:
        return "N"
    if max(ys) == scene.h - 1:
        return "S"
    return None


def _seams(scene):
    """Yield (to_scene, dir, tiles, spawn) for every previewable seam: an
    EDGE exit whose target is also seamless-world. Derived live from the
    scene's exits each call -- no registry, no tile_meta."""
    if scene.key not in _seamless_set():
        return
    seamless = _seamless_set()
    # Group exit tiles by char so a 3-tile-wide road mouth is one seam.
    by_char = {}
    for ty, row in enumerate(scene.objects):
        for tx, ch in enumerate(row):
            if ch in scene.exits:
                by_char.setdefault(ch, []).append((tx, ty))
    for ch, tiles in by_char.items():
        to_scene, spawn = scene.exits[ch]
        if to_scene not in seamless:
            continue                          # door / underground / indoor: fade
        edge = _edge_of(scene, tiles)
        if edge is None:
            continue                          # interior warp: nothing to spill
        yield to_scene, _DIR_FROM_EDGE[edge], tiles, spawn


def _far_align_tile(far, spawn):
    """The neighbour tile the seam aligns on: its landing spawn, so the
    road lines up across the threshold."""
    sp = far.spawns.get(spawn) or far.spawns.get("default")
    if sp:
        return int(sp[0] // TILE), int(sp[1] // TILE)
    return far.w // 2, far.h // 2


# ---------------------------------------------------------------------------
# Preview

def draw_reveals(game, surf):
    """Render the neighbour of each previewable seam THROUGH its edge: the
    far scene fills the band beyond the map edge, aligned so the road runs
    continuously across it. Drawn after terrain, under actors. Pure
    presentation -- touches no game state. No-op in indoor/underground
    scenes (they aren't seamless-world, so ``_seams`` yields nothing)."""
    scene = game.scene
    for to_scene, d, tiles, spawn in _seams(scene):
        _draw_seam(game, surf, to_scene, d, tiles, spawn)


def _draw_seam(game, surf, to_scene, d, tiles, spawn):
    cam_x, cam_y = game.cam_x, game.cam_y
    dx, dy = d
    far = _far_scene(to_scene)
    ftx, fty = _far_align_tile(far, spawn)
    txs = [t[0] for t in tiles]
    tys = [t[1] for t in tiles]
    tx0, tx1, ty0, ty1 = min(txs), max(txs), min(tys), max(tys)
    # The band centre maps onto the far landing tile, so the neighbour is
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
