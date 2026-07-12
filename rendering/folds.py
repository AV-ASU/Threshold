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
SEAM_DOT = 0.6                  # facing dot below which the fold is CROSSABLE
                                # (and, at pitch 0, visible -- the flat path
                                # keeps the legacy hard cut)
SEAM_VIS_MIN = 0.15             # tilt: facing dot where the pane starts to show
SEAM_VIS_FULL = 0.80            # tilt: facing dot where it reads at full
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




def _draw_rim(screen, quad, t, intensity):
    """The rift's edge per the DESIGN.md §7 spec: a dim desaturated gold band
    plus a few jagged electric arcs that flick along it and die in a few
    frames -- the 'living wound'. Re-seeded each frame so the arcs crackle
    on and off; the randomness IS the visual, so no cache needed. Cheaper
    than the old rotating tesseract beads and closer to canon."""
    k = max(0.4, min(1.0, intensity))
    bl, br, tr, tl = quad
    # 1) The continuous gold band: a thick stroke following the perimeter,
    #    so the edge reads as one unbroken object. Bottom dimmer (the sill).
    band = (int(96 * k), int(74 * k), int(24 * k))
    sill = (int(54 * k), int(42 * k), int(13 * k))
    edge = (int(150 * k), int(120 * k), int(52 * k))
    for (p, q, w, col) in ((br, tr, 9, band), (tr, tl, 9, band),
                           (tl, bl, 9, band), (bl, br, 7, sill)):
        pygame.draw.line(screen, col, p, q, w)
    pygame.draw.lines(screen, edge, False, [bl, tl, tr, br], 2)   # bright inner lip
    # 2) Jagged gold arcs that crackle along the rim. Re-seeded per frame at
    #    ~60 Hz so they flicker on and die; the canon's "living wound." A few
    #    cheap line draws -- no per-bead surfaces, no per-frame cache fill.
    rng = random.Random(int(t * 60) & 0xffff)
    sides = ((bl, br, True), (br, tr, False), (tr, tl, False), (tl, bl, False))
    bright = (int(228 * k), int(196 * k), int(94 * k))
    dim = (int(150 * k), int(118 * k), int(54 * k))
    for _ in range(rng.randint(5, 8)):
        p, q, faint = sides[rng.randint(0, 3)]
        f = rng.uniform(0.05, 0.95)
        x = p[0] + (q[0] - p[0]) * f
        y = p[1] + (q[1] - p[1]) * f
        # Jag tangent so the arc trails along the rim, not straight off it.
        tx, ty = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(tx, ty) or 1.0
        tx /= ln; ty /= ln
        nx, ny = -ty, tx
        pts = [(x, y)]
        seg = rng.randint(2, 4)
        step = rng.uniform(4, 9)
        for _ in range(seg):
            x += tx * step + nx * rng.uniform(-5, 5)
            y += ty * step + ny * rng.uniform(-5, 5)
            pts.append((x, y))
        col = dim if faint else bright
        pygame.draw.lines(screen, col, False, pts, 1)


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
    dot = pfx * nx + pfy * ny
    target = face["target"]
    ax, ay = face["anchor_tile"]
    fold_x, fold_y = face["fold_px"]
    # Optional per-fold CHARGE (set per-frame from Scene.fold_charge_fn):
    # 1.0 is a formed, crossable fold (the default; byte-identical path);
    # below 1.0 the pane renders mid-formation (the grove's way down
    # clarifying with evidence); 0 is not drawn at all (a gated-shut fold
    # reads as floor).
    charge = face.get("charge", 1.0)
    if charge <= 0.0:
        return False

    # Under tilt a fold is the SAME upright door-passage as the King's portal
    # (KING_PROMPT: one rift family), standing along its WORLD seam (the line
    # across the fold normal) so it foreshortens like a wall, showing the
    # target room centred on where you'd arrive (anchor_tile). Pitch 0 keeps
    # the legacy flat slit below.
    if camera is not None and camera.pitch > 0.02:
        # Smooth approach-angle falloff (the pane rule): full when faced
        # head-on, thinning + dimming to nothing as the approach goes
        # oblique -- the pane has no back. The old binary SEAM_DOT cut made
        # the rift blink in and out of existence; a real object fades with
        # the angle you hold it at. CROSSING stays gated at SEAM_DOT
        # (Scene.find_exit_at), so you can see a fold a little before you
        # can take it.
        f = (dot - SEAM_VIS_MIN) / (SEAM_VIS_FULL - SEAM_VIS_MIN)
        vis = max(0.0, min(1.0, f))
        if vis <= 0.0:
            return False
        vis = vis * vis * (3.0 - 2.0 * vis)          # smoothstep the ends
        from rendering.portal import draw_rift_door
        anchor_px = (ax * TILE + TILE // 2, ay * TILE + TILE // 2)
        draw_rift_door(screen, target, anchor_px, fold_x, fold_y, camera, t,
                       formed=(charge >= 0.999), charge=charge,
                       cache_key=("fold", id(face)),
                       seam_dir=(-ny, nx), vis=vis)
        return True

    if dot < SEAM_DOT:
        return False                              # not facing in: invisible

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
                            seed=getattr(npc, 'sprite_seed', 0))

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
    # Pitch-0 (dev) path: a mid-formation fold just dims the peek. The
    # charge==1.0 default keeps this byte-identical.
    pa[:, :] = (mask * (255 * charge)).astype(np.uint8)
    del pa

    # (Tilt is handled up top by the shared rift door; this is the pitch-0 path.)

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
