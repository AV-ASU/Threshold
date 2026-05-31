"""Non-Euclidean portal / hidden-fold proof of concept (offline, headless).

THRESHOLD already has *direction-gated* hidden folds: walk west across a
bare-looking tile in the cornfield maze and you step into the curse-grove
(`scenes/threshold_extras.py`, the `Z`/`P`/`S` exits). They are
mechanically invisible -- nothing on screen says a fold is there.

This POC explores *showing* a fold: compositing a live view of the
target scene into the host scene so the player can SEE through the seam
before crossing -- a non-Euclidean window -- without committing to the
live renderer yet.

It is the reference for the eventual live integration in `draw_world`.
The validated visual grammar, built and eyeballed in motion:

  1. SEAM, ONE-SIDED. The gold line *is* the portal -- a single jittered
     stroke on the leading edge (the side the fold normal points to), not
     a four-sided frame. A horizontal (E/W) normal gives a vertical cut;
     a vertical (N/S) normal gives a horizontal one. The line wavers
     per-frame so it reads as a living wound, and culls entirely when the
     player faces away (it only exists from the fold's angle).

  2. FOG-PEEK. You do NOT see an infinite view of the target. The target
     is solid at the seam and dissolves back into the HOST scene's own
     terrain over ~3 tiles of depth (`fog_mask`). The "fog" is the host
     reasserting itself -- so the far edge never hard-cuts into a
     rectangle, and you get a shallow peek, never a floor plan. Stealth:
     you must commit and cross to see the whole room.

  3. OBLIQUE PARALLAX. Standing off-axis (above/below a vertical seam)
     shears the view by depth -- content at the seam stays pinned, content
     deep in the target slides -- so you peek AROUND the edge of the tear
     at an angle and reveal what was hidden head-on (`render_slit`'s
     `along_off`). You trade straight depth for angle; you never see it all.

  4. LIVE ACTORS. The target's actors are drawn INTO the slit, fogged by
     the same mask -- so a pursuer resolves out of the murk as it nears
     the seam. "Follows a beat behind" made visible: you watch it come.

  5. GAZE-THROUGH (two-way). An actor near the seam can see YOU through
     the fold and raise visibility -- but its gaze strength is the SAME
     fog-clarity value that gates what you see (`depth_clarity`). Deep in
     the murk it is blind to you too; only at the seam does the gaze lock.
     Look away -> fold culls -> gaze breaks -> visibility decays.

CONSISTENCY RULE (for the live pursuit, Stage 3): folds are the cult's
domain -- enemies cross THEM. Mundane transitions (doors, ladders, ropes)
are player-only; pursuers cannot follow through architecture, only through
the wrongness of the world. Breaking to a normal exit loses the chase.

Run (headless, writes PNGs to /tmp):
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python tools/portal_poc.py

Nothing here is wired into the game.
"""
import os
import sys
import math
import random

import pygame
import numpy as np

from constants import SCREEN_W, SCREEN_H, TILE


# ---- tunables (mirror the live feel without importing the game) ----
SIGHT_DEPTH = 3 * TILE      # how far the peek reaches before fogging to host
SEAM_DOT = 0.6              # facing dot below which the fold culls (one-sided)
SHEAR_GAIN = 0.9           # far-layer slide per px of along-seam offset
VIS_RISE = 0.85            # visibility/sec at full gaze through a fold
VIS_DECAY = 0.45           # visibility/sec bled off when the fold is unseen


class PortalFace:
    """One side of a fold: an opening in the host scene that shows
    `target_scene`, entered/seen only from the `normal` direction.

    normal       -- unit (dx, dy); the side the cut is seen/crossed from.
    anchor_tile  -- (tx, ty) in the target the peek is centred on (aim it
                    at the target's lit content so a dark fold still reads).
    fold_tile    -- (tx, ty) in the HOST: where the seam sits.
    sight_tiles  -- depth of the peek; seam_tiles -- height/breadth of it.
    """

    def __init__(self, normal, target_key, anchor_tile, fold_tile,
                 sight_tiles=3, seam_tiles=3):
        self.normal = normal
        self.target_key = target_key
        self.anchor_tile = anchor_tile
        self.fold_tile = fold_tile
        self.sight_tiles = sight_tiles
        self.seam_tiles = seam_tiles


