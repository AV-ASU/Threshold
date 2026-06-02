"""THE UNFOLDING -- a fear-first, NON-humanoid King prototype (not wired in).

The thesis (from the chat design discussion): otherworldly = form that WON'T
RESOLVE. This is a real 4-dimensional object (a tesseract) rotating through 4D
planes and projected 4D->3D->2D, so it visibly turns INSIDE-OUT -- the inner
cell everts to become the outer one. The eye can never lock its silhouette;
it is plainly a sliver of something larger poking into our space.

Lessons carried from the failed passes: it is DARK and EATS the light; the gold
is sick and sparse -- only the membrane edges, the Yellow Sign that resolves for
a beat, and the EYES that surface on facets, find you, and are gone. No body, no
face, no symmetry the eye can rest on.

The gold halo / shatter (rendering/king_halo.py) is still the CATCH bloom.

Preview:  python tools/preview_king_unfold.py
"""
import math
import random

import pygame

from rendering.king3d import _shade

# --- palette: dark membrane, sick gold edges, the waking gold ---------------
_MEM = (12, 11, 16)                 # the membrane faces: near-black, faintly cold
_MEM_HI = (26, 24, 34)
_EDGE_DK = (84, 68, 30)             # the structure: dim, sick gold
_EDGE_HI = (206, 172, 78)
_GOLD = (210, 172, 66)
_GOLD_HI = (242, 214, 122)
_VOID = (4, 4, 6)

_W_EYE = 2.15                        # 4D camera distance (everting strength)
_Z_EYE = 3.3                         # 3D camera distance
_FOCAL = 2.7

_VERTS4 = None
_EDGES = None
_FACES = None
_EYE_FACES = None
_RNG = random.Random(13)


def reset_king_unfold_fx():
    pass


def _build():
    """The tesseract: 16 vertices, 32 edges, 24 square faces. Cached."""
    global _VERTS4, _EDGES, _FACES, _EYE_FACES
    if _VERTS4 is not None:
        return
    verts = []
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                for w in (-1, 1):
                    verts.append((x * 0.9, y * 0.9, z * 0.9, w * 0.9))
    _VERTS4 = verts
    # edges: vertices differing in exactly one coordinate
    edges = []
    for i in range(16):
        for j in range(i + 1, 16):
            d = sum(1 for k in range(4) if verts[i][k] != verts[j][k])
            if d == 1:
                edges.append((i, j))
    _EDGES = edges
    # faces: pick 2 axes to vary, fix the other 2 -> a square (CCW order)
    faces = []
    quad = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
    for a in range(4):
        for b in range(a + 1, 4):
            others = [k for k in range(4) if k not in (a, b)]
            for fv0 in (-1, 1):
                for fv1 in (-1, 1):
                    face = []
                    for (va, vb) in quad:
                        coord = [0, 0, 0, 0]
                        coord[a] = va; coord[b] = vb
                        coord[others[0]] = fv0; coord[others[1]] = fv1
                        idx = verts.index((coord[0] * 0.9, coord[1] * 0.9,
                                           coord[2] * 0.9, coord[3] * 0.9))
                        face.append(idx)
                    faces.append(face)
    _FACES = faces
    # a sparse, fixed subset of faces carry an eye (with a blink phase)
    r = random.Random(91)
    picks = r.sample(range(len(faces)), 7)
    _EYE_FACES = {fi: r.uniform(0, 9) for fi in picks}


def _rot(p, i, j, ang):
    c, s = math.cos(ang), math.sin(ang)
    q = list(p)
    q[i] = p[i] * c - p[j] * s
    q[j] = p[i] * s + p[j] * c
    return q


def _project(p4, cx, cy, scale):
    """4D -> 3D (perspective in w, the source of the everting) -> 2D."""
    w = p4[3]
    k4 = 1.0 / (_W_EYE - w)
    x, y, z = p4[0] * k4, p4[1] * k4, p4[2] * k4
    k3 = _FOCAL / (_Z_EYE - z)
    return (cx + x * k3 * scale, cy - y * k3 * scale, z, k3)


