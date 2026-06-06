"""The King's portal -- the visible 4D rift (KING_PROMPT M2).

When the player pins visibility at 100%, the King tears a rift connecting their
room to the room he stands in, and folds through. The rift wears the SAME
gold-on-black electric motif as the hidden folds (rendering.folds) -- NOT the
Threshold doorframe, which by canon never screams. Unlike a fold it is a
free-standing screaming pane the player meets head-on, and its peek into the
room beyond DESATURATES toward gray: the spaces between are colourless, the room
you stand in is where the colour lives. It is also the player's escape hatch --
step through to strand him on the wrong side.

Reuses the folds peek machinery (the target-scene draw, the fog mask, the
jittered gold seam, the stand-it-up-under-tilt blit) so the two rift kinds read
as one family.
"""
import pygame
import numpy as np

from constants import TILE
from scenes.base import apply_grade
from rendering.folds import _fog_mask, _draw_seam, _blit_tear

PORTAL_W = 3 * TILE          # peek depth into the far room
PORTAL_H = 3 * TILE          # breadth of the slit


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
    # Desaturate toward gray -- the liminal between-space has no colour.
    arr = pygame.surfarray.pixels3d(surf)
    gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
    for c in range(3):
        arr[..., c] = (arr[..., c] * 0.22 + gray * 0.78).astype(arr.dtype)
    del arr
    surf = surf.convert_alpha()
    mask = _fog_mask(w, h, (0, 1))         # solid at the seam, fading back
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * (150 + 90 * max(0.0, min(1.0, charge)))).astype(np.uint8)
    del pa
    return surf


def draw_portal(screen, portal, cam_x, cam_y, camera, t):
    """Composite the torn rift onto `screen` (already showing the host room)."""
    target = portal.get("_scene")
    if target is None:
        return
    peek = _build_peek(target, portal["anchor"], portal.get("charge", 1.0))
    fx, fy = portal["x"], portal["y"]
    seam_len = PORTAL_H
    if camera is not None and camera.pitch > 0.02:
        s0 = camera.project(fx - seam_len / 2, fy)
        s1 = camera.project(fx + seam_len / 2, fy)
        rise = int(seam_len * (0.5 + 0.7 * camera.ground_squash()))
        _blit_tear(screen, peek, s0, s1, rise)
        _draw_seam(screen, s0, s1, t)
        return
    # Flat (pitch 0): stand the pane up from the host tile.
    cx, cy = int(fx - cam_x), int(fy - cam_y)
    screen.blit(peek, (cx - PORTAL_W // 2, cy - PORTAL_H))
    _draw_seam(screen, (cx - PORTAL_W // 2, cy), (cx + PORTAL_W // 2, cy), t)
