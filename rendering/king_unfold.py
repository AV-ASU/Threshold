"""THE UNFOLDING -- the non-humanoid King (prototype, not wired into the game).

Design, decided in chat:
  * BASE FORM = a blend -- an irregular, lumpy 4D MASS (the asymmetry is the
    wrongness; it never resolves into a shape you can name) with a smooth
    hypersphere HEART everting inside it.
  * TEXTURE = oily organic membrane -- thick, near-opaque dark flesh, LIT by a
    real 3D normal so it reads as a solid mass (not a wireframe hologram). Light
    dies in the folds. The sick gold survives only as: rim-light trapped on the
    grazing silhouette, the EYES that open wetly across the skin, the Yellow
    SIGN that resolves for a beat, and the gold HEART glowing up through the
    flesh from the everting core.

It is a real 4D object: the mass + heart rotate through 4D planes and project
4D->3D->2D, so the heart visibly turns INSIDE-OUT within the body and the
silhouette is never the same twice.

The gold halo / shatter (rendering/king_halo.py) is still the CATCH bloom.
Preview:  python tools/preview_king_unfold.py
"""
import math
import random

import pygame

from rendering.sprites import door_mask_surface

# --- palette ---------------------------------------------------------------
_MEM = (22, 15, 17)                 # membrane base (warm near-black flesh)
_MEM_HI = (68, 50, 52)              # lit membrane (dark wet flesh)
_MEM_SHADOW = (9, 6, 8)             # deep fold
_SHEEN = (150, 138, 138)            # wet glint (desaturated, NOT metallic)
_SUBSURF = (74, 30, 26)             # faint blood-warmth under the skin
_GOLD = (204, 164, 64)
_GOLD_HI = (244, 216, 124)
_GOLD_RIM = (196, 156, 58)          # light trapped at the silhouette
_HEART = (168, 126, 44)             # the everting core, glowing through flesh
_EDGE_HI = (206, 172, 78)
_EDGE_DK = (84, 68, 30)             # (kept for tools/explore_4d_shapes.py)

_W_EYE = 2.15                       # 4D camera distance (eversion strength)
_Z_EYE = 3.3                        # 3D camera distance
_FOCAL = 2.7

_L = (0.35, 0.55, 0.90)            # light dir (front-upper)
_LMAG = math.sqrt(sum(c * c for c in _L))
_L = tuple(c / _LMAG for c in _L)
_H = tuple((_L[i] + (0, 0, 1)[i]) for i in range(3))      # half-vector
_HMAG = math.sqrt(sum(c * c for c in _H)) or 1.0
_H = tuple(c / _HMAG for c in _H)

_FORM = None
_MASK_CACHE = {}


def reset_king_unfold_fx():
    pass


def _mask(height, vis, gx, gy, seed):
    """A carved dark-wood mask (rendering.sprites.door_mask_surface) surfacing on
    the skin -- canon: the wrong face the threshold wears. Cached on quantized
    keys so we don't re-render per facet per frame."""
    hb = max(10, int(round(height / 8.0)) * 8)
    key = (hb, round(vis, 1), round(gx, 1), round(gy, 1), seed % 5)
    s = _MASK_CACHE.get(key)
    if s is None:
        s = door_mask_surface(height=hb, vis=max(0.25, vis),
                              gaze=(round(gx, 1), round(gy, 1)), seed=seed % 5)
        _MASK_CACHE[key] = s
    return s


# --------------------------------------------------------------------------- #
# small vector helpers
# --------------------------------------------------------------------------- #
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(a):
    m = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) or 1.0
    return (a[0] / m, a[1] / m, a[2] / m)


def _cmix(a, b, f):
    f = 0.0 if f < 0 else 1.0 if f > 1 else f
    return (a[0] + (b[0] - a[0]) * f,
            a[1] + (b[1] - a[1]) * f,
            a[2] + (b[2] - a[2]) * f)


def _cadd(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s)


