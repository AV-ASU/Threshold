"""THE DRIVE OUT -- the SPREAD ending cutscene (escape_alone).

The claiming, staged in three handcrafted compositions over ~38s:

  A  THE KEY    -- night, the car at the river's edge, taillights only.
                   The key turns and the engine that refused all game
                   roars to life: headlights bloom, the frame wakes.
  B  THE DRIVE  -- top-down road south through the corn, the car facing
                   DOWN-screen (the opening drive inverted). A gold wake
                   streams up-screen behind the car -- the King trailing,
                   pure particle, never a body. The back of the BRIMLEY
                   sign passes. A thin gold shimmer waits far ahead.
  C  THE SHIFT  -- hard cut inside the cab: dashboard, wheel, the dark
                   road rushing at the windshield, the rearview holding a
                   smear of the gold wake -- and the Pallid Mask riding
                   the passenger seat. It tilts, as if to look at you.
  D  THE GAZE   -- the camera eases into the mask; the gold wakes in its
                   deep sunken sockets. While the PI gazes, the fold's
                   frame sweeps past the windows UNWITNESSED (the
                   crossing is a non-event; the corn simply ends, the
                   mirror goes black, the static dies). Gold whites out.
  E  THE FLOOD  -- wide profile: the car stopped on the shoulder of an
                   open southern road, and COLOR arrives -- the first
                   horizon and sky in the cutscene, going gold.
  F  DRIVE ON   -- the car pulls away right and leaves the frame.
  G  THE VERDICT-- the empty road holds; the gold on the horizon
                   breathes like the light under the dream-door; fade
                   to black under "Everyone will know."

Stateless except cached grain/vignette. `draw_spread_drive(surf, t)`
with t = seconds since the ending began; systems.game builds the
escape_alone caption script from SPREAD_BEAT_DURS so the picture and
the text can never drift apart.
"""
import math
import random

import pygame

from rendering.sprites_king import _yk_radial, _YK_GOLD, _YK_HOT


# ---- Beat durations (seconds). One per caption line, in order. ----
BEAT_KEY = 4.0
BEAT_DRIVE = 5.2
BEAT_SHIFT = 4.4
BEAT_GAZE = 4.6
BEAT_FLOOD = 7.4
BEAT_ON = 6.4
BEAT_KNOW = 6.0
SPREAD_BEAT_DURS = (BEAT_KEY, BEAT_DRIVE, BEAT_SHIFT, BEAT_GAZE,
                    BEAT_FLOOD, BEAT_ON, BEAT_KNOW)

# Cumulative beat starts (the audio tick keys off these too).
SPREAD_T_DRIVE = BEAT_KEY
SPREAD_T_SHIFT = SPREAD_T_DRIVE + BEAT_DRIVE
SPREAD_T_GAZE = SPREAD_T_SHIFT + BEAT_SHIFT
SPREAD_T_FLOOD = SPREAD_T_GAZE + BEAT_GAZE
SPREAD_T_ON = SPREAD_T_FLOOD + BEAT_FLOOD
SPREAD_T_KNOW = SPREAD_T_ON + BEAT_ON
SPREAD_TOTAL = SPREAD_T_KNOW + BEAT_KNOW

# The unwitnessed crossing: mid-gaze, while his eyes are off the road.
SPREAD_CROSS_AT = SPREAD_T_GAZE + BEAT_GAZE * 0.52

# Ignition timeline inside beat A.
_KEY_AT = 0.9            # the key turns (a dry click)
_ROAR_AT = 1.35          # the engine catches -- headlights bloom

_SCROLL_SPEED = 240.0    # px/s at full speed (beat B)


def _frand(i):
    """Cheap deterministic [0,1) noise -- no RNG state to disturb."""
    x = math.sin(i * 12.9898) * 43758.5453
    return x - math.floor(x)


def _clamp01(v):
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def _lerp(a, b, f):
    return a + (b - a) * f


def _lerpc(c0, c1, f):
    f = _clamp01(f)
    return (int(_lerp(c0[0], c1[0], f)), int(_lerp(c0[1], c1[1], f)),
            int(_lerp(c0[2], c1[2], f)))


