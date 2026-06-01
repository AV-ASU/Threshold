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
    """The crack network, authored in object (theta, h) space and cached.

    CALM STATE = a SINGLE crack from the mask's right eye out toward the right
    corner, where it forks into two. As threat rises the rest reveals -- the
    seam, meridians and craquelure the mask finally SHATTERS along, so the
    cracks become exactly the shard lines.

    Returns a list of (polyline, appear): polyline is [(theta, h), ...]; appear
    is the threat at which it reveals (appear < 0 => the calm crack, always on)."""
    global _CRACKS
    if _CRACKS is not None:
        return _CRACKS
    rng = random.Random(7)
    out = []
    # the calm forking crack: right eye -> right corner, then a two-way split
    out.append(([(0.66, 1.0), (0.86, -3.0), (1.06, -8.0)], -1.0))   # stem
    out.append(([(1.06, -8.0), (1.30, -11.0)], -1.0))               # fork A
    out.append(([(1.06, -8.0), (0.94, -12.5)], -1.0))               # fork B
    # everything below reveals with threat, toward the full shatter network.
    extra = []
    for base in (0.0, -0.62, 0.62):                                 # seam + meridians
        extra.append([(base + rng.uniform(-0.06, 0.06), h) for h in range(13, -15, -2)])
    for _ in range(11):                                             # scattered craquelure
        th0 = rng.uniform(-1.2, 1.2); h0 = rng.uniform(-12, 12)
        n = rng.randint(2, 4); pl = [(th0, h0)]; th, h = th0, h0
        ad = rng.uniform(0, math.tau)
        for _ in range(n):
            ad += rng.uniform(-0.8, 0.8)
            th += math.cos(ad) * rng.uniform(0.12, 0.30)
            h += math.sin(ad) * rng.uniform(2.0, 4.0)
            pl.append((th, h))
        extra.append(pl)
    for i, pl in enumerate(extra):
        out.append((pl, 0.08 + i / max(1, len(extra) - 1) * 0.78))
    _CRACKS = out
    return _CRACKS


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


