"""The King's portal -- the visible 4D rift (KING_PROMPT M2 + the look passes).

When the player pins visibility at 100%, the King tears a rift connecting their
room to the room he stands in, and folds through. The rift wears the SAME
gold-on-black electric motif as the hidden folds (rendering.folds) -- NOT the
Threshold doorframe, which by canon never screams.

PSEUDO-3D (KING_PROMPT decision): the rift is never a flat screen-space decal.
Two parts, both camera-respecting:
  - THE FRAME is a light in the scene -- a gold light-pool spills on the ground
    at the rift's base, an additive glow climbs the tear, and the jittered gold
    cut sits on the base seam.
  - THE VIEW THROUGH IT is the target room rendered with the SAME tilt camera
    (same pitch / yaw / scale), aimed so the room you'd emerge into sits in the
    aperture, then masked to the rift's standing-tear hole. So looking through
    flows continuously with the player's own 3D view -- a real oriented hole in
    space, the floor beyond receding the same way yours does -- DESATURATED
    toward gray (the spaces between are colourless; your room keeps the colour).

Reuses the live tilt pipeline (scenes.base.draw_terrain_tilted + _tilt_tile_box,
rendering.skybox) so the far side is the same renderer as the near side, plus
the folds gold seam so the two rift kinds read as one family.
"""
import math

import pygame
import numpy as np

from constants import TILE, SCREEN_W, SCREEN_H
from scenes.base import apply_grade
from rendering.folds import _fog_mask, _draw_seam, _blit_tear

PORTAL_W = 3 * TILE          # peek depth (flat fallback only)
PORTAL_H = 3 * TILE          # breadth of the slit

_POOL_CACHE = {}
_GLOW_CACHE = {}


# ---- the camera-respecting view through the rift -----------------------------

def _render_through(target, anchor, camera, origin):
    """Render `target` with a portal-camera that matches the live tilt (pitch /
    yaw / scale) and is aimed so the target's emergence anchor projects to
    `origin` on screen. Returns a full-screen Surface of the tilted room,
    desaturated toward gray. Same renderer as the near side, so the far side's
    floor/walls recede in the same perspective."""
    from rendering.camera import Camera
    from rendering.skybox import draw_skybox
    from scenes.base import draw_terrain_tilted, _tilt_tile_box, _TILT_WALL_RISE
    ax = anchor[0] * TILE + TILE // 2
    ay = anchor[1] * TILE + TILE // 2
    pcam = Camera(cam_x=ax, cam_y=ay, pitch=camera.pitch, yaw=camera.yaw,
                  scale=camera.scale, origin=(int(origin[0]), int(origin[1])))
    buf = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_skybox(buf, (0, 0, SCREEN_W, SCREEN_H), yaw=pcam.yaw,
                kind="void", horizon_frac=0.40)
    walls, solid_decos, _wall_decos = draw_terrain_tilted(buf, target, pcam)
    # Walls back-to-front (static room view -- a plain depth sort, no per-actor
    # occlusion needed) so near walls overdraw far ones correctly.
    walls = sorted(walls, key=lambda w: pcam.depth(
        w[0] * TILE + TILE / 2, w[1] * TILE + TILE / 2, _TILT_WALL_RISE))
    for tx, ty in walls:
        _tilt_tile_box(buf, pcam, target, tx, ty)
    for d in solid_decos:
        try:
            from rendering.furniture import draw_furniture_solid
            from rendering.props import draw_prop_solid
            if not draw_furniture_solid(buf, pcam, d):
                draw_prop_solid(buf, pcam, d)
        except Exception:
            pass
    # Liminal: sink toward gray (the between has no colour).
    arr = pygame.surfarray.pixels3d(buf)
    gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
    for c in range(3):
        arr[..., c] = (arr[..., c] * 0.30 + gray * 0.62).astype(arr.dtype)
    del arr
    return buf


def _aperture_mask(quad):
    """A full-screen alpha mask shaped like the rift's standing-tear hole
    (`quad` = 4 screen points, base then top), opaque at the base and fading up
    into the liminal gray. White = show the room through; transparent = host."""
    mask = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))
    pygame.draw.polygon(mask, (255, 255, 255, 255), quad)
    top = max(0, int(min(p[1] for p in quad)))
    bot = min(SCREEN_H, int(max(p[1] for p in quad)))
    if bot > top:
        grad = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        span = bot - top
        for y in range(top, bot):
            f = (bot - y) / span                  # 1 at base -> 0 at the top
            a = int(255 * (0.32 + 0.68 * f))
            pygame.draw.line(grad, (255, 255, 255, a), (0, y), (SCREEN_W, y))
        mask.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return mask


# ---- the gold frame (light in the scene) ------------------------------------

