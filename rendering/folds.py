"""Seen hidden folds, wired into the live renderer.

THRESHOLD's hidden folds are direction-gated exits (Z/P/S/etc.): walk a
specific way across a bare-looking tile and you cross into another scene.
This draws them so the player can SEE through the seam before crossing -- a
shallow, one-sided peek into the target scene, the gold cut being the tear
itself.

Validated in tools/portal_poc.py and now made live. The grammar:
  - ONE-SIDED gold seam on the leading edge (the side the fold normal points
    to); a vertical cut for an E/W fold, horizontal for N/S. It wavers per
    frame (a living wound) and is only drawn when the player faces into it.
  - FOG-PEEK: the target shows solid at the seam and dissolves back into the
    host scene over ~3 tiles, so there is no hard far-edge -- just a slit.
  - LIVE actors in the target are drawn into the peek, fogged by the same
    mask, so a pursuer resolves out of the murk as it nears the seam.

Per-size masks are cached; the target Scene objects are built once per scene
load (Game._build_fold_cache), not per frame.
"""
import math
import random

import pygame
import numpy as np

from constants import TILE
from scenes.base import apply_grade
from rendering.sprites import draw_npc_sprite

SIGHT_DEPTH = 3 * TILE          # how far the peek reaches before fogging out
SEAM_DOT = 0.6                  # facing dot below which the fold is invisible
SEAM_TILES = 3                  # breadth of the slit, in tiles
SHEAR_GAIN = 0.9                # far-layer slide per px of along-seam offset
SHEAR_CAP = 2 * TILE            # max along-seam offset that shears the view
_DIRV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}

_MASK_CACHE = {}


def _fog_mask(w, h, normal):
    """Per-pixel alpha [0,1] (w,h): target solid at the seam, dissolving to 0
    SIGHT_DEPTH px into the target, feathered across the seam breadth."""
    key = (w, h, normal)
    cached = _MASK_CACHE.get(key)
    if cached is not None:
        return cached
    nx, ny = normal
    xs = np.arange(w)[:, None] * np.ones((1, h))
    ys = np.arange(h)[None, :] * np.ones((w, 1))
    if nx != 0:
        seam = 0 if nx > 0 else (w - 1)
        dist = np.abs(xs - seam)
        along, span, centre = ys, h, h / 2.0
    else:
        seam = 0 if ny > 0 else (h - 1)
        dist = np.abs(ys - seam)
        along, span, centre = xs, w, w / 2.0
    d = np.clip(dist / SIGHT_DEPTH, 0, 1)
    d2 = np.clip((d - 0.35) / 0.65, 0, 1)
    depth_f = 1 - (d2 * d2 * (3 - 2 * d2))
    half = span / 2.0
    edge = np.abs(along - centre)
    cross = np.clip(1 - (edge - (half - TILE * 0.6)) / (TILE * 0.6), 0, 1)
    cross = np.where(edge < (half - TILE * 0.6), 1.0, cross)
    mask = (depth_f * cross).astype(np.float32)
    _MASK_CACHE[key] = mask
    return mask


def _draw_seam(frame, p0, p1, t, alpha=1.0):
    """A single jittered gold stroke on the leading edge -- the cut itself.
    Re-seeded per frame so it wavers; only one side, never a box."""
    rng = random.Random(int(t * 1000) & 0xffff)
    horiz = abs(p1[0] - p0[0]) > abs(p1[1] - p0[1])
    n = max(2, (abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])) // 6)
    amp = 1.2 + 0.8 * math.sin(t * 6)
    pts = []
    for i in range(n + 1):
        f = i / n
        x = p0[0] + (p1[0] - p0[0]) * f
        y = p0[1] + (p1[1] - p0[1]) * f
        j = rng.uniform(-amp, amp)
        if horiz:
            y += j
        else:
            x += j
        pts.append((x, y))
    if len(pts) > 1:
        pygame.draw.lines(frame, (118, 102, 38), False, pts, 3)
        pygame.draw.lines(frame, (226, 200, 88), False, pts, 1)


def _blit_tear(out, peek, s0, s1, rise):
    """Stand `peek` up as a vertical panel whose base edge is the screen
    segment s0->s1 and whose top edge is that segment lifted `rise` px up the
    screen. Per-column vertical strips give the base its floor-seam slant while
    keeping the sides vertical (world height projects straight up)."""
    pw, ph = peek.get_size()
    (x0, y0), (x1, y1) = s0, s1
    cols = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    for i in range(cols):
        f = i / (cols - 1)
        bx = x0 + (x1 - x0) * f
        by = y0 + (y1 - y0) * f
        strip = peek.subsurface((min(pw - 1, int(f * pw)), 0, 1, ph))
        out.blit(pygame.transform.scale(strip, (2, rise)), (int(bx), int(by - rise)))