def draw_king3d(surf, cx, cy, yaw, t, threat=0.0, scale=2.4, light=-0.6,
                birth=1.0):
    """Draw the volumetric King mask centred at (cx, cy), turned `yaw`
    radians off face-on (0 = looking at the camera, pi = turned away), animated
    by `t`. `threat` 0..1 deepens the voids + seeps gold (calm preview = 0).
    `birth` 0..1 assembles the mask from converging shards (1 = whole); high
    `threat` SHATTERS it back apart -- both run through the 3D shard path
    (`_draw_shards`); calm (whole + low threat) takes the flat plate path.

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
        # NOTE: no outline here -- the void interior should have no rim; the
        # only outline belongs to the porcelain plate (drawn below).
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

    # --- BIRTH / SHATTER: the fractured 3D shard path. `birth` converges the
    # shards into the whole (spread 1->0); high `threat` flings them apart
    # again (spread 0->1). Calm (born + low threat) falls through to the flat
    # plate path below. The void interior + behind-mask glow are already laid
    # down above, so the Yellow blazes through the gaps between shards.
    bp = max(0.0, min(1.0, birth))
    grow = bp * bp * (3 - 2 * bp)                    # mask assembles in
    shat = max(0.0, (threat - 0.5) / 0.5)
    shat = shat * shat * (3 - 2 * shat)              # shatter past the midpoint
    birth_spread = 1.0 - grow
    spread = max(birth_spread, shat)
    if spread > 0.02:
        fade = grow if birth_spread >= shat else (1.0 - 0.45 * shat)
        _draw_shards(surf, cx, cy, yaw, bob, scale, spread, threat, fade)
        return

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
        # cracks: CALM shows only the single forking crack (right eye -> right
        # corner, splitting in two). As threat rises the rest of the network
        # reveals + darkens, reaching the full set of shard lines at threat 1.
        # The gold seeps the cracks, the calm crack first.
        crack_layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        gold_layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for pl, appear in _crack_net():
            if appear < 0:                          # the calm forking crack -- always on
                vis, gmul = 0.85, 1.0
            else:
                vis = max(0.0, min(1.0, (threat - appear) / 0.18))
                if vis <= 0.03:
                    continue
                gmul = 0.7
            scr = [proj(th, hh) for (th, hh) in pl]
            _draw_runs(crack_layer, scr,
                       (_PORC_DK[0], _PORC_DK[1], _PORC_DK[2], int(70 + 170 * vis)), 1)
            ga = int((24 + 180 * threat) * vis * gmul)
            if ga > 8:
                _draw_runs(gold_layer, scr, (_GOLD[0], _GOLD[1], _GOLD[2], ga), 1)
        surf.blit(crack_layer, (0, 0))
        surf.blit(gold_layer, (0, 0))

    # --- 3) surface features: the two void eyes + tear streaks. Each eye is a
    # PATCH ON THE SURFACE -- its rim is sampled in object (theta, h) space and
    # projected, so the void genuinely CURVES with the mask: it tilts on the
    # cheek, bows with the face, foreshortens on the turn and slits/hides as it
    # goes edge-on, instead of being a flat ellipse stuck on a card. ----------
    def _eye_rim(a0, h0, dth, dh, segs=16):
        """Project a ring around the eye centre, sampled on the surface."""
        ring = []
        for k in range(segs):
            ang = math.tau * k / segs
            th = a0 + math.cos(ang) * dth
            hh = h0 + math.sin(ang) * dh
            rx, _h, _rz = _surface(th, hh, yaw)
            ring.append(P(rx, hh))
        return ring
    for sgn in (-1, 1):
        a = sgn * eye_th
        c = math.cos(a + yaw)                      # this eye's surface facing
        if c <= 0.16:
            continue                               # turned edge-on / around the back
        fn = min(1.0, c / math.cos(eye_th))        # 1 face-on -> 0 as it turns edge-on
        dth = 0.30                                 # eye half-extent in azimuth
        dh = 3.0 + 1.8 * threat                    # taller (deeper) as he rouses
        # recessed socket: a slightly larger porcelain ring dipping into the void
        socket = _eye_rim(a, eye_h, dth + 0.10, dh + 1.4)
        if len(socket) >= 3:
            pygame.draw.polygon(surf, _PORC_DK, socket)
            pygame.draw.polygon(surf, _PORC_LO, socket, 1)
        void = _eye_rim(a, eye_h, dth, dh)
        if len(void) >= 3:
            pygame.draw.polygon(surf, _HOLLOW, void)
        # the recessed Yellow glimpsed deep in the void: it rides to the
        # receding (deep) edge as the eye turns, so it reads as set INTO the
        # socket, not aimed out at the camera. Sampled ON the surface.
        deep_th = a - sgn * (1.0 - fn) * 0.34      # toward the receding edge
        drx, dhh, _rz = _surface(deep_th, eye_h - 0.4, yaw)
        gdx, gdy = P(drx, dhh)
        gd = _GOLD if threat > 0.3 else _GOLD_DK
        pygame.draw.circle(surf, gd, (int(gdx), int(gdy)),
                           max(1, int((0.5 + 0.8 * threat) * scale)))
        if threat > 0.3 and fn > 0.4:             # a wet gold glint when roused
            pygame.draw.circle(surf, _GOLD_HI, (int(gdx), int(gdy + scale)),
                               max(1, int(0.5 * scale)))
        # weep: a tear-streak running down the cheek, pinned to the surface --
        # a touch thicker and a tad shorter than before.
        pts = []
        for k in range(4):
            ty = eye_h - 3 - k * 2.6
            trx, th2, trz = _surface(a * (1.0 - 0.05 * k), ty, yaw)
            if trz <= 0.3:
                break
            pts.append(P(trx, th2))
        if len(pts) >= 2:
            pygame.draw.lines(surf, _HOLLOW, False, pts, 2)



# ===========================================================================
# STEP 1 -- 3D SHARDS.  The crack network becomes a fracture: the mask plate
# tessellates into convex cells (porcelain shards), each a slice of the
# detailed surface.  Each shard gets a 3D centroid, an explode/converge push
# and a spin axis; we project, depth-sort (painter) and flip a shard to its
# dark concave INNER face when it turns its back.  BIRTH = the run in reverse
# (shards converge into the whole mask); SHATTER = explode outward, fading,
# the Yellow blazing through the gaps.  The calm detail (eye-voids, tears, the
# forking crack along the seams) rides onto the shards.
# ===========================================================================
_K3_RNG = random.Random(20247)      # own RNG -> never touches the game stream
_K3_SHARDS = None                   # cached fracture geometry (object space)
_TH_SCALE = 8.0                     # theta<->h metric scale for the Voronoi
EXPLODE = 26.0                      # object-space distance a shard flies at full spread


def _norm3(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def _rodrigues(v, axis, ang):
    """Rotate vector v about a unit axis by ang (Rodrigues' formula)."""
    c = math.cos(ang); s = math.sin(ang)
    ax, ay, az = axis
    dot = ax * v[0] + ay * v[1] + az * v[2]
    cx = ay * v[2] - az * v[1]
    cy = az * v[0] - ax * v[2]
    cz = ax * v[1] - ay * v[0]
    return (v[0] * c + cx * s + ax * dot * (1 - c),
            v[1] * c + cy * s + ay * dot * (1 - c),
            v[2] * c + cz * s + az * dot * (1 - c))


def _clip_halfplane(poly, sx, sy, ox, oy):
    """Sutherland-Hodgman clip of `poly` (list of (u,v)) to the half-plane of
    points at least as close to seed (sx,sy) as to seed (ox,oy) -- i.e. the
    side of the perpendicular bisector containing (sx,sy)."""
    mx, my = (sx + ox) / 2.0, (sy + oy) / 2.0
    nx, ny = sx - ox, sy - oy                       # normal toward (sx,sy)

    def inside(p):
        return (p[0] - mx) * nx + (p[1] - my) * ny >= 0

    def isect(a, b):
        da = (a[0] - mx) * nx + (a[1] - my) * ny
        db = (b[0] - mx) * nx + (b[1] - my) * ny
        f = da / (da - db)
        return (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))

    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = inside(a), inside(b)
        if ina:
            out.append(a)
            if not inb:
                out.append(isect(a, b))
        elif inb:
            out.append(isect(a, b))
    return out