def _pallid_mask(r, gaze):
    """The Pallid Mask as the OBJECT on the seat: an oblong of old bone,
    deep recessed sockets (shadow wells, not goggles), no mouth, one
    hairline crack. `gaze` (0..1) wakes the gold pinpoints in the
    sockets. Returns a fresh SRCALPHA surface; rotate/blit at will."""
    pad = max(4, r // 3)
    S = (r + pad) * 2
    m = pygame.Surface((S, S), pygame.SRCALPHA)
    cx = cy = r + pad
    rw, rh = int(r * 0.78), int(r * 1.04)
    # Bone, lit faintly from the upper left; the chin tapers.
    pygame.draw.ellipse(m, (118, 110, 92),
                        (cx - rw, cy - rh, 2 * rw, 2 * rh))
    pygame.draw.ellipse(m, (168, 160, 138),
                        (cx - rw + 1, cy - rh + 1, 2 * rw - 2, 2 * rh - 3))
    pygame.draw.ellipse(m, (196, 188, 166),
                        (cx - rw + 2, cy - rh + 1, 2 * rw - 5, 2 * rh - 7))
    # Cheek hollows + the brow shadow -- the gauntness.
    for sgn in (-1, 1):
        hx = cx + sgn * int(rw * 0.46)
        pygame.draw.ellipse(m, (150, 142, 120),
                            (hx - int(rw * 0.26), cy + int(rh * 0.10),
                             int(rw * 0.52), int(rh * 0.42)))
    pygame.draw.ellipse(m, (140, 132, 112),
                        (cx - int(rw * 0.78), cy - int(rh * 0.40),
                         int(rw * 1.56), int(rh * 0.26)))
    # Nose: a faint ridge, no nostrils -- a mask, not a face.
    pygame.draw.line(m, (152, 144, 124), (cx, cy - int(rh * 0.06)),
                     (cx, cy + int(rh * 0.26)), 2)
    pygame.draw.line(m, (206, 198, 178), (cx - 1, cy - int(rh * 0.06)),
                     (cx - 1, cy + int(rh * 0.20)), 1)
    # THE SOCKETS: deep sunken wells. A soft shadow ramp pools into a
    # near-black pit; the pit is oblong and angled faintly inward.
    for sgn in (-1, 1):
        ex = cx + sgn * int(rw * 0.46)
        ey = cy - int(rh * 0.14)
        for k in range(5, 0, -1):                 # the sink -- shadow ramp
            f = k / 5
            sw = int(rw * 0.34 * (0.55 + 0.45 * f))
            shh = int(rh * 0.26 * (0.55 + 0.45 * f))
            shade = _lerpc((150, 142, 122), (52, 44, 34), 1 - f)
            pygame.draw.ellipse(m, shade, (ex - sw, ey - shh, 2 * sw, 2 * shh))
        pw = int(rw * 0.20)
        phh = int(rh * 0.17)
        pygame.draw.ellipse(m, (16, 12, 9),
                            (ex - pw, ey - phh, 2 * pw, 2 * phh))
        if gaze > 0.01:                           # the gold, waking
            a = int(70 + 180 * gaze)
            _yk_radial(m, ex, ey, 2 + int(4 * gaze), _YK_HOT,
                       min(255, a), add=False)
            try:
                m.set_at((ex, ey), _YK_HOT)
            except (IndexError, ValueError):
                pass
    # One hairline crack from the brow down across the right socket rim.
    crk = [(cx + int(rw * 0.18), cy - rh + 3),
           (cx + int(rw * 0.30), cy - int(rh * 0.46)),
           (cx + int(rw * 0.22), cy - int(rh * 0.04)),
           (cx + int(rw * 0.34), cy + int(rh * 0.30))]
    pygame.draw.lines(m, (96, 88, 70), False, crk, 1)
    # No mouth. The chin is bone all the way down.
    return m


def _travelled(t):
    """Closed-form distance scrolled (px) -- the car eases from rest to
    full speed after the roar, so beat B needs no per-frame state."""
    t0, ramp = _ROAR_AT + 0.35, 1.6
    if t <= t0:
        return 0.0
    u = min(t - t0, ramp)
    d = 0.5 * u * u / ramp                  # the ease-in, in full-speed s
    if t - t0 > ramp:
        d += (t - t0 - ramp)
    return d * _SCROLL_SPEED


# ---------------------------------------------------------------------------
# Beats A + B -- the exterior road (top-down, the car facing south/down).
# ---------------------------------------------------------------------------

def _car_topdown_south(s, cx, cy, light, t, running, dome=0.0):
    """Top-down car FACING DOWN-SCREEN (south, out) -- the opening drive's
    car, turned around. `light` gates the headlights; `running` adds the
    idle tremor and exhaust; `dome` (0..1) lights the cabin from inside
    (the key-turn beat)."""
    jx = jy = 0
    if running:
        jx = int(round(math.sin(t * 47.0) * 0.9))
        jy = int(round(math.cos(t * 53.0) * 0.7))
    cx, cy = cx + jx, cy + jy
    k = 1.3

    def R(x, y, w, h):
        return pygame.Rect(int(cx + x * k), int(cy + y * k),
                           max(1, int(w * k)), max(1, int(h * k)))

    def P(x, y):
        return (int(cx + x * k), int(cy + y * k))
    rad = max(2, int(5 * k))
    # Exhaust curls from the tail (now the TOP -- behind the car).
    if running:
        pw = int(44 * k)
        puff = pygame.Surface((pw, pw), pygame.SRCALPHA)
        for i in range(3):
            pp = (t * 1.6 + i * 0.4) % 1.0
            pr = int((3 + pp * 8) * k)
            pa = int(55 * (1 - pp))
            if pa > 0:
                pygame.draw.circle(
                    puff, (90, 92, 96, pa),
                    (pw // 2 + int(math.sin(t * 2 + i) * 3),
                     pw - int((4 + pp * 26) * k)), pr)
        s.blit(puff, (int(cx - pw // 2), int(cy - 24 * k - pw // 2)))
    # Drop shadow.
    sh = pygame.Surface((int(46 * k), int(64 * k)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 110), sh.get_rect())
    s.blit(sh, (int(cx - 23 * k), int(cy - 32 * k)))
    # Hull -- sheen toward the BOTTOM now (the lamps face south).
    body = R(-13, -22, 26, 44)
    pygame.draw.rect(s, (26, 24, 30), body, border_radius=rad)
    pygame.draw.rect(s, (44, 42, 50), R(-13, 8, 26, 14), border_radius=rad)
    pygame.draw.rect(s, (9, 8, 11), body, 1, border_radius=rad)
    # Trunk (top), rear window, roof, windshield, hood (bottom).
    pygame.draw.rect(s, (24, 26, 32), R(-7, -13, 14, 5), border_radius=2)
    pygame.draw.rect(s, (40, 42, 50), R(-8, -7, 16, 12), border_radius=2)
    if dome > 0.02:
        dc = (int(196 * dome), int(166 * dome), int(108 * dome))
        pygame.draw.rect(s, dc, R(-4, -4, 8, 7), border_radius=2)
    wsh = (int(70 * light + 26), int(78 * light + 28), int(92 * light + 30))
    pygame.draw.polygon(s, wsh, [P(-7, 6), P(7, 6), P(9, 13), P(-9, 13)])
    pygame.draw.rect(s, (30, 28, 34), R(-11, 13, 22, 7), border_radius=2)
    # Mirrors.
    pygame.draw.rect(s, (24, 22, 28), R(-15, 6, 3, 3))
    pygame.draw.rect(s, (24, 22, 28), R(12, 6, 3, 3))
    # Headlights at the BOTTOM corners; taillights at the top (battery).
    hl = (int(235 * light), int(228 * light), int(190 * light))
    for hx in (-9, 9):
        pygame.draw.circle(s, hl, P(hx, 21), max(2, int(2 * k)))
        if light > 0.35:
            pygame.draw.circle(s, (255, 250, 230), P(hx, 21), max(1, int(k)))
    pygame.draw.rect(s, (150, 34, 26), R(-11, -21, 5, 3))
    pygame.draw.rect(s, (150, 34, 26), R(6, -21, 5, 3))
    pygame.draw.rect(s, (210, 70, 60), R(-10, -20, 2, 1))
    pygame.draw.rect(s, (210, 70, 60), R(7, -20, 2, 1))


def _sign_back(s, x, y, light, fonts_none=None):
    """The back of the BRIMLEY sign as it passes. Leaving, you only ever see
    the side they never painted.

    Its SHAPE has to agree with the board's front (`rendering/assemblies.py`
    `_town_sign`, and the drive-IN board in `ui/cutscenes.py`): same width,
    same two capped posts inset from the panel's ends. It is the same object
    seen from behind at the other end of the run, and it used to be a
    narrower rounded-corner board that matched neither. The back stays bare by
    design -- no frame, because the frame is on the front, and no lettering,
    because nobody ever painted this side.
    """
    def L(v):
        return (int(v[0] * light), int(v[1] * light), int(v[2] * light))
    bw, bh = 146, 48
    bx, by = x - bw // 2, y - bh
    for sgn in (-1, 1):
        fx = x + sgn * 52
        pygame.draw.polygon(s, L((70, 74, 80)), [
            (x + sgn * 38, by + 16), (x + sgn * 42, by + 16),
            (fx + sgn * 4, by + 78), (fx, by + 78)])
    # the star's plain back, still clearing the panel
    star = []
    for i in range(16):
        ang = -math.pi / 2 + i * math.pi / 8
        rr = 30 if i % 2 == 0 else 11
        star.append((x + math.cos(ang) * rr, by + 4 + math.sin(ang) * rr))
    pygame.draw.polygon(s, L((104, 84, 34)), star)
    pygame.draw.rect(s, L((84, 88, 96)), (bx - 4, by - 4, bw + 8, bh + 8))
    pygame.draw.rect(s, L((66, 70, 78)), (bx, by, bw, bh))
    pygame.draw.rect(s, L((34, 36, 40)), (bx, by, bw, bh), 2)
    # the sheet's ribs, and the plaque hanging blank underneath
    for i in range(5):
        sx = bx + 14 + i * 22
        pygame.draw.line(s, L((52, 56, 62)), (sx, by + 3), (sx, by + bh - 3), 1)
    pw2, ph2 = int(bw * 0.46), 15
    pygame.draw.rect(s, L((70, 74, 80)), (x - 3, by + bh, 6, 7))
    pygame.draw.rect(s, L((62, 66, 72)), (x - pw2 // 2, by + bh + 6, pw2, ph2))


def _exterior_road(s, t):
    W, H = s.get_size()
    cx = W // 2
    cy = int(H * 0.40)
    road_w = int(W * 0.42)
    # Right-hand traffic: heading south (down-screen, north at the top)
    # the car's lane is the WEST one -- the screen-left half of the road.
    car_x = cx - int(road_w * 0.21)
    scroll = _travelled(t)
    moving = _clamp01((t - (_ROAR_AT + 0.35)) / 1.6)

    # Headlights: dead until the roar, then bloom over ~0.4s. A faint
    # moonlit floor keeps the world legible before they wake.
    light = 0.30
    if t >= _ROAR_AT:
        light = 0.30 + 0.70 * _clamp01((t - _ROAR_AT) / 0.4)

    def L(c):
        return (int(c[0] * light), int(c[1] * light), int(c[2] * light))

    s.fill((10, 11, 10))                      # night earth
    rx0 = cx - road_w // 2
    rx1 = rx0 + road_w

    # The river behind (north -- the top edge): a still dark water band
    # with a few moving glints, sliding away once the car moves.
    riv_h = max(0, int(44 - scroll * 0.55))
    if riv_h > 2:
        pygame.draw.rect(s, (10, 14, 20), (0, 0, W, riv_h))
        for i in range(9):
            gx = int((i / 9) * W + math.sin(t * 0.8 + i * 2.2) * 14)
            ga = int(46 * (0.4 + 0.6 * math.sin(t * 1.3 + i)))
            if ga > 0:
                pygame.draw.line(s, (28 + ga // 3, 36 + ga // 3, 48 + ga // 2),
                                 (gx, riv_h - 4 - (i % 3)), (gx + 10, riv_h - 4 - (i % 3)), 1)

    # Shoulders + asphalt + paint.
    pygame.draw.rect(s, L((48, 45, 40)), (rx0 - 10, 0, 10, H))
    pygame.draw.rect(s, L((48, 45, 40)), (rx1, 0, 10, H))
    pygame.draw.rect(s, L((40, 38, 43)), (rx0, 0, road_w, H))
    pygame.draw.rect(s, L((118, 112, 90)), (rx0 + 4, 0, 2, H))
    pygame.draw.rect(s, L((118, 112, 90)), (rx1 - 6, 0, 2, H))
    # Centre dashes stream UP-screen (the world falls behind us).
    for kd in range(-1, H // 50 + 2):
        yy = int((kd * 50 + (-scroll)) % (H + 50)) - 25
        pygame.draw.rect(s, L((170, 160, 110)), (cx - 2, yy, 4, 26))

    # The corn -- both shoulders walled in, rows indexed in world space so
    # nothing shimmers as it scrolls. Each stalk: a stroke, a leaf nick,
    # a tassel.
    row_sp = 24
    lo = int((scroll - cy - 30) // row_sp) - 1
    hi = int((scroll + (H - cy) + 30) // row_sp) + 1
    cols = (list(range(10, rx0 - 14, 11))
            + list(range(rx1 + 16, W - 6, 11)))
    for ridx in range(lo, hi):
        yy = cy + ridx * row_sp - scroll
        if yy < -26 or yy > H + 8:
            continue
        for ci, xc in enumerate(cols):
            sd = (ridx * 73856093) ^ (ci * 19349663)
            f1 = _frand(sd & 0xffff)
            sx = xc + int(f1 * 7) - 3
            hgt = 10 + int(_frand(sd >> 3) * 7)
            shade = 0.55 + 0.45 * _frand(sd >> 6)
            lit = 0.55 + 0.85 * light
            col = (int(38 * shade * lit), int(52 * shade * lit),
                   int(26 * shade * lit))
            pygame.draw.line(s, col, (sx, int(yy)), (sx, int(yy) - hgt), 1)
            # one leaf nick + the tassel
            ly = int(yy) - hgt // 2
            pygame.draw.line(s, col, (sx, ly),
                             (sx + (3 if (sd & 1) else -3), ly - 2), 1)
            ty_ = int(yy) - hgt - 1
            if 0 <= ty_ < H and 0 <= sx < W:
                s.set_at((sx, ty_),
                         (int(74 * shade * lit), int(64 * shade * lit),
                          int(32 * shade * lit)))

    # A lonely power line down the west shoulder -- poles above the corn,
    # wire sagging span to span (the opening drive's line, on the way out).
    pole_sp, pole_x, ph_h = 240, rx0 - 26, 58

    def _attach(idx):
        return (pole_x + 10, cy + idx * pole_sp - int(scroll) - ph_h + 9)
    lo_i = int((scroll - cy) // pole_sp) - 3
    hi_i = int((scroll + (H - cy)) // pole_sp) + 2
    wire_c = L((46, 48, 52))
    for idx in range(lo_i, hi_i):
        ax, ay = _attach(idx)
        bx, by = _attach(idx + 1)
        if max(ay, by) < -70 or min(ay, by) > H + 70:
            continue
        pygame.draw.lines(s, wire_c, False,
                          [(ax, ay), ((ax + bx) // 2 + 6,
                                      (ay + by) // 2 + 9), (bx, by)], 1)
    for idx in range(lo_i, hi_i):
        yb = cy + idx * pole_sp - int(scroll)
        tp = yb - ph_h
        if tp > H + 20 or yb < -20:
            continue
        pf = max(0.0, 1.0 - abs(yb - cy) / 220.0)
        pc = (int(38 + 40 * pf * light), int(34 + 32 * pf * light),
              int(28 + 22 * pf * light))
        pygame.draw.rect(s, pc, (pole_x - 2, tp, 4, ph_h))
        pygame.draw.rect(s, pc, (pole_x - 11, tp + 6, 22, 3))
        pygame.draw.rect(s, pc, (pole_x - 2, tp - 4, 4, 6))

    # Reflector posts on both shoulders, flaring where the beam reaches.
    post_sp = 150
    for idx in range(int((scroll - cy) // post_sp) - 3,
                     int((scroll + (H - cy)) // post_sp) + 2):
        py = cy + idx * post_sp - int(scroll)
        if py < -10 or py > H + 10:
            continue
        rf = max(0.0, 1.0 - abs(py - (cy + 170)) / 190.0)
        for postx in (rx0 - 13, rx1 + 13):
            pygame.draw.rect(s, L((58, 54, 46)), (postx - 1, py - 14, 2, 14))
            ac = (int(100 + 150 * rf * light), int(70 + 96 * rf * light),
                  int(16 + 28 * rf))
            pygame.draw.circle(s, ac, (postx, py - 13), 2)

    # A farmhouse set back in the corn on the west side, one window lit.
    # The light goes out as the car comes level: the town shutting its
    # eyes on the way out.
    fy = cy + 420 - scroll
    if -90 <= fy <= H + 90:
        fx = rx0 - 96
        wall = (int(30 * light + 8), int(27 * light + 8), int(24 * light + 8))
        roof = (int(20 * light + 5), int(18 * light + 5), int(16 * light + 5))
        pygame.draw.rect(s, wall, (fx - 30, int(fy) - 26, 60, 26))
        pygame.draw.polygon(s, roof, [(fx - 34, int(fy) - 26),
                                      (fx, int(fy) - 46),
                                      (fx + 34, int(fy) - 26)])
        if fy > cy + 36:                          # still ahead: the lamp burns
            pygame.draw.rect(s, (216, 168, 92), (fx + 8, int(fy) - 18, 7, 8))
            _yk_radial(s, fx + 11, int(fy) - 14, 10, (216, 168, 92), 70,
                       add=False)
        else:                                     # come level: it goes dark
            pygame.draw.rect(s, (14, 12, 10), (fx + 8, int(fy) - 18, 7, 8))

    # The back of the BRIMLEY sign passes on the east shoulder.
    sy = cy + 700 - scroll
    if -70 <= sy <= H + 70:
        flare = max(0.35, 1.0 - abs(sy - (cy + 130)) / 260.0)
        _sign_back(s, rx1 + 30, int(sy), light * flare)

    # Far ahead (the bottom of the frame): the fold's edge as a thin gold
    # shimmer across the road -- never reached in this shot.
    if t > SPREAD_T_DRIVE + 1.2:
        ea = _clamp01((t - SPREAD_T_DRIVE - 1.2) / 1.5)
        gy = int(H * 0.93)
        glow = pygame.Surface((road_w + 40, 14), pygame.SRCALPHA)
        a = int(46 * ea * (0.45 + 0.55 * math.sin(t * 2.1)))
        if a > 0:
            pygame.draw.line(glow, (*_YK_GOLD, a), (0, 7), (road_w + 40, 7), 2)
            for gk in range(6):
                gxx = int(_frand(gk * 7 + int(t * 3)) * (road_w + 40))
                pygame.draw.line(glow, (*_YK_HOT, a), (gxx, 3), (gxx, 11), 1)
            s.blit(glow, (rx0 - 20, gy))

    # Headlight beam thrown DOWN the road ahead (south) + bumper hotspot.
    if light > 0.25:
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        front = cy + 30
        span = int(H * 0.46)
        slices = 46
        eh = span // slices * 3 + 4
        for i in range(slices, -1, -1):
            f = i / slices
            y = front + int(f * span)
            half = int(13 + f * f * road_w * 0.46)
            b = (1 - f) ** 1.8 * light
            col = (min(255, int(172 * b)), min(255, int(148 * b)),
                   min(255, int(102 * b)))
            if col[0] + col[1] + col[2] > 3:
                pygame.draw.ellipse(glow, col,
                                    (car_x - half, y - eh // 2, 2 * half, eh))
        for i in range(12, 0, -1):
            f = i / 12
            rw, rh = int(38 * f) + 3, int(52 * f) + 3
            hb = (1 - f) ** 1.3 * light
            col = (min(255, int(206 * hb)), min(255, int(192 * hb)),
                   min(255, int(146 * hb)))
            if col[0] + col[1] + col[2] > 3:
                pygame.draw.ellipse(glow, col,
                                    (car_x - rw, (front + 34) - rh // 2,
                                     2 * rw, rh))
        s.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # THE GOLD WAKE -- the trailing King, as particles only. A stream of
    # gold motes pulled out of Brimley behind the car, fanning as it
    # falls back, never gaining, never a body.
    if moving > 0.05:
        wake = pygame.Surface((W, H), pygame.SRCALPHA)
        tail_y = cy - 32
        reach = tail_y + 50
        for i in range(42):
            spd = 0.7 + 0.6 * _frand(i * 3 + 1)
            p = (t * 0.55 * spd + _frand(i * 5 + 2)) % 1.0
            yy = tail_y - p * reach
            fan = (6 + p * 52) * (1 if (i & 1) else -1)
            xx = car_x + int(math.sin(t * 1.7 + i * 1.31) * 5
                             + fan * _frand(i * 7 + 3))
            a = int(210 * (1 - p) * moving)
            if a <= 0:
                continue
            r = 1 + (1 if _frand(i * 11) > 0.62 else 0)
            pygame.draw.circle(wake, (*_YK_GOLD, a), (xx, int(yy)), r)
            if _frand(i * 13) > 0.55:                 # a short falling streak
                pygame.draw.line(wake, (*_YK_HOT, int(a * 0.7)),
                                 (xx, int(yy)), (xx, int(yy) + 9), 1)
        # a soft smear right at the tail, the stream's root
        _yk_radial(wake, car_x, tail_y - 6, 22, _YK_GOLD, int(46 * moving))
        s.blit(wake, (0, 0))

    # The mask riding shotgun, seen from outside: one breathing gold
    # glint through the cabin glass, right side. There before the engine.
    ga = int(60 * (0.45 + 0.55 * math.sin(t * 1.7)))
    glint = pygame.Surface((26, 26), pygame.SRCALPHA)
    _yk_radial(glint, 13, 13, 6, _YK_GOLD, ga)
    s.blit(glint, (car_x + 7 - 13, cy + 2 - 13))

    # The car, dead still then running. The dome light blinks on with
    # the key and dies once the engine holds -- something to watch in
    # the dark beat before the roar.
    dome = 0.0
    if _KEY_AT <= t < _ROAR_AT + 0.8:
        dome = (_clamp01((t - _KEY_AT) / 0.12)
                * _clamp01((_ROAR_AT + 0.8 - t) / 0.5))
    _car_topdown_south(s, car_x, cy, light, t, running=(t >= _ROAR_AT),
                       dome=dome)


# ---------------------------------------------------------------------------
# Beats C + D -- inside the cab: the mask on the passenger seat.
# ---------------------------------------------------------------------------

def _cab_interior(s, t):
    W, H = s.get_size()
    cab = pygame.Surface((W, H))
    tc = t - SPREAD_T_SHIFT
    dp = _clamp01((t - SPREAD_T_GAZE) / BEAT_GAZE)        # gaze progress
    crossed = t >= SPREAD_CROSS_AT

    vpx, vpy = int(W * 0.50), int(H * 0.30)
    dash_y = int(H * 0.64)

    # Night sky + a thin scatter of stars through the windshield.
    cab.fill((8, 9, 14))
    for i in range(16):
        sx = int(_frand(i * 3 + 1) * W)
        sy = int(_frand(i * 3 + 2) * (vpy - 14))
        tw = 0.5 + 0.5 * math.sin(t * 1.4 + i * 1.7)
        c = int(120 * _frand(i * 3 + 3) * tw)
        if c > 8:
            cab.set_at((sx, sy), (c, c, int(c * 1.1)))

    # A low waning moon through the glass, riding the corn tops.
    mx_, my_ = int(W * 0.36), int(H * 0.13)
    pygame.draw.circle(cab, (172, 176, 184), (mx_, my_), 9)
    pygame.draw.circle(cab, (8, 9, 14), (mx_ - 4, my_ - 3), 8)

    # The ground plane rushing under the lights.
    for band, (y0, y1, col) in enumerate((
            (vpy, int(H * 0.46), (17, 17, 16)),
            (int(H * 0.46), int(H * 0.56), (24, 23, 21)),
            (int(H * 0.56), dash_y + 6, (33, 31, 28)))):
        pygame.draw.rect(cab, col, (0, y0, W, y1 - y0))

    if not crossed:
        # The corn pressing in on both sides -- two ragged dark masses
        # converging on the vanishing point, a moonlit rim along their
        # tops so they read against the night.
        for side in (-1, 1):
            top_pts = []
            n = 7
            for k in range(n + 1):
                f = k / n
                x = _lerp(vpx + side * 52, W * (0.5 + side * 0.62), f)
                bump = math.sin(t * 2.0 + k * 2.1 + side) * 2.0
                yt = _lerp(vpy - 2, vpy - 58, f) - _frand(k * 5 + side) * 10 + bump
                top_pts.append((int(x), int(yt)))
            pts = ([(vpx + side * 46, vpy + 4)] + top_pts
                   + [(int(W * (0.5 + side * 0.62)), dash_y + 30),
                      (vpx + side * 46, vpy + 10)])
            pygame.draw.polygon(cab, (14, 19, 11), pts)
            pygame.draw.lines(cab, (34, 44, 24), False, top_pts, 1)
    else:
        # South of the fold: the corn is simply gone. Open dark, and the
        # first colour -- a low warm seam on the horizon.
        seam = pygame.Surface((W, 26), pygame.SRCALPHA)
        for r in range(26):
            a = int(40 * (1 - r / 26) ** 1.6)
            pygame.draw.line(seam, (214, 150, 70, a), (0, r), (W, r))
        cab.blit(seam, (0, vpy - 4))

    # Road edges + centre dashes streaking at the glass. Right-hand
    # traffic: the car rides the west lane, so the centreline streams
    # past on the DRIVER'S LEFT and the near road edge sits off right.
    edge_c = (78, 74, 58)
    pygame.draw.line(cab, edge_c, (vpx - 8, vpy + 2), (-int(W * 0.04), dash_y + 36), 2)
    pygame.draw.line(cab, edge_c, (vpx + 8, vpy + 2), (int(W * 0.96), dash_y + 36), 2)
    tx, ty = int(W * 0.27), int(H * 0.92)
    for k in range(8):
        q = (t * 1.05 + k / 8.0) % 1.0
        qq = q ** 1.8
        x = int(_lerp(vpx, tx, qq))
        y = int(_lerp(vpy, ty, qq))
        wd = 1 + int(9 * qq)
        hg = 2 + int(22 * qq)
        a = int(200 * q)
        dash = pygame.Surface((wd, hg), pygame.SRCALPHA)
        dash.fill((176, 166, 116, a))
        cab.blit(dash, (x - wd // 2, y))
    # Reflector posts whipping by on the right.
    for j in range(2):
        q = (t * 0.85 + j / 2.0) % 1.0
        qq = q ** 2.0
        x = int(_lerp(vpx + 14, W * 0.93, qq))
        y = int(_lerp(vpy + 2, dash_y - 4, qq))
        a = int(190 * q)
        if a > 12:
            pygame.draw.circle(cab, (110 + a // 3, 80 + a // 4, 26), (x, y),
                               1 + int(2 * qq))

    # ---- The crossing: the fold's frame sweeps past the glass, and the
    # PI's eyes are on the seat. Two gold uprights blow outward from the
    # vanishing point and are gone; the world does not flinch. ----
    pr = (t - (SPREAD_CROSS_AT - 0.25)) / 0.65
    if 0.0 <= pr <= 1.0:
        xoff = int((pr ** 1.6) * W * 0.58)
        a = int(200 * (1 - pr))
        wash = pygame.Surface((W, H), pygame.SRCALPHA)
        wd = 2 + int(8 * pr)
        for side in (-1, 1):
            x = vpx + side * max(8, xoff)
            pygame.draw.line(wash, (*_YK_GOLD, a), (x, int(H * 0.05)),
                             (x, dash_y + 30), wd)
            pygame.draw.line(wash, (*_YK_HOT, min(255, a + 30)),
                             (x, int(H * 0.05)), (x, dash_y + 30),
                             max(1, wd // 3))
        cab.blit(wash, (0, 0))
        ga = int(56 * math.sin(math.pi * _clamp01(pr)))
        if ga > 0:
            veil = pygame.Surface((W, H))
            veil.fill(_YK_GOLD)
            veil.set_alpha(ga)
            cab.blit(veil, (0, 0))

    # ---- Cab furniture ----
    # Roof + A-pillars.
    pygame.draw.rect(cab, (10, 9, 11), (0, 0, W, int(H * 0.075)))
    pygame.draw.polygon(cab, (11, 10, 12),
                        [(0, 0), (int(W * 0.085), 0),
                         (int(W * 0.015), dash_y), (0, dash_y)])
    pygame.draw.polygon(cab, (11, 10, 12),
                        [(W, 0), (int(W * 0.915), 0),
                         (int(W * 0.985), dash_y), (W, dash_y)])
    # The rearview mirror -- and in it, the gold wake still trailing.
    mw, mh = int(W * 0.13), int(H * 0.052)
    mx0, my0 = int(W * 0.5 - mw / 2), int(H * 0.085)
    pygame.draw.rect(cab, (12, 11, 13), (int(W * 0.5) - 2, int(H * 0.07), 4, 12))
    pygame.draw.rect(cab, (16, 15, 18), (mx0 - 2, my0 - 2, mw + 4, mh + 4),
                     border_radius=4)
    pygame.draw.rect(cab, (6, 6, 8), (mx0, my0, mw, mh), border_radius=3)
    if not crossed:
        mirr = pygame.Surface((mw, mh), pygame.SRCALPHA)
        for i in range(7):
            p = (t * 0.8 + _frand(i * 5 + 1)) % 1.0
            xx = int(mw * 0.5 + math.sin(t * 1.5 + i * 1.4) * mw * 0.16
                     + (p - 0.5) * 6)
            yy = int(mh * 0.82 - p * mh * 0.7)
            a = int(130 * (1 - p))
            if a > 0:
                pygame.draw.circle(mirr, (*_YK_GOLD, a), (xx, yy), 1)
        _yk_radial(mirr, mw // 2, int(mh * 0.8), 5, _YK_GOLD, 40)
        cab.blit(mirr, (mx0, my0))

    # Dashboard + instruments + the wheel.
    pygame.draw.rect(cab, (17, 16, 19), (0, dash_y, W, H - dash_y))
    pygame.draw.line(cab, (42, 40, 46), (0, dash_y), (W, dash_y), 2)
    pygame.draw.line(cab, (28, 26, 30), (0, dash_y + 14), (W, dash_y + 14), 1)
    icx, icy = int(W * 0.27), dash_y + int(H * 0.075)
    for gi, gx in enumerate((icx - 34, icx + 34)):
        pygame.draw.circle(cab, (10, 9, 11), (gx, icy), 20)
        pygame.draw.circle(cab, (52, 44, 30), (gx, icy), 20, 2)
        ndl = t * (0.6 + gi * 0.3)
        ang = math.pi * (0.75 + 0.1 * math.sin(ndl))
        pygame.draw.line(cab, (208, 150, 70), (gx, icy),
                         (gx + int(math.cos(ang) * 14),
                          icy - int(math.sin(ang) * 14)), 1)
        _yk_radial(cab, gx, icy, 14, (208, 150, 70), 60, add=False)
    # Steering wheel: the top arc, with the column behind it.
    pygame.draw.rect(cab, (13, 12, 14),
                     (int(W * 0.26), H - int(H * 0.10), int(W * 0.08), int(H * 0.10)))
    wheel = pygame.Rect(0, 0, int(W * 0.34), int(H * 0.42))
    wheel.center = (int(W * 0.30), int(H * 1.06))
    pygame.draw.ellipse(cab, (30, 26, 27), wheel, 10)
    pygame.draw.line(cab, (26, 22, 23), (wheel.centerx - int(W * 0.10), wheel.centery - int(H * 0.10)),
                     (wheel.centerx, wheel.centery - int(H * 0.02)), 7)
    pygame.draw.line(cab, (26, 22, 23), (wheel.centerx + int(W * 0.10), wheel.centery - int(H * 0.10)),
                     (wheel.centerx, wheel.centery - int(H * 0.02)), 7)

    # The passenger seat, and on it THE MASK.
    seat = pygame.Rect(int(W * 0.655), int(H * 0.455), int(W * 0.315), int(H * 0.55))
    pygame.draw.rect(cab, (21, 18, 21), seat, border_radius=26)
    pygame.draw.rect(cab, (32, 28, 32), seat, 2, border_radius=26)
    pygame.draw.line(cab, (14, 12, 14), (seat.centerx, seat.top + 18),
                     (seat.centerx, seat.bottom - 12), 2)
    pygame.draw.line(cab, (14, 12, 14), (seat.left + 14, seat.top + int(H * 0.16)),
                     (seat.right - 14, seat.top + int(H * 0.16)), 2)

    maskx, masky = int(W * 0.815), int(H * 0.625)
    r = 46
    # The shift: it rides facing the road, then turns to the driver.
    if tc < 1.2:
        tilt = -9.0
    elif tc < 2.6:
        f = (tc - 1.2) / 1.4
        f = f * f * (3 - 2 * f)                            # smoothstep
        tilt = _lerp(-9.0, 7.5, f)
    else:
        tilt = 7.5 + 0.6 * math.sin(t * 1.1)
    # A faint pool of dash-light under it on the seat; the only glow the
    # mask itself gives off is what wakes in the sockets.
    _yk_radial(cab, maskx, masky + 10, int(r * 1.1),
               (208, 170, 90), 26 + int(30 * dp), add=False)
    msurf = _pallid_mask(r, dp)
    rot = pygame.transform.rotozoom(msurf, tilt, 1.0)
    cab.blit(rot, rot.get_rect(center=(maskx, masky)))

    # ---- The push-in: the frame eases toward the sockets as he gazes,
    # close enough to fill the view with bone and shadow, never so close
    # it breaks into a blur. ----
    if dp > 0.001:
        z = 1.0 + 0.62 * (dp * dp * (3 - 2 * dp))
        w2, h2 = int(W / z), int(H / z)
        fx = _lerp(W / 2, maskx, dp)
        fy = _lerp(H / 2, masky - r * 0.3, dp)
        x0 = int(max(0, min(W - w2, fx - w2 / 2)))
        y0 = int(max(0, min(H - h2, fy - h2 / 2)))
        view = cab.subsurface((x0, y0, w2, h2))
        s.blit(pygame.transform.smoothscale(view, (W, H)), (0, 0))
    else:
        s.blit(cab, (0, 0))


# ---------------------------------------------------------------------------
# Beats E + F + G -- the open south: the flood, the drive on, the verdict.
# ---------------------------------------------------------------------------

def _car_profile(s, x, gy, light, t, idle, k=1.15, rim=0.0):
    """The car in profile, facing RIGHT (south), wheels on `gy`. `rim`
    (0..1) lays the horizon's gold along the hull as the colour floods
    in, so the car holds its shape against the dark road."""
    jy = int(round(math.sin(t * 22.0) * idle * 1.2))
    y = gy + jy
    # idle exhaust drifting back-left
    if idle > 0.05:
        for i in range(3):
            pp = (t * 1.2 + i * 0.43) % 1.0
            pa = int(60 * (1 - pp) * idle)
            if pa > 0:
                ex = int(x - 50 * k - pp * 26)
                ey = int(y - 10 * k - pp * 9)
                pr = 2 + int(pp * 6)
                puff = pygame.Surface((pr * 2 + 2, pr * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(puff, (90, 92, 96, pa), (pr + 1, pr + 1), pr)
                s.blit(puff, (ex - pr, ey - pr))
    # shadow
    sh = pygame.Surface((int(104 * k), int(14 * k)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 120), sh.get_rect())
    s.blit(sh, (int(x - 52 * k), int(gy - 5 * k)))
    # headlight cone thrown right
    if light > 0.05:
        cone = pygame.Surface((s.get_width(), s.get_height()), pygame.SRCALPHA)
        for i in range(14, 0, -1):
            f = i / 14
            b = (1 - f) ** 1.7 * light
            col = (min(255, int(150 * b)), min(255, int(128 * b)),
                   min(255, int(86 * b)))
            if col[0] + col[1] + col[2] > 3:
                ln = int(30 + f * 250 * k)
                hh = int(5 + f * 30 * k)
                pygame.draw.ellipse(cone, col,
                                    (int(x + 40 * k), int(y - 18 * k - hh // 2),
                                     ln, hh))
        s.blit(cone, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    # hull + cabin
    hull = pygame.Rect(int(x - 46 * k), int(y - 26 * k), int(92 * k), int(20 * k))
    pygame.draw.rect(s, (26, 24, 30), hull, border_radius=int(6 * k))
    pygame.draw.rect(s, (9, 8, 11), hull, 1, border_radius=int(6 * k))
    cabin = [(int(x - 26 * k), int(y - 26 * k)), (int(x - 13 * k), int(y - 40 * k)),
             (int(x + 17 * k), int(y - 40 * k)), (int(x + 30 * k), int(y - 26 * k))]
    pygame.draw.polygon(s, (24, 22, 27), cabin)
    pygame.draw.polygon(s, (9, 8, 11), cabin, 1)
    if rim > 0.02:
        rc = (int(150 * rim), int(118 * rim), int(64 * rim))
        pygame.draw.line(s, rc, (int(x - 44 * k), int(y - 27 * k)),
                         (int(x + 44 * k), int(y - 27 * k)), 2)
        pygame.draw.line(s, rc, (int(x - 12 * k), int(y - 41 * k)),
                         (int(x + 16 * k), int(y - 41 * k)), 2)
    win = [(int(x - 21 * k), int(y - 27 * k)), (int(x - 11 * k), int(y - 38 * k)),
           (int(x + 14 * k), int(y - 38 * k)), (int(x + 25 * k), int(y - 27 * k))]
    pygame.draw.polygon(s, (38, 42, 52), win)
    pygame.draw.line(s, (16, 15, 18), (int(x + 1 * k), int(y - 38 * k)),
                     (int(x + 1 * k), int(y - 27 * k)), 2)
    # a gold breath in the cabin glass -- the passenger, still riding
    ga = int(46 * (0.45 + 0.55 * math.sin(t * 1.7)))
    gl = pygame.Surface((22, 22), pygame.SRCALPHA)
    _yk_radial(gl, 11, 11, 5, _YK_GOLD, ga)
    s.blit(gl, (int(x + 8 * k) - 11, int(y - 33 * k) - 11))
    # wheels
    for wx in (x - 28 * k, x + 27 * k):
        pygame.draw.circle(s, (12, 12, 14), (int(wx), int(gy - 7 * k)), int(9 * k))
        pygame.draw.circle(s, (52, 52, 58), (int(wx), int(gy - 7 * k)), int(3 * k))
    # lamps
    pygame.draw.circle(s, (int(240 * max(0.3, light)), int(230 * max(0.3, light)),
                           int(190 * max(0.3, light))),
                       (int(x + 45 * k), int(y - 18 * k)), max(2, int(2 * k)))
    pygame.draw.rect(s, (170, 40, 30),
                     (int(x - 48 * k), int(y - 20 * k), int(3 * k), int(4 * k)))


def _open_south(s, t):
    W, H = s.get_size()
    te = t - SPREAD_T_FLOOD
    flood = _clamp01(te / (BEAT_FLOOD * 0.85))
    flood = flood * flood * (3 - 2 * flood)
    horizon = int(H * 0.46)

    # Sky: the first sky of the cutscene, arriving in colour.
    top0, top1 = (9, 10, 16), (58, 40, 66)
    hor0, hor1 = (18, 17, 26), (228, 162, 80)
    top_c = _lerpc(top0, top1, flood)
    hor_c = _lerpc(hor0, hor1, flood)
    step = 4
    for y in range(0, horizon, step):
        f = (y / max(1, horizon)) ** 1.25
        pygame.draw.rect(s, _lerpc(top_c, hor_c, f), (0, y, W, step))

    # The spread's arrival clock -- the ground bank and the sky
    # sickness share one front, rolling in from the north (frame left).
    fog_t = t - (SPREAD_T_ON + 2.4)
    front = (W * 1.25 * (_clamp01(fog_t / 8.0) ** 0.85)
             if fog_t > 0.0 else 0.0)
    sky_front = front * 1.12          # the sky sickens a step ahead

    # Stars above, drowning as the gold floods in -- then smothered
    # outright as the sickness crawls over them. Two of them hold:
    # steady, faintly warm, not stars.
    sick = _clamp01((t - (SPREAD_T_KNOW - 0.6)) / 3.0)
    for i in range(26):
        sx_ = int(_frand(i * 5 + 1) * W)
        sy_ = int((_frand(i * 5 + 2) ** 1.4) * horizon * 0.72)
        tw = 0.55 + 0.45 * math.sin(t * 1.5 + i * 1.9)
        dim = 1.0 - flood * 0.88
        if i < 2:                                # the pair that stays
            tw, dim = 1.0, max(0.45, 1.0 - flood * 0.5)
        elif sky_front > sx_:                    # the haze has reached it
            dim *= 0.3
        a = 150 * _frand(i * 5 + 3) * tw * dim
        if a > 8:
            c = int(a)
            col = ((int(c * 1.05), c, int(c * 0.72)) if i < 2
                   else (c, c, min(255, int(c * 1.08))))
            pygame.draw.circle(s, col, (sx_, sy_), 1)

    # Cloud shelves -- thin lenses riding the upper sky. Their
    # undersides catch the arriving gold, then go pale as the fog
    # ruins the dawn.
    for ci, (cyf, cxf, cwf, drift) in enumerate(
            ((0.10, 0.30, 0.36, 7.0), (0.17, 0.68, 0.27, -5.0),
             (0.06, 0.78, 0.20, 3.0), (0.25, 0.16, 0.24, -3.0))):
        cw_ = int(W * cwf)
        ch_ = max(5, int(cw_ * 0.065))
        cx_ = int(W * cxf + math.sin(t * 0.05 + ci * 2.1) * drift)
        cy_ = int(H * cyf)
        csick = _clamp01((sky_front - (cx_ - cw_ * 0.5)) / max(40, cw_))
        body = _lerpc(_lerpc((22, 21, 29), (88, 58, 66), flood),
                      (132, 138, 124), 0.85 * csick)
        lit = _lerpc(_lerpc((30, 29, 37), (236, 176, 96), flood),
                     (176, 182, 164), 0.95 * csick)
        pygame.draw.ellipse(s, body, (cx_ - cw_ // 2, cy_ - ch_ // 2,
                                      cw_, ch_))
        pygame.draw.ellipse(s, body, (cx_ - cw_ // 3, cy_ - ch_,
                                      int(cw_ * 0.52), ch_))
        pygame.draw.ellipse(s, lit, (cx_ - cw_ // 2, cy_ + ch_ // 2 - 2,
                                     cw_, 3))

    # THE SICKNESS IN THE SKY -- the spread is not a ground fog alone.
    # A pale haze crawls across the dome itself: mare's-tail streamers
    # running ahead, a ragged-edged veil filling in behind them,
    # smothering what it crosses. Low-res + smoothscale = vapour.
    if sky_front > 0.0:
        vsc = 0.25
        vw, vh = int(W * vsc), int(H * vsc)
        veil = pygame.Surface((vw, vh), pygame.SRCALPHA)
        vpale = (164, 178, 152)
        fl = sky_front * vsc
        hz = horizon * vsc
        pts = [(-8, 0)]                          # the veil, ragged edge
        yv = 0.0
        while yv < hz:
            xe = fl - (_frand(int(yv // 4) * 13) * 30
                       + math.sin(t * 0.4 + yv * 0.5) * 9) * vsc * 4
            pts.append((int(max(-8, xe)), int(yv)))
            yv += 4
        pts.append((-8, int(hz)))
        pygame.draw.polygon(veil, (*vpale, 48), pts)
        for k in range(8):                       # the streamers, leading
            sy_ = int((_frand(k * 19 + 3) ** 1.2) * hz * 0.92)
            tipx = fl + (30 + _frand(k * 23) * 110) * vsc
            lnw = (110 + _frand(k * 29) * 170) * vsc
            if tipx <= 0:
                continue
            ehh = max(2, int(2 + _frand(k * 31) * 3))
            av = int(38 + _frand(k * 37) * 30)
            yy_ = sy_ + math.sin(t * 0.5 + k * 1.7) * 2
            pygame.draw.ellipse(veil, (*vpale, av),
                                (int(tipx - lnw), int(yy_ - ehh / 2),
                                 int(lnw), ehh))
        s.blit(pygame.transform.smoothscale(veil, (W, H)), (0, 0))

    # A thin flock crossing south, the way he went -- everything that
    # can leave is leaving.
    bt = t - (SPREAD_T_ON + 1.2)
    if 0.0 < bt < 9.0:
        prog = bt / 9.0
        for bi in range(7):
            bx = int(W * (-0.06 + prog * 1.2) + _frand(bi * 3) * 90 - bi * 26)
            by_ = int(H * 0.13 + _frand(bi * 7) * H * 0.07
                      + math.sin(t * 2.2 + bi) * 3)
            if not (6 <= bx < W - 6):
                continue
            flap = int(math.sin(t * 7.0 + bi * 1.4) * 3)
            pygame.draw.lines(s, (16, 14, 16), False,
                              [(bx - 4, by_ - flap), (bx, by_),
                               (bx + 4, by_ - flap)], 1)

    # The glow on the horizon -- gold, breathing (beat G) like the light
    # under the dream-door.
    sunx = int(W * 0.76)
    if t >= SPREAD_T_KNOW:
        pulse = 0.62 + 0.38 * (0.5 + 0.5 * math.sin(t * 1.7))
    else:
        pulse = 1.0
    # A steady seam of light along the horizon, then the glow breathing
    # over it.
    if flood > 0.02:
        seam = pygame.Surface((W, 18), pygame.SRCALPHA)
        for r in range(18):
            a = int(54 * flood * (1 - r / 18) ** 1.5)
            pygame.draw.line(seam, (*_YK_GOLD, a), (0, r), (W, r))
        s.blit(seam, (0, horizon - 16))
    _yk_radial(s, sunx, horizon, int(W * 0.13),
               _YK_GOLD, int(190 * flood * pulse), add=False)
    _yk_radial(s, sunx, horizon, int(W * 0.05),
               _YK_HOT, int(170 * flood * pulse), add=False)

    # Far treeline + the ground plane.
    pygame.draw.rect(s, _lerpc((10, 11, 10), (30, 24, 22), flood),
                     (0, horizon - 3, W, 5))
    pygame.draw.rect(s, _lerpc((12, 12, 13), (52, 40, 30), flood),
                     (0, horizon + 2, W, H - horizon))

    # The road south, running across the frame.
    ry0, rh = int(H * 0.66), int(H * 0.15)
    pygame.draw.rect(s, _lerpc((24, 24, 27), (44, 40, 42), flood),
                     (0, ry0 - 8, W, 8))                       # gravel shoulder
    pygame.draw.rect(s, _lerpc((30, 30, 34), (58, 52, 54), flood),
                     (0, ry0, W, rh))
    pygame.draw.rect(s, _lerpc((24, 24, 27), (44, 40, 42), flood),
                     (0, ry0 + rh, W, 8))
    edge = _lerpc((70, 66, 52), (150, 138, 104), flood)
    pygame.draw.line(s, edge, (0, ry0 + 3), (W, ry0 + 3), 2)
    pygame.draw.line(s, edge, (0, ry0 + rh - 4), (W, ry0 + rh - 4), 2)
    dash_c = _lerpc((96, 90, 64), (190, 176, 122), flood)
    for x in range(-30, W + 40, 70):
        pygame.draw.rect(s, dash_c, (x, ry0 + rh // 2 - 1, 28, 3))

    # The car: stopped and overcome (E), pulling away (F), gone (G).
    gy = ry0 + rh - 12
    if t < SPREAD_T_ON:
        amp = math.sin(math.pi * _clamp01((te - 1.0) / 5.2))
        _car_profile(s, W * 0.40, gy, 0.9, t, idle=0.35 + 0.65 * amp,
                     rim=flood)
    elif t < SPREAD_T_KNOW:
        tf = t - SPREAD_T_ON
        f = _clamp01(tf / 4.8)
        x = W * 0.40 + (W * 0.78) * (f ** 1.7)
        if x < W + 80:
            _car_profile(s, x, gy, 0.9, t, idle=0.0, rim=1.0)

    # THE FOG -- pale and sickly, cresting from the north (frame left)
    # on the car's heels and rolling south down the road it took. It
    # smothers the gold layer by layer until the dawn is ruined: the
    # spread, already arriving. Thin fingers run out ahead of the bank
    # along the asphalt, reaching after him.
    if front > 0.0:
        # Built at quarter resolution and smoothscaled up, so the banks
        # blur into vapour instead of hard terraces.
        sc = 0.25
        fw_, fh_ = int(W * sc), int(H * sc)
        fog = pygame.Surface((fw_, fh_), pygame.SRCALPHA)
        pale = (160, 176, 150)
        layers = ((horizon - 32, 54, 56), (horizon - 10, 66, 80),
                  (horizon + 16, 80, 100), (ry0 - 6, rh + 34, 116))
        for li, (by, depth, alpha) in enumerate(layers):
            fl = (front - li * 60) * sc
            if fl <= 0:
                continue
            byl, dl = by * sc, depth * sc
            pts = [(-10, int(byl + dl))]
            x = -10.0
            while x < fl:
                ytop = (byl + math.sin(t * 0.5 + x * 0.05 + li * 1.9) * 2.4
                        + _frand(li * 31 + int(x // 7)) * 2.4)
                pts.append((int(x), int(ytop)))
                x += 7
            pts.append((int(fl), int(byl + dl * 0.5)))      # the bank's nose
            pts.append((int(fl), int(byl + dl)))
            pygame.draw.polygon(fog, (*pale, alpha), pts)
            for k in range(8):                   # ragged puffs along the top
                px = fl - k * 9 - _frand(li * 9 + k) * 6
                if px < 0:
                    continue
                pr = 3 + int(_frand(li * 13 + k) * 4)
                pa = int(alpha * (0.45 + 0.4 * _frand(li * 17 + k)))
                py_ = byl + math.sin(t * 0.6 + k * 1.7 + li) * 2
                pygame.draw.circle(fog, (*pale, pa), (int(px), int(py_)), pr)
        for k in range(3):                       # the fingers, on the road
            fx = (front + 40 + k * 90 + _frand(k * 7) * 40) * sc
            if fx > fw_ + 16:
                continue
            fwl = int((90 + _frand(k * 9) * 60) * sc)
            fhl = max(2, int((10 + _frand(k * 11) * 8) * sc))
            fyk = (ry0 + rh // 2 + math.sin(t * 0.7 + k * 2) * 6 + k * 9 - 9) * sc
            pygame.draw.ellipse(fog, (*pale, 70),
                                (int(fx - fwl), int(fyk - fhl / 2), fwl, fhl))
        s.blit(pygame.transform.smoothscale(fog, (W, H)), (0, 0))
        # The sun, reduced to a pale smudge behind the haze.
        if front > sunx:
            _yk_radial(s, sunx, horizon, int(W * 0.045),
                       (214, 206, 178), int(46 * pulse), add=False)


# ---------------------------------------------------------------------------
# Shared film grade + the master entry point.
# ---------------------------------------------------------------------------

_GRAIN = None
_VIG = None


def _post(surf, t, warmth, sick=0.0):
    """The cutscene grade: chunky downsample, a tint that thaws from the
    cold night grade to gold as the flood lands -- then SICKENS toward a
    pale grey-green as the fog claims the verdict (`sick` 0..1) -- with
    emulsion grain, a gate flicker, crushed edges."""
    global _GRAIN, _VIG
    w, h = surf.get_size()
    dw, dh = int(w / 1.5), int(h / 1.5)
    surf.blit(pygame.transform.scale(
        pygame.transform.smoothscale(surf, (dw, dh)), (w, h)), (0, 0))
    tint = pygame.Surface((w, h))
    base = _lerpc((200, 210, 228), (255, 238, 205), warmth)
    tint.fill(_lerpc(base, (202, 212, 190), 0.75 * sick))
    surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    if _GRAIN is None:
        g = pygame.Surface((w, h), pygame.SRCALPHA)
        rg = random.Random(31)
        for _ in range(int(w * h * 0.055)):
            x, y = rg.randint(0, w - 1), rg.randint(0, h - 1)
            if rg.random() < 0.6:
                v = rg.randint(0, 30)
                g.set_at((x, y), (v, v, v, rg.randint(30, 70)))
            else:
                v = rg.randint(120, 190)
                g.set_at((x, y), (v, v, int(v * 0.9), rg.randint(10, 28)))
        _GRAIN = g
    surf.blit(_GRAIN, (random.randint(-3, 3), random.randint(-3, 3)))
    if random.random() < 0.06:
        d = pygame.Surface((w, h))
        d.fill((7, 8, 11))
        surf.blit(d, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
    if _VIG is None:
        v = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(64):
            a = int(170 * (1 - i / 64) ** 1.5)
            pygame.draw.rect(v, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
        _VIG = v
    surf.blit(_VIG, (0, 0))


def draw_spread_drive(surf, t):
    """The whole drive out. `t` = seconds since the ending began."""
    W, H = surf.get_size()
    if t < SPREAD_T_SHIFT:
        _exterior_road(surf, t)
    elif t < SPREAD_T_FLOOD:
        _cab_interior(surf, t)
    else:
        _open_south(surf, t)

    warmth = _clamp01((t - SPREAD_T_FLOOD) / (BEAT_FLOOD * 0.6))
    sick = _clamp01((t - (SPREAD_T_KNOW - 0.6)) / 3.0)
    _post(surf, t, warmth, sick)

    # The white-gold bloom carrying the gaze into the flood (D -> E).
    bloom = 0.0
    if SPREAD_T_FLOOD - 0.8 < t < SPREAD_T_FLOOD:
        bloom = (t - (SPREAD_T_FLOOD - 0.8)) / 0.8
    elif SPREAD_T_FLOOD <= t < SPREAD_T_FLOOD + 0.9:
        bloom = 1.0 - (t - SPREAD_T_FLOOD) / 0.9
    if bloom > 0.01:
        veil = pygame.Surface((W, H))
        veil.fill((255, 238, 190))
        veil.set_alpha(int(255 * (bloom ** 1.2)))
        surf.blit(veil, (0, 0))

    # Fade in from the world at the start; fade to black under the verdict.
    if t < 0.6:
        veil = pygame.Surface((W, H))
        veil.fill((0, 0, 0))
        veil.set_alpha(int(255 * (1.0 - t / 0.6)))
        surf.blit(veil, (0, 0))
    out = (t - (SPREAD_TOTAL - 2.4)) / 2.4
    if out > 0.0:
        veil = pygame.Surface((W, H))
        veil.fill((0, 0, 0))
        veil.set_alpha(int(255 * _clamp01(out)))
        surf.blit(veil, (0, 0))
