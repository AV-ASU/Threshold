"""THE KING IN YELLOW as a true volumetric object -- PROTOTYPE (CAMERA.md tier 3).

Translates the flat pallid-mask King (`sprites._draw_king`) into a 3D form that
renders from every angle: a porcelain MASK-PLATE pinned in object space in front
of a glowing YELLOW body. The plate's front (object angle 0) points at the
player; the camera's yaw then decides what we see -- face-on, three-quarter, a
thin profile crescent, or the Yellow back when he turns away. Surface features
(the two void eyes, the tear-streaks) are pinned at object `(theta, h)` so they
slide around and self-occlude on the turn, exactly like the pseudo3d Watcher.

Isolated + previewable (`tools/preview_king3d.py`); NOT wired into the live game.
This proves build steps (1) calm shell + Yellow back and (2) wrapping features.
Shards / arms / world-space particles / threat states come next.
"""
import math
import random
import pygame

# Object-space ovoid head: (height, half_width_x, half_depth_z), chin(-) -> crown(+).
# A face is taller than wide and a touch deeper than broad (it protrudes), so the
# silhouette stays round-ish from any yaw while the FEATURES do the turning.
# Depth (hd) is deliberately SHALLOW vs width (hw): this is a flat-ish MASK,
# not a round head, so edge-on (yaw 90) it reads as a flat plate.
_SEC = [
    (-14, 5.0, 2.4),     # chin
    (-10, 7.6, 3.0),     # jaw
    (-5,  9.3, 3.6),     # cheeks
    (0,   9.7, 3.9),     # widest, the eye line
    (5,   9.0, 3.6),     # brow
    (10,  7.2, 3.0),
    (14,  4.4, 2.2),     # crown
]
_PORC    = (212, 204, 186)
_PORC_LO = (150, 144, 128)
_PORC_DK = (86, 82, 74)
_PORC_HI = (240, 234, 216)
_HOLLOW  = (6, 5, 8)               # the void eyes / tear: pure black
_VOIDC   = (9, 8, 12)              # the dark void INTERIOR of the mask
_BODY    = (120, 92, 30)           # the Yellow body mass behind the plate
_BODY_LO = (70, 52, 18)
_GOLD    = (210, 172, 56)
_GOLD_DK = (150, 104, 26)
_GOLD_HI = (248, 228, 150)

_PLATE = 1.55                       # the mask plate spans +/- this in object-theta


def _shade(col, f):
    return (max(0, min(255, int(col[0] * f))),
            max(0, min(255, int(col[1] * f))),
            max(0, min(255, int(col[2] * f))))


def _hwd(h):
    """Interpolated (half_width, half_depth) at object height h."""
    if h <= _SEC[0][0]:
        return _SEC[0][1], _SEC[0][2]
    if h >= _SEC[-1][0]:
        return _SEC[-1][1], _SEC[-1][2]
    for j in range(len(_SEC) - 1):
        h0, h1 = _SEC[j][0], _SEC[j + 1][0]
        if h0 <= h <= h1:
            f = (h - h0) / (h1 - h0)
            return (_SEC[j][1] + f * (_SEC[j + 1][1] - _SEC[j][1]),
                    _SEC[j][2] + f * (_SEC[j + 1][2] - _SEC[j][2]))
    return _SEC[-1][1], _SEC[-1][2]


def _surface(theta, h, yaw, push=1.0):
    """A point on the mask surface at object-angle theta (0 = front of the face)
    and height h, rotated by yaw about the vertical axis. Returns
    (x_offset, y_offset_up, depth) where depth>0 points toward the camera."""
    hw, hd = _hwd(h)
    ox = math.sin(theta) * hw * push
    oz = math.cos(theta) * hd * push
    rx = ox * math.cos(yaw) + oz * math.sin(yaw)
    rz = -ox * math.sin(yaw) + oz * math.cos(yaw)
    return rx, h, rz


_CRACKS = None


def _crack_net():
    """Porcelain craquelure authored in object (theta, h) space: a central
    mold seam + scattered branching hairlines. This is the SAME network the
    shatter will fracture along, so the calm detail carries onto the shards.
    Seeded -> stable (never boils). Cached. Returns list of polylines, each a
    list of (theta, h); the first entries are the 'deep' cracks that seep gold."""
    global _CRACKS
    if _CRACKS is not None:
        return _CRACKS
    rng = random.Random(7)
    cracks = []
    # the mold seam down the centre (jagged a touch), and two long meridians
    for base in (0.0, -0.62, 0.62):
        seam = []
        for h in range(13, -15, -2):
            seam.append((base + rng.uniform(-0.06, 0.06), h))
        cracks.append(seam)
    # scattered craquelure: short branching hairlines across the face
    for _ in range(12):
        th0 = rng.uniform(-1.2, 1.2); h0 = rng.uniform(-12, 12)
        n = rng.randint(2, 4); pl = [(th0, h0)]; th, h = th0, h0
        ad = rng.uniform(0, math.tau)
        for _ in range(n):
            ad += rng.uniform(-0.8, 0.8)
            th += math.cos(ad) * rng.uniform(0.12, 0.30)
            h += math.sin(ad) * rng.uniform(2.0, 4.0)
            pl.append((th, h))
        cracks.append(pl)
    _CRACKS = cracks
    return cracks