def _ci(c):
    return (max(0, min(255, int(c[0]))),
            max(0, min(255, int(c[1]))),
            max(0, min(255, int(c[2]))))


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
def _sphere_mesh(nlat, nlon, radial_fn):
    verts, grid = [], []
    for i in range(nlat + 1):
        lat = math.pi * i / nlat
        row = []
        for j in range(nlon):
            lon = math.tau * j / nlon
            d = (math.sin(lat) * math.cos(lon), math.cos(lat),
                 math.sin(lat) * math.sin(lon))
            verts.append(radial_fn(d))
            row.append(len(verts) - 1)
        grid.append(row)
    faces = []
    for i in range(nlat):
        for j in range(nlon):
            faces.append([grid[i][j], grid[i][(j + 1) % nlon],
                          grid[i + 1][(j + 1) % nlon], grid[i + 1][j]])
    return verts, faces


def _build():
    global _FORM
    if _FORM is not None:
        return _FORM

    def noise(d, s):
        return (math.sin(3.1 * d[0] + 1.3 * s) * math.sin(2.3 * d[1] + 2.1) *
                math.cos(2.7 * d[2] + 0.7) +
                0.5 * math.sin(4.2 * d[1] + 1.1) * math.cos(3.3 * d[2] + 2.4 + s))

    def outer_rf(d):
        n = noise(d, 0.0)
        rad = 0.92 * (1.0 + 0.40 * n)
        w = 0.62 * noise(d, 2.0)
        return (d[0] * rad, d[1] * rad, d[2] * rad, w)
    NLAT, NLON = 18, 26                       # subdivided -> smoother wet surface
    overts, ofaces = _sphere_mesh(NLAT, NLON, outer_rf)
    r = random.Random(23)
    mask_faces = {fi: r.uniform(0, 9) for fi in r.sample(range(len(ofaces)), 11)}
    # arm roots: a ring of vertices around the lower-front, where limbs erupt
    arm_roots = []
    for a in range(6):
        i = int(NLAT * 0.60)
        j = int((a / 6.0) * NLON + 0.5) % NLON
        arm_roots.append((i * NLON + j, r.uniform(0, 6)))

    # the heart: two nested smooth shells -> everts inside the body
    cverts, cfaces = [], []
    for (rad, w0) in ((0.50, 0.16), (0.33, 0.40)):
        def rf(d, rad=rad, w0=w0):
            return (d[0] * rad, d[1] * rad, d[2] * rad, w0)
        v, f = _sphere_mesh(5, 8, rf)
        off = len(cverts)
        cverts += v
        cfaces += [[i + off for i in face] for face in f]

    _FORM = dict(overts=overts, ofaces=ofaces, mask_faces=mask_faces,
                 arm_roots=arm_roots, cverts=cverts, cfaces=cfaces)
    return _FORM


def _rot(p, i, j, ang):
    c, s = math.cos(ang), math.sin(ang)
    q = list(p)
    q[i] = p[i] * c - p[j] * s
    q[j] = p[i] * s + p[j] * c
    return q


def _to3d(p4):
    k4 = 1.0 / (_W_EYE - p4[3])
    return (p4[0] * k4, p4[1] * k4, p4[2] * k4)


def _proj(p3, cx, cy, scale):
    k3 = _FOCAL / (_Z_EYE - p3[2])
    return (cx + p3[0] * k3 * scale, cy - p3[1] * k3 * scale)


def _project(p4, cx, cy, scale):     # kept for tools/explore_4d_shapes.py compat
    p3 = _to3d(p4)
    k3 = _FOCAL / (_Z_EYE - p3[2])
    return (cx + p3[0] * k3 * scale, cy - p3[1] * k3 * scale, p3[2], k3)


