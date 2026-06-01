"""THE KING IN YELLOW as a true volumetric object -- PROTOTYPE (CAMERA.md tier 3).

Translates the flat pallid-mask King (`sprites._draw_king`) into a 3D form that
renders from every angle: a porcelain MASK-PLATE pinned in object space in front
of a glowing YELLOW body. The plate's front (object angle 0) points at the
player; the camera's yaw then decides what we see -- face-on, three-quarter, a
thin profile crescent, or the Yellow back when he turns away. Surface features
(the two void eyes, the tear-streaks) are pinned at object `(theta, h)` so they
slide around and self-occlude on the turn, exactly like the pseudo3d Watcher.

Previewable in isolation (`tools/preview_king3d.py` -- turntable, threat ramp,
birth->shatter MP4s), AND now LIVE: `sprites._draw_king` routes here on the
tilt path (`Game._tilt_on()`), passing `king3d_yaw` (the mask faces the player,
camera.yaw gives the view) + birth/threat exactly as the flat King. At pitch 0
the flat shipping King is untouched / pixel-identical -- see CAMERA.md tier 3.

The full build, all driven by one `threat` 0..1 + `birth` 0..1:
  (1) 3D SHARDS -- `_crack_net` -> a convex-cell fracture (`_build_shards`):
      each shard a slice of the detailed surface with a 3D centroid, explode/
      converge push + spin axis; depth-sorted, flipping to its dark concave
      inner face on the turn (`_draw_shards`). BIRTH converges them into the
      whole; SHATTER flings them apart, the Yellow blazing through the gaps.
  (2) THREAT CONTINUITY -- calm (whole plate) -> seep/crack (the lit network,
      glow growing behind) -> SHATTER; the gold seam-glow carries the lit
      cracks onto the breaking shards so the network IS the fracture.
  (3) REACHING ARMS -- `_draw_arms`: tendrils anchored at object-space seams,
      reaching toward the player (the mask's local front); near ones read long,
      trailing ones foreshorten + occlude behind the shards.
  (4) WORLD-SPACE PARTICLES -- `_particles`: the wake promoted to a 3D frame
      (coalesce on birth, drift when calm, vomit gold sparks on shatter); a
      `proj` hook lets a caller push them through a real camera.
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
                birth=1.0, proj=None):
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

    # particle projection: default is the prototype's orthographic front view
    # (depth grows the mote); the live game passes a `proj` that maps each mote
    # local->world and pushes it through camera.project (true scale under tilt).
    if proj is None:
        def proj(lx, ly, lz):
            # size_mul is foreshorten only (motes are sized in screen px); the
            # live camera proj returns its own depth-scaled size_mul.
            return (cx + lx * scale, cy - (ly + bob) * scale, 1.0 + lz * 0.018)

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
        # arms only burst from the SHATTER (not the calm birth-assembly): the
        # ones reaching away from the camera trail behind the shards (occluded),
        # the ones lunging at it are drawn over the top.
        _draw_arms(surf, cx, cy, yaw, bob, scale, shat, threat, "back", t=t)
        # shards build on their own layer so the eye / tear HOLES punch clean
        # through to the void + glow already on `surf` (they turn black when the
        # shards lock together, and break apart with them).
        porc = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        _draw_shards(porc, cx, cy, yaw, bob, scale, spread, threat, fade)
        surf.blit(porc, (0, 0))
        _draw_arms(surf, cx, cy, yaw, bob, scale, shat, threat, "front", t=t)
        _particles(surf, t, threat, birth_spread, shat, proj)
        return

    # --- CALM PLATE.  The porcelain is built on its OWN layer so the eyes and
    # tears can be PUNCHED clean THROUGH it (true holes, no painted void, no
    # socket outline). The dark void + the behind-mask glow already sit on
    # `surf`, so each hole reads black when calm and lets the Yellow show
    # through as he rouses -- the mask is genuinely perforated. ---------------
    porc = pygame.Surface(surf.get_size(), pygame.SRCALPHA)

    # --- 2) the plate: only the front-facing arc of the face. For each height,
    # sweep the arc and keep the part whose surface faces the camera (rz>0); the
    # porcelain spans those projected x's, so it narrows to a crescent on the
    # turn. Track the front ridge for shading.
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
        pygame.draw.polygon(porc, _PORC, plate_poly)
        # curvature shade: darken the receding lateral half (toward whichever
        # plate edge is FARther from the front ridge), a soft band.
        if len(ridge) == len(plate_l):
            far_left = (abs(plate_l[len(plate_l)//2][0] - ridge[len(ridge)//2][0])
                        > abs(plate_r[len(plate_r)//2][0] - ridge[len(ridge)//2][0]))
            edge = plate_l if far_left else plate_r
            shp = [(e[0], e[1]) for e in edge] + ridge[::-1]
            if len(shp) >= 3:
                sh = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                pygame.draw.polygon(sh, (0, 0, 0, 64), shp)
                porc.blit(sh, (0, 0))
        # specular ridge highlight down the front of the plate
        if len(ridge) >= 2:
            pygame.draw.lines(porc, _PORC_HI, False, ridge, 1)

    eye_th = 0.62
    eye_h = 2.0

    # --- 2b) porcelain surface DETAIL, all pinned in object space so it wraps
    # on the turn: a nose ridge + the craquelure (whose deep cracks seep gold).
    if len(plate_l) >= 2:
        def projd(th, hh):
            rx, _h, rz = _surface(th, hh, yaw)
            return ((P(rx, hh)) if rz > 0.3 else None)
        # nose ridge: a soft highlight down the centre + a shadow just off it
        _draw_runs(porc, [projd(0.0, hh) for hh in (eye_h + 1.5, eye_h - 1, eye_h - 4, eye_h - 6.5)],
                   _PORC_HI, 1)
        _draw_runs(porc, [projd(0.10, hh) for hh in (eye_h - 1, eye_h - 4, eye_h - 6.5)],
                   _PORC_DK, 1)
        # cracks: CALM shows only the single forking crack; as threat rises the
        # rest reveals + the gold seeps the seams, the calm crack first.
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
            scr = [projd(th, hh) for (th, hh) in pl]
            _draw_runs(crack_layer, scr,
                       (_PORC_DK[0], _PORC_DK[1], _PORC_DK[2], int(70 + 170 * vis)), 1)
            ga = int((24 + 180 * threat) * vis * gmul)
            if ga > 8:
                _draw_runs(gold_layer, scr, (_GOLD[0], _GOLD[1], _GOLD[2], ga), 1)
        porc.blit(crack_layer, (0, 0))
        porc.blit(gold_layer, (0, 0))

    # --- 3) the eyes + tears are HOLES punched clean through the porcelain.
    # The rim is sampled in object (theta, h) space and projected, so the hole
    # genuinely CURVES with the mask -- it tilts on the cheek, bows with the
    # face and foreshortens / slits shut as it turns edge-on. No outline, no
    # painted void: the hole reveals the dark void (black) + the growing glow
    # behind it on `surf`.
    def _eye_rim(a0, h0, dth, dh, segs=16):
        ring = []
        for k in range(segs):
            ang = math.tau * k / segs
            th = a0 + math.cos(ang) * dth
            hh = h0 + math.sin(ang) * dh
            rx, _h, _rz = _surface(th, hh, yaw)
            ring.append(P(rx, hh))
        return ring
    if len(plate_l) >= 2:
        for sgn in (-1, 1):
            a = sgn * eye_th
            c = math.cos(a + yaw)                  # this eye's surface facing
            if c <= 0.16:
                continue                           # turned edge-on / around the back
            dth = 0.30                             # eye half-extent in azimuth
            dh = 3.0 + 1.8 * threat                # taller (deeper) as he rouses
            void = _eye_rim(a, eye_h, dth, dh)
            if len(void) >= 3:
                pygame.draw.polygon(porc, (0, 0, 0, 0), void)   # PUNCH the eye
            # weep: a tear-channel punched down the cheek, pinned to the surface
            pts = []
            for k in range(4):
                ty = eye_h - 3 - k * 2.6
                trx, th2, trz = _surface(a * (1.0 - 0.05 * k), ty, yaw)
                if trz <= 0.3:
                    break
                pts.append(P(trx, th2))
            if len(pts) >= 2:
                pygame.draw.lines(porc, (0, 0, 0, 0), False, pts, 2)

    surf.blit(porc, (0, 0))
    # the calm wake: only the faint ambient ash drifts off the whole mask.
    _particles(surf, t, threat, 0.0, 0.0, proj)


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
    holes = []                                      # punched LAST so no nearer
    tears = []                                      # shard refills a lined-up eye
    for zc, sh, pts3, scr, area, C, E, amt in drawn:
        front = area < 0                            # screen-space winding (y down)
        if front:
            # porcelain, shaded by depth (receded shards darker)
            f = 0.74 + 0.26 * max(0.0, min(1.0, (zc + 6) / 12.0))
            col = _shade(_PORC, f)
            pygame.draw.polygon(surf, col, scr)
            # the lit crack network BECOMES the fracture: the seam glows gold as
            # the shards first part (the seep escaping the break) and goes dark
            # once they fly wide. Drawn under the dark seam so the edge reads.
            seam_gold = max(0.0, 1.0 - spread / 0.32)
            if seam_gold > 0.04 and threat > 0.45:
                pygame.draw.polygon(surf, _shade(_GOLD, 0.55 + 0.45 * threat),
                                    scr, 2)
            pygame.draw.polygon(surf, _PORC_DK, scr, 1)   # the crack seam
        else:
            # the dark concave INNER face of the mask; a faint gold rim where
            # the Yellow behind catches the broken edge as he rouses.
            pygame.draw.polygon(surf, _VOIDC, scr)
            rimc = _shade(_GOLD_DK, 0.5 + 0.5 * threat)
            pygame.draw.polygon(surf, rimc, scr, 1)
        # the eyes / tears are HOLES owned by a shard; collect them to punch
        # after every shard is laid down (so a nearer shard can't refill a
        # lined-up eye). They ride with their shard: the holes line up into the
        # eyes as the pieces lock on birth, and break apart again on shatter.
        if front:
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
                    holes.append(rim)
            if ja["tear"]:
                sgn = ja["tear"]
                pts = []
                for k in range(4):
                    ty = eye_h - 3 - k * 2.4
                    p = _shard_xform(sgn * eye_th * (1 - 0.05 * k), ty, yaw,
                                     C, sh["axis"], ang, E, amt)
                    pts.append((cx + p[0] * scale, cy - (p[1] + bob) * scale))
                if len(pts) >= 2:
                    tears.append(pts)
    # PUNCH the eyes + tears clean through the assembled porcelain (last).
    for rim in holes:
        pygame.draw.polygon(surf, (0, 0, 0, 0), rim)
    for pts in tears:
        pygame.draw.lines(surf, (0, 0, 0, 0), False, pts, 2)


# ===========================================================================
# STEP 3 -- 3D REACHING ARMS.  Dark tendrils anchored at object-space seam
# points, reaching toward the PLAYER.  The mask always faces the player, so in
# the mask's local frame the player lies in the +front (+Z) direction (plus a
# downward bias -- he stands on the ground): when we see the face the arms
# lunge AT the camera (read long + near), and when the mask is turned away the
# same reach foreshortens and is occluded behind the shards.
# ===========================================================================
_ARM_DK = (16, 13, 20)              # the grabbing tendrils: near-black
_ARM_HI = (44, 38, 54)
_ARM_ANCHORS = [(-1.30, 1.0), (-0.66, -8.0), (0.0, 9.5),
                (0.70, -8.0), (1.30, 1.5)]     # seam points around the plate


def _yaw_vec(v, yaw):
    """Rotate a local vector (x, y_up, z_depth) about the vertical axis by yaw,
    matching _surface's ox/oz rotation (y is untouched)."""
    rx = v[0] * math.cos(yaw) + v[2] * math.sin(yaw)
    rz = -v[0] * math.sin(yaw) + v[2] * math.cos(yaw)
    return (rx, v[1], rz)


