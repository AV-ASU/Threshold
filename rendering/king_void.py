"""THE PALLID HOLE -- a fear-first King prototype (NOT wired into the live game).

The thesis (see the chat design discussion): the King should be the DARKEST
thing on screen, not the brightest. A too-tall, too-thin human silhouette in the
King's tattered robe, rendered as a VOID that *eats* the light around it. Almost
no gold -- gold is the RECOGNITION TRIGGER, a wet gleam that only wakes in the
eyes (and bleeds the Yellow Sign) once he has LOCKED onto you. In his body the
faces of the dead surface and sink, half-seen, mouths open -- the cult's fused
faces done as dread, not decoration. He is mostly STILL; he moves in stop-motion
lurches. One or two human-but-too-long arms reach only when he is almost on you.

The gold halo / shatter / eye-eruption we built (rendering/king_halo.py) is NOT
the idle pursuer -- it is the CATCH: the mask splits and the Carcosa furnace
pours out as the death blooms. This file is only the stalking dread.

Preview:  python tools/preview_king_void.py
"""
import math
import random

import pygame

from rendering.king3d import _shade

# --- palette: near-black void, dead bone, ONE waking gold ------------------
_VOID = (5, 5, 8)                    # the body: a hole, just off pure black
_VOID2 = (10, 10, 14)               # a hair lighter, for inner forms
_RIM = (44, 48, 62)                 # cold, desaturated edge light (moonless blue-grey)
_BONE = (138, 136, 124)             # the pallid mask -- grave-pale, never white
_BONE_DK = (58, 58, 52)
_BONE_HI = (176, 174, 160)
_DROWN = (96, 98, 104)              # the drowning faces: dim, cold, half-seen
_DROWN_DK = (26, 28, 32)
_GOLD = (208, 170, 64)              # the wake-up: used at <5% coverage, ever
_GOLD_DK = (120, 98, 38)
_GOLD_HI = (238, 212, 120)

_RNG = random.Random(7)
_FORM = None                        # cached body proportions (seeded, asymmetric)


def reset_king_void_fx():
    global _FORM
    _FORM = None


def _qt(t, q=5.0):
    """Stop-motion time: he exists in jerks, not glides."""
    return math.floor(t * q) / q


def _form():
    """Seeded, deliberately ASYMMETRIC proportions -- wrongness lives here: one
    shoulder higher, the head tilted and set a touch off the spine."""
    global _FORM
    if _FORM is not None:
        return _FORM
    r = random.Random(31)
    _FORM = {
        "head_tilt": r.uniform(-0.10, 0.10) - 0.06,
        "head_dx": r.uniform(-0.04, 0.04),
        "sh_l": r.uniform(0.93, 1.0),          # left shoulder height factor
        "sh_r": r.uniform(0.86, 0.97),         # right a touch dropped
        "lean": r.uniform(-0.03, 0.03),
        "hem": [r.uniform(0.0, 1.0) for _ in range(13)],   # frayed-hem noise
        "faces": [(r.uniform(-0.5, 0.5), r.uniform(0.0, 1.0), r.uniform(0, 6.28),
                   r.uniform(0.7, 1.3)) for _ in range(5)],
    }
    return _FORM


