"""Seamless-world neighbor enumeration (Phase 1 of the neighbor-strip work).

When the player walks across an open boundary (a road end, a field edge -- any
exit where both host and target are in `SEAMLESS_WORLD_SCENES`), the eventual
neighbor-strip renderer needs three things:

  1. WHICH scenes are the host's neighbors (and how to reach them in tile
     coords);
  2. The OFFSET that maps host world coords into target world coords, so the
     target can be drawn with the host camera shifted (same approach as the
     portal through-view in `rendering/portal.py`);
  3. The boundary point in host coords + which edge it sits on, so the
     renderer can decide where to put the strip and distance-cull it.

This module is pure data. Read-only. No surface drawn here; we only enumerate.
The renderer (Phase 2+) consumes `get_neighbors(scene)` and treats each entry
the way `_render_through` treats a portal target.

Doors, ladders, the well, and the King's runtime portal are NOT neighbors
in this sense -- they're hard cuts. The seamless set is what the player
should see across.
"""
from dataclasses import dataclass

from constants import TILE
from systems.config import SEAMLESS_WORLD_SCENES


@dataclass(frozen=True)
class Neighbor:
    target_key: str
    # Shift to add to a HOST world coord to get the equivalent TARGET world
    # coord. At the seam, host (boundary_x, boundary_y) == target (spawn_x,
    # spawn_y), so the offset is (spawn - boundary). A satellite camera that
    # mirrors the host camera plus this offset will project the target room so
    # the seam point lands at the same screen pixel the boundary tile does.
    offset_dx: float
    offset_dy: float
    # The boundary point in HOST world coords -- the centre of the exit tile.
    boundary_x: float
    boundary_y: float
    # Which side of the host the boundary sits on. Used to clip the strip to
    # the relevant edge and to cull strips facing away from the camera.
    edge: str               # "north" | "south" | "east" | "west"
    # The exit tile char + spawn id, kept for debugging / future inventory
    # gating once the Transition refactor lands.
    char: str
    spawn_id: str


def _edge_for(scene, tx, ty):
    """Pick the host edge the exit tile sits closest to. Ties break by axis
    distance (the corner case is rare; the renderer just needs ONE direction
    to anchor the strip)."""
    w, h = scene.w, scene.h
    d_west = tx
    d_east = (w - 1) - tx
    d_north = ty
    d_south = (h - 1) - ty
    nearest = min(d_west, d_east, d_north, d_south)
    if nearest == d_north:
        return "north"
    if nearest == d_south:
        return "south"
    if nearest == d_east:
        return "east"
    return "west"


_CACHE = {}
# Built neighbor scenes, memoized by key. The strip/solid renderers need only a
# neighbor's STATIC floor + object layout (read-only), so a one-time build is
# safe -- without this, the tilt floor pass rebuilt each seamless neighbor scene
# procedurally EVERY frame (load_scene is uncached).
_SCENE_CACHE = {}


def load_neighbor(key):
    """load_scene(key), memoized for the seamless-strip render path."""
    sc = _SCENE_CACHE.get(key)
    if sc is None:
        from scenes import load_scene
        sc = load_scene(key)
        _SCENE_CACHE[key] = sc
    return sc


def get_neighbors(scene):
    """Return [Neighbor] for the host scene's seamless connections.

    Cached per scene key -- the answer is a function of scene layout (which
    never changes after build) so a memo is safe. `clear_cache()` resets it
    if a test rebuilds scenes."""
    if scene.key in _CACHE:
        return _CACHE[scene.key]
    if scene.key not in SEAMLESS_WORLD_SCENES:
        _CACHE[scene.key] = []
        return []
    # Lazy import: scenes -> rendering shouldn't tighten into a load-time
    # circular dep just because we want load_scene here.
    from scenes import load_scene

    out = []
    for ch, (target_key, spawn_id) in scene.exits.items():
        if target_key not in SEAMLESS_WORLD_SCENES:
            continue                    # door / ladder / well -- hard cut
        if ch in scene.exit_directions:
            continue                    # eldritch direction-gated portal: it
                                        # has its own gold-rim peek; canon
                                        # says it reads as floor from any
                                        # other angle, so the neighbor strip
                                        # would defeat the trick.
        pos = scene.find_marker(ch)
        if pos is None:
            continue
        tx, ty = pos
        ex = tx * TILE + TILE // 2
        ey = ty * TILE + TILE // 2
        try:
            target_scene = load_scene(target_key)
        except Exception:
            continue
        spawn = (target_scene.spawns.get(spawn_id)
                 or target_scene.spawns.get("default"))
        if spawn is None:
            continue
        sx, sy = spawn
        out.append(Neighbor(
            target_key=target_key,
            offset_dx=sx - ex,
            offset_dy=sy - ey,
            boundary_x=ex,
            boundary_y=ey,
            edge=_edge_for(scene, tx, ty),
            char=ch,
            spawn_id=spawn_id,
        ))
    _CACHE[scene.key] = out
    return out


def clear_cache():
    """Drop the memo (test/dev hook)."""
    _CACHE.clear()
    _SCENE_CACHE.clear()
