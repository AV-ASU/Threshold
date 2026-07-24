"""THE AMALGAMS -- the Watcher-family shadows assembled from parts.

A shadow here is not one body: it is 3-5 PARTS, each emerging from its own
free-form CUT (a small aperture in the world, the same grammar at every
part: flesh clipped dead flat against the line, the rim lip on the absent
side, gold motes bleeding off it). Nothing touches anything else -- the
parts hang in formation around one anchor, thin haze threads the only
tissue, and the brain stitches "one creature" out of their synchrony.

Assembly is DATA: `assemble(seed)` deals 3-5 parts from the 17-part
library under the composition rules (at least one weight-bearing part on
the ground, masses centre, senses high, and ALWAYS at least one
eye-bearing part -- every amalgam watches). A different seed is a
different creature; the same seed always rebuilds the same one.

Behavior is the OG Watcher's, unchanged (spawn rules, hold, gaze/axe/
round/light dispel). What this module adds is presentation only:
- MANIFEST is a staggered build-out (parts enter cut by cut, driven by
  the spawn ramp passed as `birth`);
- the GAZE-DISPEL is a peeling (parts retract into their cuts in reverse,
  driven by the dispel fraction passed as `dispel`);
- IDLE is alive (masses breathe, limbs shift weight, the gut sac drips,
  eyes drift; every cut wanders a pixel around its offset).

Entry point: `draw_amalgam_sprite(surf, x, y, seed, gaze, birth, dispel)`
-- dispatched from `draw_npc_sprite` for `kind == "amalgam"`, feet at
(x, y), half-there phase + after-image like the Watcher. DESIGN.md §1.
"""
import math
import random

import pygame

SHROUD = (24, 22, 28)
SHROUD_LO = (12, 11, 15)
VOID = (6, 6, 9)
RIM = (46, 46, 60)
EMBER_G = (54, 46, 20)
EMBER = (110, 88, 30)
EMBER_DIM = (90, 74, 27)

GY = 96                      # the internal floor row of the part space
_GAZE = False                # stared-at: every ember goes dark (family rule)


def _ease(d):
    return d * d * (3 - 2 * d)


def _clamp(v):
    return max(0.0, min(1.0, v))


def _with_alpha(s, a):
    """Fade a per-pixel-alpha surface by an overall factor a (0..255)."""
    s = s.copy()
    s.fill((255, 255, 255, max(0, min(255, int(a)))),
           special_flags=pygame.BLEND_RGBA_MULT)
    return s


def _tent(s, pts, w0, w1, col=SHROUD):
    n = 36
    sm = []
    for i in range(n + 1):
        f = i / n
        seg = f * (len(pts) - 1)
        k = min(int(seg), len(pts) - 2)
        lf = seg - k
        ax, ay = pts[k]
        bx, by = pts[k + 1]
        sm.append((ax + (bx - ax) * lf, ay + (by - ay) * lf))
    for i, (px, py) in enumerate(sm):
        r = w0 + (w1 - w0) * (i / n)
        pygame.draw.circle(s, col, (int(px), int(py)), max(1, int(round(r))))


def _lump(s, cx, cy, rx, ry, lo=True):
    if rx < 1 or ry < 1:
        return
    pygame.draw.ellipse(s, SHROUD, (int(cx - rx), int(cy - ry),
                                    int(rx * 2), int(ry * 2)))
    if lo:
        pygame.draw.arc(s, SHROUD_LO, (int(cx - rx), int(cy - ry),
                                       int(rx * 2), int(ry * 2)),
                        math.pi * 1.15, math.pi * 1.95, 2)


def _eye(s, x, y, dim=False, r=1):
    pygame.draw.circle(s, EMBER_G, (int(x), int(y)), r + 2)
    if _GAZE:
        pygame.draw.circle(s, VOID, (int(x), int(y)), r)   # stared dark
    else:
        pygame.draw.circle(s, EMBER_DIM if dim else EMBER,
                           (int(x), int(y)), r)


def _haze(s, cx, cy, r, a):
    g = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(g, (40, 38, 50, int(a)), (int(cx), int(cy)), int(r))
    s.blit(g, (0, 0))


def _clip_half(lay, cx, cy, ang, side):
    """Erase everything on one side of the cut line -- the flesh ends DEAD
    FLAT against its aperture, the whole grammar in one operation."""
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy * side, dx * side
    p0 = (cx - dx * 200, cy - dy * 200)
    p1 = (cx + dx * 200, cy + dy * 200)
    p2 = (p1[0] + nx * 200, p1[1] + ny * 200)
    p3 = (p0[0] + nx * 200, p0[1] + ny * 200)
    pygame.draw.polygon(lay, (0, 0, 0, 0),
                        [(int(a), int(b)) for a, b in (p0, p1, p2, p3)])


def _cut_line(s, cx, cy, ang, ln, alpha=1.0, side=1):
    """The cut itself: VOID core on the line, RIM lip offset onto the
    absent side, motes; a partially-open (or dying) cut smokes."""
    if alpha <= 0.02 or ln <= 1:
        return
    dx, dy = math.cos(ang), math.sin(ang)
    p0 = (cx - dx * ln / 2, cy - dy * ln / 2)
    p1 = (cx + dx * ln / 2, cy + dy * ln / 2)
    nx, ny = -dy * side, dx * side
    g = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    a = int(255 * alpha)
    pygame.draw.line(g, VOID + (a,), (p0[0], p0[1]), (p1[0], p1[1]), 1)

    def lp(f, off):
        return (p0[0] + (p1[0] - p0[0]) * f + nx * off,
                p0[1] + (p1[1] - p0[1]) * f + ny * off)
    pygame.draw.line(g, RIM + (a,), lp(0.02, 1.5), lp(0.42, 1.5), 2)
    pygame.draw.line(g, RIM + (a,), lp(0.56, 1.5), lp(0.98, 1.5), 2)
    s.blit(g, (0, 0))
    rng = random.Random(int(cx * 7 + cy * 13) & 0xffff)
    for k in range(2):
        mx = cx + nx * rng.uniform(3, 8) + rng.uniform(-2, 2)
        my = cy + ny * rng.uniform(3, 8) + rng.uniform(-2, 2)
        pygame.draw.circle(s, EMBER_G if k == 0 else SHROUD,
                           (int(mx), int(my)), 1)
    if 0.05 < alpha < 0.95:
        _haze(s, cx + nx * 4, cy + ny * 4, 4, (1 - alpha) * 55)
        _haze(s, cx - dx * 5, cy - dy * 5, 3, (1 - alpha) * 40)


def _part(s, cx, cy, ang, side, draw_fn):
    lay = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    draw_fn(lay)
    _clip_half(lay, cx, cy, ang, side)
    s.blit(lay, (0, 0))


def _cl(d):
    """A part's cut-life from its deploy: opens ahead of the flesh."""
    return min(1.0, 0.35 + 0.8 * d)


