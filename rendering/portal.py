"""The King's portal -- the visible 4D rift (KING_PROMPT M2 + the look pass).

When the player pins visibility at 100%, the King tears a rift connecting their
room to the room he stands in, and folds through. The rift wears the SAME
gold-on-black electric motif as the hidden folds (rendering.folds) -- NOT the
Threshold doorframe, which by canon never screams.

PSEUDO-3D (KING_PROMPT decision): the rift is never a flat screen-space decal.
The tear and the view through it project through the one camera seam
(`camera.project`) and stand up off the ground, and the rift is a LIGHT in the
scene -- a gold light-pool spills onto the floor at its base and an additive
glow climbs the tear -- so it reads as a real oriented hole in space under the
tilt, not a sticker on the floor. Its peek into the room beyond DESATURATES
toward gray (the spaces between are colourless; the room you stand in keeps the
colour) and doubles as the window you flee through.

Reuses the folds peek machinery (the target-scene draw, the fog mask, the
jittered gold seam, the stand-it-up-under-tilt blit) so the two rift kinds read
as one family.
"""
import math

import pygame
import numpy as np

from constants import TILE
from scenes.base import apply_grade
from rendering.folds import _fog_mask, _draw_seam, _blit_tear

PORTAL_W = 3 * TILE          # peek depth into the far room
PORTAL_H = 3 * TILE          # breadth of the slit

_POOL_CACHE = {}
_GLOW_CACHE = {}


def _build_peek(target, anchor_tile, charge):
    """A desaturated, slit-masked peek into the target room. `charge` 0..1 fades
    the rift up as it forms."""
    w, h = PORTAL_W, PORTAL_H
    ax, ay = anchor_tile
    cam_x = ax * TILE + 16 - w // 2
    cam_y = ay * TILE + 16 - h // 2
    surf = pygame.Surface((w, h))
    surf.fill((8, 8, 11))
    target.draw(surf, cam_x, cam_y)
    apply_grade(surf, 1.0)
    # Desaturate toward gray + sink toward black -- the liminal between-space has
    # no colour and little light (the gold seam/pool supply the gold).
    arr = pygame.surfarray.pixels3d(surf)
    gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
    for c in range(3):
        arr[..., c] = (arr[..., c] * 0.18 + gray * 0.62).astype(arr.dtype)
    del arr
    surf = surf.convert_alpha()
    mask = _fog_mask(w, h, (0, 1))         # solid at the seam, fading back
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * (150 + 90 * max(0.0, min(1.0, charge)))).astype(np.uint8)
    del pa
    return surf


def _gold_pool(screen, cx, cy, r, intensity):
    """An additive GOLD light-pool on the floor at the rift's base -- the rift is
    a light in the scene, not an outline. Squashed to lie on the ground plane so
    it reads in 3D. Cached per radius (RGB falloff baked in; additive ignores
    alpha, so black adds nothing)."""
    r = max(10, int(r))
    base = _POOL_CACHE.get(r)
    if base is None:
        base = pygame.Surface((r * 2, r * 2))
        base.fill((0, 0, 0))
        for rr in range(r, 0, -1):
            f = 1.0 - rr / r                       # 0 at the rim -> 1 at centre
            ff = f * f
            pygame.draw.circle(base, (int(150 * ff), int(112 * ff),
                                      int(34 * ff)), (r, r), rr)
        _POOL_CACHE[r] = base
    k = max(0.2, min(1.0, intensity))
    pool = pygame.transform.scale(base, (r * 2, max(2, int(r * 1.1))))
    if k < 0.99:                                   # dim by the charge/pulse
        pool = pool.copy()
        pool.fill((int(255 * k), int(255 * k), int(255 * k)),
                  special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(pool, (int(cx - r), int(cy - r * 0.55)),
                special_flags=pygame.BLEND_RGB_ADD)


def _tear_glow(screen, s0, s1, rise, intensity):
    """A soft additive gold glow climbing the standing tear (its 'screaming'
    light), brightest at the base seam and fading up. Cached by (width, rise)."""
    x0, y0 = s0
    x1, y1 = s1
    w = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    rise = max(2, int(rise))
    key = (w, rise)
    glow = _GLOW_CACHE.get(key)
    if glow is None:
        glow = pygame.Surface((w, rise))
        glow.fill((0, 0, 0))
        for j in range(rise):
            f = 1.0 - j / rise                     # bright at base, fades up
            ff = f * f
            col = (int(120 * ff), int(92 * ff), int(28 * ff))
            pygame.draw.line(glow, col, (0, rise - 1 - j), (w, rise - 1 - j))
        _GLOW_CACHE[key] = glow
    k = max(0.2, min(1.0, intensity))
    g = glow
    if k < 0.99:
        g = glow.copy()
        g.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
    bx = int(min(x0, x1))
    by = int(min(y0, y1) - rise)
    screen.blit(g, (bx, by), special_flags=pygame.BLEND_RGB_ADD)


def draw_portal(screen, portal, cam_x, cam_y, camera, t):
    """Composite the torn rift onto `screen` (already showing the host room)."""
    target = portal.get("_scene")
    if target is None:
        return
    charge = max(0.0, min(1.0, portal.get("charge", 1.0)))
    pulse = (0.78 + 0.22 * math.sin(t * 5.0)) * (0.5 + 0.5 * charge)
    peek = _build_peek(target, portal["anchor"], charge)
    fx, fy = portal["x"], portal["y"]
    seam_len = PORTAL_H
    if camera is not None and camera.pitch > 0.02:
        s0 = camera.project(fx - seam_len / 2, fy)
        s1 = camera.project(fx + seam_len / 2, fy)
        cx = (s0[0] + s1[0]) / 2
        cy = (s0[1] + s1[1]) / 2
        rise = int(seam_len * (0.5 + 0.7 * camera.ground_squash()))
        _gold_pool(screen, cx, cy, seam_len * 0.7, pulse)   # light on the ground
        _blit_tear(screen, peek, s0, s1, rise)              # the window stands up
        _tear_glow(screen, s0, s1, rise, pulse * 0.9)       # glow climbs it
        _draw_seam(screen, s0, s1, t)                       # the gold cut
        return
    # Flat (pitch 0): stand the pane up from the host tile.
    cx, cy = int(fx - cam_x), int(fy - cam_y)
    _gold_pool(screen, cx, cy, seam_len * 0.7, pulse)
    screen.blit(peek, (cx - PORTAL_W // 2, cy - PORTAL_H))
    _draw_seam(screen, (cx - PORTAL_W // 2, cy), (cx + PORTAL_W // 2, cy), t)
