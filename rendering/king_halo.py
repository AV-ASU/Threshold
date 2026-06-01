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

# A SICKLY, jaundiced palette -- the Yellow is diseased, not holy. Most of the
# frame stays dark; the light barely escapes.
_SICK = (132, 110, 36)              # diseased amber (the core's body)
_SICK_DK = (58, 48, 16)             # its murk
_SICK_HI = (196, 172, 84)           # the most it brightens (rarely)
_SALLOW = (150, 145, 118)           # dingy, grave-pale porcelain (not clean bone)
_SALLOW_DK = (70, 66, 54)


def _stut(t, q=5.0, blend=0.62):
    """Stop-motion wrongness: bias time toward discrete steps so the swarm
    JERKS rather than glides -- it moves like something that doesn't quite
    obey time (Weeping-Angel / cosmic-wrong)."""
    return (1 - blend) * t + blend * (math.floor(t * q) / q)


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
        w = (0.34 if band == 0 else 0.24) * rng.uniform(0.9, 1.1)   # SLOW
        ph = rng.uniform(0, math.tau)
        prec = _norm3((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        out.append(dict(C0=C0, u=u, v=v, R=R, d=d, w=w, ph=ph, prec=prec,
                        axis=sh["axis"], spin=sh["spin"], verts=sh["verts"],
                        feat=sh["feat"], eye_thr=rng.uniform(0.45, 0.95),
                        crown_a=i * math.tau / len(shards)))
    _HALO = out
    return _HALO


_EYE_TH, _EYE_H = 0.62, 2.0


def _shard_screen(p, orbit, t, ts, iris, crown, cx, cy, yaw, bob, scale):
    """Project one shard. Returns (scr_pts, zc, front, eye_pts_or_None).
    `orbit` 0..1 lifts the shard from its home into its orbit; `iris` pulls the
    orbit radius IN; `crown` snaps it toward an even ring. `ts` is stuttered
    time (the wrong, jerking motion); `t` is smooth (the breath)."""
    # precessing in-plane basis (slow + stuttered)
    pa = 0.05 * ts
    u = _rodrigues(p["u"], p["prec"], pa)
    v = _rodrigues(p["v"], p["prec"], pa)
    breath = 1.0 + 0.07 * math.sin(t * 0.9)        # a slow tidal swell
    R = p["R"] * breath * (1.0 - 0.55 * iris)
    a = p["ph"] + p["d"] * p["w"] * ts
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
    tumble = orbit * p["spin"] * ts * 0.32
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
    # a sullen, diseased ember -- dim, sickly amber; it only brightens to a wan
    # gold at its very heart, and only when truly roused. Mostly dark.
    for i in range(steps, 0, -1):
        f = 1 - i / steps                            # 0 edge -> 1 centre
        al = int((30 + 26 * threat) * (f ** 2.6))    # dim: the dark keeps the upper hand
        if al <= 0:
            continue
        if i < Rc * 0.35 and threat > 0.75:
            col = _SICK_HI                           # a wan flicker, rarely
        elif i < Rc:
            col = _SICK
        else:
            col = _SICK_DK
        pygame.draw.circle(gl, (col[0], col[1], col[2], al), (g0, g0), i)
    # the Yellow Sign: three slow spokes that only barely resolve as he rouses
    if threat > 0.55:
        sa = int(46 * (threat - 0.55) / 0.45)
        for k in range(3):
            ang = t * 0.3 + k * math.tau / 3
            x2 = g0 + math.cos(ang) * Rc * 2.0
            y2 = g0 + math.sin(ang) * Rc * 2.0
            pygame.draw.line(gl, (_SICK[0], _SICK[1], _SICK[2], sa),
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
        rad = (3 + 5 * (fi % 3)) * scale * 0.5
        ang = t * (0.18 + 0.06 * fi) + seed                   # slow drift
        fx = cx + math.cos(ang) * rad
        fy = cy + math.sin(ang * 1.3 + seed) * rad * 0.7
        fs = (5.0 + 2.0 * math.sin(t * 0.5 + seed)) * scale * 0.5
        # most of the time SUNK (invisible); each rises briefly, half-glimpsed
        surfacing = max(0.0, math.sin(t * 0.5 + seed * 2)) ** 2
        a = int((70 * surfacing) * min(1.0, 0.25 + threat))   # dim: barely there
        if a < 6:
            continue
        tr = _FACE_TRAILS[fi]
        tr.append((fx, fy, fs, a))
        if len(tr) > 6:
            del tr[0]
        # the smear: older ghosts first, fading
        for gi, (gx, gy, gs, ga) in enumerate(tr):
            ghost = int(ga * (gi + 1) / len(tr) * 0.5)
            if ghost < 5:
                continue
            _one_face(surf, gx, gy, gs * (0.7 + 0.3 * (gi + 1) / len(tr)),
                      ghost, gaze if crown < 0.5 else 1.0, crown)


def _one_face(surf, x, y, s, a, gaze, crown):
    """A pale, sallow visage half-risen in the murk -- NOT a glowing blob. Drawn
    with a normal blend so it sits in the light rather than blowing it out, with
    only a faint sick rim catching the core."""
    w = int(s * 1.2); h = int(s * 1.7)
    if w < 2 or h < 2:
        return
    fc = pygame.Surface((w * 2 + 2, h * 2 + 2), pygame.SRCALPHA)
    cx2, cy2 = w + 1, h + 1
    # the face itself: dingy sallow flesh, low alpha (sits IN the light)
    pygame.draw.ellipse(fc, (_SALLOW[0], _SALLOW[1], _SALLOW[2], a),
                        (cx2 - w, cy2 - h, w * 2, h * 2))
    # gaunt cheek shadow so it reads as a face, not an egg
    pygame.draw.ellipse(fc, (_SALLOW_DK[0], _SALLOW_DK[1], _SALLOW_DK[2], int(a * 0.6)),
                        (cx2 - int(w * 0.55), cy2 - int(h * 0.2),
                         int(w * 1.1), int(h * 1.0)))
    # two deep hollow eyes (clear + dark) -- the read of a face
    ex = int(w * 0.45); ey = int(h * 0.22)
    gx = int(gaze * w * 0.16)
    for sgn in (-1, 1):
        pygame.draw.ellipse(fc, (_HOLLOW[0], _HOLLOW[1], _HOLLOW[2], min(255, a + 60)),
                            (cx2 + sgn * ex - int(w * 0.3) + gx, cy2 - ey - int(h * 0.18),
                             int(w * 0.6), int(h * 0.4)))
    # a thin mouth, opening to a maw on the crown beat
    mw = int(w * (0.25 + 0.6 * crown))
    pygame.draw.line(fc, (_HOLLOW[0], _HOLLOW[1], _HOLLOW[2], min(255, a + 40)),
                     (cx2 - mw, cy2 + int(h * 0.5)), (cx2 + mw, cy2 + int(h * 0.5)),
                     max(1, int(s * (0.15 + 0.3 * crown))))
    surf.blit(fc, (int(x - cx2), int(y - cy2)))      # NORMAL blend: in the murk
    # a faint sick rim-light catching the core, added subtly
    rim = pygame.Surface((w * 2 + 2, h * 2 + 2), pygame.SRCALPHA)
    pygame.draw.ellipse(rim, (_SICK[0], _SICK[1], _SICK[2], int(a * 0.4)),
                        (cx2 - w, cy2 - h, w * 2, h * 2), max(1, int(s * 0.12)))
    surf.blit(rim, (int(x - cx2), int(y - cy2)), special_flags=pygame.BLEND_RGBA_ADD)


def draw_king_halo(surf, cx, cy, yaw, t, threat=0.0, scale=3.0, beat=0.0):
    """Draw the halo King centred at (cx, cy). `threat` 0..1 drives the whole
    arc (calm mask -> orbiting halo -> iris); `beat` 0..1 fires the crown snap.
    `yaw` turns the swarm (the mask faces the player; camera.yaw gives view)."""
    ts = _stut(t)                                    # the jerking, wrong time
    bob = math.sin(t * 0.7) * 1.0                    # a slow, heavy sway
    breath = 1.0 + 0.07 * math.sin(t * 0.9)
    # arc mapping
    orbit = max(0.0, min(1.0, (threat - 0.32) / 0.45))
    orbit = orbit * orbit * (3 - 2 * orbit)
    iris = max(0.0, min(1.0, (threat - 0.82) / 0.18))
    crown = max(0.0, min(1.0, beat))
    # how many shards have opened an EXTRA eye (too many eyes)
    params = _halo_params()
    for p in params:
        p["_extra_eye"] = (p["feat"]["eye"] is None and threat > p["eye_thr"])
    # the gaze HOLDS, drifting slowly, with rare flicks -- then locks on the
    # beat. Not a constant scan (that read as mechanical).
    drift = math.sin(t * 0.33) * 0.5
    flick = 0.5 if (math.floor(t * 0.7) % 5 == 0) else 0.0
    gaze = (drift + flick) * (1 - crown) + crown

    # project every shard, split by depth around the core (z=0)
    items = []
    for p in params:
        r = _shard_screen(p, orbit, t, ts, iris, crown, cx, cy, yaw, bob, scale)
        if r is not None:
            items.append((p, r))
    behind = [(p, r) for (p, r) in items if r[1] < 0]
    front = [(p, r) for (p, r) in items if r[1] >= 0]
    behind.sort(key=lambda it: it[1][1])
    front.sort(key=lambda it: it[1][1])

    # 1) BEHIND shards: near-black backlit silhouettes, the faintest sick rim
    for p, (scr, zc, fr, eye) in behind:
        pygame.draw.polygon(surf, _VOIDC, scr)
        pygame.draw.polygon(surf, _shade(_SICK_DK, 0.5 + 0.5 * threat), scr, 1)

    # 2) the breathing core + the Sign corona
    _core_glow(surf, cx, cy - bob * scale, t, threat, scale, breath)

    # 3) faces surfacing in the light (with trails)
    _draw_faces(surf, cx, cy - bob * scale, t, threat, scale, gaze, crown)

    # 4) FRONT shards on a layer so the eye holes punch THROUGH to the core
    porc = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    holes, pupils = [], []
    for p, (scr, zc, fr, eye) in front:
        # dingy, grave-pale porcelain -- depth-dimmed and kept murky (never
        # clean white); the front pieces catch only a little wan light.
        f = 0.46 + 0.30 * max(0.0, min(1.0, (zc + 6) / 12.0))
        if not fr:
            pygame.draw.polygon(porc, _VOIDC, scr)
            pygame.draw.polygon(porc, _shade(_SICK_DK, 0.5 + 0.5 * threat), scr, 1)
            continue
        pygame.draw.polygon(porc, _shade(_SALLOW, f), scr)
        pygame.draw.polygon(porc, _SALLOW_DK, scr, 1)
        if eye is not None and len(eye) >= 3:
            holes.append(eye)
            ex = sum(q[0] for q in eye) / len(eye)
            ey = sum(q[1] for q in eye) / len(eye)
            pupils.append((ex, ey))
    for eye in holes:
        pygame.draw.polygon(porc, (0, 0, 0, 0), eye)            # PUNCH the eye
    surf.blit(porc, (0, 0))

    # 5) the watching: each eye holds a wet, sick-gold pupil that HOLDS the
    # player (drifts slowly, locks on the beat) with a cold gleam -- the dread
    # of being seen. A rare slow blink dims them all for a beat.
    blink = 1.0
    bz = (t * 0.5) % 7.0
    if bz < 0.18:
        blink = abs(bz - 0.09) / 0.09                # a slow shared blink
    gx = gaze * scale * 0.7
    for (ex, ey) in pupils:
        pr = max(1, int((0.9 + 0.7 * threat) * scale * 0.5))
        if blink < 0.5:
            continue
        col = _shade(_SICK if threat > 0.4 else _SICK_DK, blink)
        pygame.draw.circle(surf, col, (int(ex + gx), int(ey + scale * 0.35)), pr)
        # a single cold wet gleam, offset -- it makes the eye read as watching
        if threat > 0.45 and blink > 0.7:
            pygame.draw.circle(surf, _shade(_SICK_HI, blink),
                               (int(ex + gx - pr * 0.4), int(ey + scale * 0.15)),
                               max(1, pr // 3))

    # 6) the crown-beat INVERSION FLASH: a true one-frame photo-negative
    # (255 - colour) at the very peak -- porcelain goes black, the Yellow goes
    # cold. Gated narrow so it's a jolt, not a fade.
    if crown > 0.86:
        neg = pygame.Surface(surf.get_size())
        neg.fill((255, 255, 255))
        neg.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_SUB)   # 255 - surf
        neg.set_alpha(int(255 * (crown - 0.86) / 0.14))
        surf.blit(neg, (0, 0))