# ============================= THE 17 PARTS ==================================
# Each: (surf, x, y, d, mode, k) -- d deploy 0..1, mode "enter"/"idle"/
# "leave", k a continuous 0..1 idle phase. Limbs lead with their extremity
# and walk or fold home; masses inflate, breathe, and can breathe shut.

def f_support_arm(s, x, y, d, mode, k):
    cx, cy = x + 8, y - 54
    gy = GY
    r = _ease(d)
    bend = (0.35 + 0.5 * k) if mode == "idle" else (0.2 if mode == "enter"
                                                    else 0.55)
    hx = cx - 17 * r
    hy = gy - 2 - (3 if (mode == "leave" and d > 0.4) else 0)
    if mode == "leave" and d > 0.4:
        hx += 5                                   # mid backwards-step

    def dd(lay):
        _lump(lay, cx + 1, cy + 3, 9 * min(1, r * 1.5), 8 * min(1, r * 1.5))
        _lump(lay, cx - 3 * r, cy + 9 * r, 7 * r, 6 * r, lo=False)
        sh_ = (cx - 2 * r, cy + 6 * r)
        elbow = ((sh_[0] + hx) / 2 - 4 * r, (sh_[1] + gy) / 2 - 9 * bend)
        _tent(lay, [sh_, elbow, (hx + 4, hy - 6), (hx, hy)],
              5.4 * (0.6 + 0.4 * r), 1.8)
        if d > 0.6:
            _lump(lay, (sh_[0] + elbow[0]) / 2, (sh_[1] + elbow[1]) / 2,
                  4, 3, lo=False)                                # the muscle
        if d > 0.35:
            spl = 1.3 if mode == "enter" else (0.6 if mode == "leave" else 1.0)
            for j in range(3):
                _tent(lay, [(hx, hy), (hx - (5 + j * 2) * spl,
                                       hy + 2 + (j % 2))], 2.0, 1.0)
        if d > 0.5:
            _eye(lay, cx - 2, cy + 7, dim=True)
    _part(s, cx, cy, 1.2, -1, dd)
    _cut_line(s, cx, cy, 1.2, 26 * _cl(d), alpha=_cl(d), side=-1)


def f_crawl_hand(s, x, y, d, mode, k):
    cx, cy = x - 8, y - 24
    gy = GY
    r = _ease(d)
    reach = (14 + 4 * k) if mode == "idle" else 14 * r + 2

    def dd(lay):
        _lump(lay, cx + 2, cy, 5 * min(1, r * 1.6), 5 * min(1, r * 1.6),
              lo=False)
        wx = cx + reach * 0.6
        tip = (cx + reach, gy - 3)
        _tent(lay, [(cx + 1, cy), (wx, gy - 8 - 2 * k), tip], 4.4, 1.7)
        _lump(lay, tip[0], tip[1] - 1, 3, 2, lo=False)           # knuckles
        spl = 1.2 if mode == "enter" else (0.5 if mode == "leave" else 1.0)
        for j in range(3):
            _tent(lay, [tip, (tip[0] + (5 + j * 2) * spl,
                              gy - (j % 2) - (2 if mode == "leave" else 0))],
                  2.0, 1.0)
    _part(s, cx, cy, 1.05, 1, dd)
    _cut_line(s, cx, cy, 1.05, 20 * _cl(d), alpha=_cl(d), side=1)


def f_leg(s, x, y, d, mode, k):
    cx, cy = x - 2, y - 56
    gy = GY
    r = _ease(d)
    kb = 3 * k if mode == "idle" else 0
    lift = 4 if (mode == "leave" and d > 0.4) else (
        3 if (mode == "enter" and d < 0.75) else 0)
    fx = cx + 5 * r + (4 if (mode == "leave" and d > 0.4) else 0)

    def L(px, py):
        return (cx + (px - cx) * r, cy + (py - cy) * r)

    def dd(lay):
        _lump(lay, cx + 2, cy + 3, 8 * min(1, r * 1.5), 7 * min(1, r * 1.5))
        knee = L(cx + 9, (cy + gy) // 2 - 2 + kb)
        foot = L(fx, gy - 2 - lift)
        _tent(lay, [L(cx, cy + 4), knee,
                    ((knee[0] + foot[0]) / 2, (knee[1] + foot[1]) / 2 + 3),
                    foot], 5.0 * (0.6 + 0.4 * r), 2.0)
        _lump(lay, (knee[0] + foot[0]) / 2 - 1, (knee[1] + foot[1]) / 2,
              3 * r, 4 * r, lo=False)                            # the calf
        if d > 0.7 and lift == 0:
            for j in range(2):
                _tent(lay, [foot, (foot[0] + 4 + j * 3, gy - (j % 2))],
                      2.2, 1.2)
    _part(s, cx, cy, 1.2, -1, dd)
    if d > 0.7 and lift == 0:
        g = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(g, (0, 0, 0, 40), (int(fx - 8), gy - 4, 16, 7))
        s.blit(g, (0, 0))
    _cut_line(s, cx, cy, 1.2, 22 * _cl(d), alpha=_cl(d), side=-1)


def f_elbow_prop(s, x, y, d, mode, k):
    cx, cy = x + 4, y - 50
    gy = GY
    r = _ease(d)
    settle = 2 * k if mode == "idle" else 0
    ex_ = cx - 10 * r
    ey_ = cy + (gy - 3 - cy) * r + settle

    def dd(lay):
        _lump(lay, cx + 1, cy + 3, 8 * min(1, r * 1.5), 7 * min(1, r * 1.5))
        _tent(lay, [(cx, cy + 4), (cx - 7 * r, cy + (gy - cy) * r * 0.55),
                    (ex_, ey_)], 5.6 * (0.6 + 0.4 * r), 3.0)
        _lump(lay, ex_, ey_ - 1, 5 * r, (4 - settle * 0.5) * r, lo=False)
        fold = 0.55 if mode == "leave" else (0.7 + 0.3 * r)
        _tent(lay, [(ex_, ey_ - 2), (ex_ + 2, (cy + ey_) / 2 + 4),
                    (cx - 3 * fold, cy + 14 * fold)], 3.4 * r, 1.6)
        if d > 0.6:
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(ex_ - 5), int(ey_ - 8), 10, 8), 0.3, 2.8, 1)
            pygame.draw.line(lay, RIM, (int(ex_ - 3), int(ey_ - 4)),
                             (int(ex_ + 2), int(ey_ - 5)), 1)
    _part(s, cx, cy, 1.25, -1, dd)
    _cut_line(s, cx, cy, 1.25, 24 * _cl(d), alpha=_cl(d), side=-1)