def _point_in_poly(px, py, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and \
           (px < (xj - xi) * (py - yi) / ((yj - yi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def _build_shards():
    """Fracture the mask plate into convex Voronoi cells in (theta, h) space.
    Seeds are biased so the two eyes sit INSIDE shards (not split across a
    seam) and the calm forking crack falls on a seam.  Each shard caches its
    object-space verts, centroid, a per-shard spin axis + rate, and which
    surface features (eye sign / tear) it carries.  Returns the cached list."""
    global _K3_SHARDS
    if _K3_SHARDS is not None:
        return _K3_SHARDS
    rng = random.Random(7)                          # mirror _crack_net's seed
    hmin, hmax = -15.0, 15.0
    tmax = _PLATE + 0.18                             # a touch beyond the plate arc
    # bounds rectangle in metric (u = theta * scale, v = h)
    bounds = [(-tmax * _TH_SCALE, hmin), (tmax * _TH_SCALE, hmin),
              (tmax * _TH_SCALE, hmax), (-tmax * _TH_SCALE, hmax)]
    eye_th, eye_h = 0.62, 2.0
    seeds = [
        (eye_th * _TH_SCALE, eye_h),                # right eye core
        (-eye_th * _TH_SCALE, eye_h),               # left eye core
        (0.0, 9.0), (0.0, -10.0),                   # brow / chin centre
        (0.95 * _TH_SCALE, -8.0),                   # right corner (crack fork)
    ]
    for _ in range(13):                             # scattered craquelure seeds
        seeds.append((rng.uniform(-tmax, tmax) * _TH_SCALE,
                      rng.uniform(hmin + 1, hmax - 1)))
    shards = []
    for i, (sx, sy) in enumerate(seeds):
        cell = bounds
        for j, (ox, oy) in enumerate(seeds):
            if i == j:
                continue
            cell = _clip_halfplane(cell, sx, sy, ox, oy)
            if len(cell) < 3:
                break
        if len(cell) < 3:
            continue
        verts = [(u / _TH_SCALE, v) for (u, v) in cell]       # back to (theta, h)
        tc = sum(p[0] for p in verts) / len(verts)
        hc = sum(p[1] for p in verts) / len(verts)
        axis = _norm3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        spin = rng.uniform(2.2, 4.6) * (1 if rng.random() < 0.5 else -1)
        feat = {"eye": None, "tear": False}
        for sgn in (-1, 1):
            if _point_in_poly(sgn * eye_th, eye_h, verts):
                feat["eye"] = sgn
        # the shard owns the tear if its centroid sits below an eye on that side
        if feat["eye"] is None and -10 < hc < eye_h - 1 and abs(tc) > 0.35:
            feat["tear"] = (1 if tc > 0 else -1)
        shards.append({"verts": verts, "tc": tc, "hc": hc,
                       "axis": axis, "spin": spin, "feat": feat})
    _K3_SHARDS = shards
    return _K3_SHARDS


def _shard_xform(th, hh, yaw, C, axis, ang, E, amt):
    """Object-space surface point at (th,hh) carried by a shard's rigid motion:
    rotate about the shard centroid C by `ang`, then translate along E*amt.
    Returns the transformed 3D point (x, y_up, z_depth)."""
    rx, _h, rz = _surface(th, hh, yaw)
    lx, ly, lz = rx - C[0], hh - C[1], rz - C[2]
    lx, ly, lz = _rodrigues((lx, ly, lz), axis, ang)
    return (C[0] + lx + E[0] * amt, C[1] + ly + E[1] * amt, C[2] + lz + E[2] * amt)


def _draw_shards(surf, cx, cy, yaw, bob, scale, spread, threat, fade):
    """Render the fractured mask at `spread` 0..1 (0 = whole, 1 = flung apart),
    depth-sorted, each shard porcelain (front) or dark concave (back)."""
    shards = _build_shards()
    eye_th, eye_h = 0.62, 2.0
    ang = spread * 1.0
    drawn = []
    for sh in shards:
        # the shard's own 3D centroid at this yaw, and its outward push vector
        crx, _h, crz = _surface(sh["tc"], sh["hc"], yaw)
        C = (crx, sh["hc"], crz)
        E = _norm3((crx, sh["hc"] * 0.35, crz + 2.0))   # outward + a pop toward cam
        amt = spread * EXPLODE
        pts3 = [_shard_xform(th, hh, yaw, C, sh["axis"], ang, E, amt)
                for (th, hh) in sh["verts"]]
        scr = [(cx + p[0] * scale, cy - (p[1] + bob) * scale) for p in pts3]
        if len(scr) < 3:
            continue
        zc = sum(p[2] for p in pts3) / len(pts3)
        # facing: signed screen area sign tells us which face we see
        area = 0.0
        for k in range(len(scr)):
            x0, y0 = scr[k]; x1, y1 = scr[(k + 1) % len(scr)]
            area += x0 * y1 - x1 * y0
        drawn.append((zc, sh, pts3, scr, area, C, E, amt))
    drawn.sort(key=lambda d: d[0])                  # painter: far (low z) first
    for zc, sh, pts3, scr, area, C, E, amt in drawn:
        front = area < 0                            # screen-space winding (y down)
        if front:
            # porcelain, shaded by depth (receded shards darker)
            f = 0.74 + 0.26 * max(0.0, min(1.0, (zc + 6) / 12.0))
            col = _shade(_PORC, f)
            pygame.draw.polygon(surf, col, scr)
            pygame.draw.polygon(surf, _PORC_DK, scr, 1)   # the crack seam
        else:
            # the dark concave INNER face of the mask; a faint gold rim where
            # the Yellow behind catches the broken edge as he rouses.
            pygame.draw.polygon(surf, _VOIDC, scr)
            rimc = _shade(_GOLD_DK, 0.5 + 0.5 * threat)
            pygame.draw.polygon(surf, rimc, scr, 1)
        # --- carry the calm surface detail onto the front-facing shards ------
        if front and fade > 0.4:
            ja = sh["feat"]
            if ja["eye"] is not None:
                sgn = ja["eye"]
                rim = []
                for k in range(14):
                    a = math.tau * k / 14
                    th = sgn * eye_th + math.cos(a) * 0.30
                    hh = eye_h + math.sin(a) * (3.0 + 1.8 * threat)
                    p = _shard_xform(th, hh, yaw, C, sh["axis"], ang, E, amt)
                    rim.append((cx + p[0] * scale, cy - (p[1] + bob) * scale))
                if len(rim) >= 3:
                    pygame.draw.polygon(surf, _HOLLOW, rim)
            if ja["tear"]:
                sgn = ja["tear"]
                pts = []
                for k in range(4):
                    ty = eye_h - 3 - k * 2.4
                    p = _shard_xform(sgn * eye_th * (1 - 0.05 * k), ty, yaw,
                                     C, sh["axis"], ang, E, amt)
                    pts.append((cx + p[0] * scale, cy - (p[1] + bob) * scale))
                if len(pts) >= 2:
                    pygame.draw.lines(surf, _HOLLOW, False, pts, 2)