def _eat_light(surf, cx, cy, r, strength):
    r = int(r)
    if r < 2:
        return
    a = pygame.Surface((r * 2, r * 2))
    steps = max(6, r // 2)
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        f = 1 - i / steps
        v = int(strength * (f ** 2.3))
        if v > 0:
            pygame.draw.circle(a, (v, v, v), (r, r), rr)
    surf.blit(a, (int(cx - r), int(cy - r)), special_flags=pygame.BLEND_RGB_SUB)


def _yellow_sign(surf, x, y, r, a):
    """The Sign, resolving for a beat: a three-armed coil. Faint, sick gold."""
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
        if len(pts) >= 2:
            pygame.draw.lines(surf, (*_GOLD, a), False, pts, max(1, int(r * 0.10)))


def _eye(surf, x, y, r, openf, gaze, a):
    """An eye surfacing on a facet -- sick gold iris, black pupil, then gone."""
    if r < 1.5 or openf <= 0.05 or a < 10:
        return
    hh = max(1.0, r * 0.62 * openf)
    pts = []
    for k in range(12):
        ang = math.tau * k / 12
        pts.append((x + math.cos(ang) * r, y + math.sin(ang) * hh))
    pygame.draw.polygon(surf, (4, 4, 6, a), pts)
    pygame.draw.polygon(surf, (*_EDGE_HI, a), pts, max(1, int(r * 0.16)))
    ir = max(1, int(hh * 0.8))
    gx = int(x + gaze * r * 0.4)
    pygame.draw.circle(surf, (*_GOLD, a), (gx, int(y)), ir)
    pygame.draw.circle(surf, (4, 4, 6, a), (gx, int(y)), max(1, int(ir * 0.5)))
    if ir >= 3:
        pygame.draw.circle(surf, (*_GOLD_HI, a),
                           (gx - ir // 3, int(y) - ir // 3), max(1, ir // 4))


def draw_king_unfold(surf, cx, cy, t, threat=0.0, scale=70.0):
    """Draw THE UNFOLDING centred at (cx, cy). `threat` 0..1 escalates: a small
    distant fold -> larger, faster eversion -> eyes surface + the Sign resolves
    + it eats more light and looms."""
    _build()
    # stop-motion bias: it turns in WRONG jerks, not a smooth spin
    def stut(v, q):
        return 0.78 * v + 0.22 * (math.floor(v * q) / q)
    spd = 0.18 + 0.5 * threat
    a = stut(t * spd * 0.9, 6)                      # x-w  (everts)
    b = stut(t * spd * 0.7 + 1.3, 6)               # y-w  (everts)
    c = t * spd * 0.33                             # z-y  (tumble, smoother)
    d = t * spd * 0.21                             # x-y  (slow spin)
    sz = scale * (0.7 + 0.5 * threat)              # it LOOMS as it rouses

    # rotate + project every vertex; a faint organic breathing perturbation
    pts, depths = [], []
    for vi, v in enumerate(_VERTS4):
        p = list(v)
        wob = 0.06 * math.sin(t * 1.3 + vi)
        p = [p[0] + wob, p[1] - wob, p[2] + 0.05 * math.sin(t + vi * 2), p[3]]
        p = _rot(p, 0, 3, a)
        p = _rot(p, 1, 3, b)
        p = _rot(p, 2, 1, c)
        p = _rot(p, 0, 1, d)
        sx, sy, z, k3 = _project(p, cx, cy, sz)
        pts.append((sx, sy)); depths.append(z)
    zmin, zmax = min(depths), max(depths)
    zr = (zmax - zmin) or 1.0

    # 1) EAT the light around the mass
    _eat_light(surf, cx, cy, sz * 1.7, 55 + 95 * threat)

    # everything onto a translucent layer (membranes need real alpha)
    lay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)

    # 2) faces: dark membranes, painter-sorted back->front. The 4D projection
    # self-intersects, so the silhouette refuses to resolve.
    order = sorted(range(len(_FACES)),
                   key=lambda fi: sum(depths[i] for i in _FACES[fi]))
    most_front_area, sign_face = 0.0, None
    for fi in order:
        face = _FACES[fi]
        poly = [pts[i] for i in face]
        # signed area: sign = facing, magnitude = apparent size
        area = 0.0
        for k in range(4):
            x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % 4]
            area += x0 * y1 - x1 * y0
        facing = area < 0                          # toward camera
        fa = abs(area)
        zc = sum(depths[i] for i in face) / 4
        dn = (zc - zmin) / zr                       # 0 far -> 1 near
        # membrane fill: more head-on + nearer = a touch more substance
        al = int((26 + 60 * dn) * (0.5 + 0.5 * (1 if facing else 0.4)))
        col = _shade(_MEM_HI if facing else _MEM, 0.5 + 0.5 * dn)
        pygame.draw.polygon(lay, (col[0], col[1], col[2], al), poly)
        if facing and fa > most_front_area:
            most_front_area = fa; sign_face = (poly, fa)

    # 3) edges: the sick-gold structure, brighter where nearer
    for (i, j) in _EDGES:
        zc = (depths[i] + depths[j]) / 2
        dn = (zc - zmin) / zr
        col = _shade(_EDGE_DK, 0.4 + 0.6 * dn)
        if dn > 0.7 and threat > 0.3:
            col = _shade(_EDGE_HI, 0.4 + 0.6 * threat)
        w = max(1, int(1 + 2 * dn))
        pygame.draw.line(lay, col, pts[i], pts[j], w)

    # 4) eyes surfacing on the near, head-on facets (only as it rouses)
    if threat > 0.32:
        appear = (threat - 0.32) / 0.4
        for fi, ph in _EYE_FACES.items():
            face = _FACES[fi]
            poly = [pts[i] for i in face]
            area = 0.0
            for k in range(4):
                x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % 4]
                area += x0 * y1 - x1 * y0
            if area >= 0:                            # only front-facing facets
                continue
            zc = sum(depths[k] for k in face) / 4
            dn = (zc - zmin) / zr
            if dn < 0.45:
                continue
            ex = sum(p[0] for p in poly) / 4
            ey = sum(p[1] for p in poly) / 4
            er = math.sqrt(abs(area)) * 0.22
            bz = (t * 0.7 + ph) % 5.0
            openf = 1.0 if bz > 0.2 else abs(bz - 0.1) / 0.1
            openf *= max(0.0, min(1.0, appear))
            gaze = math.sin(t * 0.3 + ph) * 0.6
            _eye(lay, ex, ey, er, openf, gaze, int(220 * min(1.0, appear)))

    # 5) the Sign resolves for a beat on the most head-on facet
    if sign_face and threat > 0.45:
        poly, fa = sign_face
        sx = sum(p[0] for p in poly) / 4
        sy = sum(p[1] for p in poly) / 4
        pulse = max(0.0, math.sin(t * 0.5)) ** 3    # only now and then
        a = int(150 * pulse * min(1.0, (threat - 0.45) / 0.3))
        _yellow_sign(lay, sx, sy, math.sqrt(fa) * 0.28, a)

    surf.blit(lay, (0, 0))