def _gold_pool(screen, cx, cy, r, intensity):
    """An additive GOLD light-pool on the floor at the rift's base. Squashed to
    lie on the ground plane (pseudo-3D); cached per radius (RGB falloff baked
    in -- additive ignores alpha, so black adds nothing)."""
    r = max(10, int(r))
    base = _POOL_CACHE.get(r)
    if base is None:
        base = pygame.Surface((r * 2, r * 2))
        base.fill((0, 0, 0))
        for rr in range(r, 0, -1):
            ff = (1.0 - rr / r) ** 2
            pygame.draw.circle(base, (int(150 * ff), int(112 * ff),
                                      int(34 * ff)), (r, r), rr)
        _POOL_CACHE[r] = base
    k = max(0.2, min(1.0, intensity))
    pool = pygame.transform.scale(base, (r * 2, max(2, int(r * 1.1))))
    if k < 0.99:
        pool = pool.copy()
        pool.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(pool, (int(cx - r), int(cy - r * 0.55)),
                special_flags=pygame.BLEND_RGB_ADD)


def _tear_glow(screen, s0, s1, rise, intensity):
    """A soft additive gold glow climbing the standing tear, brightest at the
    base seam and fading up. Cached by (width, rise)."""
    x0, y0 = s0
    x1, y1 = s1
    w = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    rise = max(2, int(rise))
    glow = _GLOW_CACHE.get((w, rise))
    if glow is None:
        glow = pygame.Surface((w, rise))
        glow.fill((0, 0, 0))
        for j in range(rise):
            ff = (1.0 - j / rise) ** 2
            pygame.draw.line(glow, (int(120 * ff), int(92 * ff), int(28 * ff)),
                             (0, rise - 1 - j), (w, rise - 1 - j))
        _GLOW_CACHE[(w, rise)] = glow
    k = max(0.2, min(1.0, intensity))
    g = glow
    if k < 0.99:
        g = glow.copy()
        g.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(g, (int(min(x0, x1)), int(min(y0, y1) - rise)),
                special_flags=pygame.BLEND_RGB_ADD)


def _flat_peek(target, anchor, charge):
    """Pitch-0 (F3) fallback: the old flat top-down slice stood up as a panel."""
    w, h = PORTAL_W, PORTAL_H
    ax, ay = anchor
    surf = pygame.Surface((w, h))
    surf.fill((8, 8, 11))
    target.draw(surf, ax * TILE + 16 - w // 2, ay * TILE + 16 - h // 2)
    apply_grade(surf, 1.0)
    arr = pygame.surfarray.pixels3d(surf)
    gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
    for c in range(3):
        arr[..., c] = (arr[..., c] * 0.20 + gray * 0.66).astype(arr.dtype)
    del arr
    surf = surf.convert_alpha()
    mask = _fog_mask(w, h, (0, 1))
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * (150 + 90 * max(0.0, min(1.0, charge)))).astype(np.uint8)
    del pa
    return surf


def draw_portal(screen, portal, cam_x, cam_y, camera, t):
    """Composite the torn rift onto `screen` (already showing the host room)."""
    target = portal.get("_scene")
    if target is None:
        return
    charge = max(0.0, min(1.0, portal.get("charge", 1.0)))
    pulse = (0.78 + 0.22 * math.sin(t * 5.0)) * (0.5 + 0.5 * charge)
    fx, fy = portal["x"], portal["y"]
    seam_len = PORTAL_H
    if camera is not None and camera.pitch > 0.02:
        s0 = camera.project(fx - seam_len / 2, fy)
        s1 = camera.project(fx + seam_len / 2, fy)
        cx = (s0[0] + s1[0]) / 2
        cy = (s0[1] + s1[1]) / 2
        rise = int(seam_len * (0.5 + 0.7 * camera.ground_squash()))
        _gold_pool(screen, cx, cy, seam_len * 0.7, pulse)
        # The camera-respecting view through the rift, masked to the tear hole.
        quad = [s0, s1, (s1[0], s1[1] - rise), (s0[0], s0[1] - rise)]
        try:
            buf = _render_through(target, portal["anchor"], camera,
                                  (cx, cy - rise * 0.5))
            buf = buf.convert_alpha()
            buf.blit(_aperture_mask(quad), (0, 0),
                     special_flags=pygame.BLEND_RGBA_MULT)
            if charge < 0.99:
                buf.set_alpha(int(120 + 135 * charge))
            screen.blit(buf, (0, 0))
        except Exception:
            _blit_tear(screen, _flat_peek(target, portal["anchor"], charge),
                       s0, s1, rise)
        _tear_glow(screen, s0, s1, rise, pulse * 0.9)
        _draw_seam(screen, s0, s1, t)
        return
    # Flat (pitch 0): stand the old peek panel up from the host tile.
    cx, cy = int(fx - cam_x), int(fy - cam_y)
    _gold_pool(screen, cx, cy, seam_len * 0.7, pulse)
    screen.blit(_flat_peek(target, portal["anchor"], charge),
                (cx - PORTAL_W // 2, cy - PORTAL_H))
    _draw_seam(screen, (cx - PORTAL_W // 2, cy), (cx + PORTAL_W // 2, cy), t)