# ----------------------------------------------------------------------
# Core rendering
# ----------------------------------------------------------------------
def render_view(scene, cam_x, cam_y, w, h):
    """An in-game viewport of `scene` (terrain + decorations) to a w x h
    surface at the given camera. Mirrors what the live draw_world shows."""
    surf = pygame.Surface((w, h))
    surf.fill((8, 8, 11))
    scene.draw(surf, cam_x, cam_y)        # terrain + decorations (+ wrap clones)
    return surf


def fog_mask(w, h, normal, sight_depth=SIGHT_DEPTH):
    """Per-pixel alpha for the slit: the target is SOLID at the seam and
    dissolves to 0 (host shows through) `sight_depth` px perpendicular into
    the target, with a soft fade across the seam's breadth at the ends.

    The seam sits on the side `normal` points to; the peek extends the
    opposite way. Returns float32 [0,1] of shape (w, h)."""
    nx, ny = normal
    xs = np.arange(w)[:, None] * np.ones((1, h))
    ys = np.arange(h)[None, :] * np.ones((w, 1))
    if nx != 0:                                   # vertical seam, peek horizontal
        seam = 0 if nx > 0 else (w - 1)
        dist = np.abs(xs - seam)
        along, span, centre = ys, h, h / 2.0
    else:                                         # horizontal seam, peek vertical
        seam = 0 if ny > 0 else (h - 1)
        dist = np.abs(ys - seam)
        along, span, centre = xs, w, w / 2.0
    # depth fade: hold strong near the seam, dissolve the far third
    d = np.clip(dist / sight_depth, 0, 1)
    d2 = np.clip((d - 0.35) / 0.65, 0, 1)
    depth_f = 1 - (d2 * d2 * (3 - 2 * d2))        # smoothstep
    # breadth fade: full in the middle band, feather the last ~0.6 tile
    half = span / 2.0
    edge = np.abs(along - centre)
    cross = np.clip(1 - (edge - (half - TILE * 0.6)) / (TILE * 0.6), 0, 1)
    cross = np.where(edge < (half - TILE * 0.6), 1.0, cross)
    return (depth_f * cross).astype(np.float32)


def depth_clarity(dist_from_seam, sight_depth=SIGHT_DEPTH):
    """The 1-D depth fade alone, as a scalar: 1 at the seam -> 0 at
    `sight_depth`. Drives BOTH what the player sees and -- crucially --
    how strongly an actor at that depth can gaze back (the fold is blind
    in both directions until something reaches the cut)."""
    d = min(1.0, max(0.0, dist_from_seam / sight_depth))
    d2 = min(1.0, max(0.0, (d - 0.35) / 0.65))
    return 1 - (d2 * d2 * (3 - 2 * d2))