def draw_fold(screen, face, host_cam_x, host_cam_y, player, t, camera=None):
    """Composite one seen fold onto `screen` (already showing the host).

    face: dict with keys
        normal      -- unit (dx, dy); the side the fold is seen/crossed from
        target      -- the (already-built) target Scene
        anchor_tile -- (tx, ty) in target the peek aims at (its lit content)
        fold_px     -- (x, y) world pos of the seam in the HOST scene
    Returns True if it drew (player faced into it), else False.
    """
    nx, ny = face["normal"]
    pfx, pfy = player.facing
    if pfx * nx + pfy * ny < SEAM_DOT:
        return False                              # not facing in: invisible
    target = face["target"]
    ax, ay = face["anchor_tile"]
    fold_x, fold_y = face["fold_px"]

    if nx != 0:
        w, h = SIGHT_DEPTH, SEAM_TILES * TILE
    else:
        w, h = SEAM_TILES * TILE, SIGHT_DEPTH
    bias_x = (w // 2 - TILE) if nx else 0
    bias_y = (h // 2 - TILE) if ny else 0
    cam_x = ax * TILE + 16 - w // 2 + bias_x
    cam_y = ay * TILE + 16 - h // 2 + bias_y

    # Oblique parallax: the player's offset ALONG the seam shears the peek
    # by depth -- content at the seam stays pinned, deep content slides, so
    # standing off-axis lets you peek AROUND the tear's edge. The shear axis
    # is perpendicular to the fold normal.
    if nx != 0:
        along_off = (player.y - fold_y)           # vertical seam: shear in y
    else:
        along_off = (player.x - fold_x)           # horizontal seam: shear in x
    along_off = max(-SHEAR_CAP, min(SHEAR_CAP, along_off))
    margin = int(abs(along_off) * SHEAR_GAIN) + 2

    if nx != 0:
        big = pygame.Surface((w, h + 2 * margin))
    else:
        big = pygame.Surface((w + 2 * margin, h))
    big.fill((8, 8, 11))
    bw, bh = big.get_size()
    bcam_x = cam_x - (margin if nx == 0 else 0)
    bcam_y = cam_y - (margin if nx != 0 else 0)
    target.draw(big, bcam_x, bcam_y)
    apply_grade(big, 1.0)
    # Live actors -- drawn into the (sheared) view so a pursuer resolves out
    # of the murk as it nears the seam, sliding with the depth it sits at.
    for npc in target.npcs:
        if not getattr(npc, "alive", True) or getattr(npc, "_inside", False):
            continue
        sx = int(npc.x - bcam_x)
        sy = int(npc.y - bcam_y)
        if -32 <= sx <= bw + 32 and -32 <= sy <= bh + 32:
            draw_npc_sprite(big, sx, sy, npc.sprite_kind, npc.facing,
                            seed=id(npc) & 0xffff)

    if abs(along_off) < 0.5:
        if nx != 0:                               # crop the margin back off
            surf = big.subsurface((0, margin, w, h)).copy()
        else:
            surf = big.subsurface((margin, 0, w, h)).copy()
    else:
        arr = pygame.surfarray.array3d(big)
        out = np.empty((w, h, 3), dtype=arr.dtype)
        if nx != 0:                               # roll columns in y by depth
            seam_local = 0 if nx > 0 else (w - 1)
            for x in range(w):
                df = abs(x - seam_local) / max(1, SIGHT_DEPTH)
                shift = int(round(along_off * df * SHEAR_GAIN))
                y0 = margin + shift
                out[x] = arr[x, y0:y0 + h]
        else:                                     # roll rows in x by depth
            seam_local = 0 if ny > 0 else (h - 1)
            for y in range(h):
                df = abs(y - seam_local) / max(1, SIGHT_DEPTH)
                shift = int(round(along_off * df * SHEAR_GAIN))
                x0 = margin + shift
                out[:, y] = arr[x0:x0 + w, y]
        surf = pygame.Surface((w, h))
        pygame.surfarray.blit_array(surf, out)

    surf = surf.convert_alpha()
    mask = _fog_mask(w, h, face["normal"])
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * 255).astype(np.uint8)
    del pa

    # Tilted placement (CAMERA.md Phase 2): stand the tear up from the
    # projected floor seam so it reads anchored to the ground. Only when the
    # camera is actually pitched -- at pitch 0 we fall through to the
    # byte-identical legacy blit below.
    if camera is not None and camera.pitch > 0.02:
        seam_len = SEAM_TILES * TILE
        if nx != 0:                                # vertical seam runs along y
            w0 = (fold_x, fold_y - seam_len / 2)
            w1 = (fold_x, fold_y + seam_len / 2)
            peek = pygame.transform.rotate(surf, 90)   # along-seam -> width
        else:                                      # horizontal seam along x
            w0 = (fold_x - seam_len / 2, fold_y)
            w1 = (fold_x + seam_len / 2, fold_y)
            peek = surf
        s0 = camera.project(*w0)
        s1 = camera.project(*w1)
        rise = int(seam_len * (0.5 + 0.7 * camera.ground_squash()))
        _blit_tear(screen, peek, s0, s1, rise)
        _draw_seam(screen, s0, s1, t)
        return True

    # On-screen placement: the seam sits on the host fold tile, the peek
    # extends the way the normal points.
    cx = int(fold_x - host_cam_x)
    cy = int(fold_y - host_cam_y)
    if nx < 0:
        rx, ry = cx - w, cy - h // 2
        seam = ((cx, ry), (cx, ry + h))
    elif nx > 0:
        rx, ry = cx, cy - h // 2
        seam = ((cx, ry), (cx, ry + h))
    elif ny < 0:
        rx, ry = cx - w // 2, cy - h
        seam = ((rx, cy), (rx + w, cy))
    else:
        rx, ry = cx - w // 2, cy
        seam = ((rx, cy), (rx + w, cy))
    screen.blit(surf, (rx, ry))
    _draw_seam(screen, seam[0], seam[1], t)
    return True