def _xform(verts, angs, wob_amp, t):
    out3 = []
    a, b, c, d = angs
    for vi, v in enumerate(verts):
        p = list(v)
        if wob_amp:
            wob = wob_amp * math.sin(t * 1.3 + vi)
            p = [p[0] + wob, p[1] - wob, p[2] + wob * 0.6, p[3]]
        p = _rot(p, 0, 3, a); p = _rot(p, 1, 3, b)
        p = _rot(p, 2, 1, c); p = _rot(p, 0, 1, d)
        out3.append(_to3d(p))
    return out3


# --------------------------------------------------------------------------- #
# fx
# --------------------------------------------------------------------------- #
def _eat_light(surf, cx, cy, r, strength):
    r = int(r)
    if r < 2:
        return
    a = pygame.Surface((r * 2, r * 2))
    steps = max(6, r // 2)
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        v = int(strength * ((1 - i / steps) ** 2.3))
        if v > 0:
            pygame.draw.circle(a, (v, v, v), (r, r), rr)
    surf.blit(a, (int(cx - r), int(cy - r)), special_flags=pygame.BLEND_RGB_SUB)


def _heart_glow(lay, x, y, r, inten):
    r = int(r)
    if r < 2 or inten < 4:
        return
    g = pygame.Surface((r * 2, r * 2))
    for i in range(int(r), 0, -1):
        f = 1 - i / r
        v = inten * (f ** 2.2)
        col = (int(_HEART[0] / 255 * v), int(_HEART[1] / 255 * v),
               int(_HEART[2] / 255 * v))
        pygame.draw.circle(g, col, (r, r), i)
    lay.blit(g, (int(x - r), int(y - r)), special_flags=pygame.BLEND_RGB_ADD)


def _yellow_sign(surf, x, y, r, a):
    if r < 3 or a < 8:
        return
    for k in range(3):
        base = -math.pi / 2 + k * 2.0944
        pts = []
        for s in range(7):
            fr = s / 6
            ang = base + fr * 2.4
            rr = r * (0.25 + 0.75 * fr)
            pts.append((x + math.cos(ang) * rr, y + math.sin(ang) * rr * 0.92))
        pygame.draw.lines(surf, (*_GOLD, a), False, pts, max(1, int(r * 0.11)))


def _eye(surf, x, y, r, openf, gaze, a):
    if r < 1.6 or openf <= 0.05 or a < 10:
        return
    hh = max(1.0, r * 0.64 * openf)
    lid = [(x + math.cos(math.tau * k / 14) * r,
            y + math.sin(math.tau * k / 14) * hh) for k in range(14)]
    pygame.draw.polygon(surf, (3, 3, 5, a), lid)            # wet socket
    pygame.draw.polygon(surf, (*_GOLD, a), lid, max(1, int(r * 0.14)))
    ir = max(1, int(hh * 0.82))
    gx = int(x + gaze * r * 0.4)
    pygame.draw.circle(surf, (*_GOLD, a), (gx, int(y)), ir)
    pygame.draw.circle(surf, (3, 3, 5, a), (gx, int(y)), max(1, int(ir * 0.5)))
    if ir >= 3:                                             # glossy catchlight
        pygame.draw.circle(surf, (*_GOLD_HI, a),
                           (gx - ir // 3, int(y) - ir // 3), max(1, ir // 4))


# --------------------------------------------------------------------------- #
def _shade_face(N, dn, threat):
    """Oily membrane shading from a 3D normal: lit dark flesh + wet sheen +
    gold rim trapped on the grazing silhouette."""
    diff = max(0.0, _dot(N, _L))
    spec = max(0.0, _dot(N, _H)) ** 18
    rim = (1.0 - abs(N[2])) ** 3
    col = _cmix(_MEM_SHADOW, _MEM_HI, 0.12 + 0.85 * diff)
    col = _cmix(col, _MEM, 0.25)                            # keep it dark/oily
    col = _cadd(col, _SUBSURF, (1.0 - diff) * 0.18 * dn)    # blood under the skin
    col = _cadd(col, _SHEEN, spec * 0.38)                   # wet (not metallic) glint
    col = _cadd(col, _GOLD_RIM, rim * (0.45 + 0.55 * threat) * (0.4 + 0.6 * dn))
    return _ci(col)


def _blit_mask(lay, x, y, height, rise, gx, gy, seed):
    m = _mask(height * rise, 0.5 + 0.5 * rise, gx, gy, seed)
    if rise < 0.99:
        m = m.copy()
        m.fill((255, 255, 255, int(255 * rise)), special_flags=pygame.BLEND_RGBA_MULT)
    lay.blit(m, (int(x - m.get_width() / 2), int(y - m.get_height() / 2)))


def _draw_arms(lay, o3, op, ocenter, sz, cx, cy, t, threat, arm_roots):
    """Limbs that erupt from the body's own geometry and STRETCH toward the
    player -- rooted at surface vertices, curving out then lunging at a target
    below/in front of the camera, tapering to a mask 'hand'. They reach only as
    the thing rouses (threat), and each pulses on its own phase."""
    if threat < 0.18:
        return
    gate = min(1.0, (threat - 0.18) / 0.45)
    # the player: below and toward the camera (screen-down, +z toward viewer)
    tgt0 = (ocenter[0], ocenter[1] - 1.9, ocenter[2] + 1.4)
    N = 10
    rad3 = 0.30
    for ai, (idx, ph) in enumerate(arm_roots):
        if idx >= len(o3):
            continue
        root = o3[idx]
        outward = _norm(_sub(root, ocenter))
        # near-side limbs reach hard at the player; far-side ones barely stir
        nearness = 0.5 + 0.5 * (1 if outward[2] > 0 else -1) * min(1.0, abs(outward[2]) * 2)
        lunge = 0.5 + 0.5 * math.sin(t * (0.5 + 0.07 * ai) + ph)
        reach = (0.12 + 0.95 * lunge) * gate * (0.35 + 0.65 * nearness)
        if reach < 0.14:
            continue
        tgt = (tgt0[0] + 1.3 * math.sin(ai * 2.1 + t * 0.25),
               tgt0[1] + 0.5 * math.sin(ai * 1.3),
               tgt0[2] + 0.5 * math.cos(ai * 1.7))
        end = (root[0] + (tgt[0] - root[0]) * reach,
               root[1] + (tgt[1] - root[1]) * reach,
               root[2] + (tgt[2] - root[2]) * reach)
        # control bulges OUT along the surface normal AND sideways -> an organic
        # curve, not a straight stick
        side = _norm(_cross(outward, (0, 0, 1)))
        wig = 0.6 * math.sin(t * 1.4 + ph)
        ctrl = (root[0] + outward[0] * 0.9 + side[0] * wig,
                root[1] + outward[1] * 0.9 + side[1] * wig,
                root[2] + outward[2] * 0.9 + side[2] * wig)
        pts, rads = [], []
        for k in range(N + 1):
            s = k / N
            mt = 1 - s
            P = (mt * mt * root[0] + 2 * mt * s * ctrl[0] + s * s * end[0],
                 mt * mt * root[1] + 2 * mt * s * ctrl[1] + s * s * end[1],
                 mt * mt * root[2] + 2 * mt * s * ctrl[2] + s * s * end[2])
            pts.append((_proj(P, cx, cy, sz), P[2]))
            k3 = _FOCAL / (_Z_EYE - P[2])
            rads.append(max(1.0, rad3 * ((1 - s) ** 1.2 + 0.04) * k3 * sz))
        # per-point unit-perpendicular + pixel radius
        base = []
        for k in range(N + 1):
            (px, py), _z = pts[k]
            if k < N:
                (nx, ny), _ = pts[k + 1]
            else:
                (nx, ny), _ = pts[k - 1]
                nx, ny = 2 * px - nx, 2 * py - ny
            dx, dy = nx - px, ny - py
            dl = math.hypot(dx, dy) or 1.0
            base.append((px, py, -dy / dl, dx / dl, rads[k]))

        def ribbon(sc):
            l = [(px + ux * r * sc, py + uy * r * sc) for (px, py, ux, uy, r) in base]
            rt = [(px - ux * r * sc, py - uy * r * sc) for (px, py, ux, uy, r) in base]
            return l + rt[::-1]
        # nested ribbons fake a ROUND cross-section: dark rim -> mid -> a sheen
        # ridge down the middle (so the limb reads volumetric, not a flat blade)
        lit = 0.4 + 0.6 * max(0.0, outward[2])           # near-side limbs catch more
        edge = _ci(_cmix(_MEM_SHADOW, _MEM, 0.5))
        midc = _ci(_cmix(_MEM_SHADOW, _MEM_HI, 0.18 + 0.22 * lit))
        ridge = _ci(_cadd(_cmix(_MEM_SHADOW, _MEM_HI, 0.5), _SHEEN, 0.22 * lit))
        pygame.draw.polygon(lay, (*edge, 244), ribbon(1.0))
        pygame.draw.polygon(lay, (*midc, 244), ribbon(0.60))
        pygame.draw.polygon(lay, (*ridge, 150), ribbon(0.24))
        left = [(px + ux * r, py + uy * r) for (px, py, ux, uy, r) in base]
        right = [(px - ux * r, py - uy * r) for (px, py, ux, uy, r) in base]
        pygame.draw.lines(lay, (*_GOLD_RIM, 64), False, left, 1)
        pygame.draw.lines(lay, (*_GOLD_RIM, 64), False, right, 1)
        # the hand is a mask, gazing at you
        (tx, ty), _tz = pts[N]
        _blit_mask(lay, tx, ty, rads[N - 1] * 4.2, gate,
                   -max(-1.0, min(1.0, (tx - cx) / (sz * 0.9))) * 0.7, 0.4, ai + 2)


def draw_king_unfold(surf, cx, cy, t, threat=0.0, scale=96.0):
    """THE UNFOLDING, centred at (cx, cy). `threat` 0..1: a small dark fold ->
    larger, faster eversion, the heart kindling, eyes opening, the Sign
    resolving, more light eaten."""
    form = _build()
    sz = scale * (0.7 + 0.5 * threat)
    spd = 0.16 + 0.42 * threat
    body_ang = (t * spd * 0.55, t * spd * 0.43 + 1.3, t * spd * 0.27, t * spd * 0.17)
    # the heart turns faster and on different planes -> it everts WITHIN the body
    heart_ang = (t * spd * 1.15 + 0.7, t * spd * 0.9, t * spd * 0.5, t * spd * 0.3)

    o3 = _xform(form["overts"], body_ang, 0.05, t)
    c3 = _xform(form["cverts"], heart_ang, 0.0, t)
    op = [_proj(p, cx, cy, sz) for p in o3]
    cp = [_proj(p, cx, cy, sz) for p in c3]

    ocenter = (sum(p[0] for p in o3) / len(o3),
               sum(p[1] for p in o3) / len(o3),
               sum(p[2] for p in o3) / len(o3))
    zs = [p[2] for p in o3]
    zmin, zmax = min(zs), max(zs)
    zr = (zmax - zmin) or 1.0

    _eat_light(surf, cx, cy, sz * 1.85, 60 + 110 * threat)
    lay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)

    # build outer face records (outward normal, facing, depth)
    back, front = [], []
    for fi, face in enumerate(form["ofaces"]):
        v0, v1, v2 = o3[face[0]], o3[face[1]], o3[face[2]]
        N = _norm(_cross(_sub(v1, v0), _sub(v2, v0)))
        cen = ((v0[0] + v1[0] + v2[0] + o3[face[3]][0]) / 4,
               (v0[1] + v1[1] + v2[1] + o3[face[3]][1]) / 4,
               (v0[2] + v1[2] + v2[2] + o3[face[3]][2]) / 4)
        if _dot(N, _sub(cen, ocenter)) < 0:                # force outward
            N = (-N[0], -N[1], -N[2])
        rec = (cen[2], fi, face, N)
        (front if N[2] > 0 else back).append(rec)
    back.sort(key=lambda r: r[0])
    front.sort(key=lambda r: r[0])

    def draw_membrane(recs, front_side):
        for zc, fi, face, N in recs:
            poly = [op[i] for i in face]
            dn = (zc - zmin) / zr
            col = _shade_face(N, dn, threat)
            al = (196 if front_side else 232)
            pygame.draw.polygon(lay, (*col, al), poly)
            # anti-alias the silhouette only (no per-facet seam -> smoother skin)
            if front_side and abs(N[2]) < 0.30:
                pygame.draw.polygon(lay, (*col, al), poly, 1)

    # 1) far wall of the mass (inside of the back)
    draw_membrane(back, False)

    # 2) the heart: glow + emissive everting shells, glimpsed through the flesh
    hc = (sum(p[0] for p in cp) / len(cp), sum(p[1] for p in cp) / len(cp))
    _heart_glow(lay, hc[0], hc[1], sz * 0.7, 70 + 150 * threat)
    czs = [p[2] for p in c3]
    czmin, czr = min(czs), (max(czs) - min(czs)) or 1.0
    crecs = sorted(range(len(form["cfaces"])),
                   key=lambda fi: sum(c3[i][2] for i in form["cfaces"][fi]) / 4)
    for fi in crecs:
        face = form["cfaces"][fi]
        poly = [cp[i] for i in face]
        zc = sum(c3[i][2] for i in face) / len(face)
        dn = (zc - czmin) / czr
        col = _ci(_cmix(_HEART, _GOLD_HI, 0.2 + 0.6 * dn))
        pygame.draw.polygon(lay, (*col, int(40 + 70 * dn)), poly)

    # 3) near wall of the mass (occludes/veils the heart -> flesh)
    draw_membrane(front, True)

    # 4) ARMS: limbs erupt from the geometry and stretch toward the player (on
    # top of the body -- they reach out past its silhouette, toward the camera)
    _draw_arms(lay, o3, op, ocenter, sz, cx, cy, t, threat, form["arm_roots"])

    # 5) MASKS surface on the near skin -- the wrong faces, all gazing at you
    if threat > 0.28:
        appear = min(1.0, (threat - 0.28) / 0.4)
        fmap = {fi: (face, N) for zc, fi, face, N in front}
        for fi, ph in form["mask_faces"].items():
            if fi not in fmap:
                continue
            face, N = fmap[fi]
            poly = [op[i] for i in face]
            area = 0.0
            for k in range(len(poly)):
                x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % len(poly)]
                area += x0 * y1 - x1 * y0
            mcx = sum(p[0] for p in poly) / len(poly)
            mcy = sum(p[1] for p in poly) / len(poly)
            mh = math.sqrt(abs(area)) * 1.5
            surf_ph = (t * 0.5 + ph) % 6.0                 # masks surface + sink
            rise = (1.0 if surf_ph > 0.5 else surf_ph / 0.5) * appear
            if rise < 0.12:
                continue
            gx = -max(-1.0, min(1.0, (mcx - cx) / (sz * 0.9))) * 0.7   # turn to you
            _blit_mask(lay, mcx, mcy, mh, rise, gx, 0.45, int(ph))

    # 6) the Sign resolves for a beat on the most head-on facet
    if front and threat > 0.45:
        zc, fi, face, N = max(front, key=lambda r: r[3][2])
        poly = [op[i] for i in face]
        sx = sum(p[0] for p in poly) / len(poly)
        sy = sum(p[1] for p in poly) / len(poly)
        ar = 0.0
        for k in range(len(poly)):
            x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % len(poly)]
            ar += x0 * y1 - x1 * y0
        pulse = max(0.0, math.sin(t * 0.5)) ** 3
        _yellow_sign(lay, sx, sy, math.sqrt(abs(ar)) * 0.32,
                     int(150 * pulse * min(1.0, (threat - 0.45) / 0.3)))

    surf.blit(lay, (0, 0))