def render_slit(target, anchor_tile, normal, w, h, *, along_off=0.0,
                draw_actors=None, sight_depth=SIGHT_DEPTH):
    """Composite the target into a w x h slit surface (with per-pixel fog
    alpha), ready to blit over the already-drawn host.

    along_off   -- player offset ALONG the seam (px); applies the oblique
                   depth-shear so the far layer slides and you peek around.
    draw_actors -- optional callable(surf, cam_x, cam_y) that draws the
                   target's live actors into the view at the same camera.
    """
    nx, ny = normal
    bias = (w // 2 - TILE) if nx else 0
    biasy = (h // 2 - TILE) if ny else 0
    cam_x = anchor_tile[0] * TILE + 16 - w // 2 + bias
    cam_y = anchor_tile[1] * TILE + 16 - h // 2 + biasy

    if abs(along_off) < 0.5 or nx == 0:
        # No shear (dead-on, or seam axis is horizontal -> shear would be x;
        # the POC demonstrates the vertical-seam case).
        surf = render_view(target, cam_x, cam_y, w, h)
        from scenes.base import apply_grade
        apply_grade(surf, 1.0)
        if draw_actors:
            draw_actors(surf, cam_x, cam_y)
    else:
        # Depth-shear: render taller, roll each column by depth*offset.
        margin = int(abs(along_off) * SHEAR_GAIN) + 2
        big = render_view(target, cam_x, cam_y - margin, w, h + 2 * margin)
        from scenes.base import apply_grade
        apply_grade(big, 1.0)
        if draw_actors:
            draw_actors(big, cam_x, cam_y - margin)
        arr = pygame.surfarray.array3d(big)
        out = np.empty((w, h, 3), dtype=arr.dtype)
        seam_local = 0 if nx > 0 else (w - 1)
        for x in range(w):
            depth_frac = abs(x - seam_local) / max(1, sight_depth)
            shift = int(round(along_off * depth_frac * SHEAR_GAIN))
            y0 = margin + shift
            out[x] = arr[x, y0:y0 + h]
        surf = pygame.Surface((w, h))
        pygame.surfarray.blit_array(surf, out)
        surf = surf.convert_alpha()

    surf = surf.convert_alpha()
    mask = fog_mask(w, h, normal, sight_depth)
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * 255).astype(np.uint8)
    del pa
    return surf, cam_x, cam_y


def draw_seam(frame, p0, p1, alpha, t, gaze=0.0):
    """The gold cut on the leading edge: a single jittered stroke,
    re-seeded per frame so it wavers. `gaze` (0..1) makes it pulse
    brighter and more agitated -- the fold conducting a gaze through it."""
    if alpha <= 0.01:
        return
    rng = random.Random(int(t * 1000) & 0xffff)
    horiz = abs(p1[0] - p0[0]) > abs(p1[1] - p0[1])
    n = max(2, (abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])) // 6)
    amp = 1.2 + 0.8 * math.sin(t * 6) + 2.0 * gaze
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
    halo = (118, 102, 38)
    core = (min(255, 200 + int(55 * gaze)), 198, 86)
    pygame.draw.lines(frame, halo, False, pts, 3)
    pygame.draw.lines(frame, core, False, pts, 1)


# ----------------------------------------------------------------------
# Self-test: render a verification still to /tmp
# ----------------------------------------------------------------------
def _selftest():
    from scenes import load_scene
    from scenes.base import apply_grade
    from rendering.sprites import draw_npc_sprite

    host = load_scene("cornfield_maze")
    grove = load_scene("curse_grove")
    face = PortalFace(normal=(-1, 0), target_key="curse_grove",
                      anchor_tile=(7, 5), fold_tile=(6, 10))
    fx, fy = face.fold_tile[0] * TILE + 16, face.fold_tile[1] * TILE + 16
    cam_x = (fx + TILE) - SCREEN_W // 2
    cam_y = fy - SCREEN_H // 2

    f = pygame.Surface((SCREEN_W, SCREEN_H))
    f.fill((8, 8, 11))
    host.draw(f, cam_x, cam_y)
    apply_grade(f, 1.0)

    w = face.sight_tiles * TILE
    h = face.seam_tiles * TILE
    # a pursuer resolving at the seam, with lit eyes
    seam_wx = face.anchor_tile[0] * TILE + 16 - w // 2 + (w // 2 - TILE) + (w - 1)

    def actors(surf, scx, scy):
        ax = seam_wx - 10
        ay = face.anchor_tile[1] * TILE + 16
        draw_npc_sprite(surf, int(ax - scx), int(ay - scy),
                        "cultist", (1, 0), seed=4242)

    slit, scx, scy = render_slit(grove, face.anchor_tile, face.normal, w, h,
                                 draw_actors=actors)
    cx = int(fx - cam_x)
    cy = int(fy - cam_y)
    f.blit(slit, (cx - w, cy - h // 2))
    draw_seam(f, (cx, cy - h // 2), (cx, cy + h // 2), 1.0, 1.4, gaze=0.8)

    out = "/tmp/portal_poc_selftest.png"
    pygame.image.save(f, out)
    print("portal_poc self-test OK ->", out)


if __name__ == "__main__":
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    _selftest()
