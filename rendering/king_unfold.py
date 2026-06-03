"""THE UNFOLDING -- the non-humanoid King. WIRED IN as the `yellow_king`
sprite: rendering/sprites.py `draw_npc_sprite` routes the King's draw here when
`sprites.KING_UNFOLD` is True (flip it False to fall back to the flat pallid-mask
`_draw_king`). The catch/death routes to `draw_unfold_catch` from
`Game._draw_death_screen`. Fed the live `threat`, `birth`, and a screen-space
`to_player` from `Game.draw_world`.

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
_TOOTH = (198, 188, 168)            # bone (desaturated, sickly), high-contrast
_TOOTH_DK = (92, 82, 72)            # tooth in shadow / at the gum
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


def reset_king_unfold_fx():
    pass


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
    NLAT, NLON = 14, 20                       # tuned for ~90px: fewer facets
    overts, ofaces = _sphere_mesh(NLAT, NLON, outer_rf)
    r = random.Random(23)
    # EYE SITES: facets where eyes open across the skin -- wrong faces that
    # surface and gaze, never assembling into one. Each rides a facet, so it
    # slides / scales / winks with the eversion. Each carries its own blink
    # phase. (No carved mask sprites: the creature never wears a nameable face.)
    eye_sites = [(fi, r.uniform(0, 6.283))
                 for fi in r.sample(range(len(ofaces)), 16)]
    # MAW SITES: facets where eversion-maws tear open -- scattered, fewer than
    # the eyes (mouths are bigger), each gnashing on its own phase. Plural and
    # wrong: it is all watching AND all hungry; never one face-with-a-mouth.
    maw_sites = [(fi, r.uniform(0, 6.283))
                 for fi in r.sample(range(len(ofaces)), 5)]

    # arm roots: a POOL of candidate vertices spread over the mass. Each frame
    # _draw_arms extrudes only the ones whose 4D w has everted FORWARD past a
    # threshold (the eversion pushes the limb out), so the live count varies and
    # is never the same twice.
    arm_roots = []
    for a in range(18):
        i = int(NLAT * (0.30 + 0.50 * ((a * 5) % 7) / 6.0))   # scatter in lat
        j = int((a / 18.0) * NLON + 0.5) % NLON
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

    _FORM = dict(overts=overts, ofaces=ofaces, eye_sites=eye_sites,
                 maw_sites=maw_sites, nlat=NLAT, nlon=NLON,
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


def _draw_maw3d(lay, sample, N, em, openf, cx, cy, sz, zmin, zr, seed, a):
    """An EVERSION-MAW as REAL geometry, BOUND to the flesh. `sample(pu, pv)`
    returns the 3D point on the deformed surface for a param offset in [-1,1]^2
    around the maw centre -- it bilinearly interpolates the ACTUAL deformed mesh
    over a patch, so the rim follows the region's live stretch, shear AND
    curvature (it tears into curved gashes, wraps over folds, warps non-uniformly
    as the patch everts). The throat sinks INTO the body along -N to a gullet at
    the bottom; teeth are 3D bone spikes rooted on the warped rim, leaning in +
    raised out along +N. Everything projects + depth-sorts. NOT a jaw. `em` is
    the world scale for throat depth + tooth length."""
    if em <= 0.0 or a < 12 or openf <= 0.03:
        return
    hole = 0.34 + 0.50 * openf                   # opening, in patch-param radius
    depth = em * (0.50 + 0.70 * openf)           # how far the throat sinks in

    def onring(ang, rf, dz):
        p = sample(math.cos(ang) * rf, math.sin(ang) * rf)   # on the curved skin
        return (p[0] + N[0] * dz, p[1] + N[1] * dz, p[2] + N[2] * dz)

    def pr(p):
        return _proj(p, cx, cy, sz)
    K = 9
    cP = sample(0.0, 0.0)
    outer = [onring(math.tau * k / K, hole, 0.0) for k in range(K)]
    inner = [onring(math.tau * k / K, hole * 0.42, -depth * 0.72) for k in range(K)]
    bottom = (cP[0] - N[0] * depth, cP[1] - N[1] * depth, cP[2] - N[2] * depth)
    # throat walls (a dark, wet pit) -> sorted far-first within the maw
    polys = []
    for k in range(K):
        k2 = (k + 1) % K
        q = (outer[k], outer[k2], inner[k2], inner[k])
        zc = (q[0][2] + q[1][2] + q[2][2] + q[3][2]) * 0.25
        dn = max(0.0, min(1.0, (zc - zmin) / zr))
        col = _ci(_cadd(_cmix(_MEM_SHADOW, _MEM, 0.05 + 0.12 * dn), _SUBSURF, 0.10))
        polys.append((zc, [pr(p) for p in q], (*col, a)))
        tri = (inner[k], inner[k2], bottom)
        zc2 = (inner[k][2] + inner[k2][2] + bottom[2]) / 3.0
        polys.append((zc2, [pr(p) for p in tri], (*_ci(_MEM_SHADOW), a)))
    polys.sort(key=lambda r: r[0])
    for _z, pts, col in polys:
        pygame.draw.polygon(lay, col, pts)
    # the gullet -- gold light pooling at the bottom of the throat
    bx, by = pr(bottom)
    k3 = _FOCAL / (_Z_EYE - bottom[2])
    _heart_glow(lay, bx, by, max(2, int(hole * em * 0.8 * k3 * sz)),
                int(55 + 150 * openf))
    # ROWS of sharp teeth lining the throat ALL THE WAY DOWN -- concentric rings
    # receding into the gullet, each smaller, deeper, and darker than the last
    # (a lamprey/anglerfish throat), not one ring of buck teeth at the lip.
    teeth = []
    # LOD: full rows of teeth only when the maw is big on screen (close / the
    # catch); at game scale you can't resolve them, so draw fewer rings -> the
    # per-maw cost (and the worst-case spike) collapses where it matters.
    k3c = _FOCAL / (_Z_EYE - cP[2])
    rpix = hole * em * k3c * sz
    NRINGS = 3 if rpix > 16 else (2 if rpix > 8 else 1)
    for rr in range(NRINGS):
        df = rr / NRINGS                          # 0 at the lip, deeper inward
        nt = 12 - 3 * rr                          # throat narrows -> fewer teeth
        wallR = hole * (1.0 - 0.62 * df)          # throat narrows going down
        dz = -depth * (df * 0.92 + 0.05)          # how far down the gullet
        shade = 1.0 - 0.62 * df                   # deeper teeth fall into shadow
        ln_in = wallR * 0.66                       # reach toward the throat axis
        up = depth * (0.18 - 0.16 * df)            # lip teeth overhang out; deep ones don't
        jit = rr * 1.7
        for k in range(nt):
            if rr == 0 and math.sin(seed * 3.1 + k * 2.7) < -0.66:   # a few lip gaps
                continue
            ang = math.tau * k / nt + 0.09 * math.sin(seed + k + jit)
            dA = (math.tau / nt) * 0.34            # narrow base -> sharp tooth
            lv = 0.7 + 0.55 * (0.5 + 0.5 * math.sin(seed * 0.7 + k * 1.9 + jit))
            t0 = onring(ang - dA, wallR, dz)
            t1 = onring(ang + dA, wallR, dz)
            tipP = onring(ang, max(0.015, wallR - ln_in * lv), dz)   # toward the axis
            tip = (tipP[0] + N[0] * up, tipP[1] + N[1] * up, tipP[2] + N[2] * up)
            Nt = _norm(_cross(_sub(t1, t0), _sub(tip, t0)))
            if Nt[2] < 0:
                Nt = (-Nt[0], -Nt[1], -Nt[2])
            lit = max(0.0, _dot(Nt, _L)) * shade
            col = _ci(_cmix(_TOOTH_DK, _TOOTH, 0.16 + 0.84 * lit))
            zc = (t0[2] + t1[2] + 2 * tip[2]) * 0.25
            teeth.append((zc, [pr(t0), pr(t1), pr(tip)], (*col, a)))
    teeth.sort(key=lambda r: r[0])
    for _z, pts, col in teeth:
        pygame.draw.polygon(lay, col, pts)


# --------------------------------------------------------------------------- #
def _shade_face(N, dn, threat):
    """Oily membrane shading from a 3D normal: lit dark flesh + wet sheen +
    gold rim trapped on the grazing silhouette."""
    diff = max(0.0, _dot(N, _L))
    spec = max(0.0, _dot(N, _H)) ** 18
    rim = (1.0 - abs(N[2])) ** 2.7                          # gold edge band
    col = _cmix(_MEM_SHADOW, _MEM_HI, 0.12 + 0.85 * diff)
    col = _cmix(col, _MEM, 0.25)                            # keep it dark/oily
    col = _cadd(col, _SUBSURF, (1.0 - diff) * 0.18 * dn)    # blood under the skin
    col = _cadd(col, _SHEEN, spec * 0.38)                   # wet (not metallic) glint
    # a gold rim trapped on the grazing silhouette -- present even when calm, so
    # the dark flesh keeps a glowing edge against a near-black scene
    col = _cadd(col, _GOLD_RIM, rim * (0.50 + 0.5 * threat) * (0.45 + 0.55 * dn))
    return _ci(col)


def _everted_w(v4, angs):
    """The 4D w of a rest vertex after the body rotation -- how far it has
    everted toward the 4D camera. High w == that part of the mass is turning
    inside-out forward, which is where a limb erupts."""
    a, b, c, d = angs
    p = list(v4)
    p = _rot(p, 0, 3, a); p = _rot(p, 1, 3, b)
    p = _rot(p, 2, 1, c); p = _rot(p, 0, 1, d)
    return p[3]


_ARM_MAX = 5


def _draw_arms(lay, o3, op, ocenter, sz, cx, cy, t, threat, arm_roots,
               overts, body_ang, zmin, zr, pdx=0.0, pdy=1.0, birth=1.0):
    """Limbs are the body UNFOLDING, not appendages bolted on. A root extrudes
    only while its 4D w has everted FORWARD past a threshold -- so the eversion
    itself pushes the limb out, the live count varies (2-5), and the silhouette
    is never the same twice. As the thing rouses (threat) the emerged limbs
    lunge at the player below/in front of the camera, tapering to an eye.

    Each limb is REAL extruded geometry: a swept tube of mesh quads grown from
    the root, projected and shaded with _shade_face against the SAME light and
    depth range as the body -- so it reads as the same lit flesh continuing out
    of the mass, not a ribbon pasted on top."""
    if threat < 0.18:
        return
    # limbs come in LAST in the birth (they're the lethal reach) -- no limbs
    # until the body has mostly bloomed
    limb_b = max(0.0, min(1.0, (birth - 0.55) / 0.45))
    if limb_b <= 0.0:
        return
    gate = min(1.0, (threat - 0.18) / 0.45) * limb_b
    # which roots are everting forward right now -> those are the live limbs
    cand = []
    for ai, (idx, ph) in enumerate(arm_roots):
        if idx >= len(o3):
            continue
        outward = _norm(_sub(o3[idx], ocenter))
        emerge = max(0.0, min(1.0, (_everted_w(overts[idx], body_ang) - 0.48) / 0.55))
        cand.append((emerge, ai, idx, ph, outward))
    live = [c for c in cand if c[0] > 0.06]
    # above threat 0.8 the thing is fully roused: GUARANTEE at least two limbs
    # are out and reaching for the player -- force the two most player-facing
    # roots (outward toward the camera) even if eversion hasn't pushed them yet.
    forced = set()
    if threat > 0.8:
        for c in sorted(cand, key=lambda c: c[4][2], reverse=True):
            if len(forced) >= 2 or c[4][2] <= 0.0:
                break
            forced.add(c[1])
            live.append((max(c[0], 0.62), c[1], c[2], c[3], c[4]))
    # de-dup per root (keep the higher emerge), strongest first, cap the count
    best = {}
    for c in live:
        if c[1] not in best or c[0] > best[c[1]][0]:
            best[c[1]] = c
    live = sorted(best.values(), key=lambda c: c[0], reverse=True)[:_ARM_MAX]
    # the player, in the model's own space: screen +x -> +x, screen +y(down) ->
    # -y, plus a touch toward the camera so the reach reads as looming forward
    tgt0 = (ocenter[0] + pdx * 1.9, ocenter[1] - pdy * 1.9, ocenter[2] + 1.4)
    M = 8          # rings of mesh along the limb
    K = 6          # verts per ring -> a round, lit cross-section
    quads = []     # (depth, poly2d, color, alpha) gathered across all limbs
    tips = []      # tip eyes, drawn on top after the flesh
    for emerge, ai, idx, ph, outward in live:
        root = o3[idx]
        # near-side limbs reach hard at the player; far-side ones barely stir
        nearness = 0.5 + 0.5 * (1 if outward[2] > 0 else -1) * min(1.0, abs(outward[2]) * 2)
        lunge = 0.5 + 0.5 * math.sin(t * (0.5 + 0.07 * ai) + ph)
        reach = (0.12 + 0.95 * lunge) * gate * emerge * (0.35 + 0.65 * nearness)
        if ai in forced:                         # a forced limb always reaches
            reach = max(reach, 0.55 * gate)
        if reach < 0.12:
            continue
        # forced limbs lunge straight at the player; the rest SPLAY outward along
        # their own root direction (up / out / across), so the thing never reads
        # as a spider with every leg converging on the floor.
        if ai in forced:
            aim = tgt0
        else:
            aim = (ocenter[0] + outward[0] * 3.0 * 0.7 + tgt0[0] * 0.3,
                   ocenter[1] + (outward[1] * 3.0 + 0.7) * 0.7 + tgt0[1] * 0.3,
                   ocenter[2] + outward[2] * 3.0 * 0.7 + tgt0[2] * 0.3)
        tgt = (aim[0] + 1.0 * math.sin(ai * 2.1 + t * 0.25),
               aim[1] + 0.6 * math.sin(ai * 1.3),
               aim[2] + 0.5 * math.cos(ai * 1.7))
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
        # sample the centreline + a tapering WORLD-space radius (root matches the
        # local body radius so the tube grows straight out of the skin)
        rad0 = 0.25 * (0.55 + 0.45 * emerge)
        cen = []
        for k in range(M + 1):
            s = k / M
            mt = 1 - s
            P = (mt * mt * root[0] + 2 * mt * s * ctrl[0] + s * s * end[0],
                 mt * mt * root[1] + 2 * mt * s * ctrl[1] + s * s * end[1],
                 mt * mt * root[2] + 2 * mt * s * ctrl[2] + s * s * end[2])
            rw = rad0 * ((1 - s) ** 0.85 + 0.10)
            cen.append((P, rw))
        # build rings of geometry with a stable frame along the path. The
        # centreline stays 3D (so the limb keeps AIMING at the player and reads
        # as an arm) -- the 4D lives in the CROSS-SECTION: each rim point gets a
        # 4th-axis (ana/kata) offset wp, projected by the SAME w-divide as the
        # body, so the girth everts -- bulges swell, orbit, and travel down the
        # limb, turning inside-out the way no 3D tube can.
        ev = 0.40 + 0.45 * threat                    # eversion strength (4D)
        rings = []
        for k in range(M + 1):
            P, rw = cen[k]
            sfrac = k / M
            a = cen[max(0, k - 1)][0]
            b = cen[min(M, k + 1)][0]
            T = _norm((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
            ref = (0.0, 1.0, 0.0) if abs(T[1]) < 0.9 else (1.0, 0.0, 0.0)
            u = _norm(_cross(T, ref))
            v = _cross(T, u)
            ring = []
            for m in range(K):
                ang = math.tau * m / K
                cu, sv = math.cos(ang) * rw, math.sin(ang) * rw
                ox = u[0] * cu + v[0] * sv
                oy = u[1] * cu + v[1] * sv
                oz = u[2] * cu + v[2] * sv
                wp = ev * math.sin(ang - (t * 1.2 + sfrac * 4.0 + ph))
                f = _W_EYE / (_W_EYE - wp)           # the 4D->3D eversion swell
                ring.append((P[0] + ox * f, P[1] + oy * f, P[2] + oz * f))
            rings.append((ring, P))
        # quads between consecutive rings, shaded as the same membrane flesh
        al = int(150 + 98 * emerge)
        for k in range(M):
            ring0, c0 = rings[k]
            ring1, c1 = rings[k + 1]
            for m in range(K):
                m2 = (m + 1) % K
                q = (ring0[m], ring0[m2], ring1[m2], ring1[m])
                Nf = _norm(_cross(_sub(q[1], q[0]), _sub(q[3], q[0])))
                cenq = ((q[0][0] + q[1][0] + q[2][0] + q[3][0]) * 0.25,
                        (q[0][1] + q[1][1] + q[2][1] + q[3][1]) * 0.25,
                        (q[0][2] + q[1][2] + q[2][2] + q[3][2]) * 0.25)
                if _dot(Nf, _sub(cenq, c0)) < 0:           # face outward
                    Nf = (-Nf[0], -Nf[1], -Nf[2])
                if Nf[2] < -0.15:                          # cull the far side
                    continue
                dn = max(0.0, min(1.0, (cenq[2] - zmin) / zr))
                col = _shade_face(Nf, dn, threat)
                poly = [_proj(p, cx, cy, sz) for p in q]
                quads.append((cenq[2], poly, col, al))
        # the tip opens an EYE, gazing at you
        ptip, rtip = cen[M]
        (tx, ty) = _proj(ptip, cx, cy, sz)
        k3 = _FOCAL / (_Z_EYE - ptip[2])
        ter = max(2.0, rtip * k3 * sz * 1.5)
        tgx = max(-1.0, min(1.0, pdx)) * 0.85               # pupils track the player
        tips.append((tx, ty, ter, tgx, gate * emerge * (0.4 + 0.6 * threat),
                     int(235 * gate * emerge)))
    # painter's sort all limb flesh together, then the eyes on top
    quads.sort(key=lambda q: q[0])
    for _z, poly, col, al in quads:
        pygame.draw.polygon(lay, (*col, al), poly)
    for tx, ty, ter, tgx, openf, a in tips:
        _eye(lay, tx, ty, ter, openf, tgx, a)


def draw_king_unfold(surf, cx, cy, t, threat=0.0, scale=96.0,
                     to_player=(0.0, 1.0), birth=1.0, lean=(0.0, 0.0)):
    """THE UNFOLDING, centred at (cx, cy). `threat` 0..1: a small dark fold ->
    larger, faster eversion, the heart kindling, eyes opening, the Sign
    resolving, more light eaten.

    `to_player` is the SCREEN-space direction from the creature to the player
    (+x right, +y down); the reaching limbs lunge that way and the eyes gaze
    along it, so it tracks the player wherever they are. Defaults to
    down-screen.

    `lean` is the SCREEN-space travel direction (+x right, +y down) scaled by a
    0..1 locomotion magnitude -- the LOCOMOTION TELL. The mass everts FORWARD
    along it: the leading hemisphere surges ahead and swells while the trailing
    side tapers, so the clot lunges in its direction of travel instead of
    rigidly sliding to its next position. Zero = at rest (no surge).

    `birth` 0..1 is the ARRIVAL: a gold wound opens and leads, the dark mass
    blooms out of it, and the limbs come in last -- so 0->1 is the grace window
    (the thing is still assembling, not yet lethal). Driven 1->0 it plays in
    reverse as the DISSOLVE (the mass folds back into the wound and is gone)."""
    pdx, pdy = to_player
    pdl = math.hypot(pdx, pdy) or 1.0
    pdx, pdy = pdx / pdl, pdy / pdl
    bb = max(0.0, min(1.0, birth))
    body_b = bb * bb * (3.0 - 2.0 * bb)          # body blooms (smoothstep)
    form = _build()
    base_sz = scale * (0.7 + 0.5 * threat)
    sz = base_sz * body_b                        # the mass grows from the seed
    spd = 0.16 + 0.42 * threat
    body_ang = (t * spd * 0.55, t * spd * 0.43 + 1.3, t * spd * 0.27, t * spd * 0.17)
    # the heart turns faster and on different planes -> it everts WITHIN the body
    heart_ang = (t * spd * 1.15 + 0.7, t * spd * 0.9, t * spd * 0.5, t * spd * 0.3)

    o3 = _xform(form["overts"], body_ang, 0.05, t)
    c3 = _xform(form["cverts"], heart_ang, 0.0, t)

    # LOCOMOTION LEAN -- evert the mass forward in its travel direction. Map the
    # screen-space `lean` to the model frame (screen +x->+x, screen +y(down)->-y,
    # plus a push toward the camera so the surge reads as lunging forward, not
    # just sliding sideways). The leading hemisphere is shoved ahead and swells
    # (the everting bulge) while the trailing side is pulled back, so the whole
    # clot stretches into a forward surge that turns inside-out as it goes. Gated
    # by body_b so a half-born mass doesn't lunge.
    lx, ly = lean
    lmag = min(1.0, math.hypot(lx, ly)) * body_b
    if lmag > 0.01:
        dm = math.hypot(lx, ly) or 1.0
        Lm = _norm((lx / dm, -ly / dm, 0.55))    # unit travel dir, model frame
        amp = 0.46 * lmag
        oc0 = (sum(p[0] for p in o3) / len(o3),
               sum(p[1] for p in o3) / len(o3),
               sum(p[2] for p in o3) / len(o3))
        for i, p in enumerate(o3):
            rel = (p[0] - oc0[0], p[1] - oc0[1], p[2] - oc0[2])
            fwd = _dot(rel, Lm)                   # signed reach along travel
            if fwd >= 0.0:                        # leading hemisphere: swell out
                sw = 1.0 + 0.30 * amp * fwd
                rel = (rel[0] * sw, rel[1] * sw, rel[2] * sw)
            else:                                 # trailing tail: narrow it in
                al = (Lm[0] * fwd, Lm[1] * fwd, Lm[2] * fwd)
                pe = (rel[0] - al[0], rel[1] - al[1], rel[2] - al[2])
                nw = 1.0 - 0.5 * amp * (-fwd)
                rel = (al[0] + pe[0] * nw, al[1] + pe[1] * nw, al[2] + pe[2] * nw)
            o3[i] = (oc0[0] + rel[0] + Lm[0] * amp * fwd,
                     oc0[1] + rel[1] + Lm[1] * amp * fwd,
                     oc0[2] + rel[2] + Lm[2] * amp * fwd)
        # the molten heart leads the lunge -- it surges ahead inside the body
        hs = amp * 0.6
        c3 = [(p[0] + Lm[0] * hs, p[1] + Lm[1] * hs, p[2] + Lm[2] * hs)
              for p in c3]

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

    # BIRTH: a gold wound opens and the mass unfolds out of it -- a central
    # flare leads (peaking mid-eruption) while the dark body blooms up around
    # the seed. Run 1->0 this plays in reverse as the dissolve.
    if bb < 0.999:
        flare = max(0.0, math.sin(math.pi * min(1.0, bb / 0.85)))
        _heart_glow(lay, cx, cy, base_sz * (0.30 + 0.45 * bb),
                    int(60 + 170 * flare))

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

    # 2) the heart: glow + emissive everting shells, glimpsed through the flesh.
    # It is the creature's FOCAL CORE -- a pulsing molten centre the eye locks
    # onto, brightest at its heart so the dread has a centre of gravity.
    hc = (sum(p[0] for p in cp) / len(cp), sum(p[1] for p in cp) / len(cp))
    pulse = 0.82 + 0.18 * math.sin(t * 1.6)
    _heart_glow(lay, hc[0], hc[1], sz * 0.82, (80 + 165 * threat) * pulse)
    _heart_glow(lay, hc[0], hc[1], sz * 0.34, (70 + 130 * threat) * pulse)  # hot core
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
    _draw_arms(lay, o3, op, ocenter, sz, cx, cy, t, threat, form["arm_roots"],
               form["overts"], body_ang, zmin, zr, pdx, pdy, bb)

    # 5) EYES open across the skin -- wrong faces that surface and gaze, never
    # assembling into one. Each rides a facet, so it slides / scales / winks
    # with the eversion for free; threat opens more of them, wider.
    if threat > 0.12:
        appear = min(1.0, (threat - 0.12) / 0.5)
        fmap = {fi: (face, N) for zc, fi, face, N in front}
        for fi, ph in form["eye_sites"]:
            rec = fmap.get(fi)
            if rec is None:
                continue
            face, N = rec
            facing = max(0.0, N[2])                  # 1 head-on, 0 edge/back
            if facing < 0.14:
                continue
            poly = [op[i] for i in face]
            ex = sum(p[0] for p in poly) / len(poly)
            ey = sum(p[1] for p in poly) / len(poly)
            ar = 0.0
            for k in range(len(poly)):
                x0, y0 = poly[k]; x1, y1 = poly[(k + 1) % len(poly)]
                ar += x0 * y1 - x1 * y0
            er = math.sqrt(abs(ar)) * 0.26           # eye sized to the facet
            if er < 1.8:
                continue
            blink = 0.5 + 0.5 * math.sin(t * 0.7 + ph)
            openf = appear * facing * (0.35 + 0.65 * blink)
            gx = max(-1.0, min(1.0, pdx)) * 0.85             # pupils gaze at the player
            _eye(lay, ex, ey, er, openf, gx, int(235 * facing * appear))
        # MAWS tear open where the body everts -- scattered toothed throats that
        # gnash and breathe, riding their facets like the eyes. The eversion
        # turning inside-out IS the mouth: dark gullet, gold light down it.
        nlat = form["nlat"]; nlon = form["nlon"]
        for fi, ph in form["maw_sites"]:
            rec = fmap.get(fi)
            if rec is None:
                continue
            face, N = rec
            facing = max(0.0, N[2])
            if facing < 0.18:
                continue
            # the maw is BOUND to a patch of the mesh: sample(pu,pv) interpolates
            # the actual deformed verts over a few facets around this site, so
            # the rim warps with the region's live stretch / shear / curvature.
            i0 = fi // nlon
            j0 = fi % nlon
            R = 1.7                                  # patch half-size, in facets

            def sample(pu, pv, i0=i0, j0=j0, R=R):
                fi_ = (i0 + 0.5) + pu * R
                fj_ = (j0 + 0.5) + pv * R
                ii = int(math.floor(fi_)); jj = int(math.floor(fj_))
                ti = fi_ - ii; tj = fj_ - jj
                ia = max(0, min(nlat, ii)); ib = max(0, min(nlat, ii + 1))
                va = o3[ia * nlon + (jj % nlon)]; vb = o3[ia * nlon + ((jj + 1) % nlon)]
                vc = o3[ib * nlon + (jj % nlon)]; vd = o3[ib * nlon + ((jj + 1) % nlon)]
                return (va[0] + (vb[0] - va[0]) * tj + (vc[0] - va[0]) * ti +
                        (va[0] - vb[0] - vc[0] + vd[0]) * ti * tj,
                        va[1] + (vb[1] - va[1]) * tj + (vc[1] - va[1]) * ti +
                        (va[1] - vb[1] - vc[1] + vd[1]) * ti * tj,
                        va[2] + (vb[2] - va[2]) * tj + (vc[2] - va[2]) * ti +
                        (va[2] - vb[2] - vc[2] + vd[2]) * ti * tj)
            # world scale (mean facet edge) for throat depth + tooth length
            v0, v1, v3 = o3[face[0]], o3[face[1]], o3[face[3]]
            em = (math.dist(v0, v1) + math.dist(v0, v3)) * 0.5 * R
            breath = 0.5 + 0.5 * math.sin(t * 0.8 + ph * 1.7)
            openf = appear * facing * (0.22 + 0.78 * breath)
            _draw_maw3d(lay, sample, N, em, openf, cx, cy, sz, zmin, zr,
                        fi + int(ph * 7), int(235 * facing * appear))

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


# --------------------------------------------------------------------------- #
# THE CATCH -- the death. No flat face: one eversion-maw yawns wide and the
# camera goes DOWN THE THROAT. Rings of sharp teeth rush past in perspective
# toward the gold gullet (the LOD's full rows finally pay off), then the furnace
# floods to white. The most 4D death we can give it: the inside-out turn engulfs
# the player rather than resolving into a picture.
# --------------------------------------------------------------------------- #
def draw_unfold_catch(surf, t):
    """The catch, t 0..1: the maw opens and swallows the camera. Concentric
    rings of teeth scroll past in perspective down a dark throat toward the
    gold gullet, which swells and floods the screen white-gold."""
    W, H = surf.get_size()
    cx, cy = W * 0.5, H * 0.5
    surf.fill((5, 4, 6))

    def sstep(x):
        x = 0.0 if x < 0 else 1.0 if x > 1 else x
        return x * x * (3.0 - 2.0 * x)
    mouth = sstep(t / 0.20)                   # the maw irises open from shut
    opening = sstep(t / 0.26)                 # throat scales up
    dive = sstep((t - 0.20) / 0.66)           # plunge down the gullet
    flare = sstep((t - 0.82) / 0.18)          # the furnace floods

    base = max(W, H)
    lay = pygame.Surface((W, H), pygame.SRCALPHA)

    # a tunnel of tooth-rings receding to the gullet; they scroll OUTWARD past
    # the camera as we dive (near rings swell off-screen, new ones emerge deep)
    NR = 11
    phase = dive * NR * 1.6
    rings = []
    for i in range(NR):
        p = ((i - phase) % NR) / NR           # 0 = at the camera (near), ~1 = far
        depth = 0.14 + p * 1.25
        rad = (0.62 * base * (0.45 + 0.55 * opening)) / depth
        rings.append((depth, rad, p))
    rings.sort(reverse=True)                  # far first
    for depth, rad, p in rings:
        if rad < 5 or rad > base * 1.7:
            continue
        far_in = min(1.0, (1.0 - p) * 2.2 + 0.15)         # fade deep rings in
        near_out = (1.0 if rad < base * 0.85 else
                    max(0.0, 1.0 - (rad - base * 0.85) / (base * 0.6)))
        a = int(255 * near_out)
        if a < 8:
            continue
        bright = (0.25 + 0.75 * (1.0 - p)) * far_in        # darker toward the gullet
        nt = 18
        rot = depth * 5.3                                  # interleave the rings
        tlen = rad * (0.17 + 0.10 * math.sin(depth * 3.1))
        for k in range(nt):
            ang = math.tau * k / nt + rot
            dA = (math.tau / nt) * 0.40
            lv = 0.7 + 0.5 * (0.5 + 0.5 * math.sin(depth * 7.0 + k * 1.9))
            b0 = (cx + math.cos(ang - dA) * rad, cy + math.sin(ang - dA) * rad)
            b1 = (cx + math.cos(ang + dA) * rad, cy + math.sin(ang + dA) * rad)
            tipr = rad - tlen * lv
            tip = (cx + math.cos(ang) * tipr, cy + math.sin(ang) * tipr)
            shade = bright * (0.55 + 0.45 * math.sin(ang * 2 + depth))
            col = _ci(_cmix(_TOOTH_DK, _TOOTH, 0.16 + 0.84 * max(0.0, shade)))
            pygame.draw.polygon(lay, (*col, a), [b0, b1, tip])
    surf.blit(lay, (0, 0))

    # the throat closes dark around the edges -> we are inside it
    _eat_light(surf, cx, cy, base * 1.45, int(45 + 130 * opening))

    # the gold gullet at the end of the throat (drawn on the opaque surface so it
    # glows in the dark centre), swelling as we plunge toward it
    _heart_glow(surf, cx, cy, int(base * (0.10 + 0.22 * dive + 0.55 * flare)),
                int(110 + 150 * dive))

    # THE MOUTH OPENING: a foreground lip of big teeth that starts CLENCHED SHUT
    # (tips meeting at the centre, hiding the throat + gullet) and irises open to
    # a gape, then recedes as we plunge in. This is the beat that reads as a
    # mouth opening rather than starting mid-throat.
    lipf = 1.0 - dive                          # present at the start, gone inside
    if lipf > 0.02:
        lipR = base * 0.66
        nt = 22
        la = int(255 * min(1.0, lipf * 1.5))
        for k in range(nt):
            ang = math.tau * k / nt + 0.05 * math.sin(k * 1.7)
            dA = (math.tau / nt) * 0.46
            b0 = (cx + math.cos(ang - dA) * lipR, cy + math.sin(ang - dA) * lipR)
            b1 = (cx + math.cos(ang + dA) * lipR, cy + math.sin(ang + dA) * lipR)
            # tips retract from the centre (shut) out toward the rim (open)
            tipr = lipR * (0.03 + 0.93 * mouth) * (0.82 + 0.32 * math.sin(k * 1.9))
            tip = (cx + math.cos(ang) * tipr, cy + math.sin(ang) * tipr)
            shade = 0.45 + 0.4 * math.sin(ang * 2.0)
            col = _ci(_cmix(_TOOTH_DK, _TOOTH, 0.20 + 0.80 * shade))
            pygame.draw.polygon(surf, col, [b0, b1, tip])

    # the furnace floods from the gullet -> white-gold
    if flare > 0.0:
        r = int(base * (0.25 + 1.35 * flare))
        g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -max(1, r // 44)):
            f = 1 - i / r
            v = int(255 * (f ** 1.5) * flare)
            col = (255, min(255, 205 + int(50 * f)), int(110 + 145 * f))
            pygame.draw.circle(g, (*col, v), (r, r), i)
        surf.blit(g, (int(cx - r), int(cy - r)), special_flags=pygame.BLEND_RGBA_ADD)