def _draw_runs(surf, pts_or_none, col, width):
    """Draw a polyline that may dip behind the form: break it into contiguous
    runs of on-screen (facing) points and stroke each run."""
    run = []
    for p in list(pts_or_none) + [None]:
        if p is None:
            if len(run) >= 2:
                pygame.draw.lines(surf, col, False, run, width)
            run = []
        else:
            run.append(p)


def draw_king3d(surf, cx, cy, yaw, t, threat=0.0, scale=2.4, light=-0.6):
    """Draw the calm volumetric King mask centred at (cx, cy), turned `yaw`
    radians off face-on (0 = looking at the camera, pi = turned away), animated
    by `t`. `threat` 0..1 deepens the voids + seeps gold (calm preview = 0).

    Model: a glowing YELLOW BODY (a round ovoid mass) with a porcelain MASK
    PLATE on its front. The plate is only the front-FACING arc of the face, so
    as the head turns it foreshortens to a crescent and the Yellow behind is
    revealed -- a mask, not a solid head."""
    bob = math.sin(t * 1.1) * 1.5

    def P(rx, h):
        return (cx + rx * scale, cy - (h + bob) * scale)

    heights = [h * 0.5 for h in range(int(_SEC[0][0] * 2), int(_SEC[-1][0] * 2) + 1)]

    # --- 1) the mask INTERIOR is a dark VOID, and a small glow sits RECESSED
    # at its centre with void all around it. The glow rides toward the BACK as
    # he turns (-recess*sin yaw), so at profile it reads as recessed INTO the
    # flat mask. Drawn BEFORE the plate: face-on the porcelain contains it; it
    # is revealed as the plate foreshortens on the turn.
    body_l, body_r = [], []
    for h in heights:
        hw, hd = _hwd(h)
        half = math.hypot(hw * math.cos(yaw), hd * math.sin(yaw)) * scale
        x0, y0 = P(0, h)
        body_l.append((x0 - half, y0))
        body_r.append((x0 + half, y0))
    body_poly = body_r + body_l[::-1]
    if len(body_poly) >= 3:
        pygame.draw.polygon(surf, _VOIDC, body_poly)        # the dark void interior
        pygame.draw.polygon(surf, _BODY_LO, body_poly, 1)
    # ONE glow, drawn BEHIND the plate (the mask occludes it; it haloes out as
    # it grows). It starts as the small dim calm core and GROWS in size +
    # brightness with threat -- same gold character, just bigger/brighter.
    recess = 5.0
    gcx = cx - recess * math.sin(yaw) * scale               # recedes to the back on the turn
    gcy = cy - bob * scale
    gr = (3.2 + 13.0 * threat) * scale                      # calm core -> max bloom
    peak = int(170 + 80 * threat)                           # dim calm -> brighter roused
    gl = pygame.Surface((int(gr * 4) + 2, int(gr * 4) + 2), pygame.SRCALPHA)
    g0 = int(gr * 2)
    for i in range(int(gr * 2), 0, -1):
        f = 1 - i / (gr * 2)
        a = int(peak * (f ** 1.5))
        col = _GOLD_HI if i < gr * 0.5 else _GOLD
        if a > 0:
            pygame.draw.circle(gl, (col[0], col[1], col[2], a), (g0, g0), i)
    surf.blit(gl, (int(gcx - g0), int(gcy - g0)))

    # --- 2) the porcelain PLATE: only the front-facing arc of the face -------
    # For each height, sweep the plate arc and keep the part whose surface
    # faces the camera (rz>0); the porcelain spans those projected x's, so it
    # narrows to a crescent on the turn. Track the front ridge for shading.
    plate_l, plate_r, ridge = [], [], []
    for h in heights:
        hw, hd = _hwd(h)
        xs = []
        best_rz, best_x = -1e9, None
        steps = 22
        for k in range(steps + 1):
            th = -_PLATE + (2 * _PLATE) * k / steps
            rx, _hh, rz = _surface(th, h, yaw)
            if rz > 0.3:
                sx = cx + rx * scale
                xs.append(sx)
                if rz > best_rz:
                    best_rz, best_x = rz, sx
        if xs:
            _, yy = P(0, h)
            plate_l.append((min(xs), yy)); plate_r.append((max(xs), yy))
            ridge.append((best_x, yy))
    if len(plate_l) >= 2:
        plate_poly = plate_r + plate_l[::-1]
        pygame.draw.polygon(surf, _PORC, plate_poly)
        pygame.draw.polygon(surf, _PORC_LO, plate_poly, 1)
        # curvature shade: darken the receding lateral half (toward whichever
        # plate edge is FARther from the front ridge), a soft band.
        if len(ridge) == len(plate_l):
            # which side recedes: the edge whose x is farther from the ridge x
            far_left = (abs(plate_l[len(plate_l)//2][0] - ridge[len(ridge)//2][0])
                        > abs(plate_r[len(plate_r)//2][0] - ridge[len(ridge)//2][0]))
            edge = plate_l if far_left else plate_r
            sh = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            shp = [(e[0], e[1]) for e in edge] + ridge[::-1]
            if len(shp) >= 3:
                pygame.draw.polygon(sh, (0, 0, 0, 64), shp)
            surf.blit(sh, (0, 0))
        # specular ridge highlight down the front of the plate
        if len(ridge) >= 2:
            pygame.draw.lines(surf, _PORC_HI, False, ridge, 1)

    eye_th = 0.62
    eye_h = 2.0

    # --- 2b) porcelain surface DETAIL, all pinned in object space so it wraps
    # on the turn AND carries onto the shards when it shatters: a brow ridge, a
    # nose ridge, and the craquelure (whose deep cracks already seep gold). ---
    if len(plate_l) >= 2:
        def proj(th, hh):
            rx, _h, rz = _surface(th, hh, yaw)
            return ((P(rx, hh)) if rz > 0.3 else None)
        # nose ridge: a soft highlight down the centre + a shadow just off it
        _draw_runs(surf, [proj(0.0, hh) for hh in (eye_h + 1.5, eye_h - 1, eye_h - 4, eye_h - 6.5)],
                   _PORC_HI, 1)
        _draw_runs(surf, [proj(0.10, hh) for hh in (eye_h - 1, eye_h - 4, eye_h - 6.5)],
                   _PORC_DK, 1)
        # brow ridges arching over each socket
        for sgn in (-1, 1):
            _draw_runs(surf, [proj(sgn * th, eye_h + 2.6) for th in (0.95, 0.6, 0.28)],
                       _PORC_DK, 1)
        # craquelure: hairline cracks; the deep ones (first 3) carry a gold
        # thread that brightens with threat (calm = the faintest warm hint).
        gold_layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        ga = int(26 + 170 * threat)
        for ci, pl in enumerate(_crack_net()):
            scr = [proj(th, hh) for (th, hh) in pl]
            _draw_runs(surf, scr, _PORC_DK, 1)
            if ci < 3 and ga > 0:
                _draw_runs(gold_layer, scr, (_GOLD[0], _GOLD[1], _GOLD[2], ga), 1)
        surf.blit(gold_layer, (0, 0))

    # --- 3) surface features: the two void eyes + tear streaks, pinned in
    # object space so they wrap and self-occlude with the plate. -------------
    for sgn in (-1, 1):
        rx, h, rz = _surface(sgn * eye_th, eye_h, yaw)
        if rz <= 0.5:
            continue                              # around the side/back -> hidden
        vis = min(1.0, rz / _hwd(eye_h)[1])        # 1 face-on, ->0 at the edge
        ex, ey = P(rx, h)
        ew = max(1, int((2.4 + 3.0 * vis) * scale))   # big vacuous void; foreshortens
        eh = int((5.4 + 0.8 * threat) * scale)
        # recessed socket: a darker porcelain rim dipping into the void
        pygame.draw.ellipse(surf, _PORC_DK,
                            (int(ex - ew / 2 - 2), int(ey - eh / 2 - 2), ew + 4, eh + 4))
        pygame.draw.ellipse(surf, _PORC_LO,
                            (int(ex - ew / 2 - 2), int(ey - eh / 2 - 2), ew + 4, eh + 4), 1)
        pygame.draw.ellipse(surf, _HOLLOW, (int(ex - ew / 2), int(ey - eh / 2), ew, eh))
        # the recessed Yellow glimpsed deep in the void -- a small glow with the
        # black void all around it (brightens as he rouses).
        gd = _GOLD if threat > 0.3 else _GOLD_DK
        pygame.draw.circle(surf, gd, (int(ex), int(ey + eh * 0.12)),
                           max(1, int((0.5 + 0.8 * threat) * scale)))
        # weep: a tear-streak running down the cheek, pinned to the surface --
        # a touch thicker and a tad shorter than before.
        pts = []
        for k in range(4):
            ty = eye_h - 2 - k * 2.6
            trx, th2, trz = _surface(sgn * eye_th * (1.0 - 0.05 * k), ty, yaw)
            if trz <= 0.3:
                break
            pts.append(P(trx, th2))
        if len(pts) >= 2:
            pygame.draw.lines(surf, _HOLLOW, False, pts, 2)
        if threat > 0.3 and vis > 0.4:            # a wet gold glint when roused
            pygame.draw.circle(surf, _GOLD_HI, (int(ex), int(ey + eh * 0.3)),
                               max(1, int(0.5 * scale)))

