"""THE KING IN YELLOW -- the HALO / orbit redesign PROTOTYPE (CAMERA.md tier 3+).

An exploration past `king3d.py`'s explode-shatter: the Pallid Mask was only ever
a shell over the light, so when he ROUSES the face peels apart and the shards
reorganize into a COUNTER-ROTATING HALO orbiting the exposed Yellow core -- a
crown of broken porcelain around a sun. Not a face anymore: the thing the face
was hiding.

Isolated + previewable (`tools/preview_king_halo.py`); NOT wired into the live
game. Reuses the volumetric machinery from `king3d.py` (the ovoid surface, the
convex-cell fracture, the inner-face flip) and layers the agreed eldritch arc:

  * HYBRID arc, threat-driven: far = serene whole mask -> approach = crack +
    seep -> roused = mask lifts into the orbiting halo -> lethal = the orbit
    irises in -> CROWN BEAT (snap + inversion flash + the keyhole).
  * COUNTER-ROTATION + PRECESSION: two concentric bands spin opposite ways and
    their orbital planes slowly tilt.
  * TOO MANY EYES: more shards open an eye-hole as threat climbs; their gold
    pupils scan, then all snap to the player at the crown beat (gaze-lock).
  * FACES IN THE LIGHT: pallid faces surface + sink inside the core, smearing
    motion trails (high-priority -- the cult's fused faces).
  * BREATHING: the core + halo radius pulse (tidal when far, panting when near).
  * The CROWN BEAT: shards snap to an even ring/Sign, a one-frame photo-negative
    inversion, and the keyhole -- the halo blows past its bounds for a breath
    (handled screen-space by the caller; here we just scale up on `beat`).
"""
import math
import random
import pygame

from rendering.king3d import (_surface, _build_shards, _shade, _norm3,
                              _rodrigues, _PORC, _PORC_DK, _PORC_HI, _HOLLOW,
                              _VOIDC, _GOLD, _GOLD_DK, _GOLD_HI)

_HALO = None
_FACE_TRAILS = None         # per-face screen-position history (the smear)
_HALO_RNG = random.Random(91)


def reset_king_halo_fx():
    global _FACE_TRAILS
    _FACE_TRAILS = None


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _yawrot(p, yaw):
    """Rotate a 3D point about the vertical axis by yaw (the camera view)."""
    c, s = math.cos(yaw), math.sin(yaw)
    return (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)


