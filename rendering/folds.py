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

from constants import TILE, SCREEN_W, SCREEN_H
from scenes.base import apply_grade
from rendering.sprites import draw_npc_sprite

SIGHT_DEPTH = 3 * TILE          # how far the peek reaches before fogging out
SEAM_DOT = 0.6                  # facing dot below which the fold is invisible
SEAM_TILES = 3                  # breadth of the slit, in tiles
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


def draw_fold(screen, face, host_cam_x, host_cam_y, player, t):
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

    surf = pygame.Surface((w, h))
    surf.fill((8, 8, 11))
    target.draw(surf, cam_x, cam_y)
    apply_grade(surf, 1.0)
    # Live actors in the target -- fogged by the same mask, so a pursuer
    # resolves out of the murk as it nears the seam.
    for npc in target.npcs:
        if not getattr(npc, "alive", True) or getattr(npc, "_inside", False):
            continue
        sx = int(npc.x - cam_x)
        sy = int(npc.y - cam_y)
        if -32 <= sx <= w + 32 and -32 <= sy <= h + 32:
            draw_npc_sprite(surf, sx, sy, npc.sprite_kind, npc.facing,
                            seed=id(npc) & 0xffff)

    surf = surf.convert_alpha()
    mask = _fog_mask(w, h, face["normal"])
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * 255).astype(np.uint8)
    del pa

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