def f_reacher(s, x, y, d, mode, k):
    cx, cy = x + 16, y - 52
    gy = GY
    r = _ease(d)
    sweep = -8 + 16 * k if mode == "idle" else 0
    curl = mode == "leave"

    def dd(lay):
        _lump(lay, cx - 1, cy + 2, 6 * min(1, r * 1.6), 6 * min(1, r * 1.6),
              lo=False)
        tip = (cx - 40 * r + sweep, gy - 2 - (6 * r if curl else 0))
        _tent(lay, [(cx, cy + 2), (cx - 12 * r, cy + 12 * r),
                    (cx - 22 * r, gy - 8 * r - (gy - cy - 20) * (1 - r)),
                    (cx - 32 * r + sweep * 0.6,
                     gy - 3 - (3 * r if curl else 0)), tip],
              3.4 * (0.6 + 0.4 * r), 1.1)
        if d > 0.5 and not curl:
            for j in range(2):
                _tent(lay, [tip, (tip[0] - 5 - j * 3, gy - (j % 2))],
                      1.6, 1.0)
        if curl:
            _tent(lay, [tip, (tip[0] + 3, tip[1] - 4)], 1.6, 1.0)
        if d > 0.6:
            pygame.draw.line(lay, RIM, (int(cx - 10 * r), int(cy + 9 * r)),
                             (int(cx - 16 * r), int(cy + 14 * r)), 1)
    _part(s, cx, cy, 1.4, -1, dd)
    _cut_line(s, cx, cy, 1.4, 16 * _cl(d), alpha=_cl(d), side=-1)


def f_stump(s, x, y, d, mode, k):
    cx, cy = x - 2, y - 52
    gy = GY
    r = _ease(d)
    tilt = -2 + 4 * k if mode == "idle" else 0
    hike = 6 if (mode == "leave" and d > 0.4) else (
        4 if (mode == "enter" and d < 0.75) else 0)

    def dd(lay):
        _lump(lay, cx + 1, cy + 3, 8 * min(1, r * 1.5), 7 * min(1, r * 1.5))
        base = (cx + 4 * r + tilt, cy + (gy - 4 - cy) * r - hike)
        _tent(lay, [(cx, cy + 3), (cx + 3 * r + tilt * 0.5,
                                   (cy + base[1]) / 2), base],
              6.0 * (0.6 + 0.4 * r), 3.4)
        _lump(lay, base[0], base[1] + 1, 5 * r, 3 * r, lo=False)
        if d > 0.6:
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(base[0] - 5), int(base[1] - 4), 10, 6),
                            3.3, 6.1, 1)
    _part(s, cx, cy, 1.3, -1, dd)
    if d > 0.7 and hike == 0:
        g = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        pygame.draw.ellipse(g, (0, 0, 0, 40),
                            (int(cx + 4 * r + tilt - 7), gy - 4, 14, 6))
        s.blit(g, (0, 0))
    _cut_line(s, cx, cy, 1.3, 22 * _cl(d), alpha=_cl(d), side=-1)


def f_finger_fan(s, x, y, d, mode, k):
    cx, cy = x - 8, y - 40
    r = _ease(d)
    n = max(1, int(5 * d + 0.5))
    wave = 0.12 * k if mode == "idle" else 0
    curlm = 0.65 if mode == "leave" else 1.0

    def dd(lay):
        _lump(lay, cx + 1, cy + 2, 4 * min(1, r * 1.6), 6 * min(1, r * 1.6),
              lo=False)
        F = ((-0.85, 17), (-0.45, 20), (-0.05, 19), (0.35, 16), (0.75, 12))
        for j, (fa, ln) in enumerate(F[:n]):
            fa += wave * (1 if j % 2 else -1)
            ln = ln * r * curlm
            rooty = cy - 4 + j * 3
            exx = cx + math.cos(fa) * ln
            eyy = rooty + math.sin(fa) * ln + (3 if mode == "leave" else 0)
            _tent(lay, [(cx + 1, rooty),
                        (cx + math.cos(fa) * ln * 0.6,
                         rooty + math.sin(fa) * ln * 0.6 - 2),
                        (exx, eyy), (exx + 2, eyy + 2)], 1.8, 1.0)
    _part(s, cx, cy, 1.1, 1, dd)
    _cut_line(s, cx, cy, 1.1, 18 * _cl(d), alpha=_cl(d), side=1)


def f_tail(s, x, y, d, mode, k):
    cx, cy = x + 10, y - 42
    gy = GY
    r = _ease(d)
    sway = -3 + 6 * k if mode == "idle" else 0
    tiplift = 4 if mode == "leave" else 0

    def L(px, py):
        return (cx + (px - cx) * r, cy + (py - cy) * r)

    def dd(lay):
        _lump(lay, cx - 2, cy + 2, 6 * min(1, r * 1.6), 6 * min(1, r * 1.6),
              lo=False)
        _tent(lay, [L(cx, cy + 2), L(cx - 12, gy - 10),
                    L(cx - 22, gy - 3), L(cx - 32 + sway, gy - 2 - tiplift)],
              4.6 * (0.6 + 0.4 * r), 1.0)
    _part(s, cx, cy, 0.9, -1, dd)
    _cut_line(s, cx, cy, 0.9, 20 * _cl(d), alpha=_cl(d), side=-1)


def f_wing_stub(s, x, y, d, mode, k):
    cx, cy = x - 8, y - 48
    r = _ease(d)
    if mode == "enter" and d < 0.5:
        spread = 1.4                              # snaps OPEN first
    elif mode == "leave":
        spread = 0.7
    else:
        spread = 1.0 + 0.12 * k                   # the idle twitch

    def dd(lay):
        _lump(lay, cx + 1, cy + 2, 5 * min(1, r * 1.6), 5 * min(1, r * 1.6),
              lo=False)
        sp = spread * r * 1.3
        pts = [(cx + 2, cy), (cx + 14 * sp, cy - 8 * sp),
               (cx + 20 * sp, cy + 2 * sp), (cx + 15 * sp, cy + 5 * sp),
               (cx + 17 * sp, cy + 10 * sp), (cx + 10 * sp, cy + 8 * sp),
               (cx + 4 * sp, cy + 10 * sp)]
        ipts = [(int(a), int(b)) for a, b in pts]
        pygame.draw.polygon(lay, SHROUD_LO, ipts)
        pygame.draw.lines(lay, VOID, True, ipts, 1)
        if d > 0.5:
            pygame.draw.line(lay, VOID, (int(cx + 4 * sp), cy + 2),
                             (int(cx + 15 * sp), cy - 2), 1)     # membrane rib
            pygame.draw.line(lay, RIM, ipts[1], ipts[2], 1)
    _part(s, cx, cy, 0.8, -1, dd)
    _cut_line(s, cx, cy, 0.8, 16 * _cl(d), alpha=_cl(d), side=-1)


def f_haunch(s, x, y, d, mode, k):
    cx, cy = x, y - 40
    br = k if mode == "idle" else 0.4
    sc = _ease(d) * (0.93 + 0.10 * br)

    def dd(lay):
        _lump(lay, cx - 4 * sc, cy + 7 * sc, 12 * sc, 10 * sc)
        _lump(lay, cx + 4 * sc, cy + 12 * sc, 9 * sc, 7 * sc, lo=False)
        if sc > 0.5:
            pygame.draw.arc(lay, VOID, (int(cx - 9 * sc), int(cy + 5 * sc),
                                        int(16 * sc), int(9 * sc)),
                            3.5, 5.4, 1)
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(cx - 6 * sc), int(cy + 11 * sc),
                             int(14 * sc), int(8 * sc)), 3.6, 5.6, 1)
        if sc > 0.55:
            _eye(lay, cx - 4 * sc, cy + 9 * sc, dim=True)
    _part(s, cx, cy, 0.45, -1, dd)
    _cut_line(s, cx, cy, 0.45, 26 * _cl(d), alpha=_cl(d), side=-1)