def _draw_arms(surf, cx, cy, yaw, bob, scale, shat, threat, which,
               reach_local=(0.0, -0.45, 1.0), t=0.0):
    """Stroke the reaching arms whose side (toward/away from camera) matches
    `which` ('front' = drawn after the shards, 'back' = before + dimmer)."""
    if shat <= 0.04:
        return
    D = _yaw_vec(_norm3(reach_local), yaw)          # reach direction, camera space
    toward = D[2] > 0.0                             # tendrils point at the camera?
    side = "front" if toward else "back"
    if side != which:
        return
    dim = 1.0 if toward else 0.46                   # trailing arms read dim/short
    L = (9.0 + 30.0 * shat) * (0.8 + 0.4 * threat)  # object-space reach length
    segs = 7
    # a perpendicular for the waver (in the projection plane)
    plen = math.hypot(D[0], D[1]) or 1.0
    perp = (-D[1] / plen, D[0] / plen, 0.0)
    for ai, (ath, ah) in enumerate(_ARM_ANCHORS):
        ax, _h, az = _surface(ath, ah, yaw)
        A = (ax, ah, az)
        # near (reaching at the camera) read long; trailing arms foreshorten.
        ll = L * (1.0 - 0.18 * abs(ai - 2)) * (1.0 + 0.5 * D[2])
        phase = ai * 1.7 + t * 1.6
        pts, depths = [], []
        for k in range(segs + 1):
            fr = k / segs
            w = math.sin(phase + fr * 3.0) * (1.6 + 2.4 * fr) * (0.4 + shat)
            p = (A[0] + D[0] * ll * fr + perp[0] * w,
                 A[1] + D[1] * ll * fr + perp[1] * w - fr * fr * 2.0,
                 A[2] + D[2] * ll * fr)
            pts.append((cx + p[0] * scale, cy - (p[1] + bob) * scale))
            depths.append(p[2])
        # width tapers toward the tip; a tendril coming AT the camera is fat,
        # one trailing away is thin (foreshortened).
        base_w = max(2, int((3.2 + 2.2 * shat) * (0.6 + 0.6 * dim) * scale * 0.45))
        for k in range(segs):
            w = max(1, int(base_w * (1.0 - 0.82 * k / segs)))
            col = _shade(_ARM_HI if k == 0 else _ARM_DK, 0.5 + 0.5 * dim)
            pygame.draw.line(surf, col, pts[k], pts[k + 1], w)
        # a gold ember at the grasping tip once truly roused
        if toward and threat > 0.6:
            tx, ty = pts[-1]
            pygame.draw.circle(surf, _GOLD_DK, (int(tx), int(ty)),
                               max(1, int(0.9 * scale)))