def _halo_params():
    """Per-shard orbit data, cached. Two concentric COUNTER-ROTATING bands
    (inner band one way, outer the other), planes clustered toward the camera
    so the swarm reads as a crown/halo around the core, each plane precessing."""
    global _HALO
    if _HALO is not None:
        return _HALO
    rng = random.Random(91)
    shards = _build_shards()
    out = []
    for i, sh in enumerate(shards):
        crx, _h, crz = _surface(sh["tc"], sh["hc"], 0.0)
        C0 = (crx, sh["hc"], crz)                     # home (assembled) centroid
        n = _norm3((rng.uniform(-0.55, 0.55), rng.uniform(-0.55, 0.55),
                    rng.uniform(0.45, 1.0)))          # plane normal ~ toward cam
        tmp = (0.0, 1.0, 0.0) if abs(n[1]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm3(_cross(n, tmp))
        v = _norm3(_cross(n, u))
        band = i % 2                                  # 0 inner, 1 outer
        R = (22.0 if band == 0 else 33.0) + rng.uniform(-2.0, 2.0)
        d = 1.0 if band == 0 else -1.0                # counter-rotation
        w = (0.85 if band == 0 else 0.62) * rng.uniform(0.9, 1.1)
        ph = rng.uniform(0, math.tau)
        prec = _norm3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        out.append(dict(C0=C0, u=u, v=v, R=R, d=d, w=w, ph=ph, prec=prec,
                        axis=sh["axis"], spin=sh["spin"], verts=sh["verts"],
                        feat=sh["feat"], eye_thr=rng.uniform(0.45, 0.95),
                        crown_a=i * math.tau / len(shards)))
    _HALO = out
    return _HALO


_EYE_TH, _EYE_H = 0.62, 2.0


def _shard_screen(p, orbit, t, iris, crown, cx, cy, yaw, bob, scale):
    """Project one shard. Returns (scr_pts, zc, front, eye_pts_or_None).
    `orbit` 0..1 lifts the shard from its home into its orbit; `iris` pulls the
    orbit radius IN; `crown` snaps it toward an even ring."""
    # precessing in-plane basis
    pa = 0.18 * t
    u = _rodrigues(p["u"], p["prec"], pa)
    v = _rodrigues(p["v"], p["prec"], pa)
    breath = 1.0 + 0.10 * math.sin(t * 1.3)
    R = p["R"] * breath * (1.0 - 0.55 * iris)
    a = p["ph"] + p["d"] * p["w"] * t
    if crown > 0:                                    # snap toward an even ring
        a = a * (1 - crown) + p["crown_a"] * crown
        R = R * (1 - crown) + 16.0 * crown
    O = (R * (math.cos(a) * u[0] + math.sin(a) * v[0]),
         R * (math.cos(a) * u[1] + math.sin(a) * v[1]),
         R * (math.cos(a) * u[2] + math.sin(a) * v[2]))
    C0 = p["C0"]
    cen = (C0[0] + (O[0] - C0[0]) * orbit,
           C0[1] + (O[1] - C0[1]) * orbit,
           C0[2] + (O[2] - C0[2]) * orbit)
    tumble = orbit * p["spin"] * t * 0.6
    scr, zs = [], []
    for (th, hh) in p["verts"]:
        rx, _hh, rz = _surface(th, hh, 0.0)
        rel = _rodrigues((rx - C0[0], hh - C0[1], rz - C0[2]), p["axis"], tumble)
        wp = (cen[0] + rel[0], cen[1] + rel[1], cen[2] + rel[2])
        wp = _yawrot(wp, yaw)
        scr.append((cx + wp[0] * scale, cy - (wp[1] + bob) * scale))
        zs.append(wp[2])
    if len(scr) < 3:
        return None
    zc = sum(zs) / len(zs)
    area = 0.0
    for k in range(len(scr)):
        x0, y0 = scr[k]; x1, y1 = scr[(k + 1) % len(scr)]
        area += x0 * y1 - x1 * y0
    front = area < 0
    # the eye hole (this shard owns one, or opens an extra at high threat)
    eye_pts = None
    if p["feat"]["eye"] is not None or p.get("_extra_eye"):
        sgn = p["feat"]["eye"] if p["feat"]["eye"] is not None else 1
        rim = []
        for k in range(12):
            ea = math.tau * k / 12
            th = sgn * _EYE_TH + math.cos(ea) * 0.30
            hh = _EYE_H + math.sin(ea) * 3.4
            rx, _hh, rz = _surface(th, hh, 0.0)
            rel = _rodrigues((rx - C0[0], hh - C0[1], rz - C0[2]), p["axis"], tumble)
            wp = _yawrot((cen[0] + rel[0], cen[1] + rel[1], cen[2] + rel[2]), yaw)
            rim.append((cx + wp[0] * scale, cy - (wp[1] + bob) * scale))
        eye_pts = rim
    return scr, zc, front, eye_pts


def _core_glow(surf, cx, cy, t, threat, scale, breath):
    """The Yellow core: a CONTAINED breathing bloom (bright tight centre, soft
    halo) the shards orbit AROUND -- never a flat disc -- + a faint rotating
    Sign corona that only resolves as he rouses."""
    Rc = (2.0 + 3.0 * threat) * scale * breath       # bright core radius
    Rmax = Rc * 2.2                                  # soft halo reach (< inner ring)
    g0 = int(Rmax) + 1
    gl = pygame.Surface((g0 * 2 + 2, g0 * 2 + 2), pygame.SRCALPHA)
    steps = max(4, int(Rmax))
    for i in range(steps, 0, -1):
        f = 1 - i / steps                            # 0 edge -> 1 centre
        al = int(70 * (f ** 2.2))                    # low per-ring -> soft gradient
        if al <= 0:
            continue
        col = _GOLD_HI if i < Rc * 0.5 else (_GOLD if i < Rc else _GOLD_DK)
        pygame.draw.circle(gl, (col[0], col[1], col[2], al), (g0, g0), i)
    # the Yellow Sign: three slow spokes that only resolve as he rouses
    if threat > 0.45:
        sa = int(90 * (threat - 0.45) / 0.55)
        for k in range(3):
            ang = t * 0.5 + k * math.tau / 3
            x2 = g0 + math.cos(ang) * Rc * 2.2
            y2 = g0 + math.sin(ang) * Rc * 2.2
            pygame.draw.line(gl, (_GOLD_HI[0], _GOLD_HI[1], _GOLD_HI[2], sa),
                             (g0, g0), (x2, y2), 2)
    surf.blit(gl, (int(cx - g0), int(cy - g0)), special_flags=pygame.BLEND_RGBA_ADD)


def _draw_faces(surf, cx, cy, t, threat, scale, gaze, crown):
    """Pallid faces surface + sink inside the core, smearing motion trails --
    the cult's fused faces. They drift on little orbits; alpha breathes them in
    and out; at the crown beat their gazes snap forward (gaze-lock)."""
    global _FACE_TRAILS
    nf = 5
    if _FACE_TRAILS is None or len(_FACE_TRAILS) != nf:
        _FACE_TRAILS = [[] for _ in range(nf)]
    for fi in range(nf):
        seed = fi * 1.7
        rad = (4 + 6 * (fi % 3)) * scale * 0.5
        ang = t * (0.6 + 0.2 * fi) + seed
        fx = cx + math.cos(ang) * rad
        fy = cy + math.sin(ang * 1.3 + seed) * rad * 0.7
        fs = (5.5 + 2.0 * math.sin(t + seed)) * scale * 0.5    # face half-height
        surfacing = 0.5 + 0.5 * math.sin(t * 0.9 + seed * 2)   # sink/rise
        a = int((40 + 150 * surfacing) * min(1.0, 0.3 + threat))
        tr = _FACE_TRAILS[fi]
        tr.append((fx, fy, fs, a))
        if len(tr) > 7:
            del tr[0]
        # the smear: older ghosts first, fading
        for gi, (gx, gy, gs, ga) in enumerate(tr):
            ghost = int(ga * (gi + 1) / len(tr) * 0.6)
            if ghost < 8:
                continue
            _one_face(surf, gx, gy, gs * (0.7 + 0.3 * (gi + 1) / len(tr)),
                      ghost, gaze if crown < 0.5 else 1.0, crown)


def _one_face(surf, x, y, s, a, gaze, crown):
    w = int(s * 1.3); h = int(s * 1.8)
    if w < 2 or h < 2:
        return
    fc = pygame.Surface((w * 2 + 2, h * 2 + 2), pygame.SRCALPHA)
    cx2, cy2 = w + 1, h + 1
    pygame.draw.ellipse(fc, (_GOLD_HI[0], _GOLD_HI[1], _GOLD_HI[2], a),
                        (cx2 - w, cy2 - h, w * 2, h * 2))
    pygame.draw.ellipse(fc, (_PORC[0], _PORC[1], _PORC[2], int(a * 0.7)),
                        (cx2 - int(w * 0.8), cy2 - int(h * 0.8),
                         int(w * 1.6), int(h * 1.6)))
    # two void eyes; gaze nudges the dark pupil toward the player (down/centre)
    ex = int(w * 0.42); ey = int(h * 0.18)
    gx = int(gaze * w * 0.18)
    for sgn in (-1, 1):
        pygame.draw.ellipse(fc, (_HOLLOW[0], _HOLLOW[1], _HOLLOW[2], a),
                            (cx2 + sgn * ex - int(w * 0.28), cy2 - ey - int(h * 0.16),
                             int(w * 0.55), int(h * 0.34)))
    # a thin downturned slit when the crown beat opens the maw
    if crown > 0.3:
        mw = int(w * (0.4 + 0.5 * crown))
        pygame.draw.line(fc, (_HOLLOW[0], _HOLLOW[1], _HOLLOW[2], a),
                         (cx2 - mw, cy2 + int(h * 0.55)), (cx2 + mw, cy2 + int(h * 0.55)),
                         max(1, int(s * 0.2)))
    surf.blit(fc, (int(x - cx2), int(y - cy2)), special_flags=pygame.BLEND_RGBA_ADD)


def draw_king_halo(surf, cx, cy, yaw, t, threat=0.0, scale=3.0, beat=0.0):
    """Draw the halo King centred at (cx, cy). `threat` 0..1 drives the whole
    arc (calm mask -> orbiting halo -> iris); `beat` 0..1 fires the crown snap.
    `yaw` turns the swarm (the mask faces the player; camera.yaw gives view)."""
    bob = math.sin(t * 1.1) * 1.2
    breath = 1.0 + 0.10 * math.sin(t * 1.3)
    # arc mapping
    orbit = max(0.0, min(1.0, (threat - 0.32) / 0.45))
    orbit = orbit * orbit * (3 - 2 * orbit)
    iris = max(0.0, min(1.0, (threat - 0.82) / 0.18))
    crown = max(0.0, min(1.0, beat))
    # how many shards have opened an EXTRA eye (too many eyes)
    params = _halo_params()
    for p in params:
        p["_extra_eye"] = (p["feat"]["eye"] is None and threat > p["eye_thr"])
    gaze = math.sin(t * 0.7) * (1 - crown) + crown   # scan, then snap forward

    # project every shard, split by depth around the core (z=0)
    items = []
    for p in params:
        r = _shard_screen(p, orbit, t, iris, crown, cx, cy, yaw, bob, scale)
        if r is not None:
            items.append((p, r))
    behind = [(p, r) for (p, r) in items if r[1] < 0]
    front = [(p, r) for (p, r) in items if r[1] >= 0]
    behind.sort(key=lambda it: it[1][1])
    front.sort(key=lambda it: it[1][1])

    # 1) BEHIND shards: backlit silhouettes / dark inner faces
    for p, (scr, zc, fr, eye) in behind:
        pygame.draw.polygon(surf, _VOIDC, scr)
        pygame.draw.polygon(surf, _shade(_GOLD_DK, 0.4 + 0.6 * threat), scr, 1)

    # 2) the breathing core + the Sign corona
    _core_glow(surf, cx, cy - bob * scale, t, threat, scale, breath)

    # 3) faces surfacing in the light (with trails)
    _draw_faces(surf, cx, cy - bob * scale, t, threat, scale, gaze, crown)

    # 4) FRONT shards on a layer so the eye holes punch THROUGH to the core
    porc = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    holes, pupils = [], []
    for p, (scr, zc, fr, eye) in front:
        f = 0.74 + 0.26 * max(0.0, min(1.0, (zc + 6) / 12.0))
        if not fr:
            pygame.draw.polygon(porc, _VOIDC, scr)
            pygame.draw.polygon(porc, _shade(_GOLD_DK, 0.4 + 0.6 * threat), scr, 1)
            continue
        pygame.draw.polygon(porc, _shade(_PORC, f), scr)
        pygame.draw.polygon(porc, _PORC_DK, scr, 1)
        if eye is not None and len(eye) >= 3:
            holes.append(eye)
            ex = sum(q[0] for q in eye) / len(eye)
            ey = sum(q[1] for q in eye) / len(eye)
            pupils.append((ex, ey))
    for eye in holes:
        pygame.draw.polygon(porc, (0, 0, 0, 0), eye)            # PUNCH the eye
    surf.blit(porc, (0, 0))

    # 5) the eyes' gold pupils -- they scan, then GAZE-LOCK forward on the beat
    for (ex, ey) in pupils:
        pr = max(1, int((0.7 + 0.5 * threat) * scale * 0.5))
        gx = gaze * scale * 0.6
        pygame.draw.circle(surf, _GOLD if threat > 0.4 else _GOLD_DK,
                           (int(ex + gx), int(ey + scale * 0.4)), pr)

    # 6) the crown-beat INVERSION FLASH: a true one-frame photo-negative
    # (255 - colour) at the very peak -- porcelain goes black, the Yellow goes
    # cold. Gated narrow so it's a jolt, not a fade.
    if crown > 0.86:
        neg = pygame.Surface(surf.get_size())
        neg.fill((255, 255, 255))
        neg.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_SUB)   # 255 - surf
        neg.set_alpha(int(255 * (crown - 0.86) / 0.14))
        surf.blit(neg, (0, 0))