def f_hump(s, x, y, d, mode, k):
    cx, cy = x, y - 46
    br = k if mode == "idle" else 0.4
    sc = _ease(d) * (0.93 + 0.10 * br)

    def dd(lay):
        _lump(lay, cx - 3 * sc, cy + 5 * sc, 11 * sc, 9 * sc)
        _lump(lay, cx + 6 * sc, cy + 8 * sc, 8 * sc, 6 * sc, lo=False)
        if sc > 0.5:
            pygame.draw.line(lay, RIM, (int(cx - 12 * sc), int(cy + 6 * sc)),
                             (int(cx - 13 * sc), int(cy + 12 * sc)), 1)
    _part(s, cx, cy, 0.3, -1, dd)
    _cut_line(s, cx, cy, 0.3, 24 * _cl(d), alpha=_cl(d), side=-1)


def f_rib_flank(s, x, y, d, mode, k):
    cx, cy = x, y - 42
    br = (1 - k) if mode == "idle" else 0.5       # exhale surfaces the ribs
    sc = _ease(d) * (0.93 + 0.10 * (1 - br))

    def dd(lay):
        _lump(lay, cx - 2 * sc, cy + 8 * sc, 16 * sc, 9 * sc)
        _lump(lay, cx + 8 * sc, cy + 12 * sc, 10 * sc, 6 * sc, lo=False)
        if sc > 0.5:
            ribs = 4 if br < 0.5 else 2
            for j in range(ribs):
                rx_ = cx + (-10 + j * 6) * sc
                pygame.draw.arc(lay, SHROUD_LO,
                                (int(rx_), int(cy + 3 * sc),
                                 int(7 * sc), int(12 * sc)),
                                math.pi * 0.6, math.pi * 1.5, 1)
            pygame.draw.line(lay, RIM, (int(cx - 14 * sc), int(cy + 4 * sc)),
                             (int(cx - 6 * sc), int(cy + 2 * sc)), 1)
        if sc > 0.55:
            _eye(lay, cx + 11 * sc, cy + 9 * sc, dim=True)
    _part(s, cx, cy, 0.35, -1, dd)
    _cut_line(s, cx, cy, 0.35, 30 * _cl(d), alpha=_cl(d), side=-1)


def f_gut_sac(s, x, y, d, mode, k):
    cx, cy = x, y - 62
    r = _ease(d)
    swing = -2 + 4 * k if mode == "idle" else 0
    drawn = 0.6 if mode == "leave" else 1.0       # drawn up on leave
    sag = r * drawn

    def dd(lay):
        _lump(lay, cx - 1, cy + 6 * sag, 7 * r, 6 * r, lo=False)
        _lump(lay, cx + swing, cy + 14 * sag, 9 * r, 10 * sag)
        _lump(lay, cx + 1 + swing, cy + 21 * sag, 6 * r, 6 * sag, lo=False)
        if r > 0.5:
            pygame.draw.arc(lay, SHROUD_LO,
                            (int(cx - 7 + swing), int(cy + 12 * sag),
                             14, max(2, int(10 * sag))), 3.4, 5.8, 1)
            pygame.draw.arc(lay, RIM, (int(cx - 5), int(cy + 8 * sag), 8, 6),
                            1.6, 2.9, 1)
        if r > 0.7 and mode == "idle" and k > 0.7:
            _tent(lay, [(cx + 1 + swing, cy + 26 * sag),
                        (cx + 2 + swing, cy + 30 * sag)], 1.6, 1.0)
            _lump(lay, cx + 2 + swing, cy + 31 * sag, 1, 1, lo=False)
    _part(s, cx, cy, 0.1, -1, dd)
    _cut_line(s, cx, cy, 0.1, 20 * _cl(d), alpha=_cl(d), side=-1)


def f_spine_ridge(s, x, y, d, mode, k):
    cx, cy = x - 10, y - 52
    n = max(1, int(4.2 * d))                      # the chain pulls out
    wave = 1.5 * k if mode == "idle" else 0

    def dd(lay):
        pts = [(cx - 2, cy + 4), (cx + 6, cy - 4), (cx + 14, cy - 5),
               (cx + 21, cy + 1), (cx + 26, cy + 10)]
        use = pts[:n + 1]
        _tent(lay, use, 3.0, 1.6)
        for j, (px, py) in enumerate(use[:-1][:n]):
            off = wave * (1 if j % 2 else -1)
            _lump(lay, px, py - 5 + off, 3, 3, lo=False)
            pygame.draw.line(lay, RIM, (int(px - 1), int(py - 9 + off)),
                             (int(px + 1), int(py - 9 + off)), 1)
        if n >= 4:
            _lump(lay, cx + 26, cy + 12, 3, 2, lo=False)
    _part(s, cx, cy, 1.05, 1, dd)
    _cut_line(s, cx, cy, 1.05, 22 * _cl(d), alpha=_cl(d), side=1)


def f_eye_bulge(s, x, y, d, mode, k):
    cx, cy = x, y - 52
    br = k if mode == "idle" else 0.4
    sc = _ease(d) * (0.93 + 0.10 * br)
    eyes_on = (d > 0.75) if mode == "enter" else (d > 0.6)

    def dd(lay):
        _lump(lay, cx - 2 * sc, cy + 5 * sc, 8 * sc, 7 * sc, lo=False)
        _lump(lay, cx + 4 * sc, cy + 9 * sc, 6 * sc, 5 * sc, lo=False)
        if eyes_on:
            dr = (-1.5 + 3 * k) if mode == "idle" else 0
            _eye(lay, cx - 4 * sc + dr, cy + 5 * sc, r=2)
            _eye(lay, cx + 3 * sc, cy + 9 * sc + dr * 0.5, dim=True)
            _eye(lay, cx - 1 * sc, cy + 3 * sc, dim=True)
    _part(s, cx, cy, 0.15, -1, dd)
    _cut_line(s, cx, cy, 0.15, 22 * _cl(d), alpha=_cl(d), side=-1)


def f_vent(s, x, y, d, mode, k):
    cx, cy = x, y - 50
    nsm = max(1, int(11 * d))
    breathe = 1.0 + 0.35 * k if mode == "idle" else 1.0
    for j in range(nsm):
        _haze(s, cx - 1 + (j % 3) * 4 + j, cy + 2 + j * 4 * breathe,
              (5 + j * 0.7) * breathe, max(30, (90 - j * 7) * d))
    _cut_line(s, cx, cy, 1.4, 18 * _cl(d), alpha=_cl(d), side=1)
    rng = random.Random(7)
    for j in range(max(1, int(5 * d))):
        pygame.draw.circle(s, EMBER_G if j % 2 else SHROUD,
                           (int(cx + rng.uniform(-3, 10)),
                            int(cy + 2 + rng.uniform(0, 20))), 1)