def _eat_light(surf, cx, cy, r, strength):
    """Subtractively darken the scene around him -- the light dies as it nears.
    This is what makes him read as a HOLE rather than a sprite."""
    r = int(r)
    if r < 2:
        return
    d = r * 2
    a = pygame.Surface((d, d))
    c = r
    steps = max(6, r // 2)
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        f = 1 - i / steps
        v = int(strength * (f ** 2.3))
        if v > 0:
            pygame.draw.circle(a, (v, v, v), (c, c), rr)
    surf.blit(a, (int(cx - c), int(cy - c)), special_flags=pygame.BLEND_RGB_SUB)


def _body_polys(cx, cy, H, t, threat):
    """Build the void silhouette: a too-tall robed figure. Returns the robe
    polygon, the head ellipse rect, shoulder anchors, and the robe's x-half at a
    given y (for clipping the drowning faces)."""
    F = _form()
    qt = _qt(t)
    # mostly still; a slow heavy sway + a tiny stop-motion jitter (he LURCHES)
    sway = math.sin(qt * 0.5) * H * 0.012
    jit = (random.Random(int(qt * 60)).uniform(-1, 1)) * H * 0.006 * (0.3 + threat)
    ax = cx + sway + jit + F["lean"] * H
    head_y = cy - H * 0.50
    head_r = H * 0.082
    head_cx = ax + F["head_dx"] * H
    sh_y = head_y + head_r * 2.0
    sh_half = H * 0.112
    hem_y = cy + H * 0.50
    hem_half = H * 0.150
    mid_y = (sh_y + hem_y) * 0.5
    # left side down, then the frayed hem L->R, then right side up
    left = [(ax - sh_half * F["sh_l"], sh_y),
            (ax - sh_half * 1.04, mid_y - H * 0.02),
            (ax - hem_half, hem_y - H * 0.03)]
    right = [(ax + hem_half, hem_y - H * 0.03),
             (ax + sh_half * 1.0, mid_y + H * 0.01),
             (ax + sh_half * F["sh_r"], sh_y)]
    # frayed hem: tatters dripping into smoke, seeded + a slow drift
    hem = []
    n = len(F["hem"])
    for i in range(n):
        fx = ax - hem_half + (2 * hem_half) * (i / (n - 1))
        drip = (0.4 + F["hem"][i]) * H * 0.06
        drip *= 0.7 + 0.5 * math.sin(qt * 0.8 + i)
        hem.append((fx, hem_y - H * 0.03 + drip))
    robe = left + hem + right
    return {"robe": robe, "head": (head_cx, head_y, head_r),
            "sh_l": (ax - sh_half * F["sh_l"], sh_y),
            "sh_r": (ax + sh_half * F["sh_r"], sh_y),
            "ax": ax, "sh_y": sh_y, "hem_y": hem_y,
            "sh_half": sh_half, "hem_half": hem_half}


def _drown_face(surf, x, y, s, a):
    """A dim, cold face surfacing in him -- the dead, mouths open in a silence.
    Half-seen: never bright, never gold. The horror is that he is full of people."""
    w = int(s * 0.9); h = int(s * 1.15)
    if w < 2 or h < 2 or a < 6:
        return
    fc = pygame.Surface((w * 2 + 2, h * 2 + 2), pygame.SRCALPHA)
    cx2, cy2 = w + 1, h + 1
    pygame.draw.ellipse(fc, (_DROWN[0], _DROWN[1], _DROWN[2], a),
                        (cx2 - w, cy2 - h, w * 2, h * 2))
    # two sunken dark eyes
    ex, ey = int(w * 0.42), int(h * 0.18)
    for sgn in (-1, 1):
        pygame.draw.ellipse(fc, (_DROWN_DK[0], _DROWN_DK[1], _DROWN_DK[2], min(255, a + 70)),
                            (cx2 + sgn * ex - int(w * 0.26), cy2 - ey - int(h * 0.12),
                             int(w * 0.52), int(h * 0.36)))
    # the open mouth -- a vertical maw, the soundless scream
    pygame.draw.ellipse(fc, (_DROWN_DK[0], _DROWN_DK[1], _DROWN_DK[2], min(255, a + 80)),
                        (cx2 - int(w * 0.16), cy2 + int(h * 0.12),
                         int(w * 0.32), int(h * 0.58)))
    surf.blit(fc, (int(x - cx2), int(y - cy2)))


def _draw_drowning(surf, B, H, t, threat):
    """Faces rising + sinking through the robe surface, clipped to his body."""
    F = _form()
    ax, sh_y, hem_y = B["ax"], B["sh_y"], B["hem_y"]
    span = hem_y - sh_y
    for (fx, fy, ph, sz) in F["faces"]:
        # surfacing breath: mostly submerged, each rises briefly then sinks
        surf_amt = max(0.0, math.sin(t * 0.45 + ph)) ** 2.4
        a = int(120 * surf_amt * min(1.0, 0.18 + threat))   # held back when dormant
        if a < 6:
            continue
        y = sh_y + span * (0.18 + 0.7 * fy) - surf_amt * H * 0.02
        # keep inside the robe: x-half tapers from shoulders to hem
        fr = (y - sh_y) / max(1.0, span)
        half = B["sh_half"] * (1 - fr) + B["hem_half"] * fr
        x = ax + fx * half * 0.8
        _drown_face(surf, x, y, H * 0.085 * sz, a)


def _mask(surf, hx, hy, hr, t, threat, lock):
    """The pallid mask: a CALM human face, too calm. Bone, not white. Two hollow
    eyes. The only gold in the whole figure is the wet gleam that wakes in those
    eyes -- and the Yellow Sign bleeding on the brow -- once he LOCKS (lock 0..1)."""
    F = _form()
    tilt = F["head_tilt"]
    w = int(hr * 0.92); h = int(hr * 1.18)
    d = max(w, h) * 2 + 6
    fc = pygame.Surface((d, d), pygame.SRCALPHA)
    c = d // 2
    # the bone face, faintly catching the cold rim (NOT glowing)
    pygame.draw.ellipse(fc, _BONE_DK, (c - w, c - h, w * 2, h * 2))
    pygame.draw.ellipse(fc, _shade(_BONE, 0.82),
                        (c - int(w * 0.92), c - int(h * 0.95),
                         int(w * 1.84), int(h * 1.9)))
    # gaunt cheek hollows so it reads as a skull-close face, not an egg
    for sgn in (-1, 1):
        pygame.draw.ellipse(fc, (_BONE_DK[0], _BONE_DK[1], _BONE_DK[2], 150),
                            (c + sgn * int(w * 0.5) - int(w * 0.34), c - int(h * 0.05),
                             int(w * 0.5), int(h * 0.9)))
    # the two eyes: deep hollow sockets. dark, watching.
    ew, eh = int(w * 0.5), int(h * 0.3)
    ey = c - int(h * 0.18)
    eyes = []
    for sgn in (-1, 1):
        ex = c + sgn * int(w * 0.46)
        pygame.draw.ellipse(fc, (4, 4, 6), (ex - ew // 2, ey - eh // 2, ew, eh))
        eyes.append((ex, ey))
    # the mouth: a thin, level line -- calm -- parting a little as he rouses
    mw = int(w * (0.5 + 0.25 * threat))
    my = c + int(h * 0.52)
    pygame.draw.line(fc, (8, 8, 10), (c - mw, my), (c + mw, my),
                     max(1, int(hr * (0.07 + 0.10 * threat))))
    # a faint vertical seam down the mask -- it will be the split, later
    pygame.draw.line(fc, (_BONE_DK[0], _BONE_DK[1], _BONE_DK[2], 120),
                     (c, c - h), (c, c + h), 1)
    # THE WAKE: gold only here, only when locked. A wet gleam in each socket.
    if lock > 0.02:
        gx = int(math.sin(t * 0.3) * w * 0.10)      # the held, drifting gaze
        for (ex, ey) in eyes:
            gr = max(1, int(eh * 0.32))
            pygame.draw.circle(fc, (*_shade(_GOLD, 0.4 + 0.6 * lock), int(220 * lock)),
                               (ex + gx, ey), gr)
            pygame.draw.circle(fc, (*_GOLD_HI, int(180 * lock)),
                               (ex + gx - gr // 2, ey - gr // 2), max(1, gr // 2))
        # the Yellow Sign bleeding faint on the brow
        sy = c - int(h * 0.62)
        sr = int(w * 0.4)
        for k in range(3):
            aa = -math.pi / 2 + k * 2.094 + t * 0.2
            pygame.draw.line(fc, (*_GOLD_DK, int(150 * lock)), (c, sy),
                             (c + math.cos(aa) * sr, sy + math.sin(aa) * sr * 0.7),
                             max(1, int(hr * 0.05)))
    # rotate the whole head by the wrong little tilt, blit
    if abs(tilt) > 0.001:
        fc = pygame.transform.rotate(fc, math.degrees(tilt))
    r = fc.get_rect(center=(int(hx), int(hy)))
    surf.blit(fc, r.topleft)


def _arm(surf, sx, sy, ang, length, width, threat, t, seed):
    """A human-but-TOO-LONG arm: a thin void limb reaching out, ending in long
    grasping fingers. Only appears as he closes. Void body + a cold rim, no gold."""
    segs = 7
    r = random.Random(seed)
    x, y = sx, sy
    a = ang
    pts = [(x, y)]
    for k in range(1, segs + 1):
        fr = k / segs
        a += (0.10 + 0.12 * threat) * (1 if seed % 2 == 0 else -1) * 0.5
        a += math.sin(t * 1.1 + seed + fr * 3) * 0.05
        step = length / segs
        x += math.cos(a) * step
        y += math.sin(a) * step
        pts.append((x, y))
    # void body
    for k in range(len(pts) - 1):
        w = max(1, int(width * (1 - 0.7 * k / len(pts))))
        pygame.draw.line(surf, _VOID, pts[k], pts[k + 1], w + 2)
    for k in range(len(pts) - 1):
        w = max(1, int(width * (1 - 0.7 * k / len(pts))))
        pygame.draw.line(surf, _RIM, pts[k], pts[k + 1], max(1, w - 1))
    # the long grasping fingers
    tx, ty = pts[-1]
    px, py = pts[-2]
    base = math.atan2(ty - py, tx - px)
    fl = length * 0.32
    for fgr in (-0.5, -0.16, 0.16, 0.5):
        fa = base + fgr - 0.25 * threat
        fx, fy = tx + math.cos(fa) * fl, ty + math.sin(fa) * fl
        pygame.draw.line(surf, _VOID, (tx, ty), (fx, fy), max(1, int(width * 0.5)))
        pygame.draw.line(surf, _RIM, (tx, ty), (fx, fy), max(1, int(width * 0.25)))


def draw_king_void(surf, cx, cy, t, threat=0.0, scale=4.0, lock=None):
    """Draw the Pallid Hole centred at (cx, cy). `threat` 0..1 escalates: dormant
    stillness -> faces surfacing -> the gold WAKE (lock) -> arms reaching as he
    closes. `lock` overrides the eye-wake (else derived from threat)."""
    H = 26.0 * scale
    if lock is None:
        lock = max(0.0, min(1.0, (threat - 0.45) / 0.4))   # he wakes once he sees you
    # he STUTTERS closer as he rouses -- the aura (and figure) swell a little
    grow = 1.0 + 0.18 * threat
    H *= grow
    B = _body_polys(cx, cy, H, t, threat)

    # 1) EAT THE LIGHT around him -- the room darkens toward the hole
    _eat_light(surf, B["ax"], cy, H * 0.95, 60 + 90 * threat)

    # 2) arms reaching (only as he closes), behind the body
    if threat > 0.5:
        reach = (threat - 0.5) / 0.5
        al = H * (0.5 + 0.7 * reach)
        _arm(surf, B["sh_l"][0], B["sh_l"][1], math.pi * 0.62, al,
             H * 0.045, threat, t, 2)
        _arm(surf, B["sh_r"][0], B["sh_r"][1], math.pi * 0.38, al * 0.92,
             H * 0.045, threat, t, 3)

    # 3) the VOID body + frayed hem, with a faint cold edge so the shape reads
    if len(B["robe"]) >= 3:
        pygame.draw.polygon(surf, _VOID, B["robe"])
        pygame.draw.polygon(surf, _RIM, B["robe"], 1)
    hx, hy, hr = B["head"]
    pygame.draw.ellipse(surf, _VOID, (hx - hr, hy - hr * 1.15, hr * 2, hr * 2.3))
    # the cold rim only on the left (a single weak light source)
    pygame.draw.arc(surf, _RIM, (hx - hr, hy - hr * 1.15, hr * 2, hr * 2.3),
                    math.pi * 0.5, math.pi * 1.4, 1)

    # 4) the drowning dead, surfacing in him
    _draw_drowning(surf, B, H, t, threat)

    # 5) the pallid mask + the gold wake (the only gold in the figure)
    _mask(surf, hx, hy - hr * 0.05, hr, t, threat, lock)
