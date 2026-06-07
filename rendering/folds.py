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




# Tesseract topology: 16 vertices (a 4-bit index -> coord -1/+1 per axis x,y,z,w)
# and the 24 square FACES (two axes vary, the other two are fixed -- 6 axis-pairs
# x 4 fixed combos). We draw the faces filled + glossy, not wireframe.
_TESS_FACES = []
for _a in range(4):
    for _b in range(_a + 1, 4):
        _others = [x for x in range(4) if x not in (_a, _b)]
        for _cv in (0, 1):
            for _dv in (0, 1):
                _q = []
                for _av, _bv in ((0, 0), (0, 1), (1, 1), (1, 0)):
                    _idx = 0
                    for _axis, _val in zip([_a, _b, _others[0], _others[1]],
                                           [_av, _bv, _cv, _dv]):
                        if _val:
                            _idx |= (1 << _axis)
                    _q.append(_idx)
                _TESS_FACES.append(tuple(_q))

_GOLD_DK = (48, 37, 11)
_GOLD_HI = (196, 166, 88)


def _tess_project(a, b, size):
    """Project the tesseract's 16 vertices, rotating through the x-w and y-z
    planes by a, b. Returns (x2d, y2d, z3d) per vertex -- the double perspective
    divide (on w then z) gives the wrong-space churn; z3d sorts the faces."""
    ca, sa = math.cos(a), math.sin(a)
    cb, sb = math.cos(b), math.sin(b)
    out = []
    for idx in range(16):
        x = -1.0 if not (idx & 1) else 1.0
        y = -1.0 if not (idx & 2) else 1.0
        z = -1.0 if not (idx & 4) else 1.0
        w = -1.0 if not (idx & 8) else 1.0
        x2 = x * ca - w * sa
        w2 = x * sa + w * ca
        y2 = y * cb - z * sb
        z2 = y * sb + z * cb
        f = 1.6 / (2.6 - w2 * 0.6)           # 4D -> 3D
        X, Y, Z = x2 * f, y2 * f, z2 * f
        g = 1.6 / (2.6 - Z * 0.6)            # 3D -> 2D
        out.append((X * g * size, Y * g * size, Z))
    return out


def _tess_face_surf(a, b, t, size):
    """One tesseract drawn as GLOSSY OPAQUE gold faces (not see-through wire):
    faces painted back-to-front, shaded by depth + a moving specular (the
    shimmer). Transparent background (SRCALPHA) so only the solid metal shows."""
    pts = _tess_project(a, b, size * 0.46)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    h = size / 2
    faces = sorted(((sum(pts[i][2] for i in q) / 4.0, q) for q in _TESS_FACES),
                   key=lambda fz: fz[0])           # far first (painter's order)
    for zavg, q in faces:
        poly = [(pts[i][0] + h, pts[i][1] + h) for i in q]
        zn = max(0.0, min(1.0, (zavg + 1.2) / 2.4))
        spec = 0.5 + 0.5 * math.sin(t * 3.4 + zavg * 3.0)   # the shimmer
        f = max(0.0, min(1.0, 0.22 + 0.5 * zn + 0.30 * spec))
        col = (int(_GOLD_DK[0] + (_GOLD_HI[0] - _GOLD_DK[0]) * f),
               int(_GOLD_DK[1] + (_GOLD_HI[1] - _GOLD_DK[1]) * f),
               int(_GOLD_DK[2] + (_GOLD_HI[2] - _GOLD_DK[2]) * f))
        pygame.draw.polygon(surf, col, poly)
        pygame.draw.polygon(surf, _GOLD_DK, poly, 1)        # seam each face
    return surf


def _draw_rim(screen, quad, t, intensity):
    """The rift's edge: ONE continuous black-gold band around the opening, with
    rotating glossy tesseracts overlapped tightly along it as its churning 4D
    surface (not a string of separate cubes). A solid gold band underneath
    connects them into a single object; the tesseracts give it the shimmer.
    Sides + top full, a FAINT bottom sill so the frame fully encircles and the
    rift reads wholly THERE, not cut into the floor."""
    size = 15
    half = size // 2
    k = max(0.4, min(1.0, intensity))
    bl, br, tr, tl = quad
    # 1) The continuous connecting band: a thick gold stroke following the whole
    #    perimeter, so the edge is one unbroken object. Bottom dimmer (the sill).
    band = (int(96 * k), int(74 * k), int(24 * k))
    sill = (int(54 * k), int(42 * k), int(13 * k))
    edge = (int(150 * k), int(120 * k), int(52 * k))
    for (p, q, w, col) in ((br, tr, 9, band), (tr, tl, 9, band),
                           (tl, bl, 9, band), (bl, br, 7, sill)):
        pygame.draw.line(screen, col, p, q, w)
    pygame.draw.lines(screen, edge, False, [bl, tl, tr, br], 2)   # bright inner lip
    # 2) The tesseracts as the band's surface: tightly overlapped with rotation
    #    that ADVANCES smoothly along the perimeter, so they flow as one twisting
    #    object rather than read as discrete beads. Cached by quantised angle.
    cache = {}

    def _bead(ang):
        key = round(ang * 4) / 4.0                       # ~0.25 rad buckets
        s = cache.get(key)
        if s is None:
            s = _tess_face_surf(key, key * 0.7 + 0.4, t, size)
            if k < 0.99:
                s = s.copy()
                s.fill((int(255 * k),) * 3 + (255,),
                       special_flags=pygame.BLEND_RGBA_MULT)
            cache[key] = s
        return s

    dist = 0.0
    for (p, q, faint) in ((bl, br, True), (br, tr, False),
                          (tr, tl, False), (tl, bl, False)):
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        steps = max(1, int(ln / (size * 0.30)))          # heavy overlap = unbroken
        for i in range(steps + 1):
            f = i / steps
            x = p[0] + (q[0] - p[0]) * f
            y = p[1] + (q[1] - p[1]) * f
            s = _bead(t * 1.1 + dist * 0.05)             # smooth twist along path
            if faint:
                s = s.copy()
                s.fill((150, 150, 150, 255),
                       special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(s, (int(x - half), int(y - half)))
            dist += ln / steps


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

    # Under tilt a fold is the SAME upright door-passage as the King's portal
    # (KING_PROMPT: one rift family), oriented to the player's view, showing the
    # target room centred on where you'd arrive (anchor_tile). Pitch 0 keeps the
    # legacy flat slit below.
    if camera is not None and camera.pitch > 0.02:
        from rendering.portal import draw_rift_door
        anchor_px = (ax * TILE + TILE // 2, ay * TILE + TILE // 2)
        draw_rift_door(screen, target, anchor_px, fold_x, fold_y, camera, t,
                       cache_key=("fold", id(face)))
        return True

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