def f_ember_pair(s, x, y, d, mode, k):
    cx, cy = x, y - 44
    ang = 1.35
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    w = 3 * _ease(d)
    ln = 10 * (0.5 + 0.5 * d)
    pts = [(cx - dx * ln, cy - dy * ln),
           (cx - dx * ln * 0.4 + nx * w, cy - dy * ln * 0.4 + ny * w),
           (cx + dx * ln * 0.5 + nx * w, cy + dy * ln * 0.5 + ny * w),
           (cx + dx * ln, cy + dy * ln),
           (cx + dx * ln * 0.5 - nx * w, cy + dy * ln * 0.5 - ny * w),
           (cx - dx * ln * 0.4 - nx * w, cy - dy * ln * 0.4 - ny * w)]
    pygame.draw.polygon(s, VOID, [(int(a), int(b)) for a, b in pts])
    pygame.draw.lines(s, RIM, True, [(int(a), int(b)) for a, b in pts], 1)
    blink = (mode == "idle" and k > 0.75)
    if d > 0.5:
        _eye(s, cx - dx * 4, cy - dy * 4, r=2, dim=blink)
        if d > 0.8 or mode != "leave":
            _eye(s, cx + dx * 4, cy + dy * 4, r=2, dim=blink)


WEIGHT = [("leg", f_leg), ("stump", f_stump), ("elbow", f_elbow_prop),
          ("arm", f_support_arm), ("hand", f_crawl_hand)]
MASS = [("haunch", f_haunch), ("hump", f_hump), ("rib", f_rib_flank),
        ("gut", f_gut_sac), ("spine", f_spine_ridge)]
SENSE = [("eyes", f_eye_bulge), ("pair", f_ember_pair), ("vent", f_vent),
         ("fan", f_finger_fan), ("tail", f_tail), ("wing", f_wing_stub)]


def assemble(seed):
    """Deal a creature: 3-5 parts under the composition rules. The prefix
    (weights + masses) caps at 4 so there is ALWAYS room for the first
    sense slot, which is always an eye-bearing part: every amalgam
    watches. Same seed, same creature."""
    rng = random.Random(seed)
    parts = []
    nw = rng.choice((1, 2, 2, 3))
    for x0 in rng.sample([-28, -14, 2, 16, 30], nw):
        nm, fn = rng.choice(WEIGHT)
        parts.append((nm, fn, x0, 96 + rng.randint(-8, 2)))
    for _ in range(rng.choice((1, 1, 2))):
        nm, fn = rng.choice(MASS)
        parts.append((nm, fn, rng.randint(-12, 12), 96 - rng.randint(6, 24)))
    parts = parts[:4]
    ns = rng.choice((1, 2, 2))
    for i in range(ns):
        nm, fn = (rng.choice(SENSE[:2]) if i == 0 else rng.choice(SENSE))
        parts.append((nm, fn, rng.randint(-22, 22), 96 - rng.randint(12, 32)))
    return parts[:5]


# ===================== THE PALLID MASK -- the 18th part ======================
# His face made an OBJECT (NARRATIVE 6a), carried in the storm as a part like
# any other: it surfaces from its own free-form CUT, is HELD by the flesh at
# the rim, and only ONE exists storm-wide at a time (the migrating bearer,
# driven by the storm state -- NEVER dealt by assemble(), so every ordinary
# amalgam is untouched). It is a REAL 3D OBJECT: `yaw` turns it a full 360, His
# carved face toward the PI on the near hemisphere and the hollow adzed BACK on
# the far one, foreshortening to a sliver at profile (this SUPERSEDES the older
# always-camera-facing call -- the maintainer wants it to respect the tilted
# world, so it is a prop that turns, not a billboard). It draws at player scale
# (STORM_MASK_R). The timber is a bone<->wood blend: the drowned-white plate
# shape + the cult wood's carved construction (pale plate, centre seam, brow +
# long nose, faint grain, deep recessed sockets with the gold a pinprick far
# back, NO mouth, NO halo); the reverse is the unfinished hollow, adze-gouged,
# a binding cord across it, the eye-holes leaking that same gold from behind.
_PMASK_BONE = {"base": (204, 198, 186), "hi": (228, 222, 208), "lo": (152, 146, 132),
               "grain": (136, 128, 114), "edge": (82, 74, 62)}
_PMASK_WOOD = {"base": (122, 92, 56), "hi": (154, 120, 76), "lo": (82, 60, 38),
               "grain": (58, 40, 24), "edge": (38, 26, 14)}
_PMASK_GOLD = (222, 178, 46)
_PMASK_HOT = (250, 214, 92)


def _pmask_pal(blend):
    b = max(0.0, min(1.0, blend))
    return {k: tuple(int(_PMASK_BONE[k][i] + (_PMASK_WOOD[k][i] - _PMASK_BONE[k][i]) * b)
                     for i in range(3)) for k in _PMASK_BONE}


def _pmask_jag(surf, cx, cy, rx, ry, col, seed, n=26, jit=0.04):
    rng = random.Random(seed)
    pts = [(cx + math.cos(i / n * math.tau) * rx * (1 + rng.uniform(-jit, jit)),
            cy + math.sin(i / n * math.tau) * ry * (1 + rng.uniform(-jit, jit)))
           for i in range(n)]
    pygame.draw.polygon(surf, col, [(int(a), int(b)) for a, b in pts])


