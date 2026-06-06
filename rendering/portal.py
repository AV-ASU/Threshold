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
import random

import pygame
import numpy as np

from constants import TILE, SCREEN_W, SCREEN_H
from scenes.base import apply_grade
from rendering.folds import _fog_mask, _draw_seam, _blit_tear

PORTAL_W = 3 * TILE          # peek depth (flat fallback only)
PORTAL_H = 3 * TILE          # breadth of the slit

_POOL_CACHE = {}
_GLOW_CACHE = {}

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


def _tess_variants(t, size, k):
    """`k` glossy tesseract stamps at staggered rotations, all turning. Computed
    per frame (cheap: a few dozen filled faces each)."""
    return [_tess_face_surf(t * 1.25 + v * 0.9, t * 0.85 + v * 0.55, t, size)
            for v in range(k)]


def _draw_rim(screen, quad, t, intensity):
    """A gapless, buzzing rim of rotating glossy tesseracts around the rift's
    opening (the black-gold 4D edge). Sides + top full, a FAINT bottom sill so
    the frame fully encircles and the rift reads wholly THERE, not cut into the
    floor. Opaque metal faces (alpha-blit, not additive); dense overlap = no
    gaps; per-stamp jitter = the buzz."""
    size = 15
    half = size // 2
    k = max(0.4, min(1.0, intensity))
    variants = _tess_variants(t, size, 5)
    if k < 0.99:
        variants = [s.copy() for s in variants]
        for s in variants:
            s.fill((int(255 * k),) * 3 + (255,),
                   special_flags=pygame.BLEND_RGBA_MULT)
    faint = [s.copy() for s in variants]                # the bottom sill
    for s in faint:
        s.fill((120, 120, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)
    bl, br, tr, tl = quad
    edges = [(bl, br, faint), (br, tr, variants),
             (tr, tl, variants), (tl, bl, variants)]
    rng = random.Random(int(t * 90) & 0xffff)
    vi = 0
    for (p, q, vs) in edges:
        ln = math.hypot(q[0] - p[0], q[1] - p[1])
        steps = max(1, int(ln / (size * 0.40)))         # overlap -> no gaps
        for i in range(steps + 1):
            f = i / steps
            x = p[0] + (q[0] - p[0]) * f + rng.uniform(-1.6, 1.6)
            y = p[1] + (q[1] - p[1]) * f + rng.uniform(-1.6, 1.6)
            screen.blit(vs[vi % len(vs)], (int(x - half), int(y - half)))
            vi += 1


# ---- the camera-respecting view through the rift -----------------------------

def _render_through(target, anchor_px, camera, origin):
    """Render `target` with a portal-camera that matches the live tilt (pitch /
    yaw / scale) and is aimed so the EXACT emergence point `anchor_px` (world x,
    y -- where the King stands / you walk out) projects to `origin` on screen.
    Returns a full-screen Surface of the tilted room. Same renderer as the near
    side, so the far side's floor/walls recede in the same perspective."""
    from rendering.camera import Camera
    from rendering.skybox import draw_skybox
    from scenes.base import draw_terrain_tilted, _tilt_tile_box, _TILT_WALL_RISE
    ax, ay = anchor_px
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
    # Liminal: sink hard toward BLACK (the between has almost no colour or
    # light -- the gold rim/pool supply the gold; the room reads as a dim shape).
    arr = pygame.surfarray.pixels3d(buf)
    gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
    for c in range(3):
        arr[..., c] = (arr[..., c] * 0.18 + gray * 0.34).astype(arr.dtype)
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
            pygame.draw.circle(base, (int(108 * ff), int(80 * ff),
                                      int(24 * ff)), (r, r), rr)
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
    # EXACT emergence point in the target room (where the King stands / you walk
    # out): the dynamic world pos, falling back to the anchor tile centre.
    tp = portal.get("target_pos")
    anchor_px = tp if tp else (portal["anchor"][0] * TILE + TILE // 2,
                               portal["anchor"][1] * TILE + TILE // 2)
    if camera is not None and camera.pitch > 0.02:
        # An UPRIGHT door standing on the ground (like the Threshold sprite):
        # base on the floor at the rift tile, rising vertically + foreshortened
        # by the tilt, taller than wide. Smaller than a slit-in-the-floor read.
        bx, by = camera.project(fx, fy)
        sq = camera.ground_squash()
        doorW = max(18, int(seam_len * camera.scale * 0.7))
        doorH = max(22, int(seam_len * camera.scale * (0.62 + 1.05 * sq)))
        top = by - doorH
        quad = [(bx - doorW / 2, by), (bx + doorW / 2, by),
                (bx + doorW / 2, top), (bx - doorW / 2, top)]
        # Ground-contact shadow so the door bites the floor (anchored, not
        # floating), then the gold light it spills on the ground.
        shadow = pygame.Surface((doorW + 10, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 120), shadow.get_rect())
        screen.blit(shadow, (int(bx - doorW / 2 - 5), int(by - 6)))
        _gold_pool(screen, bx, by, doorW * 0.7, pulse)      # light spilt on floor
        # The camera-respecting view through the upright door -- the room beyond
        # at 1:1 scale, centred on the EXACT spot you'd emerge, cropped to the
        # door and sunk toward black so the rift reads black-gold.
        try:
            buf = _render_through(target, anchor_px, camera, (bx, (by + top) / 2))
            rect = pygame.Rect(int(bx - doorW / 2), int(top),
                               doorW, doorH).clip(screen.get_rect())
            if rect.width > 2 and rect.height > 2:
                win = buf.subsurface(rect).copy()
                win.fill((118, 118, 118), special_flags=pygame.BLEND_RGB_MULT)
                if charge < 0.99:
                    win.set_alpha(int(120 + 135 * charge))
                screen.blit(win, rect.topleft)
        except Exception:
            _blit_tear(screen, _flat_peek(target, portal["anchor"], charge),
                       (bx - doorW / 2, by), (bx + doorW / 2, by), doorH)
        _draw_rim(screen, quad, t, pulse)                   # the buzzing 4D edge
        return
    # Flat (pitch 0): stand the old peek panel up from the host tile.
    cx, cy = int(fx - cam_x), int(fy - cam_y)
    _gold_pool(screen, cx, cy, seam_len * 0.7, pulse)
    screen.blit(_flat_peek(target, portal["anchor"], charge),
                (cx - PORTAL_W // 2, cy - PORTAL_H))
    _draw_seam(screen, (cx - PORTAL_W // 2, cy), (cx + PORTAL_W // 2, cy), t)