# ===========================================================================
# STEP 4 -- WORLD-SPACE PARTICLES.  The wake (pale-ash + gold sparks) lives in
# a 3D frame (lx, ly_up, lz_depth) around the mask, not as flat screen sprites,
# so it foreshortens + scales with depth.  BIRTH pulls motes INWARD (the mask
# coalescing); SHATTER vomits sparks OUTWARD; a faint ash always drifts.  A
# `proj` hook lets the live game map each mote local->world and push it through
# camera.project (true world scale under tilt); the default is the prototype's
# orthographic-front projection, matching the mask volume.
# ===========================================================================
_K3_PARTS = []                      # [{x,y,z, vx,vy,vz, age, life, r, kind}]
_K3_PT_LAST = [0.0]


def reset_king3d_fx():
    """Clear the volumetric King's particle wake (call on scene/run change so
    the trail never leaps across a teleport)."""
    _K3_PARTS.clear()
    _K3_PT_LAST[0] = 0.0


def _particles(surf, t, threat, birth_spread, shat, proj):
    """Emit + integrate + draw the 3D wake.  `proj(lx, ly_up, lz_depth)` ->
    (screen_x, screen_y, size_mul)."""
    dt = t - _K3_PT_LAST[0]
    _K3_PT_LAST[0] = t
    if dt <= 0 or dt > 0.2:
        dt = 0.016
    rng = _K3_RNG
    # BIRTH coalescence: motes stream IN from out of the void toward the mask.
    if birth_spread > 0.35 and len(_K3_PARTS) < 200:
        for _ in range(3):
            a = rng.uniform(0, math.tau); el = rng.uniform(-1.0, 1.0)
            d = rng.uniform(20, 42); spd = rng.uniform(34, 70)
            x = math.cos(a) * d; y = el * d * 0.7; z = math.sin(a) * d * 0.5
            _K3_PARTS.append({"kind": "ash", "x": x, "y": y, "z": z,
                              "vx": -x / d * spd, "vy": -y / max(1, d) * spd,
                              "vz": -z / max(1, d) * spd, "age": 0.0,
                              "life": d / spd, "r": rng.uniform(1.5, 3.2)})
    # SHATTER: the break vomits sparks + ash outward (gold once truly roused).
    if shat > 0.08 and rng.random() < shat:
        for _ in range(2):
            a = rng.uniform(0, math.tau); el = rng.uniform(-0.8, 0.8)
            spd = rng.uniform(22, 60) * shat
            gold = rng.random() < 0.5 + 0.3 * threat
            _K3_PARTS.append({"kind": "spark" if gold else "ash",
                              "x": rng.uniform(-3, 3), "y": rng.uniform(-3, 3),
                              "z": rng.uniform(-3, 3),
                              "vx": math.cos(a) * spd, "vy": el * spd + 6,
                              "vz": math.sin(a) * spd, "age": 0.0,
                              "life": rng.uniform(0.6, 1.4), "r": rng.uniform(2, 5)})
    # ambient ash always drifting down off the floating form (a faint few)
    if rng.random() < 0.16:
        a = rng.uniform(0, math.tau); d = rng.uniform(8, 17)
        _K3_PARTS.append({"kind": "ash", "x": math.cos(a) * d,
                          "y": rng.uniform(4, 12), "z": math.sin(a) * d * 0.6,
                          "vx": rng.uniform(-3, 3), "vy": rng.uniform(-10, -4),
                          "vz": rng.uniform(-3, 3), "age": 0.0,
                          "life": rng.uniform(1.0, 2.0), "r": rng.uniform(1.2, 2.4)})
    if len(_K3_PARTS) > 240:
        del _K3_PARTS[:len(_K3_PARTS) - 240]
    keep = []
    for p in _K3_PARTS:
        p["age"] += dt
        fr = p["age"] / p["life"]
        if fr >= 1.0:
            continue
        p["x"] += p["vx"] * dt; p["y"] += p["vy"] * dt; p["z"] += p["vz"] * dt
        keep.append((p, fr))
    _K3_PARTS[:] = [p for p, _ in keep]
    # depth-sort so nearer motes draw last
    keep.sort(key=lambda pf: pf[0]["z"])
    for p, fr in keep:
        sx, sy, sm = proj(p["x"], p["y"], p["z"])
        a = 1 - fr
        if p["kind"] == "spark":
            rr = max(1, int(p["r"] * sm))
            gl = pygame.Surface((rr * 5 + 2, rr * 5 + 2), pygame.SRCALPHA)
            c = (rr * 5 + 2) // 2
            pygame.draw.circle(gl, (_GOLD[0], _GOLD[1], _GOLD[2], int(60 * a)), (c, c), int(rr * 2.2))
            pygame.draw.circle(gl, (_GOLD_HI[0], _GOLD_HI[1], _GOLD_HI[2], int(170 * a)), (c, c), rr)
            surf.blit(gl, (int(sx - c), int(sy - c)))
        else:
            rr = max(1, int(p["r"] * sm * (1 - 0.4 * fr)))
            ps = pygame.Surface((rr * 2 + 2, rr * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (_PORC[0], _PORC[1], _PORC[2], int(120 * a)),
                               (rr + 1, rr + 1), rr)
            surf.blit(ps, (int(sx - rr - 1), int(sy - rr - 1)))