def carved_pallid_surface(r, gaze=(0.0, 0.25), blend=0.5, seed=7, ember=1.0):
    """The carved-pallid Mask on its own square surface, centred and face-on.
    `ember` 0..1 guts the gold as the mask sinks back into its cut.

    RETAINED as the flat 2D face-art REFERENCE only: the shipping Mask is the
    3D `draw_pallid_3d` (whose front-hemisphere face echoes this art). Not on
    any live draw path; kept for a possible future texture-map onto the shell."""
    r = max(4, int(r))
    P = _pmask_pal(blend)
    S = int(r * 2.6)
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    mx = my = S // 2
    rx, ry = r * 0.78, r * 1.05
    plate = pygame.Surface((S, S), pygame.SRCALPHA)
    _pmask_jag(plate, mx, my, rx + 2, ry + 2, P["edge"], seed, jit=0.045)
    _pmask_jag(plate, mx, my, rx, ry, P["base"], seed + 1, jit=0.035)
    hi = pygame.Surface((S, S), pygame.SRCALPHA)
    _pmask_jag(hi, mx - int(r * 0.12), my - int(r * 0.18), rx * 0.8, ry * 0.74,
               (*P["hi"], 130), seed + 2, jit=0.04)
    plate.blit(hi, (0, 0))
    for gi in range(5):
        gx = mx + int((gi - 2) / 2.6 * rx * 0.7)
        pts = [(gx + int(math.sin(k * 0.9 + gi * 2.1) * 1.6),
                int(my - ry * 0.45 + (ry * 1.05) * k / 9)) for k in range(10)]
        pygame.draw.lines(plate, (*P["grain"], 34), False, pts, 1)
    grad = pygame.Surface((S, S), pygame.SRCALPHA)
    for yy in range(S):
        f = max(0.0, (yy - my) / (ry * 1.1))
        v = int(255 - 92 * min(1.0, f))
        pygame.draw.line(grad, (v, v, v, 255), (0, yy), (S, yy))
    plate.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    m.blit(plate, (0, 0))
    pygame.draw.line(m, (*P["grain"], 190), (mx, my - int(ry * 0.88)), (mx, my + int(ry * 0.9)), 2)
    pygame.draw.line(m, (*P["hi"], 110), (mx - 1, my - int(ry * 0.8)), (mx - 1, my + int(ry * 0.4)), 1)
    pygame.draw.arc(m, P["grain"], (mx - int(r * 0.58), my - int(r * 0.5), int(r * 1.16), int(r * 0.5)), 3.35, 6.1, 2)
    pygame.draw.line(m, P["grain"], (mx, my - int(r * 0.16)), (mx - 2, my + int(r * 0.4)), 2)
    pygame.draw.line(m, (*P["hi"], 150), (mx - 3, my - int(r * 0.14)), (mx - 5, my + int(r * 0.34)), 1)
    gx_, gy_ = max(-1, min(1, gaze[0])), max(-1, min(1, gaze[1]))
    pdx, pdy = int(gx_ * r * 0.055), int(gy_ * r * 0.065)
    for sgn in (-1, 1):
        ex = mx + sgn * int(r * 0.38)
        ey = my - int(r * 0.18)
        for i, (rr, c) in enumerate([(0.205, (66, 55, 42)), (0.15, (34, 27, 20)), (0.095, (7, 6, 4))]):
            _pmask_jag(m, ex + i, ey + i, r * rr, r * rr * 1.25, c, seed + 11 + i, n=12, jit=0.16)
        if ember > 0.05:
            px, py = ex + pdx, ey + 2 + pdy
            gs = int(r * 0.34) + 2
            gl = pygame.Surface((gs, gs), pygame.SRCALPHA)
            gr = gs // 2
            pygame.draw.circle(gl, (*_PMASK_GOLD, int(52 * ember)), (gr, gr), max(1, int(r * 0.075)))
            m.blit(gl, (px - gr, py - gr), special_flags=pygame.BLEND_RGBA_ADD)
            gcol = tuple(int((60, 50, 24)[i] + (_PMASK_GOLD[i] - (60, 50, 24)[i]) * ember) for i in range(3))
            pygame.draw.circle(m, gcol, (px, py), max(1, int(r * 0.042)))
            if ember > 0.4:
                pygame.draw.circle(m, _PMASK_HOT, (px, py), max(1, int(r * 0.02)))
    crk = [(mx + int(r * 0.46), my + int(r * 0.08)), (mx + int(r * 0.56), my + int(r * 0.44)),
           (mx + int(r * 0.4), my + int(r * 0.76))]
    pygame.draw.lines(m, P["edge"], False, crk, 2)
    return m


def draw_pallid_3d(surf, cx, cy, r, yaw=0.0, lean=6.0, gaze=(0.0, 0.25),
                   blend=0.5, seed=7, ember=1.0):
    """The Pallid Mask as ONE real 3D object: a single curved SHEET -- the FRONT
    CAP of an ellipsoid (semi-axes Rx < Ry, a REAL depth Rz), a bent oval of
    "paper", NOT a closed egg. `yaw` rotates the whole mesh about the vertical
    axis and projects it, so the carved face, the curved edge-on profile (a bent
    crescent of depth Rz, never a flat line and never a solid oval), and the pale
    concave inside seen from behind ALL fall out of the same geometry -- no swap,
    no billboard, no nose. BOTH sides render in the pale bone colour, so from
    behind it reads as a mask (its inside), never a dark half. The carved FACE
    (pale plate, brow, deep jagged sockets with a gold pinprick, centre seam, a
    hairline crack) is drawn as 3D-anchored overlays on the FRONT face ONLY and
    culls as it turns -- NO eyes from behind. `lean` is a small in-plane roll;
    `gaze` aims the gold; `ember` its life."""
    r = max(4, int(r))
    P = _pmask_pal(blend)

    def dk(c, f):
        return tuple(max(0, min(255, int(x * f))) for x in c)

    Rx, Ry, Rz = r * 0.78, r * 1.05, r * 0.42
    amb = 0.58                                               # high -> smooth, pale like the 2D
    Lx, Ly, Lz = -0.38, -0.52, 0.76
    ll = math.sqrt(Lx * Lx + Ly * Ly + Lz * Lz)
    Lx, Ly, Lz = Lx / ll, Ly / ll, Lz / ll
    cpsi, spsi = math.cos(yaw), math.sin(yaw)
    lrr = math.radians(lean)
    cl, sl = math.cos(lrr), math.sin(lrr)
    nphi, nth = 22, 48

    def rp(x, y, z):                                          # rotate + roll -> screen
        xr = x * cpsi + z * spsi
        zr = -x * spsi + z * cpsi
        return xr * cl - y * sl, xr * sl + y * cl, zr

    # ---- the shell body: a single curved SHEET (the FRONT cap only) -- a bent
    # oval of paper, NOT a closed egg. BOTH sides are drawn in the pale front
    # colour, so from behind you see its pale concave INSIDE (still reads as a
    # mask), never a dark far cap and never empty ----
    grid = []
    for i in range(nphi + 1):
        phi = math.pi * i / nphi
        sp, cpp = math.sin(phi), math.cos(phi)
        row = []
        for j in range(nth + 1):
            th = 2 * math.pi * j / nth
            st, ct = math.sin(th), math.cos(th)
            x, y, z = Rx * sp * ct, -Ry * cpp, Rz * sp * st
            nx, ny, nz = sp * ct / Rx, -cpp / Ry, sp * st / Rz
            nl = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
            nx, ny, nz = nx / nl, ny / nl, nz / nl
            sx, sy, zr = rp(x, y, z)
            row.append((z, sx, sy, zr, nx * cpsi + nz * spsi, ny,
                        -nx * spsi + nz * cpsi))
        grid.append(row)

    quads = []
    for i in range(nphi):
        for j in range(nth):
            a, b = grid[i][j], grid[i][j + 1]
            c2, e = grid[i + 1][j + 1], grid[i + 1][j]
            zc = (a[0] + b[0] + c2[0] + e[0]) * 0.25
            if zc < 0.0:                                       # FRONT cap only (no
                continue                                       # closed-egg far cap)
            nzr = (a[6] + b[6] + c2[6] + e[6]) * 0.25
            nxr = (a[4] + b[4] + c2[4] + e[4]) * 0.25
            nyr = (a[5] + b[5] + c2[5] + e[5]) * 0.25
            face = 1.0 if nzr >= 0.0 else -1.0                 # which side faces us
            lamb = max(0.0, (nxr * Lx + nyr * Ly + nzr * Lz) * face)
            sh = amb + (1 - amb) * lamb
            col = dk(P["base"], sh)                             # pale on BOTH sides
            zavg = (a[3] + b[3] + c2[3] + e[3]) * 0.25
            pts = [(int(cx + a[1]), int(cy + a[2])), (int(cx + b[1]), int(cy + b[2])),
                   (int(cx + c2[1]), int(cy + c2[2])), (int(cx + e[1]), int(cy + e[2]))]
            quads.append((zavg, pts, col))
    quads.sort(key=lambda q: q[0])                            # painter: far first
    for _, pts, col in quads:
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, col, pts, 1)               # cover facet seams

    # ---- the carved FACE, anchored in 3D on the FRONT hemisphere ONLY, so it
    # wraps with the shell and never shows from behind (no eyes on the back) ----
    def shell_pt(lx, ly):
        """Project a point on the oval face-plane onto the front bulge; return
        screen (px, py) + the point's facing (rotated normal z, ~1 head-on)."""
        u, v = lx / Rx, ly / Ry
        s2 = min(1.0, u * u + v * v)
        z = Rz * math.sqrt(max(0.0, 1.0 - s2))
        sx, sy, _zr = rp(lx, ly, z)
        nx, ny, nz = lx / (Rx * Rx), ly / (Ry * Ry), z / (Rz * Rz)
        nl = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
        return cx + sx, cy + sy, (-nx * spsi + nz * cpsi) / nl

    seam = []                                                # the centre seam
    for k in range(13):
        px, py, f_ = shell_pt(0.0, -Ry * 0.72 + k / 12.0 * Ry * 1.48)
        if f_ > 0.14:
            seam.append((int(px), int(py)))
    if len(seam) >= 2:
        pygame.draw.lines(surf, P["grain"], False, seam, 2)

    brow = []                                                # the brow ridge
    for k in range(-6, 7):
        fr = k / 6.0
        px, py, f_ = shell_pt(fr * Rx * 0.52, -Ry * 0.30 + (fr * fr) * Ry * 0.05)
        if f_ > 0.14:
            brow.append((int(px), int(py)))
    if len(brow) >= 2:
        pygame.draw.lines(surf, dk(P["grain"], 0.85), False, brow, 2)

    # the two DEEP jagged sockets + gold pupils (front hemisphere, gaze-aimed)
    gx_, gy_ = max(-1, min(1, gaze[0])), max(-1, min(1, gaze[1]))
    exl, eyl = Rx * 0.44, -Ry * 0.13
    for sgn in (-1, 1):
        px, py, fac = shell_pt(sgn * exl, eyl)
        if fac <= 0.16:                                      # gone past the edge
            continue
        srx = max(1.0, r * 0.2 * (0.35 + 0.65 * fac))        # compresses toward profile
        sry = max(1.0, r * 0.25)
        for (rr, ccol) in ((1.0, (66, 55, 42)), (0.72, (34, 27, 20)), (0.44, (7, 6, 4))):
            _pmask_jag(surf, px, py, srx * rr, sry * rr, ccol,
                       seed + 11 + int(rr * 13), n=12, jit=0.18)
        if ember > 0.05:
            ppx = px + gx_ * r * 0.05 * fac
            ppy = py + gy_ * r * 0.05
            gs = int(r * 0.5) + 2
            gl = pygame.Surface((gs, gs), pygame.SRCALPHA)
            gr = gs // 2
            pygame.draw.circle(gl, (*_PMASK_GOLD, int(60 * ember * fac)), (gr, gr),
                               max(1, int(r * 0.1)))
            surf.blit(gl, (int(ppx) - gr, int(ppy) - gr), special_flags=pygame.BLEND_RGBA_ADD)
            gcol = tuple(int((60, 50, 24)[i] + (_PMASK_GOLD[i] - (60, 50, 24)[i]) * ember)
                         for i in range(3))
            pygame.draw.circle(surf, gcol, (int(ppx), int(ppy)), max(1, int(r * 0.045)))
            if ember > 0.4:
                pygame.draw.circle(surf, _PMASK_HOT, (int(ppx), int(ppy)), max(1, int(r * 0.02)))

    crack = []                                               # a hairline crack, lower-right
    for (lx, ly) in ((Rx * 0.34, Ry * 0.04), (Rx * 0.44, Ry * 0.40), (Rx * 0.30, Ry * 0.72)):
        px, py, f_ = shell_pt(lx, ly)
        if f_ > 0.14:
            crack.append((int(px), int(py)))
    if len(crack) >= 2:
        pygame.draw.lines(surf, P["edge"], False, crack, 1)


def draw_pallid_mask_part(surf, cx, cy, r, deploy=1.0, gaze=(0.0, 0.3),
                          blend=0.5, seed=7, ang=1.2, side=-1, lean=8.0,
                          yaw=0.0):
    """The Mask as a PART: it rides out of its own cut (`deploy` 0..1) along
    the cut normal, held at the rim by shroud grips. `gaze` (gx, gy in -1..1)
    aims the gold pupils. `yaw` turns it as ONE 3D object (`draw_pallid_3d`) --
    His face, the curved edge-on profile, and the hollow back all fall out of
    the same rotating shell, no swap. Caller enforces one-bearer-at-a-time."""
    d = max(0.0, min(1.0, deploy))
    dx_, dy_ = math.cos(ang), math.sin(ang)
    nx, ny = -dy_ * side, dx_ * side
    lay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    mcx = cx + nx * r * 0.9 * d
    mcy = cy + ny * r * 0.9 * d
    ember = 0.25 + 0.75 * d
    # the Mask itself -- one rotating 3D shell, rendered onto its own layer
    draw_pallid_3d(lay, mcx, mcy, r, yaw=yaw, lean=lean, gaze=gaze,
                   blend=blend, seed=seed, ember=ember)
    # clip whatever is still INSIDE the cut (the far side of the cut line) so it
    # reads as rising from the slit; everything there ends dead flat (the grammar)
    p0 = (cx - dx_ * 400, cy - dy_ * 400); p1 = (cx + dx_ * 400, cy + dy_ * 400)
    p2 = (p1[0] - nx * 400, p1[1] - ny * 400); p3 = (p0[0] - nx * 400, p0[1] - ny * 400)
    pygame.draw.polygon(lay, (0, 0, 0, 0), [(int(a), int(b)) for a, b in (p0, p1, p2, p3)])
    surf.blit(lay, (0, 0))
    # the cut ends peek past the rim; shroud grips hold it on the line
    ln = r * (1.3 + 0.5 * d)
    q0 = (cx - dx_ * ln / 2, cy - dy_ * ln / 2); q1 = (cx + dx_ * ln / 2, cy + dy_ * ln / 2)
    pygame.draw.line(surf, VOID, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), 3)
    off = 2.2
    pygame.draw.line(surf, RIM,
                     (int(q0[0] - nx * off + dx_ * ln * 0.04), int(q0[1] - ny * off + dy_ * ln * 0.04)),
                     (int(q1[0] - nx * off - dx_ * ln * 0.06), int(q1[1] - ny * off - dy_ * ln * 0.06)), 2)
    grng = random.Random(seed + 3)
    for sgn in (-1, 1):
        gx = cx + dx_ * sgn * r * 0.52 + nx * r * 0.05
        gy = cy + dy_ * sgn * r * 0.52 + ny * r * 0.05
        lr = r * grng.uniform(0.15, 0.21)
        pygame.draw.ellipse(surf, SHROUD, (int(gx - lr), int(gy - lr * 0.75), int(lr * 2), int(lr * 1.5)))
        pygame.draw.arc(surf, SHROUD_LO, (int(gx - lr), int(gy - lr * 0.75), int(lr * 2), int(lr * 1.5)), 3.6, 5.9, 2)
    fx_ = cx + nx * r * 0.16; fy2 = cy + ny * r * 0.16; lr = r * 0.13
    pygame.draw.ellipse(surf, SHROUD, (int(fx_ - lr), int(fy2 - lr * 0.7), int(lr * 2), int(lr * 1.4)))
    for k in range(2):
        mxp = cx - nx * grng.uniform(3, 8) + grng.uniform(-2, 2)
        myp = cy - ny * grng.uniform(3, 8) + grng.uniform(-2, 2)
        pygame.draw.circle(surf, EMBER_G if k == 0 else SHROUD, (int(mxp), int(myp)), 1)


# ---- the possessed BEARER (drawn ONLY on the Mask-bearer) -------------------
# When the Mask jumps to an amalgam it POWERS IT UP -- and the power-up is
# SIZE: the bearer is simply a BIGGER amalgam than the ordinary shadows
# (BEARER_SCALE), not a busier one. Its one extra flourish is the CROWN -- an
# arc of ember-cuts (watching apertures) over the Mask. No hitbox; dread only.
BEARER_SCALE = 1.5


def _bearer_crown(surf, mcx, mcy, mr, power, seed):
    """An arc of ember-cuts over the Mask -- a crown of watching apertures."""
    if power <= 0.05:
        return
    rng = random.Random(seed + 9)
    n = 7
    for i in range(n):
        f = i / (n - 1)
        a = math.pi * (1.12 + 0.76 * f)
        cr = mr * (1.45 + 0.15 * power)
        cx = mcx + math.cos(a) * cr
        cy = mcy + math.sin(a) * cr * 0.85 - mr * 0.35
        dd = power * (0.55 + 0.45 * rng.random())
        _cut_line(surf, cx, cy, a + 1.57, mr * 0.55 * dd, alpha=dd, side=1)
        if dd > 0.4:
            _eye(surf, cx, cy, r=1)


def draw_amalgam_sprite(surf, x, y, seed=0, gaze=False, birth=None,
                        dispel=None, mask=None):
    """Feet at (x, y). `birth` 0..1 is the manifest ramp (parts build out
    staggered); `dispel` 0..1 is the gaze-dispel fraction (parts peel back
    into their cuts in reverse); `gaze` darkens every ember while the
    player stares (the family rule)."""
    global _GAZE
    t = pygame.time.get_ticks() / 1000.0
    b = 1.0 if birth is None else _clamp(birth)
    g = 0.0 if dispel is None else _clamp(dispel)
    parts = assemble(seed)
    n = len(parts)
    LW, LH = 150, 104
    lay = pygame.Surface((LW, LH), pygame.SRCALPHA)
    _GAZE = gaze
    rng = random.Random(seed * 7 + 3)
    anc = [(75 + p[2], (p[3] - 40)) for p in parts]
    for i in range(len(anc) - 1):
        a0, b0 = anc[i], anc[i + 1]
        for k in range(3):
            f = k / 2.0
            hx = a0[0] + (b0[0] - a0[0]) * f + rng.uniform(-2, 2)
            hy = a0[1] + (b0[1] - a0[1]) * f + rng.uniform(-2, 2)
            _haze(lay, hx, hy, 3 + rng.uniform(0, 2), 26)
    for idx, (nm, fn, x0, y0) in enumerate(parts):
        if g > 0.0:
            # the peeling: last parts first, each back into its cut
            dg = _clamp((g - (n - 1 - idx) * 0.13) / 0.48)
            d, mode = 1.0 - dg, "leave"
        elif b < 1.0:
            d, mode = _clamp((b - idx * 0.13) / 0.48), "enter"
        else:
            d, mode = 1.0, "idle"
        k = 0.5 + 0.5 * math.sin(t * (0.9 + 0.13 * (idx % 3))
                                 + idx * 1.7 + seed)
        dx_ = math.sin(t * 0.6 + idx * 2.1 + seed) * 1.2
        dy_ = math.cos(t * 0.5 + idx * 1.3) * 1.0
        if d > 0.01:
            fn(lay, 75 + x0 + dx_, y0 + dy_, d, mode, k)
        else:
            # its cut alone, dying
            _cut_line(lay, 75 + x0 + dx_, (y0 + dy_) - 44, 1.2, 10,
                      alpha=0.3, side=1)
    _GAZE = False
    # THE BEARER is simply a BIGGER amalgam -- that size IS the power-up tell.
    sc = 0.8 * (BEARER_SCALE if mask is not None else 1.0)
    sw, sh = int(LW * sc), int(LH * sc)
    scaled = pygame.transform.scale(lay, (sw, sh))
    base = int(GY * sc) + 2
    phase = 0.42 + 0.45 * (math.sin(t * 1.1 + seed) * 0.5 + 0.5)
    phase *= (1.0 - 0.5 * g)                      # thins as it is stared apart
    ghost = scaled.copy()
    ghost.set_alpha(int(230 * phase * 0.45))
    surf.blit(ghost, (int(x - sw // 2) - 3, int(y - base) - 1))
    scaled.set_alpha(int(230 * phase))
    surf.blit(scaled, (int(x - sw // 2), int(y - base)))
    # THE BEARER, when the storm passes `mask` (None for every ordinary
    # amalgam, so their draw is byte-identical). The power-up is the BIGGER
    # body drawn above; here we add the Mask itself + His crown of cuts.
    if mask is not None:
        power = _clamp(mask.get("deploy", 1.0))
        topy = y - base
        # the Mask itself (its own cut + grips), player-scale, a 3D prop by `yaw`
        mr = mask.get("r", max(8, int(sh * 0.17)))
        mcx = x + mask.get("dx", int(sw * 0.04))
        mcy = topy + mask.get("my", int(sh * 0.30))
        draw_pallid_mask_part(surf, mcx, mcy, mr,
                              deploy=power, gaze=mask.get("gaze", (0.0, 0.3)),
                              blend=mask.get("blend", 0.5),
                              seed=mask.get("seed", 7),
                              lean=mask.get("lean", 8.0), yaw=mask.get("yaw", 0.0))
        # the crown of ember-cuts arcing over the Mask
        _bearer_crown(surf, mcx, mcy - mr * 0.3, mr, power, seed)
